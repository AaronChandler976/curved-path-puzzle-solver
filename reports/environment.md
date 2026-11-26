# Environment audit (S0, 2026-11-21)

Log: `experiments/2026-11-21_env_audit/stdout.log`

| item | value |
|---|---|
| Python | 3.11.18 (conda env `disasm`) |
| torch | 2.11.0+cu128 (CUDA build 12.8) |
| CUDA available | True |
| GPU | NVIDIA GeForce RTX 5070 Ti, compute capability (12, 0); test matmul ran on cuda |
| PyG (torch_geometric) | 2.8.1 |
| CMG-RRT `quicksdf` (C++ ext) | imports; sign check: inside → -0.37, outside → +0.40 (negative inside) |
| CMG-RRT `taucgl_sdf`, `taucgl_rrt.*` | import OK **after** installing `spatialmath-python` (was missing; `taucgl_rrt.cspace` imports it) |
| CPU / RAM | 24 logical cores (12 physical) / 59 GiB |

Packages installed into `disasm` tonight (pip, no sudo): `spatialmath-python` (required by
taucgl_rrt), `rtree`, `tqdm`, `pymcubes` (listed in CMG-RRT's Pipfile). `austin-dist` from the
Pipfile skipped (profiler, unrelated).

Gate: PASS. torch sees the GPU and all CMG-RRT Python modules import (log above).

## Notes found while reading CMG-RRT (affects later stages)
- `scripts/test_all.py` is out of sync with the library: it calls
  `CollisionDetector(sdf_N, sdf_H, device)` (3 args) and `RRT(cd, q2_start, q2_end)` (3 args), but the
  library needs `CollisionDetector(N, H, device, threshold, eta, eps_contact)` and `RRT(cd, q1, q2_start, q2_end)`.
  `scripts/debug_rrt.py` uses the current signatures (eps_contact = |threshold|). Our smoke script follows debug_rrt.py.
- The obstacle is a **learned neural SDF** (`taucgl_sdf.model.SDFModel`, 12x64 MLP, tanh) loaded from `0.pth`.
  No `.pth` files are bundled (`*.pth` is gitignored upstream), so every obstacle needs an SDF training
  step first. For multi-part assemblies that means one SDF training **per sub-assembly state**.
