# Run 04 T4: oracle v2 — the v1 bug, the fix, validation

Code: `src/disasm/oracle/cmgrrt.py` (`query`: `precheck`, `fix`, `margin`), `src/disasm/oracle/oracle_v2.py`,
`src/disasm/oracle/path_validate.py`. Tests: `tests/test_oracle_v2.py` (regression tests for the fixed bug),
`tests/test_seeded_sampling.py`.

## T4.1 Fine-resolution validation of saved v1 / live paths (untimed)

`experiments/2026-11-23_run04_path_validation/` (`paths.jsonl`, `analyze.py`, `stdout.log`). Every successful v1
query had a saved path (0 missing). Each edge is interpolated exactly like the planner (`SE3.interpolate`) and
checked with the exact union SDF at ε = 0.005. The step is at most ε/2 of sample-point displacement (rotation lever
arm included), and wider steps are taken only where the 1-Lipschitz bound certifies them.

| source | successes checked | invalid at fine resolution | of which start pose invalid under the check's sample draw | only the goal edge bad |
|---|---|---|---|---|
| pilot_v1 labels (unseeded planner samples; checked with a seeded draw of the same size) | 14,935 | **2,764 (18.5%)** | 23 | 384 |
| run 03 live (unseeded) | 859 | 182 (21.2%) | 5 | 23 |
| run 04 T3 live rerun (seeded: the check uses the planner's exact samples) | 880 | 85 (9.7%) | 5 | 51 |

Caveat for the two live rows: live runs saved each query's path to a file named by (assembly, obstacle set, part,
seed). The same query under two methods has the same seed, so a later method could overwrite an earlier method's file
before this check read it. With seeded samples (run 04) the two paths are usually identical; for run 03 (unseeded)
they can differ. The pilot_v1 row is unaffected (one query per file). Fixed for future runs: per-method work dirs in
`scripts/live_abd.py`; T4.4 uses per-config work dirs (attempt 1 had the same collision and was stopped:
`experiments/2026-11-23_run04_oracle_validation_aborted1/`, not used).

How the v1 paths fail (pilot_v1, first bad edge of each invalid path):
- **Depth:** marginal. The deepest point is −0.0051 (median), −0.0053 (p10) against the −0.005 limit. CMG-RRT's
  contact following keeps nodes exactly at the threshold, and the straight interpolation between two valid nodes
  dips just past it.
- **Edge size:** short tree edges, median 0.0009 translation and 0.16° rotation.
- **Goal edges:** 384 paths fail only on the long goal edge, which the library checks at step 10·η = 0.02 = 4ε.
- **Iterations:** median 1. Most of these are near-straight slides found in the first extension.

The coarse goal-edge discretisation can therefore admit invalid successes, as the prompt suspected. Most invalid
successes, though, come from contact-following tree edges that dip below −ε by less than 10% of ε.

## T4.2 Why 124 linear-free queries stayed unsolved

`experiments/2026-11-23_run04_diagnose_misses/` (`results.jsonl`, `analysis.txt`, `analyze.py`). An instrumented
copy of the v1 search loop (`src/disasm/oracle/diagnose.py`, same control flow) was run on all 124 queries with seeded
samples and the v1 seeds, T = 30 s, through the idle guard.

| candidate cause | evidence | verdict |
|---|---|---|
| start pose never tested for a straight connection to any goal | the v1 loop tests only the newest node `qs[-1]` of each extension (`RRT.step`, and the adapter for goals 1..k); the start is added in `RRT.__init__` and never tested. With the seeded samples, **123/124** queries have a free straight connection from the start, and the library's own coarse edge check accepts it for all 123 | **cause** |
| nodes that are tested are rotated, so their straight goal edges collide in tight fits | the per-query minimum rotation of the tested nodes has median 2.1° (p10 0.9°, p90 5.5°); the median rotation is 4.6°. The goal edge interpolates rotation back to identity while the part is still inserted | mechanism of the cause |
| tree biased toward goal 0 | the free direction is goal 0 in only 7/123; the others are tested only from (rotated) new nodes | contributes (same mechanism) |
| goal-edge discretisation (4ε) | coarse and fine disagree on 2 start-pose goal edges, both coarse-free / fine-blocked; it never blocks a free pull | not a cause of misses; it causes invalid successes (T4.1) |
| threshold mismatch pre-check vs `is_edge_valid` | same threshold (collide iff min SDF < −ε); the start is invalid under the detector for 1/124 | not a cause |

Iterations are also slow on these queries (median 10 iterations in 30 s). Even the 51/124 that the v1 loop solves
on this re-run (different sample draw) are found by chance.
The remaining query (1/124) has an invalid start pose under the seeded sample draw (start min SDF < −ε); a straight
pull cannot start there, and the run 03 pre-check's free verdict came from a different draw.

**Fix:** test the start pose's straight connection to every goal. In oracle v2 this test *is* the straight-pull
pre-check stage (the same sweep, certified at step ≤ ε/2), so it costs nothing extra; it is also available inside
the adapter alone as `fix=("root",)`. Goal edges accepted by the coarse check are confirmed at fine resolution
(`fine_goal`), and found paths are validated edge by edge, with invalid edges removed and the search continued
(`validate`). Regression tests: `tests/test_oracle_v2.py`.

## T4.4 Validation set

`experiments/2026-11-23_run04_oracle_validation/` (`results.jsonl` every attempt; `summary.json` from
`scripts/oracle_validation_report.py`; `idle_samples.jsonl`). 624 queries = the 124 misses + 500 random v1 queries
(seed 0), each under v1 / v2a / v2b, T = 30 s, the queries' v1 seeds, seeded samples, idle guard: 1,872 jobs; 60 were
confounded and re-run clean; **0 still confounded**, 0 errors. Every reported success's saved path was re-checked
independently at fine resolution (exact SDF, ε, step ≤ ε/2, the query's own samples).

| set | config | successes | success rate | total query time (s) | median (s) | invalid successes on recheck | decided by pre-check / CMG-RRT | "CMG-RRT only" successes (time s) |
|---|---|---|---|---|---|---|---|---|
| 124 misses | v1 | 52 | 41.9% | 3,028 | 30.1 | 5 | — | — |
| 124 misses | **v2a** | **123** | **99.2%** | 144 | 0.39 | **0** | 123 / 0 | 47 (3,225) |
| 124 misses | v2b | 123 | 99.2% | 145 | 0.39 | 0 | 123 / 0 | 41 (3,351) |
| 500 random | v1 | 434 | 86.8% | 2,907 | 0.89 | 23 | — | — |
| 500 random | **v2a** | **432** | **86.4%** | **2,352** | **0.037** | **0** | 424 / 8 | 428 (3,402) |
| 500 random | v2b | 431 | 86.2% | 2,330 | 0.035 | 0 | 424 / 7 | 429 (3,304) |

- **Gate: PASS.** 123/124 misses (99.2% ≥ 95%) are solved by oracle v2. The remaining one (05832, state 0-1-2-3,
  part 0) has an invalid start pose under its seeded sample draw (start min SDF −0.0105 < −ε), so neither stage
  can move it; that is a mesh-penetration case, not an adapter miss. 0 invalid successes at fine resolution in the
  validation set (v2a and v2b, both stages), against 28 for v1.
- **v1 vs v2a on random queries:** the same success rate within 2 queries (v2a rejects invalid v1-style successes);
  19% less total time; the median query drops from 0.89 s to 0.037 s because the pre-check decides 424 of 432
  successes. The pre-check's own cost is 0.22 s per query on average (110.6 s over 500).
- **"CMG-RRT only" (secondary config)** with the v2 fixes: 428/500 random queries and 47/124 misses. It still lacks
  the start-pose test, which is exactly what the pre-check stage adds.
- Fine checks at work in v2a: 84 goal edges and 66 paths were rejected and the search continued.
- **Decision: oracle v2 = v2a** (margin 0; DECISIONS #17). The margin gives no gain in success or invalid rate and
  rejects more goal edges (193 vs 84).

