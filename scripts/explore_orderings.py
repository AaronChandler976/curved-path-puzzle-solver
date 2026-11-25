#!/usr/bin/env python
"""Campaign Phase 2 (exploratory, VAL ONLY): alternative ordering keys and budget policies on top of the trained
survival checkpoints, replayed from logged pilot_v2 query costs (main configuration). No retraining.

Ordering keys (per part; higher first), from the survival curve S_k (K bins, edges e_k):
- pc            p / c                  (registered; c = E[min(t, T)] already includes the (1 - p) T censored mass)
- p             p only
- inv_c         1 / c
- pc_risk{β}    p / (c + β · sd),  sd = std of min(t, T) under the predicted distribution (risk-averse)
- pc_tail{κ}    p / (c + κ (1 - p) T)  (extra weight on the timeout term)
Budget policies (replay-derived, exact for seeded queries up to wall-clock jitter):
- trunc{T'}     pass 1: query in p/c order with budget T' (success iff logged t <= T', cost min(t, T')); if no part
                succeeds, pass 2: the parts not yet solved, in p/c order, at the full budget (cost t, i.e. the T' already
                spent is lost: the seeded planner restarts). T' in {1, 3, 10} s.
Each key/policy is applied to every seed's predictions; per-state cost is the seed-mean, as in eval_v2.
Output: <outdir>/results.json + <md>. Reported as exploratory; nothing here is a registered result.
"""
import argparse
import json
import os
import sys
from collections import defaultdict

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@torch.no_grad()
def curves(var, ck, G, clouds, dev):
    from train_v2 import Batcher, build_model, forward, core, VARIANTS
    d = torch.load(os.path.join(ROOT, ck), weights_only=False, map_location="cpu")
    m = build_model(var, d["cfg"], G[0]["T"]); m.load_state_dict(d["state_dict"]); m.to(dev).eval()
    b = Batcher([t.cpu() for t in d["norm"]], dev, clouds if VARIANTS[var][3] else None)
    out = []
    for i in range(0, len(G), 256):
        bb = b(G[i:i + 256])
        S = core(m).survival_curve(forward(m, bb)).cpu().numpy()
        ptr = bb["ptr"]
        out += [S[ptr[j]:ptr[j + 1]] for j in range(len(ptr) - 1)]
    return out, core(m).edges.cpu().numpy()


def moments(S, edges, T):
    """p, E[min(t,T)], sd[min(t,T)] with uniform event time inside each bin and the censored mass at T."""
    lo = np.concatenate([[0.0], edges[:-1]])
    Sp = np.concatenate([np.ones((S.shape[0], 1)), S[:, :-1]], 1)
    pk = Sp - S                                   # P(event in bin k)
    m1 = (pk * (lo + edges) / 2).sum(1) + S[:, -1] * T
    m2 = (pk * (lo ** 2 + lo * edges + edges ** 2) / 3).sum(1) + S[:, -1] * T ** 2
    return 1 - S[:, -1], m1, np.sqrt(np.maximum(m2 - m1 ** 2, 0.0))


def cost_order(order, t, s):
    tot = 0.0
    for i in order:
        tot += t[i]
        if s[i]:
            return tot
    return tot


def trunc_cost(order, t, s, Tp):
    tot = 0.0
    for i in order:
        if s[i] and t[i] <= Tp:
            return tot + t[i]
        tot += min(t[i], Tp)
    rest = [i for i in order]                      # nothing solved in pass 1 (every part is retried)
    return tot + cost_order(rest, t, s)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--methods", required=True)
    ap.add_argument("--variants", default="gnn_survival,mlp_survival,gnn_survival_tail,pn_gnn_survival")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--md", required=True)
    ap.add_argument("--device", default="cuda")
    a = ap.parse_args()
    from disasm.util.runlog import log_load
    from disasm.eval.replay3 import score_order
    from disasm.eval.stats import paired
    os.makedirs(a.outdir, exist_ok=True)
    log_load(a.outdir, "start")
    P = os.path.join(ROOT, "data/processed/run05")
    G = [g for g in torch.load(os.path.join(P, "graphs_train_val.pt"), weights_only=False) if g["split"] == "val" and g["succ"].any()]
    clouds = torch.load(os.path.join(P, "clouds_train_val.pt"), weights_only=False)
    methods = json.load(open(a.methods))
    T = G[0]["T"]
    keys = {"pc": lambda p, c, sd: p / np.maximum(c, 1e-3), "p": lambda p, c, sd: p, "inv_c": lambda p, c, sd: 1 / np.maximum(c, 1e-3)}
    for beta in (0.5, 1.0, 2.0):
        keys[f"pc_risk{beta:g}"] = (lambda b: lambda p, c, sd: p / np.maximum(c + b * sd, 1e-3))(beta)
    for kap in (0.5, 1.0):
        keys[f"pc_tail{kap:g}"] = (lambda k: lambda p, c, sd: p / np.maximum(c + k * (1 - p) * T, 1e-3))(kap)
    pols = [1.0, 3.0, 10.0]
    res, per_asm = {}, {}
    for var in a.variants.split(","):
        seeds = []
        for ck in methods[var]:
            Sc, edges = curves(var, ck, G, clouds, a.device)
            seeds.append([moments(S, edges, T) for S in Sc])
        for name in list(keys) + [f"trunc{x:g}" for x in pols]:
            st = []
            for gi, g in enumerate(G):
                t, s = g["time_s"].numpy().astype(float), g["succ"].numpy().astype(bool)
                cs = []
                for sd_ in seeds:
                    p, c, sdv = sd_[gi]
                    if name.startswith("trunc"):
                        cs.append(trunc_cost(score_order(p / np.maximum(c, 1e-3)), t, s, float(name[5:])))
                    else:
                        cs.append(cost_order(score_order(keys[name](p, c, sdv)), t, s))
                st.append((g["aid"], float(np.mean(cs)), [float(x) for x in cs]))
            by = defaultdict(float)
            for aid, c, _ in st:
                by[aid] += c
            tot_seeds = [sum(x[2][k] for x in st) for k in range(len(seeds))]
            res[f"{var}/{name}"] = {"total": sum(c for _, c, _ in st), "seed_totals": tot_seeds}
            per_asm[f"{var}/{name}"] = by
        print(var, {k.split("/")[1]: round(v["total"]) for k, v in res.items() if k.startswith(var + "/")}, flush=True)
    # heuristics under the same budget policies (the policy is orthogonal to the ordering; a fair comparison needs both)
    from disasm.eval.replay3 import heuristic_orders
    for hname in ("fewest_contacts", "outside_in"):
        for name in ["pc"] + [f"trunc{x:g}" for x in pols]:
            st = []
            for g in G:
                t, s = g["time_s"].numpy().astype(float), g["succ"].numpy().astype(bool)
                o = heuristic_orders(g)[hname]
                st.append((g["aid"], trunc_cost(o, t, s, float(name[5:])) if name.startswith("trunc") else cost_order(o, t, s)))
            by = defaultdict(float)
            for aid, c in st:
                by[aid] += c
            res[f"{hname}/{name}"] = {"total": sum(c for _, c in st), "seed_totals": [sum(c for _, c in st)] * 2}
            per_asm[f"{hname}/{name}"] = by
    aids = sorted(per_asm[f"{a.variants.split(',')[0]}/pc"])
    L = ["# Phase 2 exploration (VAL only): ordering keys and budget policies\n",
         f"Script `scripts/explore_orderings.py`; raw `{os.path.relpath(a.outdir, ROOT)}/results.json`. {len(G)} val states with ≥ 1 "
         f"success, {len(aids)} assemblies, main configuration, logged costs. **Exploratory, post-registration.** "
         "Paired comparison vs the same variant's registered p/c key (ratio of totals, bootstrap CI over assemblies; HL).\n",
         "| variant / key | total (s, seed-mean) | seeds mean ± std | ratio vs p/c [95% CI] | HL vs p/c (s) | W/T/L |", "|---|---|---|---|---|---|"]
    for k, v in res.items():
        var = k.split("/")[0]
        ref = per_asm[f"{var}/pc"]      # for heuristics, "<h>/pc" = the plain heuristic order at full budget
        pr = paired([per_asm[k][i] for i in aids], [ref[i] for i in aids], 10000, hl_boot=False)
        v["vs_pc"] = pr
        L.append(f"| {k} | {v['total']:.0f} | {np.mean(v['seed_totals']):.0f} ± {np.std(v['seed_totals'], ddof=1):.0f} | "
                 f"{pr['ratio']:.3f} [{pr['ratio_ci'][0]:.3f}, {pr['ratio_ci'][1]:.3f}] | {pr['hl']:+.2f} | {pr['wins']}/{pr['ties']}/{pr['losses']} |")
    L += ["\nSame policy, learned vs heuristic (paired by assembly; the policy is held fixed):\n",
          "| A vs B | ratio of totals [95% CI] | HL (s) | W/T/L | Wilcoxon p (uncorrected) |", "|---|---|---|---|---|"]
    res["_cross"] = []
    for pol in ["pc"] + [f"trunc{x:g}" for x in pols]:
        for var in a.variants.split(","):
            A, B = per_asm[f"{var}/{pol}"], per_asm[f"fewest_contacts/{pol}"]
            pr = paired([A[i] for i in aids], [B[i] for i in aids], 10000, hl_boot=False)
            pr.update({"a": f"{var}/{pol}", "b": f"fewest_contacts/{pol}"}); res["_cross"].append(pr)
            L.append(f"| {var} vs fewest contacts, both {pol} | {pr['ratio']:.3f} [{pr['ratio_ci'][0]:.3f}, {pr['ratio_ci'][1]:.3f}] | "
                     f"{pr['hl']:+.2f} | {pr['wins']}/{pr['ties']}/{pr['losses']} | {pr['p']:.2g} |")
    json.dump(res, open(os.path.join(a.outdir, "results.json"), "w"), indent=1, default=float)
    open(a.md, "w").write("\n".join(L) + "\n")
    log_load(a.outdir, "end")
    print("\n".join(L))


if __name__ == "__main__":
    main()
