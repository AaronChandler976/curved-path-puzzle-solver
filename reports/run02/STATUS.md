STATE: RUNNING
DEADLINE: 2026-11-23T08:00:00-08:00
CURRENT STAGE: R2 Clean CMG-RRT reproduction (box ends 23:20; R0 review + R3 code written meanwhile, no heavy runs)
BACKGROUND JOBS:
13074 R2 driver scripts/run_r2.sh (SDF training, then planner runs one at a time) experiments/2026-11-22_cmgrrt_repro_clean/driver.log
DONE SO FAR:
- R1 PASS: slots + runlog + 6 tests pass: experiments/2026-11-22_run02_pytest_r1/stdout.log (commit 444da35)
- paper facts collected (arXiv 2607.17898): grid SDF 240^3, 10k samples, 4h timeout, 16 cores, elk avg 156 min
NEXT ACTION: while R2 runs: write reports/run02/cmgrrt_reference.md, run01_review.md, DECISIONS.md; write src/disasm/oracle/exact_sdf.py (do NOT run heavy jobs until driver.log says "R2 DRIVER DONE")
