# Run 03 R6: live full-disassembly evaluation (fresh CMG-RRT queries)

Run folder `experiments/2026-11-23_run03_live/` (`results.jsonl` = one line per assembly x method with every query; `stdout.log`; `load_info.txt`; `idle_wait.log`). Script `scripts/live_abd.py` via `scripts/run_r6.sh`. Exact union-SDF oracle, ε = 0.005, T = 30 s, 10 planner workers (slots), methods interleaved per assembly, planner seed per query = sha1(assembly, state, part), identical across methods.

- idle check before start: `idle=0` -> **all timings CONFOUNDED**. During the run the 10 planner workers themselves load the machine; nothing else ran.
- assemblies: 60 (20 rot_assembly); runs: 240; runs with errors: 0
- caveat: trimesh draws the robot's surface samples with an unseeded generator, and T is a wall-clock limit. The same query (same seed) can therefore end differently under two methods. These are fresh runs, not replays.

## Per-method summary (all sampled assemblies)

| method | complete / stuck | total planner time (s) | mean planner s per assembly [95% CI] | planner calls (total) | mean wall s per assembly incl. setup |
|---|---|---|---|---|---|
| random | 56 / 4 | 2018 | 33.6 [20.2, 50.5] | 263 | 33.8 |
| fewest contacts | 57 / 3 | 2107 | 35.1 [21.6, 50.4] | 258 | 35.3 |
| ASAP GNN (released weights, zero-shot) | 57 / 3 | 1805 | 30.1 [20.3, 41.5] | 249 | 30.4 |
| GNN-Surv (p/c), seed 101 | 57 / 3 | 1548 | 25.8 [14.1, 40.7] | 250 | 26.0 |

## Paired comparison: all (56 assemblies completed by all methods)

GNN-Surv minus each method; total planner time per full disassembly (negative = GNN-Surv cheaper).

| vs | GNN-Surv total / other total (s) | mean diff per assembly (s) [95% paired bootstrap CI] | ratio of totals [95% CI] | GNN-Surv wins / ties / losses | Wilcoxon p | Holm p | calls: GNN-Surv / other |
|---|---|---|---|---|---|---|---|
| random | 953 / 1225 | -4.8 [-12.7, +3.7] | 0.778 [0.502, 1.216] | 38 / 3 / 15 | 0.003 | 0.003 | 221 / 229 |
| fewest contacts | 953 / 1555 | -10.7 [-19.4, -3.8] | 0.613 [0.475, 0.801] | 47 / 0 / 9 | 8.1e-06 | 2.4e-05 | 221 / 231 |
| ASAP GNN (released weights, zero-shot) | 953 / 1423 | -8.4 [-15.6, -1.4] | 0.670 [0.477, 0.933] | 44 / 2 / 10 | 3.5e-05 | 7.1e-05 | 221 / 227 |

## Paired comparison: rot_assembly subset (19 assemblies completed by all methods)

**Underpowered** (n = 19 < 30).

GNN-Surv minus each method; total planner time per full disassembly (negative = GNN-Surv cheaper).

| vs | GNN-Surv total / other total (s) | mean diff per assembly (s) [95% paired bootstrap CI] | ratio of totals [95% CI] | GNN-Surv wins / ties / losses | Wilcoxon p | Holm p | calls: GNN-Surv / other |
|---|---|---|---|---|---|---|---|
| random | 609 / 759 | -7.9 [-25.9, +13.1] | 0.802 [0.442, 1.428] | 14 / 0 / 5 | 0.12 | 0.12 | 92 / 96 |
| fewest contacts | 609 / 1052 | -23.3 [-45.1, -6.9] | 0.579 [0.454, 0.752] | 16 / 0 / 3 | 0.002 | 0.0061 | 92 / 100 |
| ASAP GNN (released weights, zero-shot) | 609 / 783 | -9.2 [-26.5, +7.9] | 0.777 [0.503, 1.312] | 14 / 0 / 5 | 0.06 | 0.12 | 92 / 92 |

## Paired comparison: non-rot subset (37 assemblies completed by all methods)

GNN-Surv minus each method; total planner time per full disassembly (negative = GNN-Surv cheaper).

| vs | GNN-Surv total / other total (s) | mean diff per assembly (s) [95% paired bootstrap CI] | ratio of totals [95% CI] | GNN-Surv wins / ties / losses | Wilcoxon p | Holm p | calls: GNN-Surv / other |
|---|---|---|---|---|---|---|---|
| random | 344 / 466 | -3.3 [-10.0, +3.9] | 0.740 [0.368, 1.471] | 24 / 3 / 10 | 0.0076 | 0.0076 | 129 / 133 |
| fewest contacts | 344 / 503 | -4.3 [-10.7, +1.1] | 0.684 [0.355, 1.103] | 31 / 0 / 6 | 0.00018 | 0.00035 | 129 / 131 |
| ASAP GNN (released weights, zero-shot) | 344 / 639 | -8.0 [-14.2, -2.2] | 0.539 [0.301, 0.849] | 30 / 2 / 5 | 2.6e-05 | 7.9e-05 | 129 / 135 |

## Load info (start / end)

```
=== start ===
time: 2026-11-23T11:16:18-08:00
uptime: 11:16:18 up 15:04,  1 user,  load average: 0.26, 0.28, 0.27
nvidia_smi: utilization.gpu [%], memory.used [MiB]
18 %, 1946 MiB
power_profile: performance
git_hash: 1cde7d2a13f50eb994c3fe5b38ed1864ea254984
git_dirty: False
cmd: scripts/live_abd.py --assemblies experiments/2026-11-23_run03_live/assemblies.json --gnn-ckpt experiments/2026-11-23_run03_train_v2/gnn_survival/seed101/best.pt --outdir experiments/2026-11-23_run03_live --workers 10 --T 30 --eps 0.005 --save-paths
pid: 808038
=== end ===
time: 2026-11-23T11:32:34-08:00
uptime: 11:32:34 up 15:20,  1 user,  load average: 1.21, 4.67, 4.59
nvidia_smi: utilization.gpu [%], memory.used [MiB]
0 %, 594 MiB
power_profile: performance
git_hash: 1cde7d2a13f50eb994c3fe5b38ed1864ea254984
git_dirty: True
cmd: scripts/live_abd.py --assemblies experiments/2026-11-23_run03_live/assemblies.json --gnn-ckpt experiments/2026-11-23_run03_train_v2/gnn_survival/seed101/best.pt --outdir experiments/2026-11-23_run03_live --workers 10 --T 30 --eps 0.005 --save-paths
pid: 808038
```
