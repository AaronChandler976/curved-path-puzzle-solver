# Campaign decisions (choice / alternatives / why)

1. **Run 04 artefacts stay in reports/run04/; campaign bookkeeping in reports/campaign/.** As the prompt says.
2. **PREREG reading choices for Phase 1 (written 2026-11-24 ~14:20, before any v2 training or v2 val number).**
   - *Holm family.* PREREG §5 lists 9 GNN-Surv comparisons and says the intervention contrasts are "in the same family".
     Two contrasts are not among the 9: GNN-BCE vs MLP-BCE (GNN vs MLP, BCE head) and MLP-Surv vs MLP-BCE (survival vs
     BCE, MLP). So the family has **11** comparisons per evaluation and configuration (`scripts/eval_v2.py` COMPARISONS).
     *Alt:* 9 only (drops two registered contrasts) or a separate family for them (contradicts "same family").
   - *CMG-RRT-only configuration.* A state is scored there if it has ≥ 1 CMG-RRT-only success, mirroring the §0 rule for the
     main config. A state with a pre-check success but no CMG-RRT success costs the same under every order in that config.
   - *Training states.* §0: states with ≥ 1 main-config success. All their nodes are targets (unsolved ones are censored).
   - *Solve rate (§4 secondary).* Fraction of scored states whose first success is found within T = 30 s of planner time
     for that state. The PREREG doesn't define it further.
   - *HL CI.* Bootstrap over assemblies with 2,000 resamples, because HL is O(n²) per resample. Ratio CIs use 10,000 as registered.
   - *Live random seed.* The random shuffle seed is sha1("run05-live-random", assembly, state). Planner seeds follow §6.
   - *ASAP contact graph in val/test.* ASAP's own redmax graph (`scripts/asap_contact_graphs.py`, env asap) for every v2
     assembly. It is computed from geometry only, no labels.
3. **Contact-graph sampling was unseeded; fixed going forward, existing cache frozen (2026-11-24, Phase 0 T8).**
   Found because `tests/test_oracle_v2.py` failed 2 of 3 runs. `cmgrrt.contact_graph` called `np.random.seed(0)`, which
   trimesh 5.2.2 ignores, so contact samples came from fresh entropy. In the synthetic peg test the contact-normal
   candidate then sometimes fell within 5.7° of +z, and deduplication (dot ≥ 0.995) removed the exact +z axis. The
   slightly tilted pull is blocked in a 0.002-clearance hole. Effect on the project: none on labels, features or
   heuristics. Every v2 assembly's contact graph was computed once, cached in `data/processed/contacts_v2/` and reused
   everywhere (2,022/2,022 present). Their sha256 are frozen in
   `experiments/2026-11-24_run04_t8_split/contacts_v2_manifest.json`, and evaluation must use the cache. Fix:
   `default_rng(0)` passed as trimesh's `seed` (cache misses only). Tests: 5/5 repeated passes of test_oracle_v2, full
   suite 34 passed (`experiments/2026-11-24_run04_pytest_t8/stdout.log`).
   *Limitation recorded for the paper:* the pre-check tries the mean contact normal first and drops any axis direction
   within 5.7° of it. In a very tight fit a straight pull along the exact axis can therefore be skipped. CMG-RRT still
   runs in that case (main config), so such a query is costlier but not lost. The oracle is not changed, because the
   labels are frozen.
   *Also unseeded, decision-free:* `exact_sdf._check_sign` (a sign-agreement diagnostic) and `sdf_train` (learned-SDF
   path, not used by oracle v2).
4. **Phase 1 preparation overlaps the Phase 0 audit; Phase 1 results don't.** While the Phase 0 auditor runs I compute
   ASAP's redmax contact graphs (geometry only, all 2,022 v2 assemblies, no labels) and build and test the train/val
   graphs. No registered training run and no val number happen before the Phase 0 audit passes. (Correction after audit
   phase0_2: three 3-epoch smoke models were trained on a dev split of 300 train-only assemblies, to test the code.) *Why:* the prompt wants the
   machine kept busy and the order "phase starts after audit" protects results. Nothing here is a result.
   *Alt:* idle until the audit ends.
5. **Phase 0 audit MAJOR (41 test assemblies seen in T6): split kept, overlap disclosed, sensitivity analysis on the 306
   clean test assemblies pre-registered** in `docs/PREREG_addendum.md` §A (committed before any v2 training).
   *Alt:* re-split (a data-dependent change after a committed split) or drop the 41 (shrinks test, changes strata).
   The overlap informed only oracle settings shared by every method.
6. **Tail-aware loss: batched by state size, identical math; the variant was restarted.** The registered `tail_term`
   loops over states in Python, so one grid run was taking > 5 min with 6 jobs sharing the GPU (53 runs ≈ 1 day).
   `tail_term_grouped` (src/disasm/models/tail_loss.py) groups states of equal size and runs the same NeuralSort on
   each group's own n × n matrices, with no padding. Test: value equal to 1e-6, gradient equal to 1e-5 (float32)
   (`tests/test_tail_loss.py::test_grouped_tail_term_equals_loop`). The first tail launch was stopped before finishing
   its first grid run; its folder is kept as `experiments/2026-11-24_run05_train/gnn_survival_tail_aborted1/`, not used.
   The other variants are unaffected: train_v2.py's only other change is `.detach()` in logging (they loaded the
   script at launch).
7. **`experiments/2026-11-24_run05_eval_val_dev/` is a pipeline check, not a result.** It is eval_v2 on val with the
   5 variants finished at 19:30 (2,000 bootstrap resamples), run to catch bugs before the full evaluation. Phase 1 reports
   the full val evaluation with all 7 variants and 10,000 resamples. This folder is kept (never deleted) and not cited
   for any number.
8. **§7 best heuristic fixed from val: fewest contacts.** Val replay total, main configuration
   (`experiments/2026-11-24_run05_eval_val/results.json` → configs.main.best_heuristic): fewest contacts 2,275 s vs
   outside-in 2,800 s. Phase 3 passes `--best-heuristic-val fewest_contacts`. Chosen on val before any test label was
   read, as PREREG §7 requires.
9. **Phase 1 audit fixes (phase1_1: 2 MAJOR, 9 MINOR).**
   - *MAJOR 1, val selection bias:* every val table and the REPORT now say that trained models' val numbers are
     optimistic, because val chose their configs and epochs. The CV (Phase 2) early-stops on an inner fold and replays a
     held-out fold that selects nothing.
   - *MAJOR 2, GPU nondeterminism:* `eval_v2.py` scores on CPU by default. Two identical CPU runs gave bit-identical
     per-state costs and results (`experiments/2026-11-25_run05_eval_val_cpu/{a,b}`). The test evaluation will run on
     CPU. Only ASAP rows changed versus the GPU run. *Residual:* ASAP-retrained's training-time selection (val cost per
     epoch) was scored on GPU, where near-ties can flip (max score difference 6e-8). The chosen config/epochs are kept
     as trained. The effect on selection is limited to near-tie flips and is not redone.
   - *Minimum epochs:* PREREG "minimum 10 epochs" is implemented as "never stop before epoch 10". The best (smoothed)
     checkpoint can come from earlier (18 of 35 final checkpoints). This is the reading used for every variant alike.
     *Alt reading:* "only epochs ≥ 10 may be selected". Not adopted: it would force retraining every variant, and the
     code (unchanged since run 03 protocol v2) has always used the first reading. It is a reading choice, not something
     the PREREG wording settles.
   - *Folder dates:* `experiments/2026-11-25_run05_eval_val_cpu/` and `2026-11-25_run05_profile/` ran on 2026-11-24
     (local time) around 21:35–21:48 (git commit times). Named for the next day by mistake; not renamed, to keep the cited paths stable.
   - *Profile:* honest column labels, median for both batch-1 and batched timing, busy samples during the run,
     a list of what is and isn't timed; re-run alone.
   - *Wording:* §7 verdicts are printed only for test/main; other configs and val are "descriptive". The random
     ordering's "solved within T" is shown as "—". Resample counts are stated in the md header.
10. **Freeze inclusion rule, written 2026-11-24 22:43 before the exploratory variants' full CV results exist.**
    (Seen by then: the partial summary showed one fold × one seed per variant, fold-0 ratios GT 0.717, GATv2 0.797,
    ListNet 0.850. Correction after audit phase2_1: 2–4 seeds of fold 0 per variant were already on disk in
    `cv_log.txt`, though not read. All of it is train+val data; the rule below doesn't use them.)
    - *Replay on test:* all three exploratory variants (GATv2-Surv, GT-Surv, GNN-Surv-ListNet) enter the test replay
      as "post-registration, exploratory", whatever their CV result. Reporting all of them avoids choosing on CV noise;
      replay is cheap.
    - *Live on test:* an exploratory variant also enters the live evaluation only if its CV pooled ratio vs fewest
      contacts is lower than GNN-Surv's (0.874, `reports/explore/cv.md`). Live time is limited; the registered
      methods have priority.
    - *Budget policy:* the two-pass policy with T' = 3 s (best of the pre-listed {1, 3, 10} on val for most orderings,
      including fewest contacts) is replayed on test for EVERY ordering, as exploratory. Live, if time allows after the
      registered live runs: fewest contacts and GNN-Surv under the policy.
    - The registered comparisons, the §7 rule and the 11-comparison Holm family are unchanged. Exploratory results get
      their own table, with uncorrected p-values marked as such.
11. **Phase 2 audit fixes (phase2_1: 1 MAJOR, 6 MINOR).**
    - *MAJOR:* `reports/explore/REPORT.md` §2 no longer says "beats" or "help". The CV numbers are point estimates (no
      per-assembly data was saved, so no CI). ASAP-retrained is named as not in the CV (~4 h; worse than fewest
      contacts on val).
    - DECISIONS #10 now states that 2–4 fold-0 seeds were on disk when the rule was written.
    - Addendum B.4 cites the campaign shrink order, not PREREG §6. `final_frozen.yaml` gains the states path and a comment
      that the label hashes are integrity hashes of files that also contain test labels.
    - The exploratory training folder hash (b6d5ee8) and the per-variant hashes (4cc5cd7) are 19 s apart with no change to
      `scripts/train_v2.py` or `src/`. Per-variant cmd/git_hash files are now committed.
    - The val evaluation ran from a dirty tree; the auditor reproduced it exactly at HEAD.
    - New unit test `test_listnet_term_prefers_cheap_successes`.
    These edits to the addendum and the yaml are wording or provenance only, made before any test label was read.
    Every checkpoint sha256 is unchanged.
12. **Freeze commit = a13b397** (the last commit that touched `docs/PREREG_addendum.md`, `configs/final_frozen.yaml` and
    `configs/final_methods.json` before the test marker). The first freeze commit was a4eff4a; a13b397 only changed
    wording and provenance (audit phase2_2). Phase 2 audit phase2_2: PASS. MINOR fixes: ASAP CV time estimate corrected
    (about 2 h, not 4 h); exploratory live seeds now run val-best seed first (`scripts/run_final_live.sh`).
13. **Phase 3 (final test) decisions and deviations, after audit phase3_1 (3 MAJOR, 12 MINOR).**
    - *Test evaluated once:* the marker was written 2026-11-24 23:08:45 and replay ran once. Live (P1–P4) ran
      2026-11-24 23:10 → 2026-11-26 09:29: 17,697 runs, 77 re-run, 0 left confounded or errored.
    - *MAJOR 1, novelty wording:* the survival-vs-BCE result is reported as mixed. It holds per assembly with the GNN
      and on total time only in the main replay. The clean-test check, live totals and the MLP pair do not confirm the
      total-time part, and the live clean subset doesn't confirm the per-assembly part either (Holm p 0.083; REPORT §2).
    - *MAJOR 2, live budget policy:* the live 3 s budget is soft. CMG-RRT checks the time limit per RRT iteration, so
      failed pass-1 queries ran a median 4.24 s, with 4,738 s of CMG-RRT overrun beyond 3 s. Log:
      `experiments/2026-11-26_budget_overrun/` (`scripts/budget_overrun.py`, definitions stated there). Addendum B.2 named only the pre-check, which
      was incomplete. The REPORT now gives the overrun.
    - *MAJOR 3, soft T = 30 s:* in the test labels unsolved queries ran a median 31.19 s (max 73.2 s), with 8,163 s
      past 30 s summed over all 12,444 queries (same log). 24 main-config and 158 CMG-RRT-only successes took > 30 s. This is reported as a deviation from the
      PREREG's T and is not corrected after the test. It affects every ordering alike (same labels; same planner live).
    - *Code identity:* P3/P4 started with `git_dirty: True` from uncommitted report/talk edits. The live code
      (`scripts/live_abd.py`, `scripts/run_final_live.sh`, `scripts/train_v2.py`, `src/`) is identical from the
      launch commit 1905865 to HEAD (`git diff --stat` empty).
    - *MINORs fixed:* the §5 costliest-states wording, "plausible cause (not tested)", the "beats" label kept only
      for the registered rule, the Tail CI noted, HL resample counts stated in `live.md`, the one-seed budget row
      labelled (table and figure), the subset-correction wording fixed, and C-index described as having no CIs.
      Live rot_state is disclosed as not reported (live planner calls were added later, see below). The 3.6 MB demo GIF was removed from git
      (the mp4 stays).
    - *Audit phase3_2 fixes:* the overrun numbers now come from a logged script (above). The phase3_1 auditor's 8,083 s
      / 154 / 5,627 s differ only by definition (attempt 0 only; whole query). Other fixes: median-ratio CIs use 2,000
      resamples (recorded here); live planner calls added to `live.md`; the interim P1 Tail result disclosed;
      C-index wording without a superiority claim; the final `live.md` cited; "not cheaper in total" (CI includes 1);
      the live clean-subset Holm p 0.083 disclosed.
14. **Phase 4 audit fixes (phase4_1: 2 MAJOR, 13 MINOR).**
    - *MAJOR 1:* the data slide now states that sequences are planner-found, that 156/2,022 assemblies get stuck, and
      that allowance assemblies are valid only up to the tolerated interpenetration.
    - *MAJOR 2:* the demo is a main-flow slide (frame + "play talk/demo.mp4", 13 s) with a 20 s speaker-notes item.
      The backup appendix was removed.
    - *Factual fix carried into REPORT §5 and the paper:* train is 89.5% 3–8-part (79% is the v1 share). The paper's
      "root cause" became "plausible cause (not tested)".
    - *Other MINORs:* budget saving "72–79% in replay, about 50% live (fewest contacts; GNN-Surv seed 101)"; soft budget
      mentioned; SDF result on the bundled tight assembly (16505), not the puzzle; failure-analysis seed stated; "0.04 s"
      footer states its source and that it covers all outcomes; same oracle and T stated on the results slide; no
      battery CAD evaluated; latency slide is a table; notes wording on latency and shift.
15. **Phase 5 final-audit fixes (phase5_1: 4 MAJOR, 19 MINOR).**
    - *MAJOR:*
      - The paper conclusion now says the cost-aware advantage over removability holds only in the main replay and is
        not robust.
      - The budget policy is described as 72–79% in replay for every ordering replayed, and about 50% live for the two
        orderings run with it.
      - The paper defines every baseline and ablation (Experiments, "Baselines and ablations").
      - `environment-disasm.yml` adds the PyTorch cu128 extra index so the pinned CUDA builds install.
    - *MINOR:*
      - Demo time: 19.5 s in the guarded live run (18.4 s in the demo re-run).
      - Val is 89.6% 3–8-part.
      - "300 scored of the 306 never-piloted" assemblies.
      - GPU memory is the batch-of-200 peak; the profile run is called "confounded" as CLAUDE.md requires.
      - Grids are described per variant.
      - elk framing: one process using about 12 cores (median 11.7 in its guard samples); the difference from the paper
        is the missing parallel tree exploration.
      - README: "cheaper than" instead of "beats"; inputs not in git listed.
      - `video/script.md` matches the built cuts; the video caption band no longer covers the render header.
      - Talk notes say 34–39%.
      - The novelty audit calls the shift a plausible, untested cause.
      - The stale NEEDS_AARON line was removed.
    - *Left for Aaron:* the video link placeholders (upload needed).
