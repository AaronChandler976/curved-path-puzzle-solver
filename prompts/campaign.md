# Campaign: finish the CMPE 258 project end to end, as fast as possible

You are running unattended on Aaron's Ubuntu desktop until everything is done (at most until 2026-12-13).
Aaron has handed the project over: nobody will answer questions. Read
`CLAUDE.md` (including the **Campaign rules** at the bottom) and `docs/PLAN.md`
first and follow them exactly. Their hard rules outrank anything here.

**Campaign folder:** `reports/campaign/`. STATUS.md, PLAN_LOG.md, DECISIONS.md,
BLOCKERS.md, AUDITS/ and NEEDS_AARON.md go there. Each phase also keeps its own
run folder (`reports/run05/`, `reports/final_eval/`, …) as before.

## Goal
Deliver, with every number backed by a logged run:
1. A rigorous final result: the pre-registered comparison (`docs/PREREG_run05.md`)
   evaluated **once** on the fresh v2 test set.
2. The **talk** (Thu Dec 3, 10 minutes) and its slides (Canvas, .pdf or .pptx).
3. The **final submission** (due Tue Dec 15): a LaTeX conference paper (PDF,
   vector graphics only), a clean public GitHub repo, and a ≤ 2-minute demo video.

Course context you must keep in mind (read `docs/course/` once it exists; Phase 0
creates it from this prompt's appendix):
- Option 1 requirements: train models; ≥ 2 recent open-source SOTA methods used
  or compared against (CMG-RRT, ASAP, Assemble Them All data); ≥ 2 technical
  interventions (GNN vs MLP; cost-aware survival vs BCE; plus PointNet,
  tail-aware objective); evaluation-first with baselines and a working demo.
- Dr. Liu's feedback (appendix): realistic CAD assemblies, valid states from known
  feasible sequences, compare random / heuristics / MLP / GNN with the same
  planner. The paper and talk must show plainly how each point was addressed.
- Novelty vs ASAP and Cebulla 2023: we model query **cost** and **censored
  timeouts** for a curved/rotational SE(3) planner, and order queries by expected
  cost. Never claim "a GNN predicts the next removable part" as ours.

## Pace: as fast as possible (Aaron's instruction)
Start each phase **the moment the previous one has passed its audit**. Never wait
for a date. The desktop is dedicated to this project (Aaron's other project runs
on the SJSU HPC), so keep it busy: while a timed job runs, do the untimed work
of the same or the next phase that doesn't need the CPU/GPU (writing, figure
scripts, LaTeX skeletons, literature checks), as CLAUDE.md allows.

| Phase | Starts | Ends with | Latest allowed |
|---|---|---|---|
| 0 Finish run 04 | now | v2 labels, frozen v2 split, PREREG §8 filled | — |
| 1 Run 05 training | Phase 0 audited | every PREREG variant trained, 5 seeds, val only | — |
| 2 Exploration on val | Phase 1 audited | `docs/PREREG_addendum.md` + `configs/final_frozen.yaml` committed | freeze by Sat Nov 28 18:00 |
| 3 Final test (once) | freeze audited | `reports/final_eval/` | Mon Nov 30 12:00 |
| 4 Talk | Phase 3 audited | `talk/` slides PDF + speaker notes | Tue Dec 1 18:00 (talk Thu Dec 3) |
| 5 Paper, repo, video | Phase 4 audited | `paper/main.pdf`, README, `video/demo.mp4`, main updated | Sat Dec 12 18:00 |

The "latest allowed" times are limits, not targets. Phase 2 ends as soon as its
list below is done (or at the limit, whichever comes first); don't invent extra
exploration to fill time. If a phase would miss its limit, shrink it by its own
priority list and record the slip in PLAN_LOG.md. The talk (Dec 3) and the final
submission (Dec 15) are fixed dates; everything else should finish well before them.

## Working rules
- **Never stop to ask.** Decide, record it (choice / alternatives / why) in
  `reports/campaign/DECISIONS.md`, keep going. Things only Aaron can do go in
  `reports/campaign/NEEDS_AARON.md` (e.g. an `apt install` line, uploading the
  video, submitting). Keep working around them.
- **STATUS.md** format: STATE (RUNNING / DONE), DEADLINE, CURRENT PHASE and
  STEP, BACKGROUND JOBS (pid, what, log), DONE SO FAR (with evidence paths),
  NEXT ACTION. On start: read it, check PIDs, resume. Don't redo finished work.
- **Lean toward the more complete and robust method**, even when it costs more
  runs or compute (Aaron's standing preference), inside the schedule.
- **Timebox.** After 3 failed fix attempts on the same error, BLOCKERS.md, move on.
- **Commit after every step and push.** Gates pass only with evidence on disk.
- **Audit after every phase** (Campaign rules: independent auditor). A phase is
  not done until its audit passes or every finding is fixed and re-audited.

## Phase 0: finish run 04
Run 04's own runner was stopped when the campaign took over; its background
jobs (e.g. T7 labelling) may still be running. Read `reports/run04/STATUS.md` and
`prompts/run_04.md`, check the listed PIDs, and resume run 04's stages in
its own folder (`reports/run04/`) until T7 and T8 have passed. If T9 (elk 4 h)
hasn't run, **defer it to Phase 5** (it is a reproduction check and must not
delay the test). Write `reports/run04/REPORT.md` and set run 04's STATUS to DONE
(note T9 deferred). Also create `docs/course/` with the appendix texts below.
Audit.

## Phase 1: run 05 training (follow `docs/PREREG_run05.md` exactly)
Folder `reports/run05/`. Train every registered variant with the registered grid,
selection rule and seeds; val only; never open test labels. Report training
curves, selected configs, val replay tables (main and CMG-RRT-only configs),
C-index, ECE. Add **latency and memory profiling** (the final rubric asks for it):
ranker inference time per state (CPU and GPU, batch 1 and batched), parameter
count, peak memory, versus the planner time it saves. Audit.

## Phase 2: exploration on val (this list, then freeze)
The registered comparison is fixed. Here you may try to make the method better,
**on val only**, as clearly labelled *exploratory* variants:
- Attack the tail (run 03: 5% of states ≈ 60% of cost): e.g. ranking by
  expected cost including the P(unsolved)·T term, risk-averse orderings,
  restart/budget policies, a listwise loss.
- Stronger current encoders (e.g. GATv2, a graph transformer, a pretrained
  point-cloud encoder) if they are fair (same budget rule).
- 5-fold group cross-validation over train+val for the final candidates, as a
  robustness check of the val ranking (report it; it doesn't change the
  registered selection rule).
- Optional, qualitative only and never part of test: an EV-battery-module CAD
  case study, only if a public model is downloadable without a login.
Each exploratory variant: same per-config budget, 5 seeds, logged. Before the
freeze, write `docs/PREREG_addendum.md` (which exploratory variants enter the
test, as "post-registration, exploratory", and why) and `configs/final_frozen.yaml`
(every checkpoint path that will be tested, with sha256). Commit both. Audit the
freeze: nothing in either file may depend on test data.

## Phase 3: the final test (exactly once)
Folder `reports/final_eval/`. Write the marker `data/splits/.v2_test_evaluated`
when you first read test labels; if it already exists, never re-run the test
evaluation, only reporting from its saved outputs.
1. **Replay** on the v2 test set, main and CMG-RRT-only configs, every frozen
   method, the PREREG metrics, CIs, tests, Holm, subsets, and the §7 decision rule.
2. **Live** full disassembly per PREREG §6, through the idle guard. Priority if
   time runs short: replay > live with all methods at 1 seed (val-chosen) >
   live with all 5 seeds. Any shrink is a reported deviation.
3. Failure analysis (allowed after the test because it selects nothing):
   the costliest states and assemblies per method, why they failed (timeouts,
   wrong p, wrong c), with renders. Audit.

## Phase 4: the talk (10 minutes, Thu Dec 3)
Folder `talk/`. Follow the course's recommended flow (appendix): application &
problem → existing landscape & baselines → what we did and why → experiments &
ablations (the core) → key insights & negative results. About 12–14 slides,
visual, little text, every number from `reports/final_eval/` or earlier logged
runs (development results labelled as such).
- Build it as LaTeX Beamer compiled to PDF with tectonic (conda env `paper`,
  conda-forge; no sudo), with vector figures (matplotlib → PDF, TikZ diagrams).
- Write `talk/speaker_notes.md`: what to say per slide, about 45 s each, plus the
  3 questions most likely to be asked and short answers.
- Include the demo animation (GIF/MP4) as a backup slide and a separate file.
Audit (numbers vs logs, timing ≤ 10 min at a normal speaking pace).

## Phase 5: paper, repo, video
1. **Paper** `paper/`: IEEE conference format (IEEEtran), compiled with tectonic
   to `paper/main.pdf`. Structure from the final-report appendix. Vector graphics
   only: architecture diagram (TikZ), pipeline flowchart, all plots as PDF. A
   bulleted contributions list. Related work from a **fresh literature check**
   (WebSearch; 2023–2026). **Every reference must be real and verified** (title,
   authors, venue, year checked on the web; record the URL in `paper/refs_check.md`).
   No citation you could not verify.
2. **Negative results and failure analysis** are a full section (the rubric values
   them): the 18.5% invalid v1 paths and the coarse goal-edge check, the 124 missed
   straight pulls (start never tested), the learned SDF "solving" puzzles through
   parts, run 03's tail-dominated totals, anything the final test shows.
3. **elk 4 h run** (deferred T9), alone, through the guard. Report it in the paper.
4. **Repo:** a clean README (project, results table from final_eval, environment
   setup with conda commands, how to run labelling / training / evaluation /
   demo, where checkpoints and labels are — publish small checkpoints and the v2
   split as a GitHub release with `gh release create` if `gh` is authenticated;
   otherwise NEEDS_AARON). Remove the stale `cmpe258-project-build-kit/` folder
   (git rm). Make sure `literature-survey.md` and `ai-novelty-feasibility-audit.md`
   are current. Then merge the campaign branch into `main` (Campaign rules) so the
   default branch is the final version.
5. **Video** `video/demo.mp4`, **≤ 1 min 55 s**, H.264 (`-preset veryfast`),
   1080p, burned-in captions, no voice required: hook in the first 5 s, the
   problem in one picture, the system, a real CMG-RRT disassembly with the GNN's
   query order, the headline result chart, one negative result, repo link.
   ffmpeg from conda-forge. Add `video/script.md`. NEEDS_AARON: upload to
   YouTube (unlisted) or Drive, then put the link at the top of the paper (leave a
   clearly marked `\newcommand{\videourl}{...}` placeholder).
6. **Final audit** of everything (Campaign rules), fix, re-audit. Then set
   STATE: DONE and write `reports/campaign/FINAL.md`: what to submit, where each
   file is, and the exact remaining steps for Aaron.

## Appendix: course texts (verbatim summaries; copy into docs/course/ in Phase 0)

**Professor feedback on the proposal (Dr. Liu):** The puzzle application is
niche and the link to industrial disassembly (EV battery teardown, recycling) is
indirect; move evaluation to simulated mechanical assemblies or battery/module
tasks with realistic CAD geometry, keeping the learned query-ordering +
motion-planning framework. DeepCubeA-style backward rollouts don't guarantee
physically valid states; instead use assemblies with known feasible
(dis)assembly sequences and train a GNN to rank which component gets the next
expensive motion-planning query. Compare random ordering, simple
geometric/contact heuristics, an MLP and the GNN using the same motion planner.

**Presentation (Dec 1/3; Aaron presents Thu Dec 3; 10 min; slides .pptx or .pdf
uploaded after the talk, due Dec 3, closes Dec 10):** tell a clear, visual,
logically cohesive engineering story; no text-heavy slides or raw output dumps.
Flow: (1) application & problem context: target application, operational
scenario and constraints (latency, hardware, domain shift, safety), the exact
problem; (2) existing technical landscape & baselines: how SOTA/open-source
baselines approach it and what gaps remain; (3) what we did: pipeline, model
choices, data curation, modifications, and why each design decision;
(4) experiments & ablations (core): controlled quantitative evaluations,
latency/resource trade-offs, qualitative visual comparisons, ablations isolating
components; (5) key insights & negative results: what failed, why, how it was
diagnosed.

**Final submission (due Tue Dec 15 23:59; hard cutoff Wed Dec 16 17:00; 100 pts):**
(1) Final report, 50 pts: LaTeX conference format (IEEE, arXiv, CVPR, ICRA, IROS,
CoRL…), compiled PDF, written like a real research paper; all diagrams and plots
vector graphics. Structure: title, authors, clickable links to repo and video;
abstract 150–250 words with key quantitative results; 1 Introduction (application,
importance, limits of existing solutions, bulleted contributions); 2 Related Work;
3 Methodology / System Architecture (pipeline, architecture, math/losses, dataset
preparation, design choices, vector architecture diagram); 4 Experiments &
Ablations (hardware/software setup, metrics, baselines, latency/memory profiling,
qualitative visualizations, ablations); 5 Failure Analysis, Negative Results &
Limitations (concrete examples, root-cause diagnosis); 6 Conclusion & Future Work;
References. (2) GitHub repo, 30 pts: public; clean README with structure,
environment setup, how to run training/evaluation/inference, links to checkpoints
or datasets; clear meaningful commit history. (3) Video demo, 20 pts: strictly
≤ 2 minutes, creative and engaging from the first second, shows the working demo
and visual results; YouTube (public/unlisted) or Google Drive link.
