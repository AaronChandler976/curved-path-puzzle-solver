# Pre-registration addendum for the final test (run 05 / campaign)

This file extends `docs/PREREG_run05.md`. It never changes a registered comparison, metric or the §7 decision rule.
Part A was committed on 2026-11-24, before any v2 model was trained and before any v2 val number existed. Part B (which
exploratory variants enter the test) is added in campaign Phase 2, before the freeze.

## A. Disclosure: 41 test assemblies were seen during run 04 T6 development (added after the Phase 0 audit)

**What happened.** Run 04 T6 (data pool, penetration allowance) labelled two development samples with oracle v2:
`data/labels/pilot_v2_costpilot` (110 assemblies, labelling-cost estimate) and `data/labels/pilot_v2_allowance_check`
(50 recovered assemblies, used to validate and revise the per-pair allowance rule, run 04 DECISIONS #18–#19). The v2
split builder (T8) did not exclude them. **41 of the 347 test assemblies** are in one of these samples, 26 of them in
the allowance check. List: `experiments/2026-11-24_run04_t8_split/t6_test_overlap.json` (`union`; the 306 others are
`clean_test`). Found by the Phase 0 independent audit (`reports/campaign/AUDITS/phase0_1.md`).

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
