# Audit phase1_2 (Phase 1: run 05 training, val only — re-audit)

Auditor: independent subagent, instructions = `prompts/audit.md` only. Date 2026-11-24 (local, ~21:50–22:10 PST).
Audited: `reports/run05/REPORT.md`, `training.md`, `val_replay.md`, `profile.md`, the run folders they cite,
`docs/PREREG_run05.md`, `docs/PREREG_addendum.md`, `reports/campaign/DECISIONS.md`, and the findings of `phase1_1.md`.
No planner job was run and no test label was read. Audit scratch outputs (kept): `experiments/2026-11-24_audit_phase1_2_repro/`
(`cmd.txt`, `git_hash.txt` = cb359a0, `eval_val/` re-run, `eval_val.log`, `training.md` + `train_figs/` re-generated, `pytest.log`).

## Re-checks that passed
- **Val replay reproduces bit-for-bit.** I re-ran `scripts/eval_v2.py --split val` at HEAD cb359a0 with the exact arguments
  in `experiments/2026-11-25_run05_eval_val_cpu/a/cmd.txt` (CPU default). The output `per_state.jsonl` and `results.json`
  are byte-identical to `.../a/`. The output `val_replay.md` differs from `reports/run05/val_replay.md` only in the
  self-referencing path line. `.../a/` and `.../b/` are also byte-identical to each other (per_state, results; md differs only in its path).
- **GPU→CPU change only affects ASAP rows.** In the superseded GPU run `experiments/2026-11-24_run05_eval_val/per_state.jsonl`
  versus CPU `.../a/per_state.jsonl`, the only keys that differ are `asap_retrained*` (219 states per config) and `asap_zs*`
  (10). Every own variant and heuristic is identical, as the REPORT states.
- **training.md reproduces.** `scripts/run05_training_report.py` re-run on `experiments/2026-11-24_run05_train/` gives a
  byte-identical `training.md`. The "18 of the 35 final checkpoints before epoch 10" count matches the best-epoch column.
  Curve colours are now matched between the loss and cost panels (checked `train_curves_gnn_survival.png`).
- **REPORT numbers trace.**
  - §2 and §3 tables, the paired comparisons, the §7 lines, subsets, and the §4 ECE/C-index all match `val_replay.md`
    and `.../a/results.json`.
  - §5 matches `experiments/2026-11-25_run05_profile/profile.json`. The arithmetic: 0.436 s / (2.41 + 0.12 ms) ≈ 172×,
    Tail 0.632 / 2.51 ms ≈ 252×, PN 0.585 / 4.30 ms ≈ 136×.
  - "Outside load ≤ 0.36 cores" matches `idle_samples.jsonl` (max `outside_cores_30s` = 0.358).
- **Test discipline.**
  - `data/splits/.v2_test_evaluated` is absent.
  - `data/processed/run05/*` was not modified after 19:30, and no new artefact holds test data.
  - `configs/final_frozen.yaml` does not exist yet. PREREG_run05 last changed 18:40, the addendum 18:54 (both before training).
- **Tests.** `env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest`: 35 passed (`.../pytest.log`).
- **Repo.** The largest tracked file is 1.3 MB (run02 jsonl). No checkpoints or data are committed.

## Status of phase1_1 findings
| phase1_1 finding | status |
|---|---|
| MAJOR val selection bias not stated | **Resolved.** REPORT one-liner/§3, the `val_replay.md` header (script-generated) and `training.md` state it. p-values are called descriptive. DECISIONS #9 records it. |
| MAJOR ASAP GPU nondeterminism | **Resolved.** CPU scoring is the default. a/b runs and my own re-run are bit-identical. The residual (ASAP-retrained's training-time selection was scored on GPU) is disclosed in DECISIONS #9. |
| MINOR CMG-RRT-only "beats" on val | **Resolved.** It is now printed as "§7 conditions, descriptive only". The REPORT says it is not a registered claim. |
| MINOR profile labels | **Mostly resolved.** Columns are labelled with thread count, both statistics are medians, and the batch is all 200 states. Residual below (batch-1 uses only 50 states, undisclosed). |
| MINOR latency statements (PN increment, untimed costs) | **Resolved** (REPORT §5, profile.md). |
| MINOR no busy samples during profile | **Resolved** (62 samples during the run). See the new MINOR on how they are interpreted. |
| MINOR min-10-epoch reading not in DECISIONS | **Partly resolved.** DECISIONS #9 records the reading but not the alternative, and REPORT §6 still says "as registered" (see below). |
| MINOR median-ratio CI resamples | **Resolved** (disclosed in the md header). |
| MINOR random "solved within T" | **Resolved** (shown as "—"). |
| MINOR untracked provenance files | **Partly resolved.** The train variants' cmd/git_hash are now committed. `experiments/2026-11-24_run05_eval_val_dev/cmd.txt` and `git_hash.txt` are still untracked. |
| MINOR training.md curve discussion and colours | **Resolved.** |

## Findings

- **MINOR**, `reports/run05/REPORT.md` §1 table, "latency / memory profile" row: it cites `experiments/2026-11-24_run05_profile/profile.json`, which §5 calls superseded. The numbers come from `experiments/2026-11-25_run05_profile/`. Verify: compare the §1 row with §5 bullet 1.

- **MINOR**, `reports/run05/profile.md` vs `experiments/2026-11-25_run05_profile/stdout.log`: the committed profile.md is hand-edited and not the script output.
  - The busy-sample paragraph was rewritten after the run. It now says "these timings are not confounded by outside load" although the guard flagged busy_frac 0.435. CLAUDE.md's threshold for single runs is 0.05.
  - The supporting facts check out: outside cores were ≤ 0.36 in every sample. Every busy flag comes from the load-average criterion (load1 − our_load > 1.5) during the 24-thread phases (21:46:09–21:47:49, 21:48:24–21:48:54).
  - But "the excess load is ours" is an inference from the sampler's lagging own-load estimate, not a measurement.
  - **Fix:** state plainly that the run is "confounded under the guard's definition (busy_frac 0.435); outside CPU ≤ 0.36 cores, so attributed to our own threads", and either generate that text from the script or note that the md was edited.
  - **Also:** `git_hash.txt` (a832677) differs from `load_info.txt` (8c40b8e, the HEAD at start). `git diff a832677 8c40b8e` touches no profile code, so this is harmless, but it should be consistent.

- **MINOR**, `reports/run05/profile.md` and `scripts/profile_rankers.py` (residual from phase1_1):
  - Batch-1 timing cycles over only the first 50 of the 200 sampled states (`b1 = [...] for x in items[:50]`). The md doesn't say so.
  - No per-model CPU peak memory is reported. `cpu_maxrss_MB_process` is cumulative over the process, so it isn't per model, and it isn't in the table. The Phase 1 brief asks for "peak memory", and only GPU peak is given.
  - **Fix:** say "50 distinct states", and either report CPU memory per model or state that it isn't measured.

- **MINOR**, `reports/run05/REPORT.md` §6 ("the minimum-epoch rule only delays stopping, as registered") vs `reports/campaign/DECISIONS.md` #9:
  - DECISIONS #9 treats "never stop before epoch 10" as a *reading* of an ambiguous PREREG phrase. The REPORT calls it "as registered".
  - #9 also omits the alternative ("never select a checkpoint before epoch 10") that the phase1_1 fix asked for.
  - **Fix:** cite DECISIONS #9 in §6 as a reading choice, and add the alternative there.

- **MINOR**, `reports/run05/REPORT.md` §3 (Tail-aware vs plain, PN vs plain) and the selection-bias note: the optimism isn't uniform across trained variants.
  - GNN-Surv-Tail chose from 16 configs (48 grid runs), the other own variants from 8 and ASAP-retrained from 6. More candidates on the same noisy val cost mean more winner's-curse optimism.
  - So the val contrast "GNN-Surv / Tail = 1.121" is biased toward Tail. This is relevant to Phase 2 decisions about which variants enter the test.
  - **Fix:** add one sentence. Verify: `training.md` grid sizes.

- **MINOR**, `experiments/2026-11-24_run05_eval_val_dev/cmd.txt` and `git_hash.txt`, and `experiments/2026-11-24_run05_dev_smoke/`: these are still untracked (`git status --short`), although DECISIONS #6/#7 cite them. **Fix:** commit their small provenance files.

- **MINOR**, run folder names `experiments/2026-11-25_run05_eval_val_cpu/` and `experiments/2026-11-25_run05_profile/`: the names are dated 11-25, but both runs executed on 2026-11-24 local time (`load_info.txt`: 21:35–21:37 and 21:43–21:48 −08:00). CLAUDE.md names folders `<YYYY-MM-DD>_<name>`. Cosmetic, but someone tracing a report could be misled. **Fix:** leave the folders as they are (never rename/delete under experiments/ is safer), but note the UTC date convention once in DECISIONS.

No BLOCKER or MAJOR findings: every number I checked traces to a saved output and reproduces bit-for-bit, test discipline holds, and both phase1_1 MAJORs are resolved.

VERDICT: PASS
