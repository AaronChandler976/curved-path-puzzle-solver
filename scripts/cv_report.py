#!/usr/bin/env python
"""Campaign Phase 2: summarise the 5-fold group CV (scripts/cv_v2.py) over train+val.

For each variant: pooled ratio = sum over folds of the seed-mean held-out total / sum over folds of fewest contacts'
total; per-fold ratio (seed-mean) and its mean ± std over folds; per-seed pooled ratio mean ± std; rank of the variant
in each fold. Heuristic totals per fold come from the same held-out folds. Held-out folds selected nothing (inner early
stopping), so these numbers are not biased toward the trained models (configs were chosen on val, which lies inside the
folds; reported).
"""
import argparse
import glob
import json
import os
from collections import defaultdict

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cv-dir", required=True)
    ap.add_argument("--md", required=True)
    a = ap.parse_args()
    R = []
    for f in sorted(glob.glob(os.path.join(a.cv_dir, "*", "cv_results.json"))):
        R += json.load(open(f))
    heur = {}
    for r in R:
        if r["variant"] == "heuristics":
            heur[r["fold"]] = r
    folds = sorted(heur)
    byv = defaultdict(lambda: defaultdict(dict))
    for r in R:
        if r["variant"] != "heuristics":
            byv[r["variant"]][r["fold"]][r["seed"]] = r["total"]
    rows = []
    for v, F in byv.items():
        complete = sorted(F) == folds and all(len(F[k]) == len(F[folds[0]]) for k in folds)
        seeds = sorted(F[folds[0]])
        fold_tot = {k: float(np.mean(list(F[k].values()))) for k in F}
        pooled = sum(fold_tot.values()) / sum(heur[k]["fewest_contacts"] for k in F)
        per_fold = [fold_tot[k] / heur[k]["fewest_contacts"] for k in sorted(F)]
        per_seed = [sum(F[k][s] for k in F) / sum(heur[k]["fewest_contacts"] for k in F) for s in seeds if all(s in F[k] for k in F)]
        rows.append({"variant": v, "complete": complete, "folds": sorted(F), "seeds": seeds, "pooled_ratio": pooled,
                     "per_fold_ratio": per_fold, "per_seed_pooled_ratio": per_seed, "fold_totals": fold_tot})
    for name in ("outside_in", "random"):
        rows.append({"variant": name, "complete": True, "folds": folds, "seeds": [],
                     "pooled_ratio": sum(heur[k][name] for k in folds) / sum(heur[k]["fewest_contacts"] for k in folds),
                     "per_fold_ratio": [heur[k][name] / heur[k]["fewest_contacts"] for k in folds], "per_seed_pooled_ratio": []})
    rows.sort(key=lambda r: r["pooled_ratio"])
    L = ["# Phase 2: 5-fold group cross-validation over train+val (robustness check of the val ranking)\n",
         f"Source `{os.path.relpath(a.cv_dir, ROOT)}/*/cv_results.json` (`scripts/cv_v2.py`), summary `scripts/cv_report.py`. "
         "Folds = duplicate groups of train+val (1,675 assemblies), stratified by source and part-count bin; per fold, train "
         "on 3 folds, early-stop on the next fold, replay the held-out fold (which selects nothing). Configs = the "
         "val-chosen ones (val assemblies are inside the folds). Main configuration, logged costs. Ratio < 1 = cheaper than "
         "fewest contacts on the same held-out states. **Registered variants are not re-selected by this; exploratory "
         "variants are marked.** It does not change the registered selection rule.\n",
         "| variant | folds × seeds | pooled ratio vs fewest contacts | per-fold ratios (seed-mean) | mean ± std over folds | per-seed pooled ratio mean ± std |",
         "|---|---|---|---|---|---|"]
    expl = {"gatv2_survival", "gt_survival", "gnn_survival_listnet"}
    for r in rows:
        pf = r["per_fold_ratio"]
        ps = r["per_seed_pooled_ratio"]
        L.append(f"| {r['variant']}{' [expl.]' if r['variant'] in expl else ''}{'' if r['complete'] else ' (INCOMPLETE)'} | "
                 f"{len(r['folds'])} × {len(r['seeds']) or '—'} | {r['pooled_ratio']:.3f} | {', '.join(f'{x:.3f}' for x in pf)} | "
                 f"{np.mean(pf):.3f} ± {np.std(pf, ddof=1):.3f} | "
                 f"{(f'{np.mean(ps):.3f} ± {np.std(ps, ddof=1):.3f}') if len(ps) > 1 else '—'} |")
    L.append("\nHeld-out fold totals for fewest contacts (s): " + ", ".join(f"fold {k}: {heur[k]['fewest_contacts']:.0f}" for k in folds) +
             "; hindsight-optimal: " + ", ".join(f"{heur[k]['optimal']:.0f}" for k in folds) + ".")
    json.dump(rows, open(os.path.join(a.cv_dir, "cv_summary.json"), "w"), indent=1)
    open(a.md, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
