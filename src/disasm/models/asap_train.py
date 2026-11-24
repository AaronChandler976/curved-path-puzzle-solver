"""ASAP's GNN retrained on our labels with ASAP's own objective (run 04 T2.2 pipeline; real training is run 05).

What ASAP's public code fixes (external/ASAP/plan_sequence/generator/network/{model,data}.py, read in run 04 T2):
- model: ``ModelGraph`` = PointNet (1,000 pts, feat 512) -> MLPMultiFeature(volume, distance, edge_count) ->
  2 x GATv2 (8 heads) -> MLP node classifier; ``batch_norm = 1``, ``dropout = 0.0`` (args.py);
- objective: ``ModelGraph.forward`` = ``BCEWithLogitsLoss(logits, graph.y)`` with y = 1 for the single part removed
  in the ground-truth sequence step and 0 for every other present part (data.py asserts exactly one positive);
- augmentation: in the train split, every point cloud of a graph is rotated by one random rotation in 90 deg steps
  about a random canonical axis (``AssemblyDataGraph.get_random_rotation`` / ``random_rotate_points``, re-implemented
  here verbatim because data.py imports modules we do not need);
- inputs: ``load_assembly_graph`` (see disasm.search.asap_baseline.asap_node_inputs; contact graph = redmax
  ``body_in_contact(0.1)``, which our adapter reproduces exactly on 20/20 train assemblies, run 04 T2.1).
NOT in the public code: the training loop, optimiser, learning rate, batch size, epochs (the released checkpoint
says epoch 150). Those are chosen in run 05 under the shared tuning budget (docs/PREREG_run05.md).

Our label mapping: y = 1 for the part our forward disassembly removed at that state (``chosen`` in states.jsonl,
a uniformly random planner success), 0 for every other present part. This is exactly ASAP's one-positive format.
"""
from __future__ import annotations

import os
import random

import numpy as np
import torch

from disasm.search.asap_baseline import MODEL_PY, MAX_PC, asap_contact_pairs, asap_node_inputs


def new_asap_model(seed: int = 0, dropout: float = 0.0):
    import argparse
    import importlib.util
    torch.manual_seed(seed)
    spec = importlib.util.spec_from_file_location("asap_network_model", MODEL_PY)
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    return M.ModelGraph(argparse.Namespace(max_pc_size=MAX_PC, feat_len=512, dropout=dropout, batch_norm=1))


def random_rotation(rng: random.Random):
    """ASAP AssemblyDataGraph.get_random_rotation (90 deg steps about a random canonical axis)."""
    from scipy.spatial.transform import Rotation
    axes = [np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0])]
    angles = [0.0, 90.0, 180.0, 270.0]
    axis = rng.choice(axes)
    return Rotation.from_rotvec(np.radians(rng.choice(angles)) * axis)


def rotate_points(pc: torch.Tensor, rot) -> torch.Tensor:
    """ASAP AssemblyDataGraph.random_rotate_points: pc (n, m, 3) @ R."""
    R = torch.tensor(rot.as_matrix()).float().to(pc.device)
    s = pc.size()
    return torch.mm(pc.reshape(-1, 3), R).view(s)


def state_data(node_inputs: dict, pairs: set, present: list, chosen: int):
    from torch_geometric.data import Data
    idx = {p: i for i, p in enumerate(present)}
    src, dst = [], []
    for a, b in pairs:
        if a in idx and b in idx:
            src += [idx[a], idx[b]]; dst += [idx[b], idx[a]]
    ei = torch.tensor([src, dst], dtype=torch.long).reshape(2, -1)
    deg = torch.zeros(len(present))
    for s in src:
        deg[s] += 1          # = len(subgraph.edges(node)) in ASAP (undirected degree)
    y = torch.tensor([float(p == chosen) for p in present])
    return Data(x=torch.stack([node_inputs[p][0] for p in present]), edge_index=ei,
                volume=torch.stack([node_inputs[p][1] for p in present]),
                distance=torch.stack([node_inputs[p][2] for p in present]), edge_count=deg, y=y)


def build_dataset(aids, states_by_aid: dict, raw_dir: str, load_assembly):
    """One ASAP graph per labelled state that has a removal (chosen != None)."""
    out = []
    for aid in aids:
        sts = [s for s in states_by_aid.get(aid, []) if s.get("chosen") is not None]
        if not sts:
            continue
        asm = load_assembly(os.path.join(raw_dir, aid))
        pairs = {tuple(sorted(p)) for p in asap_contact_pairs(asm)}
        ni = asap_node_inputs(os.path.join(raw_dir, aid), aid)
        for s in sts:
            present = [int(p) for p in s["state_key"].split("-")]
            d = state_data(ni, pairs, present, int(s["chosen"]))
            d.aid, d.skey = aid, s["state_key"]
            out.append(d)
    return out


def train_epoch(model, data, opt, batch_size: int, rng: random.Random, device, rotate: bool = True):
    """One epoch with ASAP's loss (model.forward) and ASAP's train-time rotation. Returns (mean loss, top-1 acc)."""
    from torch_geometric.data import Batch
    model.train()
    order = list(range(len(data)))
    rng.shuffle(order)
    tot, acc, n = 0.0, 0.0, 0
    for i in range(0, len(order), batch_size):
        gs = []
        for j in order[i:i + batch_size]:
            g = data[j].clone()
            if rotate:
                g.x = rotate_points(g.x, random_rotation(rng))
            gs.append(g)
        b = Batch.from_data_list(gs).to(device)
        loss, top1 = model(b)
        opt.zero_grad()
        loss.backward()
        opt.step()
        tot += float(loss) * b.num_graphs
        acc += float(top1) * b.num_graphs
        n += b.num_graphs
    return tot / max(1, n), acc / max(1, n)
