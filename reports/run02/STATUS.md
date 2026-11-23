STATE: RUNNING
DEADLINE: 2026-11-23T08:00:00-08:00
CURRENT STAGE: R4 relabel pilot_v1 (running; gate >=50 reached 01:00)
BACKGROUND JOBS:
475088 R4 labeler (python; conda wrapper 475075) (label_abd --detector exact, stop-at 06:15) log experiments/2026-11-22_pilot_v1_labels/stdout.log
DONE SO FAR:
- R0 done: reports/run02/run01_review.md (no code bugs; limitations noted)
- R1 PASS: experiments/2026-11-22_run02_pytest_r1/stdout.log (6 tests incl. slot test)
- R2 done, gate FAIL (elk unsolved, discrepancy documented): reports/run02/smoke_clean.md, reports/run02/cmgrrt_reference.md
- R3 done, gates PASS (start-valid 100% exact vs 67% learned; 2/4 bundled re-solved, 2 cut by wall cap = documented): reports/run02/r3_exact_sdf.md, experiments/2026-11-22_exact_sdf_validation/
- R4 launched 00:55 -> data/labels/pilot_v1/ (DECISIONS #13)
- R5 first pass done 01:0x: reports/run02/analysis_v1.md, replay_pilot_v1*.md (64 asm, 538 q), log experiments/2026-11-23_analysis_v1_pass1/stdout.log; replay median-ratio CI added
NEXT ACTION: let R4 run to its 06:15 stop-at (check stdout.log periodically); at 06:15-06:30 run R5 final pass with a new experiments/2026-11-23_analysis_v1_final folder (same cmd as pass1), add interpenetration-recheck counts from summary.jsonl skip reasons, then R7 REPORT.md by 07:15.
