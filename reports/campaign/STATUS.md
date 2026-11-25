STATE: RUNNING
DEADLINE: 2026-12-13T08:00:00-08:00
CURRENT PHASE: 1 (run 05 training, val only). STEP: training 6 variants; ASAP-retrained after redmax.
BACKGROUND JOBS:
- training: experiments/2026-11-24_run05_train/ (pids.txt; stdout_<variant>.log), started 18:54 11-24
- redmax ASAP contact graphs: experiments/2026-11-24_run05_redmax/ (3 chunks; asap_graphs_{0,1,2}.jsonl)
DONE SO FAR:
- Phase 0 DONE: audits reports/campaign/AUDITS/phase0_1.md (FAIL, 1 MAJOR fixed) and phase0_2.md (PASS; MINORs fixed).
  Run 04 REPORT/STATUS DONE (T9 deferred to Phase 5). PREREG §8 filled; PREREG_addendum §A (41 T6-seen test asm).
- Phase 1 prep: train/val graphs + clouds (experiments/2026-11-24_run05_dataset/).
- Paper skeleton + verified refs (paper/).
NEXT ACTION: launch asap_retrained when redmax is done (cat chunks -> asap_graphs.jsonl); when all training is done:
  eval_v2.py --split val; profile_rankers.py alone; reports/run05/REPORT.md; Phase 1 audit.
