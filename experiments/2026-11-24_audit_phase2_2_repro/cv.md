# Phase 2: 5-fold group cross-validation over train+val (robustness check of the val ranking)

Source `experiments/2026-11-24_run06_cv/*/cv_results.json` (`scripts/cv_v2.py`), summary `scripts/cv_report.py`. Folds = duplicate groups of train+val (1,675 assemblies), stratified by source and part-count bin; per fold, train on 3 folds, early-stop on the next fold, replay the held-out fold (which selects nothing). Configs = the val-chosen ones (val assemblies are inside the folds). Main configuration, logged costs. Ratio < 1 = cheaper than fewest contacts on the same held-out states. **Registered variants are not re-selected by this; exploratory variants are marked.** It does not change the registered selection rule.

| variant | folds × seeds | pooled ratio vs fewest contacts | per-fold ratios (seed-mean) | mean ± std over folds | per-seed pooled ratio mean ± std |
|---|---|---|---|---|---|
| pn_gnn_survival | 5 × 5 | 0.788 | 0.646, 0.743, 0.953, 0.846, 0.749 | 0.787 ± 0.117 | 0.788 ± 0.027 |
| gnn_survival_listnet [expl.] | 5 × 5 | 0.832 | 0.721, 0.704, 1.112, 0.874, 0.748 | 0.832 ± 0.170 | 0.832 ± 0.036 |
| gt_survival [expl.] | 5 × 5 | 0.848 | 0.735, 0.883, 1.006, 0.872, 0.763 | 0.851 ± 0.108 | 0.848 ± 0.026 |
| gnn_survival | 5 × 5 | 0.874 | 0.741, 0.795, 1.140, 0.891, 0.809 | 0.875 ± 0.158 | 0.874 ± 0.045 |
| gnn_survival_tail | 5 × 5 | 0.891 | 0.708, 0.782, 1.303, 0.903, 0.772 | 0.894 ± 0.239 | 0.891 ± 0.047 |
| gatv2_survival [expl.] | 5 × 5 | 0.895 | 0.831, 0.844, 1.002, 0.911, 0.884 | 0.895 ± 0.068 | 0.895 ± 0.028 |
| gnn_bce | 5 × 5 | 0.928 | 0.807, 0.939, 1.126, 0.940, 0.844 | 0.931 ± 0.124 | 0.928 ± 0.051 |
| mlp_survival | 5 × 5 | 0.939 | 0.849, 0.955, 1.104, 0.894, 0.911 | 0.943 ± 0.098 | 0.939 ± 0.022 |
| mlp_bce | 5 × 5 | 0.975 | 0.838, 0.964, 1.218, 1.004, 0.867 | 0.978 ± 0.150 | 0.975 ± 0.025 |
| outside_in | 5 × — | 1.310 | 1.562, 1.304, 1.457, 1.089, 1.181 | 1.318 ± 0.194 | — |
| random | 5 × — | 2.091 | 2.199, 2.069, 2.417, 2.079, 1.731 | 2.099 ± 0.249 | — |

Held-out fold totals for fewest contacts (s): fold 0: 4098, fold 1: 3492, fold 2: 3858, fold 3: 4612, fold 4: 4360; hindsight-optimal: 230, 164, 264, 150, 172.
