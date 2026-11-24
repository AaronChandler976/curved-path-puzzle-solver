STATE: RUNNING
DEADLINE: 2026-11-25T08:00:00-08:00
CURRENT STAGE: T7 labelling pilot_v2 (timed, started 05:47 on 11-24; ~11-12 h planned)
BACKGROUND JOBS: T7 label_abd PID 1620794 -> data/labels/pilot_v2, run folder experiments/2026-11-24_run04_label_v2/ (launch_cmd.txt; resumable: rerun the same command)
MACHINE (T0, 2026-11-23T16:09-08:00): uptime 19:57, load 0.11/0.22/0.23; GPU 11% / 1534 MiB; power profile performance.
  Heavy processes: none from the project. Desktop apps running (firefox, chrome, Discord, gnome-shell), each < 6% CPU.
DONE SO FAR:
- T0 orient: read run03 REPORT/DECISIONS/rotation/results_live, run02 REPORT, PLAN run-04 section.
- T1 PASS: idle guard src/disasm/util/idle_guard.py (+CLI), seeded robot sampling (cmgrrt.seeded_surface_sampling),
  wired into scripts/label_abd.py and scripts/live_abd.py (busy_frac, confounded, re-runs). pytest 19 passed:
  experiments/2026-11-23_run04_pytest_t1/stdout.log. Dev runs: experiments/2026-11-23_run04_dev_label{,_rerun}/, experiments/2026-11-23_run04_dev_live/.
- T2 PASS: redmax built (env asap; DECISIONS #9), ASAP graph = adapter on 20/20 (experiments/2026-11-23_run04_t2_redmax/agreement.json);
  ASAP retrain 2-epoch dry run + PointNet fwd/bwd (experiments/2026-11-23_run04_t2_dryruns/). DECISIONS #9-#12.
- T3 PASS: reports/run04/live_rerun.md, experiments/2026-11-23_run04_live_rerun/ (238/240 runs clean first try, 1 fixed by re-run,
  1 still confounded: 08111/fewest_contacts busy_frac 0.015; aborted attempt 1 kept in ..._live_rerun_aborted1, DECISIONS #13).
  GNN-Surv/fewest contacts ratio of totals 0.595 [0.455, 0.821] (run 03 confounded: 0.613).
- T4 PASS: reports/run04/oracle_v2.md. Cause = start pose never tested against goals (123/124 root-free); v2a solves 123/124,
  0 invalid successes on recheck (experiments/2026-11-23_run04_oracle_validation/summary.json); v1 paths 18.5% invalid at fine res.
- T6 PASS: reports/run04/data_pool.md (694 fresh candidates; allowance validated 906/906; plan = label all, ≈11.3 h).
- T5 PASS: reports/run04/sdf_puzzles.md (16505: exact 0/3, learned 3/3 but all 3 learned paths penetrate; alpha 0/3 both;
  hybrid not triggered, DECISIONS #23).
NEXT ACTION: wait for T7; then scripts/labels_v2_report.py; T8 split (scripts/build_split_v2.py) + PREREG sizes; T9 elk 4 h.
