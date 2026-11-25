# Demo video script (≤ 1:55, 1080p, H.264, burned-in captions, no voice)

Every number shown comes from `reports/final_eval/` (test, evaluated once). Shots are rendered from logged runs
(`scripts/render_demo.py` / `scripts/render_path.py`) or from report figures. Nothing in the video is simulated
beyond replaying logged planner paths.

| time | picture | caption (burned in) |
|---|---|---|
| 0:00–0:05 | a 12-part CAD assembly; one part slides out along a curved path, fast | "Which part can come out next? Asking a motion planner costs 0.04 s… or 30 s." |
| 0:05–0:15 | the same assembly, parts highlighted one by one; a timer runs to 30 s on a stuck part | "Each question is a CMG-RRT query. A timeout proves nothing, and it is expensive." |
| 0:15–0:30 | pipeline animation: CAD → contact graph → GNN → p and c per part → query order → planner | "We predict success probability AND expected cost, timeouts included, and query in p/c order." |
| 0:30–0:55 | a real live disassembly from `experiments/2026-11-24_final_eval_live/` (GNN-Surv order shown as numbered labels; each removal replayed from its saved path) | "A real disassembly with the learned query order (fresh planner queries)." |
| 0:55–1:15 | the test-set bar chart (`reports/final_eval/figures/replay_test_totals.pdf`) | "Fresh test set, 347 assemblies, pre-registered: cost-aware ordering beats ASAP and removability-only ordering… but ties a simple contact heuristic." |
| 1:15–1:30 | failure example: the model's confident first pick times out (p ≈ 1.0, 30 s) | "Why: confident timeouts on large, unseen assemblies." |
| 1:30–1:45 | budget-policy bars: 7,202 s → 2,008 s | "The biggest win wasn't learned: try every part for 3 s first. −72% planner time." |
| 1:45–1:55 | repo URL and title card | "Code, data and paper: github.com/AaronChandler976/curved-path-puzzle-solver" |

Notes
- Hook in the first 5 s: the fast curved removal plus the 0.04 s vs 30 s contrast.
- Build with ffmpeg from the `paper` conda env: `-c:v libx264 -preset veryfast -pix_fmt yuv420p -vf scale=1920:1080`.
  Captions are burned in with the `drawtext`/`subtitles` filter from `video/captions.srt`.
- Check the length with `ffprobe` (must be ≤ 115 s).
- NEEDS_AARON: upload as unlisted (YouTube) or to Drive, then put the link in `paper/main.tex` (`\videourl`).
