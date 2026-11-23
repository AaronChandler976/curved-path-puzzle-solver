STATE: RUNNING
DEADLINE: 2026-11-23T08:00:00-08:00
CURRENT STAGE: R2 Clean CMG-RRT reproduction (box ends 23:20)
BACKGROUND JOBS:
13079 R2 driver scripts/run_r2.sh (phase 1 SDF training, phase 2 planner runs one at a time) experiments/2026-11-22_cmgrrt_repro_clean/driver.log
DONE SO FAR:
- R0 done: reports/run02/run01_review.md (no code bugs; limitations noted)
- R1 PASS: experiments/2026-11-22_run02_pytest_r1/stdout.log (6 tests incl. slot test)
- R2 reference: reports/run02/cmgrrt_reference.md (paper arXiv 2607.17898)
- R3 code: src/disasm/oracle/exact_sdf.py + tests/test_exact_sdf.py (3 pass); scripts/exact_sdf_validation.py written (not yet run)
- R4 code: scripts/label_abd.py --detector exact --eps --order-file; order list experiments/2026-11-22_pilot_v1_labels/order_v0_first.txt (336 v0 ids)
- R5 code: scripts/analysis_v1.py (tested on scratch data only)
NEXT ACTION: wait for "R2 DRIVER DONE" in driver.log; write reports/run02/smoke_clean.md; then R3 validations (start_valid, poses, s3, eps, bundled exact reruns) one at a time
