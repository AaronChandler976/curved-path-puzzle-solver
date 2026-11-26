# Cost-Aware Query Ordering for Assembly-by-Disassembly with a Tight-Clearance SE(3) Planner

CMPE 258 Deep Learning (Fall 2026, San José State University), Option 1 (train + deploy). Solo project by Aaron Chandler.

**Paper:** [`paper/main.pdf`](paper/main.pdf) · **Talk:** [`talk/main.pdf`](talk/main.pdf) ·
**Demo video:** VIDEO-LINK (see `reports/campaign/NEEDS_AARON.md`) · **Final results:** [`reports/final_eval/REPORT.md`](reports/final_eval/REPORT.md)

## What this is
Robotic disassembly needs a removal sequence for a real product. Assembly-by-disassembly finds one by asking a
motion planner, one part at a time, *"can this part come out?"*. With the tight-clearance SE(3) planner
[CMG-RRT](https://github.com/TAU-CGL/cmg-rrt), a query takes anywhere from 0.04 s (a straight pull) to a 30 s
timeout, and a timeout does not prove the part is stuck. The order of queries therefore decides the planning cost.

We train a **graph neural network with a discrete-time survival head** over each state's contact graph. It predicts,
for every part, the probability that the planner succeeds within T (p) and the expected censored query cost (c), with
timeouts treated as censored. Parts are queried in descending p/c. Earlier learned guidance (Cebulla et al., ICRA 2023;
[ASAP](https://github.com/yunshengtian/ASAP), ICRA 2024) predicts removability only.

## Results (test set, 347 fresh assemblies, pre-registered, evaluated once)
Total planner time in seconds. Replay re-uses logged query costs; live runs fresh CMG-RRT queries over full
disassemblies. Trained models are 5-seed means. Full tables, CIs and tests: `reports/final_eval/`.

| ordering | replay | live |
|---|---|---|
| random | 22,186 | 26,464 |
| ASAP zero-shot (released weights) | 12,387 | 26,667 |
| ASAP retrained on our labels | 11,500 | 23,212 |
| outside-in | 9,130 | 23,239 |
| **fewest contacts** (best heuristic, chosen on val) | **7,202** | **23,002** |
| MLP-BCE / MLP-Surv | 7,672 / 7,983 | 21,139 / 20,827 |
| GNN-BCE (removability only) | 8,563 | 20,131 |
| **GNN-Surv (ours)** | **7,595** | **21,038** |
| GNN-Surv-Tail / PN-GNN-Surv | 7,415 / 7,771 | 19,885 / 20,805 |

- **Pre-registered decision:** GNN-Surv does **not** beat fewest contacts. Replay ratio 1.055 [0.887, 1.257], Holm
  p 0.43; live 0.915 [0.819, 1.015], Holm p 0.13.
- **Against ASAP:** GNN-Surv is cheaper than both ASAP models in replay (0.613 and 0.660) and live (0.789 and 0.906).
- **Survival vs BCE:** the survival (cost-aware) head is cheaper than BCE (removability) ordering with the same GNN in
  the main replay analysis (0.887 [0.785, 0.999], Holm p 6e-7), but not robustly across evaluations.
- **Why it loses to the heuristic:** a few confident timeouts on larger, unseen assemblies (`failure_analysis.md`).
- **Biggest practical win (exploratory, not learned):** query every part with a 3 s budget first. Replay cost falls
  72–79% for every ordering replayed, and about 50% live for the two orderings run with it.
- **Ranker cost:** about 2.5 ms per state on one CPU thread (32k parameters).

## Repository layout
```
src/disasm/oracle/   CMG-RRT adapter (exact union SDF), straight-pull pre-check, oracle v2, path validation
src/disasm/data/     contact graph + features, point clouds, penetration allowance
src/disasm/models/   MLP / GNN / attention encoders, survival head, PointNet, tail and ListNet losses, ASAP training
src/disasm/eval/     replay, statistics (bootstrap, Hodges–Lehmann, Wilcoxon, Holm, C-index, ECE)
src/disasm/util/     idle guard (timing hygiene), planner slots, run logging
scripts/             one CLI per step (all take --help)
configs/             final_frozen.yaml (every test checkpoint + sha256), final_methods.json
docs/                PLAN.md, PREREG_run05.md (pre-registration), PREREG_addendum.md, course texts
reports/             per-run reports (run02–run05, explore, final_eval) and campaign logs and audits
experiments/         one folder per run: cmd.txt, git_hash.txt, logs, small results (large files are not in git)
paper/ talk/ video/  final report (LaTeX), slides (Beamer), demo video script
tests/               pytest
```

## Environment
Ubuntu, Python 3.11, PyTorch with CUDA 12.8 (RTX 5070 Ti), PyG. No sudo is needed.
```bash
conda create -n disasm python=3.11 -y && conda activate disasm
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install torch_geometric trimesh rtree scikit-learn scipy pyyaml matplotlib imageio threadpoolctl spatialmath-python pymcubes tqdm
# CMG-RRT (MIT) as a third-party clone, never edited in place (our adapter lives in src/disasm/oracle):
git clone https://github.com/TAU-CGL/cmg-rrt external/cmg-rrt
pip install -e external/cmg-rrt/src/quicksdf -e external/cmg-rrt/src/taucgl-sdf -e external/cmg-rrt/src/taucgl-rrt
pip install -e .            # this package (src/disasm)
# ASAP baseline (separate env, for its redmax contact graph): see reports/run04/DECISIONS.md #9
# LaTeX and video tools: conda create -n paper -c conda-forge tectonic ffmpeg
```
`environment-disasm.yml` lists the exact package versions used (`conda env create -f environment-disasm.yml`, then the
three local CMG-RRT packages and `pip install -e .` as above; `quicksdf` is a C++ extension built with CMake, see
`external/cmg-rrt/src/quicksdf/README.md`). On machines where ROS sets `PYTHONPATH`, prefix
commands with `env -u PYTHONPATH`. Tests: `env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest`.

## Data
Assemblies come from the Assemble Them All / ASAP Fusion 360 dataset (`data/raw/multi_assembly/`, download per the
ATA repository). Labels (`data/labels/pilot_v2/`, 41,913 queries) and processed graphs are not in git because of their
size. The frozen split `data/splits/v2_split.json` and the test marker are in git. Checkpoints and the split are
published as the GitHub release v1.0-final (see below).

## How to run
Each step writes `experiments/<date>_<name>/` with the command, git hash, load info and logs. Inputs that are not in
git or in the release must be regenerated by the earlier steps or downloaded: the raw assemblies (`data/raw/`), the
labels (`data/labels/pilot_v2/`, step 1), the processed graphs (`data/processed/run05/`, step 2), the redmax contact
graphs (`scripts/asap_contact_graphs.py`, env `asap`) and the demo frames used by `video/build_video.sh` (step 6). The
checkpoints come from the release.
```bash
# 1. labels (timed; idle-guarded; 10 planner workers; ~12 h)
python scripts/label_abd.py --outdir experiments/<d>_label --labels-dir data/labels/pilot_v2 --oracle v2 --detector exact \
  --T 30 --workers 10 --groups 3-12 --idle-wait 300 --max-reruns 2   # full command: experiments/2026-11-24_run04_label_v2/cmd.txt
# 2. split + graphs (train/val only)
python scripts/build_split_v2.py --source-file experiments/2026-11-23_run04_t6_pool/source.json --seed 0
python scripts/build_dataset_v2.py --splits train,val --clouds
# 3. training (registered grid, 5 seeds per variant, val selection)
python scripts/train_v2.py --variant gnn_survival --outdir experiments/<d>_train
python scripts/train_asap_v2.py --outdir experiments/<d>_train --redmax experiments/2026-11-24_run05_redmax/asap_graphs.jsonl
# 4. evaluation (val; the test evaluation runs once and is guarded by data/splits/.v2_test_evaluated)
python scripts/eval_v2.py --split val --methods configs/final_methods.json \
  --redmax experiments/2026-11-24_run05_redmax/asap_graphs.jsonl --outdir experiments/<d>_val --md val.md --fig-dir figs
# 5. live disassembly with any ordering (fresh planner queries)
python scripts/live_abd.py --assemblies ids.json --outdir experiments/<d>_live --methods fewest_contacts,gnn_survival#s101 \
  --model-spec experiments/2026-11-24_final_eval_live/model_spec.json --oracle v2 --save-paths
# 6. demo render (from a live run with saved paths)
python scripts/render_demo.py --live-dir experiments/2026-11-26_demo_01310 --aid 01310 --method "gnn_survival#s101" --out demo --hd
```

## Checkpoints
The 50 frozen checkpoints (10 variants × 5 seeds) are listed with sha256 in `configs/final_frozen.yaml`. They are
published with the v2 split as release
[v1.0-final](https://github.com/AaronChandler976/curved-path-puzzle-solver/releases/tag/v1.0-final)
(`checkpoints_final_frozen.tar.gz`, extract at the repo root; `SHA256SUMS`).

## How the project was run
Work was done in logged runs with pre-registration (`docs/PREREG_run05.md`), an idle guard for all timed planner
work, and an independent audit after every phase (`reports/campaign/AUDITS/`). Every number in the reports links to
the run folder that produced it.

## License and credits
No license file has been chosen for our code yet (see `reports/campaign/NEEDS_AARON.md`). Third-party: CMG-RRT
(MIT, TAU-CGL), ASAP and Assemble Them All (see their repositories). CMG-RRT is used unmodified, through our collision
adapter; `patches/README.md` lists any patches.
