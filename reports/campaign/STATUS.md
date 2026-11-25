STATE: RUNNING
DEADLINE: 2026-12-13T08:00:00-08:00
CURRENT PHASE: 3 (final test). STEP: replay DONE once (marker 2026-11-24 23:08:45); live running.
BACKGROUND JOBS:
- live: scripts/run_final_live.sh -> experiments/2026-11-24_final_eval_live/ (stdout_P1..P4.log; launcher log
  /tmp/dbg_t8/live_launcher.log). Started 23:10 11-24. P1 3,817 runs (~9 h), then P2 (9,716), P3 (3,470), P4 (694).
DONE SO FAR:
- Phases 0–2 DONE and audited (AUDITS/phase0_2, phase1_2, phase2_2 PASS).
- Phase 3: reports/final_eval/replay.md (registered §7: does NOT beat fewest contacts, 1.055 [0.887, 1.257], Holm p 0.43),
  failure_analysis.md, REPORT.md draft (live pending).
- Phase 4 drafts: talk/main.tex, talk/speaker_notes.md (not compiled: no compiling while the timed live run is active).
NEXT ACTION: wait for live; then scripts/live_report_v2.py -> reports/final_eval/live.md; fill the REPORT live
  section; failure renders; Phase 3 audit. Only text work while live runs (no compile, training or GPU).
