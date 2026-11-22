"""Train CMG-RRT's neural obstacle SDF (taucgl_sdf.model.SDFModel) for a mesh.

Upstream `taucgl_sdf/train.py` does the same thing (DeepSDF-style sampling labelled with
quicksdf, clamped L1 loss, Adam) but feeds 10M samples through a per-item DataLoader for
100 epochs, which is far too slow to run once per sub-assembly state. This module keeps the
model, the sampling function and the loss identical and only changes the data path: all
samples live on the GPU and are shuffled with randperm. Hyper-parameters are explicit
arguments so every run records what it used.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, asdict

import numpy as np
import torch
import torch.nn as nn
import trimesh

from taucgl_sdf.model import SDFModel
from taucgl_sdf.sampling import deepsdf_sampling


@dataclass
class SDFTrainConfig:
    num_samples: int = 2_000_000
    valid_samples: int = 100_000
    deepsdf_alpha: float = 0.8          # upstream default
    boundary_sigma: float = 5e-2        # upstream default
    normal_sigma: float = 0.7           # upstream default
    clamping_delta: float = 0.1         # upstream default
    N: int = 12                         # upstream default (must match the planner config)
    H: int = 64
    batch_size: int = 8192
    lr: float = 5e-4
    lr_final: float = 2e-5              # cosine decay to this
    epochs: int = 30
    num_threads: int = 8
    seed: int = 0


def train_sdf(mesh: trimesh.Trimesh, out_path: str, cfg: SDFTrainConfig | None = None,
              device: str = "cuda", log=print) -> dict:
    cfg = cfg or SDFTrainConfig()
    torch.manual_seed(cfg.seed)
    np.random.seed(cfg.seed)
    t0 = time.time()
    x, y = deepsdf_sampling(mesh, cfg.num_samples, cfg.deepsdf_alpha, 0.0, cfg.boundary_sigma,
                            0.0, cfg.normal_sigma, cfg.num_threads)
    xv, yv = deepsdf_sampling(mesh, cfg.valid_samples, cfg.deepsdf_alpha, 0.0, cfg.boundary_sigma,
                              0.0, cfg.normal_sigma, cfg.num_threads)
    t_sample = time.time() - t0
    return _fit(x, y, xv, yv, out_path, cfg, device, log, t0, t_sample)


def union_sampling(meshes: list, num_samples: int, cfg: "SDFTrainConfig", far_frac: float = 0.0,
                   far_box: float = 5.0, rng: np.random.Generator | None = None):
    """DeepSDF-style samples for the UNION of several watertight meshes.

    Same recipe as taucgl_sdf.sampling.deepsdf_sampling (alpha share of points = surface
    samples + N(0, boundary_sigma) noise, rest ~ N(0, normal_sigma)), with surface samples
    spread over all meshes by area. Labels are min over meshes of the per-mesh signed distance
    (quicksdf, negative inside): exact SDF of the union outside, and a lower bound on the depth
    inside. Per-mesh labelling avoids ray-parity errors where parts touch or overlap, which a
    concatenated mesh would have. far_frac of the points are uniform in [-far_box, far_box]^3
    so the field stays positive (clamped) far from the obstacle, where goal poses live.
    """
    rng = rng or np.random.default_rng(cfg.seed)
    n_far = int(far_frac * num_samples)
    n_surf = int(cfg.deepsdf_alpha * (num_samples - n_far))
    n_norm = num_samples - n_far - n_surf
    areas = np.array([m.area for m in meshes])
    counts = rng.multinomial(n_surf, areas / areas.sum())
    pts = [trimesh.sample.sample_surface(m, int(c))[0] for m, c in zip(meshes, counts) if c > 0]
    surf = np.concatenate(pts) + rng.normal(0.0, cfg.boundary_sigma, (n_surf, 3))
    samples = np.concatenate([surf, rng.normal(0.0, cfg.normal_sigma, (n_norm, 3)),
                              rng.uniform(-far_box, far_box, (n_far, 3))])
    vals = np.full(len(samples), np.inf)
    for m in meshes:
        np.minimum(vals, robust_sdf(m, samples, cfg.num_threads), out=vals)
    return samples, vals


def robust_sdf(mesh: trimesh.Trimesh, pts: np.ndarray, num_threads: int = 8) -> np.ndarray:
    """Signed distance, negative inside. |d| from quicksdf; the sign from libigl's fast winding
    number (inside iff |w| > 0.5). quicksdf's own sign (single-ray parity) is wrong for some
    points near axis-aligned CAD faces (found on ATA multi 00013: -0.386 for a point 0.386
    outside), which is exactly the contact region the planner depends on."""
    import igl
    import quicksdf
    V = np.ascontiguousarray(mesh.vertices, dtype=np.float64)
    F = np.ascontiguousarray(mesh.faces, dtype=np.int64)
    P = np.ascontiguousarray(pts, dtype=np.float64)
    d = np.abs(np.asarray(quicksdf.sdf(V, F, P, num_threads)))
    w = np.asarray(igl.fast_winding_number(V, F, P)).reshape(-1)
    return np.where(np.abs(w) > 0.5, -d, d)


def train_sdf_union(meshes: list, out_path: str, cfg: "SDFTrainConfig | None" = None,
                    device: str = "cuda", log=print, far_frac: float = 0.05) -> dict:
    """Train the CMG-RRT obstacle SDF (same SDFModel) for a union of meshes."""
    cfg = cfg or SDFTrainConfig()
    torch.manual_seed(cfg.seed)
    rng = np.random.default_rng(cfg.seed)
    np.random.seed(cfg.seed)  # trimesh.sample.sample_surface uses the global RNG
    t0 = time.time()
    x, y = union_sampling(meshes, cfg.num_samples, cfg, far_frac, rng=rng)
    xv, yv = union_sampling(meshes, cfg.valid_samples, cfg, far_frac, rng=rng)
    t_sample = time.time() - t0
    st = _fit(x, y, xv, yv, out_path, cfg, device, log, t0, t_sample)
    st["far_frac"] = far_frac
    st["n_meshes"] = len(meshes)
    return st


def _fit(x, y, xv, yv, out_path, cfg, device, log, t0, t_sample) -> dict:
    d = cfg.clamping_delta
    X = torch.tensor(x, dtype=torch.float32, device=device)
    Y = torch.tensor(y, dtype=torch.float32, device=device).clamp(-d, d)
    Xv = torch.tensor(xv, dtype=torch.float32, device=device)
    Yv_raw = torch.tensor(yv, dtype=torch.float32, device=device)
    Yv = Yv_raw.clamp(-d, d)

    model = SDFModel(cfg.N, cfg.H).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=cfg.lr)
    n = X.shape[0]
    steps_per_epoch = (n + cfg.batch_size - 1) // cfg.batch_size
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=cfg.epochs * steps_per_epoch,
                                                       eta_min=cfg.lr_final)
    crit = nn.L1Loss()
    t1 = time.time()
    for ep in range(cfg.epochs):
        perm = torch.randperm(n, device=device)
        tot = 0.0
        for i in range(steps_per_epoch):
            idx = perm[i * cfg.batch_size:(i + 1) * cfg.batch_size]
            out = model(X[idx]).flatten().clamp(-d, d)
            loss = crit(out, Y[idx])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            sched.step()
            tot += loss.detach()
        if ep == cfg.epochs - 1 or ep % 10 == 0:
            log(f"  sdf epoch {ep} train_l1 {float(tot) / steps_per_epoch:.5f}")
    t_train = time.time() - t1
    model.eval()
    with torch.no_grad():
        pv = model(Xv).flatten()
        err = (pv.clamp(-d, d) - Yv).abs()
        near = Yv_raw.abs() < 0.02
        sign_ok = (torch.sign(pv[near]) == torch.sign(Yv_raw[near])).float().mean()
        stats = {
            "valid_l1": float(err.mean()),
            "valid_l1_near_surface": float(err[near].mean()) if near.any() else None,
            "valid_p95_abs_err_near_surface": float(err[near].quantile(0.95)) if near.any() else None,
            "sign_agreement_near_surface": float(sign_ok),
        }
    torch.save({k: v.cpu() for k, v in model.state_dict().items()}, out_path)
    stats.update({"t_sample_s": t_sample, "t_train_s": t_train, "t_total_s": time.time() - t0,
                  "cfg": asdict(cfg), "out_path": out_path})
    return stats


def load_obj_merged(path: str) -> trimesh.Trimesh:
    """Load an .obj as a single mesh with duplicate vertices merged (makes the bundled
    CMG-RRT 0.obj files watertight; quicksdf's sign test is ray parity)."""
    m = trimesh.load_mesh(path, process=True)
    if isinstance(m, trimesh.Scene):
        m = m.to_mesh()
    m.merge_vertices()
    return m
