# Option 1 (train + deploy) requirements, as given in the campaign prompt

- Train models.
- ≥ 2 recent open-source SOTA methods used or compared against: CMG-RRT (oracle), ASAP (baseline, zero-shot and
  retrained), Assemble Them All (data).
- ≥ 2 technical interventions: GNN vs MLP; cost-aware survival vs BCE; plus PointNet features and a tail-aware
  objective.
- Evaluation-first, with baselines and a working demo.
- Novelty vs ASAP and Cebulla 2023: we model query cost and censored timeouts for a curved/rotational SE(3)
  planner and order queries by expected cost. Never claim "a GNN predicts the next removable part" as ours.
