STATE: RUNNING
DEADLINE: 2026-11-22T07:00:00-08:00
CURRENT STAGE: S4 pilot labelling (run2); S6 done
BACKGROUND JOBS:
870706 label_abd.py run2 (10 workers; stop: kill -TERM 870706, then kill its leftover children via pgrep -P) experiments/2026-11-22_pilot_labels/stdout.log
DONE SO FAR:
- S0 PASS: reports/environment.md
- S1 PASS (3/34 successes): reports/smoke_test.md, experiments/2026-11-22_smoke_sweep/
- S2 PASS: reports/data_sources.md (4196 assemblies load)
- contact/penetration scan: experiments/2026-11-22_contact_scan/results.jsonl (1104/2446 kept at max_pen<=0.002)
- S3 PASS: experiments/2026-11-22_oracle_check_v2/results.jsonl (9/22 successes in 4 assemblies); figure reports/figures/s3_path_00026_part0.png; tests 3 passed experiments/2026-11-22_pytest_oracle/stdout.log
- S4 PASS (run1 00:19-01:17, 385 queries, 40+ complete): experiments/2026-11-22_pilot_labels/stdout_run1_6workers.log; labels data/labels/pilot_v0/
- S5 early replay works: experiments/2026-11-22_replay_v0_early/replay.md
- S6 PIPELINE TEST done: reports/s6_pipeline_test.md, experiments/2026-11-22_s6_pipeline_test/ (1511-query snapshot)
NEXT ACTION: wait; labeller stops itself at 06:05 (--stop-at). At 06:10 start S7: confirm labeller exited (kill leftovers), rerun replay (planner-only and --with-prep) into reports/replay_pilot_v0*.md via experiments/2026-11-22_replay_v0_final/, write MORNING_REPORT.md, STATE: DONE, commit, push.
