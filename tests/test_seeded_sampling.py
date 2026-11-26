"""Run 04 T1: seeded robot sampling. The same query (same seed) must draw identical robot surface samples and
grow an identical CMG-RRT tree; a different seed must draw different samples."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASM = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly/00089")


def _samples(a, part, seed, tmp):
    import dataclasses
    from disasm.oracle.cmgrrt import _setup_cd, exact_union, robot_sample_seed
    from disasm.oracle.cmgrrt_core import PlannerParams, seed_all
    seed_all(seed)
    union, _, _ = exact_union(a, set(a.part_ids) - {part})
    cd = _setup_cd(a, part, union, str(tmp), dataclasses.replace(PlannerParams()), "cpu", exact=True,
                   sample_seed=robot_sample_seed(seed))
    return np.asarray(cd.robot["sampling"]), np.asarray(cd.robot["reduced_sampling"])


def test_same_seed_same_samples(tmp_path):
    from disasm.oracle.cmgrrt import load_assembly
    a = load_assembly(ASM)
    s1, c1 = _samples(a, 0, 123, tmp_path)
    s2, c2 = _samples(a, 0, 123, tmp_path)
    s3, _ = _samples(a, 0, 124, tmp_path)
    assert np.array_equal(s1, s2) and np.array_equal(c1, c2)
    assert not np.array_equal(s1, s3)


def test_library_sampler_restored(tmp_path):
    import trimesh.sample as ts
    from disasm.oracle.cmgrrt import seeded_surface_sampling
    orig = ts.sample_surface
    with seeded_surface_sampling(5):
        assert ts.sample_surface is not orig
    assert ts.sample_surface is orig


def test_same_query_same_tree(tmp_path):
    """03085 state 0-2, part 0 was unsolved in v1 (241 iterations in 30 s): a multi-iteration tree. Budget by
    iteration count (not time) so both runs do the same work."""
    from disasm.oracle.cmgrrt import load_assembly, query
    a = load_assembly(os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly/03085"))
    removed = set(a.part_ids) - {0, 2}
    rs = [query(a, removed, 0, timeout_s=1e6, seed=3758590191, workdir=str(tmp_path), detector="exact", eps=0.005,
                max_iterations=12, save_path=False) for _ in range(2)]
    for r in rs:
        assert r["error"] is None, r
    assert rs[0]["iterations"] == rs[1]["iterations"] and rs[0]["iterations"] > 1
    assert rs[0]["tree_nodes"] == rs[1]["tree_nodes"] and rs[0]["tree_nodes"] > 1
    assert rs[0]["tree_hash"] == rs[1]["tree_hash"]
    assert rs[0]["outcome"] == rs[1]["outcome"]
