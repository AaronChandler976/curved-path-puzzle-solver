# INTERIM (priority P1 only: every trained variant at its val-best seed; P2–P4 still running). Final: reports/final_eval/live.md

Source `experiments/2026-11-24_final_eval_live/results.jsonl` (every attempt), summarised by `scripts/live_report_v2.py`. Fresh queries with oracle v2 (pre-check → CMG-RRT only when the pull fails), T = 30 s, planner seed per query = sha1("run05-live", assembly, state, part), idle guard on, confounded runs re-run up to 2× (first clean attempt reported). Per-assembly cost = total planner time of the disassembly. CIs: bootstrap over assemblies (10000).

- (assembly, method) runs: 3817; re-run at least once: 57; still confounded or errored after re-runs (reported, flagged): 0.

| ordering | assemblies | seeds per assembly | complete / stuck / error | total planner time (s) [95% CI over assemblies] |
|---|---|---|---|---|
| random | 347 | [1] | 316 / 31 / 0 | 26464 [21786, 31202] |
| outside_in | 347 | [1] | 313 / 34 / 0 | 23239 [18426, 28310] |
| fewest_contacts | 347 | [1] | 312 / 35 / 0 | 23002 [18624, 27561] |
| asap_zs | 347 | [1] | 314 / 33 / 0 | 26667 [21430, 32121] |
| asap_retrained | 347 | [1] | 315 / 32 / 0 | 22840 [17726, 28553] |
| mlp_bce | 347 | [1] | 313 / 34 / 0 | 21631 [17300, 26295] |
| mlp_survival | 347 | [1] | 312 / 35 / 0 | 20219 [16094, 24681] |
| gnn_bce | 347 | [1] | 313 / 34 / 0 | 20514 [16372, 24887] |
| gnn_survival | 347 | [1] | 313 / 34 / 0 | 21401 [16946, 26224] |
| gnn_survival_tail | 347 | [1] | 314 / 33 / 0 | 18032 [14254, 22157] |
| pn_gnn_survival | 347 | [1] | 314 / 33 / 0 | 21033 [16793, 25575] |

### Registered comparisons (Holm family of 11)

| A vs B | n | ratio of totals [95% CI] | HL (s) [95% CI] | W / T / L | Wilcoxon p | Holm p |
|---|---|---|---|---|---|---|
| gnn_survival vs random | 347 | 0.809 [0.685, 0.947] | -4.58 [-15.19, -0.63] | 216 / 34 / 97 | 2.3e-09 | 2.5e-08 |
| gnn_survival vs outside_in | 347 | 0.921 [0.801, 1.060] | -0.18 [-0.55, -0.05] | 187 / 58 / 102 | 1.4e-05 | 0.00012 |
| gnn_survival vs fewest_contacts | 347 | 0.930 [0.835, 1.034] | -0.12 [-0.28, -0.03] | 179 / 64 / 104 | 0.00022 | 0.0018 |
| gnn_survival vs asap_zs | 347 | 0.803 [0.710, 0.902] | -0.41 [-1.04, -0.18] | 214 / 39 / 94 | 1e-08 | 1e-07 |
| gnn_survival vs asap_retrained | 347 | 0.937 [0.828, 1.069] | -0.10 [-0.43, -0.01] | 176 / 46 / 125 | 0.014 | 0.084 |
| gnn_survival vs mlp_survival | 347 | 1.058 [0.949, 1.183] | -0.00 [-0.03, +0.03] | 142 / 79 / 126 | 0.79 | 1 |
| gnn_survival vs gnn_bce | 347 | 1.043 [0.921, 1.182] | -0.02 [-0.12, +0.00] | 163 / 58 / 126 | 0.15 | 0.61 |
| gnn_survival vs gnn_survival_tail | 347 | 1.187 [1.060, 1.337] | +0.04 [+0.00, +0.17] | 107 / 85 / 155 | 0.0023 | 0.016 |
| gnn_survival vs pn_gnn_survival | 347 | 1.017 [0.935, 1.109] | -0.00 [-0.04, +0.01] | 139 / 78 / 130 | 0.58 | 1 |
| gnn_bce vs mlp_bce | 347 | 0.948 [0.810, 1.112] | +0.01 [-0.02, +0.09] | 131 / 67 / 149 | 0.46 | 1 |
| mlp_survival vs mlp_bce | 347 | 0.935 [0.852, 1.024] | -0.01 [-0.04, +0.00] | 137 / 97 / 113 | 0.11 | 0.54 |

**§7 rule applied to LIVE (separately, PREREG §7):** GNN-Surv / fewest contacts = 0.930 [0.835, 1.034], HL -0.12 s, Holm p 0.0018 → (a) False, (b) True: **cheaper on the typical assembly, not on total time**

### Sensitivity (addendum A): same family on the 306 clean test assemblies

| A vs B | n | ratio of totals [95% CI] | HL (s) [95% CI] | W / T / L | Wilcoxon p | Holm p |
|---|---|---|---|---|---|---|
| gnn_survival vs random | 306 | 0.828 [0.695, 0.986] | -2.58 [-15.04, -0.47] | 189 / 28 / 89 | 1.1e-07 | 1.1e-06 |
| gnn_survival vs outside_in | 306 | 0.948 [0.817, 1.109] | -0.13 [-0.43, -0.04] | 164 / 51 / 91 | 0.00011 | 0.00099 |
| gnn_survival vs fewest_contacts | 306 | 0.936 [0.834, 1.050] | -0.09 [-0.24, -0.02] | 155 / 57 / 94 | 0.0014 | 0.011 |
| gnn_survival vs asap_zs | 306 | 0.804 [0.704, 0.911] | -0.38 [-1.19, -0.16] | 187 / 35 / 84 | 1e-07 | 1.1e-06 |
| gnn_survival vs asap_retrained | 306 | 0.942 [0.826, 1.088] | -0.09 [-0.35, -0.00] | 155 / 40 / 111 | 0.027 | 0.16 |
| gnn_survival vs mlp_survival | 306 | 1.079 [0.956, 1.216] | -0.00 [-0.03, +0.03] | 125 / 70 / 111 | 0.8 | 1 |
| gnn_survival vs gnn_bce | 306 | 1.074 [0.940, 1.239] | -0.01 [-0.09, +0.02] | 141 / 51 / 114 | 0.34 | 1 |
| gnn_survival vs gnn_survival_tail | 306 | 1.231 [1.083, 1.405] | +0.04 [+0.00, +0.17] | 94 / 77 / 135 | 0.004 | 0.028 |
| gnn_survival vs pn_gnn_survival | 306 | 1.013 [0.924, 1.109] | -0.01 [-0.07, +0.00] | 127 / 71 / 108 | 0.27 | 1 |
| gnn_bce vs mlp_bce | 306 | 0.921 [0.769, 1.098] | +0.00 [-0.04, +0.07] | 118 / 59 / 129 | 0.75 | 1 |
| mlp_survival vs mlp_bce | 306 | 0.917 [0.832, 1.013] | -0.01 [-0.06, +0.00] | 120 / 88 / 98 | 0.068 | 0.34 |

### Exploratory (post-registration; uncorrected p)

| A vs B | n | ratio of totals [95% CI] | HL (s) [95% CI] | W / T / L | Wilcoxon p | (uncorrected) |
|---|---|---|---|---|---|---|

### Subsets (GNN-Surv vs fewest contacts; reported, never used for selection; < 30 assemblies = underpowered)

| subset | n | ratio [95% CI] | HL (s) | W/T/L | p (uncorrected) |
|---|---|---|---|---|---|
| source=fresh-9to12 | 127 | 0.926 [0.767, 1.096] | -0.17 | 72/15/40 | 0.024 |
| source=fresh-allowance | 220 | 0.934 [0.820, 1.073] | -0.09 | 107/49/64 | 0.0038 |
| parts=3-4 | 82 | 0.907 [0.637, 1.198] | -0.02 | 35/32/15 | 0.029 |
| parts=5-6 | 52 | 0.818 [0.678, 0.947] | -0.25 | 27/14/11 | 0.0016 |
| parts=7-8 | 37 | 0.767 [0.607, 0.919] | -16.18 | 21/1/15 | 0.032 |
| parts=9-10 | 102 | 0.959 [0.759, 1.254] | -0.12 | 57/11/34 | 0.09 |
| parts=11-12 | 74 | 1.004 [0.840, 1.159] | -0.08 | 39/6/29 | 0.7 |
