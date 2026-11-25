#!/usr/bin/env python
"""Collect {variant: [ckpt paths of the final seeds]} from <train-dir>/<variant>/selection.json (val-selected)."""
import argparse
import json
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train-dir", required=True)
    ap.add_argument("--variants", default="mlp_bce,mlp_survival,gnn_bce,gnn_survival,gnn_survival_tail,pn_gnn_survival,asap_retrained")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = {}
    for v in a.variants.split(","):
        sel = json.load(open(os.path.join(a.train_dir, v, "selection.json")))
        assert len(sel["seeds"]) == 5, (v, len(sel["seeds"]))
        out[v] = [s["ckpt"] for s in sel["seeds"]]
        for c in out[v]:
            assert os.path.exists(os.path.join(ROOT, c)), c
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
