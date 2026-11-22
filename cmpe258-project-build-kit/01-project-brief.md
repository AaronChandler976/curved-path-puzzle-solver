# Project Brief (as of 2026-11-14)

## One-paragraph summary

Solo CMPE 258 Option 1 project. Disassembly planning is split into two layers. A discrete layer decides which part to try removing next. A continuous motion-planning oracle (CMG-RRT, open source, 2026) decides whether that part can actually be extracted, including curved/rotational, near-zero-clearance motion, and returns the path. Each oracle call is expensive. The deep-learning contribution is a learned ranker (GNN over a part-contact graph) that orders oracle queries so a full disassembly takes fewer calls and less time than random, geometric-heuristic, or MLP ordering with the same planner.

## Status

- Proposal assignment: submitted (repo + README, literature survey, proposal document, AI novelty/feasibility audit). The repo is github.com/AaronChandler976/curved-path-puzzle-solver.
- Professor feedback received: **revise before implementing** (details in 02). The two problems he raised: the puzzle-only evaluation doesn't support the industrial-disassembly motivation, and the DeepCubeA backward-rollout training data may not be physically valid.
- Implementation: not started. CMG-RRT source has been read (see 04) but the smoke test has not been run or reported.
- **The revision decision is open.** It is the first thing to settle.

## What carries over from the original plan

- Two-layer architecture: learned ordering + expensive curved-path oracle.
- CMG-RRT as the oracle; its bundled puzzles (`elk` etc.) remain useful hard test cases.
- GNN vs MLP heuristic comparison (architectural intervention).
- Oracle-call reduction as the primary metric (efficiency intervention).
- Results split by translation-only vs rotation/curved-required cases.
- Caching oracle results per (part, assembly-state).
- A discretized planner (Assemble Them All style) as a cheaper ablation/dev stand-in.

## What is superseded

- DeepCubeA-style approximate value iteration from random backward rollouts. The professor flagged that randomly adding parts back doesn't guarantee valid, re-assemblable states.
- The Phase A / Phase B curriculum as justified in the proposal. A cheap-oracle pretraining phase may still be useful, but it needs re-justifying under the new training formulation.
- Puzzles as the only data and evaluation domain.
- The 12-week timeline in the old implementation plan (written for a September start).

## Hard constraints

1. Curved/rotational motion must remain in the final result (Aaron's requirement).
2. No fabricated or simulated results. Only real runs with logs.
3. Option 1: training, ≥2 recent open-source SOTA models/methods, ≥2 interventions, evaluation-first with baselines and a working demo.
4. Must differentiate clearly from ASAP (ICRA 2024) and Cebulla et al. 2023 (see 03).

## Environment

- **Primary compute:** Ubuntu desktop. RTX 5070 Ti 16 GB (Blackwell; needs a PyTorch build with CUDA 12.8+), Ryzen 9 9900X (12 cores, useful for parallel planner calls), 64 GB RAM. Native Ubuntu, not WSL.
- **Env manager:** conda.
- **Optional:** SJSU CoE HPC (P100 on HPC1; A100/H100 nodes on HPC2/HPC3; needs VPN). Nice to have, not load-bearing.
- **Claude cloud sandbox:** PyPI and conda-forge were blocked there in Sept 2026. Code is written there or by Claude Code and run on the desktop.
- **Local folder:** ~/SJSU/FALL_2026/CMPE_258/CMPE_258_PROJECT

## Open questions (resolve early)

1. Final deadline and required final deliverables (report? presentation? demo video? repo state?). There's no final-project assignment sheet in this project yet. With about 4–5 weeks likely left in the semester, the plan has to fit that window.
2. Which revision direction (02, section 3).
3. Whether to email Dr. Liu the revised plan for a quick sanity check before building.
4. Whether to rename the repo if puzzles stop being the main domain.
