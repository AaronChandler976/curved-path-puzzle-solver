# Professor feedback on the proposal (Dr. Liu)

(Verbatim summary, copied from the campaign prompt `prompts/campaign.md`, appendix.)

The puzzle application is niche and the link to industrial disassembly (EV battery teardown, recycling) is
indirect; move evaluation to simulated mechanical assemblies or battery/module tasks with realistic CAD geometry,
keeping the learned query-ordering + motion-planning framework. DeepCubeA-style backward rollouts don't guarantee
physically valid states; instead use assemblies with known feasible (dis)assembly sequences and train a GNN to rank
which component gets the next expensive motion-planning query. Compare random ordering, simple geometric/contact
heuristics, an MLP and the GNN using the same motion planner.

## How each point is addressed (kept current)
| point | where it is addressed |
|---|---|
| link to industrial disassembly (EV battery teardown, recycling) | realistic mechanical CAD (Fusion 360) instead of puzzles; framed as the planning-query cost of automated disassembly. No battery-module CAD in the evaluation (optional Phase 2 case study, qualitative only) |
| realistic CAD geometry | Fusion 360 assemblies (Assemble Them All / ASAP), 3–12 parts |
| valid states from known feasible sequences | every state is reached from the real assembled product by planner-found, path-validated removals, so every state is physically valid. The sequences are found by our planner, not given by the dataset, and 156/2,022 assemblies get stuck before full disassembly (reported) |
| GNN ranks the next expensive query | GNN over the contact graph scores parts; queried in p/c order |
| compare random / heuristics / MLP / GNN, same planner | all orderings use oracle v2 (pre-check → CMG-RRT), same T |
