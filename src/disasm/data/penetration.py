"""Run 04 T6.2: per-pair start-pose penetration with the oracle's exact part SDFs.

For an unordered pair (a, b) whose bounding boxes overlap: pen_ab = max(0, -min SDF_b over a's vertices + N surface
samples), pen_ba likewise, pen = max(pen_ab, pen_ba). Dense (N = 20,000 + vertices) so that any planner robot-sample
draw (3,888 points) sees at most this depth. Unit frame (assembly scaled to max|coord| = 1)."""
from __future__ import annotations

import os
import time

import numpy as np

N_SAMPLES = 20000


def measure_job(job: dict) -> dict:
    import trimesh
    from disasm.oracle.cmgrrt import load_assembly
    from disasm.oracle.exact_sdf import part_sdf_cached
    t0 = time.time()
    asm = load_assembly(job["asm_dir"])
    sdf = {p: part_sdf_cached(asm, p)[0] for p in asm.part_ids}
    pts = {}
    for p, m in asm.meshes.items():
        s, _ = trimesh.sample.sample_surface(m, N_SAMPLES, seed=np.random.default_rng(1000 + p))
        pts[p] = np.concatenate([np.asarray(m.vertices), np.asarray(s)])
    ext = {p: (asm.meshes[p].bounds[1] - asm.meshes[p].bounds[0]).tolist() for p in asm.part_ids}
    pairs = {}
    ids = asm.part_ids
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            pen = []
            for x, y in ((a, b), (b, a)):
                lo, hi = sdf[y].lo, sdf[y].hi
                P = pts[x][np.all((pts[x] >= lo) & (pts[x] <= hi), 1)]
                pen.append(float(max(0.0, -sdf[y].signed(P).min())) if len(P) else 0.0)
            if max(pen) > 0:
                pairs[f"{a}-{b}"] = {"pen": max(pen), "pen_ab": pen[0], "pen_ba": pen[1]}
    return {"assembly_id": asm.id, "n_parts": len(ids), "pairs": pairs,
            "max_pen": max([0.0] + [v["pen"] for v in pairs.values()]), "extents": ext, "time_s": time.time() - t0}
