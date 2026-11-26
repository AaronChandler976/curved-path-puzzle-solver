#!/usr/bin/env python
"""Vector figures (PDF) for the report, talk and paper, from saved final-evaluation outputs only.

- totals_replay_live.pdf : total planner time per ordering on the test set, replay (left) and live (right), 95% CIs.
- budget_policy.pdf      : full budget vs two-pass T'=3 s, replay and live, for fewest contacts and GNN-Surv.
- failure_scatter.pdf    : per-state cost GNN-Surv (val-best seed) vs fewest contacts, timeout-first states marked.
Colors: our models blue #2a78d6, ASAP baselines orange #eb6834, untrained orderings gray (validated pair; identity
also carried by direct labels). Every value is read from results.json / live_summary.json / failure_analysis.json.
"""
import argparse
import json
import os

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BLUE, ORANGE, GRAY, INK, INK2 = "#2a78d6", "#eb6834", "#9a9893", "#0b0b0b", "#52514e"
NAMES = {"random": "random", "outside_in": "outside-in", "fewest_contacts": "fewest contacts", "asap_zs": "ASAP zero-shot",
         "asap_retrained": "ASAP retrained", "mlp_bce": "MLP-BCE", "mlp_survival": "MLP-Surv", "gnn_bce": "GNN-BCE",
         "gnn_survival": "GNN-Surv (ours)", "gnn_survival_tail": "GNN-Surv-Tail", "pn_gnn_survival": "PN-GNN-Surv"}
ORDER = ["random", "asap_zs", "asap_retrained", "outside_in", "fewest_contacts", "mlp_bce", "mlp_survival", "gnn_bce",
         "gnn_survival", "gnn_survival_tail", "pn_gnn_survival"]


def color(m):
    return ORANGE if m.startswith("asap") else GRAY if m in ("random", "outside_in", "fewest_contacts") else BLUE


def style(plt):
    plt.rcParams.update({"font.size": 8, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                         "ytick.color": INK2, "pdf.fonttype": 42, "font.family": "DejaVu Sans"})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--replay", default=os.path.join(ROOT, "experiments/2026-11-25_final_eval_replay/results.json"))
    ap.add_argument("--live", default=os.path.join(ROOT, "experiments/2026-11-24_final_eval_live/live_summary.json"))
    ap.add_argument("--live-results", default=os.path.join(ROOT, "experiments/2026-11-24_final_eval_live/results.jsonl"))
    ap.add_argument("--failure", default=os.path.join(ROOT, "experiments/2026-11-25_final_failure_analysis/failure_analysis.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "reports/final_eval/figures"))
    a = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    style(plt)
    os.makedirs(a.out, exist_ok=True)
    R = json.load(open(a.replay))["configs"]["main"]["all"]
    # live per-method totals + bootstrap CI recomputed from the live results (first clean attempt, seed-mean)
    att = {}
    for l in open(a.live_results):
        r = json.loads(l)
        k = (r["assembly_id"], r["method"])
        if k not in att or (att[k].get("confounded") and not r.get("confounded")):
            att[k] = r
    from collections import defaultdict
    per = defaultdict(lambda: defaultdict(list))
    for (aid, m), r in att.items():
        pol = ("@b" + m.split("@b")[1]) if "@b" in m else ""
        b = m.split("@b")[0].split("#s")[0] + pol
        per[b][aid].append(float(r["planner_s"]))
    def tot_ci(m):
        v = np.array([np.mean(x) for x in per[m].values()])
        idx = np.random.default_rng(0).integers(0, len(v), (10000, len(v)))
        bs = v[idx].sum(1)
        return v.sum(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
    L = {m: tot_ci(m) for m in ORDER}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.0), sharey=True)
    for ax, src, title in ((axes[0], {m: tuple(R[m]["total"]) for m in ORDER}, "Replay (logged queries)"),
                           (axes[1], L, "Live (fresh CMG-RRT queries)")):
        y = np.arange(len(ORDER))
        v = np.array([src[m][0] for m in ORDER]) / 1000
        lo = v - np.array([src[m][1] for m in ORDER]) / 1000
        hi = np.array([src[m][2] for m in ORDER]) / 1000 - v
        ax.barh(y, v, height=0.62, color=[color(m) for m in ORDER], edgecolor="white", linewidth=1)
        ax.errorbar(v, y, xerr=[lo, hi], fmt="none", ecolor=INK2, elinewidth=0.8, capsize=1.5)
        ref = src["fewest_contacts"][0] / 1000
        ax.axvline(ref, color=INK2, lw=0.6, ls=(0, (2, 2)))
        ax.set_yticks(y); ax.set_yticklabels([NAMES[m] for m in ORDER])
        ax.invert_yaxis(); ax.set_xlabel("total planner time on the test set (1000 s)")
        ax.set_title(title, fontsize=8.5, color=INK)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="x", color="#e6e5e1", lw=0.5); ax.set_axisbelow(True)
    # the dashed line (fewest contacts) is explained in the caption
    fig.tight_layout()
    fig.savefig(os.path.join(a.out, "totals_replay_live.pdf")); plt.close(fig)
    # budget policy
    B = json.load(open(a.replay))["budget_policies"]["3"]["totals"]
    rows = [("fewest contacts", R["fewest_contacts"]["total"][0], B["fewest_contacts"], tot_ci("fewest_contacts")[0], tot_ci("fewest_contacts@b3")[0], GRAY),
            ("GNN-Surv", R["gnn_survival"]["total"][0], B["gnn_survival"], tot_ci("gnn_survival")[0], tot_ci("gnn_survival@b3")[0], BLUE)]
    fig, axes = plt.subplots(1, 2, figsize=(6.0, 2.2), sharey=True)
    for ax, (i_full, i_b3, title) in zip(axes, ((1, 2, "Replay"), (3, 4, "Live"))):
        for j, r in enumerate(rows):
            ax.barh(j * 2.6, r[i_full] / 1000, height=0.9, color=r[5], alpha=0.45, edgecolor="white")
            ax.barh(j * 2.6 + 1, r[i_b3] / 1000, height=0.9, color=r[5], edgecolor="white")
            ax.text(r[i_full] / 1000, j * 2.6, f" {r[i_full]:,.0f} s (T = 30 s)", va="center", fontsize=7, color=INK2)
            lab = " (3 s first; live: seed 101)" if (r[0] == "GNN-Surv" and title == "Live") else " (3 s first)"
            ax.text(r[i_b3] / 1000, j * 2.6 + 1, f" {r[i_b3]:,.0f} s{lab}", va="center", fontsize=7, color=INK)
        ax.set_yticks([0.5, 3.1]); ax.set_yticklabels([r[0] for r in rows]); ax.invert_yaxis()
        ax.set_title(title, fontsize=8.5); ax.set_xlabel("total planner time (1000 s)")
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xlim(0, max(r[i_full] for r in rows) / 1000 * 1.55)
    fig.tight_layout()
    fig.savefig(os.path.join(a.out, "budget_policy.pdf")); plt.close(fig)
    # failure scatter
    F = json.load(open(a.failure))
    W = F["worse"]
    fig, ax = plt.subplots(figsize=(3.4, 3.0))
    tf = [r for r in W if r["cause"].startswith("timeout")]
    sl = [r for r in W if not r["cause"].startswith("timeout")]
    ax.scatter([r["fewest"] for r in sl], [r["gnn"] for r in sl], s=10, color=GRAY, edgecolor="white", lw=0.5,
               label=f"slower first success ({len(sl)})")
    ax.scatter([r["fewest"] for r in tf], [r["gnn"] for r in tf], s=14, color=BLUE, edgecolor="white", lw=0.5,
               label=f"timeout queried first ({len(tf)})")
    mx = max(max(r["gnn"] for r in W), max(r["fewest"] for r in W)) * 1.05
    ax.plot([0.01, mx], [0.01, mx], color=INK2, lw=0.6, ls=(0, (2, 2)))
    ax.set_xscale("symlog", linthresh=0.1); ax.set_yscale("symlog", linthresh=0.1)
    ax.set_xlabel("fewest contacts: cost of the state (s)"); ax.set_ylabel("GNN-Surv: cost of the state (s)")
    ax.set_title("States where GNN-Surv (seed 101) paid more (test, replay)", fontsize=8)
    ax.legend(frameon=False, fontsize=7, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(a.out, "failure_scatter.pdf")); plt.close(fig)
    print("wrote", sorted(os.listdir(a.out)))
    print("live totals", {m: round(L[m][0]) for m in ORDER})


if __name__ == "__main__":
    main()
