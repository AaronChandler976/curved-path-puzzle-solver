# Things only Aaron can do

(filled in as the campaign goes)
- (optional, timing) During the final live run (started 2026-11-24 23:10, ~2 days), the open desktop apps (Firefox,
  Chrome, gnome-shell, localsearch) use about 0.5 CPU cores together. That sits right at the idle guard's busy threshold,
  so about 23% of runs are flagged confounded and re-run. Closing Firefox/Chrome while it runs would cut the re-runs. Nothing
  in the project depends on it.
- **License:** the repo has no LICENSE file. Choosing one (e.g. MIT) is your decision; the README says none is chosen yet.
- **Video link (required):** upload `video/demo.mp4` (YouTube unlisted or Google Drive), then replace VIDEO-LINK-PLACEHOLDER
  in `paper/main.tex` (`\videourl`) and VIDEO-LINK in `README.md`, recompile the paper
  (`cd paper && conda run -n paper tectonic -X compile main.tex`), commit and push to `main`.
- **Submissions:** talk PDF on Canvas (Dec 3); paper PDF, repo URL and video link by Dec 15.
- (optional) The labels (`data/labels/pilot_v2/`, ~94 MB) were not published. They derive from the Assemble Them All
  data, so publishing them is your call.
