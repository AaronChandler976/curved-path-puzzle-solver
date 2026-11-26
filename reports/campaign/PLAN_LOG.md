# Campaign plan log

- 2026-11-24 14:05 Session 1 starts. Phase 0: T7 labelling running since 05:47 (904/2022 done).
  Plan: finish T7 (~18:00), T8 the same evening, audit, Phase 1 training starts tonight.
- 2026-11-24 16:13 T7 at 1678/2022 (slower than the 14:05 estimate; busy_wait 2001 s so far from desktop use). Expected end ~17:30 + re-runs.
- 2026-11-24 18:14 T7 main pass done (2022/2022, 41,913 queries; 2,128 = 5.1% confounded before re-runs). Re-run round 1 at 1,717/2,128, 10 still confounded.
- 2026-11-24 18:54 Phase 0 audit PASS (2nd round). Phase 1 training started (6 variants); ASAP-retrained waits for redmax.
- 2026-11-24 19:05 Phase 2 draft plan (val only, written before any Phase 1 val result was read):
  (1) ordering keys from the same survival checkpoints: p/c (registered), p/(c + κ(1−p)T) risk-averse,
      expected-cost greedy with censoring, quantile cost; no retraining.
  (2) budget/restart policy replayed from logged times: first pass at a truncated budget T' < T, then full T for the
      rest. Exact for seeded queries up to wall-clock jitter; labelled as replay-derived.
  (3) encoders: GATv2 and a graph transformer (TransformerConv) with the survival head, same grid and budget rule, 5 seeds.
  (4) a listwise loss (ListNet-style over successes, cost-weighted), same grid, 5 seeds.
  (5) 5-fold group CV over train+val for the final candidates (robustness of the val ranking).
  (6) optional EV-battery CAD case study only if a public model downloads without a login.
- 2026-11-24 20:04 conda env paper (tectonic 0.17.0, ffmpeg 9.1) ready; paper skeleton compiles.
- 2026-11-24 21:35 Phase 1 work done (training 18:54–21:17, val eval, profile). Phase 1 audit started.
- 2026-11-24 21:50 (corrected from git commit times; was mis-typed 22:00) Phase 1 audit 1 FAIL (2 MAJOR) -> fixed (CPU eval bit-reproducible, bias caveats, CV inner early stopping, profile re-run). Re-audit started.
- 2026-11-24 21:55 (corrected; was mis-typed 22:15) Phase 1 re-audit PASS. Phase 2 started: gatv2_survival, gt_survival, gnn_survival_listnet training; ordering explorer.
- 2026-11-24 22:42 exploratory trainings done (gatv2, gt, listnet); CV launched for them.
- 2026-11-24 23:13 Phase 3: replay done once (marker 23:08:45). Live launched (experiments/2026-11-24_final_eval_live, P1 3,817 runs); idle guard waiting: Firefox media decoding (RDD process) keeps outside load ≈0.5 cores.
- 2026-11-25 00:10 live P1 at 251/3,817 runs after 35 min (~7/min → P1 ≈ 9 h, all P ≈ 41 h + re-runs). 23% confounded: outside desktop apps ≈0.55 cores, just over 0.5 (NEEDS_AARON).
- 2026-11-25 02:11 live P1 919/3,817 (5.1 runs/min; 57 confounded, 0 errors). Projection: P1 ~11:30 today; all P ~Fri 11-27.
- 2026-11-25 07:47 live P1 DONE (29,331 s wall); P2 started (9,716 runs ≈ 22 h at 7.4/min).
- 2026-11-25 11:48 live P2 1,098/9,716 (slowed to ~3/min on heavier assemblies; no busy samples). Projection: P2 ends 11-26 noon to 11-27 noon; P3+P4 by ~11-28. Phase 3 limit 11-30 12:00 holds.
- 2026-11-25 17:49 live P2 3,881/9,716 (~7/min; 20 confounded, 0 errors).
- 2026-11-26 09:45 Phase 3 live complete (09:29); live.md, figures, demo; Phase 3 audit started.
- 2026-11-26 10:03 Phase 3 DONE (audits phase3_1 FAIL, phase3_2 FAIL, phase3_3 PASS). Phase 4 starts.
- 2026-11-26 10:14 Phase 4 DONE (phase4_1 FAIL→fixed, phase4_2 PASS). Phase 5: elk 4 h run started (experiments/2026-11-26_phase5_elk), alone; only text work meanwhile.
