# Run 04 report: oracle v2, data v2, frozen fresh test set (DONE; T9 run in campaign Phase 5)

**Ready for run 05?** Yes. Oracle v2 is validated, `pilot_v2` is labelled (2,022 assemblies, 0 confounded after
re-runs), the v2 split is frozen (test = 347 fresh assemblies) and `docs/PREREG_run05.md` was committed
(2026-11-23 23:50) before any v2 training. The only stage not run is T9 (elk, 4 h reproduction check). The campaign
moved it to Phase 5 so it cannot delay the test (`prompts/campaign.md`).

## 1. Gates
| stage | gate | evidence |
|---|---|---|
| T0 orient | done | `reports/run04/STATUS.md` |
| T1 tooling | **PASS** | `src/disasm/util/idle_guard.py`, `tests/test_idle_guard.py`, `tests/test_seeded_sampling.py` |
| T2 ASAP + PointNet prep | **PASS** (redmax = our adapter on 20/20; ASAP retrain + PointNet dry runs) | `experiments/2026-11-23_run04_t2_redmax/agreement.json`, `experiments/2026-11-23_run04_t2_dryruns/results.json` |
| T3 unconfounded live rerun | **PASS** (238/240 clean first try; 1 fixed by re-run; 1 still confounded) | `reports/run04/live_rerun.md` |
| T4 oracle v2 | **PASS** (123/124 misses solved, the last explained; 0 invalid successes) | `reports/run04/oracle_v2.md` |
| T5 exact vs learned SDF | **PASS** (hybrid not triggered; oracle unchanged) | `reports/run04/sdf_puzzles.md` |
| T6 data pool | **PASS** (694 fresh candidates; allowance validated 906/906) | `reports/run04/data_pool.md` |
| T7 label pilot_v2 | **PASS** (2,022/2,022 labelled, 0 errors, 0.00% confounded after re-runs) | `reports/run04/labels_v2.md`, `experiments/2026-11-24_run04_label_v2/` |
| T8 split + PREREG | **PASS** (split committed, `tests/test_split_v2.py` passes, PREREG predates v2 training) | `data/splits/v2_split.json`, `experiments/2026-11-24_run04_t8_split/`, `experiments/2026-11-24_run04_pytest_t8/stdout.log` (34 passed) |
| T9 elk 4 h | **DEFERRED to campaign Phase 5** (not run) | `experiments/2026-11-24_run04_elk/launch_cmd.txt` (prepared only) |
| T10 report | this file | |

## 2. T3: unconfounded live rerun (run 03 models, development test set)
GNN-Surv used **0.595× [0.455, 0.821]** of fewest contacts' planner time (HL −3.5 s per assembly, 43/2/11
wins/ties/losses) and 0.637× [0.463, 0.876] of ASAP zero-shot's, over 56 assemblies. The confounded run 03 numbers
were 0.613 and 0.670, and method totals moved by under 3%, so run 03's confounding did not change its conclusion
(`reports/run04/live_rerun.md`). That file shows two slightly different CIs for the same ratio in two tables,
because both tables draw from one bootstrap random generator. They are the same statistic with Monte-Carlo noise.

## 3. T4/T5: the oracle bug, the fix, the SDF decision
- **Bug:** the v1 adapter never tested the start pose's straight connection to a goal. Only newly added
  (rotated) tree nodes were tested, and in tight fits those collide on the way out. 123 of the 124 misses had a free
  straight pull from the start.
- **Oracle v2:** a straight-pull pre-check (exactly that test, certified at step ≤ ε/2), then CMG-RRT. Goal edges are
  confirmed and paths validated at step ≤ ε/2.
- **Validation (124 misses + 500 random queries):** 123/124 misses solved (v1: 52). On the random queries, success was
  86.4% vs 86.8%, total time 19% lower, median query 0.037 s vs 0.89 s, and **0 invalid successes** (v1: 28).
  Separately, 18.5% of v1 label successes fail the fine path check. Caveat: v1 used unseeded samples, so the
  check used a seeded draw of the same size. Run 04's own T3 live rerun (oracle v1, seeded) had 9.7% invalid
  successes at fine resolution (`reports/run04/oracle_v2.md`), which is why T3's timings are a development result only.
- **T5 (16505, alpha; 3 seeds × {exact, learned}):** the learned SDF "solved" 16505 3/3 and exact 0/3, but all 3 learned
  paths penetrate the part when checked with the exact SDF (27–49% of edges, down to −0.149 against ε = 0.005).
  Counting valid solutions it is 0/3 vs 0/3 on both puzzles. The hybrid fix was not triggered and oracle v2 is
  unchanged (DECISIONS #23). 4 of the 12 T5 runs are flagged confounded (busy_frac 0.06–0.64, `sdf_puzzles.md`). The
  table's "path fine-valid" column is empty; the path re-check is in its own table below it.

## 4. T6/T7: data v2
- **Pool:** 255 clean 9–12-part assemblies plus 439 interpenetrating assemblies recovered by the per-pair allowance;
  919 stay excluded as over the caps (`reports/run04/data_pool.md`). All 1,328 v1 assemblies were relabelled.
- **Labels:** 2,022 assemblies (1,866 complete, 156 stuck), 41,913 queries, 0 errors. `labels_v2.md` describes the
  whole pool, test included. It was written as the T7 labelling check before the split existed, and nothing was
  chosen from it.
- **Code version:** the run folder's `git_hash.txt` says `b0d4bf8` (dirty) because it was written at launch. The code
  that ran is `dc8767e`, committed 21 s later and carried on every summary line.
  - Confounded: 2,128 queries (5.1%) on the first pass; all fixed by re-runs, 0 left.
  - Wall time 12.6 h (05:47–18:30, 2026-11-24) with 2,001 s of busy waits.
  - Every summary line carries git `dc8767e`.
- **Pre-check share:** the straight pull produced 95–98% of the successes in every source × size bin. Main-config
  success rate is 0.71–0.89 by bin; CMG-RRT-only success is 0.01–0.03 lower.
- **v1 vs v2 on 15,903 shared queries:**
  - success → unsolved: 147; unsolved → success: 134.
  - Planner time: v1 23.96 h, v2 main 18.85 h, v2 CMG-RRT-only 27.95 h.
  - Full table: `reports/run04/labels_v2.md`.

## 5. T8: split sizes and pre-registration
`data/splits/v2_split.json` (seed 0; 1,996 duplicate groups):

| split | assemblies | v1 / fresh-9to12 / fresh-allowance |
|---|---|---|
| train | 1,425 | 1,129 / 109 / 187 |
| val | 250 | 199 / 19 / 32 |
| test | 347 | 0 / 127 / 220 |

- **Test:** fresh assemblies only. No test assembly has any pilot_v1 query label; 171 of them have a pilot_v1
  `skipped` summary line (excluded from v1 for interpenetration). 00014 is not in test (asserted in the builder and in
  `tests/test_split_v2.py`).
- **Disclosure (Phase 0 audit, MAJOR finding):** **41 test assemblies were labelled during T6 development**
  (cost pilot 110, allowance check 50; 26 of the 41 are in the allowance check that revised the allowance rule). No
  model or ordering was chosen on them; they informed oracle settings common to all methods. The split is kept. A
  sensitivity analysis of the §7 rule on the 306 other test assemblies is pre-registered in `docs/PREREG_addendum.md`
  §A. List: `experiments/2026-11-24_run04_t8_split/t6_test_overlap.json`.
- **Distribution shift:** by source, test is 63% allowance-recovered (fresh-allowance) and 37% from the clean 9–12-part
  source. By part count, 51% of test (176/347) has 9–12 parts. Train is 79% v1 (3–8 parts, no allowance). Test performance therefore measures transfer to larger and interpenetrating assemblies,
  not in-distribution accuracy.
- **Pre-registration:** `docs/PREREG_run05.md`, with §8 filled from these counts. Since its first commit only §8 has
  changed (`git diff b0d4bf8 090863e -- docs/PREREG_run05.md`).
- **Found during T8:** contact-graph sampling was unseeded (trimesh ignores `np.random.seed`). Labels are unaffected
  because every assembly's cached contact graph is used. The cache is frozen by a sha256 manifest and the sampling is
  now seeded (`reports/campaign/DECISIONS.md` #3).

## 6. T9: elk (run in campaign Phase 5, 2026-11-26)
`experiments/2026-11-26_phase5_elk/` (`cmd.txt`, `results.jsonl`, `stdout.log`, `guard_puzzle_elk_s0/`):
`scripts/repro_cmgrrt.py --example puzzle/elk --seed 0 --cap-min 240 --detector learned` (the authors' settings: eta
0.002, threshold −0.005, 50 steps, 10,000 samples; the bundled learned SDF; GPU), run alone after a 5-min idle wait.
- **Result: not solved within the 240-min cap.** 76,901 iterations, 3.42 M tree nodes, 14,400 s of planner time.
- **Timing hygiene:** busy_frac 0.0069 over 2,881 samples (< 0.05, not confounded).
- **Comparison with the paper:** it reports a 156-min mean on 16 cores, with a parallel tree exploration that the public
  code does not include. Our run is one process, but its numerical libraries used about 12 cores (median 11.7 in
  `guard_puzzle_elk_s0/idle_samples.jsonl`), so the difference is the missing parallel exploration, not the core count. One single-process run with one seed is not enough to compare success rates. We report that the
  public, single-process code did not solve elk in 4 h here.

## 7. Needs Aaron
1. 18.5% of v1 successes are invalid at fine resolution (marginal dips below −ε). v1 labels and run 03 results are
   therefore slightly optimistic about removability. v2 replaces them, and the paper reports it as a negative result.
2. Nothing else here needs Aaron. Campaign items go in `reports/campaign/NEEDS_AARON.md`.

## 8. Decisions made on his behalf
`reports/run04/DECISIONS.md` #1–#23, and `reports/campaign/DECISIONS.md` #3 (contact sampling).

## 9. Run 05 outline (follows PREREG)
Build train/val graphs (`scripts/build_dataset_v2.py`), train the 7 variants with the registered grid and seeds
(`scripts/train_v2.py`, `scripts/train_asap_v2.py`), evaluate on val only (`scripts/eval_v2.py --split val`), then
profile latency and memory. This is campaign Phase 1, in `reports/run05/`.
