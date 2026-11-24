"""Run 04 T6.2: validate the per-pair penetration allowance on labelled success paths.

For every success of a fresh-allowance assembly (the path the main oracle config used: the straight pull if the
pre-check cleared, else the CMG-RRT path), with the query's own seeded robot samples:
  (A) start valid: min over parts of (d_k + offset_k) >= -eps at the start pose;
  (B) non-overlapping pairs keep the GLOBAL eps along the whole path: d_k >= -eps (offset_k = 0);
  (C) overlapping pairs never go deeper than at the start (+ eps tolerance): d_k(q) >= d_k(q0) - eps; a part pushed
      into or through its partner would violate this;
  (D) the end pose is clear of every part at the global eps (d_k >= -eps for all k, no allowance).
Poses: every edge interpolated as the planner does (path_validate.interpolate), step <= eps/2 of sample displacement
near contact, larger only where the union value certifies it (as in path_validate.check_edge).
"""
from __future__ import annotations

import json

import numpy as np


def _per_part(parts, P):
    out = []
    for part in parts:
        lb = part.box_lower_bound(P)
        near = lb <= 0.1
        v = lb.min() if not near.any() else min(lb[~near].min() if (~near).any() else np.inf, part.signed(P[near]).min())
        out.append(float(v))
    return np.array(out)


def check_job(job: dict) -> dict:
    import dataclasses
    from disasm.oracle.cmgrrt import _setup_cd, exact_union, load_assembly, robot_sample_seed
    from disasm.oracle.cmgrrt_core import PlannerParams, seed_all
    from disasm.oracle.path_validate import interpolate, quat_to_R, rot_angle
    eps = 0.005
    params = dataclasses.replace(PlannerParams(), threshold=-eps)
    asm = load_assembly(job["asm_dir"])
    res = []
    for it in job["items"]:
        present = set(asm.part_ids) - set(it["removed"])
        obst = sorted(present - {it["part"]})
        union, _, _ = exact_union(asm, set(obst), moving=it["part"], allowance=job["allowance"])
        seed_all(it["seed"])
        cd = _setup_cd(asm, it["part"], union, job["workdir"], params, "cpu", exact=True,
                       sample_seed=robot_sample_seed(it["seed"]))
        S = np.asarray(cd.robot["sampling"], dtype=np.float64)
        r_max = float(np.linalg.norm(S, axis=1).max())
        path = json.load(open(it["path_file"]))["path"]
        overl = union.offsets > 0
        d0 = _per_part(union.parts, S @ quat_to_R(path[0][3:]).T + np.asarray(path[0][:3]))
        off = np.where(overl, np.maximum(0.0, -d0), 0.0)     # the oracle's rule: own start depth (cmgrrt.query)
        A = bool((d0 + off).min() >= -eps)
        worst_B, worst_C = np.inf, np.inf
        for i in range(len(path) - 1):
            qa, qb = path[i], path[i + 1]
            L = float(np.linalg.norm(np.asarray(qb[:3]) - np.asarray(qa[:3]))) + 2 * rot_angle(qa, qb) * r_max
            a = 0.0
            while True:
                q = interpolate(qa, qb, a)
                d = _per_part(union.parts, S @ quat_to_R(q[3:]).T + q[:3])
                if (~overl).any():
                    worst_B = min(worst_B, float((d[~overl]).min()))
                if overl.any():
                    worst_C = min(worst_C, float((d[overl] - d0[overl]).min()))
                if a >= 1.0 or L <= 1e-15:
                    break
                a = min(1.0, a + max(eps / 2, float((d + off).min()) + eps) / L)
        dend = _per_part(union.parts, S @ quat_to_R(path[-1][3:]).T + np.asarray(path[-1][:3]))
        rec = {"id": it["id"], "A_start_valid": A, "B_min_nonoverlap": worst_B, "B_ok": bool(worst_B >= -eps),
               "C_min_deepening": worst_C, "C_ok": bool(worst_C >= -eps), "D_end_min": float(dend.min()),
               "D_ok": bool(dend.min() >= -eps), "n_overlap_pairs": int(overl.sum()), "path_nodes": len(path)}
        rec["all_ok"] = rec["A_start_valid"] and rec["B_ok"] and rec["C_ok"] and rec["D_ok"]
        res.append(rec)
    return {"items": res}
