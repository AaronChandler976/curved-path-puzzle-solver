# Audit: phase0 (finish run 04), round 2 (re-audit)

Auditor: independent subagent, instructions = `prompts/audit.md` only. Date 2026-11-24 (~18:50–19:00).
Scope: `reports/run04/REPORT.md`, `reports/run04/labels_v2.md`, `reports/run04/STATUS.md`, `docs/PREREG_run05.md`,
`docs/PREREG_addendum.md`, `docs/course/`, and the run folders they cite. No planner jobs were run.
HEAD at audit time: `8524c31` (fix commit `fca3cfc`, STATUS `c40a061`).

## What was re-run / recomputed (all on saved outputs)
- `scripts/labels_v2_report.py ... --out /tmp/audit_p0b/labels_v2.md` -> byte-identical to `reports/run04/labels_v2.md`.
- `scripts/live_rerun_report.py --out /tmp/audit_p0b/live_rerun.md` -> byte-identical to `reports/run04/live_rerun.md`.
- `scripts/build_split_v2.py --source-file experiments/2026-11-23_run04_t6_pool/source.json --seed 0` -> identical to `data/splits/v2_split.json` (all keys).
- `experiments/2026-11-24_run04_t8_split/t6_test_overlap.json` recomputed from `data/labels/pilot_v2_{allowance_check,costpilot}/summary.jsonl` ∩ test: allowance 26, cost pilot 41, union 41, clean_test 306; both lists and per_dir sets match exactly, union ∩ clean_test = ∅.
- DECISIONS #20 claim "pilot labels not reused in pilot_v2": all 41 overlap assemblies' `pilot_v2` summary lines carry git `dc8767e` and timestamps ≥ 2026-11-24T06:00 (T7 run), so they were relabelled.
- Composition: train v1 1,129/1,425 = 79.2%; test fresh-allowance 220/347 = 63.4%, fresh-9to12 127/347 = 36.6%; train v1 assemblies have 3–8 parts. pilot_v2 status: 1,866 complete / 156 stuck (matches professor_feedback.md).
- `reports/run04/sdf_puzzles.md`: 4/12 runs confounded, busy_frac 0.104/0.635/0.128/0.061 (REPORT "0.06–0.64" correct); path re-check table present below the main table.
- `reports/run04/oracle_v2.md`: 85/880 (9.7%) T3 rerun invalid; 18.5% row labelled "checked with a seeded draw" (REPORT caveats correct).
- PREREG: `git diff b0d4bf8 HEAD -- docs/PREREG_run05.md` still only §8; `docs/PREREG_addendum.md` first committed `fca3cfc` 18:49:08; `data/splits/.v2_test_evaluated` does not exist; `configs/final_frozen.yaml` does not exist.
- Pre-addendum training activity: `experiments/2026-11-24_run05_dev_smoke/` (3 variants, 3 epochs, `--quick`, 18:42–18:43) trained on `data/processed/run05/dev_train_only.pt`: 300 assemblies, all in v2 `train`, 0 in val, 0 in test. `graphs_train_val.pt`: 1,675 assemblies, 0 test. No v2 val or test number exists.
- pytest (`env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q`, env disasm): **33 passed, 1 failed** (`tests/test_idle_guard.py::test_own_burner_not_outside`, outside_cores_30s 3.03 ≥ 0.8). The cause is environmental: the three `scripts/asap_contact_graphs.py` redmax workers (PIDs in `experiments/2026-11-24_run05_redmax/`, ~100% CPU each) run outside pytest's process tree. The logged T8 run (`experiments/2026-11-24_run04_pytest_t8/stdout.log`, 34 passed) is unaffected.
- No large data or secrets tracked (largest tracked file 1.3 MB; no .pt/.ckpt/.obj/.env).

## Status of round-1 findings (`phase0_1.md`)

| # | round-1 severity | finding | status |
|---|---|---|---|
| 1 | MAJOR | 41 test assemblies seen in T6, undisclosed | **Resolved.** Disclosed in REPORT §5 and `PREREG_addendum.md` §A (committed before any v2 val/test number), list in `t6_test_overlap.json` (verified exact), sensitivity analysis on the 306 clean assemblies pre-registered and wired into `scripts/eval_v2.py --sensitivity`. Split unchanged. |
| 2 | MINOR | labels_v2.md covers test rows | Resolved (REPORT §4 states it; nothing chosen from it). |
| 3 | MINOR | git_hash.txt names b0d4bf8 | Resolved in REPORT §4 (run folder file itself not annotated; acceptable). |
| 4 | MINOR | "no pilot_v1 assembly" wording | Partly resolved: REPORT §5 fixed; `docs/PREREG_run05.md` line 17 still says "(never in pilot_v1)". See below. |
| 5 | MINOR | distribution shift not stated | Resolved, with a wording slip (below). |
| 6 | MINOR | T3 caveat (9.7% invalid) | Resolved. |
| 7 | MINOR | 18.5% seeded-draw caveat | Resolved. |
| 8 | MINOR | T5 confounded runs | Resolved. |
| 9 | MINOR | two CIs in live_rerun.md | Resolved by explanation in REPORT §2. |
| 10 | MINOR | T5 table "path fine-valid" empty | Resolved by note in REPORT §3. |
| 11 | MINOR | professor_feedback table | Resolved, with an overstatement (below). |
| 12 | MINOR | option1_requirements ATA as method | Resolved. |
| 13 | MINOR | README is the old proposal | Open, deferred to Phase 5 (logged in `reports/campaign/NEEDS_AARON.md`). Fine for Phase 0. |
| 14 | MINOR | campaign STATUS stale | Resolved. |

## New / remaining findings

| severity | file | what is wrong | how to verify |
|---|---|---|---|
| MINOR | `docs/PREREG_addendum.md` §A (line "committed ... before any v2 model was trained"), `reports/campaign/DECISIONS.md` #4–#5 | Literally false: three smoke models (`mlp_bce`, `pn_gnn_survival`, `gnn_survival_tail`, 3 epochs each, with `best.pt`) were trained at 18:42–18:43, before the addendum commit (18:49:08) and while DECISIONS #4 says "No model is trained ... before the Phase 0 audit passes". They used train-split assemblies only (300 assemblies, internal dev split) and produced no v2 val or test number, so nothing was compromised. Fix the wording to "before any v2 val or test number existed (only train-only smoke tests had run)". | `ls -l --time-style=full-iso experiments/2026-11-24_run05_dev_smoke/*/seed100/best.pt`; `git log -1 --format=%ci fca3cfc -- docs/PREREG_addendum.md`; aid membership of `data/processed/run05/dev_train_only.pt` vs `v2_split.json`. |
| MINOR | `reports/run04/REPORT.md` §5 "Distribution shift" | "test is 63% allowance-recovered and 37% 9–12-part assemblies" implies 37% of test has 9–12 parts. In fact 176/347 (51%) of test has 9–12 parts; 37% is the *clean* fresh-9to12 source, and some allowance-recovered assemblies are also 9–12 parts. Say "37% clean 9–12-part". | `v2_split.json`: count test ids with `n_parts` in 9–12 -> 176; source counts 220/127. |
| MINOR | `docs/course/professor_feedback.md` | "so every state is physically valid" overstates it for the 439 allowance-recovered assemblies, whose assembled (start) state has mesh interpenetration tolerated by the per-pair allowance. Say "valid up to the documented penetration allowance". | `reports/run04/data_pool.md`; REPORT §4 "interpenetrating assemblies recovered by the per-pair allowance". |
| MINOR | `docs/PREREG_run05.md` §0 line 17 | Still "(never in pilot_v1)"; 171 test assemblies have a pilot_v1 `skipped` summary line. The PREREG need not be edited (it would break "only §8 changed"), but the addendum should carry the clarification "no pilot_v1 query label" so the registered documents are accurate. | `grep -n 'never in pilot_v1' docs/PREREG_run05.md`; round-1 check (171 skipped, 0 labels). |
| MINOR | `experiments/2026-11-24_run04_t8_split/t6_test_overlap.json` | No command, script or git hash records how this file was produced (the folder's `cmd.txt` is only the split build). Contents are correct (recomputed exactly), but it is now an input to the registered sensitivity analysis and should have a logged generating command. | `cat experiments/2026-11-24_run04_t8_split/cmd.txt`; `grep -rl t6_test_overlap scripts` -> only `eval_v2.py` (reader). |
| MINOR | `tests/test_idle_guard.py::test_own_burner_not_outside` | Fails whenever any other CPU-heavy process runs (here the project's own redmax workers), so `pytest` is not reproducible while background jobs run. Either mark the test as requiring an idle machine (skip with a reason when outside load > threshold) or document it. Not a code regression; the logged T8 pytest run passed. | Run pytest while `experiments/2026-11-24_run05_redmax` workers are alive -> 1 failed, 33 passed. |
| MINOR | `README.md` | Still the original puzzle proposal (carried from round 1; deferred to Phase 5 and logged). | `head README.md`. |

Not found: no untraceable number (all REPORT additions traced above), no test-marker violation, no test label read
for training/selection, no PREREG change outside §8, the addendum precedes every v2 val/test number, no dropped
variant or seed (none trained for results in this phase), no large data or secrets committed, no timing without the
idle guard in T7.

VERDICT: PASS
