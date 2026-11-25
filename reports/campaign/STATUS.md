STATE: RUNNING
DEADLINE: 2026-12-13T08:00:00-08:00
CURRENT PHASE: 0 → 1. Phase 0 work done; Phase 0 audit running (reports/campaign/AUDITS/phase0_1.md when done).
BACKGROUND JOBS:
- Phase 0 auditor (subagent), output reports/campaign/AUDITS/phase0_1.md
- redmax ASAP contact graphs, PIDs in experiments/2026-11-24_run05_redmax/pids.txt (3 chunks) -> asap_graphs.jsonl
DONE SO FAR:
- Phase 0: run 04 T7 PASS (reports/run04/labels_v2.md), T8 PASS (data/splits/v2_split.json, PREREG §8), REPORT
  (reports/run04/REPORT.md), run04 STATUS DONE (T9 elk deferred to Phase 5). docs/course/ created.
- Contact-sampling bug found and fixed (DECISIONS #3), cache frozen by manifest.
- Phase 1 prep: train/val graphs + clouds (experiments/2026-11-24_run05_dataset/), trainers smoke-tested on a
  train-only dev split (experiments/2026-11-24_run05_dev_smoke/), launch script scripts/run05_train_all.sh.
- Paper skeleton + 11 verified refs (paper/).
NEXT ACTION: when the audit passes and redmax finishes: scripts/run05_train_all.sh experiments/<date>_run05_train
  experiments/2026-11-24_run05_redmax/asap_graphs.jsonl; then eval_v2.py --split val; profiling (alone).
