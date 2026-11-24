"""Statistics for run 05 (docs/PREREG_run05.md §4-§5): bootstrap by assembly, Hodges-Lehmann, Wilcoxon, Holm,
C-index, ECE. Pure numpy/scipy; unit-tested in tests/test_stats.py."""
from __future__ import annotations

import numpy as np

TIE_S = 0.01      # |d| <= 0.01 s per assembly counts as a tie (PREREG §4)


def holm(pvals):
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    run, m = 0.0, len(p)
    for k, i in enumerate(order):
        run = max(run, min(1.0, (m - k) * p[i]))
        adj[i] = run
    return adj


def hodges_lehmann(d):
    """One-sample HL estimator of the location of paired differences: median of the Walsh averages (d_i + d_j)/2, i <= j."""
    d = np.asarray(d, float)
    i, j = np.triu_indices(len(d))
    return float(np.median((d[i] + d[j]) / 2.0))


def wilcoxon_p(a, b):
    from scipy.stats import wilcoxon
    d = np.asarray(a, float) - np.asarray(b, float)
    if not np.any(np.abs(d) > 0):
        return 1.0
    try:
        return float(wilcoxon(a, b, zero_method="wilcox", alternative="two-sided").pvalue)
    except ValueError:
        return 1.0


def boot_idx(n, B=10000, seed=0):
    return np.random.default_rng(seed).integers(0, n, (B, n))


def paired(a, b, B=10000, seed=0, hl_boot=True):
    """a, b: per-assembly costs (same assemblies). Ratio of totals a/b and HL(a - b) with bootstrap CIs over
    assemblies, wins/ties/losses for a (win = a cheaper by more than TIE_S), two-sided Wilcoxon p."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = a - b
    idx = boot_idx(len(a), B, seed)
    br = a[idx].sum(1) / np.maximum(b[idx].sum(1), 1e-12)
    out = {"n": int(len(a)), "total_a": float(a.sum()), "total_b": float(b.sum()),
           "ratio": float(a.sum() / max(b.sum(), 1e-12)),
           "ratio_ci": [float(np.percentile(br, 2.5)), float(np.percentile(br, 97.5))],
           "hl": hodges_lehmann(d), "wins": int((d < -TIE_S).sum()), "ties": int((np.abs(d) <= TIE_S).sum()),
           "losses": int((d > TIE_S).sum()), "p": wilcoxon_p(a, b)}
    if hl_boot:
        # HL on a bootstrap sample of n assemblies costs O(n^2); 2,000 resamples keep it fast and stable
        bh = np.array([hodges_lehmann(d[ix]) for ix in idx[:2000]])
        out["hl_ci"] = [float(np.percentile(bh, 2.5)), float(np.percentile(bh, 97.5))]
        out["hl_boot_B"] = 2000
    return out


def boot_stat_by_asm(per_asm_vals, stat, B=10000, seed=0):
    """per_asm_vals: list (per assembly) of arrays of per-state values -> (stat over pooled states, CI lo, hi)."""
    A = len(per_asm_vals)
    idx = boot_idx(A, B, seed)
    lens = np.array([len(v) for v in per_asm_vals])
    flat = np.concatenate(per_asm_vals) if A else np.zeros(0)
    starts = np.concatenate([[0], np.cumsum(lens)[:-1]]) if A else np.zeros(0, int)
    if stat is np.sum:          # fast path
        sums = np.array([v.sum() for v in per_asm_vals])
        bs = sums[idx].sum(1)
        return float(flat.sum()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
    out = np.empty(B)
    for k in range(B):
        out[k] = stat(np.concatenate([flat[starts[i]:starts[i] + lens[i]] for i in idx[k]]))
    return float(stat(flat)), float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def cindex(pred_speed, t, event, groups=None):
    """Harrell's C for time-to-success with right censoring. pred_speed: higher = predicted sooner success.
    Comparable pair (i, j): event_i and t_i < t_j. Concordant if speed_i > speed_j (ties 0.5).
    groups: if given, only pairs within the same group (state)."""
    pred_speed, t, event = map(np.asarray, (pred_speed, t, event))
    event = event.astype(bool)
    num = den = 0.0
    ug = [np.arange(len(t))] if groups is None else [np.where(np.asarray(groups) == k)[0] for k in np.unique(groups)]
    for ix in ug:
        s, tt, e = pred_speed[ix], t[ix], event[ix]
        comp = e[:, None] & (tt[:, None] < tt[None, :])
        if not comp.any():
            continue
        dd = s[:, None] - s[None, :]
        num += ((dd > 0) * comp).sum() + 0.5 * ((dd == 0) * comp).sum()
        den += comp.sum()
    return (float(num / den) if den else float("nan")), int(den)


def ece(p, y, bins=10):
    p, y = np.asarray(p, float), np.asarray(y, float)
    edges = np.linspace(0, 1, bins + 1)
    e, rows = 0.0, []
    for i in range(bins):
        m = (p >= edges[i]) & ((p < edges[i + 1]) if i < bins - 1 else (p <= 1))
        if m.any():
            e += m.mean() * abs(p[m].mean() - y[m].mean())
            rows.append((float(p[m].mean()), float(y[m].mean()), int(m.sum())))
    return float(e), rows
