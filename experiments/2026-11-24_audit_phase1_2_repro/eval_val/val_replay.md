# Run 05 replay on v2 **val** (2026-11-24)

Script `scripts/eval_v2.py`; raw per-state costs `experiments/2026-11-24_audit_phase1_2_repro/eval_val/per_state.jsonl`, all numbers `experiments/2026-11-24_audit_phase1_2_repro/eval_val/results.json`. Graphs `data/processed/run05/graphs_train_val.pt` (1030 val states, 250 assemblies). Replay of logged pilot_v2 queries (nothing simulated). Trained variants: per-state cost = mean over their seeds; 'seeds' = mean ± std of the per-seed totals. CIs: bootstrap over assemblies (10000 resamples, seed 0; median-ratio CIs 2000 resamples; HL CIs 2,000). Scores computed on cpu.

**Selection bias (val).** Val replay cost chose every trained variant's config and checkpoint epoch (PREREG §3), and these tables report the same cost on the same states. The trained models' val numbers, CIs and p-values are therefore optimistically biased relative to the untrained heuristics and are descriptive only. Per-epoch val cost fluctuates by more than most between-variant gaps (`reports/run05/training.md` curves). Unbiased estimates: the test set (Phase 3) and the group CV with inner early stopping (Phase 2).


## Configuration: MAIN (pre-check → CMG-RRT)

Scored states: 1010; states with no success under this configuration: 20 (every ordering pays all their queries: 1857 s, not in the totals).

#### All scored states: 1010 states, 245 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) | median per-state ratio to optimal [95% CI] | mean queries to 1st success | states solved within T |
|---|---|---|---|---|---|
| random (expectation) | 6059 [4679, 7619] |  | 12.69 [8.81, 18.20] | 1.17 | — |
| outside-in | 2800 [1829, 3909] |  | 1.89 [1.55, 2.32] | 1.08 | 0.948 |
| fewest contacts | 2275 [1556, 3078] |  | 1.39 [1.20, 1.70] | 1.06 | 0.955 |
| ASAP zero-shot | 3549 [2417, 4909] |  | 2.21 [1.79, 2.66] | 1.10 | 0.924 |
| MLP-BCE (p) | 2205 [1564, 2925] | 2205 ± 125 (n=5) | 1.74 [1.53, 1.99] | 1.06 | 0.956 |
| MLP-Surv (p/c) | 2026 [1444, 2703] | 2026 ± 170 (n=5) | 1.86 [1.65, 2.17] | 1.05 | 0.957 |
| GNN-BCE (p) | 1903 [1323, 2567] | 1903 ± 136 (n=5) | 2.14 [1.89, 2.55] | 1.05 | 0.964 |
| GNN-Surv (p/c) | 1835 [1228, 2526] | 1835 ± 129 (n=5) | 1.51 [1.37, 1.72] | 1.05 | 0.969 |
| GNN-Surv-Tail (p/c) | 1637 [1115, 2228] | 1637 ± 106 (n=5) | 1.55 [1.42, 1.75] | 1.04 | 0.969 |
| PN-GNN-Surv (p/c) | 1684 [1167, 2267] | 1684 ± 88 (n=5) | 1.55 [1.37, 1.74] | 1.04 | 0.968 |
| ASAP-retrained | 3145 [2182, 4374] | 3145 ± 197 (n=5) | 2.26 [1.88, 2.96] | 1.08 | 0.937 |
| hindsight-optimal (lower bound) | 115 [65, 180] |  | 1.00 [1.00, 1.00] | 1.00 | 1.000 |

Paired per assembly (all scored states; Holm family of 11; ratio = A/B of totals; HL = Hodges–Lehmann median difference A − B per assembly, negative = A cheaper; W/T/L for A, tie |d| ≤ 0.01 s):

| A vs B | ratio of totals [95% CI] | HL diff (s) [95% CI] | W / T / L | Wilcoxon p | Holm p |
|---|---|---|---|---|---|
| GNN-Surv (p/c) vs random (expectation) | 0.303 [0.219, 0.399] | -7.37 [-11.20, -4.99] | 192 / 25 / 28 | 2.1e-27 | 2.3e-26 |
| GNN-Surv (p/c) vs outside-in | 0.656 [0.461, 0.928] | -0.02 [-0.07, -0.00] | 98 / 87 / 60 | 0.0018 | 0.011 |
| GNN-Surv (p/c) vs fewest contacts | 0.807 [0.632, 1.016] | -0.02 [-0.06, -0.00] | 99 / 89 / 57 | 0.00042 | 0.0034 |
| GNN-Surv (p/c) vs ASAP zero-shot | 0.517 [0.353, 0.733] | -0.09 [-0.31, -0.03] | 126 / 64 / 55 | 2e-07 | 2e-06 |
| GNN-Surv (p/c) vs ASAP-retrained | 0.583 [0.448, 0.758] | -0.09 [-0.27, -0.03] | 120 / 66 / 59 | 5e-06 | 4.5e-05 |
| GNN-Surv (p/c) vs MLP-Surv (p/c) | 0.906 [0.712, 1.126] | -0.01 [-0.03, -0.00] | 90 / 91 / 64 | 0.02 | 0.099 |
| GNN-Surv (p/c) vs GNN-BCE (p) | 0.964 [0.774, 1.184] | -0.01 [-0.04, -0.00] | 102 / 88 / 55 | 0.00047 | 0.0034 |
| GNN-Surv (p/c) vs GNN-Surv-Tail (p/c) | 1.121 [0.989, 1.258] | +0.00 [+0.00, +0.01] | 53 / 117 / 75 | 0.062 | 0.25 |
| GNN-Surv (p/c) vs PN-GNN-Surv (p/c) | 1.090 [0.920, 1.275] | +0.00 [-0.00, +0.00] | 63 / 117 / 65 | 0.79 | 1 |
| GNN-BCE (p) vs MLP-BCE (p) | 0.863 [0.710, 1.035] | -0.00 [-0.01, +0.00] | 75 / 96 / 74 | 0.65 | 1 |
| MLP-Surv (p/c) vs MLP-BCE (p) | 0.919 [0.796, 1.061] | -0.00 [-0.01, +0.00] | 78 / 100 / 67 | 0.23 | 0.69 |

*§7 conditions, descriptive only (val, main; the registered rule applies to test, main configuration):* best heuristic on this split = fewest contacts; GNN-Surv / heuristic = 0.807 [0.632, 1.016], HL -0.02 s, Holm p 0.0034 → (a) False, (b) True; on val these are biased toward the trained models (val chose their configs and epochs)

### Subsets (main; reported, never used for selection)

#### rot_state: 82 states, 44 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1415 [965, 1936] |  |
| outside-in | 904 [472, 1410] |  |
| fewest contacts | 635 [289, 1061] |  |
| ASAP zero-shot | 915 [519, 1378] |  |
| MLP-BCE (p) | 570 [327, 852] | 570 ± 32 (n=5) |
| MLP-Surv (p/c) | 480 [275, 717] | 480 ± 88 (n=5) |
| GNN-BCE (p) | 636 [357, 969] | 636 ± 45 (n=5) |
| GNN-Surv (p/c) | 566 [301, 929] | 566 ± 77 (n=5) |
| GNN-Surv-Tail (p/c) | 503 [267, 801] | 503 ± 93 (n=5) |
| PN-GNN-Surv (p/c) | 529 [290, 829] | 529 ± 91 (n=5) |
| ASAP-retrained | 913 [518, 1384] | 913 ± 153 (n=5) |
| hindsight-optimal (lower bound) | 73 [25, 134] |  |

GNN-Surv / fewest contacts on rot_state: 0.891 [0.599, 1.418], HL -0.01 s, W/T/L 19/10/15, p 0.73 (uncorrected)

#### non_rot_state: 928 states, 240 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 4644 [3606, 5809] |  |
| outside-in | 1896 [1175, 2736] |  |
| fewest contacts | 1640 [1059, 2295] |  |
| ASAP zero-shot | 2634 [1718, 3813] |  |
| MLP-BCE (p) | 1634 [1109, 2211] | 1634 ± 132 (n=5) |
| MLP-Surv (p/c) | 1547 [1057, 2111] | 1547 ± 115 (n=5) |
| GNN-BCE (p) | 1267 [872, 1713] | 1267 ± 159 (n=5) |
| GNN-Surv (p/c) | 1269 [796, 1814] | 1269 ± 136 (n=5) |
| GNN-Surv-Tail (p/c) | 1134 [746, 1575] | 1134 ± 172 (n=5) |
| PN-GNN-Surv (p/c) | 1155 [751, 1617] | 1155 ± 34 (n=5) |
| ASAP-retrained | 2232 [1513, 3114] | 2232 ± 170 (n=5) |
| hindsight-optimal (lower bound) | 42 [31, 56] |  |

GNN-Surv / fewest contacts on non_rot_state: 0.774 [0.571, 1.042], HL -0.01 s, W/T/L 93/95/52, p 0.00021 (uncorrected)

#### source=v1: 678 states, 194 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 3142 [2370, 4003] |  |
| outside-in | 1681 [992, 2493] |  |
| fewest contacts | 1471 [896, 2142] |  |
| ASAP zero-shot | 1776 [1164, 2458] |  |
| MLP-BCE (p) | 1428 [909, 2015] | 1428 ± 49 (n=5) |
| MLP-Surv (p/c) | 1211 [796, 1694] | 1211 ± 172 (n=5) |
| GNN-BCE (p) | 1213 [749, 1742] | 1213 ± 89 (n=5) |
| GNN-Surv (p/c) | 1082 [639, 1612] | 1082 ± 96 (n=5) |
| GNN-Surv-Tail (p/c) | 1019 [627, 1488] | 1019 ± 87 (n=5) |
| PN-GNN-Surv (p/c) | 1011 [608, 1492] | 1011 ± 122 (n=5) |
| ASAP-retrained | 1959 [1303, 2712] | 1959 ± 150 (n=5) |
| hindsight-optimal (lower bound) | 82 [34, 146] |  |

GNN-Surv / fewest contacts on source=v1: 0.735 [0.529, 1.011], HL -0.02 s, W/T/L 78/79/37, p 1.9e-05 (uncorrected)

#### source=fresh-9to12: 180 states, 19 assemblies — **UNDERPOWERED (< 30 assemblies), no conclusion**

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1044 [489, 1722] |  |
| outside-in | 216 [41, 451] |  |
| fewest contacts | 317 [71, 682] |  |
| ASAP zero-shot | 828 [172, 1719] |  |
| MLP-BCE (p) | 413 [157, 783] | 413 ± 74 (n=5) |
| MLP-Surv (p/c) | 447 [154, 891] | 447 ± 89 (n=5) |
| GNN-BCE (p) | 332 [103, 682] | 332 ± 67 (n=5) |
| GNN-Surv (p/c) | 424 [115, 841] | 424 ± 150 (n=5) |
| GNN-Surv-Tail (p/c) | 323 [83, 683] | 323 ± 100 (n=5) |
| PN-GNN-Surv (p/c) | 284 [89, 529] | 284 ± 80 (n=5) |
| ASAP-retrained | 678 [130, 1582] | 678 ± 152 (n=5) |
| hindsight-optimal (lower bound) | 6 [4, 9] |  |

GNN-Surv / fewest contacts on source=fresh-9to12: 1.340 [0.795, 3.226], HL +0.80 s, W/T/L 5/2/12, p 0.14 (uncorrected)

#### source=fresh-allowance: 152 states, 32 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1873 [1024, 2903] |  |
| outside-in | 903 [333, 1661] |  |
| fewest contacts | 487 [222, 797] |  |
| ASAP zero-shot | 944 [423, 1636] |  |
| MLP-BCE (p) | 363 [173, 589] | 363 ± 121 (n=5) |
| MLP-Surv (p/c) | 368 [211, 541] | 368 ± 125 (n=5) |
| GNN-BCE (p) | 358 [172, 585] | 358 ± 62 (n=5) |
| GNN-Surv (p/c) | 329 [153, 535] | 329 ± 111 (n=5) |
| GNN-Surv-Tail (p/c) | 296 [137, 485] | 296 ± 120 (n=5) |
| PN-GNN-Surv (p/c) | 389 [184, 638] | 389 ± 99 (n=5) |
| ASAP-retrained | 508 [286, 769] | 508 ± 60 (n=5) |
| hindsight-optimal (lower bound) | 27 [12, 48] |  |

GNN-Surv / fewest contacts on source=fresh-allowance: 0.675 [0.473, 1.007], HL -0.28 s, W/T/L 16/8/8, p 0.11 (uncorrected)

#### parts=3-4: 267 states, 118 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1063 [764, 1387] |  |
| outside-in | 677 [371, 1032] |  |
| fewest contacts | 523 [268, 822] |  |
| ASAP zero-shot | 668 [380, 989] |  |
| MLP-BCE (p) | 592 [300, 943] | 592 ± 61 (n=5) |
| MLP-Surv (p/c) | 551 [293, 855] | 551 ± 34 (n=5) |
| GNN-BCE (p) | 347 [192, 540] | 347 ± 81 (n=5) |
| GNN-Surv (p/c) | 343 [184, 537] | 343 ± 134 (n=5) |
| GNN-Surv-Tail (p/c) | 373 [204, 570] | 373 ± 53 (n=5) |
| PN-GNN-Surv (p/c) | 340 [197, 507] | 340 ± 60 (n=5) |
| ASAP-retrained | 637 [394, 918] | 637 ± 60 (n=5) |
| hindsight-optimal (lower bound) | 39 [14, 74] |  |

GNN-Surv / fewest contacts on parts=3-4: 0.657 [0.428, 1.007], HL -0.01 s, W/T/L 42/61/15, p 0.00026 (uncorrected)

#### parts=5-6: 289 states, 67 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1524 [1010, 2065] |  |
| outside-in | 1103 [521, 1796] |  |
| fewest contacts | 766 [351, 1253] |  |
| ASAP zero-shot | 800 [391, 1238] |  |
| MLP-BCE (p) | 570 [259, 946] | 570 ± 39 (n=5) |
| MLP-Surv (p/c) | 493 [233, 820] | 493 ± 76 (n=5) |
| GNN-BCE (p) | 627 [317, 982] | 627 ± 73 (n=5) |
| GNN-Surv (p/c) | 598 [290, 973] | 598 ± 110 (n=5) |
| GNN-Surv-Tail (p/c) | 498 [228, 827] | 498 ± 106 (n=5) |
| PN-GNN-Surv (p/c) | 554 [252, 926] | 554 ± 99 (n=5) |
| ASAP-retrained | 892 [499, 1369] | 892 ± 97 (n=5) |
| hindsight-optimal (lower bound) | 26 [10, 50] |  |

GNN-Surv / fewest contacts on parts=5-6: 0.780 [0.494, 1.307], HL -0.02 s, W/T/L 26/21/20, p 0.15 (uncorrected)

#### parts=7-8: 211 states, 34 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1351 [805, 1964] |  |
| outside-in | 406 [36, 856] |  |
| fewest contacts | 444 [135, 847] |  |
| ASAP zero-shot | 857 [429, 1348] |  |
| MLP-BCE (p) | 424 [168, 736] | 424 ± 56 (n=5) |
| MLP-Surv (p/c) | 311 [132, 529] | 311 ± 91 (n=5) |
| GNN-BCE (p) | 438 [154, 790] | 438 ± 43 (n=5) |
| GNN-Surv (p/c) | 341 [84, 719] | 341 ± 41 (n=5) |
| GNN-Surv-Tail (p/c) | 297 [80, 580] | 297 ± 58 (n=5) |
| PN-GNN-Surv (p/c) | 289 [79, 577] | 289 ± 91 (n=5) |
| ASAP-retrained | 727 [294, 1249] | 727 ± 48 (n=5) |
| hindsight-optimal (lower bound) | 39 [6, 93] |  |

GNN-Surv / fewest contacts on parts=7-8: 0.769 [0.330, 1.281], HL -0.14 s, W/T/L 21/4/9, p 0.064 (uncorrected)

#### parts=9-10: 130 states, 15 assemblies — **UNDERPOWERED (< 30 assemblies), no conclusion**

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 485 [223, 808] |  |
| outside-in | 52 [17, 105] |  |
| fewest contacts | 174 [28, 393] |  |
| ASAP zero-shot | 83 [22, 165] |  |
| MLP-BCE (p) | 184 [62, 329] | 184 ± 72 (n=5) |
| MLP-Surv (p/c) | 195 [91, 312] | 195 ± 67 (n=5) |
| GNN-BCE (p) | 109 [36, 210] | 109 ± 65 (n=5) |
| GNN-Surv (p/c) | 150 [37, 292] | 150 ± 48 (n=5) |
| GNN-Surv-Tail (p/c) | 133 [53, 229] | 133 ± 60 (n=5) |
| PN-GNN-Surv (p/c) | 186 [60, 342] | 186 ± 48 (n=5) |
| ASAP-retrained | 199 [70, 355] | 199 ± 41 (n=5) |
| hindsight-optimal (lower bound) | 5 [3, 9] |  |

GNN-Surv / fewest contacts on parts=9-10: 0.864 [0.419, 2.338], HL +0.01 s, W/T/L 6/1/8, p 0.98 (uncorrected)

#### parts=11-12: 113 states, 11 assemblies — **UNDERPOWERED (< 30 assemblies), no conclusion**

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1636 [875, 2424] |  |
| outside-in | 563 [112, 1185] |  |
| fewest contacts | 368 [94, 722] |  |
| ASAP zero-shot | 1142 [407, 2012] |  |
| MLP-BCE (p) | 433 [174, 769] | 433 ± 83 (n=5) |
| MLP-Surv (p/c) | 476 [207, 869] | 476 ± 67 (n=5) |
| GNN-BCE (p) | 383 [125, 718] | 383 ± 121 (n=5) |
| GNN-Surv (p/c) | 402 [110, 784] | 402 ± 128 (n=5) |
| GNN-Surv-Tail (p/c) | 336 [81, 680] | 336 ± 50 (n=5) |
| PN-GNN-Surv (p/c) | 316 [95, 570] | 316 ± 74 (n=5) |
| ASAP-retrained | 690 [144, 1527] | 690 ± 171 (n=5) |
| hindsight-optimal (lower bound) | 5 [3, 8] |  |

GNN-Surv / fewest contacts on parts=11-12: 1.093 [0.617, 2.374], HL +0.13 s, W/T/L 4/2/5, p 0.83 (uncorrected)

## Configuration: CMG-RRT only (secondary)

Scored states: 1010; states with no success under this configuration: 20 (every ordering pays all their queries: 1839 s, not in the totals).

#### All scored states: 1010 states, 245 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) | median per-state ratio to optimal [95% CI] | mean queries to 1st success | states solved within T |
|---|---|---|---|---|---|
| random (expectation) | 9347 [7474, 11396] |  | 4.50 [3.74, 5.41] | 1.20 | — |
| outside-in | 5937 [4600, 7452] |  | 2.02 [1.66, 2.35] | 1.09 | 0.932 |
| fewest contacts | 4736 [3763, 5797] |  | 1.46 [1.28, 1.68] | 1.07 | 0.950 |
| ASAP zero-shot | 6660 [5256, 8298] |  | 2.49 [2.13, 2.95] | 1.11 | 0.909 |
| MLP-BCE (p) | 4460 [3578, 5467] | 4460 ± 175 (n=5) | 1.61 [1.47, 1.81] | 1.07 | 0.948 |
| MLP-Surv (p/c) | 4401 [3515, 5434] | 4401 ± 180 (n=5) | 1.80 [1.63, 2.06] | 1.06 | 0.950 |
| GNN-BCE (p) | 4381 [3518, 5366] | 4381 ± 138 (n=5) | 2.06 [1.87, 2.39] | 1.06 | 0.952 |
| GNN-Surv (p/c) | 4016 [3173, 4969] | 4016 ± 195 (n=5) | 1.66 [1.51, 1.93] | 1.05 | 0.961 |
| GNN-Surv-Tail (p/c) | 3839 [3058, 4739] | 3839 ± 191 (n=5) | 1.74 [1.58, 1.94] | 1.05 | 0.960 |
| PN-GNN-Surv (p/c) | 4070 [3253, 4986] | 4070 ± 110 (n=5) | 1.71 [1.57, 1.97] | 1.05 | 0.960 |
| ASAP-retrained | 5614 [4369, 7148] | 5614 ± 244 (n=5) | 1.84 [1.66, 2.12] | 1.10 | 0.929 |
| hindsight-optimal (lower bound) | 1063 [842, 1346] |  | 1.00 [1.00, 1.00] | 1.00 | 1.000 |

Paired per assembly (all scored states; Holm family of 11; ratio = A/B of totals; HL = Hodges–Lehmann median difference A − B per assembly, negative = A cheaper; W/T/L for A, tie |d| ≤ 0.01 s):

| A vs B | ratio of totals [95% CI] | HL diff (s) [95% CI] | W / T / L | Wilcoxon p | Holm p |
|---|---|---|---|---|---|
| GNN-Surv (p/c) vs random (expectation) | 0.430 [0.356, 0.510] | -9.78 [-15.25, -6.27] | 191 / 2 / 52 | 2e-22 | 2.2e-21 |
| GNN-Surv (p/c) vs outside-in | 0.676 [0.569, 0.806] | -1.14 [-2.17, -0.39] | 156 / 17 / 72 | 9.5e-08 | 8.5e-07 |
| GNN-Surv (p/c) vs fewest contacts | 0.848 [0.745, 0.962] | -0.42 [-1.09, -0.16] | 147 / 15 / 83 | 0.00029 | 0.0021 |
| GNN-Surv (p/c) vs ASAP zero-shot | 0.603 [0.493, 0.725] | -2.46 [-5.17, -1.19] | 183 / 9 / 53 | 2.1e-14 | 2.1e-13 |
| GNN-Surv (p/c) vs ASAP-retrained | 0.715 [0.612, 0.837] | -0.79 [-2.38, -0.25] | 137 / 10 / 98 | 0.0006 | 0.0036 |
| GNN-Surv (p/c) vs MLP-Surv (p/c) | 0.912 [0.821, 1.014] | -0.12 [-0.35, +0.00] | 125 / 20 / 100 | 0.069 | 0.34 |
| GNN-Surv (p/c) vs GNN-BCE (p) | 0.917 [0.822, 1.013] | -0.28 [-0.54, -0.12] | 139 / 24 / 82 | 0.00024 | 0.0019 |
| GNN-Surv (p/c) vs GNN-Surv-Tail (p/c) | 1.046 [0.978, 1.114] | +0.05 [-0.01, +0.13] | 92 / 39 / 114 | 0.14 | 0.42 |
| GNN-Surv (p/c) vs PN-GNN-Surv (p/c) | 0.987 [0.903, 1.074] | -0.07 [-0.20, +0.00] | 118 / 37 / 90 | 0.091 | 0.36 |
| GNN-BCE (p) vs MLP-BCE (p) | 0.982 [0.880, 1.093] | +0.09 [-0.04, +0.31] | 109 / 22 / 114 | 0.22 | 0.44 |
| MLP-Surv (p/c) vs MLP-BCE (p) | 0.987 [0.912, 1.066] | -0.01 [-0.12, +0.09] | 113 / 28 / 104 | 0.82 | 0.82 |

*§7 conditions, descriptive only (val, cmgrrt_only; the registered rule applies to test, main configuration):* best heuristic on this split = fewest contacts; GNN-Surv / heuristic = 0.848 [0.745, 0.962], HL -0.42 s, Holm p 0.0021 → (a) True, (b) True; on val these are biased toward the trained models (val chose their configs and epochs)

### Subsets (cmgrrt_only; reported, never used for selection)

#### rot_state: 82 states, 44 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1668 [1156, 2254] |  |
| outside-in | 1129 [703, 1629] |  |
| fewest contacts | 855 [515, 1273] |  |
| ASAP zero-shot | 1219 [788, 1728] |  |
| MLP-BCE (p) | 742 [479, 1038] | 742 ± 66 (n=5) |
| MLP-Surv (p/c) | 692 [467, 952] | 692 ± 83 (n=5) |
| GNN-BCE (p) | 788 [506, 1121] | 788 ± 58 (n=5) |
| GNN-Surv (p/c) | 712 [434, 1079] | 712 ± 86 (n=5) |
| GNN-Surv-Tail (p/c) | 668 [407, 993] | 668 ± 77 (n=5) |
| PN-GNN-Surv (p/c) | 754 [461, 1103] | 754 ± 88 (n=5) |
| ASAP-retrained | 1112 [702, 1605] | 1112 ± 152 (n=5) |
| hindsight-optimal (lower bound) | 185 [123, 258] |  |

GNN-Surv / fewest contacts on rot_state: 0.833 [0.614, 1.112], HL -0.23 s, W/T/L 20/6/18, p 0.6 (uncorrected)

#### non_rot_state: 928 states, 240 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 7679 [6216, 9357] |  |
| outside-in | 4808 [3676, 6124] |  |
| fewest contacts | 3881 [3028, 4795] |  |
| ASAP zero-shot | 5441 [4262, 6815] |  |
| MLP-BCE (p) | 3717 [2947, 4561] | 3717 ± 189 (n=5) |
| MLP-Surv (p/c) | 3710 [2920, 4585] | 3710 ± 126 (n=5) |
| GNN-BCE (p) | 3593 [2853, 4440] | 3593 ± 146 (n=5) |
| GNN-Surv (p/c) | 3304 [2561, 4140] | 3304 ± 187 (n=5) |
| GNN-Surv-Tail (p/c) | 3171 [2485, 3946] | 3171 ± 248 (n=5) |
| PN-GNN-Surv (p/c) | 3317 [2619, 4088] | 3317 ± 79 (n=5) |
| ASAP-retrained | 4503 [3483, 5678] | 4503 ± 213 (n=5) |
| hindsight-optimal (lower bound) | 878 [688, 1144] |  |

GNN-Surv / fewest contacts on non_rot_state: 0.851 [0.737, 0.979], HL -0.33 s, W/T/L 142/17/81, p 0.00044 (uncorrected)

#### source=v1: 678 states, 194 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 4758 [3845, 5764] |  |
| outside-in | 3277 [2479, 4197] |  |
| fewest contacts | 2888 [2214, 3663] |  |
| ASAP zero-shot | 3690 [2878, 4549] |  |
| MLP-BCE (p) | 2674 [2063, 3352] | 2674 ± 116 (n=5) |
| MLP-Surv (p/c) | 2492 [1920, 3127] | 2492 ± 200 (n=5) |
| GNN-BCE (p) | 2587 [1983, 3270] | 2587 ± 193 (n=5) |
| GNN-Surv (p/c) | 2309 [1763, 2949] | 2309 ± 134 (n=5) |
| GNN-Surv-Tail (p/c) | 2238 [1705, 2849] | 2238 ± 113 (n=5) |
| PN-GNN-Surv (p/c) | 2419 [1840, 3088] | 2419 ± 137 (n=5) |
| ASAP-retrained | 3331 [2537, 4224] | 3331 ± 214 (n=5) |
| hindsight-optimal (lower bound) | 601 [487, 733] |  |

GNN-Surv / fewest contacts on source=v1: 0.800 [0.667, 0.965], HL -0.44 s, W/T/L 121/13/60, p 3.4e-05 (uncorrected)

#### source=fresh-9to12: 180 states, 19 assemblies — **UNDERPOWERED (< 30 assemblies), no conclusion**

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 2060 [1186, 3069] |  |
| outside-in | 1189 [562, 2035] |  |
| fewest contacts | 1037 [552, 1621] |  |
| ASAP zero-shot | 1603 [766, 2627] |  |
| MLP-BCE (p) | 1058 [587, 1604] | 1058 ± 76 (n=5) |
| MLP-Surv (p/c) | 1167 [650, 1795] | 1167 ± 98 (n=5) |
| GNN-BCE (p) | 1058 [583, 1637] | 1058 ± 135 (n=5) |
| GNN-Surv (p/c) | 1005 [511, 1598] | 1005 ± 214 (n=5) |
| GNN-Surv-Tail (p/c) | 881 [448, 1426] | 881 ± 135 (n=5) |
| PN-GNN-Surv (p/c) | 836 [466, 1257] | 836 ± 73 (n=5) |
| ASAP-retrained | 1269 [560, 2337] | 1269 ± 118 (n=5) |
| hindsight-optimal (lower bound) | 212 [95, 419] |  |

GNN-Surv / fewest contacts on source=fresh-9to12: 0.969 [0.794, 1.154], HL -0.53 s, W/T/L 9/0/10, p 0.89 (uncorrected)

#### source=fresh-allowance: 152 states, 32 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 2529 [1484, 3761] |  |
| outside-in | 1472 [815, 2317] |  |
| fewest contacts | 811 [476, 1199] |  |
| ASAP zero-shot | 1366 [816, 2090] |  |
| MLP-BCE (p) | 727 [441, 1060] | 727 ± 105 (n=5) |
| MLP-Surv (p/c) | 742 [483, 1027] | 742 ± 90 (n=5) |
| GNN-BCE (p) | 735 [483, 1026] | 735 ± 55 (n=5) |
| GNN-Surv (p/c) | 701 [452, 979] | 701 ± 105 (n=5) |
| GNN-Surv-Tail (p/c) | 720 [458, 1023] | 720 ± 139 (n=5) |
| PN-GNN-Surv (p/c) | 815 [481, 1217] | 815 ± 47 (n=5) |
| ASAP-retrained | 1014 [621, 1527] | 1014 ± 76 (n=5) |
| hindsight-optimal (lower bound) | 250 [164, 348] |  |

GNN-Surv / fewest contacts on source=fresh-allowance: 0.865 [0.678, 1.157], HL -0.33 s, W/T/L 17/2/13, p 0.57 (uncorrected)

#### parts=3-4: 267 states, 118 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1521 [1191, 1872] |  |
| outside-in | 1230 [872, 1630] |  |
| fewest contacts | 1064 [749, 1420] |  |
| ASAP zero-shot | 1227 [910, 1582] |  |
| MLP-BCE (p) | 1004 [687, 1385] | 1004 ± 79 (n=5) |
| MLP-Surv (p/c) | 939 [654, 1270] | 939 ± 39 (n=5) |
| GNN-BCE (p) | 816 [611, 1059] | 816 ± 103 (n=5) |
| GNN-Surv (p/c) | 764 [546, 1019] | 764 ± 150 (n=5) |
| GNN-Surv-Tail (p/c) | 797 [571, 1061] | 797 ± 56 (n=5) |
| PN-GNN-Surv (p/c) | 775 [573, 998] | 775 ± 71 (n=5) |
| ASAP-retrained | 1124 [827, 1467] | 1124 ± 69 (n=5) |
| hindsight-optimal (lower bound) | 257 [196, 327] |  |

GNN-Surv / fewest contacts on parts=3-4: 0.718 [0.586, 0.870], HL -0.32 s, W/T/L 74/14/30, p 2.8e-05 (uncorrected)

#### parts=5-6: 289 states, 67 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 2242 [1666, 2839] |  |
| outside-in | 1790 [1149, 2512] |  |
| fewest contacts | 1299 [865, 1798] |  |
| ASAP zero-shot | 1685 [1161, 2256] |  |
| MLP-BCE (p) | 1135 [758, 1566] | 1135 ± 66 (n=5) |
| MLP-Surv (p/c) | 1118 [743, 1571] | 1118 ± 69 (n=5) |
| GNN-BCE (p) | 1250 [838, 1714] | 1250 ± 75 (n=5) |
| GNN-Surv (p/c) | 1202 [807, 1656] | 1202 ± 133 (n=5) |
| GNN-Surv-Tail (p/c) | 1109 [737, 1533] | 1109 ± 166 (n=5) |
| PN-GNN-Surv (p/c) | 1229 [809, 1718] | 1229 ± 104 (n=5) |
| ASAP-retrained | 1574 [1080, 2141] | 1574 ± 115 (n=5) |
| hindsight-optimal (lower bound) | 265 [200, 338] |  |

GNN-Surv / fewest contacts on parts=5-6: 0.926 [0.688, 1.274], HL -0.25 s, W/T/L 38/1/28, p 0.33 (uncorrected)

#### parts=7-8: 211 states, 34 assemblies

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 2019 [1382, 2686] |  |
| outside-in | 986 [576, 1471] |  |
| fewest contacts | 961 [572, 1437] |  |
| ASAP zero-shot | 1553 [1049, 2099] |  |
| MLP-BCE (p) | 868 [547, 1232] | 868 ± 88 (n=5) |
| MLP-Surv (p/c) | 755 [488, 1070] | 755 ± 97 (n=5) |
| GNN-BCE (p) | 909 [560, 1315] | 909 ± 101 (n=5) |
| GNN-Surv (p/c) | 739 [433, 1126] | 739 ± 63 (n=5) |
| GNN-Surv-Tail (p/c) | 678 [391, 1026] | 678 ± 83 (n=5) |
| PN-GNN-Surv (p/c) | 779 [467, 1155] | 779 ± 82 (n=5) |
| ASAP-retrained | 1168 [680, 1740] | 1168 ± 61 (n=5) |
| hindsight-optimal (lower bound) | 209 [133, 302] |  |

GNN-Surv / fewest contacts on parts=7-8: 0.769 [0.556, 1.006], HL -1.60 s, W/T/L 23/0/11, p 0.024 (uncorrected)

#### parts=9-10: 130 states, 15 assemblies — **UNDERPOWERED (< 30 assemblies), no conclusion**

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 1043 [640, 1511] |  |
| outside-in | 631 [323, 979] |  |
| fewest contacts | 568 [273, 913] |  |
| ASAP zero-shot | 460 [273, 666] |  |
| MLP-BCE (p) | 621 [316, 982] | 621 ± 84 (n=5) |
| MLP-Surv (p/c) | 649 [390, 946] | 649 ± 103 (n=5) |
| GNN-BCE (p) | 486 [301, 695] | 486 ± 88 (n=5) |
| GNN-Surv (p/c) | 552 [301, 838] | 552 ± 52 (n=5) |
| GNN-Surv-Tail (p/c) | 510 [313, 729] | 510 ± 111 (n=5) |
| PN-GNN-Surv (p/c) | 546 [287, 838] | 546 ± 79 (n=5) |
| ASAP-retrained | 608 [295, 1048] | 608 ± 52 (n=5) |
| hindsight-optimal (lower bound) | 110 [62, 179] |  |

GNN-Surv / fewest contacts on parts=9-10: 0.971 [0.721, 1.310], HL +2.75 s, W/T/L 5/0/10, p 0.36 (uncorrected)

#### parts=11-12: 113 states, 11 assemblies — **UNDERPOWERED (< 30 assemblies), no conclusion**

| ordering | total planner time (s) [95% CI] | seeds (mean ± std) |
|---|---|---|
| random (expectation) | 2521 [1585, 3409] |  |
| outside-in | 1302 [569, 2195] |  |
| fewest contacts | 845 [431, 1340] |  |
| ASAP zero-shot | 1735 [924, 2603] |  |
| MLP-BCE (p) | 832 [460, 1265] | 832 ± 94 (n=5) |
| MLP-Surv (p/c) | 941 [525, 1467] | 941 ± 115 (n=5) |
| GNN-BCE (p) | 920 [501, 1415] | 920 ± 201 (n=5) |
| GNN-Surv (p/c) | 759 [340, 1295] | 759 ± 162 (n=5) |
| GNN-Surv-Tail (p/c) | 745 [337, 1243] | 745 ± 67 (n=5) |
| PN-GNN-Surv (p/c) | 742 [389, 1135] | 742 ± 38 (n=5) |
| ASAP-retrained | 1139 [476, 2093] | 1139 ± 133 (n=5) |
| hindsight-optimal (lower bound) | 222 [94, 418] |  |

GNN-Surv / fewest contacts on parts=11-12: 0.898 [0.677, 1.124], HL -10.18 s, W/T/L 7/0/4, p 0.37 (uncorrected)

## Prediction quality (main configuration, every node of every state with >= 1 success)

ECE: 10 equal-width bins of p vs observed success. Within-state C-index (Harrell, censored at min(cost, T)): comparable pair = part i succeeded at t_i < t_j at the same state; speed = p (BCE, ASAP) or −c (survival). Mean ± std over seeds.

| model | ECE of p | C-index within state | C-index pooled |
|---|---|---|---|
| ASAP zero-shot | 0.581 | 0.562 | 0.606 |
| MLP-BCE (p) | 0.021 ± 0.007 | 0.624 ± 0.003 | 0.729 ± 0.005 |
| MLP-Surv (p/c) | 0.028 ± 0.014 | 0.635 ± 0.009 | 0.735 ± 0.016 |
| GNN-BCE (p) | 0.076 ± 0.021 | 0.623 ± 0.011 | 0.701 ± 0.023 |
| GNN-Surv (p/c) | 0.031 ± 0.006 | 0.669 ± 0.005 | 0.766 ± 0.008 |
| GNN-Surv-Tail (p/c) | 0.046 ± 0.035 | 0.681 ± 0.006 | 0.763 ± 0.020 |
| PN-GNN-Surv (p/c) | 0.038 ± 0.009 | 0.671 ± 0.010 | 0.766 ± 0.009 |
| ASAP-retrained | 0.606 ± 0.013 | 0.595 ± 0.009 | 0.678 ± 0.005 |

ASAP's score is P(part is the next removed part), not P(planner success), so its ECE is not a calibration claim.

![totals](figures/replay_val_totals.png) (vector: `figures/replay_val_totals.pdf`)
