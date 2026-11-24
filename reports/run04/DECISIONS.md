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
    is enough for a small PointNet (≈ 0.1 M parameters total); (c) the encoder gets the same tuning budget as every
    other variant. Inputs (`src/disasm/data/pointcloud.py`): 1,024 area-weighted surface samples + face normals,
    part-local translation (centred on the sample mean), assembly-frame axes, assembly unit scale, seeded by
    crc32(assembly/part) + seed. Forward/backward on 32 train states ran (`.../t2_dryruns/results.json`).
