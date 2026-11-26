#!/usr/bin/env python
"""R2 (run 03): one graph per labelled pilot_v1 state + duplicate grouping + frozen group split.

Outputs
- data/processed/run03/graphs.pt : list of dicts (one per state with a complete query set):
    aid, skey, depth, n_parts, present, x (n,18), ei (2,E), ea (E,5), succ (n,), time_s (n,) logged time,
    cens_t (n,) = min(time_s, T) (unsolved = censored at its logged time, i.e. ~T), queried (n,) mask,
    T, and EVAL-ONLY fields (never model inputs): linear_free (n,), needs_rot (n,), rot_state.
- data/processed/run03/asm_meta.json : per-assembly signatures, group id, n_parts, rot_assembly.
- data/splits/v1_split.json : frozen split {train, val, test: [assembly ids]}, groups, seed, strata.
- reports/run03/dataset.md : split sizes + rotation counts.

Duplicate groups: union-find over (a) exact key = sorted per-part mesh hashes (vertices rounded to 1e-5 in the
unit frame + faces) and (b) near key = sorted per-part (log volume rounded to 0.05, sorted bbox extents rounded
to 0.01). Split: groups are stratified by (part-count bin of the group's largest assembly, any rot_assembly in
the group), shuffled with --seed, and dealt 70/15/15 within each stratum.
"""
import argparse
import hashlib
import json
import multiprocessing as mp
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly")


def part_count_bin(n):
    return "3-4" if n <= 4 else ("5-6" if n <= 6 else "7-8")


def _build_one(args):
    aid, states = args
    import torch
    from disasm.oracle.cmgrrt import load_assembly
    from disasm.data.graph import state_graph_v3
    asm = load_assembly(os.path.join(RAW, aid))
    exact, near = [], []
    for p in asm.part_ids:
        m = asm.meshes[p]
        h = hashlib.sha1(np.round(np.asarray(m.vertices), 5).tobytes() + np.asarray(m.faces).tobytes()).hexdigest()
        exact.append(h)
        ext = np.sort(m.bounds[1] - m.bounds[0])
        near.append((round(round(np.log(max(abs(m.volume), 1e-12)) / 0.05) * 0.05, 2),
                     *[round(float(e), 2) for e in ext]))
    meta = {"aid": aid, "n_parts": len(asm.part_ids), "exact_key": "|".join(sorted(exact)),
            "near_key": json.dumps(sorted(near))}
    graphs = []
    for skey, qs in states:
        present = [int(x) for x in skey.split("-")]
        by = {q["part_id"]: q for q in qs}
        if sorted(by) != sorted(present):
            continue
        pres, X, ei, ea = state_graph_v3(asm, present)
        T = float(qs[0]["T"])
        succ = np.array([by[p]["outcome"] == "success" for p in pres])
        t = np.array([float(by[p]["time_s"] or 0.0) for p in pres], dtype=np.float32)
        lf = np.array([bool(by[p].get("_linear_free")) for p in pres])
        needs = succ & ~lf
        graphs.append({"aid": aid, "skey": skey, "depth": int(qs[0]["depth"]), "n_parts": len(asm.part_ids),
                       "present": pres, "x": torch.tensor(X), "ei": torch.tensor(ei), "ea": torch.tensor(ea),
                       "succ": torch.tensor(succ), "time_s": torch.tensor(t),
                       "cens_t": torch.tensor(np.minimum(t, T)), "queried": torch.ones(len(pres), dtype=torch.bool),
                       "T": T, "linear_free": torch.tensor(lf), "needs_rot": torch.tensor(needs),
                       "rot_state": bool(needs.any())})
    return meta, graphs


class UF:
    def __init__(self):
        self.p = {}

    def f(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def u(self, a, b):
        self.p[self.f(a)] = self.f(b)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--labels", default=os.path.join(ROOT, "data/labels/pilot_v1/labels.jsonl"))
    ap.add_argument("--precheck", default=os.path.join(ROOT, "data/labels/pilot_v1/precheck.jsonl"))
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "data/processed/run03"))
    ap.add_argument("--split-out", default=os.path.join(ROOT, "data/splits/v1_split.json"))
    ap.add_argument("--report", default=os.path.join(ROOT, "reports/run03/dataset.md"))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--procs", type=int, default=8)
    args = ap.parse_args()
    import torch
    pc = {}
    for l in open(args.precheck):
        r = json.loads(l)
        if r.get("error"):
            raise SystemExit(f"precheck error row: {r['assembly_id']} {r['state_key']} {r['part_id']}: {r['error']}")
        pc[(r["assembly_id"], r["state_key"], r["part_id"])] = r["linear_free"]
    states = defaultdict(lambda: defaultdict(list))
    n_lab = 0
    for l in open(args.labels):
        r = json.loads(l)
        n_lab += 1
        k = (r["assembly_id"], r["state_key"], r["part_id"])
        if k not in pc:
            raise SystemExit(f"missing precheck for {k}")
        r["_linear_free"] = pc[k]
        states[r["assembly_id"]][r["state_key"]].append(r)
    jobs = [(aid, sorted(st.items())) for aid, st in sorted(states.items())]
    with mp.get_context("spawn").Pool(args.procs) as pool:
        res = pool.map(_build_one, jobs, chunksize=4)
    metas = {m["aid"]: m for m, _ in res}
    graphs = [g for _, gs in res for g in gs]
    rot_asm = defaultdict(bool)
    for g in graphs:
        rot_asm[g["aid"]] |= g["rot_state"]
    # ---- duplicate groups
    uf = UF()
    for key in ("exact_key", "near_key"):
        first = {}
        for aid, m in sorted(metas.items()):
            uf.f(aid)
            if m[key] in first:
                uf.u(aid, first[m[key]])
            else:
                first[m[key]] = aid
    groups = defaultdict(list)
    for aid in sorted(metas):
        groups[uf.f(aid)].append(aid)
    gid = {}
    for i, (_, mem) in enumerate(sorted(groups.items(), key=lambda kv: kv[1][0])):
        for a in mem:
            gid[a] = i
    glist = defaultdict(list)
    for a, i in gid.items():
        glist[i].append(a)
    n_exact_dup = len(metas) - len({m["exact_key"] for m in metas.values()})
    n_near_dup = len(metas) - len({m["near_key"] for m in metas.values()})
    # ---- stratified group split
    strata = defaultdict(list)
    for i, mem in sorted(glist.items()):
        s = (part_count_bin(max(metas[a]["n_parts"] for a in mem)), any(rot_asm[a] for a in mem))
        strata[s].append(i)
    rng = np.random.default_rng(args.seed)
    split = {"train": [], "val": [], "test": []}
    for s in sorted(strata):
        gs = list(strata[s])
        rng.shuffle(gs)
        n = len(gs)
        n_val, n_test = int(round(0.15 * n)), int(round(0.15 * n))
        parts = {"test": gs[:n_test], "val": gs[n_test:n_test + n_val], "train": gs[n_test + n_val:]}
        for k, v in parts.items():
            for i in v:
                split[k] += glist[i]
    for k in split:
        split[k] = sorted(split[k])
    assert not (set(split["train"]) & set(split["val"])) and not (set(split["train"]) & set(split["test"])) \
        and not (set(split["val"]) & set(split["test"]))
    os.makedirs(args.out_dir, exist_ok=True)
    os.makedirs(os.path.dirname(args.split_out), exist_ok=True)
    json.dump({"seed": args.seed, "fractions": [0.7, 0.15, 0.15],
               "stratify": "group part-count bin (3-4/5-6/7-8, largest member) x any rot_assembly in group",
               "dedup": "union-find over exact part-mesh-hash key and near (log-volume 0.05, bbox 0.01) key",
               "n_groups": len(glist), "groups": {str(i): mem for i, mem in sorted(glist.items())},
               **split}, open(args.split_out, "w"), indent=0)
    for a in metas:
        metas[a].update({"group": gid[a], "rot_assembly": bool(rot_asm[a])})
    json.dump(metas, open(os.path.join(args.out_dir, "asm_meta.json"), "w"))
    torch.save(graphs, os.path.join(args.out_dir, "graphs.pt"))
    # ---- report
    which = {a: k for k, v in split.items() for a in v}
    L = ["# Run 03 dataset (R2)\n",
         f"Built by `scripts/build_dataset_v1.py` (seed {args.seed}) from `{os.path.relpath(args.labels, ROOT)}` "
         f"({n_lab} queries) and `{os.path.relpath(args.precheck, ROOT)}`. Graphs: `data/processed/run03/graphs.pt`; "
         f"split: `data/splits/v1_split.json`.\n",
         f"- states with a complete query set: **{len(graphs)}** over **{len(metas)}** assemblies; "
         f"states with >= 1 success: {sum(1 for g in graphs if g['succ'].any())}",
         f"- duplicate groups: {len(glist)} groups for {len(metas)} assemblies "
         f"({sum(1 for v in glist.values() if len(v) > 1)} groups with > 1 member, largest {max(len(v) for v in glist.values())}); "
         f"assemblies sharing an exact part-mesh key with an earlier one: {n_exact_dup}; sharing a near key: {n_near_dup}",
         "- node features (18, model inputs): log volume, area, bbox extents (3), centroid relative to the sub-assembly "
         "bbox centre (3) and its norm, # present contact neighbours, total contact fraction, 6-bin contact-normal "
         "histogram, n_present. Edge features (5): mean away direction (3), contact fraction, contact area.",
         "- `queried` flag: stored per node as a target mask. It is 1 for every node in v1 (every remaining part was "
         "queried), so it is not used as a model input (a constant input carries no information).",
         "- rotation flags (`linear_free`, `needs_rot`, `rot_state`, `rot_assembly`) are evaluation-only fields and are "
         "never model inputs.\n",
         "| split | groups | assemblies | states | states >= 1 success | queries | rot_assembly | rot_state states | 3-4 / 5-6 / 7-8 part asm |",
         "|---|---|---|---|---|---|---|---|---|"]
    for k in ("train", "val", "test"):
        A = set(split[k])
        G = [g for g in graphs if g["aid"] in A]
        bins = defaultdict(int)
        for a in A:
            bins[part_count_bin(metas[a]["n_parts"])] += 1
        L.append(f"| {k} | {len({gid[a] for a in A})} | {len(A)} | {len(G)} | {sum(1 for g in G if g['succ'].any())} | "
                 f"{sum(len(g['present']) for g in G)} | {sum(rot_asm[a] for a in A)} | {sum(g['rot_state'] for g in G)} | "
                 f"{bins['3-4']} / {bins['5-6']} / {bins['7-8']} |")
    L.append(f"\nGroup-disjointness is asserted in the builder and in `tests/test_split.py`.")
    open(args.report, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
