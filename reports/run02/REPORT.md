# Run 02 report (2026-11-22 → 2026-11-23)

**What works now:** CMG-RRT runs as the oracle with an exact union-SDF detector (ε = 0.005). With it, 99.5% of starts are valid, setup is about 0.02 s per part, and 1,328 assemblies (17,116 queries) are labelled in `data/labels/pilot_v1/`.

## Gates
| stage | gate | evidence |
|---|---|---|
| R0 review | done (no code bugs; limitations noted) | `reports/run02/run01_review.md` |
| R1 slots + runlog | **PASS** (slot test: an 11th acquire blocks) | `experiments/2026-11-22_run02_pytest_r1/stdout.log`; re-run at end: 9 passed, `experiments/2026-11-23_run02_pytest_final/stdout.log` |
| R2 clean repro | **FAIL**: elk not solved (blocker #1) | `reports/run02/smoke_clean.md`, `reports/run02/cmgrrt_reference.md` |
| R3 exact SDF | **PARTIAL**: start-valid 100% PASS. Bundled: 2 of the 4 R2-solved examples re-solved. 16505 is **not solved even with the full 5,000 iterations** (see below). alpha was cut by the wall cap | `reports/run02/r3_exact_sdf.md`, `experiments/2026-11-22_exact_sdf_validation/` |
| R4 relabel v1 | **PASS** (1,328 ≥ 50 assemblies) | `experiments/2026-11-22_pilot_v1_labels/stdout.log` |
| R5 analysis | **PASS** (final pass) | `reports/run02/analysis_v1.md`, `experiments/2026-11-23_analysis_v1_final/` |
| R6 pipeline test | done; **PIPELINE TEST, not a result** | `experiments/2026-11-23_s6_pipeline_test_v1/pipeline_test.md` |

## Key numbers (all from logged runs)
- **Reproduction vs paper:** 4/13 bundled examples solved with the authors' `test_list.json` settings (16505, mobius_light, alpha; 11356 only after switching the SDF mesh to `0.obj`). **Elk was not solved:** it used all 5,000 iterations in 982 s. The paper reports 100% success for elk, at a mean of 156 min on 16 cores with a 4 h cap. The public script has no parallel exploration and no random-rotation step (`smoke_clean.md`).
- **Start-valid, 50 assemblies (185 queries):** learned 67.0%, exact 100.0%. **ε sensitivity** on 30 assemblies (107 queries): success was 87.9 / 90.7 / 92.5% at ε = 0.0025 / 0.005 / 0.01, with 100% start-valid at every ε (`experiments/2026-11-22_exact_sdf_validation/`).
- **v1 labels:** 17,116 queries over 4,685 states and 1,328 assemblies (1,249 complete, 79 stuck). Success rate 0.873 (v0: 0.761). Unsolved queries that started invalid: 3.3% (v0: 85.4%). Setup is 0.024 s per part at p50 (v0 prep: 66 s per query).
  - **Paired v0 → v1, depth-0 queries (1,291):** success rose from 0.668 to 0.888. 37 assemblies went from stuck to complete; 1 went from complete to stuck (02716).
  - **Interpenetration re-check at ε:** 75 assemblies that v0 skipped are now labelled (65 complete, 10 stuck). 1,033 are still skipped for penetration > 0.005 (`analysis_v1.md`).
- **Replay headroom on v1, ordering cost / hindsight-optimal, 4,606 states** (`replay_pilot_v1.md`, `replay_pilot_v1_with_prep.md`):

| ordering | planner-only: ratio of totals [95% CI] | planner-only: median per-state ratio | planner + setup: ratio of totals | planner + setup: median per-state ratio |
|---|---|---|---|---|
| random | 9.33 [8.77, 9.96] | 3.31 [3.13, 3.43] | 8.59 [8.11, 9.12] | 2.83 [2.69, 2.95] |
| outside-in | 7.33 [6.68, 8.06] | 1.92 [1.80, 2.02] | 6.76 [6.18, 7.40] | 1.75 [1.67, 1.84] |
| fewest contacts | 6.37 [5.78, 7.01] | 1.57 [1.50, 1.64] | 5.89 [5.36, 6.46] | 1.48 [1.42, 1.53] |

  The rotation subset has 70 states (57 assemblies) where a logged path rotated more than 15°. There, random / optimal is 5.43 [4.18, 7.76]. This counts rotation in the logged path, not rotation the part needed.
- **Throughput:** 5,059 queries/hour with 10 CPU workers and T = 30 s (`analysis_v1.md`; load info in `experiments/2026-11-22_pilot_v1_labels/load_info.txt`). The R5 first pass ran alongside for a few minutes near 01:00, so this rate is slightly confounded.
- **16505 with the exact detector at the full budget** (seed 0, test_list settings, run alone): **not solved**, 5,000 iterations in 3,198 s (`experiments/2026-11-23_exact_bundled_fullbudget/results.jsonl`, load info in the same folder). With the learned SDF, R2 solved it at iteration 2,880. With one seed per detector, RRT randomness and a detector effect cannot be separated, so R3's "slower, not wrong" explanation is unproven for 16505.

## Needs Aaron
1. **Elk / paper reproduction (blocker #1).** A fair test needs runs of at least 4 h or the authors' parallel code, which is not in the repo. `scripts/repro_cmgrrt.py` has no iteration-limit flag yet. Should I add `--iterations` and run elk for 4 h, alone, overnight?
2. **Exact vs learned detector on bundled examples, multiple seeds.** 16505 is solved by the learned SDF (1 seed) and not by the exact one (1 seed, full budget). Run 3 seeds of each for 16505 and alpha, alone (about 1 h per exact run). Alpha example:
   `env -u PYTHONPATH conda run --no-capture-output -n disasm python scripts/repro_cmgrrt.py --example puzzle/alpha --seed 1 --cap-min 70 --detector exact --run-dir experiments/<date>_exact_bundled_fullbudget`
3. **1,033 assemblies are skipped for mesh interpenetration > ε.** Should these be labelled with a per-pair penetration allowance, or stay excluded?
4. **Overfitting in the R6 pipeline test:** validation loss rises after the first epochs in all four model/head combinations. The real experiment needs early stopping and regularization. This is a pipeline observation, not a model comparison.

## Decisions made for you
See `reports/run02/DECISIONS.md` (#1–#17). The main ones: ε = 0.005 (#6–8); `0.obj` as the exact-detector mesh (#11); T = 30 s and `--max-pen` = ε (#13); the labeler exit bug fix (#14); running R6 after labelling finished early (#15).

## Proposed next run
- **Labelling budget:** about 5,000 queries/h at T = 30 s. The eligible 3–8-part list is exhausted. The next sources are 9–12-part assemblies (states grow roughly as n²; estimate the count from `experiments/2026-11-22_contact_scan/` before launching) and the 1,033 interpenetration skips (item 3).
- **Tier A labels from ATA:** worth setting up now for pretraining. v1 is cheap enough that Tier B is no longer the bottleneck, so this is lower priority than fixing the training recipe.
- **When the data is big enough:** 4,606 states with ≥ 1 success over 1,328 assemblies is enough for the real GNN-vs-baselines experiment, using an assembly-level split with 5 seeds. Run it next, after adding early stopping.
