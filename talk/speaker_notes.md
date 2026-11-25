# Speaker notes (10 minutes, about 45 s per slide; 13 slides + backup)

Every number on the slides comes from `reports/final_eval/` (test, evaluated once) or an earlier logged run, which
the slide footers name. Speak to the picture, not the bullets.

1. **Title (15 s).** "Robots that take products apart for recycling have to keep asking a motion planner one question:
   can this part come out? This talk is about which part to ask about next."
2. **Application (45 s).** Teardown or recycling needs a removal sequence for real CAD. In assembly-by-disassembly we
   ask CMG-RRT, a tight-clearance SE(3) planner, about one part at a time. A straight pull answers in hundredths of a
   second; a timeout burns 30 s and proves nothing. The part might still come out, so a timeout is a censored
   observation.
3. **Problem (45 s).** The cost of a state is the planner time until the first success. Classic result: for
   independent tests you query in order of p over c, success probability over expected cost. So we need a model that
   predicts both, with timeouts handled as censored data. It must also be cheap: it runs once per state on a CPU.
4. **Landscape (45 s).** Cebulla et al. and ASAP learn removability, i.e. which part comes out, and their testers are
   simulators. CMG-RRT is the open-source planner we use as the oracle. Nobody models what a query costs. That is our
   gap and our claim. We don't claim "a GNN predicts the next removable part"; ASAP already does that.
5. **Pipeline (45 s).** CAD → contact graph → GINE GNN with a survival head over 8 time bins → order by p/c → oracle,
   which is a straight-pull check, then CMG-RRT if needed. Remove the first success and repeat. Ablations: MLP instead of
   the GNN, a BCE head instead of survival, PointNet features, a tail-aware loss. Baselines: random, two heuristics,
   ASAP zero-shot and ASAP retrained on our labels.
6. **Data (45 s).** This answers the professor's feedback. We use real Fusion 360 products and states that are reached
   by verified removals, so the states are physically valid. That gives 41,913 labelled queries over 2,022 assemblies.
   We fixed the planner adapter first: it never tried the straight pull from the start, and about a fifth of its
   successes went through parts. The protocol was pre-registered, and the fresh test set of 347 assemblies, half of
   them large, was evaluated exactly once.
7. **Main result (60 s).** Bars are total planner time on the test set. GNN-Surv is far below random and 35–40% below
   both ASAP models (39% below zero-shot, 34% below retrained). Against the simple heuristic "fewest contacts first" it is a tie: 1.055, with a CI that
   includes 1. Our pre-registered rule therefore says "does not beat". I report that as is.
8. **Ablations (45 s).** The cost-aware head is the part that helps: same GNN, survival p/c instead of BCE p, 11%
   less planner time, significant after Holm. GNN vs MLP, PointNet and the tail loss show no detectable difference on
   test. Lesson: validation favoured the variants we had tuned most, and cross-validation and the test did not confirm
   them.
9. **Live (45 s).** Fresh CMG-RRT queries, full disassemblies, same methods (filled in from `live.md`).
10. **Budget policy (45 s).** The biggest win was not learned. Give every part 3 s first and retry at 30 s only if
    nothing comes out. Planner time drops 72% for every ordering. Under that policy, learned and heuristic orderings
    show no detectable difference.
11. **Latency (30 s).** The ranker costs about 2.5 ms per state on one CPU thread. One avoided timeout pays for
    about 12,000 calls. Deploying it costs nothing measurable; the question is only whether it orders well.
12. **Failure analysis (45 s).** Nearly all of the loss against the heuristic comes from 85 states where the model
    confidently queried a part that then timed out: for the part queried first it predicted 0.90–1.00
    success and at most 3.7 s cost. These are large
    assemblies, and the model was trained mostly on 3–8 parts. That is a distribution shift, and validation was too small
    in those sizes to show it.
13. **Negative results (45 s).** The planner adapter was the first bug. A learned collision model "solved" a puzzle by
    going through the part. 95–98% of successes are straight pulls, so timeouts dominate the cost. Pre-registration is
    what kept us honest about all of this.
14. **Summary (30 s).** Cost-aware ordering beats removability-only ordering and both ASAP baselines. It does not beat
    a contact heuristic on bigger, unseen products. A 3-second first pass is a 72% saving for everyone. Next steps:
    train on large assemblies and learn per-part budgets from the survival curve.

Timing check: 15 + 12 × 45 + 60 + 30 + 30 ≈ 675 s ≈ 11 min at 45 s per slide. Trim slides 4 and 11 to 30 s each
→ about 10 min. Rehearse with a timer.

## Likely questions
1. **"Why doesn't the GNN beat fewest contacts if its predictions are good?"** Its C-index is only 0.67 within a state,
   and the total is dominated by rare timeouts. A few confident mistakes on large, unseen assemblies cost more than all
   its small wins (436 cheaper states saved 3,240 s; 85 timeout-first states lost 3,153 s).
2. **"Isn't the 3-second policy just tuning?"** It was chosen on validation from three pre-listed values. It helps every
   ordering by the same mechanism, cutting off timeouts, and it is labelled exploratory because it came after
   pre-registration. It is a planner-usage policy, not a learning result.
3. **"How do you know the timings are clean?"** An idle guard pauses dispatch while anything else uses the machine.
   Every query records how busy the machine was, and confounded runs are re-run with the same seed. Only the first
   clean attempt is reported.
