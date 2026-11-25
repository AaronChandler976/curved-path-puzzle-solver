# Audit phase2_2 (Phase 2: exploration on val + freeze), re-audit

Auditor: independent subagent. Instructions: `prompts/audit.md` only, plus the phase name, the file and run paths, and
the previous audit `reports/campaign/AUDITS/phase2_1.md`.
Date: 2026-11-24 (local). HEAD at audit start: f3df2c3 (fixes in a13b397).
Audited: `reports/explore/{REPORT,cv,val_all}.md`, `docs/PREREG_addendum.md`, `configs/final_frozen.yaml`,
`configs/final_methods.json`, `reports/campaign/DECISIONS.md` #10 and #11, and the run folders
`experiments/2026-11-24_run06_{explore_orderings,explore_train,cv,eval_val_all}/` and `experiments/2026-11-24_run05_train/`.
Auditor reproduction folder: `experiments/2026-11-24_audit_phase2_2_repro/` (cmd.txt, git_hash.txt, cv.md,
chk_frozen.{py,log}, chk_seed.{py,log}, chk_listnet.{py,log}, pytest.log). I ran no planner job and nothing that reads
v2 test labels. (I briefly wrote `chk_frozen.py` to `/tmp` by mistake and then moved it into the repro folder. Nothing
else outside the project was touched.)

## Status of the phase2_1 findings
| # | phase2_1 severity | status | evidence |
|---|---|---|---|
| 1 | MAJOR (claim wording in REPORT §2) | **Resolved** | §2 is now titled "point estimates; no CI or test was computed on the CV". It says the numbers "support no 'beats' or 'significant' claim". Contrasts are given as plain numbers with the seed SD (0.02–0.05). "All learned rankers" is now limited to "Every CV'd learned ranker", and ASAP-retrained is named as the exception (3,145 vs 2,275 s, which matches `val_all.md` l.26 and `orderings.md`). A grep for beat/significan/state of the art/outperform over the audited reports finds only the disclaimer sentence. The claim that the CV saves only per-fold totals is true: `scripts/cv_v2.py` l.113–118 stores `total` per fold × seed, with no per-assembly data. |
| 2 | MINOR (ASAP-retrained missing from CV) | **Resolved** (in REPORT §2 and DECISIONS #11; `cv.md` itself is generated and still lists 9 rows without comment, which is acceptable). The justification contains a new imprecise number; see finding 1 below. | `reports/explore/REPORT.md` §2 last bullet |
| 3 | MINOR (DECISIONS #10 provenance) | **Resolved** | #10 now says "2–4 seeds of fold 0 per variant were already on disk". At 8e773a1 the logs show GT s100–s103 (4), ListNet s100–s102 (3) and GATv2 s100–s101 (2), all train+val. |
| 4 | MINOR (addendum B.4 citation) | **Resolved** | B.4 now cites `prompts/campaign.md` Phase 3. The quoted text matches `prompts/campaign.md` l.114. |
| 5 | MINOR (yaml states path / integrity comment) | **Resolved** | `data.states` added, plus a comment that the label hashes are integrity hashes. `sha256` of `data/labels/pilot_v2/states.jsonl` matches. |
| 6 | MINOR (provenance) | **Resolved / disclosed** | Per-variant cmd/git_hash files are committed in a13b397 (`git status` is clean for `run06_explore_train`). b6d5ee8 → 4cc5cd7: 19 s apart, and the diff touches only `reports/campaign/{PLAN_LOG,STATUS}.md`, which I verified with `git diff --stat`. The dirty-tree val evaluation is disclosed in #11. |
| 7 | MINOR (no ListNet unit test) | **Resolved** | `tests/test_tail_loss.py::test_listnet_term_prefers_cheap_successes` added. It is qualitative (gradient signs), so I also checked `listnet_term` against a hand computation with non-zero scores: 0.229746 vs 0.229746 (`chk_listnet.log`). |

## Checks that passed this round (evidence)
- **Freeze files do not depend on test data.** `data/splits/.v2_test_evaluated` is absent (only `.v1_test_evaluated`
  exists). `data/processed/run05/` holds only `*_train_val*`, `*_val*` and `dev_train_only.pt`, with no test graphs or clouds.
  After the "FREEZE" commit a4eff4a, the addendum and `final_frozen.yaml` changed once, in a13b397 (23:04:31). I read
  that diff line by line. It contains (a) the B.4 citation wording and (b) the yaml `states` path and a comment. It
  changes no checkpoint, seed, config, heuristic, T', live list or priority. `final_methods.json` has not changed
  since a4eff4a, and it is byte-identical to `experiments/2026-11-24_run06_eval_val_all/methods.json`. Every choice
  in the frozen files still traces to val or to train+val CV:
  - `val_best_seed` equals the argmin of `best_val_cost` in each variant's `selection.json`, 10/10 (`chk_seed.log`).
  - The best heuristic is fewest contacts (val).
  - T' = 3 is best or tied-best of {1, 3, 10} on val for every ordering (`orderings.md`; MLP-Surv ties 609 = 609).
  - The live inclusion rule uses the CV pooled ratio below 0.874 (GT 0.848, ListNet 0.832, GATv2 0.895 excluded,
    consistent with `cv.md`).
  - The only test-touching content is the integrity hashes of files that also hold test rows, which the yaml now states.
- **All 56 sha256 entries in `final_frozen.yaml` recomputed: 56/56 match.** These are 50 checkpoints, the ASAP
  zero-shot checkpoint, labels, states, split, redmax and clean_test (`chk_frozen.log`).
- **Numbers reproduce.** I re-ran `scripts/cv_report.py` on `experiments/2026-11-24_run06_cv/`, and the output is
  byte-identical to `reports/explore/cv.md`. The new or changed numbers in REPORT §2 are in `cv.md`: 0.891 / 0.874,
  0.939 / 0.975 / 0.928, 0.788, 0.788–0.975, PN fold 2 0.953, the other variants' fold 2 between 1.002 and 1.303, and
  per-seed SD 0.022–0.051. The figure 1,675 train+val assemblies equals 1,425 + 250 in `v2_split.json`. The phase2_1
  re-run of `val_all.md` is still valid: `eval_v2.py`, the methods file and the checkpoints are unchanged.
- **Pre-registration:** addendum B.3 still keeps the §7 rule and the Holm family of 11 unchanged. Exploratory rows are
  kept separate.
- **Tests:** the full suite passes, 36 passed (`pytest.log`).

## Findings
| # | severity | file | what is wrong | how to verify |
|---|---|---|---|---|
| 1 | MINOR | `reports/explore/REPORT.md` §2 (and DECISIONS #11 "~4 h") | The reason given for leaving ASAP-retrained out of the CV says "about 9 minutes per run, 25 runs would have taken about 4 h". 9 min is the **maximum** logged ASAP run: 561 s, the first grid run. The logged ASAP runs average 310 s (range 160–561 s), and the five final seeds took 160–317 s. Each CV fold also trains on fewer states (4,071 vs 5,762). A sequential estimate from the logs is therefore about 2 h or less, not 4 h. This is a justification, not a result, but every number should trace to a log. Restate it as "up to 9 min (mean ≈ 5 min) per run" and correct the total, or drop the total. | `grep -oE "\([0-9]+ epochs, [0-9]+ s\)" experiments/2026-11-24_run05_train/stdout_asap_retrained.log`; fold sizes in `experiments/2026-11-24_run06_cv/*/cv_log.txt` |
| 2 | MINOR | `configs/final_frozen.yaml` `frozen_at`, `docs/PREREG_addendum.md` | The freeze now spans two commits: a4eff4a ("FREEZE") and a13b397 (wording/provenance edits made after the audit). Both are before any test read, and the a13b397 diff changes no frozen decision, so test independence holds. `frozen_at` says only "see git log of this file", though. The Phase 3 report should name **a13b397 (or whatever is the last commit to these files before `.v2_test_evaluated` is written)** as the freeze commit, and check that nothing later touches them. | `git log --format='%h %ci' -- docs/PREREG_addendum.md configs/final_frozen.yaml` |
| 3 | MINOR | `scripts/run_final_live.sh` (Phase 3 artifact that implements yaml `live.priority`) | The yaml P3 says "gt_survival and gnn_survival_listnet …, val-best seed, then remaining seeds". The script puts all 10 exploratory checkpoints into one `methods_P3.txt` in seed order 100–104, so the val-best seed (102 for both) is not run first. This only matters if P3 is cut short. If so, the run would not follow the frozen priority, and which seeds got run would be arbitrary. Either order or split P3 as the yaml says, or record the difference as a deviation. | `sed -n '/for grp in/,/P\[4\]/p' scripts/run_final_live.sh`; yaml `live.priority[2]` |

No BLOCKER. No MAJOR. The phase2_1 MAJOR is resolved, and all six phase2_1 MINORs are resolved or disclosed. Nothing
in `docs/PREREG_addendum.md`, `configs/final_frozen.yaml` or `configs/final_methods.json` depends on test data.

VERDICT: PASS
