# Per-state replay on cached pilot queries (pilot_v1 (planner + prep + setup))

Source labels: `data/labels/pilot_v1/labels.jsonl` (565 logged CMG-RRT queries). Cost = planner time + SDF prep. Bootstrap 95% CIs: 10,000 resamples, seed 0. This replays real logged queries; nothing is simulated. The trajectory through states is fixed by the labelling run, and each ordering only changes how much is spent finding the first success at each state.

- states with complete query sets: **184** (182 with >= 1 success, 2 with none) across **68** assemblies
- states with no success (every ordering pays everything): 2, total 182 s, median 91 s/state

## Per-state cost to first success (s), states with >= 1 success

| ordering | median [95% CI] | mean [95% CI] |
|---|---|---|
| random | 0.96 [0.73, 1.13] | 4.35 [3.10, 5.82] |
| outside_in | 0.81 [0.63, 1.11] | 3.46 [2.23, 4.98] |
| fewest_contacts | 0.73 [0.61, 0.98] | 3.00 [1.91, 4.35] |
| optimal (unattainable lower bound) | 0.32 [0.27, 0.35] | 0.67 [0.45, 0.97] |

## Per-assembly cost (s): sum over the visited states with >= 1 success

| ordering | median [95% CI] | mean [95% CI] |
|---|---|---|
| random | 2.92 [2.00, 4.62] | 11.82 [7.20, 17.45] |
| outside_in | 2.58 [2.04, 3.45] | 9.41 [5.57, 14.20] |
| fewest_contacts | 2.52 [1.99, 3.36] | 8.15 [4.67, 12.61] |
| optimal | 0.90 [0.67, 1.09] | 1.81 [1.13, 2.68] |

## Headroom (cost of ordering divided by hindsight-optimal)

Ratio of totals over states, with a bootstrap CI over states. Also the median of per-state ratios.

| ordering | ratio of totals [95% CI] | median per-state ratio [95% CI] |
|---|---|---|
| random / optimal | 6.54 [5.11, 8.62] | 2.71 [2.23, 3.47] |
| outside_in / optimal | 5.21 [3.43, 7.88] | 2.04 [1.68, 2.45] |
| fewest_contacts / optimal | 4.51 [3.05, 6.77] | 1.82 [1.38, 2.23] |

## Rotation split (assembly has a successful logged path with max rotation > 15 deg)

Caveat: an RRT path can rotate even when a pure translation would work, so this measures rotation *in the logged path*, not rotation that was *needed*.

| group | assemblies | states | random/optimal (ratio of totals) [95% CI] |
|---|---|---|---|
| rotation > thr | 1 | 2 | 1.87 [1.49, 2.77] |
| translation-like | 66 | 180 | 6.64 [5.18, 8.79] |

**State-level rotation subset** (a successful query at the state has max path rotation > 15 deg): 1 states in 1 assemblies.
 Too small for a separate replay (n < 20 states).

![replay](figures/replay_pilot_v1_prep.png)
