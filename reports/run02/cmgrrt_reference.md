# What CMG-RRT's authors report (R2 reference)

Sources: **[P]** Livnat, Bilevich, Kleinbort, Halperin, "Manifold-Guided Motion Planning for Tight Assemblies",
arXiv:2607.17898v1 (WAFR), read at https://arxiv.org/html/2607.17898v1 on 2026-11-22. **[R]** github.com/TAU-CGL/cmg-rrt
at commit 4ba7d48 (`external/cmg-rrt`, README, `scripts/test_list.json`, `scripts/test_all.py`, `scripts/debug_rrt.py`).

| claim | value | source |
|---|---|---|
| benchmark | 16 rotational assemblies from [19] ("puzzle" and "other"; screws excluded); 8 per category in the original 24 | [P] §5.2, Table 1 |
| per-instance names in the table | **not stated** (only Alpha, az mentioned in text) | [P] |
| success | **100%** on all 16, average success time (AST) **3.0 min** | [P] Table 1 |
| runs | 10 per instance, seeds not stated | [P] §5.2 |
| timeout | **4 hours** per run | [P] §5.2 |
| Elk | separate test, **100% success, average 156 min**; number of runs not stated | [P] §5.2 |
| contact / penetration tolerance | δ = 0.005 (contact if \|sdf\| < δ, penetration if sdf < −δ) | [P] §5.1 |
| robot samples | 10,000 boundary points | [P] §5.1 |
| SDF | **a 240³ grid with trilinear interpolation, built with CGAL AABB distance queries** (7.4 s mean, 12.9 s max); finite-difference gradients. **No neural SDF.** | [P] §3.2, §5.1, §6 |
| hardware | Intel i7-12700, **tree exploration parallelised over 16 cores**; Python + OpenMP | [P] §5.1 |
| random rotation | RandomRotate() every N_rot iterations (N_rot not stated) | [P] Alg. 1 |
| scale | models scaled to fit the unit sphere | [P] §5.1 |
| public script settings | eta 0.002, threshold −0.005, steps 50, iterations 5000, repetitions 2, sampling 4000, sdf N 12 / H 64, device cuda | [R] test_list.json |
| per-example override | `properties.json` `sampling` (only elk: 10000) | [R] |
| learned SDF in the repo | neural `SDFModel(12, 64)` loaded from `0.pth` next to `0.obj`; **no `.pth` is shipped**; train.py defaults: 10M deepsdf samples, 100 epochs, batch 2048, Adam 1e-4 | [R] |
| interactive solver | debug_rrt.py: steps 200 ("works well for puzzles"), threshold −0.006 ("for elk feasibility"), random_rotate every 10,000 iterations, no iteration cap | [R] |
| README claim | "100% success rate across all tested instances, including ... the first fully automatic solution of the Elk" | [R] README |

## Gaps between the public repo and the paper (matter for R2)
1. **Collision model:** paper = exact-distance grid SDF (CGAL); repo = neural SDF with no weights shipped. Our R2 runs
   must train the neural SDF with train.py defaults, so R2 tests the *repo*, not the paper's configuration.
2. **Parallelism and budget:** paper = 16-core parallel tree exploration, 4 h timeout; repo `test_all.py` = single
   process, 5000 iterations. Our caps (60 min elk, 20 min others) are far below the paper's timeout; for elk the cap is
   below the paper's *mean* time (156 min).
3. **Random rotation:** in the paper's Algorithm 1 and debug_rrt.py, but **not** in test_all.py.
4. **Samples:** paper 10,000; test_list.json 4000 (test_all.py's per-example override leaks: after elk every later
   example inherits 10,000 because the script overwrites the shared dict. We apply the override per example only).
5. `test_all.py` calls `CollisionDetector(N, H, device)` and `RRT(cd, q2_start, q2_end)`, which do not match the
   library signatures; the script cannot run unmodified. We use debug_rrt.py's signatures.
6. Bundled examples: 8 `general/*` + 9 `puzzle/*` (incl. elk) = 16 + elk. This count matches the paper's 16 + Elk, but
   the paper does not name the instances, so the mapping is an inference.
