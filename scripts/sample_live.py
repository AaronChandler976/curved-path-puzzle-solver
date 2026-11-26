#!/usr/bin/env python
"""R6 (run 03): choose the live-evaluation sample of test assemblies (seed fixed).

Up to --max-rot rot_assemblies from the test split (all of them if there are fewer; otherwise a seeded random subset),
then the rest of --n from the non-rot test assemblies, stratified by part-count bin (3-4 / 5-6 / 7-8) in proportion
to the bin sizes in the non-rot test pool (largest-remainder rounding).
"""
import argparse
import json
import os

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def pbin(n):
    return "3-4" if n <= 4 else ("5-6" if n <= 6 else "7-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--max-rot", type=int, default=20)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    test = sorted(json.load(open(os.path.join(ROOT, "data/splits/v1_split.json")))["test"])
    meta = json.load(open(os.path.join(ROOT, "data/processed/run03/asm_meta.json")))
    rng = np.random.default_rng(args.seed)
    rot = [a for a in test if meta[a]["rot_assembly"]]
    non = [a for a in test if not meta[a]["rot_assembly"]]
    rot_sel = sorted(rng.choice(rot, min(args.max_rot, len(rot)), replace=False).tolist())
    k = args.n - len(rot_sel)
    bins = {b: [a for a in non if pbin(meta[a]["n_parts"]) == b] for b in ("3-4", "5-6", "7-8")}
    quota = {b: k * len(v) / len(non) for b, v in bins.items()}
    take = {b: int(np.floor(q)) for b, q in quota.items()}
    for b in sorted(quota, key=lambda b: -(quota[b] - take[b]))[: k - sum(take.values())]:
        take[b] += 1
    non_sel = []
    for b, v in bins.items():
        non_sel += rng.choice(v, take[b], replace=False).tolist()
    sel = sorted(rot_sel + non_sel)
    json.dump(sel, open(args.out, "w"))
    info = {"n": len(sel), "rot_selected": len(rot_sel), "rot_in_test": len(rot), "non_rot_by_bin": take,
            "seed": args.seed, "assemblies": sel}
    json.dump(info, open(args.out.replace(".json", "_info.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in info.items() if k != "assemblies"}))


if __name__ == "__main__":
    main()
