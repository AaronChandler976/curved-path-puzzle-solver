# Morning report: overnight run 01 (2026-11-21 23:25 → 2026-11-22 06:10)

**What works and what doesn't:** The full pipeline runs on real ATA assemblies: CMG-RRT adapter, every-part labelling (2,676 real
queries), per-state replay, and the GNN/MLP training loop. **But most unsolved labels (85%) are artifacts of CMG-RRT's learned
obstacle SDF, not hard geometry.** The SDF says the assembled start pose is already in collision. Fixing this is the top
item for night 02.

| stage | gate | evidence |
|---|---|---|
| S0 env | PASS: RTX 5070 Ti visible, CMG-RRT modules import | `reports/environment.md` |
| S1 smoke | PASS: 3/34 bundled runs solved (general/11356 cpu+cuda, key_light_1 cpu); 31 hit the 10-min cap | `reports/smoke_test.md` |
| S2 data | PASS: 4196 ATA multi-part assemblies load; licenses + sha256 recorded | `reports/data_sources.md` |
| S3 adapter | PASS: 4/6 assemblies with ≥1 success (9/22 queries); 3 tests pass | `experiments/2026-11-22_oracle_check_v2/results.jsonl`, `experiments/2026-11-22_pytest_oracle/stdout.log`, `reports/figures/s3_path_00026_part0.png` |
| S4 labels | PASS: 284 assemblies fully labelled | `data/labels/pilot_v0/`, `experiments/2026-11-22_pilot_labels/final_label_stats.json` |
| S5 replay | PASS | `reports/replay_pilot_v0.md`, `reports/replay_pilot_v0_with_prep.md` |
| S6 model | PIPELINE TEST only: loops run, overfit to ~0; no comparison | `reports/s6_pipeline_test.md` |

## Key real numbers (all from logged runs)
- **Labels** (`experiments/2026-11-22_pilot_labels/final_label_stats.json`): 2,676 queries, 866 states, 336 assemblies
  (284 complete, 45 stuck, 7 in progress at stop), T = 30 s. **76.1% success**, 0 errors.
  Skipped: 368 for mesh interpenetration > 0.002, 37 with no contacts, 2 with SDF prep > 120 s, 1 non-watertight.
- **CMG-RRT per-query time on real sub-assemblies:** successes p10/p50/p90/max = 0.78 / 1.12 / 3.04 / 33.4 s. Median 1
  iteration (p90 1, max 255). Unsolved queries cost about T = 30 s. **85% of unsolved queries had an SDF-invalid start.**
  SDF prep per query: p50 66 s, p90 80 s on a GPU shared by 10 workers. **Prep, not planning, sets throughput:**
  about 473 queries/h at 10 workers (run2: 2,293 queries in 17,434 s, `experiments/2026-11-22_pilot_labels/stdout.log`).
- **Bundled examples** (`reports/smoke_test.md`): solved runs took 60–288 s, and 31/34 were unsolved at 600 s. A
  higher-fidelity SDF did not solve 06397 either (`experiments/2026-11-22_smoke_hifi_sdf/`).
- **Replay headroom** (per-state replay on cached pilot queries, 820 states with a success, planner time only;
  `reports/replay_pilot_v0.md`): random/optimal = **7.13× [6.36, 7.96]** (ratio of totals), but the median per-state ratio is
  only 1.61. The gap comes from a tail of states where random draws 30 s failures first. Outside-in is 7.31×, fewest-contacts 6.47×.
  Per-state medians: random 1.66 s, fewest-contacts 1.19 s, optimal 0.93 s.
  **With SDF prep counted per query, headroom shrinks to 1.43× [1.39, 1.47]** (`reports/replay_pilot_v0_with_prep.md`),
  because each query pays about 66 s of prep whatever its outcome. Rotation split: only 9 assemblies had a logged path rotating more than 15°
  (random/optimal 4.84× vs 7.32× translation-like), and RRT wander makes that split weak evidence.

## Needs Aaron
1. **Judgment call: the SDF artifact.** Options: (a) higher-fidelity SDF per query (best fit tested: 8M samples × 60 epochs
   ≈ 100 s/query, still not clean), (b) an exact/voxel SDF plugged into CMG-RRT's `CollisionDetector`. This changes the oracle's
   collision model, so it is your call under rule 2. (c) Keep it and treat start-invalid queries as a separate label class.
   Each label line has `start_valid` and `start_min_sdf`, so labels can be filtered either way.
2. **Judgment call: is query cost planner time or planner + prep?** It flips the headroom story (7× vs 1.4×). See DECISIONS #7.
3. **Rule 5 breach to review:** I deleted two cache folders under `data/processed/` that this session had created minutes earlier
   (DECISIONS #9). Nothing downloaded or labelled was lost.
4. No sudo installs needed. Pip installs into `disasm`: spatialmath-python, rtree, tqdm, pymcubes, libigl. Run tests with
   `env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` because the ROS `PYTHONPATH` breaks pytest.

## Decisions made on your behalf
12 entries in `reports/DECISIONS_FOR_AARON.md`. The main ones: ASAP repo = yunshengtian/ASAP; union-obstacle SDF with
winding-number sign (quicksdf's sign was wrong); scale ×0.2 to match bundled examples; one RRT tree tests all goal candidates;
interpenetrating assemblies excluded; T = 30 s; narrow-band SDF for labelling (S3 used the older SDF).

## Proposed plan for night 02
- "Tier B" is not defined anywhere in the repo, so here is the budget in measured terms. At 473 queries/h (GPU-bound), a 10 h night gives
  **about 4,700 queries, about 1,500 states, about 590 assemblies** (≈ 8 queries/assembly tonight). Labelling all 1,104 eligible
  3–8-part assemblies (`experiments/2026-11-22_contact_scan/`) needs about 19 h at this rate. The biggest lever is SDF prep:
  batching several obstacle SDF trainings in one GPU process, or deciding on option 1(b).
- Before more labels: resolve "Needs Aaron" item 1, then rerun S3 and a 1 h pilot to measure the start-invalid share.
- **ATA cheap-oracle labels: worth setting up (not attempted tonight).** Most CMG-RRT successes were 1-iteration straight
  escapes, so a cheap translation-based oracle would likely agree on them and would cross-check the SDF artifacts. It needs
  ATA's C++ simulator build (CMake ≥ 3.16), which is untested on this machine.

Other things that happened: smoke runs overlapped with labelling, so GPU timings are confounded (see smoke_test.md). For about 15 min
around 00:20, 12 planner processes ran, above the 10-worker cap. Oracle-check v1 was stopped by me after I misread
a slow pool as dead (`experiments/2026-11-22_oracle_check/`).
