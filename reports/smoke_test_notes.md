## Notes (hand-written, from the table above)

**Gate S1: PASS.** 3 logged successes: general/11356 cpu (257 it, 60.5 s), general/11356 cuda (716 it, 288.3 s),
puzzle/key_light_1 cpu (256 it, 133.8 s). Logs: `experiments/2026-11-22_smoke_sweep/general_11356_{cpu,cuda}.log`,
`experiments/2026-11-22_smoke_sweep/puzzle_key_light_1_cpu.log`. The first elk run (cpu, 500 iterations) was unsolved in 330 s:
`experiments/2026-11-21_smoke_elk_cpu500/results.jsonl`.

**Upstream reports 100% success on these examples. We got 3/34 in 10 minutes. Plausible reasons (not yet separated):**
1. Our obstacle SDF is much cheaper than upstream's (2M samples × 30 epochs vs 10M × 100; DECISIONS #3). A higher-fidelity SDF for
   general/06397 (10M × 40 epochs, winding-number sign; near-surface p95 error 0.0018 vs 0.0062) raised the start clearance from
   -0.0027 to -0.0004, but the run was **still unsolved in 600 s** (572 iterations):
   `experiments/2026-11-22_smoke_hifi_sdf/results.jsonl`. So SDF quality alone did not explain the failure within 10 min.
2. The 10-minute cap. Upstream does not state a wall-time cap we could check; the paper's timings were not verified tonight.
3. Several starts are already below the threshold according to our SDF (09301 cpu -0.0054 / cuda -0.0088, mobius_light -0.022),
   so those runs could not move. mobius_light and 09301-cuda hit 5000 iterations quickly with no progress.

**CPU vs GPU.** For the first 4 general runs (00:00–00:10, before labelling started), s/iteration was similar (cpu 0.17–0.39, cuda
0.17–0.47). After 00:19, the pilot labeller trained SDFs on the same GPU, and most cuda runs slowed to 1.2–5.8 s/iteration (exceptions: mobius_light and 09301-cuda, whose start was invalid; they iterate fast without making progress). **This
comparison is confounded by load.** It does not show that the GPU is slower; it shows that a shared GPU is a bottleneck. All
runs went 4 at a time, and for about 10 min around 00:00 the S3 oracle check also ran (load average up to 88 before thread pinning).

**Per-query time distribution.** Solved runs took 60–288 s; 31/34 runs hit the 600 s cap (or the 5000-iteration cap).
Bundled examples are deliberately hard rotational puzzles. On real ATA multi-part sub-assemblies (S3/S4), successful
queries mostly took 1 iteration and about 1 s (see the morning report). The cost distribution is extremely bimodal:
about 1 s or the full budget.

**Through our adapter**, general/11356 succeeds in 1 iteration (0.67 s) via a +y translation goal (`tests/test_oracle_bundled.py`,
`experiments/2026-11-22_pytest_oracle/stdout.log`). Upstream's goal (2, 2, 2) needed 257 iterations. Goal choice matters a lot.
