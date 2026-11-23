"""ASAP GNN baseline (yunshengtian/ASAP, released weights, zero-shot) as a query ordering.

Model: ``ModelGraph`` from external/ASAP/plan_sequence/generator/network/model.py, loaded by file path (the package
``__init__`` imports the redmax simulator, which is not installed). Weights: ``pretrained_model.pt`` (the file the
ASAP code downloads from people.csail.mit.edu/yunsheng/ASAP/), kept in data/raw/asap_ckpt/. No code under external/
is modified.

Inputs, built exactly as ASAP's ``AssemblyDataGraph.load_assembly_graph`` + ``LearningBasedGenerator`` do, except for
the contact graph:
- per part: 1,000 surface samples of the raw mesh (trimesh, process=False), assembly-level centring and scaling
  (bbox of all parts' samples, scale = 2 / max extent), ``volume * scale`` (ASAP multiplies the raw volume by the
  linear scale; kept as is), centre of mass -> ``distance`` = norm after centring/scaling;
- per state: the subgraph induced by the present parts, ``edge_count`` = degree in that subgraph;
- contact graph: ASAP calls redmax ``body_in_contact(a, b, eps=0.1)`` = min(d_ab, d_ba) < 0.1 in raw units, with
  d_ab = min SDF of body b at body a's points. redmax is not installed, so we compute the same test with our exact
  per-part SDFs (data/processed/exact_sdf_v1) at each part's vertices + 3,000 surface samples (unit frame,
  eps = 0.1 * unit scale). This is an adapter change, documented in reports/run03/DECISIONS.md.
- score = sigmoid(logits); parts are queried in descending score (ASAP's ``generate_candidate_part``).
Point-cloud sampling is seeded per assembly (seed 0 + assembly id) for reproducibility.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import zlib

import numpy as np
import torch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODEL_PY = os.path.join(ROOT, "external/ASAP/plan_sequence/generator/network/model.py")
CKPT = os.path.join(ROOT, "data/raw/asap_ckpt/pretrained_model.pt")
ASAP_CONTACT_EPS = 0.1      # plan_sequence/physics_planner.py CONTACT_EPS (raw units)
MAX_PC = 1000               # generator/network/args.py max_pc_size


def load_asap_model(ckpt: str = CKPT):
    spec = importlib.util.spec_from_file_location("asap_network_model", MODEL_PY)
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    args = argparse.Namespace(max_pc_size=MAX_PC, feat_len=512, dropout=0.0, batch_norm=1)   # args.py values
    m = M.ModelGraph(args)
    ck = torch.load(ckpt, map_location="cpu", weights_only=False)
    m.load_state_dict(ck["model_state_dict"])
    m.eval()
    return m, {"epoch": ck.get("epoch"), "loss": float(ck.get("loss", float("nan")))}


def asap_contact_pairs(asm_unit, eps_raw: float = ASAP_CONTACT_EPS, n_samples: int = 3000) -> set:
    """Undirected contact pairs per redmax body_in_contact semantics, using exact per-part SDFs."""
    import trimesh
    from disasm.oracle.exact_sdf import part_sdf_cached
    eps = eps_raw * asm_unit.scale
    sdf = {p: part_sdf_cached(asm_unit, p)[0] for p in asm_unit.part_ids}
    pts = {}
    st = np.random.get_state()
    np.random.seed(0)
    for p, m in asm_unit.meshes.items():
        s, _ = trimesh.sample.sample_surface(m, n_samples, seed=0)
        pts[p] = np.concatenate([np.asarray(m.vertices), np.asarray(s)])
    np.random.set_state(st)
    pairs = set()
    ids = asm_unit.part_ids
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            lo, hi = sdf[b].lo - eps, sdf[b].hi + eps
            pa = pts[a][np.all((pts[a] >= lo) & (pts[a] <= hi), 1)]
            d_ab = sdf[b].signed(pa).min() if len(pa) else np.inf
            lo, hi = sdf[a].lo - eps, sdf[a].hi + eps
            pb = pts[b][np.all((pts[b] >= lo) & (pts[b] <= hi), 1)]
            d_ba = sdf[a].signed(pb).min() if len(pb) else np.inf
            if min(d_ab, d_ba) < eps:
                pairs.add((a, b))
    return pairs


def asap_node_inputs(asm_dir: str, aid: str):
    """Per-part ASAP node inputs for the full assembly: dict part -> (pc (1000,3), volume, distance)."""
    import glob
    import trimesh
    files = sorted(glob.glob(os.path.join(asm_dir, "*.obj")), key=lambda f: int(os.path.basename(f)[:-4]))
    rng_seed = zlib.crc32(aid.encode())
    pcs, vol, com = {}, {}, {}
    for f in files:
        p = int(os.path.basename(f)[:-4])
        m = trimesh.load_mesh(f, process=False, maintain_order=True)
        pc, _ = trimesh.sample.sample_surface(m, MAX_PC, seed=rng_seed + p)
        pcs[p] = torch.from_numpy(np.asarray(pc)).float()
        vol[p] = torch.tensor(m.volume).float()
        com[p] = torch.tensor(m.center_mass).float()
    allp = torch.vstack(list(pcs.values()))
    lo, hi = allp.min(0).values, allp.max(0).values
    scale = 2.0 / max(hi - lo)
    center = 0.5 * (lo + hi)
    out = {}
    for p in pcs:
        x = (pcs[p] - center) * scale
        c = (com[p] - center) * scale
        out[p] = (x, vol[p] * scale, torch.linalg.norm(c))
    return out


@torch.no_grad()
def asap_scores(model, node_inputs: dict, contact_pairs: set, present: list) -> np.ndarray:
    """sigmoid(logits) for the present parts (in the order of `present`)."""
    from torch_geometric.data import Data
    idx = {p: i for i, p in enumerate(present)}
    src, dst = [], []
    for a, b in contact_pairs:
        if a in idx and b in idx:
            src += [idx[a], idx[b]]; dst += [idx[b], idx[a]]
    ei = torch.tensor([src, dst], dtype=torch.long).reshape(2, -1)
    deg = torch.zeros(len(present))
    for s in src:
        deg[s] += 1
    x = torch.stack([node_inputs[p][0] for p in present])
    g = Data(x=x, edge_index=ei, volume=torch.stack([node_inputs[p][1] for p in present]),
             distance=torch.stack([node_inputs[p][2] for p in present]), edge_count=deg)
    logits = model.forward_logits(g).reshape(-1)
    return torch.sigmoid(logits).numpy()
