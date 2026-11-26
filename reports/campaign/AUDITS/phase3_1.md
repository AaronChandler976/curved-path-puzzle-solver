# Audit phase3_1 (Phase 3: final test, evaluated once)

Auditor: independent subagent. My only instructions were `prompts/audit.md`, the phase name, and the report and run paths.
Date: 2026-11-26 (local). HEAD at audit start: b869319. At the end it was 40186f8, because another commit landed during the audit.
Audited: `reports/final_eval/{REPORT,replay,live,live_registered,live_P1,failure_analysis}.md` and
`reports/final_eval/figures/*.pdf`. I also checked the run folders `experiments/2026-11-25_final_eval_replay/`,
`experiments/2026-11-24_final_eval_live/`, `experiments/2026-11-25_final_failure_analysis/` and
`experiments/2026-11-26_demo_01310/`, plus `data/splits/.v2_test_evaluated`, `docs/PREREG_run05.md`,
`docs/PREREG_addendum.md`, `configs/final_frozen.yaml` and `reports/campaign/DECISIONS.md`.
My reproduction folder is `experiments/2026-11-26_audit_phase3_1_repro/`. It contains `cmd.txt`, `git_hash.txt`, the scripts
`indep_live.py`, `indep_replay.py`, `check_ckpts.py` and `budget_overshoot.py` with their `.log` files, the regenerated
`live.md`, `failure_analysis.md`, `failure/` and `figures/`, the snapshot rebuilds `snap_P1/` and `snap_P12/`, and
`pytest.log`. I ran no planner job and did not re-run the test evaluation. `eval_v2.py --split test` refused because the
marker exists (`refuse_check/`), and the marker is unchanged.

## Findings (severity | file | what is wrong | how to verify)

| # | severity | file | what is wrong | how to verify |
|---|---|---|---|---|
| 1 | MAJOR | `reports/final_eval/REPORT.md` §2 ("Survival p/c vs BCE p (GNN)") | The novelty sentence overclaims: "cost-aware ordering is cheaper … on total time and per assembly … the test supports it for the GNN". That holds only in replay on all 341 assemblies, and its ratio CI upper bound is 0.999. Three pre-registered readings disagree on total time: (a) the addendum A clean-test sensitivity gives 0.877 [0.767, **1.001**], so the CI includes 1 (`replay.md` clean table); (b) live gives 1.045 [0.955, 1.150], where GNN-Surv is costlier in total and only the HL condition holds; (c) the MLP pair goes the other way (replay 1.041, live 0.985, both n.s.). §4 mentions (b), but the §2 claim and the top summary do not qualify it. Restate it as "replay, all assemblies only; not on clean test totals, not on live totals, not for the MLP". | `replay.md` lines for "GNN-Surv (p/c) vs GNN-BCE (p)" in the main and clean tables; `live.md` registered table; reproduced in `indep_replay.log` and `indep_live.log` |
| 2 | MAJOR | `docs/PREREG_addendum.md` B.2 and `REPORT.md` §4 (budget policy, live) | The stated reason replay and live differ is contradicted by the live data. B.2 says live truncates CMG-RRT at T' and that "the difference is the pre-check time over T', which is rare". REPORT §4 attributes the smaller live saving (≈50% vs 72%) only to stuck disassemblies paying the second pass. In the live @b3 runs, the CMG-RRT stage of the 1,439 unsolved pass-1 queries ran a median **4.24 s**, 90th percentile 11.05 s and max 72.6 s against T' = 3 s (pre-check median 0.26 s). Time beyond 3 s adds up to **5,627 s of the 22,083 s** the two @b3 methods spent. The budget is checked once per RRT iteration (`src/disasm/oracle/cmgrrt.py` l.562–564), so one iteration can run far past it. The report must state this and correct the explanation. The @b3 numbers themselves are measured and can stay. | `experiments/2026-11-26_audit_phase3_1_repro/budget_overshoot.{py,log}` |
| 3 | MAJOR | `reports/final_eval/REPORT.md`, `replay.md`, `live.md` (T = 30 s, PREREG §0) | The registered budget T = 30 s is a soft limit, and no report says so. In the test labels (main config, attempt 0), unsolved queries cost a median 31.2 s, 90th percentile 37.4 s and max 73.2 s. 8,083 s of the 93,951 s of logged query time is time beyond 30 s. **154 CMG-RRT-only "successes" took > 30 s (max 127.7 s)** and 24 main-config successes cost > 30 s. All of them count as "success within T" in the replay, the solve-rate column and the ECE. Live, 436 successes exceeded their budget. All orderings face the same labels and seeds, so this does not obviously favour any method or change the §7 verdicts, but it is an unreported deviation from PREREG §0/§4. Disclose it, with these counts, in REPORT §1/§2 and DECISIONS. Optionally add a clearly labelled post-hoc sensitivity on saved outputs: successes after T treated as unsolved, cost capped at T. | `budget_overshoot.log`; `data/labels/pilot_v2/labels.jsonl` (fields `cmgrrt_time_s`, `cmgrrt_outcome`) |
| 4 | MINOR | `REPORT.md` §5 ("The failure mode: in each of its 10 costliest states …") | The paragraph sits under "Where GNN-Surv loses", but in 7 of the 10 costliest GNN-Surv states fewest contacts paid about the same or more (02925, 02512 second state, 03618, 02002, both 02869 states, both 03268 states). Only 02512 (first state) and 00675 are real losses. The confident-wrong-p pattern is real, but these states mostly illustrate hard states rather than losses against the heuristic. Use the 85 timeout-first loss states (+3,153 s) for the claim, or list the costliest *loss* states. | `failure_analysis.md` table (GNN-Surv vs fewest-contacts columns) |
| 5 | MINOR | `REPORT.md` §5 ("Likely cause: distribution shift") | The causal attribution is untested, and the subsets point both ways. By source, the 9–12-part source favours GNN-Surv (replay ratio 0.976) more than allowance does (1.109), and live every bin is 0.85–0.99. The composition percentages are correct (51%, 63%, 79%, 80%). Call it a hypothesis, not the "likely cause". | `replay.md` subset lines; `live.md` subset table |
| 6 | MINOR | `REPORT.md` §4 ("Both ASAP baselines are beaten live") | The word "beaten" is only defined by PREREG §7, for GNN-Surv vs the best heuristic. Here the §7 conditions are applied to other registered comparisons. The numbers support the two conditions (ASAP-retrained: 0.906 [0.827, 0.994], Holm p 0.04, HL −0.15), so say "both §7-style conditions hold" instead of "beaten". | `live.md` registered table |
| 7 | MINOR | `REPORT.md` §4 (Tail, live) | It says the Tail comparison shows "no difference that survives Holm", but the ratio CI is **1.058 [1.003, 1.110]**, entirely above 1. On live total planner time (the primary metric), GNN-Surv-Tail is cheaper than GNN-Surv by condition (a); only (b) fails. State this plainly, together with the interim P1 value (1.187, Holm p 0.016). | `live.md` / `live_P1.md` registered tables |
| 8 | MINOR | `replay.md` header, `live.md` header (PREREG §5) | PREREG §5 requires 10,000 bootstrap resamples for the ratio *and the HL difference*. HL CIs use 2,000 (`src/disasm/eval/stats.py` l.57; replay discloses "HL CIs 2,000"). `live.md` says "CIs: bootstrap over assemblies (10000)" although its HL CIs are also 2,000. This deviation is not in DECISIONS. | `stats.py` l.55–59; `live_report_v2.py` l.107 |
| 9 | MINOR | `live.md` (PREREG §5/§6) | §6 says live totals are reported "with the same metrics and tests as replay". Live reports no planner-call counts and no rot_state subset, and gives no reason. (The ratio to optimal and the CMG-RRT-only configuration are understandably not available live.) Add both, or log them as deviations. | `live.md` vs `replay.md` columns |
| 10 | MINOR | `REPORT.md` §2 subsets ("None is significant after correction") | Subset p values are uncorrected, and no correction family for subsets is registered or defined. Say "uncorrected; subsets are descriptive" instead of implying a correction was done. | `replay.md` subset lines |
| 11 | MINOR | `REPORT.md` §3 (prediction quality) | The C-index comparisons (0.674 vs 0.593 / 0.626; ListNet 0.689 "highest") have no CI or test. CLAUDE.md asks for a CI with every comparison. Add per-assembly bootstrap CIs or mark them as point estimates. | `replay.md` prediction-quality table |
| 12 | MINOR | `reports/final_eval/figures/budget_policy.pdf`; `live.md` exploratory table | The live GNN-Surv @b3 bar/row is the val-best seed (101) only, while the full-budget GNN-Surv bar/row next to it is the 5-seed mean. Neither the figure nor `live.md` labels this; only a code comment and REPORT do. Label "seed 101" in both. | `scripts/live_report_v2.py` comment at l.136; `methods_P4.txt` |
| 13 | MINOR | `experiments/2026-11-24_final_eval_live/load_info.txt` | P3 and P4 started from a dirty tree (`git_dirty: True` at hash d22975c / 8c8afd9). The dirty files are not recorded. Between d22975c and e283df6 the only code change is the cosmetic `scripts/live_report_v2.py` table-header edit; everything else is reports and run logs (`git diff --stat d22975c e283df6`). The planner code did not change, so the risk is low, but record what was dirty or state it in DECISIONS. | `load_info.txt` P3/P4 start blocks |
| 14 | MINOR | `reports/campaign/DECISIONS.md` | There are no Phase 3 entries. Findings 2, 3, 8, 9 and 13 and the interim-snapshot policy (`live_P1.md`, `live_registered.md`) should be logged as Phase 3 decisions or deviations. | `grep -n "Phase 3" reports/campaign/DECISIONS.md` |
| 15 | MINOR | repo (`talk/demo.gif`, 3.6 MB, committed in 3a26228) | This is outside this phase's reports, noted for the repo check. A 3.6 MB GIF is committed next to a 0.7 MB mp4. Consider whether it should be committed. | `git show --stat 3a26228` |

## Checks that passed (evidence)
- **Numbers trace and reproduce.**
  - *Live:* `live_report_v2.py` re-run on the saved `results.jsonl` gives a `live.md` **byte-identical** to
    `reports/final_eval/live.md`. The interim snapshots `live_P1.md` and `live_registered.md` rebuild exactly from
    `results.jsonl` filtered to the `methods_P1` and `methods_P1+P2` sets. The only difference is the exploratory-table
    header, which a later cosmetic script change produced (`git diff 8eab38e HEAD -- scripts/live_report_v2.py`).
  - *Independent live recomputation:* first clean attempt, seed-mean per assembly, ratio, W/T/L, Wilcoxon and Holm
    (`indep_live.log`). Every total, ratio, W/T/L and p in the registered and exploratory tables matches. Also checked:
    17,774 records = 17,697 runs + 77 re-runs; 0 still confounded or errored; complete/stuck counts match; `planner_s`
    equals the sum of query times for every reported run.
  - *Replay:* recomputed from `per_state.jsonl` with my own code (`indep_replay.log`). All totals (main and CMG-RRT-only),
    all 11 registered paired rows (ratio, HL, W/T/L, p, Holm) for all assemblies and for the 300 scored clean assemblies,
    and the subset ratios and p values match `replay.md` and REPORT §2.
  - *Replay against raw labels:* per-state `n_success`, `total_s`, `optimal` and the random-order expectation match the
    raw labels (first clean attempt) for every one of the 2,226 states and 12,444 queries in both configurations (max
    difference < 1e-4 s, float rounding). The no-success totals of 4,477 s and 6,247 s match.
  - *Failure analysis:* re-run gives an identical json and an identical md (paths aside).
  - *Figures:* `final_figures.py` re-run gives PDFs that differ only in 3 bytes (timestamp). All PDFs contain no raster
    image objects, so they are vector.
- **Test-set discipline.**
  - The marker was written at 2026-11-24 23:08:45 (git b5d851a).
  - `graphs_test.pt`, `clouds_test.pt` and `asap_inputs_test.pt` were created at 23:08:51–55, after the marker. Before
    the marker, `data/processed/run05/` had only train/val files.
  - `docs/PREREG_addendum.md`, `configs/final_frozen.yaml` and `configs/final_methods.json` were last committed at a13b397
    (23:04:31), before the marker. No later commit touches them and the working tree is clean for them.
  - Only one `--split test` results folder exists (`experiments/2026-11-25_final_eval_replay`). The script refuses a
    re-run.
  - All 50 checkpoints, the ASAP zero-shot checkpoint, the labels, states, split, redmax and clean-test files match the
    sha256 values frozen in `final_frozen.yaml` (`check_ckpts.log`).
  - `final_methods.json` and the live `model_spec.json` point to exactly those 50 checkpoints. The val-best seeds used
    live match `final_frozen.yaml` `val_best_seed`.
  - The live `test_ids.json` equals `v2_split.json` test (347 assemblies).
  - The untracked `experiments/2026-11-24_run06_dev_live` used 2 non-test assemblies.
- **Pre-registration.**
  - The §7 rule is implemented correctly: heuristic chosen on val (DECISIONS #8), ratio CI and Holm-Wilcoxon with
    HL < 0, Holm family of 11 matching PREREG §5.
  - Addendum A is evaluated, in replay and live.
  - Exploratory rows are kept apart, with uncorrected p values.
  - The live priority order P1–P4 was followed and every planned live method ran on all 347 assemblies.
- **Every variant and seed reported.** Replay and live both have 5 seeds per trained variant (live seed counts are [5]
  for every assembly). GATv2-Surv's exclusion from live follows the pre-written DECISIONS #10 rule and is stated.
- **Statistics.** CIs are by assembly, tests are paired on the same assemblies, and Holm covers the registered family.
  Every subset has ≥ 30 scored assemblies (smallest: parts 7–8, 37).
- **Timing hygiene.**
  - The live run was idle-guarded, with 24,686 idle samples and 131 busy ones (mostly Firefox at the start). Load info
    was logged at the start and end of each priority stage. No confounded run remains.
  - The failure-analysis script (23:14) finished inside the live run's initial 5-minute idle wait.
  - The demo re-run (09:37) started after the live run ended (09:29). It is labelled a demo and reproduces the live
    sequence for 01310/seed 101 (same parts, same stages, 102.2° final rotation).
  - Planner seeds equal sha1("run05-live-…"), checked on a 1/50 sample of runs (2,890 queries, 0 mismatches).
- **Repo.** `pytest`: 36 passed (`pytest.log`). The raw `results.jsonl` and `per_state.jsonl` are gitignored, not
  committed.

VERDICT: FAIL
