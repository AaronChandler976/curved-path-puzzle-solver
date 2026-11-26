"""Run 04 T4.2: instrumented re-run of the v1 adapter on one query, to find why a linear-free part stays unsolved.

The search loop is a line-by-line copy of ``cmgrrt.query`` (v1: one tree toward goals[0]; after each iteration the
newest node is tested against goals[1:] with the library's coarse edge check, n = dist/eta // 10), plus logging:
- root tests (never done by v1): straight connection from the start pose to every valid goal, with the library's
  coarse check AND with the fine certified check (path_validate.check_edge, step <= eps/2);
- per iteration: how many poses the extension added, the rotation / translation of the newest node, which goals were
  tested from it and with what result;
- the index of the free direction in the goal list (goal 0 = the tree's own target).
Seeded robot samples (run 04 T1) and the query's v1 seed are used. Times here are diagnostics, not results.
"""
from __future__ import annotations

import os
import time

import numpy as np


def diagnose_job(job: dict) -> dict:
    import dataclasses
    from disasm.oracle.cmgrrt import (GOAL_MARGIN, _rotation_deg, _setup_cd, candidate_directions, exact_union,
                                      load_assembly, robot_sample_seed)
    from disasm.oracle.cmgrrt_core import PlannerParams, seed_all
    from disasm.oracle.linear_precheck import sweep_direction
    from disasm.oracle.path_validate import check_edge
    from taucgl_rrt.cspace import SE3
    from taucgl_rrt.rrt import RRT
    from threadpoolctl import threadpool_limits

    eps = job.get("eps", 0.005)
    params = dataclasses.replace(PlannerParams(), threshold=-abs(eps))
    asm = load_assembly(job["asm_dir"])
    removed, part, seed = set(job["removed"]), job["part"], job["seed"]
    present = set(asm.part_ids) - removed
    obst = present - {part}
    seed_all(seed)
    union, _, _ = exact_union(asm, obst)
    cd = _setup_cd(asm, part, union, job["workdir"], params, "cpu", exact=True, sample_seed=robot_sample_seed(seed))
    S = np.asarray(cd.robot["sampling"], dtype=np.float64)
    D = asm.bbox_diag + GOAL_MARGIN
    cands = candidate_directions(asm, part, present)
    q0 = SE3()
    out = {"assembly_id": asm.id, "state_key": job["state_key"], "part_id": part, "seed": seed,
           "start_min_sdf_cd": float(cd.distance_between_objects(q0)), "start_min_sdf_exact": float(union.eval_np(S).min()),
           "free_dir_run03": job.get("free_dir")}
    # pre-check with the seeded samples (all directions)
    pre = {}
    for name, v in cands:
        r = sweep_direction(union, S, np.asarray(v, float), D, eps)
        pre[name] = r["free"]
    out["precheck_seeded"] = pre
    out["linear_free_seeded"] = any(pre.values())
    goals, names = [], []
    invalid = []
    for name, v in cands:
        g = SE3(*(D * v), 1.0, 0.0, 0.0, 0.0)
        if cd.is_point_valid(g, params.threshold):
            goals.append(g); names.append(name)
        else:
            invalid.append(name)
    out["goals"], out["invalid_goals"] = names, invalid
    free_names = [n for n in names if pre.get(n)]
    out["free_goal_indices"] = [names.index(n) for n in free_names]
    # root tests (v1 never does these)
    root = {}
    for g, name in zip(goals, names):
        n = int(q0.distance(g) / params.eta) // 10
        coarse = bool(cd.is_edge_valid(q0, g, n=n, threshold=params.threshold))
        fine = check_edge(union, S, q0.to_numpy(), g.to_numpy(), eps)
        root[name] = {"coarse": coarse, "fine": fine["valid"], "n_coarse": n, "fine_evals": fine["n_evals"]}
    out["root"] = root
    out["root_coarse_any"] = any(v["coarse"] for v in root.values())
    out["root_fine_any"] = any(v["fine"] for v in root.values())
    if not goals:
        out["error"] = "no_valid_goal"
        return out
    # instrumented v1 loop (identical control flow to cmgrrt.query)
    T = job.get("T", 30.0)
    its = []
    _tp = threadpool_limits(1)
    rrt = RRT(cd, SE3(), q0, goals[0])
    it, win = 0, None
    t0 = time.time()
    while True:
        it += 1
        rec = {"it": it}
        solved = rrt.step(params.eta, params.threshold, params.steps)
        qs = rrt.last_edge or []
        rec["grow"] = len(qs) - 1 if qs else 0
        if len(qs) > 1:
            node = qs[-1]
            rec["rot_deg"] = _rotation_deg(node.to_numpy())
            rec["trans"] = float(np.linalg.norm(node.to_numpy()[:3]))
            rec["near_rot_deg"] = _rotation_deg(qs[0].to_numpy())
            rec["near_is_root"] = bool(np.allclose(qs[0].to_numpy(), q0.to_numpy()))
            rec["g0"] = bool(solved)
            if solved:
                win = 0
            else:
                tested = []
                for gi in range(1, len(goals)):
                    g = goals[gi]
                    ok = cd.is_edge_valid(node, g, n=int(node.distance(g) / params.eta) // 10, threshold=params.threshold)
                    tested.append(bool(ok))
                    if ok:
                        rrt.tree.add_edge(node.to_tuple(), g.to_tuple(), weight=g.distance(node))
                        rrt.q2_end = g
                        win = gi
                        break
                rec["others"] = tested
        if len(its) < 400:
            its.append(rec)
        if win is not None or time.time() - t0 > T:
            break
    _tp.restore_original_limits()
    out["time_s"] = time.time() - t0
    out["iterations"] = it
    out["outcome"] = "success" if win is not None else "unsolved"
    out["win_goal"] = names[win] if win is not None else None
    grown = [r for r in its if r["grow"] > 0]
    out["n_iter_logged"] = len(its)
    out["n_iter_grow"] = len(grown)
    out["n_iter_nogrow"] = len(its) - len(grown)
    out["n_grow_from_root"] = sum(r.get("near_is_root", False) for r in grown)
    out["tested_rot_deg_min"] = min((r["rot_deg"] for r in grown), default=None)
    out["tested_rot_deg_median"] = float(np.median([r["rot_deg"] for r in grown])) if grown else None
    out["tested_trans_max"] = max((r["trans"] for r in grown), default=None)
    out["iters"] = its[:60]
    return out
