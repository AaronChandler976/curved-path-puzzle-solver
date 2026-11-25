#!/usr/bin/env python
"""Run 05 replay evaluation on v2 (docs/PREREG_run05.md §4, §5, §7), for --split val (Phase 1/2) or test (Phase 3).

TEST DISCIPLINE: with --split test this script refuses to run if data/splits/.v2_test_evaluated exists, and writes the
marker BEFORE it reads any test label (it then builds the test graphs itself). It can therefore run on test once.

Methods (--methods json: {"<variant>": ["ckpt", ...] x 5 seeds, ...}; keys = train_v2.VARIANTS or "asap_retrained"):
untrained random (exact expectation), outside-in, fewest contacts, ASAP zero-shot (released weights, redmax contact
graph), hindsight-optimal (lower bound); every trained variant x its seeds.
Replay: cost of an ordering at a state = sum of logged query costs up to and including the first success, for each
oracle configuration: MAIN (pre-check -> CMG-RRT: succ, time_s) and CMG-RRT-only (succ_cm, time_cm). Scored states: >= 1
success under that configuration (others cost the same under every ordering; reported separately).
A trained variant's per-state cost is its seed-mean (PREREG §5); totals are also given as mean ± std over seeds.
Comparisons: GNN-Surv vs the 9 registered baselines/variants + 2 intervention pairs (GNN-BCE vs MLP-BCE,
MLP-Surv vs MLP-BCE): one Holm family of 11 per configuration. Ratio of totals and HL difference with bootstrap CIs by
assembly (10,000 resamples, seed 0; HL CI 2,000), wins/ties/losses, two-sided Wilcoxon.
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from collections import defaultdict

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MARKER = os.path.join(ROOT, "data/splits/.v2_test_evaluated")
NAMES = {"random": "random (expectation)", "outside_in": "outside-in", "fewest_contacts": "fewest contacts",
         "asap_zs": "ASAP zero-shot", "asap_retrained": "ASAP-retrained", "mlp_bce": "MLP-BCE (p)",
         "mlp_survival": "MLP-Surv (p/c)", "gnn_bce": "GNN-BCE (p)", "gnn_survival": "GNN-Surv (p/c)",
         "gnn_survival_tail": "GNN-Surv-Tail (p/c)", "pn_gnn_survival": "PN-GNN-Surv (p/c)",
         "optimal": "hindsight-optimal (lower bound)"}
MAIN = "gnn_survival"
COMPARISONS = [(MAIN, b) for b in ("random", "outside_in", "fewest_contacts", "asap_zs", "asap_retrained", "mlp_survival",
                                   "gnn_bce", "gnn_survival_tail", "pn_gnn_survival")] + \
              [("gnn_bce", "mlp_bce"), ("mlp_survival", "mlp_bce")]
CONFIGS = {"main": ("succ", "time_s"), "cmgrrt_only": ("succ_cm", "time_cm")}


def pbin(n):
    return "3-4" if n <= 4 else "5-6" if n <= 6 else "7-8" if n <= 8 else "9-10" if n <= 10 else "11-12"


def model_scores(var, ckpts, graphs, clouds, dev):
    """-> list over seeds of list over graphs of (score, p, c or None)."""
    from train_v2 import Batcher, build_model, predict, order_score, VARIANTS
    out = []
    for ck in ckpts:
        d = torch.load(os.path.join(ROOT, ck), weights_only=False, map_location="cpu")
        assert d["variant"] == var, (ck, d["variant"], var)
        m = build_model(var, d["cfg"], graphs[0]["T"])
        m.load_state_dict(d["state_dict"]); m.to(dev).eval()
        b = Batcher([t.to("cpu") for t in d["norm"]], dev, clouds if VARIANTS[var][3] else None)
        rule = "p" if VARIANTS[var][1] == "bce" else "p_over_c"
        out.append([(order_score(p, c, rule), p, c) for p, c in predict(m, graphs, b)])
    return out


def asap_model_scores(models, graphs, C, dev):
    from train_asap_v2 import make_data, predict
    data = make_data(graphs, C, False)
    res = []
    for m in models:
        m.to(dev).eval()
        res.append([(s, s, None) for s in predict(m, data, dev)])
    return res


def cost_of_order(order, t, s):
    tot, n = 0.0, 0
    for i in order:
        tot += float(t[i]); n += 1
        if s[i]:
            break
    return tot, n


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", required=True, choices=["val", "test"])
    ap.add_argument("--methods", required=True, help="json {variant: [ckpt paths]}")
    ap.add_argument("--redmax", required=True, help="asap_contact_graphs.py jsonl covering the split's assemblies")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--md", required=True)
    ap.add_argument("--fig-dir", required=True)
    ap.add_argument("--graphs", default=None, help="default data/processed/run05/graphs_<split>.pt (val: graphs_train_val.pt)")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--procs", type=int, default=10)
    ap.add_argument("--best-heuristic-val", default="", choices=["", "outside_in", "fewest_contacts"],
                    help="PREREG §7: the best heuristic chosen on VAL (required with --split test)")
    ap.add_argument("--sensitivity", default=os.path.join(ROOT, "experiments/2026-11-24_run04_t8_split/t6_test_overlap.json"),
                    help="PREREG_addendum §A: json with 'clean_test'; the §7 rule is also evaluated on those assemblies (test only)")
    a = ap.parse_args()
    if a.split == "test" and not a.best_heuristic_val:
        raise SystemExit("--best-heuristic-val is required with --split test (PREREG §7: chosen on val)")
    os.makedirs(a.outdir, exist_ok=True)
    from disasm.util.runlog import log_load
    log_load(a.outdir, "start")
    P = os.path.join(ROOT, "data/processed/run05")
    if a.split == "test":
        if os.path.exists(MARKER):
            raise SystemExit(f"v2 test already evaluated ({open(MARKER).read().strip()}); refusing to run again")
        git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
        open(MARKER, "w").write(f"{dt.datetime.now().isoformat()} first read of v2 test labels by scripts/eval_v2.py "
                                f"-> {os.path.relpath(a.outdir, ROOT)} (git {git})\n")
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts/build_dataset_v2.py"), "--splits", "test", "--clouds",
                        "--procs", str(a.procs)], check=True)
        gpath, cpath = a.graphs or os.path.join(P, "graphs_test.pt"), os.path.join(P, "clouds_test.pt")
    else:
        gpath, cpath = a.graphs or os.path.join(P, "graphs_train_val.pt"), os.path.join(P, "clouds_train_val.pt")
    G = [g for g in torch.load(gpath, weights_only=False) if g["split"] == a.split]
    methods = json.load(open(a.methods))
    clouds = torch.load(cpath, weights_only=False) if "pn_gnn_survival" in methods else None
    from train_asap_v2 import load_inputs
    C = load_inputs({g["aid"] for g in G}, a.redmax, os.path.join(P, f"asap_inputs_{a.split}.pt"), a.procs)
    # ------------------------------------------------------------------ scores
    S = {}            # method -> list over seeds of per-graph (score, p, c)
    from disasm.search.asap_baseline import load_asap_model
    zs, zs_meta = load_asap_model()
    S["asap_zs"] = asap_model_scores([zs], G, C, a.device)
    for var, cks in methods.items():
        if var == "asap_retrained":
            from disasm.models.asap_train import new_asap_model
            ms = []
            for ck in cks:
                m = new_asap_model(0)
                m.load_state_dict(torch.load(os.path.join(ROOT, ck), weights_only=False, map_location="cpu")["model_state_dict"])
                ms.append(m)
            S[var] = asap_model_scores(ms, G, C, a.device)
        else:
            S[var] = model_scores(var, cks, G, clouds, a.device)
    trained = list(methods)
    # ------------------------------------------------------------------ per-state rows
    from disasm.eval.replay3 import heuristic_orders, random_expectation, score_order
    rows = []
    for gi, g in enumerate(G):
        r = {"assembly_id": g["aid"], "state_key": g["skey"], "n": len(g["present"]), "source": g["source"],
             "n_parts": g["n_parts"], "rot_state": bool(g["rot_state"])}
        ho = heuristic_orders(g)
        for cf, (sk, tk) in CONFIGS.items():
            s, t = g[sk].numpy().astype(bool), g[tk].numpy().astype(float)
            r[f"{cf}/n_success"] = int(s.sum()); r[f"{cf}/total_s"] = float(t.sum())
            if not s.any():
                continue
            r[f"{cf}/random"], r[f"{cf}/random_q"] = random_expectation(t, s)
            for k, o in ho.items():
                r[f"{cf}/{k}"], r[f"{cf}/{k}_q"] = cost_of_order(o, t, s)
            r[f"{cf}/optimal"], r[f"{cf}/optimal_q"] = float(t[s].min()), 1
            for m in ["asap_zs"] + trained:
                cs = [cost_of_order(score_order(S[m][k][gi][0]), t, s) for k in range(len(S[m]))]
                r[f"{cf}/{m}#seeds"] = [c for c, _ in cs]
                r[f"{cf}/{m}"] = float(np.mean([c for c, _ in cs])); r[f"{cf}/{m}_q"] = float(np.mean([q for _, q in cs]))
        rows.append(r)
    with open(os.path.join(a.outdir, "per_state.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    from disasm.eval.stats import boot_stat_by_asm, cindex, ece, holm, paired
    order = ["random", "outside_in", "fewest_contacts", "asap_zs"] + trained + ["optimal"]
    results = {"split": a.split, "n_states": len(G), "n_assemblies": len({g["aid"] for g in G}),
               "methods": methods, "asap_zero_shot_ckpt": zs_meta, "configs": {}}
    L = [f"# Run 05 replay on v2 **{a.split}** ({dt.date.today().isoformat()})\n",
         f"Script `scripts/eval_v2.py`; raw per-state costs `{os.path.relpath(a.outdir, ROOT)}/per_state.jsonl`, all numbers "
         f"`{os.path.relpath(a.outdir, ROOT)}/results.json`. Graphs `{os.path.relpath(gpath, ROOT)}` ({len(G)} {a.split} states, "
         f"{results['n_assemblies']} assemblies). Replay of logged pilot_v2 queries (nothing simulated). Trained variants: "
         "per-state cost = mean over their seeds; 'seeds' = mean ± std of the per-seed totals. CIs: bootstrap over assemblies "
         f"({a.boot} resamples, seed 0).\n"]

    def per_asm(sub, key):
        by = defaultdict(float)
        for r in sub:
            by[r["assembly_id"]] += r[key]
        return by

    def table(sub, cf, label, full=True):
        aids = sorted({r["assembly_id"] for r in sub})
        res = {"n_states": len(sub), "n_assemblies": len(aids), "underpowered": len(aids) < 30}
        L.append(f"\n#### {label}: {len(sub)} states, {len(aids)} assemblies" + (" — **UNDERPOWERED (< 30 assemblies), no conclusion**" if len(aids) < 30 else "") + "\n")
        hdr = "| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |"
        if full:
            hdr += " median per-state ratio to optimal [95% CI] | mean queries to 1st success | states solved within T |"
        L.append(hdr); L.append("|---" * (hdr.count("|") - 1) + "|")
        by_asm = defaultdict(list)
        for r in sub:
            by_asm[r["assembly_id"]].append(r)
        for m in order:
            key = f"{cf}/{m}"
            per = [np.array([r[key] for r in by_asm[x]]) for x in aids]
            tot = boot_stat_by_asm(per, np.sum, a.boot)
            e = {"total": tot}
            seedtxt = ""
            if m in trained:
                st = [sum(r[key + "#seeds"][k] for r in sub) for k in range(len(S[m]))]
                e["seed_totals"] = st
                seedtxt = f"{np.mean(st):.0f} ± {np.std(st, ddof=1) if len(st) > 1 else 0:.0f} (n={len(st)})"
            line = f"| {NAMES[m]} | {tot[0]:.0f} [{tot[1]:.0f}, {tot[2]:.0f}] | {seedtxt} |"
            if full:
                rat = [np.array([r[key] / max(r[f'{cf}/optimal'], 1e-9) for r in by_asm[x]]) for x in aids]
                md = boot_stat_by_asm(rat, np.median, min(a.boot, 2000))
                q = float(np.mean([r[key + "_q"] for r in sub]))
                if m in trained:
                    solv = float(np.mean([np.mean(np.array(r[key + "#seeds"]) <= 30.0) for r in sub]))
                else:
                    solv = float(np.mean([r[key] <= 30.0 for r in sub]))
                e.update({"median_ratio_to_optimal": md, "mean_queries": q, "solved_within_T": solv})
                line += f" {md[0]:.2f} [{md[1]:.2f}, {md[2]:.2f}] | {q:.2f} | {solv:.3f} |"
            L.append(line)
            res[m] = e
        return res, by_asm, aids

    def comparisons(sub, cf, label):
        aids = sorted({r["assembly_id"] for r in sub})
        out, pv = [], []
        for x, y in COMPARISONS:
            avail = set(S) | {"random", "outside_in", "fewest_contacts"}
            if x not in avail or y not in avail:
                continue
            ax, ay = per_asm(sub, f"{cf}/{x}"), per_asm(sub, f"{cf}/{y}")
            pr = paired([ax[i] for i in aids], [ay[i] for i in aids], a.boot)
            pr.update({"a": x, "b": y})
            out.append(pr); pv.append(pr["p"])
        for pr, ph in zip(out, holm(pv)):
            pr["p_holm"] = float(ph)
        L.append(f"\nPaired per assembly ({label}; Holm family of {len(out)}; ratio = A/B of totals; HL = Hodges–Lehmann median "
                 f"difference A − B per assembly, negative = A cheaper; W/T/L for A, tie |d| ≤ 0.01 s):\n")
        L.append("| A vs B | ratio of totals [95% CI] | HL diff (s) [95% CI] | W / T / L | Wilcoxon p | Holm p |")
        L.append("|---|---|---|---|---|---|")
        for pr in out:
            L.append(f"| {NAMES[pr['a']]} vs {NAMES[pr['b']]} | {pr['ratio']:.3f} [{pr['ratio_ci'][0]:.3f}, {pr['ratio_ci'][1]:.3f}] | "
                     f"{pr['hl']:+.2f} [{pr['hl_ci'][0]:+.2f}, {pr['hl_ci'][1]:+.2f}] | {pr['wins']} / {pr['ties']} / {pr['losses']} | "
                     f"{pr['p']:.2g} | {pr['p_holm']:.2g} |")
        return out

    for cf in CONFIGS:
        sc = [r for r in rows if r.get(f"{cf}/n_success")]
        un = [r for r in rows if not r.get(f"{cf}/n_success")]
        L.append(f"\n## Configuration: {'MAIN (pre-check → CMG-RRT)' if cf == 'main' else 'CMG-RRT only (secondary)'}\n")
        L.append(f"Scored states: {len(sc)}; states with no success under this configuration: {len(un)} "
                 f"(every ordering pays all their queries: {sum(r[f'{cf}/total_s'] for r in un):.0f} s, not in the totals).")
        cres = {"n_scored": len(sc), "n_unscored": len(un), "unscored_total_s": sum(r[f"{cf}/total_s"] for r in un)}
        cres["all"], _, _ = table(sc, cf, "All scored states")
        cres["paired"] = comparisons(sc, cf, "all scored states")
        # PREREG §7: on test the best heuristic is the one chosen on VAL (main config), passed in; on val it is computed
        heur = a.best_heuristic_val if a.split == "test" else \
            min(("outside_in", "fewest_contacts"), key=lambda k: results["configs"].get("main", cres)["all"][k]["total"][0])
        cres["best_heuristic"] = heur
        if MAIN in S:
            ax, ay = per_asm(sc, f"{cf}/{MAIN}"), per_asm(sc, f"{cf}/{heur}")
            aids = sorted(ax)
            pr = paired([ax[i] for i in aids], [ay[i] for i in aids], a.boot)
            cres["vs_best_heuristic"] = pr
            ph = next((q["p_holm"] for q in cres["paired"] if q["b"] == heur and q["a"] == MAIN), None)
            ca = pr["ratio_ci"][1] < 1.0
            cb = ph is not None and ph < 0.05 and pr["hl"] < 0
            cres["decision_rule_s7"] = {"best_heuristic": heur, "a_ratio_ci_below_1": ca, "b_holm_wilcoxon_and_hl": cb,
                                        "verdict": "beats" if (ca and cb) else ("cheaper on the typical assembly, not on total time" if cb else "does not beat")}
            L.append(f"\n**§7 rule ({a.split}, {cf}):** best heuristic on this split = {NAMES[heur]}; GNN-Surv / heuristic = "
                     f"{pr['ratio']:.3f} [{pr['ratio_ci'][0]:.3f}, {pr['ratio_ci'][1]:.3f}], HL {pr['hl']:+.2f} s, Holm p "
                     f"{ph if ph is None else f'{ph:.2g}'} → (a) {ca}, (b) {cb}: **{cres['decision_rule_s7']['verdict']}**"
                     + (" (val: development only; the registered rule applies to test)" if a.split == "val" else ""))
        # PREREG_addendum §A: §7 on the clean test assemblies (not seen in run 04 T6); heuristic = the one chosen on val
        if a.split == "test" and a.sensitivity and MAIN in S:
            clean = set(json.load(open(a.sensitivity))["clean_test"])
            heur_val = heur
            sub = [r for r in sc if r["assembly_id"] in clean]
            L.append(f"\n### Sensitivity (PREREG_addendum §A): {len({r['assembly_id'] for r in sub})} clean test assemblies ({cf})")
            fam = comparisons(sub, cf, "clean test assemblies")
            ax, ay = per_asm(sub, f"{cf}/{MAIN}"), per_asm(sub, f"{cf}/{heur_val}")
            aids = sorted(ax)
            pr = paired([ax[i] for i in aids], [ay[i] for i in aids], a.boot)
            ph = next((q["p_holm"] for q in fam if q["b"] == heur_val and q["a"] == MAIN), None)
            ca, cb = pr["ratio_ci"][1] < 1.0, ph is not None and ph < 0.05 and pr["hl"] < 0
            v = "beats" if (ca and cb) else ("cheaper on the typical assembly, not on total time" if cb else "does not beat")
            cres["sensitivity_clean"] = {"n_assemblies": len(aids), "paired": fam, "vs_best_heuristic": pr,
                                         "best_heuristic": heur_val, "verdict": v}
            L.append(f"\n**§7 on clean test:** GNN-Surv / {NAMES[heur_val]} = {pr['ratio']:.3f} [{pr['ratio_ci'][0]:.3f}, "
                     f"{pr['ratio_ci'][1]:.3f}], HL {pr['hl']:+.2f} s, Holm p {ph if ph is None else f'{ph:.2g}'}: **{v}**")
        # subsets
        L.append(f"\n### Subsets ({cf}; reported, never used for selection)")
        cres["subsets"] = {}
        subs = {"rot_state": [r for r in sc if r["rot_state"]], "non_rot_state": [r for r in sc if not r["rot_state"]]}
        for src in ("v1", "fresh-9to12", "fresh-allowance"):
            subs[f"source={src}"] = [r for r in sc if r["source"] == src]
        for b in ("3-4", "5-6", "7-8", "9-10", "11-12"):
            subs[f"parts={b}"] = [r for r in sc if pbin(r["n_parts"]) == b]
        for k, sub in subs.items():
            if not sub:
                continue
            cres["subsets"][k], _, _ = table(sub, cf, k, full=False)
            if MAIN in S and len({r['assembly_id'] for r in sub}) >= 1:
                ax, ay = per_asm(sub, f"{cf}/{MAIN}"), per_asm(sub, f"{cf}/{heur}")
                aids = sorted(ax)
                pr = paired([ax[i] for i in aids], [ay[i] for i in aids], a.boot, hl_boot=len(aids) >= 2)
                cres["subsets"][k]["gnn_surv_vs_best_heuristic"] = pr
                L.append(f"\nGNN-Surv / {NAMES[heur]} on {k}: {pr['ratio']:.3f} [{pr['ratio_ci'][0]:.3f}, {pr['ratio_ci'][1]:.3f}], "
                         f"HL {pr['hl']:+.2f} s, W/T/L {pr['wins']}/{pr['ties']}/{pr['losses']}, p {pr['p']:.2g} (uncorrected)")
        results["configs"][cf] = cres
    # ------------------------------------------------------------------ calibration / prediction quality (main config)
    L.append("\n## Prediction quality (main configuration, every node of every state with >= 1 success)\n")
    L.append("ECE: 10 equal-width bins of p vs observed success. Within-state C-index (Harrell, censored at min(cost, T)): "
             "comparable pair = part i succeeded at t_i < t_j at the same state; speed = p (BCE, ASAP) or −c (survival). "
             "Mean ± std over seeds.\n")
    L.append("| model | ECE of p | C-index within state | C-index pooled |\n|---|---|---|---|")
    keep = [i for i, g in enumerate(G) if g["succ"].any()]
    yy = np.concatenate([G[i]["succ"].numpy() for i in keep]).astype(bool)
    tt = np.concatenate([G[i]["cens_t"].numpy() for i in keep])
    grp = np.concatenate([[i] * len(G[i]["present"]) for i in keep])
    calib = {}
    for m in ["asap_zs"] + trained:
        E, C1, C2 = [], [], []
        for k in range(len(S[m])):
            p = np.concatenate([S[m][k][i][1] for i in keep])
            cc = S[m][k][keep[0]][2]
            speed = p if cc is None else -np.concatenate([S[m][k][i][2] for i in keep])
            E.append(ece(p, yy)[0]); C2.append(cindex(speed, tt, yy, grp)[0]); C1.append(cindex(speed, tt, yy)[0])
        calib[m] = {"ece": E, "c_within": C2, "c_pooled": C1}
        sd = (lambda v: f" ± {np.std(v, ddof=1):.3f}" if len(v) > 1 else "")
        L.append(f"| {NAMES[m]} | {np.mean(E):.3f}{sd(E)} | {np.mean(C2):.3f}{sd(C2)} | {np.mean(C1):.3f}{sd(C1)} |")
    L.append("\nASAP's score is P(part is the next removed part), not P(planner success), so its ECE is not a calibration claim.")
    results["calibration"] = calib
    # ------------------------------------------------------------------ figure
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        os.makedirs(a.fig_dir, exist_ok=True)
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
        for ax, cf in zip(axes, CONFIGS):
            R = results["configs"][cf]["all"]
            y = np.arange(len(order))
            tot = [R[m]["total"] for m in order]
            col = ["#9E9E9E" if m in ("random", "outside_in", "fewest_contacts") else "#937860" if m.startswith("asap")
                   else "#424242" if m == "optimal" else "#C44E52" if m == MAIN else "#4C72B0" for m in order]
            ax.barh(y, [t[0] for t in tot], color=col, xerr=[[t[0] - t[1] for t in tot], [t[2] - t[0] for t in tot]],
                    capsize=2, error_kw={"lw": 0.8})
            ax.set_yticks(y); ax.set_yticklabels([NAMES[m] for m in order], fontsize=8); ax.invert_yaxis()
            ax.set_xlabel(f"total planner time over {a.split} states (s)")
            ax.set_title("main: pre-check → CMG-RRT" if cf == "main" else "CMG-RRT only", fontsize=10)
            ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        for ext in ("pdf", "png"):
            fig.savefig(os.path.join(a.fig_dir, f"replay_{a.split}_totals.{ext}"), dpi=130)
        plt.close(fig)
        L.append(f"\n![totals](figures/replay_{a.split}_totals.png) (vector: `figures/replay_{a.split}_totals.pdf`)")
    except Exception as e:  # noqa: BLE001
        L.append(f"\n(plot failed: {e})")
    json.dump(results, open(os.path.join(a.outdir, "results.json"), "w"), indent=1, default=float)
    open(a.md, "w").write("\n".join(L) + "\n")
    log_load(a.outdir, "end")
    print("\n".join(L))


if __name__ == "__main__":
    main()
