STATE: RUNNING
DEADLINE: 2026-11-24T08:00:00-08:00
CURRENT STAGE: R1 Rotation-required labels
BACKGROUND JOBS: none
DONE SO FAR:
- R0 orient (08:40-08:55): read CLAUDE.md, docs/PLAN.md, reports/run02/{REPORT,DECISIONS}.md, v1 label schema
  (data/labels/pilot_v1/{labels,states,summary}.jsonl: 17,116 queries / 4,685 states / 1,328 labelled asm),
  run-02 code (oracle/cmgrrt.py, exact_sdf.py, data/graph.py, models/nets.py, scripts/train_pipeline_test.py, replay_pilot.py).
- Machine load at 08:41: load avg 0.32, GPU 10% / 2196 MiB, power profile performance, no planner/python jobs running.
NEXT ACTION: write src/disasm/oracle/linear_precheck.py + scripts/run_precheck.py; run on all v1 queries with slots.
