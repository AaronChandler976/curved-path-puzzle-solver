# CLAUDE.md — CMPE 258 project rules (read before doing anything)

**Also read `docs/PLAN.md`.** It defines the plan, the oracle, the cost
definition, Tier A/B labels, metrics and novelty.

## What this project is
Solo CMPE 258 (Deep Learning, Fall 2026) term project, Option 1 (train + deploy).
Two-layer disassembly planner for realistic mechanical CAD assemblies:
1. **Ranker (learned):** a GNN over the part-contact graph scores every remaining part.
   It predicts P(planner succeeds) and expected query cost, with timeouts treated
   as right-censored labels. Parts are queried in descending p/c order.
2. **Oracle (classical):** CMG-RRT (github.com/TAU-CGL/cmg-rrt, MIT), a
   tight-clearance SE(3) planner that handles curved/rotational motion. It tests
   one part at a time against the remaining parts merged into one static obstacle.

Comparisons all use the same oracle and budget: random, geometric/contact heuristic,
bookkeeping, MLP (same features, no message passing), ASAP's GNN, and our GNN
with a BCE-only head versus the cost-aware survival head.
Data: Fusion 360-derived assemblies from Assemble Them All / ASAP.
Novelty: ASAP and Cebulla 2023 predict removability and count tests. We model
query cost and timeouts. Never describe "a GNN predicts the next removable part"
as our contribution.

## Hard rules (breaking any of these ruins the project)
1. **No fabricated, simulated, estimated or "as if" results.** Every number in
   any report must come from a run you actually executed. Its log must be on
   disk and the report must link the log path. If something did not run, the
   report says so. Fabricated results get an automatic 0 in this course.
2. **Curved/rotational planning stays in.** CMG-RRT is the oracle. A discretized
   or translation-only planner may be used only as a labeled ablation or dev
   stand-in, never as a replacement. Swapping CMG-RRT's *collision
   representation* (the exact union SDF in docs/PLAN.md) is allowed as a
   documented adapter change. Its planning algorithm stays unchanged.
   **Oracle v2 (from run 04):** a straight-pull pre-check runs first, and CMG-RRT
   runs whenever the pre-check finds no free straight pull. This is allowed because
   CMG-RRT still decides every part a straight pull can't remove. Its time counts
   as query cost, and reports say how many removals each stage produced.
3. **A sampling planner cannot prove a part is stuck.** A CMG-RRT query that does
   not succeed is `unsolved` (budget exhausted), never "infeasible". Store it as
   censored.
4. **Never use `sudo`.** If a system package is missing, write it to
   `reports/BLOCKERS.md` with the exact `apt install` line and move on.
5. **Stay inside this project folder.** Do not modify, move or delete anything
   outside it. Do not delete anything under `data/` or `experiments/`. One
   exception: scratch caches that the current run created itself may be
   deleted, but log each deletion in that run's DECISIONS file.
6. **Do not edit code under `external/`.** If a third-party repo needs a fix, save
   it as a patch in `patches/`, explain it in `patches/README.md`, and apply it
   from a script.
7. **Git:** commit small and often with clear messages. Push only to the current
   `overnight/*` or feature branch. Never force-push and never rewrite history.
   Never commit large data: datasets, meshes, labels and checkpoints are
   gitignored.

## Environment
- Ubuntu desktop (native, not WSL): Ryzen 9 9900X (12 cores), RTX 5070 Ti 16 GB
  (Blackwell, needs a CUDA 12.8+ PyTorch build), 64 GB RAM.
- Main conda env: `disasm` (Python 3.11). It holds our code, PyTorch, PyG and
  CMG-RRT. Install packages into it with `conda run -n disasm pip install ...`
  or after `conda activate disasm`. If a third-party repo needs conflicting
  versions, make a separate env (e.g. `ata`) and write down why.
- **Planner process cap: 10 in total across ALL jobs**, leaving 2 cores free.
  Enforce it in code: every script that starts planner workers takes
  slots from `src/disasm/util/slots.py`, a file-lock semaphore shared across
  processes. Before launching anything, check that no other planner jobs are
  running.
- **Timing hygiene:** any run whose wall-clock numbers will be reported
  (smoke tests, timing benchmarks) runs alone. No other GPU or planner jobs
  may run at the same time. Log `uptime`, `nvidia-smi
  --query-gpu=utilization.gpu,memory.used --format=csv` and the power profile
  (`powerprofilesctl get`, expected `performance`) at the start and end of
  each timed run. Labeling runs report times too, so they log the same load
  info. Mark any timing taken under contention as confounded.
- **ROS on this machine sets `PYTHONPATH`, which breaks pytest and imports.**
  The runner unsets it. If it reappears, prefix commands with
  `env -u PYTHONPATH`. Run tests as
  `env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest`.

## Layout
```
src/disasm/oracle/   CMG-RRT adapter (+ optional cheap linear pre-check)
src/disasm/data/     dataset loading, mesh prep, contact graph + features
src/disasm/models/   MLP, GNN, survival head
src/disasm/search/   orderings (random, heuristic, learned) + AbD runner
src/disasm/eval/     metrics, replay analysis, plots
scripts/             CLI entry points (one job each, argparse, --help works)
configs/             YAML configs for runs
tests/               pytest tests
experiments/<YYYY-MM-DD>_<name>/   one folder per run: config.yaml, cmd.txt,
                     git_hash.txt, stdout.log, results.* (gitignored except small md/csv)
reports/             run 01 reports at top level; from run 02 on each run uses reports/<run>/
                     (STATUS.md, REPORT.md, BLOCKERS.md, DECISIONS.md, figures/)
docs/PLAN.md         the adopted plan
data/raw, data/processed, data/labels   (gitignored)
external/            third-party clones (gitignored; versions in reports/external_versions.txt)
patches/             patches to third-party code
```

## How to log a run
Every run that produces a number uses its own `experiments/<date>_<name>/` folder
containing the exact command, the config, the git commit hash, the random seeds,
the full stdout/stderr, and machine-readable results (jsonl/csv). Reports cite
these paths.

## Long jobs
The Bash tool times out after a few minutes. Start any job longer than about
2 minutes in the background: `setsid nohup <cmd> > <log> 2>&1 &` and save the
PID to a file. Then check progress by reading the log, using `sleep 300` (or
similar) between checks instead of many quick checks. Jobs must checkpoint and
be resumable.

## Evaluation rules (added for run 03)
- **The test split is evaluated once,** after every model and config is frozen.
  Never tune, select seeds or pick checkpoints on test.
- **Report every variant and seed you trained.** Never drop a bad seed or variant.
  Trained models are reported as mean ± std over seeds.
- The rotation flags and any other evaluation-only labels are never model inputs.
- Give every comparison a CI and its sample size. If a subset is small, say it is
  underpowered instead of drawing conclusions from it.

## Run 04 rules (added 2026-11-23)
- **The run 03 test split is spent.** It was evaluated on 2026-11-23 and the method
  is being changed in response, so it can never again be the final test. The final
  test set is the test part of the v2 split, built and frozen in run 04 and
  evaluated exactly once, in run 05. Run 04 trains nothing on v2 and reads no
  v2 test labels except to check that labelling finished.
- **Idle guard for timed work.** Planner times are the labels and the metric, so
  any planner work whose times are kept goes through `src/disasm/util/idle_guard.py`:
  - "busy" = processes outside this project (not our runner, not our workers, not
    `claude`) use more than 0.5 CPU core on average over 30 s, or the 1-min load
    average minus our own planner workers is above 1.5. GPU use is logged but is
    not a criterion (the planner is CPU-only).
  - Before a timed batch starts, the machine must be non-busy for 5 minutes.
  - Labelling and live evaluation dispatch a new query only while non-busy. Each
    query record stores `busy_frac` (fraction of 5 s samples that were busy during
    the query) and `confounded = busy_frac > 0`. Confounded queries are re-run at
    the end (same seed). Keep every attempt in the log; the label uses the first
    clean attempt. If a query is still confounded after 2 re-runs, keep it, flagged.
  - Single long timed runs that can't pause (elk, SDF seeds) log busy samples
    throughout and are marked confounded if `busy_frac > 0.05`.
- **While timed work runs, nothing else heavy runs:** no training, compiling,
  pip builds or GPU jobs at the same time. Schedule those between timed stages.
- **Seeded robot sampling.** Every planner query draws its robot surface samples
  from a generator seeded by the query seed, so the same query is reproducible.

## Campaign rules (added 2026-11-24; the campaign runs until 2026-12-13)
- **The v2 test set is evaluated exactly once**, in campaign Phase 3, after
  `docs/PREREG_addendum.md` and `configs/final_frozen.yaml` are committed. The
  marker `data/splits/.v2_test_evaluated` is written at the first read of test
  labels. After that, nothing may be trained, tuned or selected for the reported
  comparison; later work (paper, failure analysis, elk) only reads saved outputs
  or uses non-test data.
- **Exploratory variants** (developed after `docs/PREREG_run05.md` was committed)
  may enter the test only through the addendum, labelled "post-registration,
  exploratory". The registered comparisons and the §7 decision rule never change.
- **Independent auditor:** after every phase, start a subagent (the Agent tool)
  whose only instructions are `prompts/audit.md` plus the phase name and the
  report/run paths. Never pass it your own conclusions or summaries. Save its
  output in `reports/campaign/AUDITS/`. Fix every BLOCKER/MAJOR finding and re-audit
  before the phase counts as done.
- **References and claims:** never cite a paper you have not verified exists
  (check it with WebSearch/WebFetch). Never write "state of the art", "beats" or
  "significant" unless the logged numbers and the pre-registered rule support it.
- **Git:** the campaign branch is pushed after every step. In Phase 5 only, merge
  it into `main` with a normal merge (`git switch main && git merge --no-ff <branch>`),
  then push `main`. Never force-push or rewrite history on any branch.
- **Tools without sudo:** LaTeX via `tectonic` and video via `ffmpeg`, both from
  conda-forge in a conda env named `paper`. Anything needing sudo goes in
  `reports/campaign/NEEDS_AARON.md`.
