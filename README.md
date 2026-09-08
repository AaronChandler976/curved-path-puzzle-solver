# Curved-Path Puzzle Solver: A Learned Heuristic for Motion-Planning-Guided Disassembly

**Course:** CMPE 258-02, Deep Learning — Fall 2026, San Jose State University
**Track:** Option 1 — Modern Deep Learning Pipeline (Training + Deployment)
**Team members:** Aaron Chandler

## Abstract

Interlocking and cast-metal puzzles are typically solved by hand, through trial and
error, or — for the narrow case of axis-aligned "burr" puzzles — by classical
combinatorial search tools that cannot represent rotational or curved extraction
moves. We propose a learned-heuristic disassembly solver for **arbitrary-shape**
interlocking puzzles that require genuinely **curved, non-axis-aligned motion**
(rotation, screw motion, rotate-then-slide sequences), not just translation. The
system uses a two-layer architecture: a graph neural network, trained via
DeepCubeA-style approximate value iteration, predicts which piece is most promising
to try extracting next from the current assembly state; a classical sampling-based
motion planner (built on the recent Critical-Manifold-Guided RRT method) answers
whether a real, collision-free — and possibly curved — path exists to extract that
piece, treating the rest of the assembly as static. Because each motion-planning
query is computationally expensive, the learned heuristic's job is to minimize how
many queries are needed to find a full disassembly sequence, compared to an
uninformed search baseline. We evaluate on procedurally generated puzzle families
(including a rotation/curved-motion-required subset) and on a small set of
real, CAD-modeled or scanned physical puzzles, comparing a graph neural network
heuristic against a flat MLP baseline and against a cheaper discretized-action
ablation, with success measured in motion-planning query count, wall-clock time, and
generalization from synthetic to real puzzles.

## Selected track

**Option 1 — Modern Deep Learning Pipeline (Training + Deployment).** The project
trains and compares neural network architectures (an MLP baseline and a graph neural
network) as a search heuristic, evaluated against classical non-learned baselines,
satisfying the required SOTA-comparison and meaningful-model-improvement components
via two interventions: an architectural change (GNN vs. MLP heuristic) and an
efficiency improvement (reducing expensive motion-planner queries).

## Repository contents

- `docs/literature-survey.md` — summary of 9 recent (last 1-3 years) papers/models
  relevant to this project's technical approach.
- `docs/ai-novelty-feasibility-audit.md` — AI-assisted critique of this project's
  novelty, red-ocean/saturation risks, and feasibility, produced during topic scouting.
- `docs/proposal-document.md` — problem formulation and proposed technical approach
  (mirrors the version submitted separately on Canvas).

## Status

Project proposal stage. Implementation has not yet begun.
