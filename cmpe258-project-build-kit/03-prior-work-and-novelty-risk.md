# Closest Prior Work, Datasets, and Novelty Risk

Searched 2026-11-14. Re-verify code links before depending on them.

## 1. Directly overlapping (must cite and differentiate)

**ASAP: Automated Sequence Planning for Complex Robotic Assembly with Physical Feasibility** (Tian et al., ICRA 2024, arXiv 2309.16909; project page asap.csail.mit.edu)
- Physics-based assembly-by-disassembly tree search for general-shaped assemblies. It also checks gravitational stability.
- Search is guided by geometric heuristics **or a GNN trained on simulation labels**. The GNN (PointNet part encoder + custom features + message passing + MLP classifier) predicts the **next part to disassemble** as node classification.
- Its planner exposes a budget, the maximum number of feasibility evaluations, so "number of feasibility checks" is already a natural metric there.
- Dataset: 2,146 assemblies, 3 to 50+ parts. Code + data released (repo linked from the project page; a fork at github.com/makolon/ASAP calls itself the official code; confirm which is canonical).
- **Overlap:** very high with the professor's suggested formulation. **Use:** strong external baseline and data source; satisfies "recent open-source SOTA."

**Cebulla, Asfour, Kröger: "Speeding Up Assembly Sequence Planning Through Learning Removability Probabilities"** (KIT, 2023)
- Trains a GNN to predict part removability so assembly-by-disassembly tests parts in a better order. This is essentially "rank which part gets the next expensive check." Reports >85% removability accuracy for products with similar designs.
- **Overlap:** very high with the core idea. Must be cited.

**GRACE: "Efficient and Feasible Robotic Assembly Sequence Planning via Graph Representation Learning"** (Atad et al., arXiv 2303.10135)
- GNN over a heterogeneous part/surface "Assembly Graph" that predicts the next assembly step. Aluminum-profile product variants. Related, lower overlap.

## 2. Building blocks

**Assemble Them All** (Tian et al., SIGGRAPH Asia 2022; github.com/yunshengtian/Assemble-Them-All)
- Physics-based assembly-by-disassembly with discretized translate/rotate actions; arbitrary shapes; up to 80-part assemblies in minutes.
- Datasets released: two-part main (221 MB), **two-part rotational (5.4 MB)**, multi-part (778 MB). Derived from the Fusion 360 Gallery dataset (check its license). Includes a script to preprocess custom .obj assemblies.
- Use: realistic CAD geometry (answers the professor's point 1), the discretized ablation planner, the rotational subset.

**CMG-RRT: "Manifold-Guided Motion Planning for Tight Assemblies"** (Tel Aviv Univ., 2026, arXiv 2607.17898; github.com/TAU-CGL/cmg-rrt, MIT license)
- Sampling-based planner for near-zero-clearance rigid-body assembly including rotation; first automatic solution to the Elk puzzle. Classical (no learning). Two-body: plans one moving body against one static body, start pose to goal pose (see 04).
- Use: the curved-path oracle; the hard-case stress set.

**DeepCubeA** (2019): the original inspiration. Its backward-rollout training is now dropped (see 02). Cite it as motivation only.

## 3. Where the novelty can come from (pick and defend one or two)

ASAP and Cebulla already show that "GNN ranks which part to test next" helps with physics/geometric feasibility checks. Candidate differences for this project:

1. **A much more expensive, continuous, tight-clearance oracle.** ASAP and Assemble Them All use discretized physics-based checks. Here each query is a CMG-RRT curved-path planning run (seconds to minutes, can time out), so wasted queries cost far more. Question: do learned rankings trained on cheap-oracle labels still cut calls when the oracle is a continuous tight-clearance planner?
2. **Rotational/tight-clearance cases where contact-graph features mislead.** Evaluate specifically on the rotational subset + CMG-RRT puzzles, where "few contacts = easy to remove" heuristics break.
3. **Cost-aware ranking (Claude's suggestion, not in the sources above as far as checked).** Predict both P(success) and expected planning time, and order queries by expected cost (e.g., by P(success)/E[time]) instead of P(success) alone. Treat timeouts as censored labels. This directly targets wall-clock time, which matters more once the oracle is expensive.
4. **Cross-oracle / cross-domain transfer (domain-adaptation intervention).** Train on labels from the cheap discretized oracle (Assemble Them All) and fine-tune or evaluate with CMG-RRT; or train on CAD assemblies and test on tight puzzles.

Not novel by itself: "a GNN predicts the next removable part." The write-up must not claim this as the contribution.

## 4. EV battery / industrial angle

- ABatRe-Sim (arXiv 2303.07617): Gazebo simulation with a generic EV battery pack CAD model (4 modules, bolts, cables). CAD availability not confirmed. Possible demo asset only.
- KIT knowledge-graph dataset of product structures and disassembly sequences for 10 EV battery packs (BMW i3, IONIQ 5, etc.), CC BY 4.0, **no CAD geometry**. Useful for motivation, not for the motion planner.
- Multi-robot EV battery disassembly task planning with RRT/RRTConnect/RRT* (Erdogan et al., *Robotics* 2024): shows the plan-then-motion-plan pattern is used in battery work.
- Realistic battery-module CAD with planner-ready geometry wasn't found. The defensible industrial claim is "realistic mechanical CAD assemblies" (Fusion 360-derived), not "battery teardown," unless a usable module CAD turns up.
