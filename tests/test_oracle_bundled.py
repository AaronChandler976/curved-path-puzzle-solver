"""Reproduce a bundled CMG-RRT two-body example through our adapter (S3).

general/11356 (the bundled example that succeeded in the S1 smoke sweep) comes from ATA joint_assembly_rotation (scaled by 0.2), so it is the same kind of
geometry our dataset queries use. The adapter must: build the obstacle SDF itself, accept the
assembled start pose as valid, and find an extraction path for part 1 within the budget.
"""
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

EXAMPLE = os.environ.get("BUNDLED_EXAMPLE", "general/11356")


def test_bundled_two_body(tmp_path):
    from disasm.oracle.cmgrrt import bundled_example_assembly, query
    a = bundled_example_assembly(EXAMPLE)
    assert a.part_ids == [0, 1]
    r = query(a, set(), 1, timeout_s=float(os.environ.get("BUNDLED_TIMEOUT", 300)), seed=0,
              workdir=str(tmp_path), device=os.environ.get("ORACLE_DEVICE", "cpu"))
    print({k: v for k, v in r.items() if k != "traceback"})
    assert r["error"] is None
    assert r["start_valid"], r["start_min_sdf"]
    assert r["outcome"] == "success"
    assert r["path_file"] and os.path.exists(r["path_file"])
