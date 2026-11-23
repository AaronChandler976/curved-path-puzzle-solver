"""Exact union SDF (src/disasm/oracle/exact_sdf.py) against analytic box SDFs, and as a CMG-RRT detector."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def box_sdf(P, c, h):
    q = np.abs(P - c) - h
    out = np.linalg.norm(np.maximum(q, 0), axis=1)
    ins = np.minimum(q.max(1), 0)
    return out + ins


def _box(c, ext):
    import trimesh
    m = trimesh.creation.box(extents=ext)
    m.apply_translation(c)
    return m


def test_part_sdf_matches_analytic_box():
    from disasm.oracle.exact_sdf import PartSDF
    rng = np.random.default_rng(0)
    c, ext = np.array([0.1, -0.2, 0.05]), np.array([0.4, 0.3, 0.2])
    m = _box(c, ext)
    ps = PartSDF(m.vertices, m.faces, name="box")
    assert ps.sign_mode == "pseudonormal" and ps.sign_check["agreement"] >= 0.999
    P = np.concatenate([rng.uniform(c - ext, c + ext, (5000, 3)),
                        c + (ext / 2) * rng.choice([-1, 1], (2000, 3)) + rng.normal(0, 1e-3, (2000, 3))])  # near corners
    got, ref = ps.signed(P), box_sdf(P, c, ext / 2)
    assert np.abs(got - ref).max() < 1e-9


def test_union_is_min_and_band_lower_bound():
    import torch
    from disasm.oracle.exact_sdf import ExactUnionSDF, PartSDF
    rng = np.random.default_rng(1)
    a, b = _box([0, 0, 0], [0.2, 0.2, 0.2]), _box([0.21, 0, 0], [0.2, 0.2, 0.2])   # 0.01 gap
    u = ExactUnionSDF([PartSDF(a.vertices, a.faces), PartSDF(b.vertices, b.faces)], band=0.1)
    P = rng.uniform(-1, 1, (20000, 3))
    ref = np.minimum(box_sdf(P, np.zeros(3), 0.1), box_sdf(P, np.array([0.21, 0, 0]), 0.1))
    got = u(torch.tensor(P, dtype=torch.float32)).numpy().reshape(-1)
    assert np.all(got <= ref + 1e-6)                       # always a lower bound
    exact = ref <= 0.1
    assert np.abs(got[exact] - ref[exact]).max() < 1e-6    # exact inside the band (float32 output)


def test_detector_validity_through_library(tmp_path):
    from disasm.oracle.cmgrrt_core import PlannerParams
    from disasm.oracle.exact_sdf import ExactUnionSDF, PartSDF, make_detector
    from taucgl_rrt.cspace import SE3
    obst = _box([0, 0, 0], [0.4, 0.4, 0.4])
    robot = _box([0.3, 0, 0], [0.2, 0.2, 0.2])      # touching face at x = 0.2 (contact, sdf = 0)
    rp = str(tmp_path / "robot.obj")
    robot.export(rp)
    cd = make_detector(PlannerParams(), "cpu", ExactUnionSDF([PartSDF(obst.vertices, obst.faces)]))
    cd.set_robot(rp)
    cd.generate_robot_sampling(1000)
    assert bool(cd.is_point_valid(SE3(), -0.005))                              # flush contact is valid
    assert abs(float(cd.distance_between_objects(SE3()))) < 1e-6
    assert not bool(cd.is_point_valid(SE3(-0.01, 0, 0, 1, 0, 0, 0), -0.005))   # 0.01 penetration
    assert bool(cd.is_point_valid(SE3(-0.004, 0, 0, 1, 0, 0, 0), -0.005))      # 0.004 < eps
    assert bool(cd.is_edge_valid(SE3(), SE3(2, 0, 0, 1, 0, 0, 0), n=100, threshold=-0.005))
    g = cd.get_contact_gradients(SE3(), 0.005)
    assert len(g) >= 1
