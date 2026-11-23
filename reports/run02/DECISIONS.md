# Run 02 decisions made on Aaron's behalf

Each entry: choice / alternatives / why.

1. **R2 "default learned SDF" = trained by us with upstream `train.py` defaults** (10M deepsdf samples, 100 epochs,
   batch 2048, Adam 1e-4, L1 sum, clamp 0.1, no shuffle). Data sits on the GPU and is sliced in the same order instead
   of going through a CPU DataLoader (`scripts/repro_cmgrrt.py`). *Alt:* call `taucgl_sdf.train.main` verbatim (same
   math, about 2–3× slower), or reuse run 01's cheap SDFs. *Why:* the repo ships no `.pth`, so this is the closest thing
   to "their default". The math is identical; per-epoch losses are logged for the convergence check.
2. **SDF training mesh = `0_sdf.obj`** (the watertight remesh shipped next to each example), not `0.obj`. *Alt:*
   `0.obj` (train.py's default path; not watertight, so quicksdf's sign is unreliable). *Why:* the file name says it is
   the SDF mesh, and a signed distance needs a closed surface. Bounds agree with 0.obj within 0.005 (`reports/oracle_design.md`).
3. **R2 sampling override applied per example only** (elk 10,000, others 4,000). `test_all.py` writes the override
   into the shared settings dict, so every example after elk would inherit 10,000. *Why:* per-example is the evident
   intent. The paper uses 10,000 for all (noted in `cmgrrt_reference.md`).
4. **R2 elk: 1 seed, 60 min cap.** The prompt asks for 3 seeds only "if the authors report several seeds". The paper
   reports 10 runs for the 16 benchmark instances but does not state the number of Elk runs. *Why:* 3 × 60 min would
   use the whole 3 h R2 box on one example whose paper mean (156 min, 16 cores) exceeds the cap. The other 16
   examples are the paper's main table.
5. **R2 order after elk:** `general/11356`, `puzzle/key_light_1` (run 01's only successes) first, then the other
   `general/*` (closest to our ATA domain), then the puzzles, each with a 20 min cap. Runs that cannot finish before the
   box end (23:20) are skipped and logged in `skipped.jsonl`. The 16 SDFs were trained 4 at a time before any planner run.
   Training time is setup and is marked confounded; planner runs are strictly one at a time.
6. **Exact detector design** (`src/disasm/oracle/exact_sdf.py`). Distance = libigl AABB exact point–triangle
   distance. **Runtime sign = angle-weighted pseudonormal** at the closest feature, which is exact for watertight,
   consistently oriented meshes. At setup it is checked against the robust **winding number** on 5,000 probes per part, with a per-part
   fallback to the winding-number sign if agreement is below 99.9%. *Alt:* winding number at every call. *Why:*
   `igl.fast_winding_number` rebuilds its tree every call (55 ms per 4,000 points on a 73k-face part, measured),
   versus 6 ms for the AABB distance. That would dominate planner time. The pseudonormal agrees with the winding number
   wherever both are defined, and the check enforces it per part.
7. **Far-field lower bound:** for points farther than `band` = 0.1 from a part's bounding box, the box distance is
   used instead of the exact distance. The returned union value is a lower bound everywhere and exact wherever the
   true union SDF ≤ 0.1 (20 × ε). Every planner decision compares against −ε or +ε. The cluster test
   `d − r ≤ ε` is conservative under a lower bound (it can only admit more clusters, which are then evaluated exactly).
8. **ε ≡ −threshold, with eps_contact = ε** (CMG-RRT ties `eps_contact = |threshold|`). **ε = 0.005** in scaled units:
   it equals the library/paper default δ = 0.005 ([P] §5.1) and the test_list threshold. It is 2.5× run 01's
   interpenetration cutoff (0.002), and below half the thinnest walls the checker can see (walls < 2ε are transparent,
   see `run01_review.md` §1). Sensitivity: 0.0025 / 0.005 / 0.01 in R3.
9. **Light single-core dev tests during R2's SDF-training phase only** (exact-detector unit tests, one 00014/00017
   query set, profiling). The training phase is untimed setup and already marked confounded (4 concurrent trainings).
   Nothing runs alongside R2's planner runs (phase 2). *Alt:* stay idle for ~45 min. *Why:* R3 can't be developed blind.
10. **Bug fixed in `scripts/label_abd.py`:** on exit the script called `os._exit` after a non-waiting executor shutdown,
    so spawned workers survived and **kept holding planner slots** (seen at 20:44: two orphans from a scratch test,
    killed). The script now terminates its workers before exiting. This also plausibly explains run 01's 12-process episode.
11. **Decision #2 was wrong and is corrected for diagnostics.** The exact start clearance of the robot
    (`experiments/2026-11-22_cmgrrt_repro_clean/diag/start_exact_0obj_vs_0sdfobj.json`) shows `0_sdf.obj` is NOT a
    faithful remesh near the contact for 9/17 examples (e.g. 11356: −0.050 vs +0.0027 for `0.obj`; duet-g1: −0.139 vs
    +0.024). The upstream-default SDFs trained on it reproduce those wrong values accurately (11356 learned −0.0496), so 6
    general examples started in collision. **Diagnostic #2** retrains on `0.obj` (train.py's default path) for 11356 and
    key_light_1 and reruns them. The other examples are left as "Needs Aaron" (R2 box exhausted). The R3 exact detector
    uses `0.obj` (except az, whose `0.obj` gives −0.57 at the start: it is not a usable closed surface there).
12. **R3 gate "bundled solved still solved"**: 16505 and alpha hit the 20 min wall cap at ~1800/5000 iterations with the exact
    detector (3–5× slower per iteration than the learned cuda SDF). Recorded as a documented speed reason, not reran
    (≈ 2 h for two full-budget reruns would eat the labelling box). *Alt:* rerun without wall cap now. Listed in Needs Aaron.
13. **R4 settings:** exact detector, ε = 0.005, T = 30 s (R3 median query ~1 s, 9% of assembled-state queries hit T; no
    evidence to change T), `--max-pen 0.005` (= ε, instead of run 01's 0.002: a start is valid when penetration ≤ ε, which the
    R3 start-valid check confirms), 10 cpu workers (all 10 slots), 4 concurrent assemblies, seed 0, v0 ids first
    (`order_v0_first.txt`), `--stop-at 06:15` so R5 final + R7 fit before 07:15. *R6 skipped by plan*: it needs the
    planner-free machine for ≥ 2 h, which would end labelling at ~04:00 and would also confound labelling times.
