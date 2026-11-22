# Decision Log

Newest first. Keep entries short: date, decision, why.

## Open

- **Revision direction:** R1 / R2 / R3 (see 02, section 3). Not decided.
- **Novelty angle vs ASAP/Cebulla:** pick from 03, section 3. Not decided.
- **Final deadline and final deliverables:** unknown; get from Canvas.
- **Repo rename:** pending the revision decision.

## Decided

- **2026-11-14:** Moved project build work to a dedicated Claude project (this one). The "Research Topic Scout CMPE_258" project stays for topic scouting only.
- **2026-11-14:** Professor feedback received: revise before implementation (application + training formulation). DeepCubeA backward-rollout training dropped. The professor's comparison set adopted: random, geometric/contact heuristic, MLP, GNN, same planner.
- **2026-11-14:** Found that ASAP (ICRA 2024) and Cebulla et al. 2023 already train GNNs for next-part removability. The contribution must be framed as something beyond that (03).
- **2026-11 (early):** Primary compute is the Ubuntu desktop (RTX 5070 Ti 16 GB, 64 GB RAM), native Linux, conda. No WSL. (Replaces the Sept plan of laptop + WSL2.)
- **2026-09-10:** CMG-RRT source located and read; the goal-pose input gap identified (04).
- **2026-09-08:** Proposal submitted: repo, README, literature survey, proposal doc, AI novelty audit.
- **2026-09-08:** **Curved-path/rotational motion is non-negotiable.** Aaron: "I won't do this project if it's only a burr 6 dof." Discretized planning is allowed only as an ablation or dev stand-in.
- **2026-09-08:** Solo project, Option 1 (Modern DL Pipeline, training required).
- **2026-09-08:** Two-layer architecture adopted: learned ordering + CMG-RRT oracle.
- **2026-09-08:** Rejected burr/voxel/translation-only scope.
