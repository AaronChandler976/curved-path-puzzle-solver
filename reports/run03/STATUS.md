STATE: RUNNING
DEADLINE: 2026-11-24T08:00:00-08:00
CURRENT STAGE: R3 Models + training (protocol v2)
BACKGROUND JOBS:
783929 train mlp_bce v2 experiments/2026-11-23_run03_train_v2/stdout_mlp_bce.log
783930 train mlp_survival v2 experiments/2026-11-23_run03_train_v2/stdout_mlp_survival.log
783931 train gnn_bce v2 experiments/2026-11-23_run03_train_v2/stdout_gnn_bce.log
783932 train gnn_survival v2 experiments/2026-11-23_run03_train_v2/stdout_gnn_survival.log
DONE SO FAR:
- R0 orient: machine idle at 08:41 (load 0.32, GPU 10%, performance profile).
- R1 PASS: precheck on 17,116/17,116 queries (data/labels/pilot_v1/precheck.jsonl, log experiments/2026-11-23_run03_precheck/stdout.log);
  reports/run03/rotation.md: 513 parts / 405 states / 211 assemblies need rotation; 124 linear-free-but-unsolved inconsistencies.
- R2 PASS: data/processed/run03/graphs.pt (4,685 states); data/splits/v1_split.json committed; reports/run03/dataset.md;
  tests/test_split.py 2 passed (experiments/2026-11-23_run03_pytest_split/stdout.log). Test: 204 asm / 716 states / 65 rot_state.
- R3 protocol v1 (dev, val only): experiments/2026-11-23_run03_train/ (4 variants x 5 seeds); val-noise finding -> protocol v2 (DECISIONS #8).
- R4 PASS: ASAP released weights zero-shot, scores for all 4,685 states, 0 errors (experiments/2026-11-23_run03_asap/{scores.jsonl,meta.json}).
NEXT ACTION: when v2 training finishes, check selection.json for all 4 variants, write reports/run03/training.md, commit; then run R5
  scripts/eval_replay_test.py --train-dir experiments/2026-11-23_run03_train_v2 --seeds 100,101,102,103,104 (ONCE).
