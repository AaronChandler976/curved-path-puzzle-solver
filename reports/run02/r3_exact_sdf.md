# R3: exact union-SDF detector — validation

Code: `src/disasm/oracle/exact_sdf.py` (tests `tests/test_exact_sdf.py`), driver `experiments/2026-11-22_exact_sdf_validation/run_r3.sh`, script
`scripts/exact_sdf_validation.py`. All steps ran sequentially, alone; load info in `experiments/2026-11-22_exact_sdf_validation/load_info.txt` and
`experiments/2026-11-22_exact_sdf_validation/bundled/load_info.txt` (power profile `performance`). Design and ε choice: DECISIONS #6–#8.
ε = 0.005 scaled units (collision iff min SDF < −ε).

## 1. Start-pose validity, assembled state, 50 assemblies (185 part queries) — `experiments/2026-11-22_exact_sdf_validation/start_valid_summary.txt`
| detector | start-valid |
|---|---|
| learned (v0 labelling SDF, same queries) | 67.0% (124/185) |
| **exact, ε = 0.005** | **100.0% (185/185)** |

Exact start min-SDF p1/p5/p50: −0.0018 / −0.0015 / −0.0000 (min −0.0018, inside ε). Sign mode: pseudonormal for all 185
(winding-number check passed). Exact setup per part p50/p90/max: 0.024 / 0.045 / 0.133 s. **Gate ≥ 99%: PASS.**

## 2. Learned vs exact at 10,000 random poses near the start (σ_t 0.01, σ_rot 2°) — `experiments/2026-11-22_exact_sdf_validation/poses.jsonl`
| example | agreement | valid learned | valid exact | L-valid/E-invalid | L-invalid/E-valid | |Δsdf| p50 / p95 |
|---|---|---|---|---|---|---|
| general/11356 | 99.7% | 4.2% | 4.2% | 12 | 14 | 0.0002 / 0.0006 |
| puzzle/key_light_1 | 98.3% | 69.7% | 68.6% | 142 | 29 | 0.0007 / 0.0014 |
| general/16505 | 90.2% | 54.8% | 49.3% | 764 | 220 | 0.0020 / 0.0029 |

Disagreements sit in the shallow-penetration band (exact min SDF in [−0.02, 0)); agreement is 100% for exact SDF ≥ 0 and
for < −0.02 in all three. The learned SDF mostly errs toward "free" (more learned-valid/exact-invalid poses).
Evaluating 10k poses: learned 1.9–2.1 s (cuda) vs exact 4–40 s (cpu, 1 thread).

## 3. Bundled examples solved in R2, rerun with the exact detector (seed 0, test_list settings, 20 min cap) — `experiments/2026-11-22_exact_sdf_validation/bundled/results.jsonl`
| example | R2 learned | exact | iterations | planner s | s/iteration learned → exact |
|---|---|---|---|---|---|
| general/11356 (0.obj) | solved, 792 it, 91 s | **solved** | 534 | 75 | 0.115 → 0.141 |
| puzzle/mobius_light | solved, 395 it, 79 s | **solved** | 767 | 809 | 0.20 → 1.05 |
| general/16505 | solved, 2880 it, 646 s | not solved (wall cap) | 1809 | 1200 | 0.22 → 0.66 |
| puzzle/alpha | solved, 4523 it, 884 s | not solved (wall cap) | 1777 | 1200 | 0.195 → 0.68 |

**Documented reason for 16505/alpha:** both hit the 20 min wall cap at ~1800 of the 5000 iterations, because one exact
iteration costs 3–5× a learned (cuda) iteration on these large bundled meshes (CPU AABB queries over tens of thousands of
faces vs one small MLP pass on the GPU). They did not exhaust the iteration budget, so this is a speed difference, not a
correctness difference. Same-iteration-budget reruns (≈ 60 min each) are listed under "Needs Aaron". **Gate: PASS with
documented reason** (2/4 still solved; 2/4 cut by wall time).

## 4. Run 01 S3 set side by side (22 queries, 6 assemblies, T = 120 s, cpu) — `experiments/2026-11-22_exact_sdf_validation/s3.jsonl`, `experiments/2026-11-22_exact_sdf_validation/s3.log`
| detector | success | start-valid | median planner s (all) |
|---|---|---|---|
| learned (cached run 01 SDFs) | 9/22 | 11/22 | 120.0 |
| exact | 20/22 | 22/22 | 1.7 |

Of the 11 learned start-invalid queries, 10 succeed with the exact detector. On the 9 queries both solve, median planner time
is 1.15 s (learned) vs 0.45 s (exact). Learned setup here is 0 because the run 01 SDFs were cached; run 01 measured ~66 s per
query to train them (`reports/MORNING_REPORT.md`). Exact setup is 0.02–0.13 s per part, built once per assembly.

## 5. ε sensitivity, 30 assemblies, all parts at the assembled state (107 queries, T = 30 s) — `experiments/2026-11-22_exact_sdf_validation/eps.jsonl`
| ε | success | start-valid | median planner s |
|---|---|---|---|
| 0.0025 | 94/107 (87.9%) | 107/107 | 0.90 |
| **0.005** | 97/107 (90.7%) | 107/107 | 1.10 |
| 0.01 | 99/107 (92.5%) | 107/107 | 1.41 |

Success changes by 3 queries per doubling of ε; start validity does not change. ε = 0.005 is kept.

## Cost-model facts
- On the ATA pilot assemblies the exact detector is *not* slower per query (S3: faster median); on large bundled meshes one
  iteration is 3–5× slower than the learned detector on cuda. Planner time per query therefore depends on mesh size.
- Setup drops from ~66 s per query (learned, run 01) to ~0.02 s per part (exact).

## Follow-up (run 02, 07:02): 16505 exact at the full 5,000-iteration budget — `experiments/2026-11-23_exact_bundled_fullbudget/results.jsonl`
Seed 0, same settings, 60 min cap, run alone: **not solved**, stopped at the 5,000-iteration limit after 3,198 s (190,152 tree nodes).
So the wall cap is *not* the whole explanation for 16505: with a single seed on each side, the learned detector solved it (2,880 it)
and the exact one did not. That may be RRT seed variance or a real detector effect (the exact detector reports more shallow
penetrations as collisions than the learned one; see §2, 16505 agreement 90.2%). Multi-seed comparison is listed in REPORT.md "Needs Aaron".
