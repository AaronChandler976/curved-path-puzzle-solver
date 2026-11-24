# Run 04 T6: fresh data pool

## T6.1 Counts (beyond pilot_v1's 1,328 labelled assemblies)
| source | candidates | usable | evidence |
|---|---|---|---|
| 9–12 parts, watertight | 581 | 255 clean (max penetration ≤ ε, has contacts); 325 interpenetrating; 1 no contacts | `experiments/2026-11-23_run04_contact_scan_9to12/results.jsonl` |
| interpenetrating, 3–8 parts (skipped in v1) | 1,033 | see T6.2 | `data/labels/pilot_v1/summary.jsonl` |

## T6.2 Per-pair penetration allowance
- **Measured** with the oracle's exact part SDFs at vertices + 20,000 samples per part, for 1,358 assemblies (1,033 + 325)
  (`experiments/2026-11-23_run04_penetration/`).
- **Caps:** absolute 0.03 (unit frame) AND 0.2 × the thinner part's smallest bbox extent (DECISIONS #18).
  **439 recovered** (342 with 3–8 parts, 97 with 9–12); **919 stay excluded** (566 over the absolute cap, 353 over the
  relative cap) (`experiments/2026-11-23_run04_t6_pool/allowance{,_meta}.json`).
- **Rule:** each listed pair's allowance = the query's own measured start penetration + ε; every other pair keeps ε
  (`cmgrrt.query`; DECISIONS #19, which also records the first, rejected rule).
- **Validation** on 48 recovered assemblies, all 906 success paths, the query's own samples, step ≤ ε/2
  (`experiments/2026-11-23_run04_allowance_check2/summary.json`):

| check | pass |
|---|---|
| (A) start pose valid | 906/906 (and 1,193/1,194 of all queries) |
| (B) non-overlapping pairs keep the global ε along the path | 906/906 |
| (C) never deeper into an overlapping partner than at the start (+ε) | 906/906 |
| (D) end pose clear of every part at the global ε | 906/906 |

  The first rule (dense offset) failed C on 30/928 paths (`experiments/2026-11-23_run04_allowance_check/`).
- **Spot renders** (5): `reports/run04/figures/allowance_*.png` (3 CMG-RRT-stage paths, 2 straight pulls).

## T6.3 Labelling cost and plan
Pilot: 110 assemblies, oracle v2 with label mode (CMG-RRT always runs), T = 30 s, idle guard
(`experiments/2026-11-23_run04_cost_pilot/estimate.txt`).

| source | assemblies | queries / assembly | worker-s / assembly | projection for the whole source at 10 workers |
|---|---|---|---|---|
| v1 | 30 | 11.3 | 83 | 1,328 → 3.1 h |
| fresh 9–12 (clean) | 30 | 57.8 | 683 | 255 → 4.8 h |
| fresh allowance (39 with 3–8 parts, 11 with 9–12) | 50 | 23.9 | 276 | 439 → 3.4 h |

Plan: label all of it (≈ 11.3 planner-hours, within ~12 h), fresh assemblies first. That gives 694 fresh candidates,
so a test set of about half (≈ 340) clears the ≥ 250 requirement; the "stop and report" condition (< 150) is not met.
