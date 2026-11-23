# Per-state replay on cached pilot queries (pilot_v1 (planner only))

Source labels: `data/labels/pilot_v1/labels.jsonl` (565 logged CMG-RRT queries). Cost = planner time only (time_s); SDF prep excluded. Bootstrap 95% CIs: 10,000 resamples, seed 0. This replays real logged queries; nothing is simulated. The trajectory through states is fixed by the labelling run, and each ordering only changes how much is spent finding the first success at each state.

- states with complete query sets: **184** (182 with >= 1 success, 2 with none) across **68** assemblies
- states with no success (every ordering pays everything): 2, total 182 s, median 91 s/state

## Per-state cost to first success (s), states with >= 1 success

| ordering | median [95% CI] | mean [95% CI] |
|---|---|---|
| random | 0.89 [0.66, 1.04] | 4.29 [3.04, 5.75] |
| outside_in | 0.75 [0.56, 1.03] | 3.40 [2.16, 4.91] |
| fewest_contacts | 0.67 [0.54, 0.93] | 2.94 [1.85, 4.28] |
| optimal (unattainable lower bound) | 0.26 [0.22, 0.30] | 0.61 [0.40, 0.91] |

## Per-assembly cost (s): sum over the visited states with >= 1 success

| ordering | median [95% CI] | mean [95% CI] |
|---|---|---|
| random | 2.67 [1.90, 4.54] | 11.65 [7.04, 17.26] |
| outside_in | 2.39 [1.88, 3.36] | 9.23 [5.40, 14.02] |
| fewest_contacts | 2.35 [1.84, 3.21] | 7.99 [4.51, 12.44] |
| optimal | 0.72 [0.58, 0.90] | 1.66 [0.98, 2.53] |

## Headroom (cost of ordering divided by hindsight-optimal)

Ratio of totals over states, with a bootstrap CI over states. Also the median of per-state ratios.

| ordering | ratio of totals [95% CI] | median per-state ratio [95% CI] |
|---|---|---|
| random / optimal | 7.03 [5.40, 9.47] | 3.04 [2.45, 4.08] |
| outside_in / optimal | 5.57 [3.63, 8.67] | 2.19 [1.83, 2.74] |
| fewest_contacts / optimal | 4.82 [3.20, 7.43] | 1.92 [1.50, 2.43] |

## Rotation split (assembly has a successful logged path with max rotation > 15 deg)

Caveat: an RRT path can rotate even when a pure translation would work, so this measures rotation *in the logged path*, not rotation that was *needed*.

| group | assemblies | states | random/optimal (ratio of totals) [95% CI] |
|---|---|---|---|
| rotation > thr | 1 | 2 | 1.89 [1.50, 2.84] |
| translation-like | 66 | 180 | 7.14 [5.47, 9.72] |

**State-level rotation subset** (a successful query at the state has max path rotation > 15 deg): 1 states in 1 assemblies.
 Too small for a separate replay (n < 20 states).

![replay](figures/replay_pilot_v1.png)
