"""Per-part point clouds for the PointNet+GNN variant (run 04 T2.3; trained in run 05).

Frame: part-local translation (points minus the part's area-weighted surface centroid), axes kept parallel to the
assembly frame, length unit = the assembly unit frame (assembly scaled to max|coord| = 1, as the oracle uses).
Rationale: removal directions and contacts live in the assembly frame, so rotating each part into its own PCA frame
would throw away exactly the orientation the ranker needs; centring removes absolute position (already a hand feature),
and a common scale keeps relative part sizes comparable across parts of one assembly.
Fixed count n (default 1,024) of area-weighted surface samples with their face normals -> (n, 6) float32.
Seeded: rng = default_rng(crc32(f"{assembly_id}/{part}") + seed), so the same part always gets the same cloud.
"""
from __future__ import annotations

import zlib

import numpy as np

N_POINTS = 1024


def part_cloud(mesh, aid: str, part: int, n: int = N_POINTS, seed: int = 0) -> np.ndarray:
    import trimesh
    rng = np.random.default_rng(zlib.crc32(f"{aid}/{int(part)}".encode()) + int(seed))
    pts, fi = trimesh.sample.sample_surface(mesh, n, seed=rng)
    pts = np.asarray(pts, dtype=np.float64)
    c = pts.mean(0)          # mean of area-weighted samples = Monte-Carlo surface centroid
    nrm = np.asarray(mesh.face_normals[fi], dtype=np.float64)
    return np.concatenate([pts - c, nrm], 1).astype(np.float32)


def assembly_clouds(asm, n: int = N_POINTS, seed: int = 0) -> dict:
    """{part: (n, 6)} for an oracle Assembly (meshes already in the unit frame)."""
    return {p: part_cloud(asm.meshes[p], asm.id, p, n, seed) for p in asm.part_ids}
