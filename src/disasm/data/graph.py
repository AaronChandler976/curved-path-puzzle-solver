"""Contact graph + per-part features for one labelled state (present parts only).

Node features (per present part, unit frame): log volume, surface area, bbox extents (3), centroid
relative to the sub-assembly bbox centre (3) and its norm (outside-in distance), number of present
contact neighbours, total contact fraction, a 6-bin contact-normal histogram (dominant signed axis of
each neighbour's mean "away" direction, weighted by contact count), and n_present (global).
Edge features (directed p->q for every contact pair among present parts): mean away direction of p
from q (3), contact fraction.
"""
from __future__ import annotations

import numpy as np

NODE_DIM = 18
EDGE_DIM = 4


def state_graph(asm, present: list):
    from disasm.oracle.cmgrrt import contact_graph
    pairs = contact_graph(asm)["pairs"]
    present = sorted(present)
    idx = {p: i for i, p in enumerate(present)}
    b = np.array([asm.meshes[p].bounds for p in present])
    center = (b[:, 0].min(0) + b[:, 1].max(0)) / 2
    X = np.zeros((len(present), NODE_DIM), dtype=np.float32)
    src, dst, E = [], [], []
    for p in present:
        m = asm.meshes[p]
        rel = np.asarray(m.centroid) - center
        hist = np.zeros(6)
        ncont, frac = 0, 0.0
        for q in present:
            e = pairs.get(f"{p}-{q}")
            if q == p or e is None:
                continue
            ncont += 1
            frac += e["frac"]
            v = np.asarray(e["away"])
            ax = int(np.argmax(np.abs(v)))
            hist[2 * ax + (0 if v[ax] >= 0 else 1)] += e["n"]
            src.append(idx[p]); dst.append(idx[q])
            E.append(list(v) + [e["frac"]])
        if hist.sum() > 0:
            hist /= hist.sum()
        ext = m.bounds[1] - m.bounds[0]
        X[idx[p]] = [np.log(max(abs(m.volume), 1e-9)), m.area, *ext, *rel, np.linalg.norm(rel), ncont, frac,
                     *hist, len(present)]
    ei = np.array([src, dst], dtype=np.int64).reshape(2, -1)
    ea = np.array(E, dtype=np.float32).reshape(-1, EDGE_DIM)
    return present, X, ei, ea


# ----------------------------------------------------------------------------- run 03 (R2) graph
EDGE_DIM_V3 = 5


def state_graph_v3(asm, present: list):
    """run 03 dataset graph: node features = state_graph's 18 (unchanged), edge features = state_graph's 4
    (mean away direction of p from q (3), contact fraction of p's surface samples) + contact area
    (fraction x surface area of p, unit frame). Directed p->q for every contact pair among present parts."""
    from disasm.oracle.cmgrrt import contact_graph
    pairs = contact_graph(asm)["pairs"]
    present, X, ei, ea = state_graph(asm, present)
    area = []
    for s, d in zip(ei[0], ei[1]):
        p, q = present[int(s)], present[int(d)]
        area.append(pairs[f"{p}-{q}"]["frac"] * float(asm.meshes[p].area))
    ea = np.concatenate([ea, np.array(area, dtype=np.float32).reshape(-1, 1)], 1)
    return present, X, ei, ea
