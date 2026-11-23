#!/usr/bin/env python
"""R5 supplement (run 03): direction and concentration of the paired test differences, computed from the STORED
one-time test results (experiments/2026-11-23_run03_eval_test/per_state.jsonl). No model is re-run and no
choice depends on it. Wilcoxon p-values do not show direction, so this adds, per comparison with GNN-Surv (p/c):
win/tie/loss counts over assemblies, the Hodges-Lehmann estimate (median of Walsh averages) of the per-assembly
difference with a bootstrap CI, and how much of each ordering's total comes from the 5% most expensive states.
"""
import argparse
import json
import os
from collections import defaultdict

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAIN = "GNN-Surv (p/c)"
KEYS = [("random", "random"), ("outside_in", "outside-in"), ("fewest_contacts", "fewest contacts"),
        ("MLP-BCE (p)", "MLP-BCE (p)"), ("MLP-Surv (p/c)", "MLP-Surv (p/c)"), ("GNN-BCE (p)", "GNN-BCE (p)"),
        ("GNN-Surv (p only)", "GNN-Surv (p only)"), ("asap", "ASAP (zero-shot)")]


def hl(d):
    d = np.asarray(d)
    w = (d[:, None] + d[None, :]) / 2
    return float(np.median(w[np.triu_indices(len(d))]))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--per-state", default=os.path.join(ROOT, "experiments/2026-11-23_run03_eval_test/per_state.jsonl"))
    ap.add_argument("--out", default=os.path.join(ROOT, "reports/run03/results_replay_supp.md"))
    args = ap.parse_args()
    rows = [json.loads(l) for l in open(args.per_state)]
    rows = [r for r in rows if r["n_success"]]
    rng = np.random.default_rng(0)
    L = ["# Run 03 R5 supplement: direction of the paired test differences\n",
         f"Computed by `scripts/replay_supp.py` from the stored one-time test results `{os.path.relpath(args.per_state, ROOT)}` "
         "(no re-evaluation). Per-assembly cost = sum over that assembly's test states with >= 1 success; trained models use the "
         "5-seed average. HL = Hodges-Lehmann estimate of the per-assembly difference (GNN-Surv minus other; negative = "
         "GNN-Surv cheaper), with a bootstrap 95% CI (2,000 resamples over assemblies). A win means GNN-Surv is cheaper by more than 0.01 s.\n"]
    for sub, sel in (("All states", lambda r: True), ("rot_state states (n < 100 states; underpowered)", lambda r: r["rot_state"]),
                     ("non-rot states", lambda r: not r["rot_state"])):
        S = [r for r in rows if sel(r)]
        by = defaultdict(list)
        for r in S:
            by[r["assembly_id"]].append(r)
        aids = sorted(by)
        A = np.array([sum(r[MAIN] for r in by[a]) for a in aids])
        L += [f"\n## {sub}: {len(S)} states, {len(aids)} assemblies\n",
              "| vs | GNN-Surv wins / ties / losses (assemblies) | HL per-assembly diff (s) [95% CI] | mean diff (s) |", "|---|---|---|---|"]
        for k, name in KEYS:
            B = np.array([sum(r[k] for r in by[a]) for a in aids])
            d = A - B
            w, l = int((d < -0.01).sum()), int((d > 0.01).sum())
            idx = rng.integers(0, len(d), (2000, len(d)))
            bs = [hl(d[i]) for i in idx]
            L.append(f"| {name} | {w} / {len(d) - w - l} / {l} | {hl(d):+.2f} [{np.percentile(bs, 2.5):+.2f}, "
                     f"{np.percentile(bs, 97.5):+.2f}] | {d.mean():+.2f} |")
        L += ["\nShare of each ordering's total from its 5% most expensive states (heavy tail):\n",
              "| ordering | top-5% states' share of total |", "|---|---|"]
        for k, name in [(MAIN, MAIN)] + KEYS:
            c = np.sort([r[k] for r in S])[::-1]
            L.append(f"| {name} | {c[: max(1, int(0.05 * len(c)))].sum() / c.sum():.2f} |")
    open(args.out, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
