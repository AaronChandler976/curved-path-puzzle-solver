#!/usr/bin/env python
"""R3 (run 03): summarize training protocols v1 (dev) and v2 (frozen) -> reports/run03/training.md (val numbers only)."""
import json
import os

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VARS = ["mlp_bce", "mlp_survival", "gnn_bce", "gnn_survival"]


def section(d, title):
    L = [f"\n## {title}\n", f"Folder `{d}`; per-run `metrics.csv` + `curve.png`; per-variant `selection.json`, `train_log.txt`.\n",
         "| variant | chosen config (hidden, lr, layers) | chosen config val metric (s) | final seeds: best val metric (s) | mean ± std | best epochs |",
         "|---|---|---|---|---|---|"]
    best_seed = {}
    for v in VARS:
        s = json.load(open(os.path.join(ROOT, d, v, "selection.json")))
        c = s["chosen"]
        vals = [x["best_val_cost"] for x in s["seeds"]]
        L.append(f"| {v} | {c['hidden']}, {c['lr']:g}, {c['layers']} | {s['chosen_val_cost']:.0f} | "
                 f"{', '.join(f'{x:.0f}' for x in vals)} | {np.mean(vals):.0f} ± {np.std(vals, ddof=1):.0f} | "
                 f"{', '.join(str(x['best_epoch']) for x in s['seeds'])} |")
        best_seed[v] = min(s["seeds"], key=lambda x: x["best_val_cost"])["seed"]
    L.append("\nGrid (val metric per config; v2 = mean of 3 seeds):\n")
    L.append("| variant | " + " | ".join(f"h{h} lr{lr:g} L{l}" for h in (64, 128) for lr in (1e-3, 3e-4) for l in (2, 3)) + " |")
    L.append("|---|" + "---|" * 8)
    for v in VARS:
        s = json.load(open(os.path.join(ROOT, d, v, "selection.json")))
        g = {(r["hidden"], r["lr"], r["layers"]): r["best_val_cost"] for r in s["grid"]}
        L.append(f"| {v} | " + " | ".join(f"{g[(h, lr, l)]:.0f}" for h in (64, 128) for lr in (1e-3, 3e-4) for l in (2, 3)) + " |")
    return L, best_seed


def main():
    base = json.load(open(os.path.join(ROOT, "experiments/2026-11-23_run03_train/val_baselines.json")))
    L = ["# Run 03 R3: training (validation numbers only)\n",
         "Val metric = total replay planner cost (s) over the 697 val states with >= 1 success; lower is better. "
         f"Val references (same metric): random {base['random']:.0f}, outside-in {base['outside_in']:.0f}, "
         f"fewest contacts {base['fewest_contacts']:.0f}, hindsight-optimal {base['optimal']:.0f} "
         "(`experiments/2026-11-23_run03_train/val_baselines.json`). The val metric was used for selection, so model val numbers "
         "are optimistically biased. Test results are in `results_replay.md`.\n",
         "Fixed for every variant: AdamW, weight decay 1e-4, dropout 0.1, grad-clip 1.0, batch 32 states, ≤ 150 epochs, K = 8 "
         "survival bins. Grid: hidden {64, 128} × lr {1e-3, 3e-4} × layers {2, 3}; the MLP uses the same residual block "
         "count as the GNN's message-passing layers."]
    l1, _ = section("experiments/2026-11-23_run03_train", "Protocol v1 (development iteration, NOT evaluated on test): grid seed 0, raw per-epoch val metric, patience 20")
    l2, bs = section("experiments/2026-11-23_run03_train_v2", "Protocol v2 (frozen, evaluated on test): grid seeds 0-2 averaged, 5-epoch trailing-mean val metric, min 10 epochs, patience 25, final seeds 100-104")
    L += l1 + ["\nWhy v2 replaced v1: the per-epoch val metric's noise SD is 98 s "
               "(`experiments/2026-11-23_run03_train/val_noise.txt`), about the size of the gaps between configs, and v1 picked epoch 0–1 "
               "checkpoints for 7/20 seeds. See DECISIONS #8."] + l2
    L.append(f"\nGNN-Surv checkpoint for R6 live evaluation (lowest val metric among the 5 v2 seeds): seed {bs['gnn_survival']}.")
    json.dump(bs, open(os.path.join(ROOT, "experiments/2026-11-23_run03_train_v2/best_val_seed.json"), "w"))
    open(os.path.join(ROOT, "reports/run03/training.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
