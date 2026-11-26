#!/usr/bin/env python
"""Campaign Phase 3 failure analysis (after the single test evaluation; reads saved outputs, selects nothing).

Inputs: test graphs (data/processed/run05/graphs_test.pt, built by the one test evaluation) and the frozen
GNN-Surv checkpoints (configs/final_frozen.yaml), scored on CPU exactly as in eval_v2.
Outputs:
- tail concentration: share of each ordering's total test cost in its costliest 1% / 5% / 10% of scored states;
- GNN-Surv (val-best seed) vs fewest contacts, state by state: where GNN-Surv paid more, classified by cause:
  * "timeout first": GNN-Surv queried an unsolved part (cost ≈ T) before its first success (wrong p),
  * "slow success": GNN-Surv's first success was slower than fewest contacts' (wrong c, p fine),
  * "failed cheap query": it queried a part that failed quickly first;
- the 10 costliest states for GNN-Surv with predicted p, c and the observed outcome/cost of every part (for renders);
- part-count and source composition of the cost-gap states.
"""
import argparse
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np
import torch
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def first_success(order, t, s):
    c = 0.0
    q = []
    for i in order:
        c += t[i]; q.append(i)
        if s[i]:
            break
    return c, q


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--replay-dir", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--md", required=True)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    from train_v2 import Batcher, build_model, predict
    from disasm.eval.replay3 import heuristic_orders, score_order
    cfg = yaml.safe_load(open(os.path.join(ROOT, "configs/final_frozen.yaml")))
    G = [g for g in torch.load(os.path.join(ROOT, "data/processed/run05/graphs_test.pt"), weights_only=False) if g["succ"].any()]
    best = cfg["val_best_seed"]["gnn_survival"]
    ck = [c["ckpt"] for c in cfg["registered"]["gnn_survival"] if f"seed{best}/" in c["ckpt"]][0]
    d = torch.load(os.path.join(ROOT, ck), weights_only=False, map_location="cpu")
    m = build_model("gnn_survival", d["cfg"], 30.0); m.load_state_dict(d["state_dict"]); m.eval()
    pc = predict(m, G, Batcher([t.cpu() for t in d["norm"]], "cpu"))
    T = 30.0
    # tail concentration from the replay's per-state costs (seed-mean for trained models)
    R = [json.loads(l) for l in open(os.path.join(a.replay_dir, "per_state.jsonl"))]
    R = [r for r in R if r.get("main/n_success")]
    keys = ["random", "outside_in", "fewest_contacts", "asap_zs", "gnn_survival", "pn_gnn_survival", "gnn_survival_tail", "optimal"]
    conc = {}
    for k in keys:
        v = np.sort(np.array([r[f"main/{k}"] for r in R]))[::-1]
        conc[k] = {f"top{p}%": float(v[:max(1, int(round(len(v) * p / 100)))].sum() / v.sum()) for p in (1, 5, 10)}
        conc[k]["total"] = float(v.sum())
    # per-state GNN-Surv (val-best seed) vs fewest contacts
    rows = []
    for (p, c), g in zip(pc, G):
        t, s = g["time_s"].numpy().astype(float), g["succ"].numpy().astype(bool)
        og = score_order(p / np.maximum(c, 1e-3))
        of = heuristic_orders(g)["fewest_contacts"]
        cg, qg = first_success(og, t, s)
        cf, qf = first_success(of, t, s)
        cause = None
        if cg > cf + 0.01:
            fails = [i for i in qg[:-1]]
            if any(t[i] >= T - 1e-6 or (not s[i] and t[i] > 10) for i in fails):
                cause = "timeout first (wrong p)"
            elif fails:
                cause = "failed cheap query first"
            else:
                cause = "slower success (wrong c)"
        rows.append({"aid": g["aid"], "skey": g["skey"], "n_parts": g["n_parts"], "source": g["source"], "n": len(t),
                     "gnn": cg, "fewest": cf, "diff": cg - cf, "cause": cause,
                     "parts": [{"part": int(g["present"][i]), "p": float(p[i]), "c": float(c[i]), "success": bool(s[i]),
                                "cost": float(t[i]), "pre_free": bool(g["pre_free"][i])} for i in range(len(t))],
                     "gnn_order": [int(g["present"][i]) for i in og], "fewest_order": [int(g["present"][i]) for i in of]})
    worse = [r for r in rows if r["cause"]]
    better = [r for r in rows if r["diff"] < -0.01]
    cause_cost = defaultdict(float)
    for r in worse:
        cause_cost[r["cause"]] += r["diff"]
    top = sorted(rows, key=lambda r: -r["gnn"])[:10]
    json.dump({"concentration": conc, "worse": worse, "better_count": len(better), "top10_gnn": top},
              open(os.path.join(a.outdir, "failure_analysis.json"), "w"), indent=1)
    L = ["# Failure analysis on the test set (after the single evaluation; selects nothing)\n",
         f"Script `scripts/failure_analysis.py`; raw `{os.path.relpath(a.outdir, ROOT)}/failure_analysis.json`. Main configuration, "
         f"{len(rows)} scored test states. GNN-Surv = val-best seed {best} (`{ck}`), scored on CPU.\n",
         "## Cost is concentrated in a few states\n",
         "| ordering | total (s) | share in costliest 1% of states | 5% | 10% |", "|---|---|---|---|---|"]
    for k in keys:
        c = conc[k]
        L.append(f"| {k} | {c['total']:.0f} | {c['top1%']:.2f} | {c['top5%']:.2f} | {c['top10%']:.2f} |")
    L += [f"\n## GNN-Surv (seed {best}) vs fewest contacts, state by state\n",
          f"- GNN-Surv cheaper on {len(better)} states (saving {-sum(r['diff'] for r in better):.0f} s), costlier on {len(worse)} "
          f"(losing {sum(r['diff'] for r in worse):.0f} s), equal on {len(rows) - len(better) - len(worse)}.",
          "- Causes of the costlier states (state count, extra seconds):"]
    cc = Counter(r["cause"] for r in worse)
    for k, n in cc.most_common():
        L.append(f"  - {k}: {n} states, +{cause_cost[k]:.0f} s")
    big = sorted(worse, key=lambda r: -r["diff"])[:20]
    L.append(f"- The 20 largest losses: {Counter(r['source'] for r in big)} by source; part counts {sorted(r['n_parts'] for r in big)}.")
    L += ["\n## The 10 costliest states for GNN-Surv\n",
          "| assembly | state (present parts) | n | GNN-Surv cost (s) | fewest contacts (s) | first-queried parts: p, c → outcome, cost |",
          "|---|---|---|---|---|---|"]
    for r in top:
        byp = {x["part"]: x for x in r["parts"]}
        q = "; ".join(f"{pt}: p {byp[pt]['p']:.2f}, c {byp[pt]['c']:.1f} → {'ok' if byp[pt]['success'] else 'unsolved'} {byp[pt]['cost']:.1f}"
                      for pt in r["gnn_order"][:3])
        L.append(f"| {r['aid']} | {r['skey']} | {r['n']} | {r['gnn']:.1f} | {r['fewest']:.1f} | {q} |")
    open(a.md, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
