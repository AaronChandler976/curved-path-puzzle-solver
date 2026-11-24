STATE: RUNNING
DEADLINE: 2026-11-25T08:00:00-08:00
CURRENT STAGE: T3 live rerun (timed, running); writing T4 code meanwhile (no execution)
BACKGROUND JOBS: T3 live_abd PID 842377 (experiments/2026-11-23_run04_live_rerun/, relaunched 16:50 after aborted attempt 1 (DECISIONS #13), log stdout.log)
MACHINE (T0, 2026-11-23T16:09-08:00): uptime 19:57, load 0.11/0.22/0.23; GPU 11% / 1534 MiB; power profile performance.
  Heavy processes: none from the project. Desktop apps running (firefox, chrome, Discord, gnome-shell), each < 6% CPU.
DONE SO FAR:
- T0 orient: read run03 REPORT/DECISIONS/rotation/results_live, run02 REPORT, PLAN run-04 section.
- T1 PASS: idle guard src/disasm/util/idle_guard.py (+CLI), seeded robot sampling (cmgrrt.seeded_surface_sampling),
  wired into scripts/label_abd.py and scripts/live_abd.py (busy_frac, confounded, re-runs). pytest 19 passed:
  experiments/2026-11-23_run04_pytest_t1/stdout.log. Dev runs: experiments/2026-11-23_run04_dev_label{,_rerun}/, experiments/2026-11-23_run04_dev_live/.
- T2 PASS: redmax built (env asap; DECISIONS #9), ASAP graph = adapter on 20/20 (experiments/2026-11-23_run04_t2_redmax/agreement.json);
  ASAP retrain 2-epoch dry run + PointNet fwd/bwd (experiments/2026-11-23_run04_t2_dryruns/). DECISIONS #9-#12.
NEXT ACTION: wait for T3; then write reports/run04/live_rerun.md; then T4.
