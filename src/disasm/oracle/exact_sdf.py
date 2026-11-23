"""Exact union-SDF collision detector for CMG-RRT (run 02 oracle; docs/PLAN.md "Oracle definition").

How CMG-RRT uses its collision model (external/cmg-rrt/.../collision_detection.py, read in R3):
every query -- is_point_valid, is_edge_valid, distance_between_objects, get_close_distances_hierarchy(_gpu),
get_gradients (central finite differences over the 7 pose coordinates, dx = 6e-6), get_contact_gradients(_weighted)
-- ends in ONE call ``self.obstacles['sdf'](points)`` with a float32 torch tensor of shape (N, 3) on ``cd.device``
(points already mapped into the obstacle frame q1), under ``torch.no_grad()``, expecting an (N, 1) tensor back on the
same device. No autograd gradients are used; gradients are finite differences of that call. So the drop-in is:
replace ``obstacles['sdf']`` by an exact callable. The planning algorithm (RRT, extend, retract, contact handling) is
untouched (CLAUDE.md rule 2: only the collision representation is swapped).

Exact SDF per part (computed once per part per assembly, cached to disk):
- |d|: exact point-to-triangle distance with libigl's AABB tree (``igl.AABB.squared_distance``), float64.
- sign: angle-weighted pseudonormal at the closest feature (face / edge / vertex), which is exact for watertight,
  consistently oriented meshes (Baerentzen & Aanaes 2005). At setup each part's pseudonormal sign is checked against
  libigl's robust fast winding number on probe points; if they disagree on more than 0.1% of the probes (e.g. a mesh
  that is not watertight) the part falls back to the winding-number sign at run time (slower, always robust).
- Gradients: not needed by the planner. Finite differences of this exact SDF equal the closest-point direction of the
  min-achieving part, (x - c)/d * sign, wherever the distance is differentiable.

Union: the obstacle SDF at x is min_k d_k(x) over the other remaining parts, each part in its own fixed
(assembled) frame. Speed-up that keeps exactness where it matters: for part k, the distance from x to the part's
bounding box is a lower bound of d_k(x); if that lower bound exceeds ``band`` (default 0.1 in scaled units, i.e. 20x
the contact tolerance) the lower bound is used instead of the exact value. The returned value is therefore always a
lower bound of the true union SDF and is EXACT wherever the true union SDF is <= band -- in particular at every
threshold the planner compares against (threshold -eps, eps_contact = eps, cluster tests d - r <= eps are
conservative under a lower bound).

Contact tolerance eps: a pose collides only if min SDF < -eps. In CMG-RRT this is exactly ``threshold = -eps``
(is_point_valid: min >= threshold), with ``eps_contact = eps`` as in the library defaults (|threshold|).
"""
from __future__ import annotations

import json
import os
import time

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CACHE = os.path.join(ROOT, "data", "processed", "exact_sdf_v1")
DEFAULT_BAND = 0.1
BARY_TOL = 1e-6


def _wn_sign(V, F, P):
    import igl
    w = np.asarray(igl.fast_winding_number(V, F, np.ascontiguousarray(P))).reshape(-1)
    return np.where(np.abs(w) > 0.5, -1.0, 1.0)


class PartSDF:
    """Exact signed distance to one triangle mesh (fixed frame). Negative inside."""

    def __init__(self, V: np.ndarray, F: np.ndarray, name: str = "", sign_mode: str | None = None,
                 n_probe: int = 4000, seed: int = 0):
        import igl
        t0 = time.time()
        self.name = name
        self.V = np.ascontiguousarray(V, dtype=np.float64)
        self.F = np.ascontiguousarray(F, dtype=np.int64)
        self.lo = self.V.min(0)
        self.hi = self.V.max(0)
        self.tree = igl.AABB()
        self.tree.init(self.V, self.F)
        self.FN = np.asarray(igl.per_face_normals(self.V, self.F, np.array([0.0, 0.0, 1.0])), dtype=np.float64)
        self.FN = np.nan_to_num(self.FN)
        self.VN = np.asarray(igl.per_vertex_normals(self.V, self.F, igl.PER_VERTEX_NORMALS_WEIGHTING_TYPE_ANGLE),
                             dtype=np.float64)
        EN, E, EMAP = igl.per_edge_normals(self.V, self.F, igl.PER_EDGE_NORMALS_WEIGHTING_TYPE_UNIFORM)
        self.EN, self.EMAP = np.asarray(EN, dtype=np.float64), np.asarray(EMAP, dtype=np.int64).reshape(-1)
        self.nF = len(self.F)
        self.build_s = time.time() - t0
        self.sign_mode = sign_mode or "pseudonormal"
        self.sign_check = None
        if sign_mode is None:
            self.sign_check = self._check_sign(n_probe, seed)
            if self.sign_check["agreement"] < 0.999:
                self.sign_mode = "winding_number"
        self.setup_s = time.time() - t0

    # ---------------------------------------------------------------- exact signed distance
    def _closest(self, P):
        d2, I, C = self.tree.squared_distance(self.V, self.F, P)
        return np.sqrt(np.maximum(np.asarray(d2).reshape(-1), 0.0)), np.asarray(I).reshape(-1), np.asarray(C)

    def _pn_sign(self, P, I, C):
        tri = self.V[self.F[I]]                      # (n, 3, 3)
        a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
        v0, v1, v2 = b - a, c - a, C - a
        d00 = np.einsum("ij,ij->i", v0, v0); d01 = np.einsum("ij,ij->i", v0, v1)
        d11 = np.einsum("ij,ij->i", v1, v1); d20 = np.einsum("ij,ij->i", v2, v0)
        d21 = np.einsum("ij,ij->i", v2, v1)
        den = d00 * d11 - d01 * d01
        den = np.where(np.abs(den) < 1e-30, 1e-30, den)
        bv = (d11 * d20 - d01 * d21) / den
        bw = (d00 * d21 - d01 * d20) / den
        bary = np.stack([1.0 - bv - bw, bv, bw], 1)  # weights of vertices 0, 1, 2
        small = bary < BARY_TOL
        nsmall = small.sum(1)
        n = self.FN[I].copy()
        # edge: exactly one barycentric ~0 -> edge opposite that vertex; igl EMAP(f + i*F) = edge opposite vertex i
        e_rows = np.where(nsmall == 1)[0]
        if len(e_rows):
            k = np.argmax(small[e_rows], 1)
            n[e_rows] = self.EN[self.EMAP[I[e_rows] + k * self.nF]]
        v_rows = np.where(nsmall >= 2)[0]
        if len(v_rows):
            k = np.argmax(bary[v_rows], 1)
            n[v_rows] = self.VN[self.F[I[v_rows], k]]
        s = np.einsum("ij,ij->i", P - C, n)
        return np.where(s < 0, -1.0, 1.0)

    def signed(self, P: np.ndarray) -> np.ndarray:
        P = np.ascontiguousarray(P, dtype=np.float64)
        if len(P) == 0:
            return np.zeros(0)
        d, I, C = self._closest(P)
        if self.sign_mode == "winding_number":
            sg = _wn_sign(self.V, self.F, P)
        else:
            sg = self._pn_sign(P, I, C)
        return sg * d

    def box_lower_bound(self, P: np.ndarray) -> np.ndarray:
        g = np.maximum(np.maximum(self.lo - P, P - self.hi), 0.0)
        return np.sqrt((g * g).sum(1))

    def _check_sign(self, n, seed):
        """Pseudonormal vs robust winding-number sign on probe points near and away from the surface."""
        import trimesh
        rng = np.random.default_rng(seed)
        m = trimesh.Trimesh(self.V, self.F, process=False)
        st = np.random.get_state(); np.random.seed(seed)
        pts, fi = trimesh.sample.sample_surface(m, n)
        np.random.set_state(st)
        off = rng.choice([-1, 1], n) * 10 ** rng.uniform(-4, -1.3, n)    # |offset| in [1e-4, 0.05]
        P = np.asarray(pts) + off[:, None] * self.FN[fi]
        box = rng.uniform(self.lo - 0.05, self.hi + 0.05, (n // 4, 3))
        P = np.concatenate([P, box])
        d, I, C = self._closest(P)
        pn = self._pn_sign(P, I, C)
        wn = _wn_sign(self.V, self.F, P)
        keep = d > 1e-7
        agree = float((pn[keep] == wn[keep]).mean()) if keep.any() else 1.0
        return {"agreement": agree, "n_probe": int(keep.sum()), "inside_frac_wn": float((wn < 0).mean())}

    def meta(self) -> dict:
        return {"name": self.name, "n_faces": int(self.nF), "n_vertices": int(len(self.V)), "build_s": self.build_s,
                "setup_s": self.setup_s, "sign_mode": self.sign_mode, "sign_check": self.sign_check,
                "bbox": [self.lo.tolist(), self.hi.tolist()]}


class ExactUnionSDF:
    """Callable drop-in for CMG-RRT's ``obstacles['sdf']``: torch (N, 3) -> torch (N, 1), min over parts."""

    def __init__(self, parts: list, band: float = DEFAULT_BAND):
        self.parts = list(parts)
        self.band = band
        self.n_calls = 0
        self.n_points = 0
        self.n_exact = 0

    def eval_np(self, P: np.ndarray) -> np.ndarray:
        P = np.ascontiguousarray(P, dtype=np.float64)
        out = np.full(len(P), np.inf)
        for part in self.parts:
            lb = part.box_lower_bound(P)
            near = lb <= self.band
            val = lb
            if near.any():
                val = lb.copy()
                val[near] = part.signed(P[near])
                self.n_exact += int(near.sum())
            np.minimum(out, val, out=out)
        self.n_calls += 1
        self.n_points += len(P)
        return out

    def __call__(self, pts):
        import torch
        P = pts.detach().to("cpu", torch.float64).numpy()
        v = self.eval_np(P)
        return torch.from_numpy(v.astype(np.float32)).reshape(-1, 1).to(pts.device)

    # nn.Module-like no-ops so code that calls .to()/.eval() on the SDF keeps working
    def to(self, *_a, **_k):
        return self

    def eval(self):
        return self


def make_detector(params, device, union: ExactUnionSDF, q1=None, eps: float | None = None):
    """CMG-RRT CollisionDetector with the exact union SDF installed. eps (contact tolerance) defines
    threshold = -eps and eps_contact = eps; default = the planner params (threshold -0.005)."""
    import torch
    from taucgl_rrt.collision_detection import CollisionDetector
    from taucgl_rrt.cspace import SE3

    class ExactSDFCollisionDetector(CollisionDetector):
        """Library detector; only set_obstacles differs (installs the exact union instead of a .pth)."""

        def set_obstacles(self, sdf, q1):
            if isinstance(sdf, ExactUnionSDF):
                self.obstacles = {"sdf": sdf, "q1": q1, "Aq1_inv": np.linalg.inv(q1.to_matrix())}
            else:
                super().set_obstacles(sdf, q1)

    thr = params.threshold if eps is None else -abs(eps)
    cd = ExactSDFCollisionDetector(params.sdf_N, params.sdf_H, torch.device(device), thr, params.eta, abs(thr))
    cd.set_obstacles(union, q1 if q1 is not None else SE3())
    return cd


# ----------------------------------------------------------------------------- per-assembly cache
def part_sdf_cached(asm, part: int, cache_dir: str = CACHE) -> tuple:
    """(PartSDF, setup_s_this_call, from_cache). The mesh arrays + sign check are cached on disk per
    (assembly, part); the AABB is rebuilt on load (milliseconds)."""
    d = os.path.join(cache_dir, asm.id)
    os.makedirs(d, exist_ok=True)
    npz, js = os.path.join(d, f"{part}.npz"), os.path.join(d, f"{part}.json")
    t0 = time.time()
    if os.path.exists(npz) and os.path.exists(js):
        z = np.load(npz)
        meta = json.load(open(js))
        ps = PartSDF(z["V"], z["F"], name=f"{asm.id}/{part}", sign_mode=meta["sign_mode"])
        ps.sign_check = meta.get("sign_check")
        ps.first_setup_s = meta.get("setup_s")
        return ps, time.time() - t0, True
    m = asm.meshes[part]
    ps = PartSDF(np.asarray(m.vertices), np.asarray(m.faces), name=f"{asm.id}/{part}")
    tmp = npz + f".tmp{os.getpid()}.npz"
    np.savez(tmp, V=ps.V, F=ps.F)
    os.replace(tmp, npz)
    meta = ps.meta()
    json.dump(meta, open(js + f".tmp{os.getpid()}", "w"))
    os.replace(js + f".tmp{os.getpid()}", js)
    ps.first_setup_s = ps.setup_s
    return ps, time.time() - t0, False
