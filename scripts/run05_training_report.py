#!/usr/bin/env python
"""Run 05 training report: grid tables (every config x grid seed), chosen configs, every final seed, training curves.

Reads <train-dir>/<variant>/{selection.json, grid_*/result.json, seed*/metrics.csv}. Writes <md> and vector figures
(<fig-dir>/train_curves_<variant>.pdf + .png). Only val numbers appear (the test split is never loaded in training).
"""
import argparse
import csv
import glob
import json
import os

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ORDER = ["mlp_bce", "mlp_survival", "gnn_bce", "gnn_survival", "gnn_survival_tail", "pn_gnn_survival", "asap_retrained"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train-dir", required=True)
    ap.add_argument("--md", required=True)
    ap.add_argument("--fig-dir", required=True)
    a = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(a.fig_dir, exist_ok=True)
    rel = os.path.relpath(a.train_dir, ROOT)
    L = ["# Run 05 training (val only)\n",
         f"Source: `{rel}/<variant>/` (`selection.json`, `grid_*/result.json`, `seed*/metrics.csv`, `train_log.txt`, "
         f"`load_info.txt`). Script `scripts/run05_training_report.py`. Selection metric = total replay planner cost on "
         "val (main config), 5-epoch trailing mean, min 10 epochs, patience 25, ≤ 150 epochs; configs ranked by the mean "
         "over grid seeds 0, 1, 2; the chosen config retrained with seeds 100–104 (docs/PREREG_run05.md §3).\n",
         "| variant | configs | chosen config | chosen mean val cost (s, seeds 0–2) | final seeds 100–104: best smoothed val cost (s) | mean ± std | best epochs | params |",
         "|---|---|---|---|---|---|---|---|"]
    grids = []
    for v in ORDER:
        sp = os.path.join(a.train_dir, v, "selection.json")
        if not os.path.exists(sp):
            L.append(f"| {v} | — | NOT TRAINED / not finished | | | | | |")
            continue
        sel = json.load(open(sp))
        seeds = sel.get("seeds", [])
        vals = [s["best_val_cost"] for s in seeds]
        npar = ""
        r0 = glob.glob(os.path.join(a.train_dir, v, "seed*", "result.json"))
        if r0:
            npar = f"{json.load(open(r0[0])).get('n_params', ''):,}"
        L.append(f"| {v} | {len(sel['grid'])} | `{json.dumps(sel['chosen'])}` | {sel['chosen_mean_val_cost']:.1f} | "
                 f"{', '.join(f'{x:.0f}' for x in vals)} | {np.mean(vals):.1f} ± {np.std(vals, ddof=1) if len(vals) > 1 else 0:.1f} | "
                 f"{', '.join(str(s['best_epoch']) for s in seeds)} | {npar} |")
        grids.append((v, sel))
        # curves of the 5 final seeds
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
        cols = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3"]
        for s, col in zip(seeds, cols):
            m = list(csv.DictReader(open(os.path.join(a.train_dir, v, f"seed{s['seed']}", "metrics.csv"))))
            e = [int(r["epoch"]) for r in m]
            ax[0].plot(e, [float(r["train_loss"]) for r in m], lw=1, color=col, label=f"s{s['seed']} train")
            if "val_loss" in m[0]:
                ax[0].plot(e, [float(r["val_loss"]) for r in m], lw=1, ls="--", color=col)
            ax[1].plot(e, [float(r["val_cost"]) for r in m], lw=1, color=col, label=f"seed {s['seed']}")
            ax[1].axvline(s["best_epoch"], lw=0.6, color="#888888", ls=":")
        ax[0].set_xlabel("epoch"); ax[0].set_ylabel("loss (solid train, dashed val)")
        ax[1].set_xlabel("epoch"); ax[1].set_ylabel("val total replay cost (s)"); ax[1].legend(frameon=False, fontsize=7)
        for x in ax:
            x.spines[["top", "right"]].set_visible(False)
        fig.suptitle(f"{v}: final seeds (chosen config)", fontsize=9)
        fig.tight_layout()
        for ext in ("pdf", "png"):
            fig.savefig(os.path.join(a.fig_dir, f"train_curves_{v}.{ext}"), dpi=110)
        plt.close(fig)
    L.append("\nEvery seed is listed; none is dropped.\n")
    L.append("**Reading the curves.** Train loss keeps falling while val loss and val replay cost bottom out early and "
             "then drift up: the models overfit after roughly 5–15 epochs. Val replay cost also jumps by several hundred "
             "seconds from epoch to epoch, because a few states where an unsolved (~30 s) query is tried first dominate the "
             "total. The 5-epoch trailing mean and the early best epochs are the registered response to this. Because val cost "
             "selected each checkpoint, val numbers for trained models are optimistic (see REPORT.md). The registered minimum "
             "of 10 epochs is implemented as 'do not stop before epoch 10'; the best checkpoint may come from an earlier epoch "
             "(18 of the 35 final checkpoints do; DECISIONS #9).\n")
    for v, sel in grids:
        keys = [k for k in sel["grid"][0] if k not in ("mean_val_cost", "per_seed", "best_epoch")]
        L.append(f"\n### Grid: {v}\n")
        L.append("| " + " | ".join(keys) + " | mean val cost (s) | per grid seed | best epochs |")
        L.append("|" + "---|" * (len(keys) + 3))
        for g in sorted(sel["grid"], key=lambda r: r["mean_val_cost"]):
            L.append("| " + " | ".join(str(g[k]) for k in keys) + f" | {g['mean_val_cost']:.1f} | "
                     f"{', '.join(f'{x:.0f}' for x in g['per_seed'])} | {g['best_epoch']} |")
        L.append(f"\n![curves](figures/train_curves_{v}.png) (vector: `figures/train_curves_{v}.pdf`)")
    open(a.md, "w").write("\n".join(L) + "\n")
    print("\n".join(L[:14]))


if __name__ == "__main__":
    main()
