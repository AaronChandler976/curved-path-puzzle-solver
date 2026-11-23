# R2: clean CMG-RRT reproduction on the bundled examples

Runs: `scripts/repro_cmgrrt.py` via `scripts/run_r2.sh` (then `diag/run_diag2.sh`). Settings: `test_list.json` (eta 0.002, threshold −0.005, steps 50, 5000 iterations, sampling 4000 or the properties.json override, N 12 / H 64, cuda), learned SDF trained with train.py defaults (DECISIONS #1). **One planner run at a time, nothing else running** (load info at start/end of every run in the listed file). Seed 0. Paper reference: `reports/run02/cmgrrt_reference.md`. The paper does not name its 16 instances, so "paper" below is the table-level claim (100% within 4 h, AST 3.0 min, 16 cores, grid SDF).

| example | SDF mesh | seed | success | stop | iterations | planner wall s | start SDF (learned) | exact start vs 0.obj | log / load-info | paper |
|---|---|---|---|---|---|---|---|---|---|---|
| puzzle/elk | 0_sdf.obj | 0 | **no** | iterations | 5000 | 982 | +0.0218 | +0.0480 | `experiments/2026-11-22_cmgrrt_repro_clean/puzzle_elk_s0.log`, `experiments/2026-11-22_cmgrrt_repro_clean/load_info.txt` | Elk: 100%, mean 156 min (16 cores, 4 h cap) |
| general/11356 | 0_sdf.obj | 0 | **no** | iterations | 5000 | 56 | -0.0496 | +0.0027 | `experiments/2026-11-22_cmgrrt_repro_clean/general_11356_s0.log`, `experiments/2026-11-22_cmgrrt_repro_clean/load_info.txt` | 100% / 4 h (table-level) |
| puzzle/key_light_1 | 0_sdf.obj | 0 | **no** | iterations | 5000 | 112 | -0.0640 | +0.0012 | `experiments/2026-11-22_cmgrrt_repro_clean/puzzle_key_light_1_s0.log`, `experiments/2026-11-22_cmgrrt_repro_clean/load_info.txt` | 100% / 4 h (table-level) |
| general/06397 | 0_sdf.obj | 0 | **no** | wall_cap | 4601 | 1200 | +0.0004 | -0.0003 | `experiments/2026-11-22_cmgrrt_repro_clean/general_06397_s0.log`, `experiments/2026-11-22_cmgrrt_repro_clean/load_info.txt` | 100% / 4 h (table-level) |
| general/07631 | 0_sdf.obj | 0 | **no** | iterations | 5000 | 921 | -0.0011 | -0.0003 | `experiments/2026-11-22_cmgrrt_repro_clean/general_07631_s0.log`, `experiments/2026-11-22_cmgrrt_repro_clean/load_info.txt` | 100% / 4 h (table-level) |
| general/08862 | 0_sdf.obj | 0 | **no** | iterations | 5000 | 52 | -0.0375 | -0.0000 | `experiments/2026-11-22_cmgrrt_repro_clean/general_08862_s0.log`, `experiments/2026-11-22_cmgrrt_repro_clean/load_info.txt` | 100% / 4 h (table-level) |
| general/09301 | 0_sdf.obj | 0 | **no** | iterations | 5000 | 218 | -0.0729 | -0.0000 | `experiments/2026-11-22_cmgrrt_repro_clean/general_09301_s0.log`, `experiments/2026-11-22_cmgrrt_repro_clean/load_info.txt` | 100% / 4 h (table-level) |
| general/11019 | 0_sdf.obj | 0 | **no** | iterations | 5000 | 137 | -0.0132 | +0.0115 | `experiments/2026-11-22_cmgrrt_repro_clean/general_11019_s0.log`, `experiments/2026-11-22_cmgrrt_repro_clean/load_info.txt` | 100% / 4 h (table-level) |
| general/11780 | 0_sdf.obj | 0 | **no** | iterations | 5000 | 67 | -0.0415 | +0.0020 | `experiments/2026-11-22_cmgrrt_repro_clean/general_11780_s0.log`, `experiments/2026-11-22_cmgrrt_repro_clean/load_info.txt` | 100% / 4 h (table-level) |
| general/16505 | 0_sdf.obj | 0 | **yes** | solved | 2880 | 646 | +0.0059 | +0.0030 | `experiments/2026-11-22_cmgrrt_repro_clean/general_16505_s0.log`, `experiments/2026-11-22_cmgrrt_repro_clean/load_info.txt` | 100% / 4 h (table-level) |
| puzzle/mobius_light | 0_sdf.obj | 0 | **yes** | solved | 395 | 79 | -0.0042 | +0.0023 | `experiments/2026-11-22_cmgrrt_repro_clean/puzzle_mobius_light_s0.log`, `experiments/2026-11-22_cmgrrt_repro_clean/load_info.txt` | 100% / 4 h (table-level) |
| puzzle/abc_light | 0_sdf.obj | 0 | **no** | iterations | 5000 | 948 | +0.0246 | +0.0209 | `experiments/2026-11-22_cmgrrt_repro_clean/puzzle_abc_light_s0.log`, `experiments/2026-11-22_cmgrrt_repro_clean/load_info.txt` | 100% / 4 h (table-level) |
| puzzle/alpha | 0_sdf.obj | 0 | **yes** | solved | 4523 | 884 | +0.0164 | +0.0145 | `experiments/2026-11-22_cmgrrt_repro_clean/puzzle_alpha_s0.log`, `experiments/2026-11-22_cmgrrt_repro_clean/load_info.txt` | 100% / 4 h (table-level) |
| general/11356 | 0.obj | 0 | **yes** | solved | 792 | 91 | +0.0036 | +0.0027 | `experiments/2026-11-22_cmgrrt_repro_clean/diag/general_11356_s0.log`, `experiments/2026-11-22_cmgrrt_repro_clean/diag/load_info.txt` | 100% / 4 h (table-level) |
| puzzle/key_light_1 | 0.obj | 0 | **no** | iterations | 5000 | 1038 | +0.0021 | +0.0012 | `experiments/2026-11-22_cmgrrt_repro_clean/diag/puzzle_key_light_1_s0.log`, `experiments/2026-11-22_cmgrrt_repro_clean/diag/load_info.txt` | 100% / 4 h (table-level) |

Not run (R2 timebox): puzzle/az, puzzle/aj, puzzle/doublealpha, puzzle/duet-g1 (`experiments/2026-11-22_cmgrrt_repro_clean/skipped.jsonl`).

## Outcome
- **Solved: 3/13 runs with the `0_sdf.obj` SDF (16505, mobius_light, alpha) + 11356 after the mesh fix; 4 distinct examples.
  Elk not solved:** it stopped at test_list's 5000-iteration limit after 982 s (16 min). The paper's Elk mean is 156 min with
  16-core parallel exploration and a 4 h timeout, so the public script's settings give Elk about 1/10 of the paper's mean single-run time
  and 1/16 of its cores. **Gate R2: FAIL (elk unsolved); discrepancy documented below (blocker #1).**
- **Diagnosis (3 attempts allowed, 2 used + 1 static):**
  1. *Invocation vs test_all.py* (static): identical loop, settings and iteration limit; only differences are the constructor
     signatures (test_all.py's are stale and cannot run) and per-example sampling override (DECISIONS #3). The paper's
     Algorithm 1 adds random rotations every N_rot iterations and runs 16 exploration cores; neither exists in test_all.py.
  2. *Sampling overrides:* only elk overrides (10,000) and it was applied (log line `sampling 10000`).
  3. *SDF / device:* cuda, N 12, H 64 as specified. Elk's SDF converged (valid L1 0.00105, −3% over the last 10 epochs,
     near-surface sign agreement 97.1%; `data/processed/cmgrrt_bundled_sdf/upstream_defaults/puzzle_elk/0_sdf.pth.json`), and its
     start is valid (+0.022). **But the SDF mesh mattered elsewhere:** `0_sdf.obj` differs from `0.obj` near the start for 9/17
     examples (`diag/start_exact_0obj_vs_0sdfobj.json`), so 6 general examples started in collision (my DECISIONS #2, corrected in
     #11). Diagnostic run: 11356 with an SDF of `0.obj` → **solved** in 792 iterations / 91 s; key_light_1 → valid start, still
     unsolved at 5000 iterations.
- **Exact discrepancy (blocker #1):** with the repo's public settings (single process, 5000 iterations, no random rotation,
  neural SDF), elk is not solved in 16 min; the paper reports 156 min mean on 16 cores with a 4 h cap and a grid SDF. A fair
  test needs ≥ 4 h single-process runs (or the authors' parallel code, which is not in the repo).

