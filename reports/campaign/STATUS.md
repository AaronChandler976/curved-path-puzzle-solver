STATE: RUNNING
DEADLINE: 2026-12-13T08:00:00-08:00
CURRENT PHASE: 1. Audit phase1_1 FAIL (2 MAJOR: val selection bias, GPU nondeterminism) -> fixed; re-audit phase1_2 running.
BACKGROUND JOBS:
- Phase 1 auditor (subagent)
DONE SO FAR:
- Phase 0 DONE (audits phase0_1 FAIL→fixed, phase0_2 PASS). Run 04 DONE (T9 elk deferred to Phase 5).
- Phase 1: 7 variants x 5 seeds trained (experiments/2026-11-24_run05_train/), val replay
  (reports/run05/val_replay.md), profile (reports/run05/profile.md), REPORT (reports/run05/REPORT.md).
  §7 best heuristic from val = fewest contacts (DECISIONS #8).
- Phase 2 code ready (not run): GATv2/GT encoders, ListNet variant, scripts/explore_orderings.py.
- Paper: skeleton compiles (tectonic, env paper); method, related work, data drafted; refs verified (paper/refs_check.md).
NEXT ACTION: fix audit findings; then Phase 2: explore_orderings.py on val; train gatv2_survival, gt_survival,
  gnn_survival_listnet (same grid, 5 seeds); 5-fold group CV over train+val for candidates; write
  docs/PREREG_addendum.md part B + configs/final_frozen.yaml; freeze audit.
