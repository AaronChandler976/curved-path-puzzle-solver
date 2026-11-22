# CLAUDE.md — CMPE 258 project rules (read before doing anything)

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
   stand-in, never as a replacement.
3. **A sampling planner cannot prove a part is stuck.** A CMG-RRT query that does
   not succeed is `unsolved` (budget exhausted), never "infeasible". Store it as
   censored.
4. **Never use `sudo`.** If a system package is missing, write it to
   `reports/BLOCKERS.md` with the exact `apt install` line and move on.
5. **Stay inside this project folder.** Do not modify, move or delete anything
   outside it. Do not delete anything under `data/` or `experiments/`.
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
- Parallel planner runs: at most 10 worker processes, leaving 2 cores free.

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
reports/             STATUS.md, MORNING_REPORT.md, BLOCKERS.md, smoke_test.md, ...
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
