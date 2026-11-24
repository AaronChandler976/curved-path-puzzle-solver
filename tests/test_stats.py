import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from disasm.eval.stats import cindex, ece, hodges_lehmann, holm, paired  # noqa: E402


def test_holm_matches_definition():
    adj = holm([0.01, 0.04, 0.03])
    assert np.allclose(adj, [0.03, 0.06, 0.06])


def test_hl_symmetric_and_shift():
    d = np.array([-3.0, -1.0, 0.0, 2.0, 10.0])
    assert hodges_lehmann(d + 5) == hodges_lehmann(d) + 5
    assert hodges_lehmann(np.array([1.0])) == 1.0


def test_paired_wtl_and_ratio():
    a = np.array([1.0, 2.0, 3.0, 4.0])
    b = np.array([2.0, 2.005, 1.0, 8.0])
    r = paired(a, b, B=500)
    assert (r["wins"], r["ties"], r["losses"]) == (2, 1, 1)
    assert abs(r["ratio"] - 10.0 / 13.005) < 1e-9
    assert r["ratio_ci"][0] <= r["ratio"] <= r["ratio_ci"][1]


def test_cindex_perfect_and_ece():
    t = np.array([1.0, 2.0, 3.0]); e = np.array([1, 1, 0])
    assert cindex(-t, t, e)[0] == 1.0
    assert cindex(t, t, e)[0] == 0.0
    assert ece(np.array([0.0, 1.0]), np.array([0, 1]))[0] == 0.0


def test_main_cost():
    from build_dataset_v2 import main_cost
    assert main_cost({"precheck_free": True, "precheck_time_s": 0.1, "cmgrrt_time_s": 12.0}) == 0.1
    assert main_cost({"precheck_free": False, "precheck_time_s": 0.1, "cmgrrt_time_s": 12.0}) == 12.1
