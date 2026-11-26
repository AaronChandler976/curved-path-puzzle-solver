# Run 05 replay on v2 **val** (2026-11-24)

Script `scripts/eval_v2.py`; raw per-state costs `experiments/2026-11-24_run05_eval_val_dev/per_state.jsonl`, all numbers `experiments/2026-11-24_run05_eval_val_dev/results.json`. Graphs `data/processed/run05/graphs_train_val.pt` (1030 val states, 250 assemblies). Replay of logged pilot_v2 queries (nothing simulated). Trained variants: per-state cost = mean over their seeds; 'seeds' = mean ± std of the per-seed totals. CIs: bootstrap over assemblies (2000 resamples, seed 0).


## Configuration: MAIN (pre-check → CMG-RRT)

Scored states: 1010; states with no success under this configuration: 20 (every ordering pays all their queries: 1857 s, not in the totals).

#### All scored states: 1010 states, 245 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) | median per-state ratio to optimal [95% CI] | mean queries to 1st success | states solved within T |
|---|---|---|---|---|---|
| random (expectation) | 6059 [4617, 7624] |  | 12.69 [8.81, 18.20] | 1.17 | 0.934 |
| outside-in | 2800 [1818, 3910] |  | 1.89 [1.55, 2.32] | 1.08 | 0.948 |
| fewest contacts | 2275 [1542, 3079] |  | 1.39 [1.20, 1.70] | 1.06 | 0.955 |
| ASAP zero-shot | 3549 [2395, 4913] |  | 2.20 [1.78, 2.64] | 1.10 | 0.924 |
| MLP-BCE (p) | 2205 [1560, 2939] | 2205 ± 125 (n=5) | 1.74 [1.53, 1.99] | 1.06 | 0.956 |
| MLP-Surv (p/c) | 2026 [1418, 2697] | 2026 ± 170 (n=5) | 1.86 [1.65, 2.17] | 1.05 | 0.957 |
| GNN-BCE (p) | 1903 [1298, 2536] | 1903 ± 136 (n=5) | 2.14 [1.89, 2.55] | 1.05 | 0.964 |
| GNN-Surv (p/c) | 1835 [1203, 2501] | 1835 ± 129 (n=5) | 1.51 [1.37, 1.72] | 1.05 | 0.969 |
| PN-GNN-Surv (p/c) | 1684 [1141, 2258] | 1684 ± 88 (n=5) | 1.55 [1.37, 1.74] | 1.04 | 0.968 |
| hindsight-optimal (lower bound) | 115 [63, 178] |  | 1.00 [1.00, 1.00] | 1.00 | 1.000 |

Paired per assembly (all scored states; Holm family of 9; ratio = A/B of totals; HL = Hodges–Lehmann median difference A − B per assembly, negative = A cheaper; W/T/L for A, tie |d| ≤ 0.01 s):

| A vs B | ratio of totals [95% CI] | HL diff (s) [95% CI] | W / T / L | Wilcoxon p | Holm p |
|---|---|---|---|---|---|
| GNN-Surv (p/c) vs random (expectation) | 0.303 [0.221, 0.398] | -7.37 [-11.20, -4.99] | 192 / 25 / 28 | 2.1e-27 | 1.9e-26 |
| GNN-Surv (p/c) vs outside-in | 0.656 [0.459, 0.942] | -0.02 [-0.07, -0.00] | 98 / 87 / 60 | 0.0018 | 0.0089 |
| GNN-Surv (p/c) vs fewest contacts | 0.807 [0.637, 1.004] | -0.02 [-0.06, -0.00] | 99 / 89 / 57 | 0.00042 | 0.0029 |
| GNN-Surv (p/c) vs ASAP zero-shot | 0.517 [0.351, 0.729] | -0.09 [-0.31, -0.03] | 126 / 64 / 55 | 2.1e-07 | 1.7e-06 |
| GNN-Surv (p/c) vs MLP-Surv (p/c) | 0.906 [0.721, 1.135] | -0.01 [-0.03, -0.00] | 90 / 91 / 64 | 0.02 | 0.079 |
| GNN-Surv (p/c) vs GNN-BCE (p) | 0.964 [0.779, 1.189] | -0.01 [-0.04, -0.00] | 102 / 88 / 55 | 0.00047 | 0.0029 |
| GNN-Surv (p/c) vs PN-GNN-Surv (p/c) | 1.090 [0.925, 1.274] | +0.00 [-0.00, +0.00] | 63 / 117 / 65 | 0.79 | 1 |
| GNN-BCE (p) vs MLP-BCE (p) | 0.863 [0.710, 1.040] | -0.00 [-0.01, +0.00] | 75 / 96 / 74 | 0.65 | 1 |
| MLP-Surv (p/c) vs MLP-BCE (p) | 0.919 [0.793, 1.056] | -0.00 [-0.01, +0.00] | 78 / 100 / 67 | 0.23 | 0.69 |

**§7 rule (val, main):** best heuristic on this split = fewest contacts; GNN-Surv / heuristic = 0.807 [0.637, 1.004], HL -0.02 s, Holm p 0.0029 → (a) False, (b) True: **cheaper on the typical assembly, not on total time** (val: development only; the registered rule applies to test)

### Subsets (main; reported, never used for selection)

#### rot_state: 82 states, 44 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1415 [950, 1930] |  |
| outside-in | 904 [478, 1406] |  |
| fewest contacts | 635 [290, 1072] |  |
| ASAP zero-shot | 915 [509, 1383] |  |
| MLP-BCE (p) | 570 [327, 855] | 570 ± 32 (n=5) |
| MLP-Surv (p/c) | 480 [277, 715] | 480 ± 88 (n=5) |
| GNN-BCE (p) | 636 [361, 972] | 636 ± 45 (n=5) |
| GNN-Surv (p/c) | 566 [306, 940] | 566 ± 77 (n=5) |
| PN-GNN-Surv (p/c) | 529 [299, 830] | 529 ± 91 (n=5) |
| hindsight-optimal (lower bound) | 73 [26, 135] |  |

GNN-Surv / fewest contacts on rot_state: 0.891 [0.604, 1.403], HL -0.01 s, W/T/L 19/10/15, p 0.73 (uncorrected)

#### non_rot_state: 928 states, 240 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 4644 [3595, 5855] |  |
| outside-in | 1896 [1162, 2760] |  |
| fewest contacts | 1640 [1063, 2289] |  |
| ASAP zero-shot | 2634 [1722, 3884] |  |
| MLP-BCE (p) | 1634 [1105, 2194] | 1634 ± 132 (n=5) |
| MLP-Surv (p/c) | 1547 [1049, 2136] | 1547 ± 115 (n=5) |
| GNN-BCE (p) | 1267 [872, 1703] | 1267 ± 159 (n=5) |
| GNN-Surv (p/c) | 1269 [789, 1814] | 1269 ± 136 (n=5) |
| PN-GNN-Surv (p/c) | 1155 [746, 1637] | 1155 ± 34 (n=5) |
| hindsight-optimal (lower bound) | 42 [31, 56] |  |

GNN-Surv / fewest contacts on non_rot_state: 0.774 [0.572, 1.045], HL -0.01 s, W/T/L 93/95/52, p 0.00021 (uncorrected)

#### source=v1: 678 states, 194 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 3142 [2391, 4021] |  |
| outside-in | 1681 [979, 2489] |  |
| fewest contacts | 1471 [879, 2148] |  |
| ASAP zero-shot | 1776 [1158, 2492] |  |
| MLP-BCE (p) | 1428 [919, 2012] | 1428 ± 49 (n=5) |
| MLP-Surv (p/c) | 1211 [793, 1685] | 1211 ± 172 (n=5) |
| GNN-BCE (p) | 1213 [754, 1747] | 1213 ± 89 (n=5) |
| GNN-Surv (p/c) | 1082 [655, 1612] | 1082 ± 96 (n=5) |
| PN-GNN-Surv (p/c) | 1011 [608, 1514] | 1011 ± 122 (n=5) |
| hindsight-optimal (lower bound) | 82 [35, 146] |  |

GNN-Surv / fewest contacts on source=v1: 0.735 [0.531, 1.016], HL -0.02 s, W/T/L 78/79/37, p 1.9e-05 (uncorrected)

#### source=fresh-9to12: 180 states, 19 assemblies — **UNDERPOWERED (< 30 assemblies), no conclusion**

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1044 [491, 1701] |  |
| outside-in | 216 [39, 445] |  |
| fewest contacts | 317 [71, 678] |  |
| ASAP zero-shot | 828 [165, 1727] |  |
| MLP-BCE (p) | 413 [156, 778] | 413 ± 74 (n=5) |
| MLP-Surv (p/c) | 447 [154, 883] | 447 ± 89 (n=5) |
| GNN-BCE (p) | 332 [103, 680] | 332 ± 67 (n=5) |
| GNN-Surv (p/c) | 424 [114, 834] | 424 ± 150 (n=5) |
| PN-GNN-Surv (p/c) | 284 [91, 526] | 284 ± 80 (n=5) |
| hindsight-optimal (lower bound) | 6 [4, 9] |  |

GNN-Surv / fewest contacts on source=fresh-9to12: 1.340 [0.780, 3.267], HL +0.80 s, W/T/L 5/2/12, p 0.14 (uncorrected)

#### source=fresh-allowance: 152 states, 32 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1873 [1019, 2902] |  |
| outside-in | 903 [339, 1648] |  |
| fewest contacts | 487 [221, 809] |  |
| ASAP zero-shot | 944 [414, 1639] |  |
| MLP-BCE (p) | 363 [171, 589] | 363 ± 121 (n=5) |
| MLP-Surv (p/c) | 368 [217, 542] | 368 ± 125 (n=5) |
| GNN-BCE (p) | 358 [174, 581] | 358 ± 62 (n=5) |
| GNN-Surv (p/c) | 329 [153, 548] | 329 ± 111 (n=5) |
| PN-GNN-Surv (p/c) | 389 [184, 639] | 389 ± 99 (n=5) |
| hindsight-optimal (lower bound) | 27 [11, 49] |  |

GNN-Surv / fewest contacts on source=fresh-allowance: 0.675 [0.471, 1.021], HL -0.28 s, W/T/L 16/8/8, p 0.11 (uncorrected)

#### parts=3-4: 267 states, 118 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1063 [756, 1380] |  |
| outside-in | 677 [375, 1028] |  |
| fewest contacts | 523 [265, 813] |  |
| ASAP zero-shot | 668 [370, 989] |  |
| MLP-BCE (p) | 592 [295, 913] | 592 ± 61 (n=5) |
| MLP-Surv (p/c) | 551 [297, 841] | 551 ± 34 (n=5) |
| GNN-BCE (p) | 347 [187, 535] | 347 ± 81 (n=5) |
| GNN-Surv (p/c) | 343 [188, 523] | 343 ± 134 (n=5) |
| PN-GNN-Surv (p/c) | 340 [198, 501] | 340 ± 60 (n=5) |
| hindsight-optimal (lower bound) | 39 [14, 73] |  |

GNN-Surv / fewest contacts on parts=3-4: 0.657 [0.427, 0.988], HL -0.01 s, W/T/L 42/61/15, p 0.00026 (uncorrected)

#### parts=5-6: 289 states, 67 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1524 [1019, 2061] |  |
| outside-in | 1103 [525, 1793] |  |
| fewest contacts | 766 [343, 1265] |  |
| ASAP zero-shot | 800 [379, 1254] |  |
| MLP-BCE (p) | 570 [261, 942] | 570 ± 39 (n=5) |
| MLP-Surv (p/c) | 493 [245, 829] | 493 ± 76 (n=5) |
| GNN-BCE (p) | 627 [315, 969] | 627 ± 73 (n=5) |
| GNN-Surv (p/c) | 598 [293, 993] | 598 ± 110 (n=5) |
| PN-GNN-Surv (p/c) | 554 [252, 947] | 554 ± 99 (n=5) |
| hindsight-optimal (lower bound) | 26 [10, 50] |  |

GNN-Surv / fewest contacts on parts=5-6: 0.780 [0.488, 1.303], HL -0.02 s, W/T/L 26/21/20, p 0.15 (uncorrected)

#### parts=7-8: 211 states, 34 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1351 [781, 1928] |  |
| outside-in | 406 [36, 858] |  |
| fewest contacts | 444 [135, 831] |  |
| ASAP zero-shot | 857 [431, 1341] |  |
| MLP-BCE (p) | 424 [158, 741] | 424 ± 56 (n=5) |
| MLP-Surv (p/c) | 311 [130, 529] | 311 ± 91 (n=5) |
| GNN-BCE (p) | 438 [143, 795] | 438 ± 43 (n=5) |
| GNN-Surv (p/c) | 341 [85, 710] | 341 ± 41 (n=5) |
| PN-GNN-Surv (p/c) | 289 [77, 563] | 289 ± 91 (n=5) |
| hindsight-optimal (lower bound) | 39 [5, 91] |  |

GNN-Surv / fewest contacts on parts=7-8: 0.769 [0.328, 1.281], HL -0.14 s, W/T/L 21/4/9, p 0.064 (uncorrected)

#### parts=9-10: 130 states, 15 assemblies — **UNDERPOWERED (< 30 assemblies), no conclusion**

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 485 [224, 802] |  |
| outside-in | 52 [16, 105] |  |
| fewest contacts | 174 [28, 399] |  |
| ASAP zero-shot | 83 [22, 166] |  |
| MLP-BCE (p) | 184 [62, 329] | 184 ± 72 (n=5) |
| MLP-Surv (p/c) | 195 [89, 308] | 195 ± 67 (n=5) |
| GNN-BCE (p) | 109 [37, 214] | 109 ± 65 (n=5) |
| GNN-Surv (p/c) | 150 [36, 292] | 150 ± 48 (n=5) |
| PN-GNN-Surv (p/c) | 186 [60, 338] | 186 ± 48 (n=5) |
| hindsight-optimal (lower bound) | 5 [3, 9] |  |

GNN-Surv / fewest contacts on parts=9-10: 0.864 [0.429, 2.271], HL +0.01 s, W/T/L 6/1/8, p 0.98 (uncorrected)

#### parts=11-12: 113 states, 11 assemblies — **UNDERPOWERED (< 30 assemblies), no conclusion**

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1636 [915, 2407] |  |
| outside-in | 563 [116, 1178] |  |
| fewest contacts | 368 [95, 708] |  |
| ASAP zero-shot | 1142 [424, 2025] |  |
| MLP-BCE (p) | 433 [186, 758] | 433 ± 83 (n=5) |
| MLP-Surv (p/c) | 476 [210, 869] | 476 ± 67 (n=5) |
| GNN-BCE (p) | 383 [130, 712] | 383 ± 121 (n=5) |
| GNN-Surv (p/c) | 402 [112, 774] | 402 ± 128 (n=5) |
| PN-GNN-Surv (p/c) | 316 [102, 565] | 316 ± 74 (n=5) |
| hindsight-optimal (lower bound) | 5 [3, 7] |  |

GNN-Surv / fewest contacts on parts=11-12: 1.093 [0.612, 2.390], HL +0.13 s, W/T/L 4/2/5, p 0.83 (uncorrected)

## Configuration: CMG-RRT only (secondary)

Scored states: 1010; states with no success under this configuration: 20 (every ordering pays all their queries: 1839 s, not in the totals).

#### All scored states: 1010 states, 245 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) | median per-state ratio to optimal [95% CI] | mean queries to 1st success | states solved within T |
|---|---|---|---|---|---|
| random (expectation) | 9347 [7427, 11367] |  | 4.50 [3.74, 5.41] | 1.20 | 0.895 |
| outside-in | 5937 [4576, 7361] |  | 2.02 [1.66, 2.35] | 1.09 | 0.932 |
| fewest contacts | 4736 [3733, 5772] |  | 1.46 [1.28, 1.68] | 1.07 | 0.950 |
| ASAP zero-shot | 6660 [5241, 8272] |  | 2.49 [2.12, 2.96] | 1.11 | 0.909 |
| MLP-BCE (p) | 4460 [3564, 5418] | 4460 ± 175 (n=5) | 1.61 [1.47, 1.81] | 1.07 | 0.948 |
| MLP-Surv (p/c) | 4401 [3512, 5402] | 4401 ± 180 (n=5) | 1.80 [1.63, 2.06] | 1.06 | 0.950 |
| GNN-BCE (p) | 4381 [3501, 5347] | 4381 ± 138 (n=5) | 2.06 [1.87, 2.39] | 1.06 | 0.952 |
| GNN-Surv (p/c) | 4016 [3146, 4962] | 4016 ± 195 (n=5) | 1.66 [1.51, 1.93] | 1.05 | 0.961 |
| PN-GNN-Surv (p/c) | 4070 [3228, 4994] | 4070 ± 110 (n=5) | 1.71 [1.57, 1.97] | 1.05 | 0.960 |
| hindsight-optimal (lower bound) | 1063 [846, 1344] |  | 1.00 [1.00, 1.00] | 1.00 | 1.000 |

Paired per assembly (all scored states; Holm family of 9; ratio = A/B of totals; HL = Hodges–Lehmann median difference A − B per assembly, negative = A cheaper; W/T/L for A, tie |d| ≤ 0.01 s):

| A vs B | ratio of totals [95% CI] | HL diff (s) [95% CI] | W / T / L | Wilcoxon p | Holm p |
|---|---|---|---|---|---|
| GNN-Surv (p/c) vs random (expectation) | 0.430 [0.358, 0.512] | -9.78 [-15.25, -6.27] | 191 / 2 / 52 | 2e-22 | 1.8e-21 |
| GNN-Surv (p/c) vs outside-in | 0.676 [0.571, 0.811] | -1.14 [-2.17, -0.39] | 156 / 17 / 72 | 9.5e-08 | 6.6e-07 |
| GNN-Surv (p/c) vs fewest contacts | 0.848 [0.745, 0.959] | -0.42 [-1.09, -0.16] | 147 / 15 / 83 | 0.00029 | 0.0015 |
| GNN-Surv (p/c) vs ASAP zero-shot | 0.603 [0.495, 0.727] | -2.46 [-5.17, -1.19] | 183 / 9 / 53 | 2e-14 | 1.6e-13 |
| GNN-Surv (p/c) vs MLP-Surv (p/c) | 0.912 [0.824, 1.014] | -0.12 [-0.35, +0.00] | 125 / 20 / 100 | 0.069 | 0.27 |
| GNN-Surv (p/c) vs GNN-BCE (p) | 0.917 [0.825, 1.014] | -0.28 [-0.54, -0.12] | 139 / 24 / 82 | 0.00024 | 0.0015 |
| GNN-Surv (p/c) vs PN-GNN-Surv (p/c) | 0.987 [0.901, 1.075] | -0.07 [-0.20, +0.00] | 118 / 37 / 90 | 0.091 | 0.27 |
| GNN-BCE (p) vs MLP-BCE (p) | 0.982 [0.880, 1.089] | +0.09 [-0.04, +0.31] | 109 / 22 / 114 | 0.22 | 0.44 |
| MLP-Surv (p/c) vs MLP-BCE (p) | 0.987 [0.912, 1.061] | -0.01 [-0.12, +0.09] | 113 / 28 / 104 | 0.82 | 0.82 |

**§7 rule (val, cmgrrt_only):** best heuristic on this split = fewest contacts; GNN-Surv / heuristic = 0.848 [0.745, 0.959], HL -0.42 s, Holm p 0.0015 → (a) True, (b) True: **beats** (val: development only; the registered rule applies to test)

### Subsets (cmgrrt_only; reported, never used for selection)

#### rot_state: 82 states, 44 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1668 [1145, 2253] |  |
| outside-in | 1129 [705, 1625] |  |
| fewest contacts | 855 [518, 1268] |  |
| ASAP zero-shot | 1219 [795, 1731] |  |
| MLP-BCE (p) | 742 [486, 1036] | 742 ± 66 (n=5) |
| MLP-Surv (p/c) | 692 [474, 945] | 692 ± 83 (n=5) |
| GNN-BCE (p) | 788 [514, 1120] | 788 ± 58 (n=5) |
| GNN-Surv (p/c) | 712 [437, 1092] | 712 ± 86 (n=5) |
| PN-GNN-Surv (p/c) | 754 [469, 1104] | 754 ± 88 (n=5) |
| hindsight-optimal (lower bound) | 185 [125, 259] |  |

GNN-Surv / fewest contacts on rot_state: 0.833 [0.616, 1.106], HL -0.23 s, W/T/L 20/6/18, p 0.6 (uncorrected)

#### non_rot_state: 928 states, 240 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 7679 [6223, 9411] |  |
| outside-in | 4808 [3684, 6178] |  |
| fewest contacts | 3881 [3040, 4816] |  |
| ASAP zero-shot | 5441 [4260, 6886] |  |
| MLP-BCE (p) | 3717 [2936, 4601] | 3717 ± 189 (n=5) |
| MLP-Surv (p/c) | 3710 [2893, 4619] | 3710 ± 126 (n=5) |
| GNN-BCE (p) | 3593 [2850, 4474] | 3593 ± 146 (n=5) |
| GNN-Surv (p/c) | 3304 [2565, 4177] | 3304 ± 187 (n=5) |
| PN-GNN-Surv (p/c) | 3317 [2621, 4150] | 3317 ± 79 (n=5) |
| hindsight-optimal (lower bound) | 878 [686, 1144] |  |

GNN-Surv / fewest contacts on non_rot_state: 0.851 [0.740, 0.982], HL -0.33 s, W/T/L 142/17/81, p 0.00044 (uncorrected)

#### source=v1: 678 states, 194 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 4758 [3875, 5814] |  |
| outside-in | 3277 [2460, 4181] |  |
| fewest contacts | 2888 [2212, 3665] |  |
| ASAP zero-shot | 3690 [2891, 4539] |  |
| MLP-BCE (p) | 2674 [2047, 3332] | 2674 ± 116 (n=5) |
| MLP-Surv (p/c) | 2492 [1929, 3095] | 2492 ± 200 (n=5) |
| GNN-BCE (p) | 2587 [1980, 3289] | 2587 ± 193 (n=5) |
| GNN-Surv (p/c) | 2309 [1773, 2961] | 2309 ± 134 (n=5) |
| PN-GNN-Surv (p/c) | 2419 [1840, 3112] | 2419 ± 137 (n=5) |
| hindsight-optimal (lower bound) | 601 [487, 734] |  |

GNN-Surv / fewest contacts on source=v1: 0.800 [0.668, 0.963], HL -0.44 s, W/T/L 121/13/60, p 3.4e-05 (uncorrected)

#### source=fresh-9to12: 180 states, 19 assemblies — **UNDERPOWERED (< 30 assemblies), no conclusion**

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 2060 [1174, 3037] |  |
| outside-in | 1189 [561, 2065] |  |
| fewest contacts | 1037 [555, 1615] |  |
| ASAP zero-shot | 1603 [757, 2626] |  |
| MLP-BCE (p) | 1058 [580, 1604] | 1058 ± 76 (n=5) |
| MLP-Surv (p/c) | 1167 [640, 1786] | 1167 ± 98 (n=5) |
| GNN-BCE (p) | 1058 [578, 1636] | 1058 ± 135 (n=5) |
| GNN-Surv (p/c) | 1005 [503, 1598] | 1005 ± 214 (n=5) |
| PN-GNN-Surv (p/c) | 836 [469, 1262] | 836 ± 73 (n=5) |
| hindsight-optimal (lower bound) | 212 [95, 422] |  |

GNN-Surv / fewest contacts on source=fresh-9to12: 0.969 [0.794, 1.156], HL -0.53 s, W/T/L 9/0/10, p 0.89 (uncorrected)

#### source=fresh-allowance: 152 states, 32 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 2529 [1471, 3756] |  |
| outside-in | 1472 [819, 2343] |  |
| fewest contacts | 811 [474, 1220] |  |
| ASAP zero-shot | 1366 [818, 2091] |  |
| MLP-BCE (p) | 727 [438, 1052] | 727 ± 105 (n=5) |
| MLP-Surv (p/c) | 742 [485, 1029] | 742 ± 90 (n=5) |
| GNN-BCE (p) | 735 [480, 1019] | 735 ± 55 (n=5) |
| GNN-Surv (p/c) | 701 [452, 986] | 701 ± 105 (n=5) |
| PN-GNN-Surv (p/c) | 815 [480, 1215] | 815 ± 47 (n=5) |
| hindsight-optimal (lower bound) | 250 [164, 349] |  |

GNN-Surv / fewest contacts on source=fresh-allowance: 0.865 [0.675, 1.161], HL -0.33 s, W/T/L 17/2/13, p 0.57 (uncorrected)

#### parts=3-4: 267 states, 118 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1521 [1183, 1858] |  |
| outside-in | 1230 [880, 1624] |  |
| fewest contacts | 1064 [756, 1404] |  |
| ASAP zero-shot | 1227 [904, 1574] |  |
| MLP-BCE (p) | 1004 [685, 1353] | 1004 ± 79 (n=5) |
| MLP-Surv (p/c) | 939 [659, 1251] | 939 ± 39 (n=5) |
| GNN-BCE (p) | 816 [610, 1040] | 816 ± 103 (n=5) |
| GNN-Surv (p/c) | 764 [544, 1006] | 764 ± 150 (n=5) |
| PN-GNN-Surv (p/c) | 775 [577, 980] | 775 ± 71 (n=5) |
| hindsight-optimal (lower bound) | 257 [196, 326] |  |

GNN-Surv / fewest contacts on parts=3-4: 0.718 [0.583, 0.862], HL -0.32 s, W/T/L 74/14/30, p 2.8e-05 (uncorrected)

#### parts=5-6: 289 states, 67 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 2242 [1675, 2855] |  |
| outside-in | 1790 [1147, 2518] |  |
| fewest contacts | 1299 [850, 1816] |  |
| ASAP zero-shot | 1686 [1146, 2258] |  |
| MLP-BCE (p) | 1135 [755, 1563] | 1135 ± 66 (n=5) |
| MLP-Surv (p/c) | 1118 [744, 1557] | 1118 ± 69 (n=5) |
| GNN-BCE (p) | 1250 [833, 1715] | 1250 ± 75 (n=5) |
| GNN-Surv (p/c) | 1202 [811, 1653] | 1202 ± 133 (n=5) |
| PN-GNN-Surv (p/c) | 1229 [790, 1710] | 1229 ± 104 (n=5) |
| hindsight-optimal (lower bound) | 265 [200, 336] |  |

GNN-Surv / fewest contacts on parts=5-6: 0.926 [0.683, 1.287], HL -0.25 s, W/T/L 38/1/28, p 0.33 (uncorrected)

#### parts=7-8: 211 states, 34 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 2019 [1367, 2663] |  |
| outside-in | 986 [587, 1470] |  |
| fewest contacts | 961 [570, 1429] |  |
| ASAP zero-shot | 1552 [1055, 2088] |  |
| MLP-BCE (p) | 868 [543, 1236] | 868 ± 88 (n=5) |
| MLP-Surv (p/c) | 755 [484, 1072] | 755 ± 97 (n=5) |
| GNN-BCE (p) | 909 [553, 1313] | 909 ± 101 (n=5) |
| GNN-Surv (p/c) | 739 [438, 1114] | 739 ± 63 (n=5) |
| PN-GNN-Surv (p/c) | 779 [464, 1146] | 779 ± 82 (n=5) |
| hindsight-optimal (lower bound) | 209 [132, 302] |  |

GNN-Surv / fewest contacts on parts=7-8: 0.769 [0.556, 1.008], HL -1.60 s, W/T/L 23/0/11, p 0.024 (uncorrected)

#### parts=9-10: 130 states, 15 assemblies — **UNDERPOWERED (< 30 assemblies), no conclusion**

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1043 [644, 1509] |  |
| outside-in | 631 [345, 973] |  |
| fewest contacts | 568 [278, 909] |  |
| ASAP zero-shot | 460 [275, 658] |  |
| MLP-BCE (p) | 621 [320, 973] | 621 ± 84 (n=5) |
| MLP-Surv (p/c) | 649 [394, 945] | 649 ± 103 (n=5) |
| GNN-BCE (p) | 486 [306, 697] | 486 ± 88 (n=5) |
| GNN-Surv (p/c) | 552 [305, 840] | 552 ± 52 (n=5) |
| PN-GNN-Surv (p/c) | 546 [290, 840] | 546 ± 79 (n=5) |
| hindsight-optimal (lower bound) | 110 [62, 179] |  |

GNN-Surv / fewest contacts on parts=9-10: 0.971 [0.719, 1.318], HL +2.75 s, W/T/L 5/0/10, p 0.36 (uncorrected)

#### parts=11-12: 113 states, 11 assemblies — **UNDERPOWERED (< 30 assemblies), no conclusion**

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 2521 [1567, 3420] |  |
| outside-in | 1302 [574, 2204] |  |
| fewest contacts | 845 [444, 1320] |  |
| ASAP zero-shot | 1735 [938, 2623] |  |
| MLP-BCE (p) | 832 [464, 1256] | 832 ± 94 (n=5) |
| MLP-Surv (p/c) | 941 [522, 1460] | 941 ± 115 (n=5) |
| GNN-BCE (p) | 920 [498, 1400] | 920 ± 201 (n=5) |
| GNN-Surv (p/c) | 759 [340, 1282] | 759 ± 162 (n=5) |
| PN-GNN-Surv (p/c) | 742 [394, 1114] | 742 ± 38 (n=5) |
| hindsight-optimal (lower bound) | 222 [92, 419] |  |

GNN-Surv / fewest contacts on parts=11-12: 0.898 [0.673, 1.119], HL -10.18 s, W/T/L 7/0/4, p 0.37 (uncorrected)

## Prediction quality (main configuration, every node of every state with >= 1 success)

ECE: 10 equal-width bins of p vs observed success. Within-state C-index (Harrell, censored at min(cost, T)): comparable pair = part i succeeded at t_i < t_j at the same state; speed = p (BCE, ASAP) or −c (survival). Mean ± std over seeds.

| model | ECE of p | C-index within state | C-index pooled |
|---|---|---|---|
| ASAP zero-shot | 0.581 | 0.563 | 0.606 |
| MLP-BCE (p) | 0.021 ± 0.007 | 0.624 ± 0.003 | 0.729 ± 0.005 |
| MLP-Surv (p/c) | 0.028 ± 0.014 | 0.635 ± 0.009 | 0.735 ± 0.016 |
| GNN-BCE (p) | 0.076 ± 0.021 | 0.623 ± 0.011 | 0.701 ± 0.023 |
| GNN-Surv (p/c) | 0.031 ± 0.006 | 0.669 ± 0.005 | 0.766 ± 0.008 |
| PN-GNN-Surv (p/c) | 0.038 ± 0.009 | 0.671 ± 0.010 | 0.766 ± 0.009 |

ASAP's score is P(part is the next removed part), not P(planner success), so its ECE is not a calibration claim.

![totals](figures/replay_val_totals.png) (vector: `figures/replay_val_totals.pdf`)
