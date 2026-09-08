# Literature & SOTA Survey

Nine papers published within the last 1-3 years (2023-2026), directly relevant to the
curved-path puzzle-solving project. Two older foundational papers are also noted at the
end for context, since the project's method extends them, but they are not counted
toward the recency requirement.

## 1. DeepCubeAF (2025)

Generalizes DeepCubeA into a single learned heuristic that transfers across
pathfinding/search domains without per-domain retraining, drawing on domain-
randomization ideas from reinforcement learning. Directly relevant as the closest
precedent for the "learn one flexible heuristic, don't retrain per puzzle" goal of our
high-level GNN heuristic.
[Paper](https://rlj.cs.umass.edu/2025/papers/Paper235.html)

## 2. Learning Empirically Admissible Neural Heuristics for Combinatorial Search (2026)

Very recent work on training neural heuristics for combinatorial search problems with
empirical admissibility guarantees. Cited as the current state of the art in
learned-heuristic-guided search, the technique family our high-level search belongs to.
[arXiv:2606.04860](https://arxiv.org/abs/2606.04860)

## 3. RL-Lock: Reinforcement Learning for Generating Interlocking Assemblies (2026)

The first reinforcement learning framework for generating interlocking assemblies:
decomposes a target voxel-grid shape into interlocking pieces using structured action
chunking with MCTS-guided policy/value learning. Important as the closest recent
competing work — it addresses generation from a synthetic voxel target, not solving an
existing puzzle's disassembly and not real/scanned geometry, which is precisely the
differentiation our project's solving-side, real-object-grounded approach relies on.
[arXiv:2608.01744](https://arxiv.org/abs/2608.01744)

## 4. Manifold-Guided Motion Planning for Tight Assemblies (2026)

Introduces Critical-Manifold-Guided RRT (CMG-RRT), a sampling-based motion planner for
rigid-body assemblies with near-zero-clearance contact constraints, including
rotational motion. Reports the first fully automatic solution to the well-known "Elk"
disentanglement puzzle, with open-source code released. This is the core low-level
motion-planning oracle our project builds on directly for real curved-path extraction.
[arXiv:2607.17898](https://arxiv.org/abs/2607.17898) ·
[Code](https://www.cgl.cs.tau.ac.il/projects/tight-assembly-planning)

## 5. Hybrid Task and Motion Planning with Reactive Collision Handling for Multi-Robot Disassembly: Application to EV Batteries (2026)

Combines discrete task-level sequencing with continuous motion planning for real
industrial disassembly (electric-vehicle battery packs), including reactive collision
handling. Direct precedent for our project's two-layer architecture (discrete
high-level ordering search + continuous low-level motion planning), and evidence this
pattern is active and industrially relevant, not just an academic construction.
[Frontiers in Robotics and AI](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2026.1857847/full)

## 6. Reinforcement Learning Approach for Decision Making in Disassembly Processes (2025)

Applies deep RL to sequence disassembly decisions for complex products, evaluating
against classical planning baselines. Relevant supporting evidence that learned methods
are being actively applied to disassembly-sequencing decisions, the same category of
problem as our high-level "which piece next" search.
[Journal of Intelligent Manufacturing](https://link.springer.com/article/10.1007/s10845-025-02622-4)

## 7. Motion Planning Diffusion: Learning and Adapting Robot Motion Planning with Diffusion Models (2024)

Uses diffusion models to learn and adapt robot motion-planning trajectories, an
alternative current SOTA direction for injecting learning into motion planning beyond
heuristic-guided search. Included as a comparison point / discussion of alternative
architectures we considered and why we chose the heuristic-guided-search approach
instead (better fit for the discrete "which piece" decision layered on top of a
geometric planner).
[arXiv:2412.19948](https://arxiv.org/abs/2412.19948)

## 8. Diffusion Models for Robotic Manipulation: A Survey (2025)

Recent survey covering how diffusion models are being applied across robotic
manipulation and planning tasks. Used to confirm the current SOTA landscape for
learned motion planning broadly, situating our chosen heuristic-guided-search approach
within it.
[Frontiers in Robotics and AI](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2025.1606247/full)

## 9. Integrating Active Sensing and Rearrangement Planning for Efficient Object Retrieval from Unknown, Confined, Cluttered Environments (2024)

Addresses a closely related real-world problem: deciding which object to move first in
a cluttered scene to retrieve a target, combining active sensing with rearrangement
planning. Evidence that the "which item to move first, given a limited/expensive
ability to test candidate moves" problem our project targets for puzzles generalizes
directly to real robotic manipulation in clutter (bin-picking, warehouse robotics),
supporting the project's broader applicability beyond the puzzle domain.
[arXiv:2411.11733](https://arxiv.org/html/2411.11733v1)

---

## Foundational context (older than 3 years, not counted toward the recency requirement)

- **DeepCubeA** (McAleer et al., *Nature Machine Intelligence*, 2019) — the original
  learned-heuristic-guided search method (solves Rubik's Cube, 15-puzzle, and Sokoban
  from scratch via approximate value iteration + batch weighted A*). Our high-level
  search is a direct generalization of this pattern to general interlocking-puzzle
  disassembly ordering.
  [GitHub](https://github.com/forestagostinelli/DeepCubeA)
- **Assemble Them All: Physics-Based Planning for Generalizable Assembly by
  Disassembly** (SIGGRAPH Asia 2022) — arbitrary-shape, 6-DOF (translation+rotation)
  disassembly planning via physics-simulated BFS over discretized canonical actions.
  Retained in our project as a classical, discretized-action ablation/baseline to
  quantify what true curved-path planning (via CMG-RRT) gains over it.
  [arXiv:2211.03977](https://arxiv.org/abs/2211.03977)
