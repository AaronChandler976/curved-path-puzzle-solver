"""CMG-RRT adapter for multi-part assemblies: "can part p leave the current sub-assembly?"

Public entry point: ``query(assembly, removed, part, timeout_s, seed, workdir)``.

Design (see reports/oracle_design.md for the reasoning and the checks behind each point):
- Two-body limit: CMG-RRT plans one moving body against one static obstacle SDF. The obstacle is
  the union of every part still present except ``part``; its neural SDF is trained once per
  obstacle set and cached on disk (key = sorted obstacle part ids).
- Scale: ATA multi-part assemblies are stored in assembled pose, normalised to max|coord| = 5.
  CMG-RRT's bundled ATA-derived examples (resources/models/general/*) are the same meshes x 0.2,
  and the planner constants (eta = 0.002, threshold = -0.005) are absolute lengths in that frame.
  We therefore scale each assembly by 1/max|coord| (= 0.2 for normalised assemblies).
- Poses: CMG-RRT SE3 is [x, y, z, qw, qx, qy, qz]. The obstacle SDF is evaluated in the q1 frame
  and robot surface samples are moved by q2 (collision_detection.py: Aq2 = inv(A(q1)) @ A(q2)).
  All meshes are already in world/assembled coordinates, so q1 = q2_start = identity.
- Goals: each candidate escape direction d gives goal = translate(D * d), D = bbox diagonal of the
  whole assembly + margin, so the part is fully clear of every other part at the goal.
  Candidates share ONE timeout: we grow a single CMG-RRT tree from the assembled pose (exactly
  RRT.step from the library) and after every iteration also test the straight connection of the
  newest node to every other candidate goal with the library's own is_edge_valid (same
  discretisation as RRT.step). The first goal connected wins and is recorded.
- A query that does not connect within the budget is "unsolved" (censored), never "infeasible".
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import time
from dataclasses import dataclass, field

import numpy as np
import trimesh

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_CACHE = os.path.join(ROOT, "data", "processed")

CONTACT_EPS = 0.01       # unit-frame distance under which surface samples count as contact
CONTACT_SAMPLES = 3000   # surface samples per part for contact detection
GOAL_MARGIN = 0.1


@dataclass
class Assembly:
    id: str
    dir: str
    part_ids: list
    meshes: dict                 # part id -> trimesh.Trimesh in the unit (scaled) frame
    scale: float                 # unit = raw * scale
    raw_max_abs: float
    _contacts: dict | None = field(default=None, repr=False)

    @property
    def bbox_diag(self) -> float:
        b = np.array([m.bounds for m in self.meshes.values()])
        return float(np.linalg.norm(b[:, 1].max(0) - b[:, 0].min(0)))

    def centroid(self, p: int) -> np.ndarray:
        return np.asarray(self.meshes[p].centroid)


def load_assembly(asm_dir: str) -> Assembly:
    files = sorted(glob.glob(os.path.join(asm_dir, "*.obj")), key=lambda f: int(os.path.basename(f)[:-4]))
    raw = {}
    for f in files:
        m = trimesh.load_mesh(f, process=True)
        if isinstance(m, trimesh.Scene):
            m = m.to_mesh()
        raw[int(os.path.basename(f)[:-4])] = m
    if len(raw) < 2:
        raise ValueError(f"{asm_dir}: fewer than 2 parts")
    max_abs = float(max(np.abs(m.vertices).max() for m in raw.values()))
    s = 1.0 / max_abs
    meshes = {}
    for k, m in raw.items():
        m = m.copy()
        m.apply_scale(s)
        meshes[k] = m
    return Assembly(id=os.path.basename(os.path.normpath(asm_dir)), dir=asm_dir, part_ids=sorted(raw),
                    meshes=meshes, scale=s, raw_max_abs=max_abs)


# ----------------------------------------------------------------------------------- contacts
def contact_graph(asm: Assembly, cache_dir: str = DEFAULT_CACHE) -> dict:
    """Pairwise contacts in the assembled pose (parts never move except by removal, so this is
    computed once per assembly). For ordered pair (p, q): number of p's surface samples within
    CONTACT_EPS of q, and the mean of -n_p over them (direction that moves p away from q)."""
    if asm._contacts is not None:
        return asm._contacts
    path = os.path.join(cache_dir, "contacts", f"{asm.id}.json")
    if os.path.exists(path):
        asm._contacts = json.load(open(path))
        return asm._contacts
    from disasm.oracle.sdf_train import robust_sdf
    rng_state = np.random.get_state()
    np.random.seed(0)
    samples = {}
    for p, m in asm.meshes.items():
        pts, fi = trimesh.sample.sample_surface(m, CONTACT_SAMPLES)
        samples[p] = (np.asarray(pts), np.asarray(m.face_normals[fi]))
    np.random.set_state(rng_state)
    pairs = {}
    for p in asm.part_ids:
        pts, nrm = samples[p]
        for q in asm.part_ids:
            if q == p:
                continue
            mq = asm.meshes[q]
            # cheap bbox reject
            lo, hi = mq.bounds[0] - CONTACT_EPS, mq.bounds[1] + CONTACT_EPS
            inb = np.all((pts >= lo) & (pts <= hi), axis=1)
            if not inb.any():
                continue
            d = robust_sdf(mq, pts[inb], 4)
            c = np.abs(d) < CONTACT_EPS
            if c.sum() == 0:
                continue
            mean_away = (-nrm[inb][c]).mean(0)
            pairs[f"{p}-{q}"] = {"n": int(c.sum()), "away": mean_away.tolist(),
                                 "frac": float(c.sum()) / CONTACT_SAMPLES}
    out = {"eps": CONTACT_EPS, "samples": CONTACT_SAMPLES, "pairs": pairs}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + f".tmp{os.getpid()}"
    json.dump(out, open(tmp, "w"))
    os.replace(tmp, path)
    asm._contacts = out
    return out


def neighbors(asm: Assembly, p: int, present: set) -> list:
    pairs = contact_graph(asm)["pairs"]
    return [q for q in asm.part_ids if q != p and q in present and (f"{p}-{q}" in pairs or f"{q}-{p}" in pairs)]


def candidate_directions(asm: Assembly, part: int, present: set) -> list:
    """Ordered, de-duplicated unit escape directions: [mean outward contact normal over present
    neighbours] + [+x,-x,+y,-y,+z,-z] + [away from each present neighbour's centroid]."""
    pairs = contact_graph(asm)["pairs"]
    cands = []
    acc, w = np.zeros(3), 0
    for q in present:
        if q == part:
            continue
        e = pairs.get(f"{part}-{q}")
        if e:
            acc += np.asarray(e["away"]) * e["n"]
            w += e["n"]
    if w > 0 and np.linalg.norm(acc) > 1e-6:
        cands.append(("contact_normal", acc / np.linalg.norm(acc)))
    for i, name in enumerate("xyz"):
        for sgn in (1, -1):
            v = np.zeros(3)
            v[i] = sgn
            cands.append((("+" if sgn > 0 else "-") + name, v))
    c = asm.centroid(part)
    for q in neighbors(asm, part, present):
        v = c - asm.centroid(q)
        if np.linalg.norm(v) > 1e-6:
            cands.append((f"away_from_{q}", v / np.linalg.norm(v)))
    out = []
    for name, v in cands:
        if all(np.dot(v, u) < 0.995 for _, u in out):
            out.append((name, v))
    return out


# ----------------------------------------------------------------------------------- obstacle SDF
def obstacle_key(obstacle_ids) -> str:
    ids = "-".join(str(i) for i in sorted(obstacle_ids))
    return ids if len(ids) <= 80 else hashlib.sha1(ids.encode()).hexdigest()


def obstacle_sdf(asm: Assembly, obstacle_ids, cache_dir: str = DEFAULT_CACHE, cfg=None,
                 device: str = "cuda", log=lambda *a: None) -> tuple:
    """Return (pth_path, stats, prep_seconds, cached: bool). Atomic write; safe across workers."""
    from disasm.oracle.sdf_train import SDFTrainConfig, train_sdf_union
    cfg = cfg or SDFTrainConfig(num_threads=int(os.environ.get("DISASM_SDF_THREADS", "8")))
    d = os.path.join(cache_dir, "obstacle_sdf", asm.id)
    os.makedirs(d, exist_ok=True)
    key = obstacle_key(obstacle_ids)
    pth = os.path.join(d, f"{key}_e{cfg.epochs}_n{cfg.num_samples}.pth")
    if os.path.exists(pth) and os.path.exists(pth + ".json"):
        return pth, json.load(open(pth + ".json")), 0.0, True
    t0 = time.time()
    tmp = pth + f".tmp{os.getpid()}"
    st = train_sdf_union([asm.meshes[i] for i in sorted(obstacle_ids)], tmp, cfg, device=device, log=log)
    st["obstacle_ids"] = sorted(int(i) for i in obstacle_ids)
    st["out_path"] = pth
    os.replace(tmp, pth)
    json.dump(st, open(pth + ".json.tmp", "w"))
    os.replace(pth + ".json.tmp", pth + ".json")
    return pth, st, time.time() - t0, False


# ----------------------------------------------------------------------------------- query
def _rotation_deg(q7) -> float:
    w = min(1.0, abs(float(q7[3])) / max(1e-12, float(np.linalg.norm(q7[3:7]))))
    return float(np.degrees(2 * np.arccos(w)))


def _setup_cd(asm, part, sdf_path, workdir, params, device):
    import torch
    from taucgl_rrt.cspace import SE3
    from taucgl_rrt.collision_detection import CollisionDetector
    os.makedirs(workdir, exist_ok=True)
    robot_obj = os.path.join(workdir, f"robot_{asm.id}_{part}.obj")
    asm.meshes[part].export(robot_obj)
    cd = CollisionDetector(params.sdf_N, params.sdf_H, torch.device(device), params.threshold,
                           params.eta, abs(params.threshold))
    cd.set_robot(robot_obj)
    cd.generate_robot_sampling(params.sampling)
    cd.set_obstacles(sdf_path, SE3())
    return cd


def linear_precheck(asm: Assembly, removed: set, part: int, seed: int, workdir: str,
                    device: str = "cpu", params=None) -> dict:
    """Straight-line translation sweep along each candidate direction, with the same collision
    checker and discretisation CMG-RRT uses for goal connection. Diagnostic only: it never
    replaces a CMG-RRT query and is logged as a separate field."""
    from disasm.oracle.cmgrrt_core import PlannerParams, seed_all
    from taucgl_rrt.cspace import SE3
    params = params or PlannerParams()
    seed_all(seed)
    present = set(asm.part_ids) - set(removed)
    obst = present - {part}
    t0 = time.time()
    sdf, _, _, _ = obstacle_sdf(asm, obst)
    cd = _setup_cd(asm, part, sdf, workdir, params, device)
    D = asm.bbox_diag + GOAL_MARGIN
    res = {}
    for name, v in candidate_directions(asm, part, present):
        g = SE3(*(D * v), 1.0, 0.0, 0.0, 0.0)
        res[name] = bool(cd.is_edge_valid(SE3(), g, n=int(SE3().distance(g) / params.eta) // 10,
                                          threshold=params.threshold))
    return {"free_dirs": [k for k, ok in res.items() if ok], "n_dirs": len(res),
            "time_s": time.time() - t0}


def query(assembly: Assembly, removed: set, part: int, timeout_s: float, seed: int, workdir: str,
          device: str = "cpu", params=None, max_iterations: int | None = None,
          sdf_device: str = "cuda", save_path: bool = True) -> dict:
    """Can ``part`` leave the sub-assembly (all parts minus ``removed``)? One CMG-RRT query.

    Returns {outcome: "success"|"unsolved", time_s, iterations, goal_pose, escape_dir,
    n_goal_candidates_tried, path_file, error, ...diagnostics}. time_s is planner wall time
    (tree growth + goal checks); prep_s (obstacle SDF training if not cached + robot sampling)
    is reported separately.
    """
    from disasm.oracle.cmgrrt_core import PlannerParams, seed_all
    from taucgl_rrt.cspace import SE3
    from taucgl_rrt.rrt import RRT
    params = params or PlannerParams()
    asm = assembly
    present = set(asm.part_ids) - set(removed)
    out = {"outcome": "unsolved", "time_s": 0.0, "iterations": 0, "goal_pose": None, "escape_dir": None,
           "n_goal_candidates_tried": 0, "path_file": None, "error": None,
           "assembly_id": asm.id, "part_id": int(part), "removed": sorted(int(r) for r in removed),
           "timeout_s": timeout_s, "seed": seed, "device": device}
    if part not in present:
        out["error"] = "part_not_present"
        return out
    obst = present - {part}
    if not obst:
        out["error"] = "no_obstacle"   # caller should never query the last part
        return out
    try:
        seed_all(seed)
        t_prep0 = time.time()
        sdf, sdf_stats, t_sdf, cached = obstacle_sdf(asm, obst, device=sdf_device)
        cd = _setup_cd(asm, part, sdf, workdir, params, device)
        out["prep_s"] = time.time() - t_prep0
        out["sdf_train_s"] = t_sdf
        out["sdf_cached"] = cached
        out["sdf_sign_agreement"] = sdf_stats.get("sign_agreement_near_surface")
        out["sdf_p95_err"] = sdf_stats.get("valid_p95_abs_err_near_surface")
        out["sdf_path"] = sdf

        D = asm.bbox_diag + GOAL_MARGIN
        cands = candidate_directions(asm, part, present)
        q0 = SE3()
        out["start_min_sdf"] = float(cd.distance_between_objects(q0))
        out["start_valid"] = bool(out["start_min_sdf"] >= params.threshold)
        goals, names, dirs = [], [], []
        invalid_goals = []
        for name, v in cands:
            g = SE3(*(D * v), 1.0, 0.0, 0.0, 0.0)
            if cd.is_point_valid(g, params.threshold):
                goals.append(g); names.append(name); dirs.append(v)
            else:
                invalid_goals.append(name)
        out["goal_candidates"] = names
        out["invalid_goals"] = invalid_goals
        out["n_goal_candidates_tried"] = len(goals)
        if not goals:
            out["error"] = "no_valid_goal"
            return out

        rrt = RRT(cd, SE3(), q0, goals[0])
        it, win = 0, None
        t0 = time.time()
        while True:
            it += 1
            if rrt.step(params.eta, params.threshold, params.steps):
                win = 0
            elif rrt.last_edge is not None and len(rrt.last_edge) > 1:
                node = rrt.last_edge[-1]
                for gi in range(1, len(goals)):
                    g = goals[gi]
                    if cd.is_edge_valid(node, g, n=int(node.distance(g) / params.eta) // 10,
                                        threshold=params.threshold):
                        rrt.tree.add_edge(node.to_tuple(), g.to_tuple(), weight=g.distance(node))
                        rrt.q2_end = g
                        win = gi
                        break
            el = time.time() - t0
            if win is not None or el > timeout_s or (max_iterations and it >= max_iterations):
                break
        out["time_s"] = time.time() - t0
        out["iterations"] = it
        out["tree_nodes"] = rrt.tree.number_of_nodes()
        if win is not None:
            path = [p.to_numpy().tolist() for p in rrt.get_path()]
            out["outcome"] = "success"
            out["goal_pose"] = goals[win].to_numpy().tolist()
            out["escape_dir"] = names[win]
            out["escape_vec"] = np.asarray(dirs[win]).tolist()
            out["goal_index"] = win
            out["path_len_nodes"] = len(path)
            out["path_max_rot_deg"] = max(_rotation_deg(q) for q in path) if path else 0.0
            if save_path:
                pf = os.path.join(workdir, f"path_{asm.id}_{obstacle_key(obst)}__{part}_s{seed}.json")
                json.dump({"scale": asm.scale, "path": path}, open(pf, "w"))
                out["path_file"] = pf
    except Exception as e:  # noqa: BLE001 - logged, never hidden
        import traceback
        out["error"] = f"{type(e).__name__}: {e}"
        out["traceback"] = traceback.format_exc()
    return out
