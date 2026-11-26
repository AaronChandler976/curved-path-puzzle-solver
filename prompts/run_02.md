# Run 02 (day run): reproduce CMG-RRT cleanly, fix the oracle, relabel

You are running unattended on Aaron's Ubuntu desktop. Nobody will answer
questions until the run ends. Read `CLAUDE.md` and `docs/PLAN.md` first and
follow them exactly. Their hard rules outrank anything in this prompt.

**Run folder:** `reports/run02/`. All of this run's STATUS.md, REPORT.md,
BLOCKERS.md, DECISIONS.md and figures/ go there. Run 01's top-level reports
are read-only history.

## Why this run exists
Run 01 (`reports/MORNING_REPORT.md`, `reports/DECISIONS_FOR_AARON.md`) found:
1. 85% of unsolved queries started in collision under CMG-RRT's learned
   obstacle SDF. Those are artifacts, so the failure labels and the 7× replay
   headroom can't be trusted.
2. CMG-RRT solved only 3/34 bundled runs, while the GPU was shared with
   labeling. Its paper's results have not been reproduced cleanly on this
   machine.
3. Building the learned SDF (~66 s/query) dominated throughput.
4. Workers went above the 10-process cap for a while, and timings were
   confounded.

Aaron's decisions (also in docs/PLAN.md):
- Use an **exact per-part SDF, combined into a union with min, plus a contact
  tolerance ε**.
- **Query cost = planner time**, with setup reported separately.

## Working rules (same as run 01, with the new run folder)
- **Never stop to ask.** When a choice is needed, take the most reasonable
  option, record it in `reports/run02/DECISIONS.md` (choice, alternatives,
  why), and keep going.
- **Keep `reports/run02/STATUS.md` current.** It is your memory across
  restarts. Format:
  ```
  STATE: RUNNING            (or DONE when R7 is complete)
  DEADLINE: <ISO time from the launch message>
  CURRENT STAGE: R<n> <name>
  BACKGROUND JOBS: <pid> <what> <log path>   (one per line, or "none")
  DONE SO FAR: <bullets with evidence paths>
  NEXT ACTION: <exact next step>
  ```
- **On start,** read STATUS.md, check whether the listed PIDs are alive, and
  resume from NEXT ACTION. Don't redo work that is done.
- **Timebox every stage.** After 3 failed fix attempts on the same error,
  write it to BLOCKERS.md and move to the next stage that doesn't depend on it.
- **Gates pass only with evidence on disk.** Quote the paths.
- **Commit** after each stage and push the current branch.
- **Start R7** no later than 45 minutes before DEADLINE.

## Stages

### R0 Review run 01 (≤ 30 min)
- Read run 01's reports, DECISIONS_FOR_AARON.md and the adapter code in
  `src/disasm/oracle/`.
- Write `reports/run02/run01_review.md` with a short check of the decisions
  that affect correctness:
  - the ×0.2 scale, and whether every absolute threshold (planner `eta` and
    `threshold`, the interpenetration cutoff, ε) is in the same scaled units;
  - the winding-number sign fix;
  - one RRT tree testing all goal candidates;
  - the interpenetration exclusion.
  Fix real bugs you find, and log them.

### R1 Process fixes (≤ 45 min)
- `src/disasm/util/slots.py`: a cross-process planner-slot semaphore, using a
  file lock under `logs/slots/`, with a hard cap of 10. Make every script that
  starts planner workers use it. Add a test proving that an 11th acquire
  blocks.
- `src/disasm/util/runlog.py`: helpers that write `uptime`, `nvidia-smi`,
  `powerprofilesctl get`, the git hash and the command line into a run folder.
  Make every experiment script call them at start and end.
- Confirm pytest passes using the CLAUDE.md command.
- **Gate:** tests pass, and the slot test is part of them.

### R2 Clean CMG-RRT reproduction (≤ 3 h; nothing else may run during it)
- Find what the CMG-RRT paper/README reports, which bundled examples it solves
  and with which settings, and record it in
  `reports/run02/cmgrrt_reference.md` with the source of each claim.
- Run the bundled examples with **the authors' own `scripts/test_list.json`
  settings** and their default learned SDF, on `cuda`, **one at a time**, with
  full iterations. Order: `elk` first (cap 60 min), then every other example
  the authors report as solved (cap 20 min each), then the rest (cap 10 min
  each) if time remains in the box. If the authors report several seeds, use
  3 seeds for `elk`.
- If `elk` fails, diagnose before rerunning:
  - compare our invocation line by line with `scripts/test_all.py`;
  - check `sampling` overrides in `properties.json`;
  - check sdf-N/sdf-H, device, and whether the SDF training converged.
  At most 3 diagnostic attempts.
- Write `reports/run02/smoke_clean.md`: a table of example, seed, settings,
  success, iterations, wall time, load-info path, and the paper's reported
  result.
- **Gate:** `elk` solved, or the exact discrepancy with the paper documented
  and listed as blocker #1 in REPORT.md.

### R3 Exact union-SDF collision detector (≤ 2.5 h)
- Read how CMG-RRT's RRT calls its `CollisionDetector`: which methods, batched
  or not, torch tensors or numpy, whether gradients are used, and on which
  device. Write `src/disasm/oracle/exact_sdf.py` with a drop-in detector class
  that matches that interface. Do not edit `external/`; subclass or wrap.
- Per-part exact SDF: unsigned distance to the part's mesh (quicksdf/CGAL AABB
  if its API exposes it, else an equivalent exact method), signed with the
  robust winding number. Compute once per part per assembly and cache to disk.
  The obstacle for a query is the min over the other remaining parts, with each
  part's SDF evaluated in its own fixed assembled frame.
- If the planner needs gradients, take them from the closest-point direction
  of the min-achieving part.
- **Contact tolerance ε:** a pose collides only if min SDF < −ε. Choose ε in
  scaled units, justify it against mesh quality and the interpenetration
  cutoff, and run a sensitivity check at 0.5ε, ε and 2ε on 30 assemblies.
- Validation:
  1. Start-pose validity on the assembled-state queries of 50 assemblies:
     report the valid % for the learned vs the exact detector.
  2. On 2–3 bundled examples, compare the exact and learned detectors at
     10,000 random poses near the moving body's start: agreement %, and where
     they disagree.
  3. Rerun every bundled example solved in R2 using the exact detector.
  4. Rerun the S3 set from run 01 side by side.
  Measure setup time per part and planner time per query for both detectors
  (timing hygiene applies).
- **Gate:**
  - start-valid ≥ 99% on the 50 assemblies;
  - every bundled example solved in R2 still solved with the exact detector,
    or a documented reason;
  - all results logged under `experiments/<date>_exact_sdf_validation/`.

  If planner time per query gets much slower (> 3× median), still go on, but
  note it as a cost-model fact.

### R4 Relabel as pilot_v1 (from R3 until R6 must start)
- Use the R3 detector and T = 30 s, unless the R3 timings justify a change
  (record it). Keep the same labeling protocol (every part at every state,
  random removal with a logged seed).
- Under the new ε, re-check run 01's interpenetration exclusions and include
  any assemblies that are now valid. Record the counts.
- Order: first the **same assemblies labeled in v0**, for a paired v0-vs-v1
  comparison. Then the remaining eligible 3–8-part assemblies (list in
  `experiments/2026-11-22_contact_scan/`).
- Output to `data/labels/pilot_v1/`, with the v0 fields plus `detector`,
  `epsilon`, `setup_time_s` (amortized per part), `start_valid` and
  `start_min_sdf`. Resumable, with a checkpoint per assembly, using planner
  slots.
- **Gate:** ≥ 50 assemblies fully labeled.

### R5 Analysis (≤ 1 h; first pass once R4 has ≥ 50 assemblies, final pass in R7)
- v0 vs v1 on the shared assemblies: success rate, the share of unsolved that
  started invalid, and planner time distributions. Then which assemblies change
  from stuck to complete.
- Rerun the per-state replay from run 01 on v1. Report:
  - planner-only and planner + setup totals (setup amortized as recorded);
  - the ratio of totals and the median per-state ratio, with bootstrap CIs;
  - random, outside-in, fewest contacts and hindsight-optimal.
- Rotation analysis: count the v1 assemblies and states where a successful
  path needed rotation > 15°. Report the replay separately for that subset if
  n ≥ 20 states; otherwise say it is too small.
- Output `reports/run02/analysis_v1.md` with figures.

### R6 Optional pipeline test on v1 (only if ≥ 2 h remain and ≥ 1,500 v1 queries)
- Rerun run 01's S6 training loop on v1 (overfit check, then one split by
  assembly).
- **PIPELINE TEST, not a result.** Label it that way everywhere, and don't
  compare models in REPORT.md.

### R7 Final report (start ≤ 45 min before DEADLINE; mandatory)
- Stop background jobs cleanly and run R5's final pass.
- Write `reports/run02/REPORT.md` (≤ about 1.5 screens):
  1. One line on what works now.
  2. A gate table (PASS / FAIL / SKIPPED) with evidence paths.
  3. Key real numbers with log paths:
     - the clean reproduction outcome versus the paper;
     - start-valid % (learned vs exact) and the ε sensitivity;
     - v1 label counts and success rate;
     - replay headroom, planner-only and with setup.
  4. **Needs Aaron:** items with exact commands or questions.
  5. Decisions made on his behalf (link DECISIONS.md).
  6. Proposed next run: the remaining labeling budget in queries/hour as
     measured, whether to set up the Tier A labels from ATA, and when the
     dataset is big enough for the real GNN-vs-baselines experiment.
- Set `STATE: DONE` in `reports/run02/STATUS.md`, then commit and push.
