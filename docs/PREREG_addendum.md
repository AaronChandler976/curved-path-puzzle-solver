# Pre-registration addendum for the final test (run 05 / campaign)

This file extends `docs/PREREG_run05.md`. It never changes a registered comparison, metric or the §7 decision rule.
Part A was committed on 2026-11-24 at 18:49, before any v2 val or test number existed and before the registered
training began. (Three 3-epoch pipeline smoke models had been trained at 18:42–18:43 on a dev split made of 300 *train*
assemblies only, `experiments/2026-11-24_run05_dev_smoke/`; they produced no v2 val/test number and are not used.) Part B (which
exploratory variants enter the test) is added in campaign Phase 2, before the freeze.

## A. Disclosure: 41 test assemblies were seen during run 04 T6 development (added after the Phase 0 audit)

**What happened.** Run 04 T6 (data pool, penetration allowance) labelled two development samples with oracle v2:
`data/labels/pilot_v2_costpilot` (110 assemblies, labelling-cost estimate) and `data/labels/pilot_v2_allowance_check`
(50 recovered assemblies, used to validate and revise the per-pair allowance rule, run 04 DECISIONS #18–#19). The v2
split builder (T8) did not exclude them. **41 of the 347 test assemblies** are in one of these samples, 26 of them in
the allowance check. List: `experiments/2026-11-24_run04_t8_split/t6_test_overlap.json` (`union`; the 306 others are
`clean_test`), made by `experiments/2026-11-24_run04_t8_split/make_t6_overlap.py` (re-run gives an identical file).
Wording note: `docs/PREREG_run05.md` §0 says the test set is fresh assemblies "never in pilot_v1". Precisely, no test
assembly has a pilot_v1 query label; 171 have a pilot_v1 `skipped` summary line (they were excluded from v1 for
interpenetration). Found by the Phase 0 independent audit (`reports/campaign/AUDITS/phase0_1.md`).

**What was and was not chosen on them.** No model, ordering, feature or hyperparameter was chosen on them. They
informed two oracle settings that apply to every method equally: the allowance caps and rule, and the labelling
budget plan. Their T6 labels are not part of `pilot_v2` (relabelled from scratch in T7, DECISIONS #20). Any bias
therefore affects the oracle's behaviour on those assemblies, not the comparison between orderings.

**Decision.** The frozen split is kept as is. Re-splitting after the split was committed would itself be a
data-dependent choice, and the overlap doesn't favour any ordering. *Alt:* drop the 41 from test; rebuild the split.

**Pre-registered sensitivity analysis (fixed now, before any result).** In Phase 3 the §7 decision rule (replay, main
configuration; and live, if run) is also evaluated on the **306 `clean_test` assemblies** with exactly the same
procedure: best heuristic chosen on val; ratio-of-totals bootstrap CI; Holm-adjusted Wilcoxon over the same family of
comparisons, recomputed on the 306; HL difference. The registered result remains the full 347-assembly test. The
report states both verdicts. If they differ, the report says so and attributes nothing to the method.

## B. Exploratory variants and policies that enter the test (post-registration, exploratory)

Written in campaign Phase 2 from val and train+val cross-validation only; no test label has been read
(`data/splits/.v2_test_evaluated` absent). Evidence: `reports/explore/REPORT.md`. Frozen checkpoints with sha256:
`configs/final_frozen.yaml`. Inclusion rule written before the full CV results: `reports/campaign/DECISIONS.md` #10.

**B.1 Exploratory model variants (all three enter the replay; nothing is dropped after seeing CV).** Each has the same
per-config budget, grid rule (8 configs; ListNet's λ ∈ {0.1, 1.0} gives 16, as for Tail) and 5 seeds (100–104) as the
registered variants.
| id | what | val-chosen config | 5-fold group CV pooled ratio vs fewest contacts | test replay | test live |
|---|---|---|---|---|---|
| GT-Surv | graph-transformer (TransformerConv, 4 heads, edge features) + survival head, p/c | h128, lr 3e-4, L2 | 0.848 | yes | yes (CV < GNN-Surv's 0.874) |
| GNN-Surv-ListNet | GINE + survival NLL + λ · ListNet top-1 term (cost-weighted successes), p/c | h128, lr 3e-4, L2, λ 1.0 | 0.832 | yes | yes (CV < 0.874) |
| GATv2-Surv | GATv2 (4 heads, edge features) + survival head, p/c | h64, lr 3e-4, L2 | 0.895 | yes | no (CV ≥ 0.874) |

**B.2 Exploratory budget policy (all orderings).** Two-pass policy: pass 1 queries in the method's order with a CMG-RRT
budget T' = 3 s; if no part succeeds, pass 2 queries again at T = 30 s with the same seeds. T' = 3 was the best of the
pre-listed {1, 3, 10} on val for most orderings, including fewest contacts. Replayed on test for every ordering
(`eval_v2.py --budget-policies 3`), compared with fewest contacts under the same policy. Live, at priority P4 only:
fewest contacts and GNN-Surv (val-best seed) under the policy. The replay truncates the logged total (pre-check +
CMG-RRT) at T'. The live run truncates CMG-RRT at T', and the pre-check always runs. The difference is the pre-check time
over T', which is rare (median pre-check 0.04 s).

**B.3 How they are reported.** One exploratory table per evaluation (replay; live), apart from the registered tables.
Uncorrected Wilcoxon p-values are marked as such, with ratio-of-totals bootstrap CIs and HL. No exploratory result can
change the §7 decision, which uses only GNN-Surv vs the val-chosen best heuristic (fewest contacts), main
configuration, Holm over the registered family of 11.

**B.4 Other fixed test-time settings.** Scoring on CPU (bit-reproducible, DECISIONS #9). §7 heuristic = fewest
contacts (chosen on val, DECISIONS #8). Live priority (the shrink order of `prompts/campaign.md` Phase 3, "replay > live with all methods at 1 seed
(val-chosen) > live with all 5 seeds", extended to the exploratory rows; PREREG §6 itself has no shrink order): P1 every method at its
val-best seed → P2 the remaining seeds of the registered trained variants → P3 exploratory live variants → P4 budget
policy. Any part not run is reported as a deviation.
