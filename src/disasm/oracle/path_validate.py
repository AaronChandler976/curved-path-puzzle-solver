"""Fine-resolution path validation with the exact union SDF (run 04 T4; docs/PLAN.md Run 04 additions).

A path is a list of SE(3) poses [x, y, z, qw, qx, qy, qz] (CMG-RRT order). The robot's surface samples S are in the
world frame at the identity pose (q1 = q2_start = identity in our adapter), so at pose q they sit at R(q) S + t(q).
Each consecutive pair (an edge) is interpolated exactly as the planner interpolates it (``SE3.interpolate``: linear
translation, normalised-linear quaternion with sign fix), and checked against the contact tolerance: a pose
collides iff min over samples of the union SDF < -eps.

Step rule (the same as run 03 R1, reports/run03/DECISIONS.md #1, extended to rotation):
    the next checked pose is at most  max(step, d + eps)  of sample-point displacement away, d = min SDF at the
    current pose, step = eps / 2 by default.
Displacement of any sample point between interpolation parameters a and a + da is bounded by
    da * L,   L = |dt| + 2 * theta * r_max
with theta the rotation angle between the edge's end orientations and r_max = max |s| over samples (rotation is about
the world origin). The factor 2 bounds the non-uniform angular speed of normalised-linear interpolation (its peak
speed is at most 1.27x the mean for theta <= pi). Under a displacement of at most d + eps the 1-Lipschitz SDF cannot
drop below -eps, so every skipped pose is certified collision-free; near contact the check is a uniform <= eps/2
sweep. This is at least as strict as a uniform eps/2 sweep. The union SDF is a lower bound of the exact one
(exact_sdf.ExactUnionSDF), which keeps the certificate valid.
"""
from __future__ import annotations

import numpy as np


def quat_to_R(q):
    w, x, y, z = q
    n = np.sqrt(w * w + x * x + y * y + z * z)
    w, x, y, z = w / n, x / n, y / n, z / n
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def interpolate(qa, qb, a):
    """Exactly taucgl_rrt.cspace.SE3.interpolate on 7-vectors."""
    qa, qb = np.asarray(qa, float), np.asarray(qb, float)
    pos = (1 - a) * qa[:3] + a * qb[:3]
    ra, rb = qa[3:], qb[3:]
    if np.dot(ra, rb) < 0:
        rb = -rb
    r = (1 - a) * ra + a * rb
    r = r / np.linalg.norm(r)
    return np.concatenate([pos, r])


def rot_angle(qa, qb) -> float:
    ra, rb = np.asarray(qa[3:], float), np.asarray(qb[3:], float)
    ra, rb = ra / np.linalg.norm(ra), rb / np.linalg.norm(rb)
    return float(2 * np.arccos(min(1.0, abs(float(np.dot(ra, rb))))))


def pose_min_sdf(union, S, q) -> float:
    P = S @ quat_to_R(q[3:]).T + np.asarray(q[:3], float)
    return float(union.eval_np(P).min())


def check_edge(union, S, qa, qb, eps: float, step: float | None = None, r_max: float | None = None,
               max_evals: int = 500000) -> dict:
    """Validate the interpolated edge qa -> qb (both endpoints included). Returns
    {valid, a_fail, d_fail, d_min, n_evals}."""
    step = eps / 2.0 if step is None else step
    r_max = float(np.linalg.norm(S, axis=1).max()) if r_max is None else r_max
    L = float(np.linalg.norm(np.asarray(qb[:3], float) - np.asarray(qa[:3], float))) + 2.0 * rot_angle(qa, qb) * r_max
    a, n, dmin = 0.0, 0, np.inf
    while True:
        q = interpolate(qa, qb, a)
        d = pose_min_sdf(union, S, q)
        n += 1
        dmin = min(dmin, d)
        if d < -eps:
            return {"valid": False, "a_fail": a, "d_fail": d, "d_min": dmin, "n_evals": n}
        if a >= 1.0:
            return {"valid": True, "a_fail": None, "d_fail": None, "d_min": dmin, "n_evals": n}
        if n >= max_evals:
            return {"valid": False, "a_fail": a, "d_fail": d, "d_min": dmin, "n_evals": n, "aborted": True}
        if L <= 1e-15:
            a = 1.0
            continue
        a = min(1.0, a + max(step, d + eps) / L)


def validate_path(union, S, path, eps: float, step: float | None = None) -> dict:
    """Every edge of the path. Returns {valid, n_edges, first_bad_edge, bad_edges, d_min, n_evals, goal_edge_bad}."""
    S = np.ascontiguousarray(S, dtype=np.float64)
    r_max = float(np.linalg.norm(S, axis=1).max())
    bad, n_ev, dmin = [], 0, np.inf
    for i in range(len(path) - 1):
        r = check_edge(union, S, path[i], path[i + 1], eps, step, r_max)
        n_ev += r["n_evals"]
        dmin = min(dmin, r["d_min"])
        if not r["valid"]:
            bad.append({"edge": i, "a_fail": r["a_fail"], "d_fail": r["d_fail"]})
    if len(path) == 1:
        d = pose_min_sdf(union, S, path[0])
        dmin = d
        if d < -eps:
            bad.append({"edge": 0, "a_fail": 0.0, "d_fail": d})
    return {"valid": not bad, "n_edges": max(0, len(path) - 1), "first_bad_edge": bad[0]["edge"] if bad else None,
            "bad_edges": bad[:10], "n_bad": len(bad), "d_min": dmin, "n_evals": n_ev,
            "goal_edge_bad": bool(bad) and bad[-1]["edge"] == len(path) - 2}


# ------------------------------------------------------------------ pool job: validate saved paths of one assembly
_ASM = {}


def validate_saved_job(job: dict) -> dict:
    """job = {asm_dir, items: [{id, removed, part, seed, path_file}], eps, workdir}. Robot samples = the seeded
    planner sample set for that query seed (cmgrrt._setup_cd with robot_sample_seed(seed), i.e. what a run 04 planner
    query with this seed uses). For v1 paths (unseeded planner draw) this is an independent draw of the same size."""
    import dataclasses
    import json
    import time as _t
    from disasm.oracle.cmgrrt import _setup_cd, exact_union, load_assembly, robot_sample_seed
    from disasm.oracle.cmgrrt_core import PlannerParams, seed_all
    eps = job.get("eps", 0.005)
    params = dataclasses.replace(PlannerParams(), threshold=-abs(eps))
    asm = load_assembly(job["asm_dir"])
    res = []
    for it in job["items"]:
        t0 = _t.time()
        rec = {"id": it["id"], "assembly_id": asm.id, "part": it["part"], "removed": it["removed"], "seed": it["seed"]}
        try:
            present = set(asm.part_ids) - set(it["removed"])
            union, _, _ = exact_union(asm, present - {it["part"]})
            seed_all(it["seed"])
            cd = _setup_cd(asm, it["part"], union, job["workdir"], params, "cpu", exact=True,
                           sample_seed=robot_sample_seed(it["seed"]))
            S = np.asarray(cd.robot["sampling"], dtype=np.float64)
            path = json.load(open(it["path_file"]))["path"]
            rec["start_min_sdf"] = pose_min_sdf(union, S, path[0])
            rec.update(validate_path(union, S, path, eps))
            rec["error"] = None
        except Exception as e:  # noqa: BLE001
            rec["error"] = f"{type(e).__name__}: {e}"
        rec["time_s"] = _t.time() - t0
        res.append(rec)
    return {"items": res}
