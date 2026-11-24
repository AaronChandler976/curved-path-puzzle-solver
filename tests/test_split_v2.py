"""Run 04 T8: v2 split invariants — no duplicate group in two splits, no pilot_v1 assembly in test, 00014 not in test,
test = fresh assemblies only. Synthetic check of make_split + the frozen file if present."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
V2 = os.path.join(ROOT, "data/splits/v2_split.json")


def _check(sp, sources):
    where = {}
    for k in ("train", "val", "test"):
        for a in sp[k]:
            assert a not in where, f"{a} in two splits"
            where[a] = k
    for mem in sp["groups"].values():
        assert len({where[a] for a in mem}) == 1, f"group {mem} split across splits"
    assert all(sources[a] != "v1" for a in sp["test"])
    assert "00014" not in sp["test"]


def test_make_split_synthetic():
    from build_split_v2 import make_split
    meta = {}
    for i in range(400):
        src = "v1" if i < 150 else ("fresh-9to12" if i < 300 else "fresh-allowance")
        meta[f"{i:05d}"] = {"n_parts": 3 + i % 10, "source": src, "exact_key": f"e{i}", "near_key": f"n{i}"}
    meta["00014"]["source"] = "v1"
    meta["00200"]["near_key"] = meta["00003"]["near_key"]     # fresh assembly duplicates a v1 one -> never test
    meta["00350"]["exact_key"] = meta["00250"]["exact_key"]   # two fresh duplicates -> same split
    sp = make_split(meta, seed=0)
    _check(sp, {a: m["source"] for a, m in meta.items()})
    assert "00200" not in sp["test"]
    fresh = [a for a, m in meta.items() if m["source"] != "v1"]
    assert 0.4 < len(sp["test"]) / len(fresh) < 0.6


@pytest.mark.skipif(not os.path.exists(V2), reason="v2 split not built yet")
def test_frozen_v2_split():
    sp = json.load(open(V2))
    _check(sp, sp["sources"])
    v1 = json.load(open(os.path.join(ROOT, "data/splits/v1_split.json")))
    assert not (set(sp["test"]) & (set(v1["train"]) | set(v1["val"]) | set(v1["test"])))
