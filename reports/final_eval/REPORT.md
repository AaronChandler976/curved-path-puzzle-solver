# Final evaluation on the v2 test set (campaign Phase 3; evaluated once)

**Registered answer (PREREG §7, replay, main configuration): GNN-Surv does NOT beat the best heuristic.** The best
heuristic was chosen on val: fewest contacts. Ratio of total planner time GNN-Surv / fewest contacts = **1.055
[0.887, 1.257]**, HL +0.02 s per assembly, W/T/L 132/61/148, Holm-adjusted Wilcoxon p = 0.43. Neither condition (a) nor
(b) holds. The pre-registered sensitivity check on the 300 scored clean test assemblies (addendum A) agrees: 0.999
[0.829, 1.226], Holm p 0.81, does not beat. **Live, applied separately, gives the same verdict:** 0.915 [0.819, 1.015],
Holm p 0.13 (§4).

## 1. Discipline (evidence)
- **Marker:** `data/splits/.v2_test_evaluated` was written at 2026-11-24 23:08:45 (git b5d851a) by `scripts/eval_v2.py`, before
  it read any test label.
- **Freeze:** commit a13b397, which precedes the marker (`docs/PREREG_addendum.md`, `configs/final_frozen.yaml`, DECISIONS
  #12).
- **Replay:** `experiments/2026-11-25_final_eval_replay/` (command in `cmd.txt`, identical to the one frozen in
  `configs/final_frozen.yaml`), ran once and scored on CPU. Tables: `reports/final_eval/replay.md`.
  The folder is dated the 25th but ran on the 24th at 23:08 local time (same naming slip as DECISIONS #9).
- **Coverage:** 347 test assemblies, 2,226 states. 2,195 states on 341 assemblies have ≥ 1 main-config success and are
  scored. 31 states have none: every ordering pays 4,477 s there, outside the totals.
- **Seeds:** every trained variant enters as its seed-mean over 5 seeds, and all 50 frozen checkpoints were used. Their
  sha256 values are in `configs/final_frozen.yaml`.

## 2. Replay, main configuration (pre-check → CMG-RRT), registered comparisons
| ordering | total planner time (s) [95% CI] | seeds mean ± std |
|---|---|---|
| random (expectation) | 22,186 [18,793, 25,788] | |
| outside-in | 9,130 [6,764, 11,965] | |
| **fewest contacts** (best heuristic, val) | **7,202** [5,477, 9,177] | |
| ASAP zero-shot | 12,387 [9,712, 15,294] | |
| ASAP-retrained | 11,500 [9,102, 14,102] | 11,500 ± 529 |
| MLP-BCE | 7,672 [5,977, 9,512] | 7,672 ± 690 |
| MLP-Surv | 7,983 [6,306, 9,861] | 7,983 ± 768 |
| GNN-BCE | 8,563 [6,826, 10,441] | 8,563 ± 1,123 |
| **GNN-Surv** | **7,595** [5,921, 9,415] | 7,595 ± 210 |
| GNN-Surv-Tail | 7,415 [5,926, 8,988] | 7,415 ± 688 |
| PN-GNN-Surv | 7,771 [6,123, 9,512] | 7,771 ± 841 |
| hindsight-optimal | 416 [261, 603] | |

**Paired, Holm family of 11** (ratio of totals A/B [95% CI]; Holm p):

| A vs B | ratio | Holm p |
|---|---|---|
| GNN-Surv vs random | 0.342 [0.278, 0.413] | 1.4e-36 |
| GNN-Surv vs outside-in | 0.832 [0.671, 1.043] | 1 |
| GNN-Surv vs fewest contacts | 1.055 [0.887, 1.257] | 0.43 |
| GNN-Surv vs ASAP zero-shot | 0.613 [0.517, 0.726] | 2.1e-06 |
| GNN-Surv vs ASAP-retrained | 0.660 [0.543, 0.793] | 5e-07 |
| GNN-Surv vs MLP-Surv | 0.951 [0.831, 1.084] | 0.55 |
| GNN-Surv vs GNN-BCE | 0.887 [0.785, 0.999] | 6.2e-07 |
| GNN-Surv vs GNN-Surv-Tail | 1.024 [0.934, 1.112] | 1 |
| GNN-Surv vs PN-GNN-Surv | 0.977 [0.871, 1.091] | 1 |
| GNN-BCE vs MLP-BCE | 1.116 [0.948, 1.317] | 0.0027 |
| MLP-Surv vs MLP-BCE | 1.041 [0.952, 1.136] | 0.29 |

How to read this (claims limited to what the rule and numbers support):
- **Against the two open-source GNN baselines**, both conditions hold: ASAP zero-shot (0.613) and ASAP retrained on our
  data with its own objective (0.660). Ratio CI below 1, Holm p < 0.05, HL < 0 (−0.39 s and −0.63 s).
- **Survival p/c vs BCE p (GNN):** 0.887 [0.785, 0.999], Holm p 6.2e-7, HL −0.21 s. Cost-aware ordering is cheaper
  than removability-only ordering with the same encoder, on total time and per assembly. This is the project's
  novelty claim, and the test supports it for the GNN.
- **Not supported on test:** GNN vs MLP (survival head: 0.951, p 0.55). With the BCE head the GNN is costlier per
  assembly than the MLP (HL +0.10 s, Holm p 0.0027; ratio CI includes 1). PointNet features and the tail-aware objective
  made no detectable difference (CIs include 1, Holm p = 1).
- **CMG-RRT-only configuration (robustness, descriptive):** GNN-Surv / fewest contacts 0.986 [0.882, 1.100], Holm p 0.88.
- **Subsets (none used for a claim):**
  - Every subset has ≥ 30 scored assemblies (rot_state 105; parts 7–8 has 37).
  - The ratio vs fewest contacts ranges from 0.927 (5–6 parts) to 1.241 (9–10 parts). None is significant after
    correction; 9–10 parts has uncorrected p 0.022.

## 3. Exploratory (post-registration; addendum B; uncorrected)
- **Exploratory variants (replay):** GNN-Surv-ListNet 7,226 s, GATv2-Surv 7,773 s, GT-Surv 8,411 s, against 7,202 s
  for fewest contacts. The CV ranking (ListNet and GT best) did not carry over for GT.
- **Two-pass budget policy, T' = 3 s, every ordering:** this is the largest effect measured on test.
  - Fewest contacts 7,202 → **2,008 s** (−72%); GNN-Surv 7,595 → 1,904 s; ListNet 1,890 s.
  - Under the same policy, GNN-Surv / fewest contacts is 0.948 [0.820, 1.095], p 0.15 (uncorrected): no detectable
    difference.
  - The policy is not learned. It removes most of the cost of queries that time out, whatever the ordering.
- **Prediction quality** (`replay.md`):
  - Survival models are calibrated (ECE 0.038 GNN-Surv) and rank parts by time better than ASAP's score:
    within-state C-index 0.674 vs ASAP zero-shot 0.593 and ASAP-retrained 0.626. ListNet is the highest at 0.689.
  - The C-index is only modestly above 0.5, and the failures (§5) are confident mistakes.

## 4. Live full disassembly (PREREG §6) — complete
- **Run:** `experiments/2026-11-24_final_eval_live/` (`scripts/run_final_live.sh`), tables in
  `reports/final_eval/live_registered.md`.
  - Every method ran on all 347 test assemblies, with fresh queries (oracle v2: CMG-RRT only when the pull fails).
  - Planner seed per query = sha1("run05-live", …). The idle guard was on.
  - 13,533 (assembly, method) runs. 77 were confounded and re-run, and **0 remain confounded or errored**.
- **Seeds:** P1 ran each trained variant at its val-best seed, and P2 added the remaining 4 seeds. Trained variants enter
  as the seed-mean over 5 seeds per assembly (PREREG §5).
- **Cost:** per-assembly cost = total planner time of the whole disassembly, including stuck runs. That is why live
  totals are about 3× the replay totals, which leave out states with no success.

| ordering | complete / stuck runs | total planner time (s) [95% CI] |
|---|---|---|
| random | 316 / 31 | 26,464 [21,786, 31,202] |
| outside-in | 313 / 34 | 23,239 [18,426, 28,310] |
| fewest contacts | 312 / 35 | 23,002 [18,624, 27,561] |
| ASAP zero-shot | 314 / 33 | 26,667 [21,430, 32,121] |
| ASAP-retrained (5 seeds) | 1,565 / 170 | 23,212 [18,512, 28,367] |
| MLP-BCE | 1,563 / 172 | 21,139 [17,005, 25,681] |
| MLP-Surv | 1,560 / 175 | 20,827 [16,767, 25,237] |
| GNN-BCE | 1,569 / 166 | 20,131 [16,285, 24,209] |
| **GNN-Surv** | 1,572 / 163 | **21,038** [16,700, 25,758] |
| GNN-Surv-Tail | 1,569 / 166 | 19,885 [15,987, 24,045] |
| PN-GNN-Surv | 1,566 / 169 | 20,805 [16,644, 25,350] |

- **§7 rule applied to live (separately):** GNN-Surv / fewest contacts = **0.915 [0.819, 1.015]**, HL −0.05 s, W/T/L
  181/45/121, Wilcoxon p 0.019, Holm p 0.13: **does not beat**. On the 306 clean assemblies: 0.907 [0.801, 1.020], Holm
  p 0.22.
  - Disclosed: the interim P1 table (val-best seed only, `live_P1.md`) had Holm p 0.0018 for the typical-assembly
    condition. With the registered 5-seed mean it is not significant.
- **Both ASAP baselines are beaten live**, both conditions met:
  - ASAP zero-shot: 0.789 [0.699, 0.880], Holm p 2.8e-7.
  - ASAP-retrained: 0.906 [0.827, 0.994], Holm p 0.04, HL −0.15 s.
  - Random: 0.795 [0.674, 0.932], Holm p 3.6e-8.
- **Interventions live:**
  - Survival vs BCE (GNN): 1.045 [0.955, 1.150] on totals, but HL −0.06 s with Holm p 0.035. GNN-Surv is cheaper on the
    typical assembly, not on total time, the opposite of replay, where it was cheaper on both.
  - GNN vs MLP (survival 1.010; BCE 0.952), PointNet (1.011) and Tail (1.058 [1.003, 1.110], Holm p 0.18): no
    difference that survives Holm.
- **Subsets** (GNN-Surv vs fewest contacts, uncorrected): ratios 0.85–0.99 in every source and size bin; none has a CI
  entirely below 1.
- **Exploratory live rows** (post-registration, uncorrected p; `reports/final_eval/live.md`). P3 and P4 finished at
  2026-11-26 09:29 (17,697 runs in total).
  - *ListNet:* 18,336 s, the cheapest live ordering. Ratio vs fewest contacts 0.797 [0.711, 0.886], p 3.7e-5; vs
    GNN-Surv 0.872 [0.806, 0.942]. In replay ListNet was no cheaper than fewest contacts (7,226 vs 7,202 s), so replay
    and live disagree for this variant. It is a hypothesis for future work, not a finding.
  - *GT-Surv:* 21,735 s; vs fewest contacts 0.945 [0.844, 1.055].
  - *Budget policy T' = 3 s:* fewest contacts 23,002 → 11,273 s (ratio 0.490 [0.424, 0.557]); GNN-Surv (val-best
    seed) 10,810 s (vs its 5-seed full-budget mean: 0.514). Under the same policy GNN-Surv / fewest contacts = 0.959
    [0.896, 1.023]. The live saving (about 50%) is smaller than the replay saving (72%) because a stuck live
    disassembly pays the second pass in full.
- Figures: `reports/final_eval/figures/totals_replay_live.pdf`, `budget_policy.pdf`, `failure_scatter.pdf`
  (`scripts/final_figures.py`; dashed line = fewest contacts).

## 5. Failure analysis (`reports/final_eval/failure_analysis.md`)
- **Tail concentration:** the costliest 5% of states hold 89% of fewest contacts' total and 77% of GNN-Surv's.
- **Where GNN-Surv loses** (val-best seed 101, vs fewest contacts, state by state): cheaper on 436 states (−3,240 s),
  costlier on 368 (+3,404 s).
  - *Timeout first:* 85 states, **+3,153 s**. It queried a part that ran to the full budget before the first success.
  - *Slower first success:* 283 states, +251 s.
- **The failure mode:** in each of its 10 costliest states, the part GNN-Surv queried first had predicted p 0.90–1.00
  and c 0.1–3.7 s, and then ran unsolved for > 30 s. So did the next two parts in most of these states. These are
  confident wrong predictions.
- **Where it happens:** the 20 largest losses are all on assemblies with 4–12 parts (15 of 20 with 9–12 parts) from the
  fresh sources.
- **Likely cause:** distribution shift. Test is 51% 9–12-part and 63% allowance-recovered assemblies, train is 79% 3–8-part
  v1. Val (80% v1) and the train+val CV could not show this, because 9–12-part assemblies were underpowered there.
