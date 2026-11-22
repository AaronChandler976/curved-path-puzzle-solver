# Per-state replay on cached pilot queries (pilot_v0)

Source labels: `experiments/2026-11-22_replay_v0_early/labels_snapshot.jsonl` (99 logged CMG-RRT queries). Cost = planner time only (time_s); SDF prep excluded. Bootstrap 95% CIs: 10,000 resamples, seed 0. This replays real logged queries; nothing is simulated. The trajectory through states is fixed by the labelling run, and each ordering only changes how much is spent finding the first success at each state.

- states with complete query sets: **34** (33 with >= 1 success, 1 with none) across **15** assemblies
- states with no success (every ordering pays everything): 1, total 151 s, median 151 s/state

## Per-state cost to first success (s), states with >= 1 success

| ordering | median [95% CI] | mean [95% CI] |
|---|---|---|
| random | 1.40 [1.09, 2.31] | 6.61 [3.00, 10.88] |
| outside_in | 1.12 [0.98, 1.85] | 5.20 [1.49, 9.85] |
| fewest_contacts | 1.12 [0.96, 1.42] | 5.17 [1.38, 10.75] |
| optimal (unattainable lower bound) | 0.95 [0.87, 1.03] | 1.12 [0.94, 1.34] |

## Per-assembly cost (s): sum over the visited states with >= 1 success

| ordering | median [95% CI] | mean [95% CI] |
|---|---|---|
| random | 5.04 [2.36, 30.22] | 15.58 [7.10, 25.33] |
| outside_in | 3.63 [2.40, 8.63] | 12.25 [4.12, 22.74] |
| fewest_contacts | 3.31 [2.28, 5.95] | 12.19 [3.34, 24.80] |
| optimal | 2.08 [1.91, 3.30] | 2.63 [2.18, 3.14] |

## Headroom (cost of ordering divided by hindsight-optimal)

Ratio of totals over states, with a bootstrap CI over states. Also the median of per-state ratios.

| ordering | ratio of totals [95% CI] | median per-state ratio |
|---|---|---|
| random / optimal | 5.92 [3.02, 9.13] | 1.42 |
| outside_in / optimal | 4.65 [1.44, 8.64] | 1.22 |
| fewest_contacts / optimal | 4.63 [1.30, 9.36] | 1.09 |

## Rotation split (assembly has a successful logged path with max rotation > 15 deg)

Caveat: an RRT path can rotate even when a pure translation would work, so this measures rotation *in the logged path*, not rotation that was *needed*.

| group | assemblies | states | random/optimal (ratio of totals) [95% CI] |
|---|---|---|---|
| rotation > thr | 0 | 0 | n/a |
| translation-like | 14 | 33 | 5.92 [2.98, 9.14] |

![replay](replay_pilot_v0.png)
