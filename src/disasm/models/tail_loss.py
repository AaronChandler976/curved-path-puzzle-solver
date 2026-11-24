"""Tail-aware objective for run 05 (pre-registered in docs/PREREG_run05.md; implemented and unit-tested in run 04).

Motivation (run 03): replay totals are dominated by the tail. The 5% most expensive states are 51-65% of the time,
and those are states where unsolved queries (each costing about T) are tried before the first success. The run 03
survival NLL is per node, so it does not weight those states by what they cost.

Definition. For one state with n present parts, model scores s_i = log p_i - log c_i (the p/c ordering key;
p, c from the survival head, ranker3.Ranker3.predict without no_grad), observed outcomes y_i in {0, 1} (success)
and observed query costs t_i (logged planner time; for unsolved queries, the logged time, which is about T).
The replay cost of ordering by s is  C(s) = sum_k t_(k) * prod_{j<k} (1 - y_(j))  (query in order until the first
success). C is piecewise constant in s, so we use the NeuralSort relaxation (Grover et al., ICLR 2019):
    P_hat[k, :] = softmax( ((n + 1 - 2k) * s - A_s 1) / tau ),   A_s[i, j] = |s_i - s_j|,   k = 1..n,
a row-stochastic "soft permutation" (row k = soft position k). Soft sorted outcomes y~ = P_hat y, costs t~ = P_hat t, and
    C_soft(s) = sum_k t~_k * prod_{j<k} (1 - y~_j).
As tau -> 0, P_hat tends to the hard sort and C_soft to C. A state with no success has a constant cost (all parts are
queried), so it is excluded from this term.
Objective:  L = L_surv + lambda * mean over states with >= 1 success of C_soft(s) / T.
Fixed in the pre-registration: tau = 0.1 and lambda in {0.1, 1.0} (part of the shared tuning grid). Gradients reach
s through P_hat and from there both p and c, so the term pushes cheap-and-likely parts ahead of the parts that
time out.
"""
from __future__ import annotations

import torch


def neuralsort(s: torch.Tensor, tau: float) -> torch.Tensor:
    """s: (n,) scores -> (n, n) soft permutation matrix sorting s in DESCENDING order (Grover et al. 2019, eq. 4)."""
    n = s.shape[0]
    s = s.reshape(n, 1)
    A = (s - s.T).abs()
    B = A.sum(1, keepdim=True)                          # A_s 1
    k = torch.arange(1, n + 1, device=s.device, dtype=s.dtype).reshape(n, 1)
    C = (n + 1 - 2 * k) * s.T                            # (n, n): row k, column i -> (n+1-2k) s_i
    return torch.softmax((C - B.T) / tau, dim=1)


def soft_replay_cost(s: torch.Tensor, y: torch.Tensor, t: torch.Tensor, tau: float = 0.1) -> torch.Tensor:
    P = neuralsort(s, tau)
    ys, ts = P @ y.float(), P @ t.float()
    surv = torch.cumprod(torch.cat([torch.ones(1, device=s.device, dtype=ys.dtype), 1 - ys[:-1]]), 0)
    return (ts * surv).sum()


def hard_replay_cost(s, y, t) -> float:
    o = torch.argsort(s, descending=True)
    c = 0.0
    for i in o.tolist():
        c += float(t[i])
        if y[i]:
            break
    return c


def tail_term(score: torch.Tensor, succ: torch.Tensor, cost: torch.Tensor, batch: torch.Tensor, T: float,
              tau: float = 0.1) -> torch.Tensor:
    """Mean over states (graph ids in `batch`) with >= 1 success of soft_replay_cost / T."""
    vals = []
    for g in torch.unique(batch):
        m = batch == g
        if succ[m].any():
            vals.append(soft_replay_cost(score[m], succ[m], cost[m], tau) / T)
    return torch.stack(vals).mean() if vals else score.sum() * 0.0
