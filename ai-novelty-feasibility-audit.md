# AI Novelty & Feasibility Audit

## Final status (updated 2026-11-26, end of the project)
The proposal below was written for interlocking puzzles. After the course feedback the project moved to real
mechanical CAD (Fusion 360 assemblies) and to a sharper claim. How the original risks played out:

- **Novelty, as finally claimed:** a GNN with a censoring-aware survival head predicts each planner query's success
  probability and expected (censored) cost, and parts are queried in p/c order with a tight-clearance SE(3) planner
  (CMG-RRT) as the oracle. Prior learned assembly-by-disassembly guidance (Cebulla et al., ICRA 2023; ASAP, ICRA 2024)
  predicts removability only. "A GNN predicts the next removable part" is not claimed. The closest related idea we
  found later orders collision checks by expected time cost at the narrow-phase level (Jiang et al., arXiv 2609.30599,
  2026), one level below our queries.
- **Outcome on the pre-registered test (347 fresh assemblies, evaluated once):**
  - The cost-aware ranker is cheaper than ASAP (zero-shot and retrained), and cheaper than removability-only ordering
    with the same GNN in the main replay analysis, though not robustly.
  - It does **not** beat a fewest-contacts heuristic (`reports/final_eval/REPORT.md`).
  - The largest saving came from an untrained two-pass planner-budget policy.
- **Feasibility risks that did materialise:**
  - The CMG-RRT adapter had a start-pose bug and coarse goal checks (fixed in run 04).
  - The learned SDF accepted penetrating paths (the exact SDF was adopted).
  - Validation optimism did not survive cross-validation and test.
  - The planner's time budget is soft (checked per iteration).
  - On the test set's larger, interpenetrating assemblies the ranker made confident timeout errors; distribution shift
    is the plausible but untested cause. All of this is reported in the paper's failure analysis.
- **Scale:** 2,022 assemblies, 41,913 labelled queries, 17,697 live test disassemblies. That is larger than the
  proposal planned, and possible because 95–98% of successes turned out to be cheap straight pulls.

---

## Original audit (proposal stage, kept for the record)

*Produced by Claude during topic scouting and project development for this proposal.
Reproduced here as the required AI critique summary.*

## Novelty assessment

**What is genuinely new:** No existing work combines (a) a real or CAD-derived 3D
interlocking/cast puzzle of arbitrary shape, (b) a learned heuristic guiding a discrete
"which piece to try next" search so that an expensive continuous motion-planning oracle
is called as few times as possible, and (c) a curved-path (not discretized) motion
planner as that oracle. DeepCubeA (2019) established that a learned heuristic beats
brute-force search on fixed permutation puzzles, but never touched geometric,
variable-shape assemblies. Assemble Them All (2022) established that general 6-DOF
disassembly is solvable at scale, but with zero learning and only discretized canonical
actions, not true curved motion. Manifold-Guided Motion Planning / CMG-RRT (2026)
established that genuinely curved, rotational single-piece extraction is solvable even
for famously hard cases (the Elk disentanglement puzzle), but as a pure geometric
planner with no notion of *which* piece to try or in what order across a multi-piece
assembly. RL-Lock (2026) applies RL to interlocking-assembly *generation* from a
synthetic voxel target, not to solving an existing puzzle's disassembly. Putting a
learned heuristic in front of a curved-path motion-planning oracle, for real
arbitrary-shape puzzles, appears to be an open combination.

**What is not new, and should not be oversold:** "Use a learned heuristic to guide
search" is a well-established pattern (DeepCubeA and its descendants). "Use motion
planning to sequence disassembly" is a well-established pattern in the manufacturing/
robotics literature. This project's contribution is a specific, non-obvious combination
of two active but previously separate lines of work, not a new paradigm. The proposal
should frame the novelty claim at this level of precision — a defensible, meaningful new
combination — rather than claiming to have invented learned search or curved-path
planning from scratch.

## Red-ocean / saturation risks identified during scouting

1. **"Just build a learned puzzle generator" is no longer blue ocean.** This was the
   original project concept before RL-Lock (2026) was found during scouting — it already
   does RL-based interlocking-assembly generation. The project pivoted to the solving
   side specifically because of this finding. Any future direction that drifts back
   toward "generate new puzzles" as the primary contribution should be re-checked
   against RL-Lock before being treated as novel.
2. **"Just solve general 6-DOF disassembly" is also not novel by itself**, since
   Assemble Them All already does this at industrial scale with classical BFS and no
   learning. This is why the project's evaluation is framed around *reducing expensive
   motion-planner queries relative to uninformed search*, not "solving puzzles that
   couldn't be solved before."
3. **Fully continuous, jointly-coordinated multi-piece motion planning remains a
   genuinely hard, unsaturated research frontier** (C-Space Tunnel Discovery, 2020,
   needs 250+ CPU-hours per case and tops out at two-piece puzzles even with a learned
   component) — but this cell is arguably too hard for a semester project, not too
   crowded. The project explicitly scopes around this by decomposing into single-piece
   continuous motion (tractable, per CMG-RRT) plus discrete high-level ordering
   (tractable, per DeepCubeA-style search), rather than attempting the harder joint case.
4. **Tutorial-level topics were screened out per course policy.** MNIST-style
   classification, basic CNN demos, and similarly outdated topics were never candidates;
   this is noted for completeness, not because the current topic was ever close to that
   category.
5. **No competing consumer product was found** that scans a physical interlocking
   puzzle and solves or generates puzzles from it — the space remains research-only,
   which is favorable, but the research side (especially RL-Lock and CMG-RRT, both
   2026) is moving fast, so the window for this specific combination being unclaimed
   should not be assumed to last indefinitely.

## Feasibility risks and mitigations

- **CMG-RRT integration risk:** the project depends on the open-source CMG-RRT code
  working as expected on unfamiliar puzzle geometry. Mitigation: confirm this hands-on
  in week 1, before other design commitments; keep a cheaper discretized-action
  (PyBullet-based) ablation as a working fallback environment.
- **Query cost risk:** each motion-planning query is expensive, which could bottleneck
  training-time data generation. Mitigation: cache oracle results per (piece, state)
  pair; consider modest paid cloud compute to parallelize queries if needed (estimated
  tens of dollars, not a large budget item).
- **Real-object risk:** scanning a physical metal puzzle via photogrammetry is a known
  failure mode for reflective surfaces. Mitigation: CAD-model from caliper measurements
  as the primary path, with matte-spray-assisted photogrammetry as a secondary option.
- **Training-signal risk:** if generated training puzzles are all translation-solvable,
  the model never learns to value curved/rotational moves. Mitigation: deliberately
  construct and verify a rotation-required subset of the training family before
  training begins.

## Scale and framing risks

- **Training-scale honesty.** DeepCubeA's original approximate value iteration trained
  on state volumes (and compute) far beyond what a laptop-plus-modest-cloud semester
  project can reach, because in this project — unlike a Rubik's Cube move — checking
  whether a candidate extraction is legal requires a real motion-planning query, not a
  free lookup. Unrestricted training against the real CMG-RRT oracle would be
  bottlenecked by query cost long before reaching a meaningful sample size. Mitigation:
  a two-phase training curriculum — bulk approximate value iteration (targeting
  10^4-10^5 sampled states) against the cheap, near-free discretized-action oracle
  (PyBullet), which is enough volume for a real GNN-vs-MLP comparison, followed by
  transfer/fine-tuning and final evaluation against the real CMG-RRT oracle on a small,
  deliberately curated set (10^2-10^3 queries). This is an honest, bounded-scale
  demonstration of the method, not a claim to match industrial-scale training runs.
- **Domain-perception risk ("is this just a toy puzzle demo").** Even with a rigorous
  method, "solves a puzzle" can read as recreational unless explicitly connected to why
  it matters outside puzzle-enthusiast circles. The connection is real: the same
  expensive-verification-plus-occasional-curved-motion structure recurs in EV battery
  disassembly, cluttered-scene retrieval, and recycling/maintenance robotics (literature
  survey items 5, 6, 9) — puzzles are used here as a controlled, cheaply reproducible
  testbed for that problem class, not as the target application itself. Mitigation:
  state this framing explicitly in the README and proposal document rather than leaving
  it implicit in the citation list, and lead the final demo with the falsifiable claim
  (fewer oracle calls than uninformed search, on a real physical object) rather than
  "look, it solved a puzzle."

## Overall verdict

The project occupies a specific, currently unclaimed combination of two active research
lines, is scoped to avoid both the "already solved" cell (general 6-DOF disassembly via
classical search) and the "still too hard" cell (joint multi-piece continuous motion),
and has concrete, citable open-source tools (DeepCubeA, CMG-RRT) to build on rather than
requiring everything to be built from scratch. The main risk to the novelty claim is the
pace of adjacent publication (RL-Lock and CMG-RRT are both from 2026), which argues for
moving on implementation promptly and re-checking the landscape before the final report
rather than treating this audit as a one-time check.
