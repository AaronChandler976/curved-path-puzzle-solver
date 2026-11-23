#!/usr/bin/env python
"""S5: per-state replay on cached pilot queries.

Every remaining part was queried at every labelled state, so the planner time any ordering
spends before (and including) its first success at that state is computed exactly from the
logged query times. This is a replay of real logged runs, not a simulation.

cost(order, state) = sum of logged time_s of the queries in `order` up to and including the
first success. Failed/unsolved queries cost their logged time (about T). States with no
success are reported separately (every ordering pays the sum of all queries there).

Orderings: random (exact expectation, by enumerating all permutations for n <= 8, else 10,000
samples with a fixed seed), outside-in (distance of part centroid from the centre of the
current sub-assembly's bbox, farthest first; ASAP's heuristic), fewest-contacts-first (contacts
with parts still present; ties broken by outside-in), hindsight-optimal (cheapest success first;
an unattainable lower bound).
"""
import argparse
import itertools
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ORDERS = ["random", "outside_in", "fewest_contacts", "optimal"]


def first_success_cost(order, t, s):
    c = 0.0
    for p in order:
        c += t[p]
        if s[p]:
            return c
    return c


def random_expectation(parts, t, s, rng, n_samples=10000):
    n = len(parts)
    if n <= 8:
        tot = 0.0
        cnt = 0
        for perm in itertools.permutations(parts):
            tot += first_success_cost(perm, t, s)
            cnt += 1
        e = tot / cnt
        k = sum(s[p] for p in parts)
        if k:  # closed form check: failures cost t/(k+1) in expectation, successes t/k
            cf = sum(t[p] / (k + 1) for p in parts if not s[p]) + sum(t[p] / k for p in parts if s[p])
            assert abs(cf - e) < 1e-6 * max(1.0, e), (cf, e)
        return e, "enumerated"
    vals = [first_success_cost(list(rng.permutation(parts)), t, s) for _ in range(n_samples)]
    return float(np.mean(vals)), f"sampled_{n_samples}"


def boot_ci(x, stat, rng, B=10000):
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return (float("nan"),) * 3
    idx = rng.integers(0, len(x), (B, len(x)))
    bs = stat(x[idx], axis=1)
    return float(stat(x)), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def boot_ratio(num, den, rng, B=10000):
    num, den = np.asarray(num, float), np.asarray(den, float)
    idx = rng.integers(0, len(num), (B, len(num)))
    r = num[idx].sum(1) / den[idx].sum(1)
    return float(num.sum() / den.sum()), float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--labels", default=os.path.join(ROOT, "data/labels/pilot_v0/labels.jsonl"))
    ap.add_argument("--out-md", default=os.path.join(ROOT, "reports/replay_pilot_v0.md"))
    ap.add_argument("--out-json", default="", help="machine-readable per-state results (jsonl)")
    ap.add_argument("--fig-dir", default=os.path.join(ROOT, "reports/figures"))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--rot-deg", type=float, default=15.0)
    ap.add_argument("--with-prep", action="store_true",
                    help="add per-query prep (prep_s) and, if recorded, the amortised per-part setup (setup_time_s)")
    ap.add_argument("--title", default="pilot_v0")
    ap.add_argument("--fig-name", default="replay_pilot_v0")
    args = ap.parse_args()
    from disasm.oracle.cmgrrt import load_assembly, contact_graph, neighbors

    rng = np.random.default_rng(args.seed)
    labs = [json.loads(l) for l in open(args.labels)]
    states = defaultdict(list)
    for r in labs:
        states[(r["assembly_id"], r["state_key"])].append(r)
    asm_cache = {}
    rows = []
    rot_asm = defaultdict(bool)
    for (aid, skey), qs in sorted(states.items()):
        present = [int(x) for x in skey.split("-")]
        if sorted(q["part_id"] for q in qs) != sorted(present):
            continue  # incomplete state (should not happen: states are written whole)
        if aid not in asm_cache:
            asm_cache[aid] = load_assembly(os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly", aid))
        a = asm_cache[aid]
        t = {q["part_id"]: (q["time_s"] or 0.0) + (((q.get("prep_s") or 0.0) + (q.get("setup_time_s") or 0.0)
                                                    if q.get("detector") == "exact" else (q.get("prep_s") or 0.0))
                                                   if args.with_prep else 0.0) for q in qs}
        s = {q["part_id"]: q["outcome"] == "success" for q in qs}
        rot_state = False
        for q in qs:
            if q["outcome"] == "success" and (q.get("path_max_rot_deg") or 0) > args.rot_deg:
                rot_asm[aid] = True
                rot_state = True
        pres = set(present)
        b = np.array([a.meshes[p].bounds for p in present])
        center = (b[:, 0].min(0) + b[:, 1].max(0)) / 2
        dist = {p: float(np.linalg.norm(a.centroid(p) - center)) for p in present}
        ncont = {p: len(neighbors(a, p, pres)) for p in present}
        oi = sorted(present, key=lambda p: (-dist[p], p))
        fc = sorted(present, key=lambda p: (ncont[p], -dist[p], p))
        k = sum(s.values())
        row = {"assembly_id": aid, "state_key": skey, "n": len(present), "n_success": k,
               "total_s": sum(t.values()), "rot_state": rot_state}
        if k:
            row["random"], row["random_method"] = random_expectation(present, t, s, rng)
            row["outside_in"] = first_success_cost(oi, t, s)
            row["fewest_contacts"] = first_success_cost(fc, t, s)
            row["optimal"] = min(t[p] for p in present if s[p])
        rows.append(row)

    solved = [r for r in rows if r["n_success"] > 0]
    unsolved = [r for r in rows if r["n_success"] == 0]
    per_asm = defaultdict(lambda: defaultdict(float))
    for r in solved:
        for o in ORDERS:
            per_asm[r["assembly_id"]][o] += r[o]
    asm_ids = sorted(per_asm)

    L = []
    tag = "planner time + SDF prep" if args.with_prep else "planner time only (time_s); SDF prep excluded"
    L.append(f"# Per-state replay on cached pilot queries ({args.title})\n")
    L.append(f"Source labels: `{os.path.relpath(args.labels, ROOT)}` ({len(labs)} logged CMG-RRT queries). "
             f"Cost = {tag}. Bootstrap 95% CIs: 10,000 resamples, seed {args.seed}. "
             "This replays real logged queries; nothing is simulated. The trajectory through states is fixed by "
             "the labelling run, and each ordering only changes how much is spent finding the first success at each state.\n")
    L.append(f"- states with complete query sets: **{len(rows)}** ({len(solved)} with >= 1 success, {len(unsolved)} with none) "
             f"across **{len(set(r['assembly_id'] for r in rows))}** assemblies")
    if unsolved:
        L.append(f"- states with no success (every ordering pays everything): {len(unsolved)}, total "
                 f"{sum(r['total_s'] for r in unsolved):.0f} s, median {np.median([r['total_s'] for r in unsolved]):.0f} s/state")
    L.append("")
    if solved:
        L.append("## Per-state cost to first success (s), states with >= 1 success\n")
        L.append("| ordering | median [95% CI] | mean [95% CI] |\n|---|---|---|")
        for o in ORDERS:
            x = [r[o] for r in solved]
            m = boot_ci(x, np.median, rng)
            mu = boot_ci(x, np.mean, rng)
            name = o + (" (unattainable lower bound)" if o == "optimal" else "")
            L.append(f"| {name} | {m[0]:.2f} [{m[1]:.2f}, {m[2]:.2f}] | {mu[0]:.2f} [{mu[1]:.2f}, {mu[2]:.2f}] |")
        L.append("\n## Per-assembly cost (s): sum over the visited states with >= 1 success\n")
        L.append("| ordering | median [95% CI] | mean [95% CI] |\n|---|---|---|")
        for o in ORDERS:
            x = [per_asm[a][o] for a in asm_ids]
            m = boot_ci(x, np.median, rng)
            mu = boot_ci(x, np.mean, rng)
            L.append(f"| {o} | {m[0]:.2f} [{m[1]:.2f}, {m[2]:.2f}] | {mu[0]:.2f} [{mu[1]:.2f}, {mu[2]:.2f}] |")
        L.append("\n## Headroom (cost of ordering divided by hindsight-optimal)\n")
        L.append("Ratio of totals over states, with a bootstrap CI over states. Also the median of per-state ratios.\n")
        L.append("| ordering | ratio of totals [95% CI] | median per-state ratio |\n|---|---|---|")
        for o in ["random", "outside_in", "fewest_contacts"]:
            rr = boot_ratio([r[o] for r in solved], [r["optimal"] for r in solved], rng)
            med = float(np.median([r[o] / max(r["optimal"], 1e-9) for r in solved]))
            L.append(f"| {o} / optimal | {rr[0]:.2f} [{rr[1]:.2f}, {rr[2]:.2f}] | {med:.2f} |")
        L.append(f"\n## Rotation split (assembly has a successful logged path with max rotation > {args.rot_deg:.0f} deg)\n")
        L.append("Caveat: an RRT path can rotate even when a pure translation would work, so this measures rotation "
                 "*in the logged path*, not rotation that was *needed*.\n")
        L.append("| group | assemblies | states | random/optimal (ratio of totals) [95% CI] |\n|---|---|---|---|")
        for g, sel in (("rotation > thr", True), ("translation-like", False)):
            ss = [r for r in solved if rot_asm[r["assembly_id"]] == sel]
            if ss:
                rr = boot_ratio([r["random"] for r in ss], [r["optimal"] for r in ss], rng)
                L.append(f"| {g} | {len(set(r['assembly_id'] for r in ss))} | {len(ss)} | {rr[0]:.2f} [{rr[1]:.2f}, {rr[2]:.2f}] |")
            else:
                L.append(f"| {g} | 0 | 0 | n/a |")
        rs = [r for r in solved if r["rot_state"]]
        L.append(f"\n**State-level rotation subset** (a successful query at the state has max path rotation > "
                 f"{args.rot_deg:.0f} deg): {len(rs)} states in {len(set(r['assembly_id'] for r in rs))} assemblies.")
        if len(rs) >= 20:
            L.append("\n| ordering / optimal (rotation states) | ratio of totals [95% CI] | median per-state ratio |\n|---|---|---|")
            for o in ["random", "outside_in", "fewest_contacts"]:
                rr = boot_ratio([r[o] for r in rs], [r["optimal"] for r in rs], rng)
                med = float(np.median([r[o] / max(r["optimal"], 1e-9) for r in rs]))
                L.append(f"| {o} | {rr[0]:.2f} [{rr[1]:.2f}, {rr[2]:.2f}] | {med:.2f} |")
        else:
            L.append(" Too small for a separate replay (n < 20 states).")
        # plots
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            os.makedirs(args.fig_dir, exist_ok=True)
            fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
            for o, c in zip(ORDERS, ["#4C72B0", "#DD8452", "#55A868", "#555555"]):
                x = np.sort([max(r[o], 1e-2) for r in solved])
                ax[0].plot(x, np.arange(1, len(x) + 1) / len(x), label=o, color=c, ls="--" if o == "optimal" else "-")
            ax[0].set_xscale("log"); ax[0].set_xlabel("planner seconds to first success (per state)")
            ax[0].set_ylabel("fraction of states"); ax[0].legend(frameon=False, fontsize=8)
            ax[0].set_title("Per-state cost CDF (replay)")
            ratios = [r["random"] / max(r["optimal"], 1e-9) for r in solved]
            ax[1].hist(np.log10(np.maximum(ratios, 1)), bins=30, color="#4C72B0")
            ax[1].set_xlabel("log10(random / optimal)"); ax[1].set_ylabel("states")
            ax[1].set_title("Headroom per state")
            for a_ in ax:
                a_.spines[["top", "right"]].set_visible(False)
            fig.tight_layout()
            fp = os.path.join(args.fig_dir, args.fig_name + ("_prep" if args.with_prep else "") + ".png")
            fig.savefig(fp, dpi=130)
            L.append(f"\n![replay]({os.path.relpath(fp, os.path.dirname(args.out_md))})")
        except Exception as e:  # noqa: BLE001
            L.append(f"\n(plot failed: {e})")
    os.makedirs(os.path.dirname(args.out_md), exist_ok=True)
    open(args.out_md, "w").write("\n".join(L) + "\n")
    if args.out_json:
        with open(args.out_json, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
