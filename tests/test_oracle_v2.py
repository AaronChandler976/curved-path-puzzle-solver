"""Run 04 T4: regression tests for the oracle v1 misses fixed in oracle v2 (reports/run04/oracle_v2.md).

Synthetic scenes (no files written under data/: exact part SDFs are injected into the adapter's per-process cache,
contacts are computed into tmp_path):
1. Peg in a tight blind hole: only a straight pull along +z frees it. The v1 adapter never tests the start pose
   against a goal; v2's pre-check (= the start pose's straight connection to every goal) must solve it with zero
   CMG-RRT iterations, and the "root" fix alone must do the same.
2. Thin wall crossed by a thin plate: the library's coarse goal-edge check (n = dist/eta // 10 -> step 0.02 = 4 eps,
   end pose excluded) steps over a 0.015-thick wall; the fine check (step <= eps/2) must reject the edge.
"""
import os
import sys

import numpy as np
import trimesh

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
EPS = 0.005


def _box(lo, hi):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    m = trimesh.creation.box(extents=hi - lo)
    m.apply_translation((lo + hi) / 2)
    return m


_SDFS = {}


def _peg_scene(tmp_path, aid="t_peg", monkeypatch=None):
    from disasm.oracle import cmgrrt, exact_sdf
    from disasm.oracle.exact_sdf import PartSDF
    if monkeypatch is not None:     # never build/cache test SDFs under data/ even if the adapter's cache is cleared
        monkeypatch.setattr(exact_sdf, "part_sdf_cached", lambda asm, i, *a, **k: (_SDFS[(asm.id, int(i))], 0.0, True))
    c = 0.002                                   # clearance < eps
    peg = _box([-0.1, -0.1, 0.0], [0.1, 0.1, 0.6])
    walls = trimesh.util.concatenate([
        _box([-0.4, -0.4, -0.2], [0.4, 0.4, 0.0]),                  # bottom (peg rests on it)
        _box([-0.4, -0.4, 0.0], [-0.1 - c, 0.4, 0.5]),              # -x wall
        _box([0.1 + c, -0.4, 0.0], [0.4, 0.4, 0.5]),                # +x wall
        _box([-0.1 - c, -0.4, 0.0], [0.1 + c, -0.1 - c, 0.5]),      # -y wall
        _box([-0.1 - c, 0.1 + c, 0.0], [0.1 + c, 0.4, 0.5]),        # +y wall
    ])
    asm = cmgrrt.assembly_from_meshes(aid, {0: walls, 1: peg})
    cmgrrt.contact_graph(asm, cache_dir=str(tmp_path))
    for p, m in asm.meshes.items():
        _SDFS[(aid, p)] = PartSDF(np.asarray(m.vertices), np.asarray(m.faces), name=f"{aid}/{p}",
                                  sign_mode="winding_number")
        cmgrrt._PART_SDF[(aid, p)] = _SDFS[(aid, p)]
    return asm


def test_precheck_solves_peg_at_root(tmp_path, monkeypatch):
    from disasm.oracle.oracle_v2 import query_v2
    asm = _peg_scene(tmp_path, monkeypatch=monkeypatch)
    r = query_v2(asm, set(), 1, 5.0, seed=0, workdir=str(tmp_path), eps=EPS, always_cmgrrt=False, save_path=False)
    assert r["error"] is None, r.get("traceback")
    assert r["start_valid"]
    assert r["precheck_free"] and r["outcome"] == "success" and r["stage"] == "precheck"
    v = np.asarray(r["precheck_vec"])
    assert v[2] > 0.99                          # the only way out is +z
    assert r["cmgrrt_ran"] is False and r["time_s"] == r["precheck_time_s"]


def test_root_fix_alone_solves_peg(tmp_path, monkeypatch):
    from disasm.oracle.cmgrrt import query
    asm = _peg_scene(tmp_path, "t_peg2", monkeypatch)
    r = query(asm, set(), 1, 5.0, seed=0, workdir=str(tmp_path), detector="exact", eps=EPS, fix=("root",),
              save_path=False)
    assert r["error"] is None, r.get("traceback")
    assert r["outcome"] == "success" and r["solved_at_root"] and r["iterations"] == 0


def test_fine_goal_edge_catches_thin_wall(tmp_path):
    import dataclasses
    from disasm.oracle.cmgrrt_core import PlannerParams
    from disasm.oracle.exact_sdf import ExactUnionSDF, PartSDF, make_detector
    from disasm.oracle.path_validate import check_edge
    from taucgl_rrt.cspace import SE3
    wall = _box([-0.0075, -0.5, -0.5], [0.0075, 0.5, 0.5])          # 0.015 thick: inside depth up to 0.0075 > eps
    plate = _box([-0.002, -0.1, -0.1], [0.002, 0.1, 0.1])           # robot: 0.004 thick plate
    union = ExactUnionSDF([PartSDF(np.asarray(wall.vertices), np.asarray(wall.faces), sign_mode="winding_number")])
    params = dataclasses.replace(PlannerParams(), threshold=-EPS)
    cd = make_detector(params, "cpu", union, q1=SE3())
    f = os.path.join(str(tmp_path), "plate.obj")
    plate.export(f)
    cd.set_robot(f)
    cd.generate_robot_sampling(params.sampling)
    qa, qb = SE3(-0.05, 0, 0, 1, 0, 0, 0), SE3(0.05, 0, 0, 1, 0, 0, 0)
    n = int(qa.distance(qb) / params.eta) // 10                    # the library's goal-edge discretisation
    assert n == 5
    assert cd.is_edge_valid(qa, qb, n=n, threshold=params.threshold)      # coarse: steps over the wall
    S = np.asarray(cd.robot["sampling"], dtype=np.float64)
    r = check_edge(union, S, qa.to_numpy(), qb.to_numpy(), EPS)
    assert not r["valid"] and r["d_fail"] < -EPS                   # fine: hits it


def test_margin_keeps_start_valid_and_solves(tmp_path, monkeypatch):
    from disasm.oracle.oracle_v2 import query_v2
    asm = _peg_scene(tmp_path, "t_peg3", monkeypatch)
    r = query_v2(asm, set(), 1, 5.0, seed=0, workdir=str(tmp_path), eps=EPS, always_cmgrrt=True, save_path=False,
                 margin=0.0005, max_iterations=3)
    assert r["error"] is None, r.get("traceback")
    assert r["start_valid"] and r["precheck_free"] and r["outcome"] == "success"
    assert r["cmgrrt_ran"] and r["margin"] == 0.0005
