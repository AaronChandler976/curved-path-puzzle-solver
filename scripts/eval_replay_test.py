#!/usr/bin/env python
"""R5 (run 03): ONE-TIME test-split evaluation by replay of logged v1 queries.

Loads the frozen R3 checkpoints (4 variants x 5 seeds, selected on val) and the R4 ASAP zero-shot scores, and
replays every ordering on every test state (src/disasm/eval/replay3.py). Refuses to run twice (marker file),
so the test split is evaluated exactly once.

Trained models: per-state cost is computed per seed. Tables report the total as mean ± std over the 5 seeds. The CI
and the paired tests use the per-state cost averaged over the 5 seeds (the expected cost of a randomly drawn seed).
Bootstrap: 10,000 resamples of ASSEMBLIES (seed 0). Paired comparisons: GNN-Surv (p/c) minus each other ordering,
per-assembly summed cost; paired bootstrap CI of the mean per-assembly difference; Wilcoxon signed-rank over
assemblies (zero differences dropped, scipy 'wilcox'); Holm correction across the comparisons in each table.
"""
import argparse
import json
import os
import sys
from collections import defaultdict

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VARIANTS = [("mlp_bce", "MLP-BCE (p)", "p"), ("mlp_survival", "MLP-Surv (p/c)", "p_over_c"),
            ("gnn_bce", "GNN-BCE (p)", "p"), ("gnn_survival", "GNN-Surv (p/c)", "p_over_c"),
            ("gnn_survival", "GNN-Surv (p only)", "p")]
FIXED = [("random", "random (exact expectation)"), ("outside_in", "outside-in"), ("fewest_contacts", "fewest contacts"),
         ("asap", "ASAP GNN (released weights, zero-shot)")]
MAIN = "GNN-Surv (p/c)"


def holm(pvals):
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    run = 0.0
    m = len(p)
    for k, i in enumerate(order):
        run = max(run, min(1.0, (m - k) * p[i]))
        adj[i] = run
    return adj


def boot_by_asm(per_asm_vals, stat, rng, B=10000):
    """per_asm_vals: list (per assembly) of arrays of per-state values -> stat over the pooled states."""
    A = len(per_asm_vals)
    idx = rng.integers(0, A, (B, A))
    out = np.empty(B)
    for b in range(B):
        out[b] = stat(np.concatenate([per_asm_vals[i] for i in idx[b]]))
    return float(stat(np.concatenate(per_asm_vals))), float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def cindex(pred_speed, t, event, groups=None):
    """Harrell's C for time-to-success with right censoring. pred_speed: higher = predicted sooner success.
    Comparable pair (i, j): event_i and t_i < t_j. Concordant if speed_i > speed_j (ties = 0.5).
    groups: if given, only pairs within the same group (state) are used."""
    pred_speed, t, event = map(np.asarray, (pred_speed, t, event))
    num = den = 0.0
    if groups is None:
        ug = [np.arange(len(t))]
    else:
        g = np.asarray(groups)
        ug = [np.where(g == k)[0] for k in np.unique(g)]
    for ix in ug:
        s, tt, e = pred_speed[ix], t[ix], event[ix]
        comp = e[:, None] & (tt[:, None] < tt[None, :])
        if not comp.any():
            continue
        d = s[:, None] - s[None, :]
        num += ((d > 0) * comp).sum() + 0.5 * ((d == 0) * comp).sum()
        den += comp.sum()
    return float(num / den) if den else float("nan"), int(den)


def ece(p, y, bins=10):
    p, y = np.asarray(p, float), np.asarray(y, float)
    edges = np.linspace(0, 1, bins + 1)
    e, rows = 0.0, []
    for i in range(bins):
        m = (p >= edges[i]) & ((p < edges[i + 1]) if i < bins - 1 else (p <= 1))
        if m.any():
            e += m.mean() * abs(p[m].mean() - y[m].mean())
            rows.append((float(p[m].mean()), float(y[m].mean()), int(m.sum())))
    return float(e), rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train-dir", default=os.path.join(ROOT, "experiments/2026-11-23_run03_train"))
    ap.add_argument("--asap", default=os.path.join(ROOT, "experiments/2026-11-23_run03_asap/scores.jsonl"))
    ap.add_argument("--graphs", default=os.path.join(ROOT, "data/processed/run03/graphs.pt"))
    ap.add_argument("--split", default=os.path.join(ROOT, "data/splits/v1_split.json"))
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--md", default=os.path.join(ROOT, "reports/run03/results_replay.md"))
    ap.add_argument("--fig-dir", default=os.path.join(ROOT, "reports/run03/figures"))
    ap.add_argument("--seeds", default="0,1,2,3,4")
    ap.add_argument("--boot", type=int, default=10000)
    args = ap.parse_args()
    marker = os.path.join(ROOT, "data/splits/.v1_test_evaluated")
    if os.path.exists(marker):
        raise SystemExit(f"test split already evaluated ({open(marker).read().strip()}); refusing to run again")
    from disasm.models.ranker3 import Ranker3
    from disasm.data.graph import NODE_DIM, EDGE_DIM_V3
    from disasm.eval.replay3 import state_row
    from disasm.util.runlog import log_load
    sys.path.insert(0, os.path.dirname(__file__))
    from train_ranker import collate
    os.makedirs(args.outdir, exist_ok=True)
    log_load(args.outdir, "start")
    G = torch.load(args.graphs, weights_only=False)
    test = set(json.load(open(args.split))["test"])
    TG = [g for g in G if g["aid"] in test]
    open(marker, "w").write(f"evaluated by scripts/eval_replay_test.py -> {os.path.relpath(args.outdir, ROOT)}\n")
    seeds = [int(s) for s in args.seeds.split(",")]
    # ---------- predictions
    preds = defaultdict(dict)      # (variant, seed) -> list of (p, c)
    for var, _, _ in VARIANTS:
        for sd in seeds:
            if (var, sd) in preds:
                continue
            ck = torch.load(os.path.join(args.train_dir, var, f"seed{sd}", "best.pt"), weights_only=False)
            cfg = ck["cfg"]
            m = Ranker3(cfg["enc"], NODE_DIM, EDGE_DIM_V3, cfg["head"], h=cfg["hidden"], layers=cfg["layers"],
                        dropout=cfg["dropout"], K=8, T=TG[0]["T"])
            m.load_state_dict(ck["state_dict"]); m.eval()
            st = ck["norm"]
            out = []
            with torch.no_grad():
                for i in range(0, len(TG), 512):
                    b = TG[i:i + 512]
                    x, ei, ea, s, c, ptr = collate(b, st, "cpu")
                    p, cc = m.predict(m(x, ei, ea))
                    for j in range(len(b)):
                        out.append((p[ptr[j]:ptr[j + 1]].numpy(), None if cc is None else cc[ptr[j]:ptr[j + 1]].numpy()))
            preds[(var, sd)] = out
    asap = {}
    for l in open(args.asap):
        r = json.loads(l)
        if r["assembly_id"] in test:
            asap[(r["assembly_id"], r["state_key"])] = dict(zip(r["present"], r["score"]))
    missing_asap = [(g["aid"], g["skey"]) for g in TG if (g["aid"], g["skey"]) not in asap]
    assert not missing_asap, f"ASAP scores missing for {len(missing_asap)} test states"
    # ---------- per-state rows (one per seed for model orderings)
    rows = []
    for gi, g in enumerate(TG):
        sc = {"asap": np.array([asap[(g["aid"], g["skey"])][p] for p in g["present"]])}
        for var, name, rule in VARIANTS:
            for sd in seeds:
                p, c = preds[(var, sd)][gi]
                sc[f"{name}#s{sd}"] = p if rule == "p" else p / np.maximum(c, 1e-3)
        r = state_row(g, sc)
        if r["n_success"]:
            for _, name, _ in VARIANTS:
                r[name] = float(np.mean([r[f"{name}#s{sd}"] for sd in seeds]))
                r[name + "_q"] = float(np.mean([r[f"{name}#s{sd}_q"] for sd in seeds]))
        rows.append(r)
    with open(os.path.join(args.outdir, "per_state.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    solved = [r for r in rows if r["n_success"]]
    unsolved = [r for r in rows if not r["n_success"]]
    rng = np.random.default_rng(0)
    order_names = [(k, n) for k, n in FIXED[:3]] + [(n, n) for _, n, _ in VARIANTS] + [FIXED[3]] + [("optimal", "hindsight-optimal (lower bound)")]
    results = {}

    def table(subset, label):
        by_asm = defaultdict(list)
        for r in subset:
            by_asm[r["assembly_id"]].append(r)
        aids = sorted(by_asm)
        L = [f"\n### {label}: {len(subset)} states, {len(aids)} assemblies\n",
             "| ordering | total planner time (s) [95% CI] | mean per state (s) [95% CI] | median per-state ratio to optimal [95% CI] | mean queries to first success |",
             "|---|---|---|---|---|"]
        res = {}
        for key, name in order_names:
            per = [np.array([r[key] for r in by_asm[a]]) for a in aids]
            rat = [np.array([r[key] / max(r["optimal"], 1e-9) for r in by_asm[a]]) for a in aids]
            tot = boot_by_asm(per, np.sum, rng, args.boot)
            mu = boot_by_asm(per, np.mean, rng, args.boot)
            md = boot_by_asm(rat, np.median, rng, args.boot)
            q = float(np.mean([r[key + "_q"] for r in subset]))
            seedtxt = ""
            if "#" not in key and any(key == n for _, n, _ in VARIANTS):
                tots = [sum(r[f"{key}#s{sd}"] for r in subset) for sd in seeds]
                seedtxt = f" (seeds: {np.mean(tots):.0f} ± {np.std(tots, ddof=1):.0f})"
                res[key + "_seed_totals"] = tots
            L.append(f"| {name} | {tot[0]:.0f} [{tot[1]:.0f}, {tot[2]:.0f}]{seedtxt} | {mu[0]:.2f} [{mu[1]:.2f}, {mu[2]:.2f}] | "
                     f"{md[0]:.2f} [{md[1]:.2f}, {md[2]:.2f}] | {q:.2f} |")
            res[key] = {"total": tot, "mean": mu, "median_ratio": md, "mean_queries": q}
        # paired comparisons
        L += [f"\nPaired: {MAIN} minus each ordering, per-assembly summed cost (negative = {MAIN} cheaper). "
              f"n = {len(aids)} assemblies.\n",
              "| comparison | mean diff per assembly (s) [95% paired bootstrap CI] | ratio of totals [95% CI] | Wilcoxon p | Holm-adjusted p |",
              "|---|---|---|---|---|"]
        from scipy.stats import wilcoxon
        comps = [(k, n) for k, n in order_names if k not in (MAIN, "optimal")]
        A_main = np.array([sum(r[MAIN] for r in by_asm[a]) for a in aids])
        pv, lines = [], []
        for key, name in comps:
            B_ = np.array([sum(r[key] for r in by_asm[a]) for a in aids])
            d = A_main - B_
            idx = rng.integers(0, len(aids), (args.boot, len(aids)))
            bd = d[idx].mean(1)
            br = A_main[idx].sum(1) / np.maximum(B_[idx].sum(1), 1e-9)
            try:
                p = float(wilcoxon(A_main, B_, zero_method="wilcox").pvalue) if np.any(d != 0) else 1.0
            except ValueError:
                p = 1.0
            pv.append(p)
            lines.append((name, d.mean(), np.percentile(bd, 2.5), np.percentile(bd, 97.5),
                          A_main.sum() / max(B_.sum(), 1e-9), np.percentile(br, 2.5), np.percentile(br, 97.5), p))
        adj = holm(pv)
        for (name, m_, lo, hi, rr, rlo, rhi, p), pa in zip(lines, adj):
            L.append(f"| vs {name} | {m_:+.2f} [{lo:+.2f}, {hi:+.2f}] | {rr:.3f} [{rlo:.3f}, {rhi:.3f}] | {p:.2g} | {pa:.2g} |")
            res["paired_vs_" + name] = {"mean_diff": m_, "ci": [lo, hi], "ratio": rr, "ratio_ci": [rlo, rhi], "p": p, "p_holm": float(pa)}
        return L, res

    L = ["# Run 03 R5: test-split replay results (evaluated once)\n",
         f"Script `scripts/eval_replay_test.py`; outputs `{os.path.relpath(args.outdir, ROOT)}/` (per-state costs in "
         "`per_state.jsonl`, all numbers in `results.json`). Checkpoints: "
         f"`{os.path.relpath(args.train_dir, ROOT)}/<variant>/seed<k>/best.pt`, seeds {args.seeds} (selected on val). ASAP scores: `experiments/2026-11-23_run03_asap/scores.jsonl`. Cost = logged CMG-RRT planner time "
         "(time_s) of the queries an ordering makes at a state, up to and including the first success. This replays real logged "
         "queries; nothing is simulated.\n",
         f"- test split: {len(TG)} states over {len(test)} assemblies; **{len(solved)}** states with >= 1 success are scored; "
         f"{len(unsolved)} states have no success. Every ordering pays all of their queries there: {sum(r['total_s'] for r in unsolved):.0f} s in total.",
         "- trained models: 5 seeds each (configs chosen on val, `<train-dir>/<variant>/selection.json`). "
         "The total is shown with its CI over the seed-averaged per-state cost; 'seeds:' gives mean ± std of the 5 per-seed totals.",
         "- CIs: bootstrap over assemblies (10,000 resamples). Ratios use hindsight-optimal = cheapest successful query at the state.\n",
         "## Main table (all test states with >= 1 success)"]
    l1, results["all"] = table(solved, "All states")
    L += l1
    rot = [r for r in solved if r["rot_state"]]
    nonrot = [r for r in solved if not r["rot_state"]]
    L.append("\n## Rotation subsets (rot_state from R1; evaluation-only flag)")
    if len(rot) < 30:
        L.append(f"\n**Underpowered:** only {len(rot)} rot_state test states (< 30).")
    l2, results["rot"] = table(rot, "rot_state states" + (" (UNDERPOWERED, n < 30)" if len(rot) < 30 else ""))
    l3, results["nonrot"] = table(nonrot, "non-rot states")
    L += l2 + l3
    # ---------- calibration and prediction quality
    L.append("\n## Calibration and prediction quality (test nodes, all test states)\n")
    L.append("ECE: 10 equal-width bins of p against the observed success. C-index (Harrell, censored): a pair is comparable when "
             "part i succeeded at t_i < t_j. The predicted 'speed' is p for BCE heads and −c (expected cost) for survival heads. "
             "'within-state' uses only pairs at the same state, which is what an ordering needs. Values are mean ± std over the 5 seeds.\n")
    L.append("| model | head | ECE of p | C-index (pooled) | C-index (within-state) |\n|---|---|---|---|---|")
    yy = np.concatenate([g["succ"].numpy() for g in TG]).astype(bool)
    tt = np.concatenate([g["cens_t"].numpy() for g in TG])
    grp = np.concatenate([[i] * len(g["present"]) for i, g in enumerate(TG)])
    calib = {}
    for var in ["mlp_bce", "mlp_survival", "gnn_bce", "gnn_survival"]:
        E, C1, C2, rel = [], [], [], None
        for sd in seeds:
            pr = preds[(var, sd)]
            p = np.concatenate([a for a, _ in pr])
            speed = p if pr[0][1] is None else -np.concatenate([c for _, c in pr])
            e, rel_ = ece(p, yy)
            E.append(e); C1.append(cindex(speed, tt, yy)[0]); C2.append(cindex(speed, tt, yy, grp)[0])
            if sd == seeds[0]:
                rel = rel_
        calib[var] = {"ece": E, "c_pooled": C1, "c_within": C2, "reliability_seed0": rel}
        L.append(f"| {var.split('_')[0].upper()} | {var.split('_')[1]} | {np.mean(E):.3f} ± {np.std(E, ddof=1):.3f} | "
                 f"{np.mean(C1):.3f} ± {np.std(C1, ddof=1):.3f} | {np.mean(C2):.3f} ± {np.std(C2, ddof=1):.3f} |")
    pa = np.concatenate([[asap[(g["aid"], g["skey"])][p] for p in g["present"]] for g in TG])
    e_a, rel_a = ece(pa, yy)
    calib["asap"] = {"ece": e_a, "c_pooled": cindex(pa, tt, yy)[0], "c_within": cindex(pa, tt, yy, grp)[0], "reliability": rel_a}
    L.append(f"| ASAP (zero-shot; its score is P(part is the next removed), not P(planner success)) | BCE | {e_a:.3f} | "
             f"{calib['asap']['c_pooled']:.3f} | {calib['asap']['c_within']:.3f} |")
    results["calibration"] = calib
    results["n"] = {"test_states": len(TG), "solved_states": len(solved), "unsolved_states": len(unsolved),
                    "rot_states": len(rot), "nonrot_states": len(nonrot), "test_assemblies": len(test),
                    "unsolved_total_s": sum(r["total_s"] for r in unsolved)}
    # ---------- figures
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        os.makedirs(args.fig_dir, exist_ok=True)
        fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), gridspec_kw={"width_ratios": [1.4, 1, 1]})
        names = [n for _, n in order_names]
        keys = [k for k, _ in order_names]
        for ax, sub, title in ((axes[0], "all", f"All test states (n={len(solved)})"),
                               (axes[1], "rot", f"rot_state (n={len(rot)})"), (axes[2], "nonrot", f"non-rot (n={len(nonrot)})")):
            tot = [results[sub][k]["total"] for k in keys]
            y = np.arange(len(keys))
            col = ["#B0B0B0" if k in ("random", "outside_in", "fewest_contacts", "asap") else
                   ("#555555" if k == "optimal" else ("#C44E52" if k == MAIN else "#4C72B0")) for k in keys]
            ax.barh(y, [t[0] for t in tot], color=col,
                    xerr=[[t[0] - t[1] for t in tot], [t[2] - t[0] for t in tot]], capsize=2, error_kw={"lw": 0.8})
            ax.set_yticks(y); ax.set_yticklabels(names if sub == "all" else [""] * len(names), fontsize=8)
            ax.invert_yaxis(); ax.set_xlabel("total planner time over test states (s)"); ax.set_title(title, fontsize=10)
            ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        fig.savefig(os.path.join(args.fig_dir, "replay_test_totals.png"), dpi=130); plt.close(fig)
        fig, ax = plt.subplots(1, 1, figsize=(4.8, 4.6))
        ax.plot([0, 1], [0, 1], color="#999999", lw=1, ls="--")
        for var, colr in (("mlp_bce", "#8172B3"), ("mlp_survival", "#64B5CD"), ("gnn_bce", "#4C72B0"), ("gnn_survival", "#C44E52")):
            rel = calib[var]["reliability_seed0"]
            ax.plot([r[0] for r in rel], [r[1] for r in rel], marker="o", ms=3, color=colr,
                    label=f"{var} (ECE {np.mean(calib[var]['ece']):.3f})")
        ax.plot([r[0] for r in rel_a], [r[1] for r in rel_a], marker="s", ms=3, color="#937860", label=f"ASAP zero-shot (ECE {e_a:.3f})")
        ax.set_xlabel("predicted P(success by T)"); ax.set_ylabel("observed success rate"); ax.legend(frameon=False, fontsize=7)
        ax.set_title("Reliability (test nodes, seed 0)", fontsize=10); ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout(); fig.savefig(os.path.join(args.fig_dir, "reliability_test.png"), dpi=130); plt.close(fig)
        L.append("\n![totals](figures/replay_test_totals.png)\n\n![reliability](figures/reliability_test.png)")
    except Exception as e:  # noqa: BLE001
        L.append(f"\n(plot failed: {e})")
    json.dump(results, open(os.path.join(args.outdir, "results.json"), "w"), indent=1, default=float)
    os.makedirs(os.path.dirname(args.md), exist_ok=True)
    open(args.md, "w").write("\n".join(L) + "\n")
    log_load(args.outdir, "end")
    print("\n".join(L))


if __name__ == "__main__":
    main()
