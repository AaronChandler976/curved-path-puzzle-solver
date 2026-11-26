# CMG-RRT smoke test on bundled examples (S1)

Each row is one real run of `scripts/smoke_cmgrrt.py`: library CMG-RRT, unmodified example files, test_list.json parameters (eta 0.002, threshold -0.005, steps 50; sampling from properties.json, else 4000), our fast obstacle SDF (see DECISIONS #3). Cap: --iterations and --timeout (wall s). `start_sdf` = min SDF of the robot samples at q2_start; the start is valid when it is >= -0.005.

| example | device | outcome | iterations | planner wall s | s/iter | start_sdf | SDF (epochs, samples, sign) | log |
|---|---|---|---|---|---|---|---|---|
| general/06397 | cpu | **unsolved** | 1550 | 600.5 | 0.387 | -0.0046 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/general_06397_cpu.log` |
| general/06397 | cuda | **unsolved** | 1266 | 600.1 | 0.474 | -0.0027 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/general_06397_cuda.log` |
| general/06397 | cuda | **unsolved** | 572 | 600.7 | 1.050 | -0.0004 | 40, 10M, robust | `experiments/2026-11-22_smoke_hifi_sdf/stdout.log` |
| general/07631 | cpu | **unsolved** | 3528 | 601.3 | 0.170 | -0.0021 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/general_07631_cpu.log` |
| general/07631 | cuda | **unsolved** | 3581 | 600.0 | 0.168 | -0.0027 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/general_07631_cuda.log` |
| general/08862 | cpu | **unsolved** | 1535 | 600.4 | 0.391 | -0.0016 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/general_08862_cpu.log` |
| general/08862 | cuda | **unsolved** | 1923 | 600.3 | 0.312 | -0.0038 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/general_08862_cuda.log` |
| general/09301 | cpu | **unsolved** | 1971 | 600.0 | 0.304 | -0.0054 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/general_09301_cpu.log` |
| general/09301 | cuda | **unsolved** | 5000 | 193.5 | 0.039 | -0.0088 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/general_09301_cuda.log` |
| general/11019 | cpu | **unsolved** | 717 | 600.1 | 0.837 | +0.0066 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/general_11019_cpu.log` |
| general/11019 | cuda | **unsolved** | 509 | 606.6 | 1.192 | +0.0069 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/general_11019_cuda.log` |
| general/11356 | cpu | **success** | 257 | 60.5 | 0.235 | +0.0033 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/general_11356_cpu.log` |
| general/11356 | cuda | **success** | 716 | 288.3 | 0.403 | +0.0028 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/general_11356_cuda.log` |
| general/11780 | cpu | **unsolved** | 3129 | 600.2 | 0.192 | -0.0006 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/general_11780_cpu.log` |
| general/11780 | cuda | **unsolved** | 483 | 606.7 | 1.256 | -0.0002 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/general_11780_cuda.log` |
| general/16505 | cpu | **unsolved** | 1020 | 600.1 | 0.588 | +0.0024 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/general_16505_cpu.log` |
| general/16505 | cuda | **unsolved** | 104 | 600.6 | 5.775 | +0.0023 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/general_16505_cuda.log` |
| puzzle/abc_light | cpu | **unsolved** | 1276 | 600.0 | 0.470 | +0.0226 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_abc_light_cpu.log` |
| puzzle/abc_light | cuda | **unsolved** | 177 | 606.0 | 3.424 | +0.0212 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_abc_light_cuda.log` |
| puzzle/aj | cpu | **unsolved** | 1287 | 600.3 | 0.466 | +0.0100 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_aj_cpu.log` |
| puzzle/aj | cuda | **unsolved** | 219 | 606.5 | 2.769 | +0.0100 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_aj_cuda.log` |
| puzzle/alpha | cpu | **unsolved** | 1187 | 600.2 | 0.506 | +0.0114 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_alpha_cpu.log` |
| puzzle/alpha | cuda | **unsolved** | 169 | 611.3 | 3.617 | +0.0119 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_alpha_cuda.log` |
| puzzle/az | cpu | **unsolved** | 1350 | 600.2 | 0.445 | +0.0041 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_az_cpu.log` |
| puzzle/az | cuda | **unsolved** | 172 | 603.7 | 3.510 | +0.0054 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_az_cuda.log` |
| puzzle/doublealpha | cpu | **unsolved** | 1318 | 600.0 | 0.455 | +0.0416 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_doublealpha_cpu.log` |
| puzzle/doublealpha | cuda | **unsolved** | 233 | 603.2 | 2.589 | +0.0421 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_doublealpha_cuda.log` |
| puzzle/duet-g1 | cpu | **unsolved** | 1260 | 600.1 | 0.476 | +0.0271 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_duet-g1_cpu.log` |
| puzzle/duet-g1 | cuda | **unsolved** | 209 | 600.1 | 2.871 | +0.0312 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_duet-g1_cuda.log` |
| puzzle/elk | cpu | **unsolved** | 464 | 600.1 | 1.293 | +0.0470 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_elk_cpu.log` |
| puzzle/elk | cpu | **unsolved** | 500 | 330.2 | 0.660 | +0.0459 | 30, 2M, quicksdf | `experiments/2026-11-21_smoke_elk_cpu500/stdout.log` |
| puzzle/elk | cuda | **unsolved** | 305 | 610.8 | 2.002 | +0.0485 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_elk_cuda.log` |
| puzzle/key_light_1 | cpu | **success** | 256 | 133.8 | 0.523 | -0.0004 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_key_light_1_cpu.log` |
| puzzle/key_light_1 | cuda | **unsolved** | 375 | 604.5 | 1.612 | -0.0019 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_key_light_1_cuda.log` |
| puzzle/mobius_light | cpu | **unsolved** | 5000 | 161.4 | 0.032 | -0.0220 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_mobius_light_cpu.log` |
| puzzle/mobius_light | cuda | **unsolved** | 4181 | 601.4 | 0.144 | -0.0205 | 30, 2M, quicksdf | `experiments/2026-11-22_smoke_sweep/puzzle_mobius_light_cuda.log` |

**Successes: 3 / 36 runs.**
- cpu: s/iteration median 0.461 (min 0.032, max 1.293) over 18 runs
- cuda: s/iteration median 1.434 (min 0.039, max 5.775) over 18 runs
- success times (s): median 133.8, min 60.5, max 288.3

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

