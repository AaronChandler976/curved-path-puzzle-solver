STATE: RUNNING
DEADLINE: 2026-12-13T08:00:00-08:00
CURRENT PHASE: 0 (finish run 04); STEP: T7 labelling still running (run 04's own job)
BACKGROUND JOBS:
- PID 1620794: run 04 T7 label_abd -> data/labels/pilot_v2; log experiments/2026-11-24_run04_label_v2/stdout.log
  (at 14:05 on 11-24: 904/2022 assemblies done; all 694 fresh done; v1 relabel remains, est. ~3-4 h)
DONE SO FAR:
- Session 1 start 2026-11-24 14:05: read CLAUDE.md, PLAN.md, PREREG_run05.md, run04 STATUS/prompt.
- docs/course/ created from the campaign appendix.
- Phase 1 code written (untested until T7 frees the CPU): scripts/build_dataset_v2.py, train_v2.py, train_asap_v2.py,
  eval_v2.py (test-marker guard), profile_rankers.py, src/disasm/eval/stats.py, tests/test_stats.py; live_abd.py run05 methods.
- Paper: paper/main.tex skeleton (method drafted), paper/refs.bib + paper/refs_check.md (11 refs verified on the web).
NEXT ACTION: when PID 1620794 exits: scripts/labels_v2_report.py -> reports/run04/labels_v2.md (T7 gate),
  T8 build_split_v2.py + test_split_v2 + PREREG §8, run04 REPORT.md (T9 deferred to Phase 5), audit Phase 0.
