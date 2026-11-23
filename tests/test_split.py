"""Run 03 R2 gate: the frozen split is assembly- and group-disjoint and covers every labelled assembly."""
import json
import os

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPLIT = os.path.join(ROOT, "data/splits/v1_split.json")


@pytest.mark.skipif(not os.path.exists(SPLIT), reason="split not built")
def test_split_disjoint():
    s = json.load(open(SPLIT))
    tr, va, te = set(s["train"]), set(s["val"]), set(s["test"])
    assert not (tr & va) and not (tr & te) and not (va & te)
    g_of = {a: g for g, mem in s["groups"].items() for a in mem}
    assert set(g_of) == tr | va | te
    for name, A in (("train", tr), ("val", va), ("test", te)):
        others = (tr | va | te) - A
        assert not ({g_of[a] for a in A} & {g_of[a] for a in others}), f"group crosses split ({name})"


@pytest.mark.skipif(not os.path.exists(SPLIT), reason="split not built")
def test_split_covers_labels():
    s = json.load(open(SPLIT))
    lab = os.path.join(ROOT, "data/labels/pilot_v1/labels.jsonl")
    if not os.path.exists(lab):
        pytest.skip("labels not present")
    aids = {json.loads(l)["assembly_id"] for l in open(lab)}
    assert aids == set(s["train"]) | set(s["val"]) | set(s["test"])
