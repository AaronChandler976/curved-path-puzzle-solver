# Audit phase4_2: 10-minute talk (Thu Dec 3), re-audit

Auditor: an independent subagent. Its instructions were `prompts/audit.md` plus the phase name and the paths. Date: 2026-11-26.
Scope:
- `talk/main.tex`, `talk/main.pdf`, `talk/speaker_notes.md`, `talk/demo.mp4`, `talk/figures/`
- `docs/course/*.md`

The previous audit is `reports/campaign/AUDITS/phase4_1.md`. Scratch files are in `experiments/2026-11-26_audit_phase4_2_repro/`. I ran no planner jobs, did not re-run the test evaluation and committed nothing.

## What was checked (and held)
- **Build.** I copied `main.tex` and `figures/` into scratch and ran `conda run -n paper tectonic -X compile main.tex`.
  - rc 0, 15 pages.
  - `pdftotext` of the rebuild is identical to the committed `talk/main.pdf`, which is current with `main.tex` (both from commit cc2c409).
  - Log: `tectonic.log`. Two cosmetic warnings: an overfull vbox of 5.4 pt (l.139) and an overfull hbox of 5.1 pt (l.161).
  - Renders: `montage_all.png`, `hi-06..11.png`.
- **Figures.** All 4 PDFs in `talk/figures/` contain 0 raster images, so they are vector.
  - `budget_policy.pdf` is byte-identical to `reports/final_eval/figures/`.
  - The other two match in text.
  - `demo_frame.png` is a video frame, so being raster is acceptable.
- **Demo.**
  - `talk/demo.mp4` is byte-identical to `experiments/2026-11-26_demo_01310/demo_01310.mp4`.
  - ffprobe: 13.375 s, 1920×1080 h264. That is under 2 min.
  - Slide footer "19.3 s planner time vs 20.5 s in the live run" matches the sources: demo `results.jsonl` planner_s 19.32 against `experiments/2026-11-24_final_eval_live/results.jsonl` `gnn_survival#s101` on 01310, planner_s 20.52.
  - Part 7 was decided by `stage: cmgrrt` (`precheck_free: false`), with `path_max_rot_deg` 102.2.
- **Numbers re-traced:**
  - Replay ratios, CIs and Holm p (slides 8–9) match `reports/final_eval/REPORT.md` §2 and `replay.md`. The clean-subset CI upper bound of 1.001 matches `replay.md` l.60. "39% below zero-shot / 34% below retrained" (notes item 7) matches 0.613 and 0.660.
  - Live (slide 10) matches `REPORT.md` and `live.md`: 0.915 [0.819, 1.015] with Holm 0.13, ASAP-zs 0.789, ASAP-retrained 0.906 [0.827, 0.994], ListNet 0.797, 17,697 runs.
  - Budget policy (slide 11): totals 7,202→2,008 and 7,595→1,904, and the ratio 0.948 [0.820, 1.095], all match `replay.md` §"Exploratory budget policy".
    - I recomputed the saving for every ordering in that table: 72.1% (fewest contacts) to 79.0% (ASAP-zs).
    - Live: fewest contacts −51.0% (23,002→11,273). GNN-Surv ratio 0.514 (seed 101 vs 5-seed mean).
    - "Timeouts ran a median 31 s" matches `REPORT.md` §4b (31.19 s).
  - Latency table (slide 12) matches `reports/run05/profile.md`: 32,392 / 61,192 / 1,703,681 params; 0.12 / 1.89 / 7.04–7.07 ms; 2.41 ms features; 11 / 904 / 3,849 MB. 30 s / 2.5 ms ≈ 12,000.
  - Failure analysis (slide 13) matches `failure_analysis.md`: 89%/77%, 85 states, +3,153 s, 436 states / 3,240 s. The 89.5% train figure is from the phase4_1 recomputation.
  - Run 04 numbers (slides 7, 14) match `reports/run04/REPORT.md`, `oracle_v2.md`, `labels_v2.md` and `sdf_puzzles.md`: 2,022, 41,913, 12.6 h, 156 stuck, 95–98%, 123/124, 18.5%, 3/3 and 0/3.
- **References.**
  - Simon & Kadane 1975 is now verified on the web: dblp record journals/ai/SimonK75, Artificial Intelligence 6(3):235–247.
  - CMG-RRT, ASAP and Cebulla 2023 were verified in phase4_1. Their slide citations are unchanged.
- **Novelty.** Slide 4 credits removability prediction to Cebulla and ASAP. The claim made is cost plus censored timeouts. Notes item 4 says explicitly that "a GNN predicts the next removable part" is not claimed.
- **Course flow** (`docs/course/presentation.md`):
  - application and problem: slides 2–3
  - landscape: slide 4
  - what we did: slide 5
  - demo, a qualitative visual: slide 6
  - data: slide 7
  - experiments, ablations, live, budget and latency: slides 8–12
  - failure analysis and negative results: slides 13–14
  - summary: slide 15
  - The order is followed. Option 1's "working demo" is now in the main flow.
- **Professor feedback.**
  - Battery: slide 2 says no battery models were evaluated.
  - Valid states: slide 7 states all three caveats from `professor_feedback.md`.
  - Same planner: slide 8 footer.
  - Random / heuristic / MLP / GNN: all appear on slides 8–9.
- **Timing.**
  - The spoken text of items 1–14 plus 5b is 954 words by `wc` (headers included). That is 6.4–7.3 min at 150–130 wpm, plus 13 s of video.
  - It fits in 10 minutes. See the MINOR finding on the stale timing note.

## Status of phase4_1 findings
| phase4_1 finding | status |
|---|---|
| MAJOR: valid-states overclaim (slide/notes) | **Resolved.** Slide 7 title is now "states reached by verified disassemblies". The three caveats are on the slide (planner-found sequences, 156/2,022 stuck, 63% interpenetrating CAD valid only up to the allowance) and in notes item 6. |
| MAJOR: demo only in backup, never played | **Resolved.** Demo slide 6 is in the main flow and notes item 5b plays `demo.mp4` (20 s). |
| MINOR: text-heavy slides | Partly resolved. Latency is now a table. Problem, Data, Live, Negative results and Summary are still bullet-only (see below). |
| MINOR: "72% for every ordering" | Resolved. Now "−72% to −79%" in replay and "about −50%" live for the two orderings run, which matches the recomputation. Nit below. |
| MINOR: learned SDF "puzzle 3/3" | Resolved. The slide now says "bundled tight assembly" (PLAN.md l.102 calls 16505 a bundled puzzle), and the exact check 0/3 is stated. |
| MINOR: "79% 3–8-part" | Resolved (89.5%). |
| MINOR: failure analysis single seed not labelled | Partly resolved. Bullet 3 and notes item 12 say seed 101. The figure and bullet 2 (85 states) do not. See below. |
| MINOR: shift stated as fact / "confident timeouts are the reason" | Partly resolved. Slide 13 and notes item 12 now say "plausible cause (not tested)". Summary slide 15 still says "confident timeouts are the reason". See below. |
| MINOR: 0.04 s median footer | **Not resolved, now mis-stated** (see below). |
| MINOR: soft T = 30 s not mentioned | Resolved. Slide 11 says the budgets are soft and that timeouts ran a median of 31 s. |
| MINOR: battery not evaluated | Resolved (slide 2). |
| MINOR: same planner not stated | Resolved (slide 8 footer). |
| MINOR: budget figure mixes seeds | Resolved in text. Slide 11 says "GNN-Surv at one seed, 101", and the figure label says "live: seed 101". |
| MINOR: "costs nothing measurable" | Resolved. Notes item 11 now says "about 2.5 ms … negligible". |
| MINOR: overfull hbox | Not resolved (cosmetic). There is also a new overfull vbox (see below). |

## Findings
| severity | file | what is wrong | how to verify |
|---|---|---|---|
| MINOR | `talk/main.tex` slide 2 footer | The footer reads "median 0.037 s over its 624-query oracle-validation set, all outcomes". That is wrong: 0.037 s is the median of the **500 random** queries under v2a only. On the 124 misses the v2a median is 0.39 s, so the 624-query median is not 0.037 s. Should read "median 0.037 s over 500 random validation queries (oracle v2), all outcomes". | `reports/run04/oracle_v2.md` T4.4 table, rows "124 misses / v2a" (0.39) and "500 random / v2a" (0.037) |
| MINOR | `talk/main.tex` slide 15 | The summary still says "It does not beat a simple contact heuristic … **confident timeouts are the reason**." The decomposition behind it is replay and seed 101 only. Slide 13 itself frames the deeper cause as untested. Live, GNN-Surv is 0.915 (n.s.), not worse. Suggest "most of its replay loss comes from confident timeouts". | Slide 15 vs `reports/final_eval/failure_analysis.md` header (seed 101) and `REPORT.md` §5 |
| MINOR | `talk/main.tex` slide 13, `talk/figures/failure_scatter.pdf` | The slide mixes bases. Bullet 1 (89%/77%) uses seed-mean totals, while bullets 2–3 and the scatter are seed 101 (`scripts/failure_analysis.py` l.57 vs l.66). Only bullet 3 says "(seed 101)". The figure title and bullet 2 do not. | `failure_analysis.md` header; `pdftotext talk/figures/failure_scatter.pdf -` |
| MINOR | `talk/main.tex` slide 6, `talk/speaker_notes.md` item 5b | "Part 7 **needs** a 102° rotation" and "a 102° rotation that **only** CMG-RRT finds" overclaim. What the log shows is that the straight-pull pre-check failed (`precheck_free: false`) and CMG-RRT found a path whose maximum rotation is 102.2°. An RRT path is not minimal, so "needs" 102° and "only CMG-RRT" are not shown. Suggest "CMG-RRT found a path with a 102° rotation after the straight pull failed". | `experiments/2026-11-26_demo_01310/results.jsonl`, last state, query for part 7 |
| MINOR | `talk/main.tex` slide 7 | "18.5% of its successes went through parts at fine resolution" is stronger than the source. `reports/run04/REPORT.md` l.95 describes these as "marginal dips below −ε" and notes l.38 a caveat: v1 samples were unseeded, so the check used a seeded draw. Slide 14's "18.5% invalid paths" is accurate. | `reports/run04/REPORT.md` l.36–40, l.95 |
| MINOR | `talk/speaker_notes.md` header and "Timing check" | Stale. The header says "13 slides + backup", but there are now 14 content slides plus the title and no backup. The timing check says "about 860 words … 5.8–6.6 min", but `wc` now gives 954 words (6.4–7.3 min). The per-slide allocations add up to 605 s, more than 600 s, so the plan leaves no slack. It still fits at a normal pace, but update the numbers and rehearse with a timer. | `awk '/^1\. \*\*Title/{f=1} /^Timing check/{f=0} f' talk/speaker_notes.md \| wc -w`; sum of "(N s)" = 605 |
| MINOR | `talk/main.tex` slide 11 | "−72% to −79% for every ordering": random was not run under the policy (it is not in the `replay.md` policy table). Say "every ordering tested". The summary slide already does. | `reports/final_eval/replay.md` l.530–548 |
| MINOR | `talk/main.tex` slides 3, 7, 10, 14, 15 | Course rule: "visual, no text-heavy slides". Five of the 14 content slides are bullets only. Data (slide 7) has 5 dense bullets. Live (slide 10) repeats numbers that the slide-8 figure already shows. | `experiments/2026-11-26_audit_phase4_2_repro/montage_all.png` |
| MINOR | `talk/main.tex` l.139 (main result), l.161 | Overfull vbox of 5.4 pt (new) and overfull hbox of 5.1 pt. On slide 8 the footer wraps to two lines and sits against the frame number. Cosmetic. | `experiments/2026-11-26_audit_phase4_2_repro/tectonic.log`, `hi-08.png` |

No BLOCKER or MAJOR findings. Both phase4_1 MAJORs are resolved, and every number on the slides traced to a logged source. The remaining items are wording and cosmetic.

VERDICT: PASS
