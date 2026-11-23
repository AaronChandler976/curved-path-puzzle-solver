# Run 03 R5 supplement: direction of the paired test differences

Computed by `scripts/replay_supp.py` from the stored one-time test results `experiments/2026-11-23_run03_eval_test/per_state.jsonl` (no re-evaluation). Per-assembly cost = sum over that assembly's test states with >= 1 success; trained models use the 5-seed average. HL = Hodges-Lehmann estimate of the per-assembly difference (GNN-Surv minus other; negative = GNN-Surv cheaper), with a bootstrap 95% CI (2,000 resamples over assemblies). A win means GNN-Surv is cheaper by more than 0.01 s.


## All states: 702 states, 197 assemblies

| vs | GNN-Surv wins / ties / losses (assemblies) | HL per-assembly diff (s) [95% CI] | mean diff (s) |
|---|---|---|---|
| random | 161 / 2 / 34 | -4.51 [-6.64, -2.30] | -10.50 |
| outside-in | 133 / 6 / 58 | -0.85 [-1.71, -0.42] | -4.43 |
| fewest contacts | 128 / 12 / 57 | -0.64 [-1.12, -0.31] | -1.94 |
| MLP-BCE (p) | 132 / 10 / 55 | -0.45 [-0.82, -0.21] | -0.53 |
| MLP-Surv (p/c) | 118 / 17 / 62 | -0.12 [-0.26, -0.01] | +0.91 |
| GNN-BCE (p) | 134 / 13 / 50 | -0.55 [-0.96, -0.29] | +0.93 |
| GNN-Surv (p only) | 132 / 21 / 44 | -0.32 [-0.55, -0.18] | -0.45 |
| ASAP (zero-shot) | 144 / 4 / 49 | -1.40 [-2.37, -0.76] | -2.54 |

Share of each ordering's total from its 5% most expensive states (heavy tail):

| ordering | top-5% states' share of total |
|---|---|
| GNN-Surv (p/c) | 0.63 |
| random | 0.37 |
| outside-in | 0.56 |
| fewest contacts | 0.60 |
| MLP-BCE (p) | 0.59 |
| MLP-Surv (p/c) | 0.65 |
| GNN-BCE (p) | 0.51 |
| GNN-Surv (p only) | 0.59 |
| ASAP (zero-shot) | 0.52 |

## rot_state states (n < 100 states; underpowered): 65 states, 33 assemblies

| vs | GNN-Surv wins / ties / losses (assemblies) | HL per-assembly diff (s) [95% CI] | mean diff (s) |
|---|---|---|---|
| random | 24 / 0 / 9 | -3.06 [-10.14, +1.84] | -4.95 |
| outside-in | 14 / 4 / 15 | +0.00 [-3.49, +9.29] | -1.32 |
| fewest contacts | 14 / 4 / 15 | -0.25 [-3.61, +2.04] | -2.99 |
| MLP-BCE (p) | 14 / 6 / 13 | +0.02 [-0.50, +6.01] | +4.14 |
| MLP-Surv (p/c) | 10 / 8 / 15 | +0.29 [-0.09, +5.40] | +5.22 |
| GNN-BCE (p) | 18 / 5 / 10 | -0.04 [-1.62, +12.23] | +5.36 |
| GNN-Surv (p only) | 15 / 6 / 12 | -0.13 [-1.00, +2.09] | +2.06 |
| ASAP (zero-shot) | 15 / 3 / 15 | +0.04 [-3.21, +11.17] | +2.11 |

Share of each ordering's total from its 5% most expensive states (heavy tail):

| ordering | top-5% states' share of total |
|---|---|
| GNN-Surv (p/c) | 0.36 |
| random | 0.17 |
| outside-in | 0.49 |
| fewest contacts | 0.49 |
| MLP-BCE (p) | 0.37 |
| MLP-Surv (p/c) | 0.37 |
| GNN-BCE (p) | 0.29 |
| GNN-Surv (p only) | 0.40 |
| ASAP (zero-shot) | 0.44 |

## non-rot states: 637 states, 193 assemblies

| vs | GNN-Surv wins / ties / losses (assemblies) | HL per-assembly diff (s) [95% CI] | mean diff (s) |
|---|---|---|---|
| random | 159 / 3 / 31 | -3.33 [-5.88, -1.84] | -9.87 |
| outside-in | 133 / 8 / 52 | -0.93 [-1.54, -0.50] | -4.30 |
| fewest contacts | 126 / 15 / 52 | -0.61 [-1.07, -0.32] | -1.47 |
| MLP-BCE (p) | 128 / 11 / 54 | -0.42 [-0.71, -0.22] | -1.25 |
| MLP-Surv (p/c) | 114 / 21 / 58 | -0.12 [-0.25, -0.03] | +0.04 |
| GNN-BCE (p) | 133 / 12 / 48 | -0.47 [-0.81, -0.27] | +0.04 |
| GNN-Surv (p only) | 124 / 31 / 38 | -0.27 [-0.41, -0.16] | -0.81 |
| ASAP (zero-shot) | 144 / 8 / 41 | -1.35 [-2.16, -0.84] | -2.95 |

Share of each ordering's total from its 5% most expensive states (heavy tail):

| ordering | top-5% states' share of total |
|---|---|
| GNN-Surv (p/c) | 0.65 |
| random | 0.40 |
| outside-in | 0.56 |
| fewest contacts | 0.60 |
| MLP-BCE (p) | 0.61 |
| MLP-Surv (p/c) | 0.69 |
| GNN-BCE (p) | 0.53 |
| GNN-Surv (p only) | 0.60 |
| ASAP (zero-shot) | 0.52 |
