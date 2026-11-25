# Phase 2: exploration on val (post-registration, exploratory)

Everything here uses train+val only. Trained models' val numbers are biased toward them (val chose their configs and
epochs). The group CV with inner early stopping is the unbiased check. Nothing here changes the registered comparison.

## 1. What was tried (the campaign list)
| item | evidence | outcome (val / CV) |
|---|---|---|
| ordering keys on the trained survival models: p/c, p, 1/c, risk-averse p/(c+β·sd), extra timeout weight p/(c+κ(1−p)T) | `experiments/2026-11-24_run06_explore_orderings/orderings.md` | all within ±4% of p/c; no key is better in a stable way. c = E[min(t, T)] already includes the P(unsolved)·T term |
| **two-pass budget policy** T' ∈ {1, 3, 10} s, every ordering | same file; `reports/explore/val_all.md` | the largest effect found. Fewest contacts 2,275 → 757 s, GNN-Surv 1,835 → 638 s at T' = 3. It helps every ordering, so it is a planner-usage policy, not a learning result. Under the same policy GNN-Surv / fewest = 0.844 [0.666, 1.010] |
| stronger encoders: GATv2, graph transformer (same head, grid, budget, 5 seeds) | `experiments/2026-11-24_run06_explore_train/`, `reports/explore/val_all.md` | GT-Surv val 1,633 s, GATv2-Surv 2,070 s (seed-mean replay), GNN-Surv 1,835 s |
| listwise loss (ListNet top-1 on cost-weighted successes, λ ∈ {0.1, 1}) | same | GNN-Surv-ListNet val 1,581 s |
| 5-fold group CV over train+val, 5 seeds, inner early stopping | `reports/explore/cv.md`, `experiments/2026-11-24_run06_cv/` | pooled ratio vs fewest contacts: PN 0.788, ListNet 0.832, GT 0.848, GNN-Surv 0.874, Tail 0.891, GATv2 0.895, GNN-BCE 0.928, MLP-Surv 0.939, MLP-BCE 0.975; outside-in 1.310, random 2.091 |
| EV-battery CAD case study (optional) | — | not done: no public battery-module CAD found that downloads without a login in the time spent. Low priority by the campaign list |

## 2. What the CV says about the val ranking
- **Val overstated the tail-aware objective.** Tail was the best registered variant on val (1,637 s vs 1,835 s), but
  in CV it is no better than plain survival (0.891 vs 0.874). It also had the most val selection (16 configs vs 8).
- **The intervention ordering holds out of sample:**
  - GNN beats MLP (survival 0.874 vs 0.939; BCE 0.928 vs 0.975).
  - Survival beats BCE (GNN 0.874 vs 0.928; MLP 0.939 vs 0.975).
  - PointNet features help (0.788).
- **All learned rankers beat fewest contacts on pooled held-out totals,** but fold 2 is a loss for every variant except
  PN (per-fold ratios in `cv.md`).
- **Per-seed spread** of the pooled ratio is 0.02–0.05, the same size as the gaps between neighbouring variants.

## 3. What enters the test
`docs/PREREG_addendum.md` §B: all three exploratory variants in replay, GT-Surv and ListNet also live, and the T' = 3 s
budget policy for every ordering. Checkpoints and sha256: `configs/final_frozen.yaml`.
