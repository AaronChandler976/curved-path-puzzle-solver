STATE: RUNNING
DEADLINE: 2026-12-13T08:00:00-08:00
CURRENT PHASE: 2 -> 3. Freeze committed (a4eff4a + audit fixes a13b397). Audit phase2_1 FAIL (1 MAJOR wording) -> fixed;
  re-audit phase2_2 running.
BACKGROUND JOBS: Phase 2 re-auditor (subagent)
DONE SO FAR:
- Phase 0 DONE, Phase 1 DONE (reports/run05/REPORT.md; audits phase1_1 FAIL→fixed, phase1_2 PASS).
- Phase 2: reports/explore/REPORT.md (orderings, budget policy, GATv2/GT/ListNet, 5-fold group CV);
  docs/PREREG_addendum.md (A, B), configs/final_frozen.yaml (50 checkpoint sha256), configs/final_methods.json.
- Phase 3 prep: eval_v2.py (test marker, CPU, sensitivity, budget policy), scripts/run_final_live.sh (P1..P4),
  live_abd.py @b policy (dev smoke experiments/2026-11-24_run06_dev_live/, train assemblies, not reported).
NEXT ACTION: when phase2_2 PASSES: Phase 3 = (1) replay on test ONCE:
  eval_v2.py --split test (command in configs/final_frozen.yaml) -> reports/final_eval/replay.md;
  (2) scripts/run_final_live.sh experiments/<date>_final_eval_live (P1..P4, ~30-57 h);
  (3) live report + failure analysis; audit.
