# Audit phase2_1 (Phase 2: exploration on val + freeze)

Auditor: independent subagent, instructions = `prompts/audit.md` only, plus the phase name and file/run paths.
Date 2026-11-24 (local, ~22:58–23:15 PST). HEAD at audit start: 29985df.
Audited: `reports/explore/{REPORT,cv,val_all}.md`, `docs/PREREG_addendum.md` (A, B), `configs/final_frozen.yaml`,
`configs/final_methods.json`, `reports/campaign/DECISIONS.md` (#10), the run folders `experiments/2026-11-24_run06_explore_orderings/`,
`..._run06_explore_train/`, `..._run06_cv/`, `..._run06_eval_val_all/`, `..._run05_train/`.
Auditor reproduction folder: `experiments/2026-11-24_audit_phase2_1_repro/` (cmd.txt, git_hash.txt, eval_val_all/, val_all.md,
eval_val_all.stdout.log, pytest_subset.log). No planner job and nothing that reads v2 test labels was run.

## Checks that passed (evidence)
- **Test-set discipline / freeze independence from test.** `data/splits/.v2_test_evaluated` does not exist; no
  `data/processed/run05/graphs_test.pt` / `clouds_test.pt` exist. `train_v2.py` (l.224) and `cv_v2.py` (l.75) assert
  graphs are train/val only; `cv_v2.folds` restricts to train+val; `explore_orderings.py` (l.90) keeps `split == "val"`.
  The addendum, `final_frozen.yaml` and `final_methods.json` were last changed in a4eff4a (22:56:03); no later commit
  touches them. Every choice in them traces to val or train+val CV: val-chosen configs (selection.json, match the B.1
  table), `val_best_seed` = argmin `best_val_cost` in each variant's `selection.json` (recomputed, all 10 match),
  best heuristic = fewest contacts (val, DECISIONS #8), T' = 3 (val, `orderings.md`), live inclusion (CV pooled ratio vs
  GNN-Surv's 0.874). The {1, 3, 10} T' list and the ordering keys were committed in 5b89b3e (19:29) before any
  exploration result (21:57). The only test-dependent content is `data.labels_sha256` (a file fingerprint of
  `labels.jsonl`, which contains test rows); it carries no information used in any decision (see MINOR 5).
- **sha256 of all 50 frozen checkpoints** (35 registered + 15 exploratory) recomputed: 50/50 match. Also match: labels,
  split, redmax, clean_test, ASAP zero-shot checkpoint. `final_methods.json` lists exactly the same 50 paths, and equals
  `experiments/2026-11-24_run06_eval_val_all/methods.json` (the val evaluation used the frozen checkpoints).
- **Numbers trace.** `scripts/cv_report.py` re-run on `experiments/2026-11-24_run06_cv/*/cv_results.json` gives a file
  byte-identical to `reports/explore/cv.md`. `scripts/eval_v2.py --split val` re-run at HEAD (CPU, 4 procs) gives a md
  identical to `reports/explore/val_all.md` after normalising the output path. Every number in `REPORT.md` §1–§2
  (2,275 → 757; 1,835 → 638; 0.844 [0.666, 1.010]; GT 1,633; GATv2 2,070; ListNet 1,581; Tail 1,637; CV ratios; "±4%"
  (max 1.039); fold-2 losses for all but PN; per-seed spread 0.022–0.051) is found in `val_all.md`, `orderings.md` or `cv.md`.
- **Equal budget.** Exploratory variants: grid seeds 0,1,2, smooth 5, min 10 epochs, patience 25, ≤ 150 epochs,
  8 configs (ListNet 16 with λ ∈ {0.1, 1.0}, like Tail), 5 final seeds 100–104 — identical to the registered variants.
- **Every variant/seed reported** in val_all.md (10 trained × 5 seeds) and cv.md (9 trained × 5 folds × 5 seeds), with
  the one exception in MINOR 2. All three exploratory variants enter the test replay regardless of CV (DECISIONS #10).
- **Registered comparison unchanged.** Addendum B.3 keeps the §7 rule and the Holm family of 11; exploratory results
  get separate tables with uncorrected p-values marked. Live seed prefix `run05-live` matches PREREG §6. The frozen
  replay command relies on eval_v2's default `--sensitivity experiments/2026-11-24_run04_t8_split/t6_test_overlap.json`,
  so the addendum §A clean-test analysis will run.
- Pytest subset (no oracle tests, since a dev live planner job was running): 15 passed
  (`experiments/2026-11-24_audit_phase2_1_repro/pytest_subset.log`).

## Findings
| # | severity | file | what is wrong | how to verify |
|---|---|---|---|---|
| 1 | MAJOR | `reports/explore/REPORT.md` §2 | Claim wording the evidence does not support (campaign rule: no "beats" unless logged numbers *and* the pre-registered rule support it). "GNN beats MLP (0.874 vs 0.939; BCE 0.928 vs 0.975)", "Survival beats BCE", "PointNet features help (0.788)" and "All learned rankers beat fewest contacts on pooled held-out totals" are based on CV point estimates with no CI or paired test. The same section says the per-seed spread (0.02–0.05) is as large as the gaps, and fold 2 is a loss for 8 of 9 variants. "All learned rankers" is also false as worded: ASAP-retrained (a learned ranker) was not in the CV, and on val it costs 3,145 s vs fewest contacts' 2,275 s. Reword as descriptive ("lower pooled CV ratio"), add the noise caveat to each line or give a fold/assembly-level CI, and limit "all" to the 9 CV'd variants. | `reports/explore/cv.md` (no CI column; per-seed std column); `reports/explore/val_all.md` ASAP-retrained row; grep "beat" in REPORT.md |
| 2 | MINOR | `reports/explore/cv.md`, `REPORT.md` §1 | The registered variant ASAP-retrained is missing from the 5-fold CV, and neither file says so or why. (The CV is a robustness check of "final candidates", so leaving it out may be fine, but the omission should be stated.) | `ls experiments/2026-11-24_run06_cv/` (no asap_retrained); cv.md table has 9 trained rows |
| 3 | MINOR | `reports/campaign/DECISIONS.md` #10 | The disclosure "Seen by then: one fold × one seed per exploratory variant" understates what was on disk and committed when the rule was committed (8e773a1, 22:43:30). Its parent commit 176434f already holds fold-0 results for GT s100–s102 (0.717, 0.722, 0.707), GATv2 s100–s101 (0.797, 0.919) and ListNet s100–s101 (0.850, 0.648). 8e773a1 itself commits GT s103 and ListNet s102. All of it is train+val CV, which Phase 2 may legitimately use, so this does not affect test independence. The provenance statement should still be exact. | `git show 176434f:experiments/2026-11-24_run06_cv/gt_survival/cv_log.txt` (and gatv2_survival, gnn_survival_listnet); `git show 8e773a1 --stat` |
| 4 | MINOR | `docs/PREREG_addendum.md` B.4 | "Live priority (§6 shrink order, …)": PREREG_run05 §6 has no shrink order. The order comes from `prompts/campaign.md` Phase 3 ("replay > live with all methods at 1 seed (val-chosen) > live with all 5 seeds"). P1–P4 are consistent with that source, but the citation is wrong. Also, P1–P2 cover all of PREREG §6; any P2 shortfall is a registered deviation, which B.4 already says. | `grep -n shrink docs/PREREG_run05.md prompts/campaign.md` |
| 5 | MINOR | `configs/final_frozen.yaml` `data` | `states_sha256` has no path. It matches `data/labels/pilot_v2/states.jsonl`. `labels_sha256` fingerprints a file that includes test labels. That is an integrity hash, not a data-dependent choice, but a one-line comment would make the "nothing depends on test data" property explicit. | `sha256sum data/labels/pilot_v2/states.jsonl` = 33ba9d6e… |
| 6 | MINOR | `experiments/2026-11-24_run06_explore_train/`, `..._run06_eval_val_all/` | Provenance gaps. (a) The per-variant `cmd.txt` / `git_hash.txt` of the three exploratory trainings are untracked (`git status`). (b) The folder-level `git_hash.txt` (b6d5ee8) differs from the per-variant ones (4cc5cd7). (c) The val evaluation ran from a dirty tree (`load_info.txt`: git 4a91e09, dirty; eval_v2.py changed in 176434f). Impact is nil for (c): the auditor's re-run at HEAD reproduces `val_all.md` exactly. | `git status --short experiments/2026-11-24_run06_explore_train`; `cat experiments/2026-11-24_run06_eval_val_all/load_info.txt` |
| 7 | MINOR | `src/disasm/models/tail_loss.py::listnet_term` | The exploratory ListNet loss (used by a test-bound variant) has no unit test. The registered tail term has one. A hand-computed check on a small batch (target q ∝ y/(t+ε), per-state softmax CE) would cover it. | `grep -n listnet tests/*.py` (no hits) |

No BLOCKER. One MAJOR (wording of claims in the exploration report; it does not affect the frozen files or their
independence from test data).

VERDICT: FAIL
