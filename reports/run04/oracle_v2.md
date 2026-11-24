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

(filled in below from `experiments/2026-11-23_run04_oracle_validation/`)
