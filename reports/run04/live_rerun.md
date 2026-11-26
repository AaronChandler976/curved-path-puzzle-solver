# Run 04 T3: unconfounded rerun of run 03 R6 — **run 03 models, development test set**

These are run 03's frozen models on run 03's (spent) test split. This is a development result, NOT the final test (the final test is the v2 test split, evaluated once in run 05).

Run folder `experiments/2026-11-23_run04_live_rerun/` (`results.jsonl`: one line per attempt of each assembly x method run; `idle_samples.jsonl`: every 5 s idle-guard sample; `stdout.log`; `load_info.txt`). Script `scripts/live_abd.py` (command in `launch_cmd.txt`), report `scripts/live_rerun_report.py`. Identical to run 03 R6: the same 60 assemblies, the same 4 methods, the same GNN-Surv checkpoint (seed 101), the same planner seeds (sha1('run03-live', assembly, state, part)), exact union-SDF oracle v1 (CMG-RRT only), ε = 0.005, T = 30 s, 10 workers. New in run 04: seeded robot sampling (the same query is reproducible across methods up to the wall-clock T) and the idle guard (CLAUDE.md Run 04 rules).

- runs: 240 (attempts incl. re-runs: 243); clean on the first attempt: 238; confounded then clean on a re-run: 1; **still confounded after 2 re-runs: 1** (kept, flagged).
- queries in the reported attempts: 1022; confounded among them: 1 (0.10%).
- assemblies: 60 (20 rot_assembly); runs with errors: 0

## Per-method summary (all sampled assemblies)

| method | complete / stuck | total planner time (s) | mean planner s per assembly [95% CI] | planner calls (total) | mean wall s per assembly incl. setup |
|---|---|---|---|---|---|
| random | 56 / 4 | 1997 | 33.3 [20.0, 50.1] | 262 | 39.5 |
| fewest contacts | 57 / 3 | 2057 | 34.3 [20.8, 49.9] | 258 | 40.8 |
| ASAP GNN (released weights, zero-shot) | 57 / 3 | 1853 | 30.9 [20.6, 42.8] | 250 | 37.2 |
| GNN-Surv (p/c), seed 101 | 57 / 3 | 1506 | 25.1 [13.7, 39.8] | 252 | 31.3 |

## Paired comparison: all (56 assemblies completed by all methods)

GNN-Surv minus each method; total planner time per full disassembly (negative = GNN-Surv cheaper). Primary: ratio of totals; co-reported: per-assembly Hodges–Lehmann median difference.

| vs | GNN-Surv total / other total (s) | ratio of totals [95% CI] | HL median diff per assembly (s) [95% CI] | mean diff (s) [95% CI] | GNN-Surv wins / ties / losses | Wilcoxon p | Holm p | calls: GNN-Surv / other |
|---|---|---|---|---|---|---|---|---|
| random | 933 / 1209 | 0.772 [0.502, 1.192] | -2.85 [-11.92, -0.66] | -4.9 [-12.5, +3.3] | 37 / 2 / 17 | 0.0068 | 0.0068 | 223 / 228 |
| fewest contacts | 933 / 1568 | 0.595 [0.455, 0.821] | -3.51 [-8.56, -1.61] | -11.3 [-20.9, -3.3] | 43 / 2 / 11 | 7.4e-05 | 0.00022 | 223 / 232 |
| ASAP GNN (released weights, zero-shot) | 933 / 1464 | 0.637 [0.463, 0.876] | -4.68 [-13.74, -1.84] | -9.5 [-16.8, -2.5] | 44 / 1 / 11 | 8.2e-05 | 0.00022 | 223 / 228 |

## Paired comparison: rot_assembly subset (19 assemblies completed by all methods)

**Underpowered** (n = 19 < 30).

GNN-Surv minus each method; total planner time per full disassembly (negative = GNN-Surv cheaper). Primary: ratio of totals; co-reported: per-assembly Hodges–Lehmann median difference.

| vs | GNN-Surv total / other total (s) | ratio of totals [95% CI] | HL median diff per assembly (s) [95% CI] | mean diff (s) [95% CI] | GNN-Surv wins / ties / losses | Wilcoxon p | Holm p | calls: GNN-Surv / other |
|---|---|---|---|---|---|---|---|---|
| random | 586 / 738 | 0.793 [0.438, 1.392] | -11.30 [-28.46, +4.26] | -8.0 [-25.3, +11.7] | 13 / 0 / 6 | 0.13 | 0.27 | 92 / 96 |
| fewest contacts | 586 / 1125 | 0.521 [0.401, 0.721] | -19.28 [-50.35, -3.30] | -28.4 [-52.5, -8.5] | 15 / 0 / 4 | 0.011 | 0.032 | 92 / 103 |
| ASAP GNN (released weights, zero-shot) | 586 / 793 | 0.739 [0.477, 1.311] | -6.12 [-23.28, +3.50] | -10.9 [-30.4, +7.2] | 13 / 0 / 6 | 0.2 | 0.27 | 92 / 92 |

## Paired comparison: non-rot subset (37 assemblies completed by all methods)

GNN-Surv minus each method; total planner time per full disassembly (negative = GNN-Surv cheaper). Primary: ratio of totals; co-reported: per-assembly Hodges–Lehmann median difference.

| vs | GNN-Surv total / other total (s) | ratio of totals [95% CI] | HL median diff per assembly (s) [95% CI] | mean diff (s) [95% CI] | GNN-Surv wins / ties / losses | Wilcoxon p | Holm p | calls: GNN-Surv / other |
|---|---|---|---|---|---|---|---|---|
| random | 347 / 470 | 0.738 [0.373, 1.470] | -1.36 [-5.93, -0.11] | -3.3 [-10.0, +3.9] | 24 / 2 / 11 | 0.021 | 0.021 | 131 / 132 |
| fewest contacts | 347 / 443 | 0.784 [0.406, 1.295] | -1.87 [-3.90, -0.58] | -2.6 [-8.5, +3.1] | 28 / 2 / 7 | 0.00073 | 0.0015 | 131 / 129 |
| ASAP GNN (released weights, zero-shot) | 347 / 671 | 0.517 [0.314, 0.722] | -4.01 [-15.39, -1.56] | -8.8 [-14.2, -4.2] | 31 / 1 / 5 | 8.2e-06 | 2.4e-05 | 131 / 136 |

## Side by side: run 04 rerun (unconfounded) vs run 03 R6 (confounded)

Same assemblies in both: 56 (completed by all methods in both runs). Run 03 timings were all confounded (reports/run03/DECISIONS.md #12) and drew unseeded robot samples.

| method | run 03 total planner s (all 60) | run 04 total planner s (all 60) | run 03 complete/stuck | run 04 complete/stuck |
|---|---|---|---|---|
| random | 2018 | 1997 | 56/4 | 56/4 |
| fewest contacts | 2107 | 2057 | 57/3 | 57/3 |
| ASAP GNN (released weights, zero-shot) | 1805 | 1853 | 57/3 | 57/3 |
| GNN-Surv (p/c), seed 101 | 1548 | 1506 | 57/3 | 57/3 |

GNN-Surv vs each method on the 56 assemblies completed by all methods in BOTH runs:

| vs | run 03 ratio of totals [CI] | run 04 ratio of totals [CI] | run 03 HL diff (s) [CI] | run 04 HL diff (s) [CI] | run 03 W/T/L | run 04 W/T/L | run 03 Holm p | run 04 Holm p |
|---|---|---|---|---|---|---|---|---|
| random | 0.778 [0.503, 1.213] | 0.772 [0.498, 1.182] | -2.57 [-9.69, -0.79] | -2.85 [-11.94, -0.55] | 38/3/15 | 37/2/17 | 0.003 | 0.0068 |
| fewest contacts | 0.613 [0.476, 0.804] | 0.595 [0.456, 0.829] | -3.81 [-7.14, -2.00] | -3.51 [-7.96, -1.49] | 47/0/9 | 43/2/11 | 2.4e-05 | 0.00022 |
| ASAP GNN (released weights, zero-shot) | 0.670 [0.477, 0.935] | 0.637 [0.465, 0.878] | -4.19 [-14.85, -1.91] | -4.68 [-13.19, -2.04] | 44/2/10 | 44/1/11 | 7.1e-05 | 0.00022 |

## Load info (start / end)

```
=== start ===
time: 2026-11-23T16:45:52-08:00
uptime: 16:45:52 up 20:33,  1 user,  load average: 0.12, 1.02, 1.17
nvidia_smi: utilization.gpu [%], memory.used [MiB]
0 %, 1572 MiB
power_profile: performance
git_hash: b7ec4d23f4d6cf41d99978813c75c51a69a5b4a0
git_dirty: True
cmd: scripts/live_abd.py --assemblies experiments/2026-11-23_run04_live_rerun/assemblies.json --gnn-ckpt experiments/2026-11-23_run03_train_v2/gnn_survival/seed101/best.pt --outdir experiments/2026-11-23_run04_live_rerun --workers 10 --T 30 --eps 0.005 --save-paths --oracle v1 --seed-prefix run03-live --idle-wait 300 --max-reruns 2
pid: 842377
=== end ===
time: 2026-11-23T17:19:30-08:00
uptime: 17:19:30 up 21:07,  1 user,  load average: 1.03, 1.61, 2.95
nvidia_smi: utilization.gpu [%], memory.used [MiB]
2 %, 1604 MiB
power_profile: performance
git_hash: b7ec4d23f4d6cf41d99978813c75c51a69a5b4a0
git_dirty: True
cmd: scripts/live_abd.py --assemblies experiments/2026-11-23_run04_live_rerun/assemblies.json --gnn-ckpt experiments/2026-11-23_run03_train_v2/gnn_survival/seed101/best.pt --outdir experiments/2026-11-23_run04_live_rerun --workers 10 --T 30 --eps 0.005 --save-paths --oracle v1 --seed-prefix run03-live --idle-wait 300 --max-reruns 2
pid: 842377
```
