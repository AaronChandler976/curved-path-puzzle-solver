# Run 04 report: oracle v2, data v2, frozen fresh test set (IN PROGRESS)

**Ready for run 05?** Not yet: T5 (exact vs learned SDF) is running; T7 (labelling), T8 (split + PREREG) and T9 (elk)
follow. This file is refreshed before each deadline; STATUS.md has the live state.

## Gates
| stage | gate | evidence |
|---|---|---|
| T0 orient | done | `reports/run04/STATUS.md` |
| T1 tooling | **PASS** (idle guard, seeded sampling, guarded runners; tests pass) | `src/disasm/util/idle_guard.py`, `tests/test_idle_guard.py`, `tests/test_seeded_sampling.py`, `experiments/2026-11-23_run04_pytest_t6/stdout.log` |
| T2 ASAP + PointNet prep | **PASS** (redmax built; adapter = redmax on 20/20; ASAP retrain + PointNet dry runs) | `experiments/2026-11-23_run04_t2_redmax/agreement.json`, `experiments/2026-11-23_run04_t2_dryruns/results.json`, DECISIONS #9–#12 |
| T3 unconfounded live rerun | **PASS** (238/240 runs clean on the first try, 1 fixed by a re-run, 1 still confounded) | `reports/run04/live_rerun.md` |
| T4 oracle v2 | **PASS** (123/124 misses solved, the last one explained; 0 invalid successes) | `reports/run04/oracle_v2.md` |
| T5 exact vs learned SDF | running | `experiments/2026-11-23_run04_t5_sdf/` |
| T6 data pool | **PASS** (694 fresh candidates; allowance validated 906/906) | `reports/run04/data_pool.md` |
| T7 label pilot_v2 | pending | |
| T8 split + PREREG | pending (PREREG drafted: `docs/PREREG_run05.md`) | |
| T9 elk | pending | |

## T3: unconfounded live rerun (run 03 models, development test set)
GNN-Surv used **0.595× [0.455, 0.821]** of fewest contacts' planner time (HL −3.5 s per assembly, 43/2/11
wins/ties/losses) and 0.637× [0.463, 0.876] of ASAP zero-shot's, over 56 assemblies. The confounded run 03 numbers
were 0.613 and 0.670; method totals moved by under 3%. So run 03's confounding did not change the conclusion.

## T4: the oracle bug and the fix
The v1 adapter never tested the start pose's straight connection to any goal; it only tested newly added tree
nodes, which are rotated by a few degrees and collide on the way out of tight fits. Oracle v2 = straight-pull
pre-check (exactly that test, certified at step ≤ ε/2) → CMG-RRT, with goal edges confirmed and paths validated at
step ≤ ε/2. Validation set (124 misses + 500 random): misses solved 123/124 (v1: 52); random queries 86.4% vs 86.8%
success, 19% less total time, median query 0.037 s vs 0.89 s; **0 invalid successes** (v1: 28). Separately, 18.5% of
the v1 label successes fail the fine path check, almost all by under 10% of ε.

## Needs Aaron (so far)
1. 18.5% of v1 successes are invalid at fine resolution (marginal dips below −ε). This makes v1 labels and run 03
   results slightly optimistic about removability; v2 replaces them.

## Decisions made on his behalf
`reports/run04/DECISIONS.md` #1–#22.
