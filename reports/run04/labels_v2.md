# Run 04 T7: pilot_v2 labels (oracle v2)

Labels `data/labels/pilot_v2/` (labels.jsonl = first clean attempt per query; attempts.jsonl = every attempt, 44051 lines); run folder `experiments/2026-11-24_run04_label_v2/` (stdout.log, idle_samples.jsonl, load_info.txt). Report: `scripts/labels_v2_report.py`.

- planned assemblies: 2022; with a summary line: 2022; **missing: 0**
- summary status: {'complete': 1866, 'stuck': 156}
- skipped reasons: {}
- queries: 41913; still confounded after 2 re-runs: 0 (**0.00%**); fixed by a re-run: 2128; errors: 0

## Per source and part-count bin (main config = pre-check → CMG-RRT)

| source | bin | assemblies (complete / stuck) | states | queries | success rate | pre-check share of successes | CMG-RRT-only success rate | main-config planner h | CMG-RRT-only planner h |
|---|---|---|---|---|---|---|---|---|---|
| fresh-9to12 | 9-10 | 145 (129 / 16) | 1190 | 6932 | 0.841 | 0.980 | 0.828 | 10.84 | 16.25 |
| fresh-9to12 | 11-12 | 110 (102 / 8) | 1119 | 7616 | 0.817 | 0.977 | 0.802 | 13.65 | 20.54 |
| fresh-allowance | 3-4 | 165 (157 / 8) | 391 | 1083 | 0.861 | 0.958 | 0.852 | 1.47 | 2.05 |
| fresh-allowance | 5-6 | 106 (91 / 15) | 440 | 1644 | 0.793 | 0.962 | 0.776 | 3.24 | 4.27 |
| fresh-allowance | 7-8 | 71 (64 / 7) | 437 | 2081 | 0.709 | 0.951 | 0.695 | 5.92 | 7.17 |
| fresh-allowance | 9-10 | 59 (45 / 14) | 471 | 2772 | 0.720 | 0.978 | 0.702 | 7.31 | 9.57 |
| fresh-allowance | 11-12 | 38 (31 / 7) | 385 | 2651 | 0.706 | 0.960 | 0.679 | 7.97 | 10.93 |
| v1 | 3-4 | 725 (680 / 45) | 1689 | 4648 | 0.893 | 0.980 | 0.885 | 4.72 | 6.98 |
| v1 | 5-6 | 400 (380 / 20) | 1725 | 6414 | 0.874 | 0.970 | 0.865 | 7.83 | 11.25 |
| v1 | 7-8 | 203 (187 / 16) | 1276 | 6072 | 0.850 | 0.974 | 0.836 | 8.81 | 13.33 |

## v1 vs v2 on the same queries (identical state, part and seed; v1 = pilot_v1 label)

Queries present in both: 15903 (v2 states follow v2's own removals, so only the shared states match).

| v1 outcome → v2 main outcome | count |
|---|---|
| success → success | 13798 |
| success → unsolved | 147 |
| unsolved → success | 134 |
| unsolved → unsolved | 1824 |

| v1 outcome → v2 CMG-RRT-only outcome | count |
|---|---|
| success → success | 13725 |
| success → unsolved | 220 |
| unsolved → success | 79 |
| unsolved → unsolved | 1879 |

v1 assemblies, status v1 → v2: {'complete→complete': 1236, 'complete→stuck': 13, 'stuck→complete': 11, 'stuck→stuck': 68}

v1 total planner time on the shared queries: 23.96 h; v2 main config: 18.85 h; v2 CMG-RRT only: 27.95 h.

## Load info

```
=== start ===
time: 2026-11-24T05:47:08-08:00
uptime: 05:47:08 up 1 day,  9:35,  1 user,  load average: 1.45, 3.28, 4.18
nvidia_smi: utilization.gpu [%], memory.used [MiB]
0 %, 1395 MiB
power_profile: performance
git_hash: b0d4bf85de8aeda387dba9d47ca7c2f33760835d
git_dirty: True
cmd: scripts/label_abd.py --outdir experiments/2026-11-24_run04_label_v2 --labels-dir data/labels/pilot_v2 --T 30 --workers 10 --concurrent-assemblies 6 --seed 0 --groups 3-12 --scan experiments/2026-11-23_run04_t6_pool/scan_all.jsonl --detector exact --oracle v2 --eps 0.005 --max-pen 0.005 --allowance-file experiments/2026-11-23_run04_t6_pool/allowance.json --source-file experiments/2026-11-23_run04_t6_pool/source.json --order-file experiments/2026-11-24_run04_label_v2/order.txt --only-order --idle-wait 300 --max-reruns 2
pid: 1620794
=== end ===
time: 2026-11-24T18:30:18-08:00
uptime: 18:30:18 up 1 day, 22:18,  1 user,  load average: 6.26, 6.87, 6.88
nvidia_smi: utilization.gpu [%], memory.used [MiB]
0 %, 1710 MiB
power_profile: performance
git_hash: 7e36b4f04e89a482762a61b89ff38dccfae9ff9a
git_dirty: False
cmd: scripts/label_abd.py --outdir experiments/2026-11-24_run04_label_v2 --labels-dir data/labels/pilot_v2 --T 30 --workers 10 --concurrent-assemblies 6 --seed 0 --groups 3-12 --scan experiments/2026-11-23_run04_t6_pool/scan_all.jsonl --detector exact --oracle v2 --eps 0.005 --max-pen 0.005 --allowance-file experiments/2026-11-23_run04_t6_pool/allowance.json --source-file experiments/2026-11-23_run04_t6_pool/source.json --order-file experiments/2026-11-24_run04_label_v2/order.txt --only-order --idle-wait 300 --max-reruns 2
pid: 1620794
```
