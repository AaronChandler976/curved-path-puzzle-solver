"""Run 03 per-state replay of orderings on logged v1 queries (same cost model as scripts/replay_pilot.py).

cost(order, state) = sum of logged time_s of queries in `order` up to and including the first success.
Only states with >= 1 success are scored; others are reported separately (every ordering pays everything).
Heuristics are computed from the state graph's node features (data/graph.py column layout):
  col 8 = distance of the part centroid from the sub-assembly bbox centre (outside-in: farthest first),
  col 9 = number of present contact neighbours (fewest contacts first; ties by outside-in, then part id).
Random = exact expectation (closed form: each failure costs t/(k+1), each success t/k, k = #successes).
"""
from __future__ import annotations

import numpy as np

COL_DIST, COL_NCONT = 8, 9


def cost_of_order(order, t, s):
    tot, n = 0.0, 0
    for i in order:
        tot += float(t[i]); n += 1
        if s[i]:
            return tot, n
    return tot, n


def random_expectation(t, s):
    k = int(s.sum())
    cost = float(sum(t[i] / (k + 1) for i in range(len(t)) if not s[i]) + sum(t[i] / k for i in range(len(t)) if s[i]))
    nq = (len(t) + 1) / (k + 1)          # expected number of queries to the first success
    return cost, nq


def heuristic_orders(g):
    x = g["x"].numpy()
    n = x.shape[0]
    dist, ncont = x[:, COL_DIST], x[:, COL_NCONT]
    oi = sorted(range(n), key=lambda i: (-dist[i], g["present"][i]))
    fc = sorted(range(n), key=lambda i: (ncont[i], -dist[i], g["present"][i]))
    return {"outside_in": oi, "fewest_contacts": fc}


def score_order(score):
    """Descending score; ties broken by node index (= ascending part id), deterministic."""
    score = np.asarray(score, dtype=float)
    return list(np.lexsort((np.arange(len(score)), -score)))


def state_row(g, model_scores: dict):
    """model_scores: name -> per-node score array (higher = query first). Returns dict of costs/queries."""
    t, s = g["time_s"].numpy().astype(float), g["succ"].numpy().astype(bool)
    row = {"assembly_id": g["aid"], "state_key": g["skey"], "n": len(t), "n_success": int(s.sum()),
           "rot_state": bool(g["rot_state"]), "total_s": float(t.sum())}
    if not s.any():
        return row
    row["random"], row["random_q"] = random_expectation(t, s)
    for k, o in heuristic_orders(g).items():
        row[k], row[k + "_q"] = cost_of_order(o, t, s)
    row["optimal"] = float(min(t[i] for i in range(len(t)) if s[i]))
    row["optimal_q"] = 1
    for name, sc in model_scores.items():
        row[name], row[name + "_q"] = cost_of_order(score_order(sc), t, s)
    return row
