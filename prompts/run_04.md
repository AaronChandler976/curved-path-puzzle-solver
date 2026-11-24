# Run 04: oracle v2, data v2 and a frozen fresh test set

You are running unattended on Aaron's Ubuntu desktop. Nobody will answer
questions until the run ends. Read `CLAUDE.md` and `docs/PLAN.md` first (both
have new run-04 sections at the bottom) and follow them exactly. Their hard
rules outrank anything in this prompt.

**Run folder:** `reports/run04/`. STATUS.md, REPORT.md, BLOCKERS.md,
DECISIONS.md and figures/ go there.

## Why this run exists
Run 03 (`reports/run03/REPORT.md`) answered the project question once, on a
test split that is now spent. Aaron reviewed it and decided to fix what can be
fixed rather than list it as a limitation, even when that costs more compute:
the oracle misses, the weak ASAP baseline, the missing PointNet variant, the
confounded live timings and the small data pool. This run builds the oracle,
the data and the frozen evaluation protocol. **Run 05 trains and evaluates; this
run does not train on v2 and does not evaluate anything on the v2 test split.**

Aaron's decisions for this run:
- Lean toward the more complete and robust method, even if it takes more runs
  or compute time. Prefer fixing a problem over documenting it.
- Run 03 protocol v2 is accepted. Assembly 00014 is disclosed in run 03 and is
  never put in a v2 test set.
- The write-up reports total planner time (primary) and per-assembly paired
  cost side by side.

## Working rules
- **Never stop to ask.** Decide, record it in `reports/run04/DECISIONS.md`
  (choice, alternatives, why), and keep going. The exceptions are the
  explicit "stop and report" points below.
- **Keep `reports/run04/STATUS.md` current** (same format as run 03:
  STATE, DEADLINE, CURRENT STAGE, BACKGROUND JOBS, DONE SO FAR, NEXT ACTION).
- **On start,** read STATUS.md, check whether listed PIDs are alive, and resume.
  Don't redo finished work.
- **This run may span several launches** (the runner may stop at a deadline and
  be started again). Keep STATE: RUNNING until every stage has passed or been
  recorded as blocked. 45 minutes before each DEADLINE, refresh
  `reports/run04/REPORT.md` with progress so far.
- **Timebox every stage.** After 3 failed fix attempts on the same error,
  record it in BLOCKERS.md and move on.
- **Gates pass only with evidence on disk.** Commit after each stage; push the branch.
- **Timed work goes through the idle guard** (CLAUDE.md, Run 04 rules). While a
  timed stage runs, don't train, compile or use the GPU.
- **Stage order matters** because later stages depend on earlier decisions. If
  the machine is busy (Aaron is using it), do untimed stages and come back.

## Stages

### T0 Orient (≤ 20 min)
Read `reports/run03/REPORT.md`, `DECISIONS.md`, `rotation.md`, `results_live.md`
and `reports/run02/REPORT.md`. Record the machine state (uptime, nvidia-smi,
power profile, heavy processes) in STATUS.md.

### T1 Tooling (untimed, ≤ 2 h)
1. **Idle guard** `src/disasm/util/idle_guard.py` exactly as CLAUDE.md defines it,
   with a CLI (`python -m disasm.util.idle_guard --wait-idle 300`) and a sampler
   that planner workers can query. Tests in `tests/`.
2. **Seeded robot sampling.** trimesh's `sample_surface` uses an unseeded
   generator (run 03 DECISIONS #3). Make every planner query draw its robot
   samples from a generator seeded by the query seed: a `seed` argument if the
   installed trimesh supports it, otherwise a patch in `patches/` applied by a
   script (never edit `external/` directly). Test: the same query twice gives
   identical samples and an identical tree.
3. **Wire both** into `scripts/label_abd.py` and `scripts/live_abd.py`:
   per-query `busy_frac`, `confounded`, and re-runs of confounded queries at the
   end (CLAUDE.md).
- **Gate:** tests pass (`env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest`).

### T2 ASAP and PointNet preparation (untimed, ≤ 3 h)
Do this before the timed stages, since it compiles and uses the GPU.
1. **redmax.** Try to install ASAP's redmax simulator into a separate conda env
   (e.g. `asap`) or into `disasm` if versions allow. No sudo: if a system
   package is missing, write the exact `apt install` line to BLOCKERS.md and
   use the run 03 contact adapter as the fallback. If it installs, build ASAP's
   own contact graphs for 20 train assemblies and compare them with our adapter
   (edge agreement), so the effect of the adapter is known.
2. **ASAP retraining dry run.** Find ASAP's training code and objective. Make it
   train for 2 epochs on 50 run 03 *train* assemblies through our data. This is
   only a pipeline check; the real training happens in run 05 on v2.
3. **PointNet inputs.** Write the per-part point-cloud extraction (fixed point
   count, part-local frame, seeded) so run 05 can train PointNet+GNN end to end
   or with a pretrained encoder. Decide which in DECISIONS.md, with reasons.
   Dry-run one forward/backward pass on a run 03 train batch.
- **Gate:** each item works or has a BLOCKERS.md entry with the fallback chosen.

### T3 Unconfounded rerun of run 03's live evaluation (timed, ≈ 30 min)
Rerun run 03 R6 exactly (same 60 assemblies, same 4 methods, same frozen
checkpoints, seed 101 for GNN-Surv), now with the idle guard and seeded robot
sampling. Nothing is tuned: this only replaces confounded timings.
Output `experiments/<date>_run04_live_rerun/` and `reports/run04/live_rerun.md`
in the same table format as `reports/run03/results_live.md`, plus a side-by-side
with the confounded run. Label it everywhere as "run 03 models, development
test set".

### T4 Oracle v2 (timed parts through the guard, ≤ 4 h)
1. **Path validation.** Re-check every successful v1 query that has a saved path,
   and the live-run paths, edge by edge with the exact detector at step ≤ ε/2.
   If v1 paths weren't saved, validate a re-run sample of ≥ 500 successes
   instead. Report how many successes are invalid at fine resolution. The goal
   connection check uses a coarse discretisation (`n = dist/eta // 10` in
   `src/disasm/oracle/cmgrrt.py`), so invalid successes are possible.
2. **Diagnose the 124 misses** (`reports/run03/rotation.md`). Find the actual
   cause, not a guess. Candidates: the start pose is never tested for a straight
   connection to every goal; the tree is biased toward goal 0; the goal-edge
   discretisation; a threshold mismatch between the pre-check and
   `is_edge_valid`. Fix it in our adapter (not in `external/`). If the
   discretisation is too coarse, make goal-edge checks use step ≤ ε/2 too.
3. **Oracle v2** = straight-pull pre-check (`src/disasm/oracle/linear_precheck.py`,
   now with its time counted) → CMG-RRT with the fixed adapter if no straight
   pull clears. For labels, **always** also run CMG-RRT, even when the pre-check
   clears, and record both results and times, so both oracle configurations can
   be replayed.
4. **Validation set:** the 124 misses + 500 random v1 queries (seeded), run
   through oracle v2. Report: misses recovered, success rate and time vs v1,
   path-validation results, pre-check vs CMG-RRT share.
- **Gate:** ≥ 95% of the 124 are now solved (or each remaining one is explained
  with evidence), and 0 invalid successes at fine resolution in the validation set.
  Also add tests for the fixed bug.

### T5 Exact vs learned SDF on tight puzzles (timed, alone, ≤ 3 h)
Bundled puzzles 16505 and alpha, **3 seeds × {exact, learned}**, authors'
`test_list.json` settings, one run at a time, through the guard. If the exact
detector is clearly worse, implement the fix from run 02: exact SDF for every
collision decision, a smoothed SDF only for CMG-RRT's guidance gradient. Re-test
it on the same seeds, and on a 200-query ATA sample to show it is no worse there.
Adopt it in oracle v2 only if both hold; record the decision. If time allows,
add the other bundled examples with 3 seeds × both detectors.
**This stage must finish before T7**, because it can change the oracle.

### T6 Fresh data pool (mostly untimed, ≤ 3 h)
1. **Count** what's available beyond pilot_v1: 9–12-part assemblies (use
   `experiments/2026-11-22_contact_scan/`), and the 1,033 interpenetrating ones.
2. **Per-pair penetration allowance** for the interpenetrating assemblies:
   each pair that overlaps at the start pose gets an allowance of its measured
   start penetration + ε, capped (pick the cap from the penetration distribution
   and record it). Pairs that don't overlap keep ε. Validate it: on 50 recovered
   assemblies, check that start poses are valid, that successful paths don't
   pass through parts (fine-resolution path check with the global ε), and spot-
   render 5. Assemblies over the cap stay excluded, with counts.
3. **Estimate the labelling cost** of each source from a 30-assembly pilot
   (queries per assembly, planner hours at 10 workers). Choose how much of each
   to label so the v2 test set can have **≥ 250 fresh assemblies**, stratified by
   part count, and so labelling fits in about 12 planner-hours (10 workers). Record the plan.
- **Stop and report** (put it in "Needs Aaron", carry on with T9 and T10) if the
  fresh pool can't give ≥ 150 test assemblies.

### T7 Label `pilot_v2` (timed, through the guard; the longest stage)
- All 1,328 v1 assemblies relabelled from scratch with oracle v2 (forward
  disassembly; every remaining part queried at every visited state; one random
  success removed, logged seed), plus the fresh assemblies chosen in T6.
- Order: fresh assemblies first (they decide the test set), then v1.
- Checkpointed and resumable. Re-run confounded queries at the end.
- Output `data/labels/pilot_v2/` with the same schema as v1 plus: precheck result
  and time, CMG-RRT result and time, path-validation flag, busy_frac, confounded,
  source (v1 / fresh-9to12 / fresh-allowance), allowance used.
- `reports/run04/labels_v2.md`: counts, success rates per source and size bin,
  v1 vs v2 on the same assemblies, pre-check share, confounded count.
- **Gate:** every planned assembly labelled or listed as failed with a reason;
  confounded queries < 1% after re-runs.

### T8 Frozen v2 split and pre-registration (untimed, ≤ 1.5 h)
1. **Split** `data/splits/v2_split.json` (commit it): duplicate groups as in
   run 03 (#6), across the whole v2 pool. The **test set = fresh assemblies only**
   (never in pilot_v1), about half of the fresh pool, stratified by source and
   part-count bin. The rest of the fresh pool and all v1 assemblies go to
   train/val (85/15 by group). Assert in a test: no group in two splits, no
   pilot_v1 assembly in test, 00014 not in test.
2. **Pre-registration** `docs/PREREG_run05.md`, written and committed **before any
   v2 training**:
   - the variants (PLAN.md, Run 04 additions), the shared tuning grid and budget,
     5 seeds each, and the selection rule (run 03 protocol v2, val only);
   - the tail-aware objective, defined exactly;
   - primary metric (total planner time) and co-reported paired metric (HL
     median difference, wins/ties/losses), both for replay and for live;
   - the comparisons, CIs (bootstrap by assembly), tests (Wilcoxon), Holm;
     subsets (rot_state, source, part-count bin) and which are underpowered;
   - the live evaluation: every test assembly, all methods, all 5 seeds of each
     trained model, idle guard on;
   - both oracle configurations (pre-check → CMG-RRT as the main one,
     CMG-RRT only as the secondary one);
   - what counts as "GNN-Surv beats the best heuristic" before seeing results.
- **Gate:** split committed, tests pass, PREREG committed with a timestamp
  earlier than any v2 training run.

### T9 elk reproduction (timed, alone, 4 h)
One 4 h `elk` run with the learned SDF, authors' settings, alone, through the
guard (`scripts/repro_cmgrrt.py --iterations ...`). Report it honestly against
the paper (156 min mean on 16 cores, with parallel exploration not in the public
code). Run it after T7 so it doesn't block labelling.

### T10 Report (mandatory before each DEADLINE; final when all stages are done)
`reports/run04/REPORT.md` (≤ about 2 screens):
1. One line: is everything ready for run 05, and if not, what's missing.
2. Gate table (PASS / FAIL / BLOCKED, with evidence paths).
3. T3: unconfounded live rerun vs the confounded run 03 numbers.
4. T4/T5: what the oracle bug was, how it was fixed, validation numbers, the
   SDF decision.
5. T6/T7: the data pool, v2 label counts per source, v1 vs v2 differences.
6. T8: split sizes, and a link to PREREG.
7. T9: the elk result.
8. **Needs Aaron.** 9. Decisions made on his behalf. 10. A proposed run 05 prompt
   outline that follows PREREG.

Set `STATE: DONE` only when T0–T10 have all passed or are recorded as blocked.
Then commit and push.
