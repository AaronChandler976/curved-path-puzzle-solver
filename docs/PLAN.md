# Project plan (adopted 2026-11-21; updated 2026-11-22 after run 01)

Source of truth for agents working in this repo. When this file and CLAUDE.md
disagree, CLAUDE.md's hard rules win.

## Question
Can a learned structural model (a GNN over the part-contact graph) that
predicts both whether a planner query will succeed and what it will cost
reduce total planning time in assembly-by-disassembly (AbD)? The baseline is
removability-only ranking (ASAP, ICRA 2024; Cebulla et al., ICRA 2023), with
the same curved/rotational SE(3) planner (CMG-RRT) used throughout.

## Pipeline
1. State = the set of remaining parts. The ranker scores every remaining part.
2. Parts are queried in descending p/c order, where p = P(success within T)
   and c = E[min(time, T)]. This ordering is optimal for sequential tests
   searching for a first success (Simon & Kadane 1975).
3. Oracle = CMG-RRT on one moving part against the union of the other
   remaining parts. The first success is removed; repeat.

## Oracle definition (from run 02 on)
- Collision model: an **exact per-part SDF** (mesh distance plus a robust
  winding-number sign), computed once per part per assembly. The obstacle for
  a query is the **min over the other remaining parts' SDFs** (the SDF of a
  union is the min of the SDFs).
- **Contact tolerance ε:** penetration below ε counts as contact, not
  collision. Assembled parts touch, so the start pose sits at SDF ≈ 0. ε is
  chosen and sensitivity-checked in run 02.
- The CMG-RRT planning algorithm itself is unchanged; only the collision
  representation is swapped, through our own detector class (never by editing
  `external/`). The learned-SDF path is kept for reproducing the bundled
  examples and for comparison.
- A non-success is `unsolved` (censored at T), never "infeasible."

## Cost definition (decided 2026-11-22)
- **Query cost = planner wall-clock time** (CMG-RRT search only).
- **Setup cost** (SDF construction, mesh prep) is logged per part and per
  assembly and reported separately. Ordering can't change it. Reports show
  both "planner only" and "planner + setup" totals.

## Labels
- States are reached by forward disassembly from the real assembled product
  using planner-verified removals, so every state is physically valid.
- At each visited state, **every** remaining part is queried; one random
  success is removed (logged seed).
- **Tier A (cheap):** Assemble Them All's discretized physics planner. Many
  assemblies. Not yet set up; needs its C++ simulator.
- **Tier B (expensive):** CMG-RRT with the oracle above. Label sets:
  `pilot_v0` (run 01, learned SDF; failures mostly artifacts) and `pilot_v1`
  (run 02, exact union SDF).

## Model
Per-part features (volume, bbox, distance to center, contact count,
contact-normal histogram, optional PointNet embedding) → GNN (GINE/GATv2, contact edge features)
→ discrete-time survival head over K log-spaced bins up to T (censoring-aware NLL).
Ablations: BCE-only head; MLP (no message passing) on identical features.

## Interventions (course requirement: ≥ 2)
1. Architectural: GNN vs MLP.
2. Efficiency: cost-aware survival objective + p/c ordering vs BCE removability-only ordering.
3. Domain adaptation: Tier A pretrain → Tier B fine-tune (if Tier A gets set up).

## Baselines (same oracle, same T)
Random; outside-in (ASAP's heuristic); fewest contacts; bookkeeping; MLP; ASAP's GNN
(yunshengtian/ASAP); our GNN with BCE only. Hindsight-optimal = lower bound in replay.

## Metrics
Primary: total planner time per full disassembly. Secondary: planner calls, solve rate under a
time budget, P(success) calibration, censored time error. Split: rotation-required vs
translation-like. Paired per assembly, bootstrap 95% CIs, fixed seeds.

## Novelty statement
ASAP/Cebulla predict removability and count tests. We model query cost and censored timeouts
for a continuous tight-clearance SE(3) planner, and order queries by expected cost. Odense et
al. (IROS 2022) predicted sampling-planner runtime with GNNs, but not for AbD query ordering.
"A GNN predicts the next removable part" is NOT our contribution.

## Run 01 findings that shape the plan (reports/MORNING_REPORT.md)
- 85% of unsolved v0 queries started in collision under the learned SDF (artifact).
- Successes: median 1.1 s and 1 iteration; most parts escape almost straight.
- Learned-SDF setup ≈ 66 s/query dominated throughput.
- CMG-RRT solved 3/34 bundled runs under GPU contention; not yet a clean reproduction.
