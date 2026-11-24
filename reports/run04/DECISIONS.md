# Run 04 decisions made on Aaron's behalf

Each entry: choice / alternatives / why.

1. **T1 "ours" for the idle guard** = the runner process and all its descendants (walked through /proc ppid links at
   every 5 s sample) plus processes whose command name is `claude`. Commands the agent itself starts (bash, python
   checks) are NOT ours and count as outside load. *Alt:* exclude the whole Claude tree. *Why:* CLAUDE.md excludes
   `claude` itself; anything heavy the agent runs during a timed stage really is contention and should be flagged.
2. **T1 load criterion: "our planner workers"** = number of our threads in run state R/D, smoothed with the kernel's
   own 1-min exponential (exp(−5/60) per 5 s sample), subtracted from /proc/loadavg's 1-min value. *Alt:* subtract the
   number of held planner slots. *Why:* load average is a 1-min EMA of runnable threads, so subtracting the same EMA of
   our runnable threads is the like-for-like comparison; idle workers holding a slot add no load.
3. **T1 first sample is "busy"** (no CPU baseline yet), and a missing or stale (> 30 s) sampler state is treated as
   busy by workers. *Why:* conservative; at worst a few seconds of extra waiting.
4. **T1 busy_frac window:** a 5 s sample at time s covers (s − 5, s]; every sample overlapping the query counts; a
   query shorter than the sampling gap uses the nearest sample. Each sample's busy flag uses the CLAUDE.md 30 s
   average, so a burst marks the next ~30 s of queries confounded (conservative by construction).
5. **T1 seeded robot sampling without a patch.** The installed trimesh (5.2.2) has a `seed` argument, but the
   unmodified CMG-RRT library calls `sample_surface` without one. Our adapter wraps the call in a context manager
   (`cmgrrt.seeded_surface_sampling`) that passes `seed=np.random.default_rng(robot_sample_seed(query seed))` and
   restores the module attribute on exit. Nothing under external/ changes, so no file in patches/ is needed.
   `robot_sample_seed = sha1("robot-samples-<seed>")[:8]` is logged with every query.
   *Alt:* a patch to collision_detection.py. *Why:* the prompt prefers the seed argument when trimesh supports it.
6. **T1 single-thread KMeans for reproducibility.** With samples fixed, the library's KMeans (robot-sample clustering
   and contact-gradient clustering inside extend) still differed at 1e-16 when multithreaded. `query()` now runs robot
   sampling and the planning loop under `threadpoolctl.threadpool_limits(1)`. Planner workers were already pinned
   to 1 thread (pool.pin_threads), so planner timing is unchanged; the test process now matches worker behaviour.
   Test: `tests/test_seeded_sampling.py` (identical samples, cluster centres, iterations, tree node set hash).
7. **T1 labelling re-runs keep the trajectory.** In `label_abd.py` the removal choice at each state is made from
   attempt 0 (its success is a planner-found path). Confounded queries are re-run at the end with the same seed;
   `attempts.jsonl` keeps every attempt; `labels.jsonl` (consolidation) uses the first clean attempt, else attempt 0
   flagged `still_confounded`. *Alt:* re-run the whole state/assembly. *Why:* a clean re-run measures the same query
   again; the visited state stays physically valid because attempt 0's removal was planner-verified.
8. **T1 live re-run unit = the whole (assembly, method) disassembly.** In a sequential disassembly a re-run query
   could change the trajectory, so a run with any confounded query is repeated from the start (same seeds) up to 2
   times; reports use the first clean attempt.
9. **T2.1 redmax builds without sudo, in a separate env `asap` (Python 3.8).** ASAP's bundled pybind11 is 2.9, which
   does not support Python 3.11 (`disasm`), so redmax cannot go into `disasm`. Build from a *copy* of
   external/ASAP/simulation in `build/asap_simulation` (gitignored), so no build artefacts land under external/.
   Three attempts (logs in `experiments/2026-11-23_run04_t2_redmax/build{1,2,3}.log`):
   (1) CMake 4.2 rejects glfw's `cmake_policy(SET CMP0042 OLD)`; (2) with pip `cmake==3.31.6` in env asap, GCC 15
   rejects old Eigen under `-Wtemplate-body`; (3) `CXXFLAGS="-Wno-template-body -fpermissive"` builds and installs.
   No source file was edited, so nothing goes to patches/. Env `asap`: python 3.8, numpy, scipy, networkx,
   cmake 3.31.6, trimesh 3.10.8, rtree 0.9.7, pyquaternion 0.9.9, matplotlib 3.5.1, tqdm.
10. **T2.1 result: our run 03 ASAP contact adapter = redmax exactly** on 20 seeded run 03 train assemblies (109/109
    edges, 20/20 graphs identical; `experiments/2026-11-23_run04_t2_redmax/agreement.json`). Our own GNN contact graph
    (|d| < 0.01 unit) misses 6 of the 109 redmax edges (3 assemblies). Run 05 uses redmax's own graph for ASAP
    (`scripts/asap_contact_graphs.py`, env asap) as the prompt asks; the adapter is now validated as equivalent.
11. **T2.2 ASAP retraining = ASAP's code, our loop.** ASAP's public repo has the model and the objective
    (`ModelGraph.forward`: BCEWithLogits over nodes, one positive = the removed part; 90° random-axis rotation
    augmentation on train) but no training loop, optimiser or learning rate. `src/disasm/models/asap_train.py`
    loads `ModelGraph` by file path (fresh init) and trains with its own `forward` loss. Label mapping: y = 1 for the
    part our forward disassembly removed at that state (a uniformly random planner success), else 0 — ASAP's
    one-positive format. *Alt:* multi-label (all successes = 1). *Why:* "its own objective" means ASAP's format;
    multi-label is what our GNN-BCE already does. Optimiser/lr/batch/epochs are tuned in run 05 under the shared budget.
    Dry run (2 epochs, 50 train assemblies, Adam 1e-4, batch 16) ran: `experiments/2026-11-23_run04_t2_dryruns/`.
12. **T2.3 PointNet trained end to end (not a pretrained encoder).** *Alt:* ASAP's released PointNet as a frozen
    encoder. *Why:* (a) ASAP's pretraining set is built from the same Fusion 360 / ATA assemblies, so it may contain
    v2 test assemblies, which would contaminate the fresh test set; (b) ~10k distinct parts across ~1,600+ assemblies
    is enough for a small PointNet (the PointNet+GNN model has 61k parameters); (c) the encoder gets the same tuning budget as every
    other variant. Inputs (`src/disasm/data/pointcloud.py`): 1,024 area-weighted surface samples + face normals,
    part-local translation (centred on the sample mean), assembly-frame axes, assembly unit scale, seeded by
    crc32(assembly/part) + seed. Forward/backward on 32 train states ran (`.../t2_dryruns/results.json`).
13. **T3 attempt 1 aborted after 10 runs (all confounded); relaunched in a fresh folder.** At 16:40 desktop apps
    (Firefox media decoder "RDD Process", Firefox content process, Chrome) used 0.5–0.72 outside cores once our 10
    workers were loaded, so every query was busy (busy_frac 1.0). Re-running under those conditions would only have
    produced more confounded attempts. I stopped the process group (slots verified free), probed the desktop with
    nothing of ours running (`experiments/2026-11-23_run04_idle_probe/`: busy for the first ~75 s, then
    0.05–0.1 cores), and relaunched at ~16:50 when it was quiet. The aborted attempt is kept unchanged in
    `experiments/2026-11-23_run04_live_rerun_aborted1/` (10 runs, all `confounded`), and is not used in any table.
14. **T4.2 diagnosis attempt 1 discarded (code bug, not data).** A misplaced edit in `ExactUnionSDF.__init__` (the
    margin change) made every job fail with `AttributeError: n_exact`; no planner result was produced. Fixed, tests
    re-run (25 passed, `experiments/2026-11-23_run04_pytest_t4b/`), relaunched. The failed folder is kept as
    `experiments/2026-11-23_run04_diagnose_misses_err1/`.
15. **T4.4 attempt 1 stopped at 1,063/1,872 jobs: path-file collision.** The three configs of one query used one work
    dir, and the path file name has no config in it, so a recheck could read another config's path (one read a
    half-written file). Planner outcomes were unaffected, but the independent recheck (part of the gate) could not be
    trusted. Relaunched with per-config work dirs; attempt 1 is kept in `..._oracle_validation_aborted1/` and not used.
    The same collision can affect live runs (same seed across methods): `live_abd.py` now uses per-method work dirs,
    and the caveat is stated in `reports/run04/oracle_v2.md` (T4.1 live rows).
16. **T4 variants v2a / v2b.** T4.1 showed that 18.5% of v1 successes dip below −ε between valid tree nodes, by under
    10% of ε. v2a = pre-check → CMG-RRT, with fine confirmation of goal edges and lazy fine validation of paths
    (invalid edges are removed from the tree and the search continues). v2b = v2a + a planning margin of 0.1ε (nodes
    must stay above −0.9ε; checks stay at ε; obstacle parts already touched deeper at the start get exactly enough
    relief to keep the start valid). This is a collision-representation change only (CLAUDE.md rule 2). Both are
    measured on the T4.4 validation set; the one adopted is recorded in #17.
17. **Oracle v2 = v2a (no planning margin).** On the T4.4 validation set, v2a and v2b both give 0 invalid
    successes and 99.2% of the misses; v2b is no better on success (554 vs 555 of 624) and rejects more goal
    edges. The simpler variant is adopted: `oracle_v2.FIX_V2 = ("fine_goal", "validate")`, `MARGIN_V2 = 0`.
18. **T6 allowance caps: absolute 0.03 (unit frame) AND relative 0.2 × the thinner part's smallest bbox extent.**
    Per-pair penetration was measured with the oracle's exact part SDFs at vertices + 20,000 surface samples per
    part (`experiments/2026-11-23_run04_penetration/`). Overlapping pairs (> ε): median 0.022, p75 0.040, p90 0.071;
    relative to the thinner part's smallest extent: median 0.20, p75 0.47. *Alt:* an absolute cap only (0.05 would
    recover 1,011 of 1,358). *Why:* many overlaps are a large fraction of a thin part's thickness. With a relative
    cap of 0.2, a sample point allowed to sink in can never reach a part's mid-plane, which rules out passing
    through it; the absolute cap 0.03 (≈ p65 of overlapping pairs) bounds the geometric error.
    Result: 439 recovered (342 with 3–8 parts, 97 with 9–12), 919 excluded (566 absolute cap, 353 relative cap)
    (`experiments/2026-11-23_run04_t6_pool/allowance_meta.json`).
19. **T6 allowance rule: the query's own start depth + ε, not the dense pair measurement.** The first allowance check
    (dense pen + ε as a fixed offset; `experiments/2026-11-23_run04_allowance_check/`) passed start validity,
    non-overlapping pairs at the global ε and end-pose clearance on 928/928 paths. But 30 paths (10 of the 30
    CMG-RRT-stage paths) went deeper into an overlapping partner than at the start, by up to 0.017: the dense offset
    exceeded the start depth seen by the query's own samples, so the planner could squeeze in. Now each listed pair's
    offset = max(0, −d_k(start)) on the planner's own samples (`cmgrrt.query`), i.e. "its measured start
    penetration + ε" measured where it matters. Start validity and no-deepening then hold by construction; the
    dense measurement only decides the caps. Re-validated on the same 50 assemblies (#20).
20. **T6 labelling plan: label everything.** Cost pilot (110 assemblies, oracle v2, T = 30 s, idle guard;
    `experiments/2026-11-23_run04_cost_pilot/estimate.txt`), in worker-seconds per assembly: v1 83 (11.3 queries),
    fresh 9–12 683 (57.8), fresh allowance 276 (23.9; a 39/11 mix of 3–8 / 9–12 parts). Projection at 10 workers:
    v1 1,328 → 3.1 h; clean 9–12 255 → 4.8 h; allowance 439 (342 × ≈ 161 + 97 × ≈ 683 worker-s; 161 solved from the pilot mix) → 3.4 h; total
    ≈ 11.2 planner-hours, within the ~12 h budget. So all 694 fresh assemblies are labelled (the test set ≈ half
    ≈ 340 ≥ 250) and all 1,328 v1 assemblies. Pilot labels are NOT reused in pilot_v2: the allowance rule changed
    (#19), and relabelling keeps a single run with a single code version.
21. **T6 pilot confounding.** 426/3,269 pilot queries were confounded (Firefox media decoding, 20:40–21:30), 89 still
    after 2 re-runs (2.7%). The pilot is a cost estimate, not a label set, so this only adds noise to the
    estimate. T7 has a < 1% gate and is launched overnight when the desktop is quiet.
22. **T5: idle-guard "our load" estimate fixed; the first two T5 runs stay flagged confounded.** In T5's single
    multithreaded process (igl/BLAS/torch threads), counting our running threads at the sample instant missed most of
    our load, so "1-min load − our workers" read 4–8 while outside CPU stayed ≤ 0.17 cores. 16505 seed 0 learned
    (busy_frac 0.64) and exact (0.10) were therefore flagged. The sampler now uses max(thread-count EMA, EMA of our
    measured CPU cores) (`src/disasm/util/idle_guard.py`, test `test_own_multithreaded_burner_not_load`). The batch
    was stopped two samples into alpha seed 0 (its guard folder is kept as `guard_puzzle_alpha_s0_aborted/`) and
    resumed. Per CLAUDE.md, single long runs are *marked* confounded rather than re-run; the two flagged runs are
    reported as confounded with this evidence, and re-run at the end only if time remains.
    Earlier timed stages used single-threaded workers, where the thread count tracks the load correctly.
