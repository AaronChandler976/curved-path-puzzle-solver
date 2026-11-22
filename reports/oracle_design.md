# CMG-RRT oracle adapter: design and checks (S3)

Code: `src/disasm/oracle/cmgrrt.py` (query, contacts, goals), `src/disasm/oracle/sdf_train.py` (obstacle SDF),
`src/disasm/oracle/cmgrrt_core.py` (two-body runner used by the smoke test). CMG-RRT itself (`external/cmg-rrt`) is unmodified.

## What CMG-RRT needs, and how we feed it
| CMG-RRT input | what it is in the library | what we pass |
|---|---|---|
| obstacle | neural SDF `.pth` (`taucgl_sdf.model.SDFModel(12, 64)`), evaluated in the q1 frame | SDF trained on the union of all present parts except the queried one |
| robot | mesh file, from which `generate_robot_sampling(4000)` draws surface samples | the queried part's mesh, exported in world (assembled) coordinates |
| q1, q2_start | SE3 `[x, y, z, qw, qx, qy, qz]`; `Aq2 = inv(A(q1)) @ A(q2)` (collision_detection.py) | identity / identity (meshes are already posed) |
| q2_end | goal pose | translation by D·d per candidate direction d, D = assembly bbox diagonal + 0.1 |
| eta, threshold, steps, sampling | test_list.json: 0.002, -0.005, 50, 4000 | unchanged |

**Pose convention check.** In bundled `general/06397`, `properties.json` q1/q2_start equal 0.2 × the ATA
`translation.json` offsets ([0.0064, 0, -0.0133] → [0.00129, 0, -0.00265]; [0.447, 0, 1.857] → [0.0895, 0, 0.371]),
and the bundled `0.obj` equals ATA's `0.obj` × 0.2. So bundled examples are ATA geometry scaled by 0.2, with each
part's local mesh placed by its pose. ATA multi-part meshes are stored already assembled with max|coord| = 5, so
scaling by 0.2 and using identity poses reproduces the same frame. `tests/test_oracle_bundled.py` builds a bundled
example by applying properties.json q1/q2_start to the meshes and runs it through `query()`.

**`*_sdf.obj` files.** `0_sdf.obj` is a watertight remesh of `0.obj` at the same scale and bounds (6184 vertices / 12364
faces vs 6677 / 5056, bounds equal within 0.005; bundled 0.obj is not watertight). `1_sdf.obj` is the moving part
renormalised to max|coord| = 1 (its own SDF frame). CMG-RRT itself only reads `0.pth` (obstacle SDF) and `1.obj`
(robot samples). The repo has no script that generates `*_sdf.obj`. ATA multi-part meshes are already watertight
(4192/4196, `experiments/2026-11-21_inspect_multi/summary.json`), so we skip remeshing and label directly on the meshes.

## Obstacle SDF
- Samples: DeepSDF recipe as in upstream `deepsdf_sampling` (80% surface + N(0, 0.05), 20% N(0, 0.7)), spread over the
  obstacle parts by area, plus 5% uniform in [-5, 5]^3 so the far field (where goals are) is trained positive.
- Labels: min over parts of the per-part signed distance. Magnitude from quicksdf; **sign from libigl fast winding number**.
  quicksdf's ray-parity sign is wrong for some points near axis-aligned CAD faces. On 00013 it reported -0.386 for a
  point 0.386 outside a genus-1 part, which made a non-touching pair look 0.69 deep in penetration.
- Training: 2M samples, 30 epochs, batch 8192, Adam 5e-4 with cosine decay to 2e-5, clamped L1 (delta 0.1). This is far
  cheaper than upstream (10M × 100 epochs × batch 2048). Validation stats are logged per SDF (`*.pth.json`), and each label
  line carries `sdf_sign_agreement` (sign agreement within 0.02 of the surface).
- Cache: `data/processed/obstacle_sdf/<assembly>/<sorted obstacle ids>_e30_n2000000.pth`, written atomically.

## Goals and the shared budget
Candidate directions, deduplicated at cos > 0.995: mean outward contact normal (mean of −n_p over p's surface samples
within 0.01 of a present neighbour, weighted by count), ±x, ±y, ±z, and unit vectors from each present neighbour's
centroid to the part's centroid. A goal is kept only if the SDF says it is collision-free. One CMG-RRT tree is grown from
the assembled pose. `RRT.step` tests the first goal itself, and after each step the newest node is also tested for a straight
connection to every other goal with `is_edge_valid` (same discretisation as `RRT.step`). The first connection wins.

## Known limitations (measured, see the morning report)
- **Mesh interpenetration:** many ATA assemblies have parts overlapping in the assembled pose (00008: 0.07, 00009: 0.096
  unit-frame depth). The start pose is then invalid (SDF < -0.005), and the query cannot succeed. Such assemblies are
  excluded from labelling (filter from `experiments/2026-11-22_contact_scan/`, threshold 0.002).
- **SDF error at flush contacts:** with our fast SDF, start clearance at flush contacts reads about -0.002 to -0.004 (00089), close
  to the -0.005 threshold.
- `linear_precheck()` (a straight-line sweep along each candidate) is diagnostic only and never replaces a CMG-RRT query.
