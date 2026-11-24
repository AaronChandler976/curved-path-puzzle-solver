"""PointNet part encoder + run 03 ranker (run 04 T2.3; trained end to end in run 05, decision in reports/run04/DECISIONS.md).

PointNetEnc: shared per-point MLP (6 -> 64 -> 128 -> 128), max-pool, then a linear layer to d. No BatchNorm (states have
3-12 nodes, so batch statistics over parts are noisy), max-pool over points. The part embedding (d = 64) is
concatenated to the 18 hand-made node features and fed to the unchanged Ranker3 (GNN + survival head).
"""
from __future__ import annotations

import torch
import torch.nn as nn

from disasm.models.ranker3 import Ranker3


class PointNetEnc(nn.Module):
    def __init__(self, d_out: int = 64, d_in: int = 6, h: int = 128):
        super().__init__()
        self.mlp = nn.Sequential(nn.Linear(d_in, 64), nn.ReLU(), nn.Linear(64, h), nn.ReLU(), nn.Linear(h, h))
        self.out = nn.Sequential(nn.ReLU(), nn.Linear(h, d_out))

    def forward(self, pc):                      # pc: (n_nodes, n_points, 6)
        return self.out(self.mlp(pc).max(1).values)


class PointNetRanker(nn.Module):
    def __init__(self, d_hand: int, d_edge: int, head: str = "survival", d_pn: int = 64, **kw):
        super().__init__()
        self.pn = PointNetEnc(d_pn)
        self.ranker = Ranker3("gnn", d_hand + d_pn, d_edge, head, **kw)

    def forward(self, x_hand, pc, edge_index, edge_attr):
        return self.ranker(torch.cat([x_hand, self.pn(pc)], 1), edge_index, edge_attr)

    def loss(self, out, succ, cens_t):
        return self.ranker.loss(out, succ, cens_t)

    def predict(self, out):
        return self.ranker.predict(out)
