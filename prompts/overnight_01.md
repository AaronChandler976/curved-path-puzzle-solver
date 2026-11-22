# Overnight run 01: pipeline, CMG-RRT timing, first real labels

You are running unattended on Aaron's Ubuntu desktop. Nobody will answer
questions until morning. Read `CLAUDE.md` first and follow it exactly. Its hard
rules outrank anything in this prompt.

## Goal for tonight
Tonight is not the GNN-vs-baselines experiment. That needs labels, and the
labels need a working, timed pipeline. Tonight's job is to make the pipeline
real and measure it:
1. CMG-RRT installed, smoke-tested and timed on its bundled examples.
2. Datasets downloaded, with licenses recorded.
3. A CMG-RRT adapter that answers "can part p leave the current sub-assembly?"
   on real multi-part CAD assemblies.
4. A first set of real, logged labels: every remaining part queried at every
   visited state.
5. A replay analysis of those real queries: how much planner time random and
   heuristic orderings waste compared with the best possible ordering.
6. A morning report that Aaron can trust line by line.

## Working rules for an unattended night
- **Never stop to ask.** When a choice is needed, take the most reasonable
  option, write it in `reports/DECISIONS_FOR_AARON.md` (what you chose, the
  alternatives, why), and keep going.
- **Keep `reports/STATUS.md` current.** It is your memory: this session may be
  restarted with a fresh context, and the next session resumes from that file.
  Update it after every meaningful step. Format:
  ```
  STATE: RUNNING            (or DONE when the final stage is complete)
  DEADLINE: <ISO time from the launch message>
  CURRENT STAGE: S<n> <name>
  BACKGROUND JOBS: <pid> <what> <log path>   (one per line, or "none")
  DONE SO FAR: <bullets, each with the log/report path>
  NEXT ACTION: <the exact next thing to do>
  ```
- **On start,** read `reports/STATUS.md` if it exists. Check whether the listed
  background PIDs are still alive (`ps -p <pid>`) and continue from
  NEXT ACTION. Don't redo work that is already done.
- **Timebox every stage.** If a stage runs past its box, or you are stuck on
  the same error after 3 real fix attempts, record it in `reports/BLOCKERS.md`
  (exact error, what you tried, what Aaron would need to do) and move on to the
  next stage that doesn't depend on it.
- **Gates are checked with evidence.** A stage passes only when the command
  output on disk shows the gate condition. Quote the log path.
- **Commit** after each stage (`git add -A`; large data is gitignored) and push
  the current branch. If the push fails, note it and continue.
- **Final stage timing:** start it no later than 45 minutes before DEADLINE,
  whatever else is going on. Stop background jobs cleanly first; they must have
  checkpointed.

## Stages

### S0 Environment audit (≤ 30 min)
- In conda env `disasm`: record Python, torch, CUDA availability,
  `torch.cuda.get_device_name()`, PyG version, and the CMG-RRT package import
  status in `reports/environment.md`.
- Fix missing Python packages inside the env. For anything needing sudo, see
  CLAUDE.md rule 4.
- Record the commit hash of every repo under `external/` in
  `reports/external_versions.txt`.
- **Gate:** torch sees the GPU, or the CPU fallback is recorded, **and** CMG-RRT's
  Python modules import.

### S1 CMG-RRT smoke test and timing (≤ 1.5 h)
- Read `external/cmg-rrt` (README, `scripts/test_all.py`, `scripts/test_list.json`)
  to learn the real API. Write `scripts/smoke_cmgrrt.py`, which runs one bundled
  example from a config **without editing their files**, and logs success,
  iterations and wall time.
- First run `elk` with `device: cpu` and `iterations: 500`. Then run every
  bundled example in `resources/models/puzzle/` and `resources/models/general/`
  on both `cpu` and `cuda`, each capped at 10 min wall time, running up to 4 in
  parallel.
- Write `reports/smoke_test.md`: a table of example, device, success,
  iterations, wall time and log path, plus a short note on CPU vs GPU speed and
  how per-query times are distributed.
- **Gate:** at least one logged success.

### S2 Data acquisition (≤ 1 h; run downloads in the background during S1)
- Assemble Them All (`external/Assemble-Them-All`): follow its README to
  download the **multi-part** dataset and the **two-part rotational** set into
  `data/raw/`. The two-part main set is optional.
- ASAP: find the canonical code repo from asap.csail.mit.edu or the paper
  (arXiv 2309.16909); there is also a fork at github.com/makolon/ASAP, which
  calls itself official. Clone it into `external/ASAP`, record which repo you
  chose and why, and download its released data and checkpoints if available.
- Record each dataset's license (including the Fusion 360 Gallery license),
  source URL, size and checksum in `reports/data_sources.md`.
- Write `scripts/inspect_dataset.py`: count assemblies, show the part-count
  histogram, and confirm meshes load with trimesh. Report the results.
- If a download is blocked (login wall, dead link, Google Drive quota), record
  it in BLOCKERS with the URL and continue with what you have.
- **Gate:** multi-part set on disk, with ≥ 100 assemblies whose meshes load.

### S3 CMG-RRT adapter for multi-part assemblies (≤ 2.5 h)
Implement `src/disasm/oracle/cmgrrt.py` with one public function:
```
query(assembly, removed: set[int], part: int, timeout_s: float, seed: int, workdir) ->
  {outcome: "success" | "unsolved", time_s, iterations, goal_pose, escape_dir,
   n_goal_candidates_tried, path_file | None, error | None}
```
Design, following `04-cmg-rrt-integration.md` (summarized here):
- **Two-body limit:** merge every part not in `removed`, except `part`, into one
  static obstacle mesh. Cache it per state (key = sorted remaining-part ids).
- **Collision meshes:** work out how the bundled `*_sdf.obj` files relate to the
  full meshes. If the repo has a script for this, use it; otherwise simplify
  with trimesh/fast-simplification and write the method down. Generate the URDFs
  only if they are needed for visualization.
- **Goal pose:** start with the part's assembled pose. Candidate escape
  directions are the mean outward contact normal, the six ±axes, and the
  directions away from neighboring parts' centroids. Goal = translate the part
  along a direction by (assembly bounding-box diagonal + margin). Try candidates
  in order while sharing one `timeout_s` budget, and record which one worked.
- **Coordinates:** CMG-RRT poses are SE(3). Check the pose convention against
  the bundled `properties.json` files before trusting your own.
- Optional `linear_precheck()`: a straight-line sweep along each candidate
  direction with collision checks. Log it as a separate field. It never replaces
  the CMG-RRT query.
- **Tests:** `tests/test_oracle_bundled.py` reproduces a bundled two-body example
  through the adapter. `tests/test_oracle_multipart.py` runs one small dataset
  assembly.
- **Sanity image:** render one successful extraction path for a multi-part
  assembly to `reports/figures/` as a PNG strip (pybullet DIRECT or a trimesh
  offscreen render), so Aaron can see it isn't nonsense.
- **Gate:** on ≥ 3 dataset assemblies with 3–6 parts, querying every part at the
  assembled state gives ≥ 1 success, and all calls are logged under
  `experiments/<date>_oracle_check/`.

### S4 Pilot labeling (from S3's end until the final stage)
- Choose the per-query timeout: T = clamp(3 × median success time from S3,
  30 s, 300 s). Record T and the reasoning in DECISIONS_FOR_AARON.md.
- Write `scripts/label_abd.py`, which is resumable and checkpoints after every
  assembly. For each selected assembly, start at the assembled state. At each
  state, query **every** remaining part (parallel, ≤ 10 workers), then remove one
  successful part, picked uniformly at random with a logged seed. Continue until
  one part is left, or until no part succeeds (mark the assembly `stuck`).
- Order: assemblies with 3–5 parts first, then 6–8. Skip assemblies whose
  meshes are broken or whose obstacle prep takes > 2 min, and log why.
- Output: `data/labels/pilot_v0/labels.jsonl`, one line per query: assembly_id,
  state_key, removed list, part_id, outcome, time_s, iterations, goal candidate,
  seed, T, git hash, timestamp. Also write a per-assembly summary jsonl.
- Run in the background under `experiments/<date>_pilot_labels/`. Check
  progress every ~10 min and update STATUS.md with counts (assemblies done,
  queries, success rate, median time).
- **Gate:** ≥ 1 assembly fully labeled.

### S5 Replay analysis on real logged queries (≤ 45 min; run it as soon as S4 has ≥ 20 labeled states, rerun at the end)
Because every part was queried at each labeled state, any ordering's cost to
reach the first success at that state can be computed exactly from the logged
times. That is a replay of real runs, not a simulation. Label it as
"per-state replay on cached pilot queries."
- A failed query costs its logged time (≈ T). The cost at a state = the sum of
  times up to and including the first success. States with no success cost the
  sum of all queries; report them separately.
- Orderings:
  1. **Random:** the exact expectation, from enumerating permutations when
     n ≤ 8, otherwise 10,000 samples with a fixed seed.
  2. **Outside-in:** distance from the assembly center, farthest first (ASAP's
     heuristic).
  3. **Fewest contacts first.**
  4. **Hindsight-optimal:** the cheapest success first. This is a lower bound,
     labeled as unattainable.
- Report per-state and per-assembly medians/means, with bootstrap 95% CIs
  (fixed seed). Add the headroom ratio (random ÷ optimal) and its split for
  assemblies where any successful path needed noticeable rotation (rotation
  angle measured from the logged path > 15°) vs translation-only.
- Output `reports/replay_pilot_v0.md` with one or two matplotlib plots in
  `reports/figures/`.

### S6 Optional: model pipeline smoke test (only if ≥ 1,500 labeled queries and ≥ 2 h remain)
- Build the contact graph and per-part features (volume, bbox, distance to
  center, contact count, contact-normal histogram). PointNet is optional
  tonight.
- Implement an MLP and a GNN (PyG, GINE or GATv2) with (a) a BCE head and (b) a
  discrete-time survival head with censoring.
- Run: an overfit test on 20 states (loss must go near zero), then one
  train/val split by assembly with a fixed seed.
- Everything here is a **PIPELINE TEST, not a result.** Say so in every heading
  and table. Don't compare models on this data in the morning report beyond
  "the training loop runs and the loss goes down."

### S7 Final: morning report (start ≤ 45 min before DEADLINE; mandatory)
- Stop background jobs cleanly (they have checkpointed). Rerun S5 on all labels.
- Write `reports/MORNING_REPORT.md`, at most about 1.5 screens, leading with:
  1. One line: what works now and what doesn't.
  2. A gate table for each stage: PASS / FAIL / SKIPPED, with the evidence path.
  3. Key real numbers, each with its log path: CMG-RRT per-query time
     distribution, label counts and success rate, replay headroom.
  4. **Needs Aaron:** blockers that need him (sudo installs, logins, judgment
     calls), each with the exact command or question.
  5. Decisions made on his behalf (link DECISIONS_FOR_AARON.md).
  6. The proposed plan for night 02 (the Tier B labeling budget implied by the
     measured times, plus whether the ATA cheap-oracle labels are worth setting
     up).
- Set `STATE: DONE` in STATUS.md, commit and push.
