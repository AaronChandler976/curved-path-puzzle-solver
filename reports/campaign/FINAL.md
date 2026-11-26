# Campaign final handover

## What to submit
| deliverable | due | file | status |
|---|---|---|---|
| Talk slides (10 min, Thu Dec 3) | Dec 3 (Canvas closes Dec 10) | `talk/main.pdf` (speaker notes: `talk/speaker_notes.md`; video to play: `talk/demo.mp4`) | ready (audit phase4_2 PASS) |
| Final report (50 pts) | Tue Dec 15 23:59 | `paper/main.pdf` (6 pages, IEEEtran; audit phase5_2 PASS) | ready except the video link |
| GitHub repo (30 pts) | Dec 15 | https://github.com/AaronChandler976/curved-path-puzzle-solver (branch `main`; release v1.1-final with the 50 checkpoints and the split; v1.0-final has the same assets on an earlier commit) | merged |
| Demo video ≤ 2 min (20 pts) | Dec 15 | `video/demo.mp4` (112.8 s, 1080p) → upload (YouTube unlisted or Drive) | built; upload needed |

## Remaining steps for Aaron
1. Upload `video/demo.mp4` (YouTube unlisted or Google Drive, link viewable by anyone with it).
2. Put the link in `paper/main.tex` (`\newcommand{\videourl}{...}`) and in `README.md` (VIDEO-LINK), then recompile:
   `cd paper && conda run -n paper tectonic -X compile main.tex`, and commit.
3. Upload `talk/main.pdf` to Canvas after the talk; submit `paper/main.pdf`, the repo URL and the video link by Dec 15.
4. See `reports/campaign/NEEDS_AARON.md` for the rest (license choice, optional items).

## Where the results are
- Final (test, evaluated once): `reports/final_eval/REPORT.md`
- Training and validation: `reports/run05/REPORT.md`; exploration and CV: `reports/explore/REPORT.md`
- Oracle and data: `reports/run04/REPORT.md`
- Decisions: `reports/campaign/DECISIONS.md`; audits: `reports/campaign/AUDITS/`

## Audit trail
Every phase passed an independent audit after its fixes: `reports/campaign/AUDITS/` (phase0_1/2, phase1_1/2,
phase2_1/2, phase3_1/2/3, phase4_1/2, phase5_1/2). Every number in the reports links to a run folder under
`experiments/`.

## Headline results (for the submission text)
- Test set: 347 fresh assemblies, pre-registered, evaluated once.
- GNN-Surv vs fewest contacts: replay 1.055 [0.887, 1.257] (Holm p 0.43); live 0.915 [0.819, 1.015] (Holm p 0.13).
  It does not beat the heuristic.
- Cheaper than ASAP zero-shot and ASAP retrained in replay (0.613, 0.660) and live (0.789, 0.906).
- A two-pass 3 s budget policy cuts replay planner time by 72–79% for every ordering (exploratory).
