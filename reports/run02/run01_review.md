# R0: review of run 01's correctness-relevant decisions

Code read: `src/disasm/oracle/{cmgrrt.py, cmgrrt_core.py, sdf_train.py, pool.py}`, `scripts/{label_abd.py, scan_contacts.py}`,
and the library calls in `external/cmg-rrt/src/taucgl-rrt/taucgl_rrt/{rrt.py, extend.py, collision_detection.py}`.

## 1. The ×0.2 scale and units: OK
- `load_assembly` scales every ATA assembly by 1/max|coord| (= 0.2), so all meshes live in a frame with max|coord| = 1.
  Bundled examples are the same ATA meshes × 0.2 (checked in run 01: `reports/oracle_design.md`). The paper says models are
  "scaled ... to fit inside the unit sphere" ([P] §5.1). Our frame fits the unit *cube*, so corners can reach √3. That is
  a slightly larger frame than the paper's, but the bundled examples use the same frame as ours, so the thresholds transfer.
- Every absolute length is in this scaled frame: planner `eta` = 0.002, `threshold` = −0.005, `eps_contact` = 0.005
  (`cmgrrt_core.PlannerParams`, passed unchanged in `cmgrrt._setup_cd`); `CONTACT_EPS` = 0.01 and the
  interpenetration cutoff 0.002 (`scan_contacts.py` → `contact_graph` on `load_assembly` meshes, i.e. scaled);
  `GOAL_MARGIN` = 0.1. ε for run 02 is defined in the same frame (ε ≡ −threshold, see DECISIONS).
- **Finding (limitation, not a code bug):** with surface samples only and a tolerance of ε, a robot sample sitting in
  the middle of a wall thinner than 2ε reads ≥ −ε, so **walls thinner than 2ε (0.01) are transparent** to the
  checker. In addition, the library's straight goal-connection check (`RRT.step`, mirrored by our multi-goal check)
  samples poses every `10·eta` = 0.02 along the edge, so a fast straight connection can step over features up to
  about 0.02 + 2ε thick. This is upstream behaviour and part of the oracle; it is one reason not to pick ε > 0.005.

## 2. Winding-number sign fix: OK (v0), and kept in v1
`sdf_train.robust_sdf` takes |d| from quicksdf and the sign from `igl.fast_winding_number` (inside iff |w| > 0.5).
That is the correct robust sign for watertight and near-watertight meshes. The v1 exact detector uses the same sign rule
with exact AABB distances (libigl), so v0 labels and v1 detector agree on the sign convention (negative inside).

## 3. One RRT tree testing all goal candidates: OK, with one note
`cmgrrt.query` grows one tree with the library's `RRT.step` (goal 0 tested inside `step`). After each step it tests the
newest node against every other valid goal with the library's `is_edge_valid` and the same discretisation. On success it
sets `rrt.q2_end = g` so `get_path` works. Checked: if `step` returns `None` (no extension), no goal test happens, which
matches the library. The candidate goals depend on the contact graph (mean contact normal, ±axes, away from neighbours).
With an exact detector, run 01's "1 iteration" successes become pure straight-line escapes. Rotational solutions only
appear when the tree must wander. **This is part of the oracle definition (goal set), not a bug.** It is unchanged in v1.

## 4. Interpenetration exclusion: correct in v0, re-derived for v1
- v0 skipped assemblies whose sampled max penetration > 0.002 (368 skipped among those attempted). With the planner
  threshold −0.005, assemblies with penetration in (0.002, 0.005] would still have had valid starts under an exact SDF.
  The cutoff 0.002 was stricter than needed because the *learned* SDF had ±0.004 errors at contacts.
- Distribution over all 2,446 scanned 3–8-part assemblies (`experiments/2026-11-22_contact_scan/results.jsonl`):
  pen ≤ 0.002: 1,191; ≤ 0.005: 1,412; ≤ 0.01: 1,584; 87 have no contacts. Under ε = 0.005, about 221 more assemblies
  become eligible (R4 records the exact count).
- `max_penetration` is estimated from 3,000 surface samples per part. That is a lower bound on the true mesh
  penetration, so v1 still checks start validity per query (`start_valid`, `start_min_sdf` on the planner's own samples).

## 5. Other checks
- **Process cap (run 01 breach):** fixed in R1. Every pool worker now holds a flock slot (`src/disasm/util/slots.py`,
  `tests/test_slots.py`).
- **`start_valid` definition** = `min SDF over robot samples ≥ threshold`, the same test as `is_point_valid`. OK.
- **Bundled smoke in run 01** trained a cheaper SDF (2M × 30 epochs) and ran 4 examples at a time next to labelling. R2
  redoes it with upstream train.py defaults, one run at a time.
- **Paper vs repo** (new, `reports/run02/cmgrrt_reference.md`): the paper's CMG-RRT uses an **exact-distance grid SDF
  (CGAL AABB, 240³)**, not the repo's neural SDF. So the v1 exact detector moves our oracle *closer* to the published
  method, not away from it.

No code bugs found that change v0 numbers beyond what run 01 already reported. No fixes applied in R0.
