#!/usr/bin/env python
"""R6 (run 03): summarize the live full-disassembly run -> reports/run03/results_live.md.

Per (assembly, method): total planner time (sum of CMG-RRT time_s), planner calls, complete/stuck, wall time incl. setup
(assembly load, SDF/collision setup, ordering inference, planner). Paired comparisons (GNN-Surv minus each other
method) only over assemblies COMPLETED by all methods: paired bootstrap CI over assemblies (10,000, seed 0),
Wilcoxon signed-rank, Holm. Load info at start/end is copied from load_info.txt; idle status from idle_status.txt.
"""
import argparse
import json
import os
from collections import defaultdict

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
METHODS = [("random", "random"), ("fewest_contacts", "fewest contacts"), ("asap", "ASAP GNN (released weights, zero-shot)"),
           ("gnn_surv", "GNN-Surv (p/c), seed 101")]
MAIN = "gnn_surv"


def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); adj = np.empty_like(p); run = 0.0
    for k, i in enumerate(o):
        run = max(run, min(1.0, (len(p) - k) * p[i])); adj[i] = run
    return adj


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default=os.path.join(ROOT, "experiments/2026-11-23_run03_live"))
    ap.add_argument("--out", default=os.path.join(ROOT, "reports/run03/results_live.md"))
    args = ap.parse_args()
    from scipy.stats import wilcoxon
    R = [json.loads(l) for l in open(os.path.join(args.dir, "results.jsonl"))]
    meta = json.load(open(os.path.join(ROOT, "data/processed/run03/asm_meta.json")))
    by = defaultdict(dict)
    for r in R:
        by[r["assembly_id"]][r["method"]] = r
    aids = sorted(by)
    errs = [r for r in R if r.get("error")]
    idle = open(os.path.join(args.dir, "idle_status.txt")).read().strip() if os.path.exists(os.path.join(args.dir, "idle_status.txt")) else "?"
    conf = idle != "idle=1"
    rng = np.random.default_rng(0)
    rel = os.path.relpath(args.dir, ROOT)
    L = ["# Run 03 R6: live full-disassembly evaluation (fresh CMG-RRT queries)\n",
         f"Run folder `{rel}/` (`results.jsonl` = one line per assembly x method with every query; `stdout.log`; "
         f"`load_info.txt`; `idle_wait.log`). Script `scripts/live_abd.py` via `scripts/run_r6.sh`. Exact union-SDF oracle, ε = 0.005, "
         "T = 30 s, 10 planner workers (slots), methods interleaved per assembly, planner seed per query = sha1(assembly, state, part), "
         "identical across methods.\n",
         f"- idle check before start: `{idle}`" + (" -> **all timings CONFOUNDED**" if conf else
                                                  " (load avg < 2 and GPU < 10% for 5 min; see idle_wait.log)") +
         ". During the run the 10 planner workers themselves load the machine; nothing else ran.",
         f"- assemblies: {len(aids)} ({sum(meta[a]['rot_assembly'] for a in aids)} rot_assembly); runs: {len(R)}; runs with errors: {len(errs)}",
         "- caveat: trimesh draws the robot's surface samples with an unseeded generator, and T is a wall-clock limit. "
         "The same query (same seed) can therefore end differently under two methods. These are fresh runs, not replays.\n",
         "## Per-method summary (all sampled assemblies)\n",
         "| method | complete / stuck | total planner time (s) | mean planner s per assembly [95% CI] | planner calls (total) | mean wall s per assembly incl. setup |",
         "|---|---|---|---|---|---|"]
    for m, name in METHODS:
        rs = [by[a][m] for a in aids if m in by[a]]
        pl = np.array([r.get("planner_s", np.nan) for r in rs])
        idx = rng.integers(0, len(pl), (10000, len(pl)))
        ci = np.nanpercentile(np.nanmean(pl[idx], 1), [2.5, 97.5])
        L.append(f"| {name} | {sum(r.get('status') == 'complete' for r in rs)} / {sum(r.get('status') == 'stuck' for r in rs)} | "
                 f"{np.nansum(pl):.0f} | {np.nanmean(pl):.1f} [{ci[0]:.1f}, {ci[1]:.1f}] | {sum(r.get('calls') or 0 for r in rs)} | "
                 f"{np.mean([r['wall_s'] for r in rs]):.1f} |")
    allc = [a for a in aids if all(by[a].get(m, {}).get("status") == "complete" for m, _ in METHODS)]

    def paired(sub, label):
        out = [f"\n## Paired comparison: {label} ({len(sub)} assemblies completed by all methods)\n"]
        if len(sub) < 2:
            return out + ["too few assemblies"]
        if len(sub) < 30:
            out.append(f"**Underpowered** (n = {len(sub)} < 30).\n")
        out += ["GNN-Surv minus each method; total planner time per full disassembly (negative = GNN-Surv cheaper).\n",
                "| vs | GNN-Surv total / other total (s) | mean diff per assembly (s) [95% paired bootstrap CI] | ratio of totals [95% CI] | GNN-Surv wins / ties / losses | Wilcoxon p | Holm p | calls: GNN-Surv / other |",
                "|---|---|---|---|---|---|---|---|"]
        A = np.array([by[a][MAIN]["planner_s"] for a in sub])
        rows, pv = [], []
        for m, name in METHODS:
            if m == MAIN:
                continue
            B = np.array([by[a][m]["planner_s"] for a in sub])
            d = A - B
            idx = rng.integers(0, len(d), (10000, len(d)))
            ci = np.percentile(d[idx].mean(1), [2.5, 97.5])
            rr = np.percentile(A[idx].sum(1) / B[idx].sum(1), [2.5, 97.5])
            try:
                p = float(wilcoxon(A, B).pvalue)
            except ValueError:
                p = 1.0
            pv.append(p)
            ca = sum(by[a][MAIN]["calls"] for a in sub); cb = sum(by[a][m]["calls"] for a in sub)
            rows.append((name, A.sum(), B.sum(), d.mean(), ci, A.sum() / B.sum(), rr,
                         (int((d < -0.01).sum()), int((abs(d) <= 0.01).sum()), int((d > 0.01).sum())), p, ca, cb))
        for (name, a_, b_, md, ci, r, rr, wtl, p, ca, cb), pa in zip(rows, holm(pv)):
            out.append(f"| {name} | {a_:.0f} / {b_:.0f} | {md:+.1f} [{ci[0]:+.1f}, {ci[1]:+.1f}] | {r:.3f} [{rr[0]:.3f}, {rr[1]:.3f}] | "
                       f"{wtl[0]} / {wtl[1]} / {wtl[2]} | {p:.2g} | {pa:.2g} | {ca} / {cb} |")
        return out

    L += paired(allc, "all")
    L += paired([a for a in allc if meta[a]["rot_assembly"]], "rot_assembly subset")
    L += paired([a for a in allc if not meta[a]["rot_assembly"]], "non-rot subset")
    L.append("\n## Load info (start / end)\n\n```")
    L.append(open(os.path.join(args.dir, "load_info.txt")).read().strip())
    L.append("```")
    if errs:
        L.append("\nErrors: " + "; ".join(f"{r['assembly_id']}/{r['method']}: {r['error']}" for r in errs))
    open(args.out, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
