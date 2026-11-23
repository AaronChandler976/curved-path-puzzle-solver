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
