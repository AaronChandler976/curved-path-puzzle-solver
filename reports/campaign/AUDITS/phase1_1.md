# Audit phase1_1 (Phase 1: run 05 training, val only)

Auditor: independent subagent, instructions = `prompts/audit.md` only. Date 2026-11-24.
Audited: `reports/run05/REPORT.md`, `training.md`, `val_replay.md`, `profile.md`, and the run folders they cite.
No planner job was run and no test label was read.
Audit scratch outputs (kept, not deleted): `experiments/2026-11-24_audit_phase1_1_repro/`
(`training.md` and `val_replay.md` re-generated from saved outputs, `eval_val/`, `asap_nondet_probe.py` + `.log`, `pytest.log`).

## What was checked and passed
- **Numbers trace / reproduce.**
  - `scripts/run05_training_report.py` re-run on `experiments/2026-11-24_run05_train/` gives a `training.md` byte-identical to `reports/run05/training.md`.
  - `scripts/eval_v2.py --split val` re-run with the exact `cmd.txt` arguments (into the scratch folder) gives identical numbers for every row except the ASAP rows (see MAJOR 2). That covers all heuristics, all 6 own variants, hindsight-optimal, all paired comparisons not involving ASAP, the §7 lines, subsets, ECE and C-index.
  - REPORT §5 trade-off arithmetic matches `profile.json` and `results.json`: 0.4356 s / 2.62 ms ≈ 166×, Tail 244×, PN 134×.
  - "51% of test is 9–12 parts" is (102+74)/347.
  - The claim that totals are tail-driven holds: for GNN-Surv the top 5% of states carry 79% of the val total.
  - redmax: 2,022 lines, 0 errors.
  - Dataset summary matches the REPORT (5,867/1,030 states; 5,762/1,010 with a success). 0 confounded queries in train/val.
- **Test discipline.**
  - `data/splits/.v2_test_evaluated` is absent.
  - `graphs_train_val.pt`, `clouds_train_val.pt`, `asap_inputs_train_val.pt` and `asap_inputs_val.pt` contain 0 test assemblies. Every graph's `split` field agrees with `v2_split.json`, and no duplicate group crosses splits.
  - `build_dataset_v2.py` skips lines from other splits without parsing them and refuses `test` without the marker.
  - `train_v2.py` and `train_asap_v2.py` assert that no test graphs are present.
  - Neither `configs/final_frozen.yaml` nor PREREG Part B exists yet. PREREG_run05 was last changed 18:40, the addendum 18:54, and training started 18:54:32.
  - DECISIONS #2 (Holm family, reading choices) was committed at 14:16, before training.
- **Pre-registration.**
  - Grid: 8 configs per variant (16 for Tail, 6 for ASAP), with AdamW, wd 1e-4, dropout 0.1, clip 1.0, batch 32 and ≤150 epochs.
  - Selection: 5-epoch trailing mean, patience 25, configs ranked by the mean over grid seeds 0–2, then retrained with seeds 100–104.
  - Ordering keys are p for BCE and p/c for survival. Normalisation uses train statistics only. Training uses states with ≥1 success.
  - Every `best.pt` in `methods.json` matches its `selection.json` (epoch, smoothed cost, chosen config).
  - Eval-only flags (`rot_state`, `needs_rot`, `pre_free`, `confounded`) are not model inputs.
  - Holm family of 11 recomputed by hand from the raw p values: matches.
  - Bootstrap is by assembly and paired. Wilcoxon is on per-assembly costs.
- **Every variant/seed.**
  - 7 variants × (grid runs + 5 final seeds) all have `result.json` and `best.pt` (grid 24/24/24/24/48/24/18).
  - The aborted tail launch, the dev smoke models and `eval_val_dev` are disclosed (DECISIONS #6, #7, addendum A).
- **Subsets.** <30-assembly subsets are labelled UNDERPOWERED, and the REPORT draws no conclusion from them.
- **Tests.** `env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest`: 35 passed (`experiments/2026-11-24_audit_phase1_1_repro/pytest.log`).
- **Repo.** No checkpoints or large data are committed. The largest tracked run05 file is `results.json` (96 KB).
- **Figures.** Vector PDFs exist for every PNG in `reports/run05/figures/`.
- **Code identity.** The tail variant's git hash 30825d8 differs from the "524e7b3" in `cmd.txt`, but the diff between them is docs only.

## Findings

- **MAJOR**, `reports/run05/REPORT.md` (one-line summary, §3, §4) and `reports/run05/val_replay.md`: the val comparisons are optimistically biased, and the report doesn't say so.
  - **Problem:** the val replay cost these comparisons report is the selection metric itself. It picked each variant's config and each seed's checkpoint epoch. The heuristic and ASAP-zero-shot baselines get no such selection.
  - The REPORT still gives val CIs and Holm p values ("Holm p 0.0034", "Both §7 conditions hold on val", "Survival p/c vs BCE p (GNN) … Holm p 0.0034") as if they were unselected.
  - The per-epoch val cost is very noisy. In `figures/train_curves_gnn_survival.png` the seeds swing between ~1,550 and ~2,700 s from one epoch to the next. That is larger than most between-variant gaps, so picking the best smoothed epoch is a winner's-curse selection.
  - **Fix:** state this bias plainly in REPORT §3/§4 and in `val_replay.md`, and treat val p values as descriptive only. The 5-fold CV planned for Phase 2 should also not pick epochs on the fold it reports.
  - **Verify:** compare the `scripts/train_v2.py` `val_cost` / `best.pt` logic with the `eval_v2.py` input (same val graphs, same replay cost).

- **MAJOR**, `reports/run05/val_replay.md`, REPORT §3/§4 (ASAP rows): ASAP numbers don't reproduce on re-run, because ASAP scoring on the GPU is non-deterministic.
  - **Problem:** re-running the identical `eval_v2.py --split val` command changed several ASAP-retrained numbers:

    | number | reported | re-run |
    |---|---|---|
    | main total | 3180 [2224, 4396], ±243 | 3179 [2217, 4404], ±246 |
    | GNN-Surv vs ASAP-retrained, main: HL / W-T-L / Holm p | −0.09 / 119-67-59 / 6.7e-05 | −0.10 / 119-68-58 / 4.3e-05 |
    | same, CMG-RRT-only: HL / Holm p | −0.72 / 0.0044 | −0.81 / 0.0027 |
    | rot_state total | 920 | 914 |
    | parts 9–10 total | 199 | 193 |
    | within-state C-index | 0.595 ± 0.009 | 0.595 ± 0.008 |
    | ASAP-zs Wilcoxon p | 2.1e-07 | 2.2e-07 |
    | ASAP-zs median-ratio CI | [1.78, 2.64] | [1.77, 2.64] |

  - 64 `asap_retrained` and 8 `asap_zs` per-state entries differ (`per_state.jsonl` diff). The six own variants reproduce bit-for-bit.
  - **Cause:** probe `experiments/2026-11-24_audit_phase1_1_repro/asap_nondet_probe.py`. On CUDA, 141 of 1,030 val states get different ASAP scores in two identical runs (max |Δ| 6e-8), which flips near-tie orders. On CPU, 0 differ.
  - **Impact:** the conclusions don't change. But the reported numbers can't be regenerated, and the test evaluation can run only once.
  - **Fix:** before the freeze, make ASAP scoring deterministic (score on CPU, or `torch.use_deterministic_algorithms(True)` plus a deterministic aggregation). Re-run val and update the ASAP rows. Record the fix in DECISIONS.
  - **Verify:** run the probe, then diff two `eval_v2.py --split val` outputs.

- **MINOR**, `reports/run05/val_replay.md` (§7 line for `cmgrrt_only`), REPORT one-line summary and §3: the CMG-RRT-only verdict on val says **beats** ("Both §7 conditions hold on val").
  - **Problem:** PREREG §7 defines the rule only for test replay in the main config (and for live). The secondary config on val is not a registered claim.
  - **Fix:** reword, e.g. "(a) and (b) hold — secondary config, val, not a registered claim", and avoid the word "beats" here.
  - **Verify:** `eval_v2.py` prints the verdict for every config.

- **MINOR**, `reports/run05/profile.md`, REPORT §5: several profile labels are wrong or unclear.
  - The "CPU batched" column is the **24-thread** batched time. The header doesn't say so.
  - "Batched" is a batch of **200** states, because only 200 are sampled. The `profile_rankers.py` docstring and REPORT §5 ("3.8 GB peak GPU memory at batch 256") say 256.
  - Batch-1 timing uses only the first 50 of the 200 states.
  - Batch-1 is a median over repeated single-state calls, while batched is total/n, so the two aren't comparable. This is visible where batched per-state CPU time is *higher* than batch-1: PN 3.65 vs 1.88 ms, ASAP 14.5 vs 7.06 ms (1 thread).
  - **Fix:** label the columns correctly and state the statistic for each.
  - **Verify:** `scripts/profile_rankers.py` lines building `b1`, `bb` and the table.

- **MINOR**, REPORT §5: two latency statements are inaccurate or incomplete.
  - "PointNet: its point-cloud encoder costs 1.9 ms per state on CPU". 1.88 ms is the full PN-GNN-Surv forward pass. The PointNet increment over GNN-Surv is ≈1.77 ms.
  - "Feature extraction 2.50 ms" leaves out three costs: point-cloud sampling (PN), the redmax contact graph (ASAP), and the per-assembly contact-graph computation (cached; fewest contacts also needs it).
  - **Fix:** state these so the "≈170×" trade-off is read correctly.
  - **Verify:** `profile.json`, and `scripts/profile_rankers.py` (feature timing calls `state_graph_v3` on cached contacts).

- **MINOR**, `experiments/2026-11-24_run05_profile/`: the timed profile logs no busy samples during the run.
  - The idle guard only ran before start. The 1-min load at the end is 6.70 (`load_info.txt`), probably from the run's own 24-thread benchmarks, but `profile.md` doesn't say so.
  - **Fix:** note it, or sample load during the run.
  - **Verify:** `guard/idle_samples.jsonl` covers only the wait period.

- **MINOR**, REPORT §6, `reports/campaign/DECISIONS.md`: the "minimum 10 epochs" reading isn't recorded.
  - **Problem:** the code lets the selected checkpoint be epoch 4, the first epoch with a 5-epoch mean. Because patience is 25, the "min 10 epochs" rule then has no effect. As a result, 18 of the 35 final checkpoints were taken before epoch 10.
  - The REPORT calls this "as registered", but the reading isn't recorded in DECISIONS #2 as a PREREG reading choice.
  - **Fix:** add it there with the alternative ("do not select before epoch 10").
  - **Verify:** `scripts/train_v2.py` `train_one` (stopping condition), `selection.json` `best_epoch`.

- **MINOR**, `scripts/eval_v2.py`, `val_replay.md`: the CIs for the median per-state ratio to optimal use **2,000** resamples (`min(a.boot, 2000)`), not the stated 10,000. DECISIONS #2 discloses this only for HL.
  - **Fix:** disclose it, or use 10,000.
  - **Verify:** `table()` in `eval_v2.py`.

- **MINOR**, `scripts/eval_v2.py`, `val_replay.md`: "states solved within T" for random (expectation) is computed as 1[expected cost ≤ 30 s]. That isn't the probability that a random order solves the state within T, so the 0.934 is not comparable to the other rows.
  - **Fix:** compute the exact probability, or footnote it.
  - **Verify:** the `solv` lines in `table()`.

- **MINOR**, `experiments/2026-11-24_run05_train/<variant>/cmd.txt` and `git_hash.txt` (7 variants + `gnn_survival_tail_aborted1`) and `experiments/2026-11-24_run05_eval_val_dev/cmd.txt` and `git_hash.txt`: these provenance files are untracked, so they aren't committed. Other runs' provenance files are tracked.
  - **Fix:** commit them.
  - **Verify:** `git status --short experiments/`.

- **MINOR**, `reports/run05/training.md` and figures: training.md doesn't discuss what the curves show.
  - Val loss rises from about epoch 4–5 in every final seed (overfitting). Per-epoch val cost is very noisy.
  - In the left (loss) panel of the curve figures, lines aren't colour-matched or legended to the seeds in the right panel.
  - **Fix:** add one sentence on the overfitting and noise, and match the colours.
  - **Verify:** `reports/run05/figures/train_curves_*.png`.

VERDICT: FAIL
