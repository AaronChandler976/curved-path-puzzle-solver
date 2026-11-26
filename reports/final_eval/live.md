# Final live evaluation on the v2 test set (PREREG §6; evaluated once)

Source `experiments/2026-11-24_final_eval_live/results.jsonl` (every attempt), summarised by `scripts/live_report_v2.py`. Fresh queries with oracle v2 (pre-check → CMG-RRT only when the pull fails), T = 30 s, planner seed per query = sha1("run05-live", assembly, state, part), idle guard on, confounded runs re-run up to 2× (first clean attempt reported). Per-assembly cost = total planner time of the disassembly. Ratio/total CIs: bootstrap over assemblies (10000); HL CIs: 2,000 resamples. `gnn_survival@b3` is the val-best seed (101) only.

- (assembly, method) runs: 17697; re-run at least once: 77; still confounded or errored after re-runs (reported, flagged): 0.

| ordering | assemblies | seeds per assembly | complete / stuck / error | total planner time (s) [95% CI over assemblies] | planner calls per assembly (mean) |
|---|---|---|---|---|---|
| random | 347 | [1] | 316 / 31 / 0 | 26464 [21786, 31202] | 8.5 |
| outside_in | 347 | [1] | 313 / 34 / 0 | 23239 [18426, 28310] | 8.2 |
| fewest_contacts | 347 | [1] | 312 / 35 / 0 | 23002 [18624, 27561] | 8.2 |
| asap_zs | 347 | [1] | 314 / 33 / 0 | 26667 [21430, 32121] | 8.4 |
| asap_retrained | 347 | [5] | 1565 / 170 / 0 | 23212 [18512, 28367] | 8.2 |
| mlp_bce | 347 | [5] | 1563 / 172 / 0 | 21139 [17005, 25681] | 8.0 |
| mlp_survival | 347 | [5] | 1560 / 175 / 0 | 20827 [16767, 25237] | 8.0 |
| gnn_bce | 347 | [5] | 1569 / 166 / 0 | 20131 [16285, 24209] | 7.9 |
| gnn_survival | 347 | [5] | 1572 / 163 / 0 | 21038 [16700, 25758] | 8.0 |
| gnn_survival_tail | 347 | [5] | 1569 / 166 / 0 | 19885 [15987, 24045] | 7.9 |
| pn_gnn_survival | 347 | [5] | 1566 / 169 / 0 | 20805 [16644, 25350] | 8.0 |
| gt_survival [expl.] | 347 | [5] | 1566 / 169 / 0 | 21735 [17381, 26548] | 8.1 |
| gnn_survival_listnet [expl.] | 347 | [5] | 1568 / 167 / 0 | 18336 [14716, 22146] | 7.8 |
| fewest_contacts@b3 [expl.] | 347 | [1] | 311 / 36 / 0 | 11273 [8668, 14047] | 9.0 |
| gnn_survival@b3 [expl.] | 347 | [1] | 311 / 36 / 0 | 10810 [8164, 13693] | 8.7 |

### Registered comparisons (Holm family of 11)

| A vs B | n | ratio of totals [95% CI] | HL (s) [95% CI] | W / T / L | Wilcoxon p | Holm p |
|---|---|---|---|---|---|---|
| gnn_survival vs random | 347 | 0.795 [0.674, 0.932] | -6.03 [-14.54, -0.95] | 218 / 26 / 103 | 3.3e-09 | 3.6e-08 |
| gnn_survival vs outside_in | 347 | 0.905 [0.779, 1.050] | -0.07 [-0.26, -0.00] | 179 / 45 / 123 | 0.026 | 0.16 |
| gnn_survival vs fewest_contacts | 347 | 0.915 [0.819, 1.015] | -0.05 [-0.18, -0.00] | 181 / 45 / 121 | 0.019 | 0.13 |
| gnn_survival vs asap_zs | 347 | 0.789 [0.699, 0.880] | -0.50 [-2.38, -0.20] | 218 / 35 / 94 | 2.8e-08 | 2.8e-07 |
| gnn_survival vs asap_retrained | 347 | 0.906 [0.827, 0.994] | -0.15 [-0.87, -0.02] | 179 / 40 / 128 | 0.005 | 0.04 |
| gnn_survival vs mlp_survival | 347 | 1.010 [0.929, 1.091] | -0.01 [-0.07, +0.01] | 155 / 63 / 129 | 0.3 | 0.91 |
| gnn_survival vs gnn_bce | 347 | 1.045 [0.955, 1.150] | -0.06 [-0.21, -0.01] | 183 / 55 / 109 | 0.0039 | 0.035 |
| gnn_survival vs gnn_survival_tail | 347 | 1.058 [1.003, 1.110] | +0.02 [+0.00, +0.08] | 116 / 78 / 153 | 0.037 | 0.18 |
| gnn_survival vs pn_gnn_survival | 347 | 1.011 [0.957, 1.066] | -0.00 [-0.04, +0.02] | 136 / 69 / 142 | 1 | 1 |
| gnn_bce vs mlp_bce | 347 | 0.952 [0.864, 1.055] | +0.00 [-0.06, +0.06] | 141 / 53 / 153 | 1 | 1 |
| mlp_survival vs mlp_bce | 347 | 0.985 [0.943, 1.033] | -0.01 [-0.07, +0.01] | 153 / 59 / 135 | 0.18 | 0.73 |

**§7 rule applied to LIVE (separately, PREREG §7):** GNN-Surv / fewest contacts = 0.915 [0.819, 1.015], HL -0.05 s, Holm p 0.13 → (a) False, (b) False: **does not beat**

### Sensitivity (addendum A): same family on the 306 clean test assemblies

| A vs B | n | ratio of totals [95% CI] | HL (s) [95% CI] | W / T / L | Wilcoxon p | Holm p |
|---|---|---|---|---|---|---|
| gnn_survival vs random | 306 | 0.802 [0.673, 0.956] | -5.28 [-13.22, -0.71] | 193 / 22 / 91 | 4.2e-08 | 4.6e-07 |
| gnn_survival vs outside_in | 306 | 0.918 [0.779, 1.082] | -0.05 [-0.23, -0.00] | 158 / 40 / 108 | 0.042 | 0.25 |
| gnn_survival vs fewest_contacts | 306 | 0.907 [0.801, 1.020] | -0.04 [-0.19, -0.00] | 159 / 40 / 107 | 0.031 | 0.22 |
| gnn_survival vs asap_zs | 306 | 0.779 [0.681, 0.880] | -0.50 [-2.68, -0.20] | 194 / 29 / 83 | 1.3e-07 | 1.3e-06 |
| gnn_survival vs asap_retrained | 306 | 0.883 [0.801, 0.972] | -0.17 [-1.10, -0.02] | 158 / 34 / 114 | 0.0048 | 0.043 |
| gnn_survival vs mlp_survival | 306 | 1.012 [0.924, 1.099] | -0.01 [-0.07, +0.02] | 138 / 56 / 112 | 0.28 | 0.89 |
| gnn_survival vs gnn_bce | 306 | 1.053 [0.950, 1.175] | -0.05 [-0.20, -0.01] | 159 / 50 / 97 | 0.01 | 0.083 |
| gnn_survival vs gnn_survival_tail | 306 | 1.056 [0.995, 1.114] | +0.02 [-0.00, +0.08] | 103 / 70 / 133 | 0.077 | 0.38 |
| gnn_survival vs pn_gnn_survival | 306 | 1.012 [0.955, 1.071] | +0.00 [-0.03, +0.02] | 118 / 61 / 127 | 0.94 | 1 |
| gnn_bce vs mlp_bce | 306 | 0.943 [0.844, 1.055] | -0.00 [-0.07, +0.06] | 125 / 47 / 134 | 0.94 | 1 |
| mlp_survival vs mlp_bce | 306 | 0.981 [0.937, 1.035] | -0.01 [-0.07, +0.01] | 134 / 51 / 121 | 0.22 | 0.89 |

### Exploratory (post-registration; uncorrected p)

| A vs B | n | ratio of totals [95% CI] | HL (s) [95% CI] | W / T / L | Wilcoxon p (uncorrected) |
|---|---|---|---|---|---|
| gt_survival vs fewest_contacts | 347 | 0.945 [0.844, 1.055] | -0.05 [-0.17, +0.01] | 176 / 43 / 128 | 0.079 |
| gnn_survival_listnet vs fewest_contacts | 347 | 0.797 [0.711, 0.886] | -0.22 [-0.74, -0.06] | 192 / 49 / 106 | 3.7e-05 |
| gt_survival vs gnn_survival | 347 | 1.033 [0.977, 1.094] | +0.03 [+0.00, +0.43] | 126 / 70 / 151 | 0.036 |
| gnn_survival_listnet vs gnn_survival | 347 | 0.872 [0.806, 0.942] | -0.11 [-0.56, -0.02] | 180 / 57 / 110 | 0.00031 |
| fewest_contacts@b3 vs fewest_contacts | 347 | 0.490 [0.424, 0.557] | -11.16 [-21.28, -0.05] | 154 / 151 / 42 | 4e-17 |
| gnn_survival@b3 vs gnn_survival | 347 | 0.514 [0.446, 0.582] | -7.15 [-14.72, -2.87] | 193 / 74 / 80 | 2.3e-16 |
| gnn_survival@b3 vs fewest_contacts@b3 | 347 | 0.959 [0.896, 1.023] | -0.12 [-0.26, -0.04] | 182 / 59 / 106 | 9.4e-05 |

### Subsets (GNN-Surv vs fewest contacts; reported, never used for selection; < 30 assemblies = underpowered)

| subset | n | ratio [95% CI] | HL (s) | W/T/L | p (uncorrected) |
|---|---|---|---|---|---|
| source=fresh-9to12 | 127 | 0.876 [0.714, 1.051] | -0.06 | 67/15/45 | 0.18 |
| source=fresh-allowance | 220 | 0.945 [0.831, 1.070] | -0.04 | 114/30/76 | 0.047 |
| parts=3-4 | 82 | 0.918 [0.670, 1.218] | -0.02 | 39/17/26 | 0.28 |
| parts=5-6 | 52 | 0.899 [0.767, 1.037] | -0.05 | 26/12/14 | 0.07 |
| parts=7-8 | 37 | 0.847 [0.704, 1.005] | -4.69 | 21/0/16 | 0.35 |
| parts=9-10 | 102 | 0.849 [0.675, 1.085] | -0.14 | 58/10/34 | 0.061 |
| parts=11-12 | 74 | 0.990 [0.810, 1.157] | -0.00 | 37/6/31 | 0.98 |
