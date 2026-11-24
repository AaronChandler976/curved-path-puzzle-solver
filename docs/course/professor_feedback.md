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
| realistic CAD geometry | Fusion 360 assemblies (Assemble Them All / ASAP), 3–12 parts |
| valid states from known feasible sequences | states reached by forward disassembly with planner-verified (path-validated) removals |
| GNN ranks the next expensive query | GNN over the contact graph scores parts; queried in p/c order |
| compare random / heuristics / MLP / GNN, same planner | all orderings use oracle v2 (pre-check → CMG-RRT), same T |
