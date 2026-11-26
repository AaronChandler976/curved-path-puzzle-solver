# Audit phase5_2: final audit, re-audit (paper, repo, video, campaign)

Auditor: independent subagent, instructions `prompts/audit.md` only. Date 2026-11-26.
Scratch and logs: `experiments/2026-11-26_audit_phase5_2_repro/` (`pytest.log`, `tectonic.log`, `help_*.log`,
`pip_pins.txt`, `page-*.png`, `vframe_*.png`). I ran no planner jobs, did not re-run the test evaluation, did not touch
`data/splits/.v2_test_evaluated`, and committed nothing.

State audited: campaign branch `c060076` = `origin/run/2026-11-24-campaign`; `main` = `origin/main` = `8df2c15`, a
`--no-ff` merge of `c060076` (`git diff main HEAD` is empty).

## What was re-checked and holds
- **Compile:** a copy of `paper/` builds with `conda run -n paper tectonic -X compile main.tex` (exit 0, 6 pages). The
  PDF is the same size as `paper/main.pdf` (667,920 B) and has identical `pdftotext` output. There are no
  undefined-reference warnings. The TU/ptm font-shape warnings are substitutions, and `pdffonts` shows embedded
  NimbusRomNo9L (Times).
- **Vector graphics:** `pdfimages -list` finds 0 raster images in `paper/main.pdf` and in all 4 `paper/figures/*.pdf`.
- **Tests:** `env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 conda run -n disasm python -m pytest` gives 36 passed,
  exit 0 (`pytest.log`).
- **README:** all 9 scripts named in "How to run" answer `--help` with exit 0 (`help_*.log`).
- **Test discipline:**
  - The marker content is unchanged since 1905865 (2026-11-24 23:09:11; first read 23:08:45).
  - The addendum and frozen config were last committed at a13b397 (23:04:31), before the marker.
  - The marker's mtime (Nov 26 14:23) comes from the 14:24 `git checkout` in the reflog, not from a rewrite.
- **Release v1.0-final:** public, not a draft, with 3 assets (checkpoints tarball, SHA256SUMS, v2_split.json). Phase5_1
  verified the checksums, and the assets have not changed.
- **No large data or secrets:**
  - The largest tracked file on `main` is `video/demo.mp4` (2.2 MB).
  - No `.pt`/`.pth`/`.ckpt`/mesh/`.env`/credentials files are tracked.
  - A grep for token and key patterns over `main` finds nothing.
- **References:** `paper/refs.bib` has not changed since the phase5_1 web check (last commit ad3dabb). I spot-checked
  the two newest arXiv entries again:
  - 2607.17898: "Manifold-Guided Motion Planning for Tight Assemblies", Livnat, Bilevich, Kleinbort, Halperin.
  - 2609.30599: "Learning-Accelerated Narrow-Phase Collision Detection via Check Ordering for Sampling-Based Motion
    Planning", Jiang, Wang, He, Duan.
  - The fix commit adds no new citations.
- **Video:** ffprobe (env `paper`) on `video/demo.mp4` reports 112.8 s, h264, 1920×1080, 30 fps, so it is ≤ 2 min.
  - In the frames at 2 s and 100 s, the caption band no longer covers the render's header: the frame is scaled to 970
    px and padded under a 110 px band.
  - `talk/demo.mp4` is 13.4 s.
- **New and changed text, traced to sources:**
  - *Budget policy, 72–79% replay:* from `budget_policies.3.totals` in
    `experiments/2026-11-25_final_eval_replay/results.json` against the Table I totals. Outside-in 74.0%, fewest
    contacts 72.1%, ASAP-zs 79.0%, MLP-BCE 76.4%, MLP-Surv 76.0%, GNN-BCE 75.1%, GNN-Surv 74.9%, Tail 74.5%,
    ASAP-retrained 78.7%.
  - *Budget policy, live:* "two orderings" matches the live `@b3` methods found in phase5_1.
  - *Baseline definitions:*
    - Outside-in and fewest contacts (with its tie order), hindsight optimal and random-as-expectation match
      `src/disasm/eval/replay3.py`.
    - Live outside-in and fewest contacts match `scripts/live_abd.py`.
    - The ASAP description (PointNet + 2×GATv2, one-positive BCE) matches `src/disasm/models/asap_train.py`.
    - The live ASAP zero-shot used the redmax graph in all 2,261 logged states.
  - *Grids:* hidden×lr×layers plus λ for Tail/ListNet, and ASAP's lr {1e-3, 3e-4, 1e-4} × batch {16, 32}. These match
    `docs/PREREG_run05.md` §2–3 and `docs/PREREG_addendum.md`.
  - *Demo:* the guarded live run of 01310 `gnn_survival#s101`, state 5-7, part 7 is a success in 19.52 s (attempt 0,
    not confounded). The demo re-run took 18.36 s. p and c are 0.97 and 1.33.
  - *Elk:* `our_cores` median 11.656 over 2,944 guard samples.
  - *Conclusion's "a few confident timeouts account for most of the loss":* in `failure_analysis.md`, 85 timeout-first
    states account for +3,153 s of the 3,404 s lost.
  - *Val share:* 89.6% 3–8-part (phase5_1 recomputation). "300 scored among the 306 never piloted" is consistent with
    phase5_1.
- **`environment-disasm.yml`:**
  - It now has `--extra-index-url https://download.pytorch.org/whl/cu128`.
  - `torch-2.11.0+cu128` and `torchvision-0.26.0+cu128` cp311 manylinux x86_64 wheels exist on that index.
  - All 79 other pip pins exist on PyPI (JSON API, each returned 200; `pip_pins.txt`).
- **Video-link placeholders** (`paper/main.tex` l.14, `README.md` l.6): still present. They are documented as a
  human-only step in `reports/campaign/NEEDS_AARON.md` (l.9–10) and `reports/campaign/FINAL.md` (l.7, 9, 12–13).
  Per the audit scope, this alone does not fail the audit.

## Status of phase5_1 findings

| phase5_1 finding | status |
|---|---|
| MAJOR conclusion overstates cost-aware vs removability | **Resolved.** §VI now says "cheaper than ranking by removability … in the main replay analysis, but not robustly across evaluations or encoders" |
| MAJOR "72% … about 50% live for every ordering" | **Resolved.** The abstract, Contribution 4 and README now say 72–79% replay for every ordering replayed and about 50% live for the two orderings run with it (numbers verified above) |
| MAJOR baselines undefined | **Resolved.** "Baselines and ablations" paragraph in §IV-A; definitions match the code (one wording slip, see new MINOR below) |
| MAJOR env yml cu128 pins uninstallable | **Resolved.** Extra index added; wheels exist; other pins exist on PyPI |
| MINOR video-link placeholder | Open, documented (Aaron-only) |
| MINOR demo 18.4 s unguarded | **Resolved** in the paper (19.5 s guarded, 18.4 s re-run). The DECISIONS disclosure that the demo is a fresh post-marker planner run on a test assembly is still only implicit (cmd.txt says "DEMO (not an evaluation)"). Open, MINOR |
| MINOR val "80%" | Resolved (89.6%) |
| MINOR "300 test assemblies never used in a pilot" | Resolved |
| MINOR latency: 11 MB, 7.0 vs 7.07, "confounded" | 11 MB and "confounded" resolved. The text still says 7.0 ms where the table says 7.07: open, trivial |
| MINOR "same grid" for every variant | Resolved |
| MINOR $c_i$ notation clash | **Open** (l.167 censoring time vs l.175 expected cost) |
| MINOR graph-transformer claim uncited | **Open** (l.88) |
| MINOR no software versions | **Open** (l.210 "PyTorch and PyG" without versions) |
| MINOR elk core framing | Resolved (paper §V(iv) and run04 REPORT §6) |
| MINOR "straight pull certified in about 0.04 s" source | **Open** (l.47). Not listed in DECISIONS #15 |
| MINOR Fig. 2 label size | **Open.** The figure is unchanged; labels are about 4–5 pt (`page-3.png`) |
| MINOR README "beats" | Resolved |
| MINOR README inputs not in git | Mostly resolved. The new paragraph omits `experiments/2026-11-23_run04_t6_pool/source.json` (step 2 `build_split_v2.py`) and `…/allowance.json`, which are untracked |
| MINOR video/script.md stale | Resolved |
| MINOR caption band covers header | Resolved |
| MINOR talk notes 35–40% | Resolved |
| MINOR novelty audit "exposed a shift" | Resolved |
| MINOR stale NEEDS_AARON line | Resolved |

DECISIONS #15 says all 19 MINORs were handled, but six of them (the open rows above) were not changed and not listed.

## Findings

| severity | file | what is wrong | how to verify |
|---|---|---|---|
| MINOR | `paper/main.tex` l.14, `README.md` l.6 | `VIDEO-LINK-PLACEHOLDER` / `VIDEO-LINK` are still in the paper and README. This is documented as Aaron-only (NEEDS_AARON l.9–10, FINAL l.12–13) and must be done before the Dec 15 submission. | `pdftotext paper/main.pdf - \| grep PLACEHOLDER` |
| MINOR | `paper/main.tex` §IV-A "Baselines" (l.217) | "*Random*: the exact expectation over uniformly random query orders" is true only for replay (`replay3.random_expectation`). Live random (Table I, 26,464 s) is one hash-seeded shuffle per state (`scripts/live_abd.py` `order_parts`, `method == "random"`). | `grep -n -A3 'if method == "random"' scripts/live_abd.py` |
| MINOR | `reports/campaign/DECISIONS.md` #15 | It states the 19 phase5_1 MINORs were fixed, but six were neither changed nor recorded as declined: $c_i$ clash, uncited graph-transformer claim, missing software versions, the source of "0.04 s", Fig. 2 label size, and 7.0 vs 7.07 ms. It should say which were declined and why. | table above; `git show c060076 -- paper/main.tex` |
| MINOR | `paper/main.tex` l.167/175 | $c_i$ is still both the censoring time and the expected cost (carried over). | read §III-C |
| MINOR | `paper/main.tex` l.88 | "graph-transformer models predict sequences step by step" still has no citation (carried over). | `grep -n graph-transformer paper/main.tex` |
| MINOR | `paper/main.tex` l.210 | No PyTorch/PyG/Python versions are given (carried over; they are in `environment-disasm.yml`). | `grep -n PyTorch paper/main.tex` |
| MINOR | `paper/main.tex` l.47 | "a straight pull is certified in about 0.04 s": the source median (0.037 s, `reports/run04/REPORT.md` §3) covers all queries in the validation sample, not straight pulls (carried over; the talk footer was corrected). | `grep -n 0.037 reports/run04/REPORT.md` |
| MINOR | `paper/figures/totals_replay_live.pdf` (Fig. 2) | Tick and method labels are about 4–5 pt at column width and hard to read in print (carried over). | `experiments/2026-11-26_audit_phase5_2_repro/page-3.png` |
| MINOR | `paper/main.tex` l.341 | "takes 7.0 ms" while Table III gives 7.07 (it would round to 7.1). | `sed -n 330,342p paper/main.tex` |
| MINOR | `README.md` "How to run" | The list of inputs not in git omits `experiments/2026-11-23_run04_t6_pool/source.json` (used by step 2) and `…/allowance.json` (used by the demo command in `cmd.txt`). Both are untracked. | `git ls-files --error-unmatch experiments/2026-11-23_run04_t6_pool/source.json` fails |
| MINOR | `reports/campaign/DECISIONS.md` | The demo (`experiments/2026-11-26_demo_01310`) is a fresh planner run on a test assembly after the marker, launched with `--no-guard`. It feeds no comparison, and the paper caption calls it a re-run, but DECISIONS does not record it against the campaign rule that post-marker work "only reads saved outputs" (carried over, partly addressed). | `cat experiments/2026-11-26_demo_01310/cmd.txt` |
| MINOR | release `v1.0-final` | The tag points to 092f54f, before the phase5 fixes. The release body says "Paper: `paper/main.pdf`", and the source snapshot at that tag holds the pre-fix paper (overstated conclusion, "72% for every ordering") and the uninstallable env file. The checkpoint assets are unaffected. Point readers to `main`, or note that the tag's source is superseded. | `git rev-list -n1 v1.0-final` gives 092f54f; `git rev-parse main` gives 8df2c15 |
| MINOR | `video/build_video.sh` cut 7 | The caption "-72% replay, -50% live" is under a figure whose GNN-Surv bars show -75% replay (7,595 to 1,904) and -49% live. -72% is the fewest-contacts saving only. Acceptable as rounding of the minimum, but "-72 to -75%" would match the picture. | `vframe_100.png` |
| MINOR | `reports/campaign/STATUS.md` l.10 | NEXT ACTION still reads "final audit (phase5_1) …". Update it after this audit. | `sed -n 10p reports/campaign/STATUS.md` |

No BLOCKER or MAJOR findings. All four phase5_1 MAJORs are resolved and verified against code, logs and package
indexes. The remaining items are MINOR, and the video link is a documented human-only step.

VERDICT: PASS
