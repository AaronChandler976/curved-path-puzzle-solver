"""Straight-line pull pre-check for one (state, part) query (run 03 R1: rotation-required labels).

For a query (assembly, removed, part) the part is translated along each goal-candidate direction the
CMG-RRT adapter uses (``cmgrrt.candidate_directions``, same order) out to the adapter's goal distance
D = bbox_diag + GOAL_MARGIN. Collision model = the run 02 oracle: exact union SDF of the other remaining
parts, evaluated at the SAME robot surface samples CMG-RRT uses (``generate_robot_sampling`` after
``seed_all(query seed)``, exactly as in ``cmgrrt.query``), with the same contact tolerance: a pose
collides iff min SDF < -eps.

Step size. Poses along the line are checked at steps of at most eps/2 wherever that matters:
  step_k = max(eps/2, d_k + eps),   d_k = min over samples of the (lower-bound) union SDF at pose k.
Under a pure translation by s every sample point moves by exactly s and the union SDF is 1-Lipschitz,
so the true min SDF at every pose in (t_k, t_k + d_k + eps] is >= d_k - s >= -eps: all of those poses are
proven collision-free, not just sampled. Where d_k + eps < eps/2 the step is exactly eps/2. The check
is therefore at least as strict as a uniform eps/2 sweep (it is a uniform eps/2 sweep near contact and a
certified continuous check elsewhere). The returned union value is a lower bound of the true SDF
(exact_sdf.ExactUnionSDF), which keeps the certificate valid. The last pose checked is exactly t = D.

Outputs ``linear_free`` (some direction clears) and the first clearing direction in candidate order.
A pre-check never replaces a CMG-RRT query; it only labels which successes needed more than a pull.
"""
from __future__ import annotations

import os
import time

import numpy as np


def sweep_direction(union, samples: np.ndarray, v: np.ndarray, D: float, eps: float,
                    max_evals: int = 200000) -> dict:
    """Translate the sample set along unit v from t=0 to t=D. Returns {free, t_block, n_evals, min_step}."""
    t, n, min_step = 0.0, 0, np.inf
    while True:
        d = float(union.eval_np(samples + t * v).min())
        n += 1
        if d < -eps:
            return {"free": False, "t_block": t, "n_evals": n, "min_step": float(min_step)}
        if t >= D:
            return {"free": True, "t_block": None, "n_evals": n, "min_step": float(min_step)}
        if n >= max_evals:
            return {"free": False, "t_block": t, "n_evals": n, "min_step": float(min_step), "aborted": True}
        step = max(eps / 2.0, d + eps)
        min_step = min(min_step, step)
        t = min(D, t + step)


def precheck(asm, removed, part: int, seed: int, workdir: str, eps: float = 0.005, all_dirs: bool = False) -> dict:
    """Straight-line pull test for one query. Same robot samples and union SDF as cmgrrt.query(detector='exact')."""
    from disasm.oracle.cmgrrt import GOAL_MARGIN, _setup_cd, candidate_directions, exact_union
    from disasm.oracle.cmgrrt_core import PlannerParams, seed_all
    import dataclasses
    t0 = time.time()
    params = dataclasses.replace(PlannerParams(), threshold=-abs(eps))
    present = set(asm.part_ids) - set(removed)
    obst = present - {part}
    seed_all(seed)                                    # same order of RNG use as cmgrrt.query
    union, _, _ = exact_union(asm, obst)
    cd = _setup_cd(asm, part, union, workdir, params, "cpu", exact=True)
    S = np.asarray(cd.robot["sampling"], dtype=np.float64)     # world frame (q1 = q2_start = identity)
    start_min = float(union.eval_np(S).min())
    D = asm.bbox_diag + GOAL_MARGIN
    dirs = candidate_directions(asm, part, present)
    per_dir, first, n_evals = {}, None, 0
    for name, v in dirs:
        r = sweep_direction(union, S, np.asarray(v, dtype=np.float64), D, eps)
        n_evals += r["n_evals"]
        per_dir[name] = {"free": r["free"], "t_block": r["t_block"], "n_evals": r["n_evals"]}
        if r["free"] and first is None:
            first = name
            if not all_dirs:
                break
    return {"linear_free": first is not None, "first_free_dir": first, "n_dirs_total": len(dirs),
            "n_dirs_checked": len(per_dir), "dirs": per_dir, "start_min_sdf_precheck": start_min,
            "n_samples": int(len(S)), "goal_distance": D, "eps": eps, "step_rule": "max(eps/2, d+eps)",
            "max_fixed_step": eps / 2.0, "n_evals": n_evals, "time_s": time.time() - t0}


# ------------------------------------------------------------------ pool job (one assembly per job)
_ASM = {}


def run_assembly_job(job: dict) -> list:
    """job = {asm_dir, assembly_id, queries: [{state_key, removed, part_id, seed}], workdir, eps}."""
    import traceback
    from disasm.oracle.cmgrrt import load_assembly
    out = []
    try:
        asm = load_assembly(job["asm_dir"])
    except Exception as e:  # noqa: BLE001
        return [{**q, "assembly_id": job["assembly_id"], "error": f"load: {e}"} for q in job["queries"]]
    for q in job["queries"]:
        rec = {"assembly_id": job["assembly_id"], "state_key": q["state_key"], "part_id": q["part_id"],
               "removed": q["removed"], "seed": q["seed"]}
        try:
            rec.update(precheck(asm, set(q["removed"]), q["part_id"], q["seed"], job["workdir"], job["eps"]))
            rec["error"] = None
        except Exception as e:  # noqa: BLE001 - logged, never hidden
            rec["error"] = f"{type(e).__name__}: {e}"
            rec["traceback"] = traceback.format_exc()
        rec["worker_pid"] = os.getpid()
        out.append(rec)
    return out
