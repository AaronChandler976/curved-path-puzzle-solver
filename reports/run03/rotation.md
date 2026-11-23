# Run 03 R1: rotation-required labels

Pre-check: `src/disasm/oracle/linear_precheck.py`, driver `scripts/run_precheck.py`, log `experiments/2026-11-23_run03_precheck/stdout.log`, output `data/labels/pilot_v1/precheck.jsonl`. Report built by `scripts/rotation_report.py`.

**Method.** For each query the part is translated along every goal-candidate direction of the adapter (`cmgrrt.candidate_directions`, same order), out to the adapter goal distance D = bbox diagonal + 0.1. Collision model: the exact union SDF of the other remaining parts, ε = 0.005 (collide iff min SDF < −ε), evaluated at the robot's surface samples (same count as CMG-RRT: 3,888). **Step size:** step = max(ε/2, d + ε), where d = current min SDF. The step is 0.0025 (= ε/2) near contact. Wherever it is larger, every skipped pose is proven collision-free by the 1-Lipschitz bound of the SDF under translation. So the check is at least as strict as a uniform ε/2 sweep. The final pose checked is exactly t = D.

## Gate

- queries in v1: 17116; with a pre-check result: 17116 (**100.00%**); pre-check errors: 0
- pre-check time per query: median 0.062 s, p95 0.809 s (not a reported timing result)

## Counts

| level | needs rotation | out of | share |
|---|---|---|---|
| part (query) | 513 | 14935 successful queries | 3.43% |
| state (rot_state) | 405 | 4606 states with >= 1 success | 8.79% |
| assembly (rot_assembly) | 211 | 1328 assemblies | 15.89% |

First clearing direction among linear-free queries: {'contact_normal': 7624, 'axis': 6830, 'away_from_neighbour': 92}.

## Inconsistencies: `linear_free == True` but CMG-RRT unsolved

**124** of 2181 unsolved queries (5.7%) could have been removed by a straight pull that the pre-check certifies collision-free.
Their CMG-RRT iterations: median 18, min 1, max 2887; logged time median 30.8 s.

| assembly | state | part | CMG-RRT time (s) | iterations | first clearing direction | candidates |
|---|---|---|---|---|---|---|
| 00031 | 0-1 | 1 | 31.0 | 56 | +y | 7 |
| 00072 | 0-1-2 | 1 | 32.8 | 6 | -y | 7 |
| 00426 | 0-1-2-3-4 | 3 | 31.5 | 8 | +z | 7 |
| 00494 | 0-2-3-4 | 4 | 30.2 | 63 | +y | 8 |
| 00494 | 0-2-4 | 4 | 30.5 | 67 | +y | 8 |
| 00498 | 1-2-3 | 3 | 31.1 | 16 | away_from_1 | 9 |
| 00673 | 0-1-2 | 1 | 30.7 | 148 | +y | 8 |
| 00673 | 0-1 | 1 | 30.0 | 193 | +y | 8 |
| 01466 | 0-1-2 | 0 | 30.5 | 488 | +x | 9 |
| 01467 | 0-1-2 | 0 | 30.0 | 540 | +x | 8 |

**What this implies about the oracle at T = 30 s.** The adapter grows ONE CMG-RRT tree toward the first valid goal candidate. It tests straight connections to the other candidates only from newly added tree nodes, never from the start pose, and only with the library's coarse edge check (step 10·η = 0.02 = 4ε). A part that a straight pull would free can therefore stay unsolved: the tree is pulled toward a blocked goal, and the free direction is never tried from a node that can see it. These queries are real oracle misses, not physical blockages. They are labelled `unsolved` (censored), exactly as the oracle returned them. They inflate costs equally for every ordering in replay. They mean the v1 success rate is a lower bound on true removability, and a cheap linear pre-check before CMG-RRT would rescue them (run 04 candidate; it would change the oracle, so it is NOT applied in this run).

## Diagnostics for the rotation flag

- Max path rotation (logged) of `needs_rotation` queries: median 5.6°, share > 15°: 12.3%, share < 5°: 46.2%.
- For comparison, successful linear-free queries: median 5.5°, share > 15°: 0.1%.
- `needs_rotation` queries whose pre-check start pose is already below −ε (start penetration > ε with this sample draw): 21. A pull cannot start there, so the CMG-RRT success started from a pose that its own sample set judged valid.
- |start min SDF (pre-check) − logged start min SDF|: median 2.74e-08, p95 4.66e-04. They differ slightly because trimesh 5.2 draws the robot surface samples with an unseeded generator, so CMG-RRT's exact sample set is not reproducible from the logged seed. The pre-check uses a fresh draw of the same size.
- Caveat: almost half of the `needs_rotation` successes have a logged path that rotates < 5°. Such a part was freed by one of three things: a non-straight translation (sideways moves that no straight pull along a candidate direction makes), a small rotation, or a pass through CMG-RRT's coarse edge check (step 0.02 = 4ε) where the fine sweep (step ≤ ε/2) collides. This data does not separate the three. So `needs_rotation` really means 'needs more than a straight pull along the adapter's candidate directions'. It follows the run 03 definition exactly. The < 5° and > 15° shares above let the reader weigh it.
