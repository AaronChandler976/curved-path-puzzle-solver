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
