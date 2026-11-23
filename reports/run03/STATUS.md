STATE: RUNNING
DEADLINE: 2026-11-24T08:00:00-08:00
CURRENT STAGE: R6 Live evaluation (idle wait, then run)
BACKGROUND JOBS:
786658 scripts/run_r6.sh (idle wait + live_abd.py) experiments/2026-11-23_run03_live/stdout.log
DONE SO FAR:
- R0 orient: machine idle at 08:41 (load 0.32, GPU 10%, performance profile).
- R1 PASS: precheck on 17,116/17,116 queries (data/labels/pilot_v1/precheck.jsonl, log experiments/2026-11-23_run03_precheck/stdout.log);
  reports/run03/rotation.md: 513 parts / 405 states / 211 assemblies need rotation; 124 linear-free-but-unsolved inconsistencies.
- R2 PASS: data/processed/run03/graphs.pt (4,685 states); data/splits/v1_split.json committed; reports/run03/dataset.md;
  tests/test_split.py 2 passed (experiments/2026-11-23_run03_pytest_split/stdout.log). Test: 204 asm / 716 states / 65 rot_state.
- R3 protocol v1 (dev, val only): experiments/2026-11-23_run03_train/ (4 variants x 5 seeds); val-noise finding -> protocol v2 (DECISIONS #8).
- R3 PASS (protocol v2): experiments/2026-11-23_run03_train_v2/ (4 variants x 5 seeds 100-104), reports/run03/training.md.
- R4 PASS: ASAP released weights zero-shot, scores for all 4,685 states, 0 errors (experiments/2026-11-23_run03_asap/{scores.jsonl,meta.json}).
- R5 PASS (test evaluated once, 09:04): reports/run03/results_replay.md (+ results_replay_supp.md), experiments/2026-11-23_run03_eval_test/.
- R6 sample: experiments/2026-11-23_run03_live/assemblies.json (60 test asm, 20 rot); GNN-Surv ckpt seed 101 (val-chosen).
NEXT ACTION: R6 idle-wait in progress (attempts every 10 min up to 2 h; desktop GPU spikes > 10%). Wait for LIVE EXIT in experiments/2026-11-23_run03_live/stdout.log; then scripts/live_report.py; then R7 scripts/render_demo.py --aid <rot asm completed by gnn_surv>.
