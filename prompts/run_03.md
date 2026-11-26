# Run 03: the real experiment (GNN vs baselines on pilot_v1)

You are running unattended on Aaron's Ubuntu desktop. Nobody will answer
questions until the run ends. Read `CLAUDE.md` and `docs/PLAN.md` first (both
have new run-03 sections at the bottom) and follow them exactly. Their hard
rules outrank anything in this prompt.

**Run folder:** `reports/run03/`. STATUS.md, REPORT.md, BLOCKERS.md,
DECISIONS.md and figures/ go there.

## What this run must produce
The course deliverable: a fair, logged comparison of learned query orderings
against baselines, all using the same CMG-RRT oracle. Aaron's decisions for
this run:
- The 1,033 interpenetrating assemblies stay **excluded** (report it as a
  limitation).
- Training uses **early stopping, weight decay and dropout**. Models are
  selected on **validation planner cost**, not validation loss.
- **Rotation-required** = CMG-RRT succeeded AND a straight-line pull along
  every candidate direction fails.
- ASAP's GNN is a **required** external baseline (it is the course's second
  open-source SOTA method).
- The 4 h `elk` run and the multi-seed exact-vs-learned SDF test are **NOT**
  part of this run. They belong to run 04.

## Working rules (same as before)
- **Never stop to ask.** Decide, record the choice in
  `reports/run03/DECISIONS.md` (choice, alternatives, why), and keep going.
- **Keep `reports/run03/STATUS.md` current.** Format:
  ```
  STATE: RUNNING            (or DONE when R8 is complete)
  DEADLINE: <ISO time from the launch message>
  CURRENT STAGE: R<n> <name>
  BACKGROUND JOBS: <pid> <what> <log path>   (one per line, or "none")
  DONE SO FAR: <bullets with evidence paths>
  NEXT ACTION: <exact next step>
  ```
- **On start,** read STATUS.md, check whether the listed PIDs are alive, and
  resume. Don't redo finished work.
- **Timebox every stage.** After 3 failed fix attempts on the same error,
  record it in BLOCKERS.md and move on.
- **Gates pass only with evidence on disk.**
- **Commit** after each stage and push the branch.
- **Start R8** no later than 45 minutes before DEADLINE.
- **Priority if time runs short:** R1–R5 (the core result) > R6 (live
  evaluation) > R7 (demo). Shrink R6 before you skip R5.

## Stages

### R0 Orient (≤ 20 min)
- Read `reports/run02/REPORT.md` and `reports/run02/DECISIONS.md`, the v1 label
  schema, and run 02's R6 pipeline-test code. Reuse that code; don't rewrite it.
- Check the machine load: `uptime`, `nvidia-smi`, and `pgrep` for other heavy
  jobs. Record what you find in STATUS.md. Stages R1–R5 don't report
  wall-clock timings and may run under load. R6 may not (see R6).

### R1 Rotation-required labels (≤ 1.5 h)
- `src/disasm/oracle/linear_precheck.py`: for a (state, part) query, sweep the
  part in a straight line along each goal-candidate direction the adapter
  would use, out to the same goal distance. Use the exact union-SDF detector
  with the same ε, checking at a step ≤ ε/2. Record the step size used.
  Output: `linear_free` (bool) and the first direction that clears.
- Run it, using planner slots, on **every** v1 query (successes and unsolved).
  Write `data/labels/pilot_v1/precheck.jsonl`, keyed like the labels.
- Definitions:
  - `needs_rotation = (CMG-RRT success) and (linear_free == False)`
  - State-level: `rot_state` = at least one successful part at that state
    needs rotation.
  - Assembly-level: `rot_assembly` = any state is a rot_state.
- Report in `reports/run03/rotation.md`:
  - the counts of parts, states and assemblies that need rotation;
  - **inconsistencies**: `linear_free == True` but CMG-RRT unsolved. Give the
    count, examples, and what they imply about the oracle at T = 30 s.
- **Gate:** precheck results exist for 100% of v1 queries, and the counts are
  reported.

### R2 Dataset + frozen split (≤ 1 h)
- One graph per labeled state:
  - nodes = remaining parts; edges = contacts in that state, with edge
    features (contact area, mean normal);
  - node features as in docs/PLAN.md, plus a flag for whether the part was
    queried;
  - per-node targets: outcome, time_s and a censored flag (unsolved = censored
    at T).
  The rotation flags are kept for evaluation only, **never as inputs**.
- **Duplicate check:** Fusion 360-derived sets can contain near-identical
  assemblies. Group assemblies whose sorted part-mesh hashes match (or are
  near-identical by volume+bbox signature) and **split by group**.
- Split groups 70/15/15 (train/val/test) with a fixed seed, stratified by
  part-count bin and by rot_assembly. Save it to `data/splits/v1_split.json`
  **and commit that file**, since it's small.
- Gate:
  - no assembly or group appears in two splits (assert in a test);
  - split sizes and rot counts reported in `reports/run03/dataset.md`.
- **The test split is not touched until R5.**

### R3 Models + training (≤ 3.5 h)
- Variants:
  - **MLP** (per-node; same features, no message passing)
  - **GNN** (GINE with edge features, residual, LayerNorm)
  Each gets two heads:
  - **BCE** (P(success)): orders parts by p (the removability-only objective
    of ASAP/Cebulla);
  - **Survival** (discrete-time hazards over K = 8 log-spaced bins up to T,
    censoring-aware NLL): orders by p/c, where p = P(solved by T) and
    c = E[min(time, T)].

  Extra ordering ablation, with no new training: the **survival model ordered
  by p only**. This separates the effect of the objective from the effect of
  the ordering rule.
- Training: AdamW with weight decay, dropout, gradient clipping. Early
  stopping on the **validation metric** = total replay planner cost over val
  states (computed every epoch), with patience. Save the best checkpoint.
- **Fair, equal tuning budget:** a small grid on val only, the same for each
  of the 4 variants (hidden {64, 128} × lr {1e-3, 3e-4} × layers {2, 3}, or
  equivalent; MLP depth matched). Pick each variant's config by val metric.
  Then train **5 seeds** of each chosen config.
- Log training curves (CSV + PNG) for every run under
  `experiments/<date>_run03_train/`. PointNet embeddings are optional: add
  them only if R1–R5 finish with ≥ 3 h spare, as a separate, labeled variant.
- **Gate:** 4 variants × 5 seeds trained, with the configs and the val-metric
  selection logged.

### R4 ASAP baseline (≤ 2 h; required)
- In `external/ASAP` (yunshengtian/ASAP), find the released GNN checkpoint and
  its input pipeline: point clouds and custom features.
- Build its inputs for our states and use its scores as an ordering
  (zero-shot). Label it "ASAP GNN (released weights, zero-shot)".
- If the weights can't be found or loaded after 3 real attempts: train ASAP's
  architecture, from their code, on our train split with their objective.
  Label it "ASAP architecture, retrained on v1", record why, and use the same
  early stopping.
- **Gate:** at least one ASAP variant produces scores for every test state.
  If both fail, this is blocker #1, because the course requires it.

### R5 Test evaluation by replay (≤ 1 h; run ONCE on the test split)
For every test state, compute each ordering's planner cost to the first
success from the logged v1 queries. Failed queries cost their logged time;
states with no success are reported separately.
- **Orderings:**
  - random (exact expectation);
  - outside-in;
  - fewest contacts;
  - MLP-BCE (p);
  - MLP-Surv (p/c);
  - GNN-BCE (p);
  - GNN-Surv (p/c);
  - GNN-Surv (p only);
  - ASAP;
  - hindsight-optimal (lower bound).
- **Metrics:**
  - total planner time over test states;
  - mean per state;
  - median per-state ratio to optimal;
  - queries to the first success;
  - mean ± std across the 5 seeds for the trained models.
- **Statistics:**
  - bootstrap 95% CIs, resampled by **assembly**;
  - **paired** GNN-Surv-vs-each-baseline differences with a paired bootstrap
    CI and a Wilcoxon signed-rank test over assemblies;
  - Holm correction across the comparisons.
- Everything again on the **rot_state** subset and the non-rot subset. If the
  rot subset has < 30 test states, report it but call it underpowered.
- **Calibration and prediction quality:**
  - reliability diagram + ECE for p;
  - concordance index (censored) for time predictions;
  - all for the BCE and survival heads.
- Output `reports/run03/results_replay.md`: a main table, a paired-comparison
  table and figures (bar chart with CIs, reliability plot).
- **Report every variant you trained.** No seed or variant cherry-picking.

### R6 Live full-disassembly evaluation (≤ 3 h; timed, so the machine must be idle)
- **Before starting,** wait until no other heavy job is running: load average
  < 2 and GPU utilization < 10% for 5 minutes, checking every 10 min for up to
  2 h. If it never goes idle, run anyway and mark every timing as confounded.
- Sample 60 test assemblies with a fixed seed, stratified by part count, and
  include every rot_assembly in the test split, up to 20 of them.
- **Methods:** random, fewest contacts, ASAP, GNN-Surv (seed chosen by **val**
  metric, not test).
- Real AbD with **fresh CMG-RRT queries**, T = 30 s:
  - query parts in the method's order until one succeeds, remove it, repeat
    until done or stuck;
  - planner seed per query = hash(assembly, state_key, part), so the same
    query gets the same seed under every method;
  - interleave methods per assembly;
  - ≤ 10 workers via slots.
- **Metrics per assembly:** total planner time, planner calls, solved or not,
  and wall time with setup. Report paired comparisons only over assemblies
  completed by all methods, with CIs as in R5.
- Output `reports/run03/results_live.md`, with load info logged at the start
  and end.

### R7 Demo asset (≤ 45 min)
Pick one test assembly (prefer a rot_assembly). Render:
- the GNN-Surv query order with p and c per part;
- each query's outcome;
- the extraction paths, animated.

Save a GIF (imageio) and a PNG strip to `reports/run03/figures/`. If MP4,
encode H.264 with `-preset veryfast`. Write a 3-line caption, with its
numbers taken from the logs.

### R8 Final report (start ≤ 45 min before DEADLINE; mandatory)
`reports/run03/REPORT.md` (≤ about 2 screens):
1. **One line: the answer to the project question so far,** in plain terms,
   with its CI. If the GNN doesn't beat the best heuristic, say so plainly.
2. A gate table (PASS / FAIL / SKIPPED, with evidence).
3. The main replay results table (R5) and the paired comparisons, with
   p-values after Holm.
4. The rotation subset results, and the R1 counts and inconsistencies.
5. Live evaluation results (R6), if they ran.
6. The intervention summary for the course write-up:
   - architectural (GNN vs MLP);
   - efficiency/objective (survival p/c vs BCE p, plus the p-only ablation);
   - SOTA methods used (CMG-RRT oracle, ASAP baseline, Assemble Them All
     data).
7. **Needs Aaron.**
8. Decisions made on his behalf.
9. A proposed run 04: the `elk` 4 h run, the multi-seed SDF test, and
   anything this run left open.

Set `STATE: DONE`, then commit and push.
