"""Run the adapter on one small ATA multi-part assembly (00089: 3 parts, stacked, with contacts).
Every part is queried at the assembled state; at least one must succeed, all must run without
errors, and the outcome vocabulary must be success/unsolved only (never 'infeasible')."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASM = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly/00089")


def test_contacts_and_candidates():
    from disasm.oracle.cmgrrt import load_assembly, contact_graph, candidate_directions
    a = load_assembly(ASM)
    assert abs(a.scale - 0.2) < 1e-6
    cg = contact_graph(a)
    assert "0-1" in cg["pairs"] and "1-2" in cg["pairs"] and "0-2" not in cg["pairs"]
    names = [n for n, _ in candidate_directions(a, 0, set(a.part_ids))]
    assert names[0] == "contact_normal" and "away_from_1" in names


def test_query_all_parts(tmp_path):
    from disasm.oracle.cmgrrt import load_assembly, query
    a = load_assembly(ASM)
    res = [query(a, set(), p, timeout_s=60, seed=0, workdir=str(tmp_path)) for p in a.part_ids]
    for r in res:
        assert r["error"] is None, r
        assert r["outcome"] in ("success", "unsolved")
    assert any(r["outcome"] == "success" for r in res)
    # removing part 0 leaves a 2-part sub-assembly: part 2 must still be queryable
    r = query(a, {0}, 2, timeout_s=60, seed=0, workdir=str(tmp_path))
    assert r["error"] is None and r["removed"] == [0]
