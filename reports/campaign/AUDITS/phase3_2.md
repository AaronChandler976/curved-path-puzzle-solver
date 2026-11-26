# Audit phase3_2 (Phase 3: final test, evaluated once; re-audit)

Auditor: independent subagent. My only instructions were `prompts/audit.md`, the phase name, and the report and run paths.
I was also given the previous audit `reports/campaign/AUDITS/phase3_1.md` so I could check each finding.
Date: 2026-11-26. HEAD at audit: 0b2701b (the fix commit for phase3_1).
Reproduction folder: `experiments/2026-11-26_audit_phase3_2_repro/`. It contains `git_hash.txt`, `marker_before.txt`,
`live.md` (rebuilt), `failure/` and `failure_analysis.md` (rebuilt), `figures/` (rebuilt), the scripts
`overrun_variants.py` and `live_overrun_variants.py` with their `.log` files, and `pytest.log`. I ran no planner job and did
not re-run the test evaluation. The marker `data/splits/.v2_test_evaluated` is unchanged: same mtime (Nov 24 23:08) and
same sha256 (7242bbf5…) before and after.

## Status of the phase3_1 findings

| # | phase3_1 severity | status | evidence |
|---|---|---|---|
| 1 | MAJOR (novelty overclaim) | **Resolved.** REPORT §2 now says "mixed evidence" and lists the replay, clean, live and MLP readings with the correct numbers. Two small residues remain (new findings 3 and 4). | REPORT l.65–74 vs `replay.md` main/clean tables and `live.md` registered table |
| 2 | MAJOR (live budget overrun) | **Resolved in content.** REPORT §4 l.148–152 and DECISIONS #13 now give the soft-budget explanation. "Median 4.24 s, max 72.6 s, 4,738 s of 22,083 s" reproduces: 4,738 s is the CMG-RRT stage time beyond 3 s, summed over the 1,439 failed pass-1 queries. The phase3_1 figure of 5,627 s was whole-query time beyond 3 s. Both definitions are defensible, and the CMG-RRT-stage one matches addendum B.2's "truncates CMG-RRT at T'". However, the report gives no log path (new finding 1). | `live_overrun_variants.log` |
| 3 | MAJOR (soft T = 30 s) | **Resolved in content.** REPORT §4b and DECISIONS #13 disclose it. Every number reproduces on all 12,444 test queries: unsolved median 31.19 s, max 73.2 s; 8,163 s beyond 30 s (of 95,032 s); 24 main-config successes > 30 s (max 89.1 s); 158 CMG-RRT-only successes > 30 s (max 127.7 s). The numbers differ from phase3_1's (8,083 s, 154) only because phase3_1 filtered `attempt == 0` (12,367 rows) and so dropped the 77 re-run queries. The report gives no log path (new finding 1). | `overrun_variants.log` |
| 4 | MINOR | Resolved (REPORT l.174–175). | — |
| 5 | MINOR | Resolved ("Plausible cause (not tested)"). | REPORT l.180 |
| 6 | MINOR | Resolved ("satisfies both §7 criteria … the 'beats' label is registered only for the best heuristic"). | REPORT l.61–64, l.127–128 |
| 7 | MINOR | **Partly resolved.** The Tail CI is now stated (l.135–136). The interim P1 Tail result is still not disclosed (new finding 5). | `live_P1.md` l.32 |
| 8 | MINOR | Resolved for HL: `live.md` header states 2,000 resamples, and DECISIONS #2 l.14 already logged it, so the phase3_1 claim "not in DECISIONS" was wrong. The median-ratio part has a residue (new finding 6). | `live.md` l.3; DECISIONS l.14 |
| 9 | MINOR | Resolved as a disclosed omission (REPORT l.12–13, DECISIONS #13). Residue in new finding 7. | — |
| 10 | MINOR | Resolved (l.81–82). | — |
| 11 | MINOR | **Partly resolved.** l.11 says C-index has no CIs and is descriptive, but §3 l.93–94 still makes a comparative claim from it (new finding 8). | REPORT l.93–94 |
| 12 | MINOR | Resolved. `live.md` header: "`gnn_survival@b3` is the val-best seed (101) only". The figure label reads "(3 s first; live: seed 101)" (checked with `pdftotext`). | `live.md` l.3; `figures/budget_policy.pdf` |
| 13 | MINOR | Resolved. `git diff --stat 1905865 HEAD -- scripts/live_abd.py scripts/run_final_live.sh scripts/train_v2.py src/` is empty. 1905865 is the P1 launch hash in `load_info.txt` (git_dirty False). The dirty-tree contents at the P3/P4 launches are still unrecorded, but they cannot have been committed code changes to these paths. | `load_info.txt`; git |
| 14 | MINOR | Resolved (DECISIONS #13). | — |
| 15 | MINOR | Resolved. `talk/demo.gif` is removed from the index and gitignored. It remains in history (3a26228), which is correct since history must not be rewritten. | `git ls-files talk` |

## New findings (severity | file | what is wrong | how to verify)

| # | severity | file | what is wrong | how to verify |
|---|---|---|---|---|
| 1 | MAJOR | `reports/final_eval/REPORT.md` §4b (l.156–166) and §4 (l.148–152); `reports/campaign/DECISIONS.md` #13 | The overrun numbers (31.19 s, 73.2 s, 8,163 s, 24 / 89.1 s, 158 / 127.7 s, 4.24 s, 72.6 s, 4,738 s, 22,083 s) cite no script or log. The only logs on disk for this topic are the phase3_1 auditor's untracked `budget_overshoot.log`, which gives *different* values (8,083 s, 154, 5,627 s). So a reader cannot trace the reported numbers. CLAUDE.md hard rule 1 requires the log to be on disk and the report to link its path. I could reproduce every value (so this is not a BLOCKER), but only by guessing the definitions. Fix: add a small script (e.g. `scripts/budget_overrun.py`) that writes a log under an `experiments/<date>_budget_overrun/` folder. Cite that path in §4b, §4 and DECISIONS #13, and state the two definitions: all 12,444 test queries including the 77 re-run queries, and "CMG-RRT stage time beyond T'" for the 4,738 s (5,627 s if the pre-check is counted). | `experiments/2026-11-26_audit_phase3_2_repro/overrun_variants.log`, `live_overrun_variants.log`; `grep -rn 8,163 experiments/` finds nothing |
| 2 | MINOR | `REPORT.md` §4 l.98–99 | The live tables are cited as `reports/final_eval/live_registered.md`, the interim P1+P2 snapshot. The final file is `live.md`. The registered rows are identical (diffed), but the citation should point to the final file, with the snapshot as secondary. | `diff` of the registered rows of both files: identical |
| 3 | MINOR | `REPORT.md` §2 l.70 | "Live: GNN-Surv is costlier in total (1.045 [0.955, 1.150])". The CI includes 1, so the direction is not established. Say "no detectable difference in total (1.045 [0.955, 1.150])". | `live.md` registered table, row gnn_survival vs gnn_bce |
| 4 | MINOR | `REPORT.md` §2 l.73 | "supported per assembly with the GNN" holds in replay (all and clean) and live (all assemblies, Holm p 0.035). On the live addendum-A clean set (306 assemblies) the per-assembly condition fails (Holm p 0.083, HL −0.05 s). This is not mentioned, although the paragraph enumerates the other readings. | `live.md` sensitivity table, row gnn_survival vs gnn_bce |
| 5 | MINOR | `REPORT.md` §4 l.125–126 / l.135–136 | The report discloses the interim P1 value only for the §7 comparison. In P1, GNN-Surv vs GNN-Surv-Tail was 1.187 [1.060, 1.337], Holm p 0.016, which satisfies both §7-style conditions in favour of Tail. With 5 seeds it fell to Holm p 0.18. For consistency, disclose this interim value too (phase3_1 #7 asked for it). | `live_P1.md` l.32 |
| 6 | MINOR | `REPORT.md` l.10–11 | "median-ratio CIs 2,000 (DECISIONS #2)", but DECISIONS #2 covers only HL (l.14). The median-ratio resample count is stated in the `replay.md` header but is not logged as a decision or deviation. | `sed -n 4,20p reports/campaign/DECISIONS.md` |
| 7 | MINOR | `REPORT.md` l.12–13; DECISIONS #13 | Live planner calls are "not reported", with no reason given, but each live record has a `calls` field, so they could be computed from saved outputs. Either report them or say why not. (The rot_state reason given is acceptable.) | `results.jsonl` record keys (`live_overrun_variants.log` / `overrun_variants.log` last line) |
| 8 | MINOR | `REPORT.md` §3 l.93–94 | "rank parts by time better than ASAP's score: C-index 0.674 vs 0.593 / 0.626", plus "ListNet is the highest". These are comparative claims with no CI or n, even though l.11 now calls the C-index descriptive. Phrase them as point estimates ("descriptive, no CI"). | REPORT l.11 vs l.93–94 |

## Checks that passed (evidence)
- **Reproduction on saved outputs.**
  - `scripts/live_report_v2.py` rebuilds a `live.md` byte-identical to `reports/final_eval/live.md`, including the new
    header.
  - `scripts/failure_analysis.py` rebuilds an identical `failure_analysis.md` (paths aside).
  - `scripts/final_figures.py` rebuilds the three PDFs with 3 differing bytes each (timestamp).
  - No figure PDF contains raster image objects (vector).
  - The registered and clean-test numbers quoted in the new REPORT §2/§4 text match `replay.md` and `live.md`
    (0.887/0.999, 0.877/1.001, Holm p 2.9e-5, HL −0.18; 1.045, HL −0.06, Holm p 0.035; 1.041 / 0.985; 1.058 [1.003, 1.110],
    Holm p 0.18; ASAP-retrained 0.906, Holm p 0.04, HL −0.15).
  - 13,533 = 4×347 + 7×5×347 registered runs. All 77 re-runs fall on registered methods, so "77 re-run" is right for both
    the 13,533 and the 17,697 counts.
- **Test-set discipline.**
  - No commit after a13b397 touches `docs/PREREG_addendum.md`, `docs/PREREG_run05.md`, `configs/final_frozen.yaml` or
    `configs/final_methods.json`, and the working tree is clean for them.
  - The only test result folders are `experiments/2026-11-25_final_eval_replay` and `2026-11-24_final_eval_live`. The
    phase3_1 checks (marker before test-file creation, checkpoint sha256, single replay) still stand; nothing relevant
    changed in 0b2701b.
- **Live code identity.** The live code is unchanged from the launch commit to HEAD (above).
- **Repo.**
  - `pytest`: 36 passed (`pytest.log`).
  - The largest tracked files are under 1.4 MB, with no datasets or checkpoints.
  - The demo GIF is now untracked.

VERDICT: FAIL
