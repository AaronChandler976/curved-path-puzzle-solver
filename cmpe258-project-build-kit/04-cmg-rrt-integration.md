# CMG-RRT Integration Notes

Read from source in Sept 2026; not yet run. Update this file after the first smoke test.

## Repository

github.com/TAU-CGL/cmg-rrt (MIT). Linked from cgl.cs.tau.ac.il/projects/tight-assembly-planning. Don't confuse it with TAU-CGL/tr-rrt-public.

- `src/quicksdf/`: C++ extension (pybind11 + scikit-build-core) for fast SDF queries via CGAL AABB trees. The only non-trivial build dependency.
- `src/taucgl-sdf/`, `src/taucgl-rrt/`: pure-Python collision detector and RRT planner.
- `scripts/test_all.py`: reference driver. Also `debug_rrt.py`, `visualize_config.py`.
- `resources/models/puzzle/`: bundled examples incl. **`elk`**, `mobius_light`, `key_light_1`, `abc_light`, `alpha`, `az`, `aj`, `doublealpha`, `duet-g1`.
- `resources/models/general/`: eight numbered two-body test cases.

## Input / output

Each example folder:
- `0.obj` = static/obstacle body, `1.obj` = moving body
- `0.urdf`, `1.urdf`: for PyBullet visualization only
- `0_sdf.obj`, `1_sdf.obj`: simplified meshes for SDF/collision
- `properties.json`: `q1` (obstacle SE(3) pose), `q2_start`, `q2_end` (moving-body start and **goal** pose); optional per-example `sampling` override

Driver: build `CollisionDetector(obstacle mesh, moving mesh)` → `RRT(cd, q2_start, q2_end)` → loop `rrt.step(eta, threshold, steps)` until solved or iteration cap → `rrt.get_path()` (pickled). Logs success, iterations, wall-clock. Settings in `scripts/test_list.json`: `device` (cpu/cuda), `eta`, `threshold`, `steps`, `iterations`, `sdf-N`, `sdf-H`, `sampling`.

## Integration gaps to design for

1. **Goal pose required.** CMG-RRT answers "path from pose A to pose B?", not "can part P get out?" The query layer must supply a "clear of the assembly" goal pose: e.g., translate outward along an estimated escape direction (from contact normals or the Assemble Them All planner's direction) by a margin, possibly trying several candidates.
2. **Two bodies only.** For multi-part assemblies, merge all remaining static parts into one obstacle mesh per query (recompute the SDF per state, or cache per state).
3. **Timeouts.** Decide whether a timeout counts as failure, a censored label, or a retry with a different goal pose. This affects both labels and the call-count metric.
4. **Mesh preprocessing.** Fusion 360 / Assemble Them All meshes need the `*_sdf.obj` simplified versions and URDFs generated. Script this.

## Install on the Ubuntu desktop (native, conda)

```bash
sudo apt update && sudo apt install -y build-essential cmake libcgal-dev libgmp-dev libmpfr-dev git
conda create -n cmgrrt python=3.11 -y
conda activate cmgrrt
mkdir -p ~/SJSU/FALL_2026/CMPE_258/CMPE_258_PROJECT && cd ~/SJSU/FALL_2026/CMPE_258/CMPE_258_PROJECT
git clone https://github.com/TAU-CGL/cmg-rrt.git && cd cmg-rrt
pip install ./src/quicksdf
pip install -e ./src/taucgl-sdf -e ./src/taucgl-rrt
# then install the rest of the README's runtime deps; austin-dist is an unrelated profiler and safe to skip
```

GPU note: the RTX 5070 Ti (Blackwell) needs a PyTorch build for CUDA 12.8+ (check pytorch.org's install selector). Try `device: "cpu"` first anyway.

First smoke test: trim `scripts/test_list.json` to only `elk`, `device: "cpu"`, `iterations: 500`, run `python scripts/test_all.py`, record success/iterations/time. Then repeat with `cuda` and full iterations. **Per-query time from this run sets the whole project's query budget.**

## Status

- Source read: done (Sept 2026).
- Install + smoke test: **not yet run/reported.**
- Next: run the smoke test, record timings here, then try one Assemble Them All rotational two-part assembly converted to CMG-RRT format.
