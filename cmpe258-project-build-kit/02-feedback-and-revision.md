# Professor Feedback and Revision Plan

## 1. Feedback (verbatim, Dr. Liu, received Nov 2026)

> The proposal has an interesting learned-search idea, but I recommend reconsidering both the application and the training formulation. The current puzzle-solving application is quite niche, and the connection from interlocking puzzles to industrial disassembly (e.g., EV battery teardown or recycling) is currently indirect: the proposed data, evaluation, and final demonstration are all puzzle-based, so success would not yet establish that the method is useful for a real disassembly problem. If industrial disassembly is the motivation, I recommend moving the evaluation closer to that application—for example, use simulated mechanical assemblies or battery/module disassembly tasks with realistic CAD geometry, while keeping the same learned query-ordering + motion-planning framework.
>
> There is also a fundamental issue with the proposed DeepCubeA-style training procedure. DeepCubeA can generate scrambled states by applying random backward moves because Rubik's Cube actions are reversible. Starting from a fully disassembled mechanical assembly and randomly adding pieces does not guarantee a physically valid or re-assemblable state, so the proposed backward-rollout training data may not be valid. A safer semester scope is to generate assemblies with known feasible assembly/disassembly sequences and train a GNN to rank which component should receive the next expensive motion-planning query. Compare random ordering, simple geometric/contact heuristics, an MLP, and the GNN using the same motion planner. This keeps the useful deep-learning question—whether learned structural representations can reduce expensive planning calls—without depending on an uncertain DeepCubeA formulation.
>
> Overall, I would revise the project before implementation: either move from puzzles to a more practically motivated disassembly benchmark, or provide much stronger justification for why results on puzzles should transfer to the target application.

## 2. What the feedback requires

1. **Application/evaluation:** either evaluate on realistic mechanical CAD assemblies (simulated mechanical or battery/module tasks), or give much stronger justification for puzzle-to-industry transfer. He clearly prefers the first.
2. **Training formulation:** drop DeepCubeA backward rollouts. Use assemblies with known feasible sequences and train a GNN to rank which component gets the next planner query.
3. **Comparison set (his list):** random ordering, simple geometric/contact heuristic, MLP, GNN, all with the same motion planner.
4. **Keep:** the learned query-ordering + motion-planning framework, and the core DL question (do learned structural representations reduce expensive planning calls?).

## 3. Revision directions (to decide)

**R1: Move to a realistic CAD-assembly benchmark (follows his main suggestion).**
Use the Assemble Them All and/or ASAP datasets: Fusion 360-derived mechanical assemblies, including a two-part rotational set and multi-part sets (see 03). Labels come from offline assembly-by-disassembly runs. Industrial relevance is direct. Risk: ASAP already trains a GNN on this exact data for next-part prediction, so novelty has to come from the oracle and objective (see 03, section 3).

**R2: Keep puzzles and argue transfer harder.**
Least rework. It goes against the professor's stated preference, though, and puzzle-only results would still not "establish usefulness for a real disassembly problem." Not recommended.

**R3: Hybrid. CAD assemblies as the main benchmark, tight/rotational puzzles as a hard-case stress set.**
The industrial CAD set is the main evaluation and answers feedback point 1. CMG-RRT's bundled tight-clearance puzzles (`elk` etc.) and the rotational CAD subset become the curved-motion stress test. This is where the curved-path requirement lives, and it's where ASAP's discretized physics planner is weakest. This also gives a natural domain-adaptation experiment: train on one family, test on the other.

*Claude's initial read (not decided):* R3 answers both feedback points, keeps the curved-path requirement, and gives the clearest differentiation from ASAP. Confirm against the deadline before committing.

## 4. Revised training formulation (applies to R1 and R3)

- **Data with known feasible sequences:** for each training assembly, run an offline assembly-by-disassembly search with the planner and cache every query result. Known-feasible sequences come from the solved runs. ASAP's released data and labels may already provide this for its dataset; check before regenerating.
- **Labels per state:** for parts tested at a state, record success, failure or timeout, plus planning time. Note that only labeling along one sequence biases negatives. Decide how many extra parts per state to test offline (cost: up to N queries per state, about N² per assembly).
- **Model:** GNN over the part-contact graph. Node features are geometric (volume, bounding box, distance to centroid, contact count, contact normals; optionally a PointNet embedding as in ASAP). Output is a per-part score. Loss: per-node BCE (removable or not) or a listwise ranking loss.
- **Inference:** query parts in score order until one succeeds, remove it, update the graph, repeat.
- **Comparison (same planner for all):** random, geometric/contact heuristic, MLP on per-part features (no message passing), GNN. If its code runs, add ASAP's GNN as the external SOTA baseline.
- **Metrics:** oracle calls per full disassembly (primary), wall-clock planning time, solve rate under a fixed call/time budget, all split by translation-only vs rotation/curved-required.

## 5. Things the revised plan must still state explicitly

- What is new compared with ASAP and Cebulla 2023 (03, section 3).
- How CMG-RRT's goal-pose input gets supplied for "extract this part" queries (04).
- How timeouts are treated (failure? censored label?).
- The honest scope limit: parts must be removable one at a time (or as small pre-declared subgroups).
