# Audit phase3_3 (Phase 3: final test, evaluated once; third audit)

Auditor: independent subagent. My only instructions were `prompts/audit.md`, the phase name, the report and run paths,
and the two previous audits of this phase (`phase3_1.md`, `phase3_2.md`) so I could check their findings.
Date: 2026-11-26. HEAD at audit: 744f214 (the phase3_2 fixes are in e892878 and e9976c1).
Reproduction folder: `experiments/2026-11-26_audit_phase3_3_repro/`. It contains `cmd.txt`, `git_hash.txt`,
`marker_before.txt` / `marker_after.txt`, `budget_overrun/` + `.log`, the rebuilt `live.md`, `failure/` and
`failure_analysis.md`, `figures/`, `indep_calls.py` / `.log`, and `pytest.log`. I ran no planner job and did not re-run the
test evaluation. Before and after the audit, the marker `data/splits/.v2_test_evaluated` has the same sha256 (7242bbf5…) and
the same mtime (2026-11-24 23:08).

## Status of the phase3_1 findings
All 15 were resolved, as `phase3_2.md` already records. I re-checked the two content MAJORs (#2 and #3): the numbers are
now produced by a logged script (see phase3_2 #1 below). Phase3_1 #7 (interim Tail) and #11 (C-index) were partial in
phase3_2; both are now resolved (phase3_2 #5 and #8 below).

## Status of the phase3_2 findings

| # | phase3_2 severity | status | evidence |
|---|---|---|---|
| 1 | MAJOR (overrun numbers had no log) | **Resolved.** `scripts/budget_overrun.py` (committed e892878) states both definitions in its docstring and in its output. The run folder `experiments/2026-11-26_budget_overrun/` has `cmd.txt`, `git_hash.txt`, `stdout.log` and `budget_overrun.json`. REPORT §4 and §4b and DECISIONS #13 cite it. Re-running the script gives a **byte-identical** json. Every quoted value matches it: 12,444 / 2,663 / 31.19 / 73.2 / 8,163 / 24 / 89.1 / 158 / 127.7; 1,439 / 4.24 / 72.6 / 4,738 / 5,627 / 22,083. | `budget_overrun/budget_overrun.json` vs `experiments/2026-11-26_budget_overrun/budget_overrun.json` (diff empty) |
| 2 | MINOR (cited interim snapshot) | Resolved. REPORT §4 cites `live.md` (final) and names `live_registered.md` as the snapshot. | REPORT §4 "Run" bullet |
| 3 | MINOR ("costlier in total") | Resolved ("not cheaper in total … the CI includes 1"). | REPORT §2 |
| 4 | MINOR (live clean Holm p 0.083) | Resolved. The value is disclosed and matches `live.md` (sensitivity row gnn_survival vs gnn_bce: Holm p 0.083). | REPORT §2; `live.md` |
| 5 | MINOR (interim P1 Tail) | Resolved. "1.187 [1.060, 1.337], Holm p 0.016" matches `live_P1.md` l.32. | REPORT §4 |
| 6 | MINOR (median-ratio resamples) | Resolved. DECISIONS #13 now records it. The code agrees: `scripts/eval_v2.py` l.216 uses `min(a.boot, 2000)`. | DECISIONS #13 last bullet |
| 7 | MINOR (live calls) | Resolved. `live.md` has a "planner calls per assembly (mean)" column. I recomputed it independently: all 17,697 reported runs have `calls`, and `calls` equals the number of logged queries in every run (0 mismatches). The seed-mean per method matches every row (e.g. gnn_survival 7.996 → 8.0, random 8.54 → 8.5, fewest_contacts@b3 8.98 → 9.0). | `indep_calls.log` |
| 8 | MINOR (C-index comparative claim) | Resolved. It is now marked "mean over seeds, no CI, descriptive". The values match `replay.md` l.556–566. | REPORT §3 |

## New findings (severity | file | what is wrong | how to verify)

| # | severity | file | what is wrong | how to verify |
|---|---|---|---|---|
| 1 | MINOR | `reports/campaign/DECISIONS.md` #13, "MINORs fixed" bullet | The bullet still says "Live planner calls and live rot_state are disclosed as not reported". The last bullet of the same entry, and REPORT l.12, now say calls *are* reported in `live.md`. Update or strike the stale clause so the entry does not contradict itself. | `sed -n 128,137p reports/campaign/DECISIONS.md` |
| 2 | MINOR | `reports/campaign/DECISIONS.md` #13, "MAJOR 1" bullet | It says the survival-vs-BCE result "holds per assembly with the GNN". REPORT §2 now correctly states that the per-assembly condition fails on the live clean subset (Holm p 0.083). Align the DECISIONS wording with REPORT §2. | DECISIONS #13 vs REPORT §2 "Live" bullet; `live.md` sensitivity table |
| 3 | MINOR | `live.md` calls column (PREREG §6 "same metrics and tests") | Live calls are a mean only, with no CI. Replay's per-method count columns have none either, so this is consistent with replay and is descriptive. To be fully explicit, add "descriptive, no CI" to the header. | `live.md` header row |
| 4 | MINOR (outside this phase's reports; for Phase 4) | `video/script.md` l.13 (last changed 0274f4c, 2026-11-25, before the phase3 fixes) | The narration says "cost-aware ordering **beats** ASAP and removability-only ordering". That contradicts the audited claims: "beats" is registered only for the best heuristic, and survival vs BCE is mixed and not robust (REPORT §2). The talk and paper were updated (talk/main.tex l.213, paper/main.tex l.55), but the video script was not. Fix it before the video is (re)rendered or audited. | `grep -n beats video/script.md` |

## Checks that passed (evidence)
- **Reproduction on saved outputs.**
  - `scripts/live_report_v2.py` rebuilds a `live.md` byte-identical to `reports/final_eval/live.md` (calls column included).
  - `scripts/failure_analysis.py` rebuilds `failure_analysis.md`, identical apart from paths.
  - `scripts/final_figures.py` rebuilds `budget_policy.pdf`, `failure_scatter.pdf` and `totals_replay_live.pdf`. They differ
    only in 3 bytes or fewer (timestamp).
  - `replay_test_totals.pdf` is not produced by `final_figures.py`. It was committed with the single test replay
    (9d7d592) and is unchanged since then.
  - `pdfimages -list` finds 0 raster images in all four PDFs, so they are vector. The `budget_policy.pdf` text shows the
    "(3 s first; live: seed 101)" label and the numbers 1,904 / 7,595 / 2,008 / 7,202 / 10,810 / 21,038 / 11,273 / 23,002,
    which match REPORT §3/§4 and `live.md`.
- **REPORT numbers against tables.** I checked every live number in REPORT §2 and §4 against the rebuilt `live.md`
  (registered, sensitivity, exploratory and subset tables), and the interim values against `live_P1.md`. All match.
  `replay.md`, `scripts/eval_v2.py`, `src/` and the failure-analysis outputs are unchanged since the phase3_1 audit
  (b869319), so the replay reproduction in phase3_1/phase3_2 still applies.
- **Test-set discipline.**
  - The last commit touching `docs/PREREG_addendum.md`, `docs/PREREG_run05.md`, `configs/final_frozen.yaml` or
    `configs/final_methods.json` is a13b397 (23:04:31), before the marker (23:08:45). The working tree is clean for them.
  - Only one replay and one live test folder exist.
  - `budget_overrun.py` only reads saved test outputs, after the evaluation. It selects nothing and produces no timings.
- **Claims.** "beats" appears in REPORT only as the registered verdict. "significant" is used only with Holm-corrected
  registered p values. Negative results are stated plainly: the §7 verdict in replay, clean and live; GNN vs MLP; PN;
  Tail.
- **Repo.**
  - `pytest`: 36 passed (`pytest.log`).
  - No tracked file is larger than about 1.3 MB.
  - The budget-overrun folder commits only small text and json.

VERDICT: PASS
