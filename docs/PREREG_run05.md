# Pre-registration for run 05 (written in run 04, before any v2 training)

Status: frozen when committed. Run 05 may not change anything below after seeing any v2 val/test number, except
to fix a bug, and any such fix is reported as a deviation with its reason. Everything not fixed here is decided on
val only.

## 0. Data, oracle, split (fixed by run 04)
- **Labels:** `data/labels/pilot_v2/labels.jsonl` (oracle v2 = straight-pull pre-check → CMG-RRT with the v2 adapter
  fixes, `reports/run04/oracle_v2.md`). Every query records both stages, so two oracle configurations can be replayed:
  - **main = "pre-check → CMG-RRT"**: a query succeeds if the pull clears or CMG-RRT succeeds;
    cost = precheck_time_s + (cmgrrt_time_s if the pull did not clear).
  - **secondary = "CMG-RRT only"**: outcome cmgrrt_outcome, cost cmgrrt_time_s.
  Labels (success and cost) for training and replay use the **main** configuration. The secondary configuration
  is reported for every replay table as a robustness check; models are NOT retrained for it.
  The label is the first clean attempt; queries still confounded after 2 re-runs are kept and flagged.
- **Split:** `data/splits/v2_split.json` (seed 0; tested in `tests/test_split_v2.py`). The test set is fresh
  assemblies only (never in pilot_v1), about half of the fresh pool's duplicate groups, stratified by (source,
  part-count bin). 00014 and every run 03 test assembly are in train/val. Sizes: see §8.
- **T = 30 s**, ε = 0.005, K = 8 survival bins (log-spaced 0.1 s … T), exactly as run 03.
- **A state counts** for training and replay if it has ≥ 1 success under the main config (states with none have
  the same cost under every ordering and are reported separately).

## 1. Variants (5 seeds each: 100, 101, 102, 103, 104)
| id | encoder | head / objective | ordering key | inputs |
|---|---|---|---|---|
| MLP-BCE | MLP (same depth as the GNN, no message passing) | BCE (success) | p | 18 hand-made node features |
| MLP-Surv | MLP | discrete-time survival NLL (censoring-aware) | p/c | same |
| GNN-BCE | GINE GNN (run 03 `Ranker3`) | BCE | p | same + 5 edge features |
| **GNN-Surv** (main) | GINE GNN | survival NLL | p/c | same |
| GNN-Surv-Tail | GINE GNN | survival NLL + λ · tail term (§2) | p/c | same |
| PN-GNN-Surv | PointNet (end to end, `src/disasm/models/pointnet.py`) + GINE GNN | survival NLL | p/c | same + 1,024-point part clouds with normals (`src/disasm/data/pointcloud.py`) |
| ASAP-retrained | ASAP's `ModelGraph` (fresh init) | ASAP's own objective: BCEWithLogits, one positive = the removed part, 90° random-axis rotation augmentation (`src/disasm/models/asap_train.py`) | σ(logit) | ASAP inputs; ASAP's own redmax contact graph (env `asap`, `scripts/asap_contact_graphs.py`) |

Untrained orderings: random (expectation over orderings in replay; seeded shuffle in live), outside-in, fewest
contacts (ties: outside-in, then part id), **ASAP zero-shot** (released weights, redmax contact graph), and
hindsight-optimal (replay lower bound).

## 2. Tail-aware objective (exact definition; `src/disasm/models/tail_loss.py`, tested in `tests/test_tail_loss.py`)
For a state with ≥ 1 success: scores s_i = log p_i − log c_i from the survival head (with gradients), observed
success y_i and observed cost t_i (main-config query cost). NeuralSort soft permutation
P̂[k, :] = softmax(((n + 1 − 2k) s − A_s 1) / τ), A_s[i, j] = |s_i − s_j|; ỹ = P̂y, t̃ = P̂t;
C_soft = Σ_k t̃_k Π_{j<k} (1 − ỹ_j).
**L = L_survNLL + λ · mean over states with ≥ 1 success of C_soft / T,** with τ = 0.1; λ ∈ {0.1, 1.0} is a grid axis
for this variant only (so its grid has 16 configs; the budget rule in §3 is per config).

## 3. Shared tuning grid, budget and selection (run 03 protocol v2)
- Fixed for every trained variant except ASAP-retrained: AdamW, weight decay 1e-4, dropout 0.1, grad-clip 1.0,
  batch 32 states, ≤ 150 epochs.
- Grid: hidden {64, 128} × lr {1e-3, 3e-4} × layers {2, 3} (8 configs; ×2 λ for GNN-Surv-Tail). PN-GNN-Surv adds
  nothing (PointNet width 128, embedding 64, fixed).
- ASAP-retrained: ASAP's architecture constants (feat 512, batch norm, dropout 0); grid lr {1e-3, 3e-4, 1e-4} ×
  batch {16, 32} (6 configs), Adam, ≤ 150 epochs, the same early stopping.
- **Selection metric:** total replay planner cost on val (main config), read as the 5-epoch trailing mean;
  minimum 10 epochs, patience 25. A config is ranked by the mean over seeds 0, 1, 2. The chosen config is then
  trained with the fresh seeds 100–104. Each variant gets the same per-config budget.
- Report every variant and every seed (mean ± std over the 5 seeds); never drop a seed.

## 4. Metrics (decided before any result)
- **Primary:** total planner time (main config) summed over the test set, replay and live.
- **Co-reported paired metric:** per-assembly Hodges–Lehmann median difference of planner time, with
  wins / ties (|d| ≤ 0.01 s) / losses, replay and live.
- Secondary: planner calls; median per-state ratio to hindsight-optimal; within-state C-index for time; ECE of p;
  solve rate; the same tables under the CMG-RRT-only configuration.

## 5. Comparisons, CIs, tests
- Comparisons (Holm-corrected as one family per evaluation (replay; live)): GNN-Surv vs each of random, outside-in,
  fewest contacts, ASAP zero-shot, ASAP-retrained, MLP-Surv, GNN-BCE, GNN-Surv-Tail, PN-GNN-Surv (9 comparisons).
  Interventions for the course: GNN vs MLP (survival head; BCE head), survival p/c vs BCE p (GNN; MLP),
  PointNet vs hand-made features, tail-aware vs plain survival. These are reported in the same family.
- A trained variant enters a comparison as its seed-mean per assembly (each assembly's cost averaged over the 5 seeds).
- CIs: bootstrap over assemblies (10,000 resamples, seed 0) for the ratio of totals and the HL difference.
  Tests: two-sided Wilcoxon signed-rank on per-assembly costs.
- **Subsets** (reported, never used for selection): rot_state (needs more than a straight pull; evaluation-only flag),
  source (fresh-9to12, fresh-allowance), part-count bin (3–4, 5–6, 7–8, 9–10, 11–12). Any subset with < 30 assemblies
  is labelled underpowered and gets no conclusion. Expected underpowered before seeing data: rot_state on its own and
  the smallest part-count bins of the allowance source (to be confirmed from counts only, §8).

## 6. Live evaluation (run 05)
Every test assembly; methods: random, outside-in, fewest contacts, ASAP zero-shot, ASAP-retrained (5 seeds) and
every trained variant (5 seeds each), oracle v2 main config with live mode (CMG-RRT only when the pull fails), fresh
queries, planner seed per query = sha1("run05-live", assembly, state, part), 10 workers, per-method work dirs, idle
guard on (5 min non-busy; dispatch only while non-busy; confounded runs re-run up to 2 times; first clean attempt
reported). Live totals are reported with the same metrics and tests as replay.

## 7. Decision rule: "GNN-Surv beats the best heuristic"
The **best heuristic** is the untrained ordering (outside-in or fewest contacts; random excluded) with the lowest val
replay total (main config), chosen on val before test is opened. GNN-Surv beats it iff, on the test set in REPLAY
(main config), **both** (a) the 95% bootstrap CI of the ratio of totals (GNN-Surv seed-mean / heuristic) lies entirely
below 1.0, **and** (b) the Holm-adjusted Wilcoxon p < 0.05 with an HL difference < 0. If only (b) holds, it is
reported as "cheaper on the typical assembly, not on total time". Live results are reported next to replay, and the
same rule is applied to live separately. The test split is evaluated exactly once.

## 8. Split sizes (filled in at run 04 T8, 2026-11-24, from `data/splits/v2_split.json`; assembly counts only, no labels)
Built by `scripts/build_split_v2.py --seed 0` (`experiments/2026-11-24_run04_t8_split/`), 2,022 labelled assemblies in
1,996 duplicate groups, none excluded.

| split | assemblies | groups | v1 | fresh-9to12 | fresh-allowance |
|---|---|---|---|---|---|
| train | 1,425 | 1,406 | 1,129 | 109 | 187 |
| val | 250 | 247 | 199 | 19 | 32 |
| **test** | **347** | 343 | 0 | 127 | 220 |

Test by part-count bin: 3–4: 82, 5–6: 52, 7–8: 37, 9–10: 102, 11–12: 74 (all from fresh sources).
Underpowered (< 30 assemblies), from counts only: no registered test subset by source or bin alone. Source × bin
cells are not registered subsets (fresh-allowance 11–12 has 19). rot_state is a state-level flag; its assembly count
is only known once test labels are read, so whether it is underpowered is decided then, by the same < 30 rule.
States with no main-config success drop out of scoring, so a subset's scored assembly count can be lower than the
counts above. The < 30 rule is applied to the scored count.
