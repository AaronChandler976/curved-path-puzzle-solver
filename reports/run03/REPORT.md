# Run 03 report: GNN vs baselines on pilot_v1 (2026-11-23)

**Answer so far:** the cost-aware GNN (GNN-Surv, ordered by p/c) wins on the typical test assembly but **does not significantly beat the best heuristic on total planner time in replay**.
- **Typical assembly:** it is cheaper than fewest contacts on 128 of 197 assemblies, with a median saving of 0.64 s per assembly [0.31, 1.12].
- **Replay total:** GNN-Surv / fewest contacts = 0.865 [0.685, 1.075].
- **Live full disassembly** (60 test assemblies, fresh CMG-RRT queries, timings confounded): it used **0.613× [0.475, 0.801]** of fewest contacts' planner time and 0.670× [0.477, 0.933] of ASAP's, over the 56 assemblies every method completed.
- **Other learned variants:** in replay, MLP-Surv and GNN-BCE had *lower* totals than GNN-Surv (not significant).

## Gates
| stage | gate | evidence |
|---|---|---|
| R0 orient | done; machine idle at 08:41 | `reports/run03/STATUS.md` |
| R1 rotation labels | **PASS**: 17,116/17,116 queries prechecked | `data/labels/pilot_v1/precheck.jsonl`, `reports/run03/rotation.md`, `experiments/2026-11-23_run03_precheck/stdout.log` |
| R2 dataset + split | **PASS**: group-disjoint (test asserts, 11/11 tests pass) | `data/splits/v1_split.json`, `reports/run03/dataset.md`, `experiments/2026-11-23_run03_pytest_final/stdout.log` |
| R3 training | **PASS**: 4 variants × 5 seeds, equal grid, selected on val | `reports/run03/training.md`, `experiments/2026-11-23_run03_train_v2/` (v1 dev iteration: `experiments/2026-11-23_run03_train/`) |
| R4 ASAP | **PASS**: released weights, zero-shot, scores for all 716 test states | `experiments/2026-11-23_run03_asap/{scores.jsonl,meta.json}` |
| R5 test replay | **PASS**: evaluated once (marker `data/splits/.v1_test_evaluated`) | `reports/run03/results_replay.md`, `results_replay_supp.md`, `experiments/2026-11-23_run03_eval_test/` |
| R6 live | **PASS, timings CONFOUNDED** (never idle for 5 min in 2 h, see DECISIONS #12) | `reports/run03/results_live.md`, `experiments/2026-11-23_run03_live/` |
| R7 demo | **PASS** | `reports/run03/figures/demo_05443.gif`, `demo_05443_strip.png`, `demo_05443_caption.md` |

## Main replay results (R5, test: 702 states with ≥ 1 success, 197 assemblies; CIs = bootstrap over assemblies)
| ordering | total planner s [95% CI] | median per-state ratio to optimal | GNN-Surv vs it: ratio of totals [CI] | per-assembly HL diff (s) [CI]; wins/ties/losses | Wilcoxon Holm p |
|---|---|---|---|---|---|
| random (expectation) | 4519 [3438, 5758] | 3.83 | 0.542 [0.422, 0.677] | −4.51 [−6.64, −2.30]; 161/2/34 | 2.4e-15 |
| outside-in | 3322 [2405, 4417] | 2.01 | 0.737 [0.566, 0.950] | −0.85 [−1.71, −0.42]; 133/6/58 | 3.4e-05 |
| fewest contacts | 2832 [2051, 3739] | 1.67 | 0.865 [0.685, 1.075] | −0.64 [−1.12, −0.31]; 128/12/57 | 6.7e-05 |
| ASAP GNN (released weights, zero-shot) | 2950 [2200, 3794] | 2.44 | 0.830 [0.648, 1.032] | −1.40 [−2.37, −0.76]; 144/4/49 | 2.4e-07 |
| MLP-BCE (p), 5 seeds | 2555 ± 199 | 1.62 | 0.959 [0.803, 1.127] | −0.45 [−0.82, −0.21]; 132/10/55 | 6.1e-05 |
| MLP-Surv (p/c) | 2271 ± 93 | 1.34 | 1.079 [0.915, 1.292] | −0.12 [−0.26, −0.01]; 118/17/62 | 0.035 |
| GNN-BCE (p) | 2266 ± 225 | 1.90 | 1.081 [0.874, 1.309] | −0.55 [−0.96, −0.29]; 134/13/50 | 3.7e-06 |
| **GNN-Surv (p/c)** | **2450 ± 89** | **1.16** | — | — | — |
| GNN-Surv (p only) | 2538 ± 218 | 1.64 | 0.965 [0.856, 1.072] | −0.32 [−0.55, −0.18]; 132/21/44 | 3.7e-07 |
| hindsight-optimal | 405 | 1.00 | | | |

How to read it:
- **Two kinds of evidence:** GNN-Surv is cheaper on most assemblies against every ordering (the Wilcoxon tests, Hodges–Lehmann (HL) medians, and the best median per-state ratio, 1.16). But totals are **heavy-tailed**: the 5% most expensive states make up 51–65% of each non-random ordering's total (63% for GNN-Surv; 37% for random) (`results_replay_supp.md`), and on totals its advantage over fewest contacts, ASAP and the other learned models is inside the CIs.
- **Unscored states:** 14 test states had no success (1,515 s, identical for every ordering).
- **Prediction quality** (test nodes, 5 seeds):
  - Within-state C-index for time: GNN-Surv 0.665 ± 0.008, MLP-Surv 0.628, GNN-BCE 0.581, MLP-BCE 0.576, ASAP 0.486.
  - ECE of p: MLP 0.025–0.029, GNN 0.077–0.089.

## Rotation (R1) and the rotation subset
- **Counts:** `needs_rotation` = CMG-RRT success AND no straight pull clears (exact SDF, ε = 0.005, step ≤ ε/2). It holds for **513 / 14,935 successful queries (3.4%)**, **405 / 4,606 states (8.8%)** and **211 / 1,328 assemblies (15.9%)**.
- **Caveat on the flag:** 46% of these have a logged path rotating < 5°, so the flag means "needs more than a straight pull" (`rotation.md`).
- **Inconsistencies:** **124 of 2,181 unsolved queries (5.7%) are linear-free.** The adapter's single tree and coarse goal-edge check miss a free straight pull, so at T = 30 s the oracle under-reports removability. Labels stay `unsolved` (censored).
- **Test rot_state subset** (65 states / 33 assemblies; few assemblies, treat as weak evidence): no comparison is significant after Holm (all p = 1). Totals:

| GNN-Surv | fewest contacts | ASAP | GNN-BCE | MLP-Surv |
|---|---|---|---|---|
| 704 [371, 1093] | 803 | 635 | 527 | 532 |

  GNN-Surv vs fewest contacts = 0.877 [0.540, 1.389]. On non-rot states, GNN-Surv vs fewest contacts = 0.860 [0.659, 1.120].

## Live evaluation (R6; 60 test assemblies, 20 rot; 240 runs, 0 errors; **timings confounded**)
| method | complete / stuck | total planner s (all 60) | GNN-Surv vs it, 56 completed by all: ratio of totals [CI] | wins/ties/losses | Holm p |
|---|---|---|---|---|---|
| random | 56 / 4 | 2018 | 0.778 [0.502, 1.216] | 38/3/15 | 0.003 |
| fewest contacts | 57 / 3 | 2107 | 0.613 [0.475, 0.801] | 47/0/9 | 2.4e-05 |
| ASAP zero-shot | 57 / 3 | 1805 | 0.670 [0.477, 0.933] | 44/2/10 | 7.1e-05 |
| GNN-Surv (seed 101, chosen on val) | 57 / 3 | 1548 | — | — | — |

- **Random vs fewest contacts:** live random had a lower total than fewest contacts, unlike replay. Live totals are dominated by a few stuck/long assemblies.
- **Rot_assembly subset** (19, underpowered): vs fewest contacts 0.579 [0.454, 0.752].
- **Wall time:** within 0.3 s of planner time per assembly.

## Interventions (for the course write-up)
1. **Architectural (GNN vs MLP):** no significant total-time difference.
   - Survival head: 2450 vs 2271 (ratio 1.079 [0.915, 1.292]).
   - BCE head: 2266 vs 2555.
   - The GNN ranks better within a state (C-index 0.665 vs 0.628; median ratio 1.16 vs 1.34) but is less calibrated (ECE 0.077 vs 0.029).
2. **Efficiency/objective (survival p/c vs BCE p):** it lowers the typical cost but not the total.
   - Median per-state ratio: 1.16 vs 1.90 (GNN) and 1.34 vs 1.62 (MLP).
   - GNN-Surv beats GNN-BCE on 134/197 assemblies, yet GNN-BCE's total is lower (ratio 1.081 [0.874, 1.309]).
   - **p-only ablation:** the same survival model ordered by p costs 2538 vs 2450 (ratio 0.965 [0.856, 1.072]; HL −0.32 s, Holm p 3.7e-07). Most of the gain in typical cost comes from the p/c rule, not from the objective alone.
3. **SOTA methods used:** CMG-RRT (TAU-CGL) as the oracle with the exact union-SDF adapter; ASAP's released GNN as a zero-shot baseline; Assemble Them All / Fusion 360 assemblies as data.

## Needs Aaron
1. **Primary metric.** Totals are tail-dominated (5% of states ≈ 60% of time). Which should the course write-up headline: total time (GNN-Surv not significantly better than fewest contacts in replay), per-assembly paired cost (significantly better), or live (significantly better, confounded timings)?
2. **I replaced the prompt's training recipe (v1) with v2** after seeing val-metric noise (SD 98 s per epoch; DECISIONS #8). Only val was used and v1 is reported, but please confirm.
3. **Disclosure:** a dev smoke test touched test assembly 00014 before R5 (DECISIONS #11). Nothing was tuned after it.
4. **R6 timing:** desktop apps (Chrome/Discord/Firefox) kept GPU utilization above 10%. To get unconfounded live timings, close them, or relax the GPU criterion (the planner is CPU-only).
5. **Oracle misses:** 124 linear-free queries were unsolved. Should a straight-pull pre-check be added to the oracle (this would mean relabelling v1)?
6. 1,033 interpenetrating assemblies remain excluded (limitation, as decided).

## Decisions made on Aaron's behalf
`reports/run03/DECISIONS.md` #1–#13. The main ones:
- the R1 step rule (#1) and fresh robot samples (#3);
- protocol v2 (#8);
- the ASAP contact-graph adapter, since redmax isn't installed (#9);
- PointNet skipped to keep the test split single-use (#10);
- R6 run without idle, all timings flagged (#12).

## Proposed run 04
- **elk 4 h run**, alone (`repro_cmgrrt.py --iterations`), plus the **multi-seed exact-vs-learned SDF test** (16505 and alpha, 3 seeds per detector).
- **A tail-aware objective or ordering:** a penalty on P(unsolved) × T, or a learned risk term. Most of the total cost is the tail, and that is where GNN-Surv does not yet win.
- **Seeded robot sampling** (a patch applying a seed to trimesh's sampler) so that identical queries are bit-reproducible across methods.
- **An oracle variant with a linear pre-check** (labelled ablation) to recover the 124 misses.
- **A PointNet-feature variant**, trained before a fresh test protocol (new data or a new held-out split).
- **Live evaluation on the full test split** with desktop apps closed.
- **More data:** 9–12-part assemblies, and the interpenetration cases with a per-pair allowance.
