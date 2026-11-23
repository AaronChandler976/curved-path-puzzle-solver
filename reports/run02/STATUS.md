STATE: RUNNING
DEADLINE: 2026-11-23T08:00:00-08:00
CURRENT STAGE: R7 drafting; 16505 exact rerun in background
BACKGROUND JOBS:
667337 16505 exact full-budget rerun (cap 60 min, alone) experiments/2026-11-23_exact_bundled_fullbudget/stdout.log
DONE SO FAR:
- R0 done: reports/run02/run01_review.md (no code bugs; limitations noted)
- R1 PASS: experiments/2026-11-22_run02_pytest_r1/stdout.log (6 tests incl. slot test)
- R2 done, gate FAIL (elk unsolved, discrepancy documented): reports/run02/smoke_clean.md, reports/run02/cmgrrt_reference.md
- R3 done, gates PASS: reports/run02/r3_exact_sdf.md, experiments/2026-11-22_exact_sdf_validation/
- R4 DONE 04:18 (list exhausted): 1328 labeled (1249 complete, 79 stuck), 1118 skipped; data/labels/pilot_v1/, experiments/2026-11-22_pilot_v1_labels/stdout.log; exit-cleanup bug fixed (DECISIONS #14)
- R5 final: reports/run02/analysis_v1.md, replay_pilot_v1*.md (1328 asm, 17116 q), experiments/2026-11-23_analysis_v1_final/
- R6 PIPELINE TEST done: experiments/2026-11-23_s6_pipeline_test_v1/pipeline_test.md
- pytest 9 passed: experiments/2026-11-23_run02_pytest_final/stdout.log
NEXT ACTION: wait for 16505 rerun (ends <= 07:12), add its row to REPORT.md + r3_exact_sdf.md, set STATE DONE, commit, push.
