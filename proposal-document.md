# Project Proposal: Curved-Path Puzzle Solver via Learned-Heuristic-Guided Motion Planning

**Track:** Option 1 — Modern Deep Learning Pipeline (Training + Deployment)

## Problem Formulation

**Domain problem.** Interlocking and cast-metal puzzles are solved by manual trial and
error, or, for the narrow case of axis-aligned "burr" puzzles, by classical
combinatorial tools (e.g. BurrTools) that cannot represent rotational or curved
extraction moves. Many real puzzles — and many real disassembly tasks in
manufacturing, recycling, and maintenance — require a piece to rotate or trace a
curved path before it can be removed. We address: given a 3D model of an assembled
interlocking puzzle (arbitrary piece shapes, arbitrary contact geometry), find a valid
disassembly sequence, where each individual extraction move may require curved,
non-axis-aligned rigid-body motion, using as few expensive geometric search operations
as possible.

**Input/output specification.**
- *Input:* mesh geometry for each puzzle piece (from CAD or 3D scan) in its assembled
  pose.
- *Output:* an ordered sequence of piece extractions, each paired with a concrete,
  collision-free 6-DOF motion path (translation and/or rotation) that removes it,
  given the remaining pieces held static.

**Success criteria / target metrics.** (1) Solve rate: fraction of held-out puzzles
fully disassembled within a fixed budget. (2) Query efficiency: number of calls to the
underlying motion-planning oracle needed to find a full disassembly, compared to an
uninformed search baseline using the same oracle — this is the primary metric, since it
directly measures the value the learned component adds. (3) Wall-clock time to
solution. (4) Generalization gap between models trained only on synthetic puzzles and
models fine-tuned on a small set of real, physically-modeled puzzles. Metrics are
reported separately for translation-only vs. rotation/curved-motion-required puzzles,
to directly evidence that the system handles genuine nonlinear motion, not an
approximation of it.

## Proposed Technical Approach

**High-level architecture.** A two-layer system. (1) A discrete high-level search
decides which piece to attempt extracting next, given the current assembly state
(which pieces remain, and their contact relationships). This search is guided by a
trained neural network that estimates how much work remains from a given state,
analogous to DeepCubeA's learned heuristic for Rubik's Cube. (2) Each candidate
extraction is checked by a continuous, curved-path motion-planning oracle — Critical-
Manifold-Guided RRT (CMG-RRT), from the 2026 open-source "Manifold-Guided Motion
Planning for Tight Assemblies" — which either returns a real collision-free path
(rotation included) or reports failure. Decomposing the problem this way keeps the
expensive, high-dimensional part of motion planning (searching one piece's continuous
6-DOF pose space against static obstacles) tractable, while leaving the combinatorial
"which piece, in what order" decision to the learned component.

**Chosen models and required interventions.** Two heuristic architectures are trained
and compared, satisfying the two required Option 1 interventions: (1) *Architectural
change* — a graph neural network (nodes = pieces, with pose and shape features; edges =
current contact) versus a flat MLP over concatenated piece poses (the DeepCubeA-style
baseline representation), evaluated for generalization across puzzles of different
piece counts and shapes. (2) *Efficiency improvement* — the learned heuristic's
explicit objective is minimizing motion-planning oracle calls versus an uninformed
ordering search, which matters because each oracle call is computationally expensive,
unlike a simple table lookup.

**Data sources.** Procedurally generated synthetic puzzle families of varying piece
count and contact structure, with a training subset deliberately constructed to require
rotational/curved extraction (e.g., keyed contacts that clear only at a specific
angle) so the model is not merely translation-solvable. A small held-out set (5-15
puzzles) of real puzzles, CAD-modeled from physical measurements or 3D-scanned, used to
evaluate synthetic-to-real generalization.

**Baselines.** DeepCubeA-style MLP heuristic; uninformed/greedy ordering search using
the same CMG-RRT oracle; a cheaper discretized-action ablation (translate/rotate in
fixed increments, physics-checked via PyBullet, following "Assemble Them All") to
quantify what true curved-path planning gains over a discretized approximation.

**Evaluation-first plan.** Every claim is backed by a working demo (an animated,
CMG-RRT-derived disassembly of a real puzzle requiring curved extraction) and
quantitative metrics (oracle-call counts, solve rates, wall-clock time), logged across
training runs, consistent with the course's evaluation-first requirement.
