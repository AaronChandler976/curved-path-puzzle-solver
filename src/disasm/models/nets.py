"""Ranker models (PIPELINE TEST stage): MLP (no message passing) and GNN (GINE) encoders, each with
either a BCE head (P(success within T)) or a discrete-time survival head with right-censoring.

Survival head: K hazard logits per part over equal bins of [0, T]. A success at time t is an event in
bin b = min(K-1, floor(t / T * K)); an unsolved query is censored at T (survived all K bins).
  NLL(event in b)  = -[sum_{j<b} log(1 - h_j) + log h_b]
  NLL(censored)    = -sum_{j<K} log(1 - h_j)
From the hazards: p = P(success by T) = 1 - prod_k (1 - h_k), and the expected query cost (restricted
mean time, capped at T) c = sum_k S_{k-1} * (T/K), where S_{k-1} is survival up to the start of bin k (S_{-1} = 1).
The ranking score is p / c.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class MLPEnc(nn.Module):
    def __init__(self, d_in, h=64, layers=3):
        super().__init__()
        mods, d = [], d_in
        for _ in range(layers):
            mods += [nn.Linear(d, h), nn.ReLU()]
            d = h
        self.net = nn.Sequential(*mods)

    def forward(self, x, edge_index=None, edge_attr=None):
        return self.net(x)


class GNNEnc(nn.Module):
    def __init__(self, d_in, d_edge, h=64, layers=3):
        super().__init__()
        from torch_geometric.nn import GINEConv
        self.inp = nn.Linear(d_in, h)
        self.convs = nn.ModuleList(
            [GINEConv(nn.Sequential(nn.Linear(h, h), nn.ReLU(), nn.Linear(h, h)), edge_dim=d_edge) for _ in range(layers)])

    def forward(self, x, edge_index, edge_attr):
        x = F.relu(self.inp(x))
        for c in self.convs:
            x = x + F.relu(c(x, edge_index, edge_attr))
        return x


class Ranker(nn.Module):
    def __init__(self, enc: str, d_in, d_edge, head: str = "bce", K: int = 10, h: int = 64):
        super().__init__()
        self.enc = MLPEnc(d_in, h) if enc == "mlp" else GNNEnc(d_in, d_edge, h)
        self.head_type, self.K = head, K
        self.head = nn.Linear(h, 1 if head == "bce" else K)

    def forward(self, x, edge_index, edge_attr):
        return self.head(self.enc(x, edge_index, edge_attr))

    def loss(self, out, success, time_s, T):
        if self.head_type == "bce":
            return F.binary_cross_entropy_with_logits(out.squeeze(-1), success.float())
        K = self.K
        b = torch.clamp((time_s / T * K).long(), max=K - 1)
        log_s = F.logsigmoid(-out)          # log(1 - h)
        log_h = F.logsigmoid(out)           # log h
        cum = torch.cumsum(log_s, dim=1)    # sum_{j<=k} log(1-h_j)
        prev = torch.cat([torch.zeros_like(cum[:, :1]), cum[:, :-1]], dim=1)
        ev = -(prev.gather(1, b[:, None]).squeeze(1) + log_h.gather(1, b[:, None]).squeeze(1))
        cens = -cum[:, -1]
        return torch.where(success, ev, cens).mean()

    @torch.no_grad()
    def score(self, out, T):
        if self.head_type == "bce":
            return torch.sigmoid(out.squeeze(-1)), None
        h = torch.sigmoid(out)
        S = torch.cumprod(1 - h, dim=1)
        p = 1 - S[:, -1]
        S_prev = torch.cat([torch.ones_like(S[:, :1]), S[:, :-1]], dim=1)
        c = S_prev.sum(1) * (T / self.K)
        return p, c
