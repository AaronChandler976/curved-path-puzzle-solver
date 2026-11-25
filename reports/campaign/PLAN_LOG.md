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
