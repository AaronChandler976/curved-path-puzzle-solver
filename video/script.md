# Demo video script (≤ 1:55, 1080p, H.264, burned-in captions, no voice)

**Built:** `video/demo.mp4` (`bash video/build_video.sh`): 112.8 s, 1920×1080, H.264 (veryfast), no audio. Eight cuts, as
in the table below; the actual captions are in `video/build_video.sh`. The original plan of a stuck-part timer and a
pipeline animation became a text card and the "What we built" slide.

Every number shown comes from `reports/final_eval/` (test, evaluated once). Shots are rendered from logged runs
(`scripts/render_demo.py` / `scripts/render_path.py`) or from report figures. Nothing in the video is simulated
beyond replaying logged planner paths.

| time | picture | caption (burned in) |
|---|---|---|
| 0:00–0:06 | the real CMG-RRT rotation removal (test assembly 01310, last state) | "Which part can come out next? Asking the planner costs 0.04 s ... or 30 s." |
| 0:06–0:16 | text card | "Each removal test is a CMG-RRT motion-planning query. / A timeout (30 s) proves nothing - and it dominates the cost. / So - which part should we ask about first?" |
| 0:16–0:30 | talk slide "What we built" | "GNN + survival head - P(success) and expected cost per part; query in p/c order." |
| 0:30–0:55 | the whole demo disassembly of 01310 (GNN-Surv order, p and c, removals from logged paths) | "A real test assembly - the learned query order, fresh CMG-RRT queries." |
| 0:55–1:15 | test totals figure (replay and live) | "Fresh test set - cheaper than ASAP, no better than fewest contacts." |
| 1:15–1:30 | failure scatter | "Why - a few confident timeouts on larger, unseen assemblies." |
| 1:30–1:45 | budget-policy figure | "Biggest win, not learned - try every part for 3 s first (-72% replay, -50% live)." |
| 1:45–1:53 | end card with title, repo URL and author | — |

Notes
- Hook in the first 5 s: the fast curved removal plus the 0.04 s vs 30 s contrast.
- Build with ffmpeg from the `paper` conda env: `-c:v libx264 -preset veryfast -pix_fmt yuv420p -vf scale=1920:1080`.
  Captions are burned in with the `drawtext`/`subtitles` filter from `video/captions.srt`.
- Check the length with `ffprobe` (must be ≤ 115 s).
- NEEDS_AARON: upload as unlisted (YouTube) or to Drive, then put the link in `paper/main.tex` (`\videourl`).
