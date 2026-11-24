#!/usr/bin/env python
"""Run 04 T2.1: edge agreement between ASAP's own redmax contact graph and (a) our run 03 ASAP adapter
(asap_baseline.asap_contact_pairs: same predicate min(d_ab, d_ba) < 0.1 raw, exact per-part SDFs) and (b) our own
contact graph (cmgrrt.contact_graph, |d| < 0.01 unit frame at 3,000 samples; the GNN's input graph)."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--asap", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from disasm.oracle.cmgrrt import load_assembly, contact_graph
    from disasm.search.asap_baseline import asap_contact_pairs
    rows, tot = [], {"adapter": [0, 0, 0], "ours": [0, 0, 0]}   # [both, asap_only, other_only]
    for l in open(a.asap):
        r = json.loads(l)
        if r["error"]:
            continue
        asm = load_assembly(os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly", r["assembly_id"]))
        A = {tuple(e) for e in r["edges"]}
        B = {tuple(sorted(p)) for p in asap_contact_pairs(asm)}
        C = {tuple(sorted(map(int, k.split("-")))) for k in contact_graph(asm)["pairs"]}
        row = {"assembly_id": r["assembly_id"], "n_parts": len(asm.part_ids), "asap": len(A)}
        for name, X in (("adapter", B), ("ours", C)):
            both, ao, oo = len(A & X), len(A - X), len(X - A)
            tot[name][0] += both; tot[name][1] += ao; tot[name][2] += oo
            row[name] = {"edges": len(X), "both": both, "asap_only": sorted(A - X), "other_only": sorted(X - A),
                         "identical": A == X}
        rows.append(row)
    summ = {}
    for name, (b, ao, oo) in tot.items():
        summ[name] = {"edges_both": b, "asap_only": ao, "other_only": oo, "jaccard": b / max(1, b + ao + oo),
                      "assemblies_identical": sum(r[name]["identical"] for r in rows), "n_assemblies": len(rows)}
    json.dump({"summary": summ, "rows": rows}, open(a.out, "w"), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
