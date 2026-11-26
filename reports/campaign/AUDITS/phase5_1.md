# Audit phase5_1: final audit (paper, repo, video, campaign)

Auditor: independent subagent, instructions `prompts/audit.md` only. Date 2026-11-26.
Scratch and logs: `experiments/2026-11-26_audit_phase5_1_repro/` (commands in `cmd.txt`). I ran no planner jobs, did not
re-run the test evaluation, did not touch `data/splits/.v2_test_evaluated`, and committed nothing.

## What was checked and holds
- **Compile:** a copy of `paper/` builds with `tectonic -X compile` (exit 0, 6 pages, only underfull-hbox warnings;
  `tectonic.log`). The result has the same size as `paper/main.pdf` and differs only in metadata bytes.
- **Vector graphics:** `pdfimages -list` finds 0 raster images in `paper/main.pdf` and in all 4 `paper/figures/*.pdf`.
  The architecture figure is TikZ.
  - `totals_replay_live` and `budget_policy` have the same text as `reports/final_eval/figures/`.
  - `failure_scatter` is byte-identical.
  - `demo_01310.pdf` regenerated with `scripts/demo_figure.py` has identical text and is vector.
- **Replay numbers:** I recomputed them from `experiments/2026-11-25_final_eval_replay/per_state.jsonl` with my own
  script (`recompute_replay.py`/`.log`).
  - All 11 replay totals match Table I, as do hindsight-optimal 416 and the exploratory ListNet/GATv2/GT totals.
  - All 11 registered ratios, bootstrap CIs (10,000 resamples) and Holm p values match. Examples: 1.055 [0.887, 1.257] p 0.43;
    0.887 [0.785, 0.999] p 6.2e-7; 0.613, 0.660, 0.342, 0.951.
  - Scored states (2,195), unscored states (31, 4,477 s) and 341 assemblies match.
  - Budget policy: 2,008 / 1,904 s, 0.948 [0.820, 1.095]. ECE 0.038, C-index 0.674, and ASAP 0.593 (from `results.json`).
- **Live numbers:** I recomputed them from `experiments/2026-11-24_final_eval_live/results.jsonl` (first clean attempt;
  `recompute_live.py`/`.log`).
  - 17,697 runs and 0 still confounded.
  - Every live total in Table I and the README matches.
  - Ratios: 0.915 [0.819, 1.015], 0.789 [0.699, 0.880], 0.906 [0.827, 0.994], 1.045 [0.955, 1.150], ListNet 0.797.
  - Budget-policy totals: 11,273 and 10,810 s.
- **Other paper numbers trace to source:**
  - Table I ratio columns (all 22 cells recomputed from the totals).
  - Latency table: `reports/run05/profile.md`.
  - Failure analysis: 89%/77%; 436/3,240 s; 368/3,404 s; 85/3,153 s; p ≥ 0.90, c ≤ 3.7 s; 15 of 20 with 9–12 parts. Source: `failure_analysis.md`.
  - Data counts: 2,022 = 1,328 + 255 + 439; 919 excluded; 5.1%; 12.6 h; 1,425/250/347; 51%/63%. Source:
    `reports/run04/REPORT.md` and `data/splits/v2_split.json`.
  - Train is 89.5% 3–8-part (recomputed).
  - Oracle negative results (123/124, 18.5%, < 10% of ε, 4ε goal edge): `reports/run04/oracle_v2.md`.
  - 16505 result: `sdf_puzzles.md`.
  - Demo: p 0.97, c 1.33, 102.2°. Source: `experiments/2026-11-26_demo_01310/results.jsonl`.
  - Method constants: K = 8, τ = 0.1, λ ∈ {0.1, 1}, AdamW, the grid, 18 node and 5 edge features. Checked against
    `docs/PREREG_run05.md`, `scripts/train_v2.py` and `src/disasm/data/graph.py`.
- **Elk (`reports/run04/REPORT.md` §6):** `results.jsonl` and `stdout.log` agree: 76,901 iterations, 3.42 M nodes,
  14,400 s, wall cap, busy_frac 0.0069 over 2,881 samples, idle-wait 300 s, and load info at start and end. The paper's "156-min mean on 16 cores, parallel
  exploration" matches the CMG-RRT paper (arXiv 2607.17898 HTML: "parallelized among 16 cores", "average time of 156
  minutes"). No multiprocessing or parallel code exists in `external/cmg-rrt` (grep).
- **Test discipline:**
  - The marker was written 2026-11-24 23:08:45 (commit 1905865).
  - `docs/PREREG_addendum.md` and `configs/final_frozen.yaml` were last committed at 23:04:31 (a13b397), before the marker.
  - There is one replay folder and one live folder. The only other `--split test` invocation is the phase3_1 refusal check.
  - The untracked `run06_dev_live` used 2 train assemblies.
- **Release v1.0-final:**
  - It is public and has 3 assets. `sha256sum -c SHA256SUMS` passes.
  - The tarball holds 50 checkpoints, and all 50 match the sha256 values in `configs/final_frozen.yaml`.
  - The bundled yaml and `v2_split.json` are byte-identical to the repo copies.
- **Branch main:**
  - `main` = `origin/main` = 69b7705, built from `--no-ff` merges (092f54f, 69b7705). The campaign branch is pushed.
  - Nothing large is tracked on `main`: the largest file is `video/demo.mp4` at 2.2 MB.
  - Only one blob over 3 MB exists in history (`talk/demo.gif`, 3.6 MB, since removed).
  - No `.pt`/`.pth`/mesh/label files are tracked on `main`, and a token/key-pattern grep finds no secrets.
- **Tests:** `env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 conda run -n disasm python -m pytest`: 36 passed (`pytest.log`).
- **README:** every script named in "How to run" answers `--help` (`help_*.log`), and the referenced files exist locally.
- **Video:** ffprobe (env `paper`) reports 112.8 s, h264 1920×1080, 30 fps, so it is within the 2-minute limit. Frames match the build script.
- **References:** all 14 entries were checked on the web (arXiv abstract pages, Crossref, ICML/DBLP, PeerJ search). Titles, authors,
  venues and years match.
  - Cebulla et al., ICRA 2023, pp. 12388–12394 (Crossref DOI 10.1109/icra48891.2023.10160920).
  - ASAP, 13 authors, ICRA 2024.
  - ATA, TOG/SIGGRAPH Asia 2022.
  - CMG-RRT, 4 authors, WAFR, arXiv 2607.17898.
  - Odense, IROS 2022.
  - Atad, IROS 2023.
  - Jiang et al., arXiv 2609.30599, Sep 2026.
  - Simon & Kadane, AI 6(3):235–247.
  - Gensheimer, PeerJ 7:e6257.
  - Hu, ICLR 2020.
  - Brody, ICLR 2022.
  - Grover, ICLR 2019.
  - Qi, CVPR 2017.
  - Cao, ICML 2007, pp. 129–136.
  - The paper's descriptions of Odense and Jiang match their abstracts.
- **Novelty and course structure:**
  - The paper never claims "a GNN predicts the next removable part".
  - The novelty is cost and censoring, stated against Cebulla and ASAP.
  - The abstract has 217 words and includes numbers.
  - The structure has sections 1–6 plus references, with bulleted contributions and a failure/negative/limitations section.
  - The professor's feedback points are addressed in the Introduction and the Data section: real CAD, verified states, a GNN ranking the next query, and random/heuristic/MLP/GNN baselines on the same planner.

## Findings

| severity | file | what is wrong | how to verify |
|---|---|---|---|
| MAJOR | `paper/main.tex` §VI Conclusion (l.~372) | First sentence: "Modelling what a planner query costs … makes a learned AbD ranker cheaper than ranking by removability and than ASAP's model". This is unqualified. The paper's own Ablations (live total 1.045 [0.955, 1.150]; clean-subset CI reaches 1.001; MLP pair reversed), the abstract ("but not robustly across evaluations"), `reports/final_eval/REPORT.md` §2 ("not robust across evaluations or encoders") and the talk summary all qualify it. The conclusion overstates the evidence for the project's central claim. | `sed -n 370,376p paper/main.tex`. Compare §IV-C and `reports/final_eval/REPORT.md` "Survival p/c vs BCE p: mixed evidence" |
| MAJOR | `paper/main.tex` abstract and Contributions bullet 4 | "An untrained two-pass budget policy cuts planner time by 72% in replay and about 50% live for every ordering". Live, the policy was run for only 2 orderings: fewest contacts, and GNN-Surv at seed 101 only (`live_summary.json` methods `*@b3`). In replay 72% is the smallest saving (fewest contacts); the others save 73–79% (`results.json` `budget_policies.3.totals`). Contribution 4 repeats "72% for every ordering". The phase4_1 fix ("72–79% in replay, about 50% live (fewest contacts; GNN-Surv seed 101)", DECISIONS #14) was applied to the talk but not to the paper. | `grep -n "every ordering" paper/main.tex`. `grep -o '"method": "[^"]*@b3"' experiments/2026-11-24_final_eval_live/results.jsonl \| sort -u` |
| MAJOR | `paper/main.tex` §III/§IV | The baselines are never defined, so the main verdict cannot be interpreted or reproduced. Missing: what "fewest contacts" and "outside-in" compute (the main comparison is against fewest contacts); that random is an expectation; how ASAP zero-shot was applied (released weights, whose contact graph: redmax vs our adapter); ASAP-retrained's objective and grid; the MLP architecture (same features, no message passing); hindsight-optimal. The course structure asks for baselines in §4 (`docs/course/final_submission.md`). | `grep -n -i "outside-in\|fewest contacts\|zero-shot" paper/main.tex`: these names appear only in tables and results, never defined |
| MAJOR | `environment-disasm.yml` (README "Environment") | The pip section pins `torch==2.11.0+cu128` and `torchvision==0.26.0+cu128` (l.99, 101) but has no `--extra-index-url https://download.pytorch.org/whl/cu128`. PyPI only has `torch-2.11.0` without the `+cu128` local tag, and PEP 440 `==` on a local version does not match it. So `conda env create -f environment-disasm.yml`, which the README tells users to run, fails at the pip step. (The explicit `pip install torch --index-url …cu128` line in the README works; the yml path does not.) | `grep -n "index-url\|torch==" environment-disasm.yml`. `curl -s https://pypi.org/simple/torch/ \| grep -c '2.11.0+cu128'` gives 0, while `curl -s https://download.pytorch.org/whl/cu128/torch/ \| grep -c 'torch-2.11.0%2Bcu128-cp311'` gives > 0 |
| MINOR | `paper/main.tex` l.15, `README.md` l.5 | `VIDEO-LINK-PLACEHOLDER` / `VIDEO-LINK`: the required clickable video link is missing in the PDF. This is tracked in NEEDS_AARON/FINAL as a human-only step and must be done before submission. | `pdftotext paper/main.pdf - \| grep PLACEHOLDER` |
| MINOR | `paper/main.tex` §IV-D (Qualitative example) | "CMG-RRT finds a path … in 18.4 s". This time comes from the demo re-run, launched with `--no-guard` (`experiments/2026-11-26_demo_01310/cmd.txt`), so it is not an idle-guarded timing. The guarded live run of the same query (01310, `gnn_survival#s101`, state 5-7, part 7) took 19.52 s. Either cite 19.5 s from the guarded live run or label 18.4 s as unguarded. (The demo is also a fresh planner run on a test assembly after the marker. It feeds no comparison, but the campaign rule says later work "only reads saved outputs"; disclose it in DECISIONS.) | the auditor's comparison of both `results.jsonl` records (run inline; numbers in this row) |
| MINOR | `paper/main.tex` §V ("Plausible cause") | "Validation (80% small assemblies)" mislabels the source figure. Val is 89.6% assemblies with 3–8 parts; 79.6% is the v1 share. This is the same mislabel already fixed for train in phase4_1. | `python3` on `data/splits/v2_split.json`: val ≤ 8 parts 0.896, v1 0.796 |
| MINOR | `paper/main.tex` §IV-B | "The same holds on the 300 test assemblies that were never used in any pilot". 306 test assemblies were never used in a pilot (347 − 41); 300 of them are scored in replay. | `reports/final_eval/replay.md` "300 clean test assemblies"; `reports/run04/REPORT.md` §5 "306 other" |
| MINOR | `paper/main.tex` §IV-G | (a) "0.24 ms on the GPU at batch 1, 11 MB peak": 11 MB is the *batched* GPU peak (`profile.md` column header). (b) "ASAP … takes 7.0 ms" while the table shows 7.07 (7.1). (c) The profile run is CONFOUNDED under the CLAUDE.md single-run rule (busy_frac 0.435 > 0.05, `profile.md`). The paper only says "flagged", but CLAUDE.md requires marking it confounded. | `sed -n 1,20p reports/run05/profile.md` |
| MINOR | `paper/main.tex` §IV-A | "Every variant gets the same grid (hidden × lr × layers)" is not accurate. GNN-Surv-Tail has 16 configs (×λ), and ASAP-retrained uses Adam with an lr × batch grid (PREREG §3). This also conflicts with negative result (v), "the variant with the largest grid". | `docs/PREREG_run05.md` l.47–52 |
| MINOR | `paper/main.tex` §III-C | Notation clash: $c_i$ is both the censoring time in the loss and the expected cost $\mathbb{E}[\min(t_i,T)]$ two lines later. | read §III-C |
| MINOR | `paper/main.tex` §II | "graph-transformer models predict sequences step by step" has no citation. The candidate (Ma et al., `refs_check.md`) is marked "confirm acceptance before citing". | `grep -n "graph-transformer" paper/main.tex` |
| MINOR | `paper/main.tex` §IV-A | The software setup gives no versions. PyTorch 2.11.0+cu128, PyG 2.8.1 and Python 3.11 are in `environment-disasm.yml`. | `grep -n "PyTorch" paper/main.tex` |
| MINOR | `paper/main.tex` §V (iv), `reports/run04/REPORT.md` §6 | Elk is framed as "public, single-process CMG-RRT" against the paper's "16 cores". The run's own guard log shows our process using about 11.6 CPU cores throughout (`our_cores` ≈ 11.6, load1 ≈ 11–12). So the difference is the parallel tree exploration, not core count; worth stating so the comparison is not read as 1 core vs 16. | `experiments/2026-11-26_phase5_elk/guard_puzzle_elk_s0/idle_samples.jsonl`: fields `our_cores` and `load1` |
| MINOR | `paper/main.tex` §I | "a straight pull is certified in about 0.04 s". The 0.037 s source is the median of *all* queries in the 500-query oracle validation sample (`reports/run04/REPORT.md` §3), not of straight pulls specifically. The talk footer was corrected to say so. | `grep -n "0.037" reports/run04/REPORT.md` |
| MINOR | `paper/figures/totals_replay_live.pdf` (Fig. 2) | At `\linewidth` in one column, the tick and method labels render at roughly 4–5 pt and are hard to read in print. | `pdftoppm -r 70 -f 3 -l 3 paper/main.pdf`; see `experiments/2026-11-26_audit_phase5_1_repro/page-3.png` |
| MINOR | `README.md` Results | "the survival (cost-aware) head **beats** BCE (removability) ordering". `reports/final_eval/REPORT.md` reserves the "beats" label for the registered heuristic comparison ("described by those criteria, not by the label"). Use "is cheaper than". | `grep -n "beats" README.md` |
| MINOR | `README.md` How to run; `video/build_video.sh` | The commands depend on gitignored inputs that are in neither git nor the release: `experiments/2026-11-23_run04_t6_pool/source.json`, `experiments/2026-11-24_run05_redmax/asap_graphs.jsonl` and `…/allowance.json`. `build_video.sh` depends on `experiments/2026-11-26_demo_01310/demo_01310_frames/`. A fresh clone cannot run steps 2–5 or rebuild the video, and the README does not say so. | `git ls-files --error-unmatch experiments/2026-11-24_run05_redmax/asap_graphs.jsonl` fails |
| MINOR | `video/script.md` | The shot table still describes the abandoned plan: a timer on a stuck part, a pipeline animation, "a 12-part CAD assembly" (01310 has 8 parts), `replay_test_totals.pdf`, and an end card reading "Code, data and paper" (data is not published). Only the header note says it changed. | compare with `video/build_video.sh` captions |
| MINOR | `video/demo.mp4` 0–6 s | The burned-in caption band partly covers the render's own header text; faint ghost text is visible behind and beside the caption. | `experiments/2026-11-26_audit_phase5_1_repro/vframe_2.png` |
| MINOR | `talk/speaker_notes.md` item 7 | "35–40% below both ASAP models (39% … 34% …)": 34% falls outside "35–40%". The paper says 34–39%. | `grep -n "35–40" talk/speaker_notes.md` |
| MINOR | `ai-novelty-feasibility-audit.md` Final status | "The test set's larger, interpenetrating assemblies exposed a distribution shift" states as fact what the paper and REPORT call a "plausible cause (not tested)". | `grep -n "exposed" ai-novelty-feasibility-audit.md` |
| MINOR | `reports/campaign/NEEDS_AARON.md` | A stale line remains: "README.md is still the original puzzle proposal; it is rewritten in Phase 5". It has been rewritten. | `sed -n 4p reports/campaign/NEEDS_AARON.md` |

VERDICT: FAIL
