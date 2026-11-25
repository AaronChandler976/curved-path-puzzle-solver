# Run 05 (campaign Phase 1): training on v2, validation only

**One line.** All 7 pre-registered variants were trained with the registered grid, selection rule and seeds
(`docs/PREREG_run05.md` §1–§3; 5 final seeds each, none dropped), on train/val only. On val, GNN-Surv is cheaper than
the best heuristic (fewest contacts) on the typical assembly. On total planner time it is not, in the main
configuration (ratio CI crosses 1); in the CMG-RRT-only configuration it is. These are **development (val) numbers**;
the registered result is the single test evaluation in Phase 3. **Val numbers for trained models are
optimistically biased:** val replay cost chose each variant's config and checkpoint epoch, and the same cost is
reported here. The heuristics had no such selection. The CIs and p-values below are therefore descriptive, not
inferential (Phase 1 audit, MAJOR 1). The test split was never loaded: no
`data/splits/.v2_test_evaluated` marker, and the graphs file holds train and val only.

## 1. What ran (evidence)
| step | output | log / provenance |
|---|---|---|
| train/val graphs + point clouds | `data/processed/run05/graphs_train_val.pt`, `clouds_train_val.pt` (5,867 train / 1,030 val states; 5,762 / 1,010 with ≥ 1 success) | `experiments/2026-11-24_run05_dataset/` |
| ASAP's own redmax contact graphs (geometry only) | 2,022/2,022 assemblies, 0 errors | `experiments/2026-11-24_run05_redmax/` |
| training, 7 variants | `experiments/2026-11-24_run05_train/<variant>/` (grid runs, `seed100`–`seed104/best.pt`, `selection.json`, `metrics.csv`, `train_log.txt`, `load_info.txt`) | `cmd.txt`, `git_hash.txt` there |
| val replay (main + CMG-RRT-only), C-index, ECE, **scored on CPU** | `reports/run05/val_replay.md`, `experiments/2026-11-25_run05_eval_val_cpu/a/results.json`, `per_state.jsonl` | `cmd.txt`, `stdout.log` there. A second identical run (`.../b/`) gives bit-identical per-state costs and results. The earlier GPU run `experiments/2026-11-24_run05_eval_val/` is superseded: GPU ASAP scoring was not deterministic (audit MAJOR 2). Only the ASAP rows differ. |
| latency / memory profile (alone, idle guard 5 min) | `reports/run05/profile.md`, `experiments/2026-11-24_run05_profile/profile.json` | `load_info.txt`, `guard/idle_samples.jsonl` |
| training curves, grid tables, every seed | `reports/run05/training.md`, `reports/run05/figures/train_curves_*.pdf` | `scripts/run05_training_report.py` |

## 2. Selected configurations (val; full grids in `training.md`)
| variant | chosen config | final seeds' best smoothed val cost (s) | mean ± std |
|---|---|---|---|
| MLP-BCE | h64, lr 3e-4, L2 | 2128, 2228, 2193, 2080, 2342 | 2194 ± 101 |
| MLP-Surv | h64, lr 3e-4, L2 | 1716, 2079, 2135, 2014, 2050 | 1999 ± 164 |
| GNN-BCE | h64, lr 1e-3, L2 | 2020, 1964, 2011, 1976, 1728 | 1940 ± 121 |
| GNN-Surv (main) | h64, lr 3e-4, L3 | 1887, 1616, 1778, 1834, 1992 | 1821 ± 140 |
| GNN-Surv-Tail | h128, lr 3e-4, L2, λ 1.0 | 1794, 1700, 1580, 1629, 1637 | 1668 ± 82 |
| PN-GNN-Surv | h64, lr 3e-4, L2 | 1693, 1795, 1763, 1648, 1709 | 1722 ± 58 |
| ASAP-retrained | lr 1e-3, batch 16 | 3270, 3206, 3234, 3200, 3327 | 3248 ± 52 |

"Best smoothed" = the 5-epoch trailing mean at the selected epoch (the selection statistic). The replay totals
below re-evaluate each saved checkpoint once.

## 3. Val replay, main configuration (pre-check → CMG-RRT), 1,010 scored states, 245 assemblies
From `reports/run05/val_replay.md` (bootstrap over assemblies, 10,000 resamples; trained variants = seed-mean;
descriptive, see the selection-bias note above):

| ordering | total planner time (s) [95% CI] | seeds mean ± std |
|---|---|---|
| random (expectation) | 6059 [4679, 7619] | |
| outside-in | 2800 [1829, 3909] | |
| fewest contacts | 2275 [1556, 3078] | |
| ASAP zero-shot | 3549 [2417, 4909] | |
| ASAP-retrained | 3145 [2182, 4374] | 3145 ± 197 |
| MLP-BCE | 2205 [1564, 2925] | 2205 ± 125 |
| MLP-Surv | 2026 [1444, 2703] | 2026 ± 170 |
| GNN-BCE | 1903 [1323, 2567] | 1903 ± 136 |
| **GNN-Surv** | 1835 [1228, 2526] | 1835 ± 129 |
| GNN-Surv-Tail | 1637 [1115, 2228] | 1637 ± 106 |
| PN-GNN-Surv | 1684 [1167, 2267] | 1684 ± 88 |
| hindsight-optimal | 115 [65, 180] | |

- **GNN-Surv vs fewest contacts** (the best heuristic on val; this fixes the §7 heuristic for test, DECISIONS #8):
  ratio of totals 0.807 [0.632, 1.016], HL −0.02 s, W/T/L 99/89/57, Holm p 0.0034. Only the §7 typical-assembly
  condition (b) is met here, on val, descriptively; the registered rule is applied only to test in the main
  configuration.
- **CMG-RRT-only configuration:** ratio 0.848 [0.745, 0.962], HL −0.42 s, Holm p 0.0021. Descriptively both
  conditions are met on val, but the registered rule doesn't cover this configuration (it is a robustness table).
- **Interventions on val** (Holm family of 11):
  - GNN vs MLP (survival): 0.906 [0.712, 1.126], Holm p 0.099.
  - Survival p/c vs BCE p (GNN): 0.964 [0.774, 1.184], Holm p 0.0034.
  - PointNet vs hand-made features: GNN-Surv / PN = 1.090 [0.920, 1.275], p 1.
  - Tail-aware vs plain: GNN-Surv / Tail = 1.121 [0.989, 1.258], Holm p 0.25.
  - GNN vs MLP (BCE) and survival vs BCE (MLP): both n.s.
- **Effect sizes are small per assembly, large in total.** Most states succeed on the first query (mean 1.04–1.17
  queries), so HL differences are hundredths of a second. The totals are driven by a few states where an unsolved
  query (~30 s) is tried first. 20 val states have no success under any order (1,857 s, outside the totals).
- **Subsets** (val; `val_replay.md`):
  - 9–12-part assemblies are **underpowered on val** (fresh-9to12: 19 assemblies; parts 9–10: 15; 11–12: 11). GNN-Surv /
    fewest contacts is 1.34 [0.80, 3.23] on fresh-9to12. No conclusion is drawn, but the test set is 51% 9–12-part,
    so this is a risk for test.
  - rot_state: 44 assemblies, 0.891 [0.599, 1.418].

## 4. Prediction quality (val, main configuration)
| model | ECE of p | within-state C-index | pooled C-index |
|---|---|---|---|
| ASAP zero-shot (score is P(next removed), not P(success)) | 0.581 | 0.562 | 0.606 |
| MLP-BCE | 0.021 ± 0.007 | 0.624 ± 0.003 | 0.729 ± 0.005 |
| MLP-Surv | 0.028 ± 0.014 | 0.635 ± 0.009 | 0.735 ± 0.016 |
| GNN-BCE | 0.076 ± 0.021 | 0.623 ± 0.011 | 0.701 ± 0.023 |
| GNN-Surv | 0.031 ± 0.006 | 0.669 ± 0.005 | 0.766 ± 0.008 |
| GNN-Surv-Tail | 0.046 ± 0.035 | 0.681 ± 0.006 | 0.763 ± 0.020 |
| PN-GNN-Surv | 0.038 ± 0.009 | 0.671 ± 0.010 | 0.766 ± 0.009 |

ASAP-retrained's row is in `val_replay.md`.

## 5. Latency, memory and the planner time it saves (`reports/run05/profile.md`)
- **Run:** `experiments/2026-11-25_run05_profile/`, alone after a 5-minute idle wait; outside load ≤ 0.36 cores
  throughout. The earlier run `experiments/2026-11-24_run05_profile/` is superseded (it had mislabelled columns).
- **What is timed:** the forward pass on collated inputs (median), batch 1 and one batch of all 200 sampled val states.
- **Feature extraction:** 2.41 ms per state (median) from the cached per-assembly contact graph. Not included in any
  timing: the per-assembly contact graph, PointNet point-cloud sampling, and ASAP's point clouds and redmax graph (all
  once per assembly).
- **GNN-Surv:** 32,392 parameters; 0.12 ms per state on 1 CPU thread at batch 1; 0.24 ms on GPU at batch 1;
  0.0013 ms per state batched on GPU; 11 MB peak GPU memory batched.
- **ASAP's model:** 1.7 M parameters; 7.0 ms on 1 CPU thread; 3.8 GB peak GPU memory batched.
- **PN-GNN-Surv:** its whole forward pass, PointNet encoder included, costs 1.89 ms on 1 CPU thread at batch 1, and
  904 MB peak GPU memory batched.
- **Trade-off (val, descriptive):** GNN-Surv saves 0.44 s of planner time per state against fewest contacts (Tail 0.63,
  PN 0.59). That is about 170× its own per-state cost on one CPU thread (2.41 + 0.12 ≈ 2.5 ms); Tail ≈ 250×, PN ≈ 140×.
  Even with the val optimism (§3) the ranker's cost is negligible next to the planner time at stake.

## 6. Deviations and choices (each with its reason)
- `reports/campaign/DECISIONS.md` #2: Holm family of 11 (9 + 2 intervention pairs), CMG-RRT-only scored states,
  solve-rate definition, HL CI with 2,000 resamples.
- #6: tail loss computed by an exactly equivalent batched implementation (equivalence test). The first tail launch
  was stopped before finishing a grid run and is kept as `gnn_survival_tail_aborted1/`, not used.
- #7: `experiments/2026-11-24_run05_eval_val_dev/` is a pipeline check, not cited.
- Best epochs are early (4–45; the minimum-epoch rule only delays stopping, as registered).

## 7. Next
Phase 1 audit. Then Phase 2 (exploration on val; `reports/campaign/PLAN_LOG.md`), which also runs the 5-fold group CV
over train+val so the large-assembly subsets have more coverage.
