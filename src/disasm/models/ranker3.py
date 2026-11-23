"""Run 03 rankers: MLP (no message passing) and GNN (GINE + edge features, residual, LayerNorm), each with a
BCE head (P(success)) or a discrete-time survival head over K log-spaced bins up to T (censoring-aware NLL).

Survival head. Bin right edges e_1 < ... < e_K = T, log-spaced from e_1 = 0.1 s (``bin_edges``). Hazard
h_k = P(event in bin k | survived to its start). A success at time t is an event in bin b = first k with t <= e_k
(t > T -> b = K, the planner finished an iteration after the deadline). An unsolved query censored at time c
survived every bin whose right edge is <= c (for v1 every unsolved time is > T, i.e. all K bins).
  NLL(event in b) = -[sum_{j<b} log(1 - h_j) + log h_b],   NLL(censored) = -sum_{j: e_j <= c} log(1 - h_j)
p = P(solved by T) = 1 - S_K, and c = E[min(time, T)] = integral_0^T S(t) dt, with S linear inside each bin
(uniform event time within a bin): c = sum_k w_k (S_{k-1} + S_k) / 2.
"""
from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


def bin_edges(T: float, K: int = 8, first: float = 0.1) -> np.ndarray:
    return np.geomspace(first, T, K)


class MLPEnc(nn.Module):
    """Per-node MLP with the same block structure as the GNN, minus message passing (depth matched)."""

    def __init__(self, d_in, h, layers, dropout):
        super().__init__()
        self.inp = nn.Linear(d_in, h)
        self.blocks = nn.ModuleList([nn.Sequential(nn.Linear(h, h), nn.ReLU(), nn.Linear(h, h)) for _ in range(layers)])
        self.norms = nn.ModuleList([nn.LayerNorm(h) for _ in range(layers)])
        self.drop = nn.Dropout(dropout)

    def forward(self, x, edge_index=None, edge_attr=None):
        x = F.relu(self.inp(x))
        for blk, ln in zip(self.blocks, self.norms):
            x = ln(x + self.drop(F.relu(blk(x))))
        return x


class GNNEnc(nn.Module):
    def __init__(self, d_in, d_edge, h, layers, dropout):
        super().__init__()
        from torch_geometric.nn import GINEConv
        self.inp = nn.Linear(d_in, h)
        self.convs = nn.ModuleList([GINEConv(nn.Sequential(nn.Linear(h, h), nn.ReLU(), nn.Linear(h, h)), edge_dim=d_edge)
                                    for _ in range(layers)])
        self.norms = nn.ModuleList([nn.LayerNorm(h) for _ in range(layers)])
        self.drop = nn.Dropout(dropout)

    def forward(self, x, edge_index, edge_attr):
        x = F.relu(self.inp(x))
        for conv, ln in zip(self.convs, self.norms):
            x = ln(x + self.drop(F.relu(conv(x, edge_index, edge_attr))))
        return x


class Ranker3(nn.Module):
    def __init__(self, enc: str, d_in: int, d_edge: int, head: str, h: int = 64, layers: int = 2,
                 dropout: float = 0.1, K: int = 8, T: float = 30.0):
        super().__init__()
        self.enc_type, self.head_type, self.K, self.T = enc, head, K, T
        self.enc = MLPEnc(d_in, h, layers, dropout) if enc == "mlp" else GNNEnc(d_in, d_edge, h, layers, dropout)
        self.head = nn.Sequential(nn.Linear(h, h), nn.ReLU(), nn.Linear(h, 1 if head == "bce" else K))
        e = bin_edges(T, K)
        self.register_buffer("edges", torch.tensor(e, dtype=torch.float32))
        self.register_buffer("widths", torch.tensor(np.diff(np.concatenate([[0.0], e])), dtype=torch.float32))

    def forward(self, x, edge_index, edge_attr):
        return self.head(self.enc(x, edge_index, edge_attr))

    def loss(self, out, succ, cens_t):
        if self.head_type == "bce":
            return F.binary_cross_entropy_with_logits(out.squeeze(-1), succ.float())
        K = self.K
        b = torch.clamp(torch.searchsorted(self.edges, cens_t.contiguous(), right=False), max=K - 1)
        log_s = F.logsigmoid(-out)                 # log(1 - h)
        log_h = F.logsigmoid(out)                  # log h
        cum = torch.cumsum(log_s, 1)
        prev = torch.cat([torch.zeros_like(cum[:, :1]), cum[:, :-1]], 1)
        ev = -(prev.gather(1, b[:, None]).squeeze(1) + log_h.gather(1, b[:, None]).squeeze(1))
        n_surv = (self.edges[None, :] <= cens_t[:, None] + 1e-6).sum(1)   # bins fully survived
        cens = -torch.where(n_surv > 0, cum.gather(1, torch.clamp(n_surv - 1, min=0)[:, None]).squeeze(1),
                            torch.zeros_like(cum[:, 0]))
        return torch.where(succ, ev, cens).mean()

    @torch.no_grad()
    def predict(self, out):
        """-> p (P(success by T)), c (expected cost E[min(time,T)], survival head only else None)."""
        if self.head_type == "bce":
            return torch.sigmoid(out.squeeze(-1)), None
        h = torch.sigmoid(out)
        S = torch.cumprod(1 - h, 1)
        S_prev = torch.cat([torch.ones_like(S[:, :1]), S[:, :-1]], 1)
        p = 1 - S[:, -1]
        c = (self.widths[None, :] * (S_prev + S) / 2).sum(1)
        return p, c

    @torch.no_grad()
    def survival_curve(self, out):
        return torch.cumprod(1 - torch.sigmoid(out), 1)


def order_scores(p, c, rule: str):
    """Ordering score (higher first). rule: 'p' or 'p_over_c'."""
    if rule == "p":
        return p
    return p / torch.clamp(c, min=1e-3)


def first_success_cost(order, t, s) -> float:
    tot = 0.0
    for i in order:
        tot += float(t[i])
        if s[i]:
            return tot
    return tot


def replay_cost(score: np.ndarray, t: np.ndarray, s: np.ndarray, tie=None):
    """Cost to first success when querying in descending score (ties: lower index first, deterministic),
    and number of queries."""
    idx = np.lexsort((np.arange(len(score)) if tie is None else tie, -score))
    tot, n = 0.0, 0
    for i in idx:
        tot += float(t[i]); n += 1
        if s[i]:
            break
    return tot, n
