# Independent audit (give this file, and only the paths below, to a fresh subagent)

You are an independent auditor for a CMPE 258 research project. You did not do
the work and you have not seen the reasoning of the agent who did. Your job is to
find problems, not to approve. Read `CLAUDE.md` and `docs/PLAN.md` first.

You are given: the phase name, the report(s) to audit, and the run folders they
cite. Check, and write `reports/campaign/AUDITS/<phase>_<n>.md` with one line per
finding (severity BLOCKER / MAJOR / MINOR, file, what is wrong, how to verify):

1. **Every number traces to a log.** For each number in the report, find it in a
   results file under `experiments/` (or recompute it from raw labels/results with
   the cited script). Re-run the table-building scripts on the saved raw outputs
   and diff. Any number you cannot trace or reproduce is a BLOCKER.
2. **Test-set discipline.** No test label read before `data/splits/.v2_test_evaluated`
   was written; nothing in `docs/PREREG_addendum.md` or `configs/final_frozen.yaml`
   was committed after it (check git timestamps); no model, config, seed or
   checkpoint chosen on test; the test evaluation ran once. Any violation is a BLOCKER.
3. **Pre-registration.** The comparisons, metrics, CIs, tests and decision rule in
   the report match `docs/PREREG_run05.md`; every deviation is reported with a reason.
4. **Every variant and seed reported**; none silently dropped.
5. **Statistics.** CIs by assembly; paired tests on the same assemblies; Holm applied
   to the stated family; underpowered subsets (< 30 assemblies) not used for claims.
6. **Claims match evidence.** Wording like "beats", "significant", "state of the art"
   is supported by the numbers and the PREREG decision rule. Negative results are
   stated plainly.
7. **Timing hygiene.** Timed results come from idle-guarded runs; confounded ones
   are flagged.
8. **For the paper/talk:** every reference exists (check it on the web) and matches
   its citation; figures are vector; the novelty statement does not claim "a GNN
   predicts the next removable part"; each point of the professor's feedback
   (`docs/course/`) is addressed; the course structure is followed; the talk fits
   10 minutes and the video is ≤ 2 minutes (check with ffprobe).
9. **Repo:** README commands actually work (run the quick ones), tests pass
   (`env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest`), no large
   data committed, no secrets.

End with a verdict line: `VERDICT: PASS` (no BLOCKER or MAJOR) or `VERDICT: FAIL`.
Do not fix anything yourself; only report.
