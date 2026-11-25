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
   - *Profile:* honest column labels, median for both batch-1 and batched timing, busy samples during the run,
     a list of what is and isn't timed; re-run alone.
   - *Wording:* §7 verdicts are printed only for test/main; other configs and val are "descriptive". The random
     ordering's "solved within T" is shown as "—". Resample counts are stated in the md header.
