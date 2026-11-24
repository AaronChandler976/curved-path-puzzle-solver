#!/usr/bin/env python
"""Run 04 T8: frozen v2 split -> data/splits/v2_split.json.

Pool = every assembly with a finished pilot_v2 label (summary status complete or stuck).
Duplicate groups exactly as run 03 (reports/run03/DECISIONS.md #6): union-find over (a) the sorted per-part mesh hash
(vertices rounded to 1e-5 in the unit frame + faces) and (b) the sorted per-part (log volume to 0.05, sorted bbox
extents to 0.01), computed across the WHOLE v2 pool.
- A group with any pilot_v1 member (source v1) is never in test. 00014 is never in test.
- Test = about half of the fresh-only groups, stratified by (source of the group's largest member, part-count bin
  of that member), dealt with --seed: in each stratum round(0.5 * n) groups go to test.
- Everything else (the other fresh-only groups + every group with a v1 member) goes to train/val, 85/15 by group,
  stratified by (has v1 member, source, part-count bin).
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
NEVER_TEST = {"00014"}


def part_count_bin(n):
    return "3-4" if n <= 4 else "5-6" if n <= 6 else "7-8" if n <= 8 else "9-10" if n <= 10 else "11-12"


def keys(aid):
    from disasm.oracle.cmgrrt import load_assembly
    asm = load_assembly(os.path.join(RAW, aid))
    exact, near = [], []
    for p in asm.part_ids:
        m = asm.meshes[p]
        exact.append(hashlib.sha1(np.round(np.asarray(m.vertices), 5).tobytes() + np.asarray(m.faces).tobytes()).hexdigest())
        ext = np.sort(m.bounds[1] - m.bounds[0])
        near.append((round(round(np.log(max(abs(m.volume), 1e-12)) / 0.05) * 0.05, 2), *[round(float(e), 2) for e in ext]))
    return aid, len(asm.part_ids), "|".join(sorted(exact)), json.dumps(sorted(near))


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


def make_split(meta: dict, seed: int = 0, test_frac: float = 0.5, val_frac: float = 0.15) -> dict:
    """meta: aid -> {n_parts, source, exact_key, near_key}. Pure function (unit-tested)."""
    uf = UF()
    for key in ("exact_key", "near_key"):
        first = {}
        for aid in sorted(meta):
            uf.f(aid)
            k = meta[aid][key]
            if k in first:
                uf.u(aid, first[k])
            else:
                first[k] = aid
    groups = defaultdict(list)
    for aid in sorted(meta):
        groups[uf.f(aid)].append(aid)
    glist = [sorted(m) for _, m in sorted(groups.items(), key=lambda kv: sorted(kv[1])[0])]
    rng = np.random.default_rng(seed)

    def stratum(mem):
        big = max(mem, key=lambda a: (meta[a]["n_parts"], a))
        return meta[big]["source"], part_count_bin(meta[big]["n_parts"])

    fresh_only = [i for i, m in enumerate(glist) if all(meta[a]["source"] != "v1" for a in m) and not (set(m) & NEVER_TEST)]
    st = defaultdict(list)
    for i in fresh_only:
        st[stratum(glist[i])].append(i)
    test_g = set()
    for s in sorted(st):
        gs = list(st[s])
        rng.shuffle(gs)
        test_g |= set(gs[:int(round(test_frac * len(gs)))])
    rest = [i for i in range(len(glist)) if i not in test_g]
    st2 = defaultdict(list)
    for i in rest:
        st2[(any(meta[a]["source"] == "v1" for a in glist[i]),) + stratum(glist[i])].append(i)
    val_g = set()
    for s in sorted(st2):
        gs = list(st2[s])
        rng.shuffle(gs)
        val_g |= set(gs[:int(round(val_frac * len(gs)))])
    split = {"train": [], "val": [], "test": []}
    for i, m in enumerate(glist):
        k = "test" if i in test_g else "val" if i in val_g else "train"
        split[k] += m
    for k in split:
        split[k] = sorted(split[k])
    return {"groups": {str(i): m for i, m in enumerate(glist)}, "n_groups": len(glist), **split}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--labels-dir", default=os.path.join(ROOT, "data/labels/pilot_v2"))
    ap.add_argument("--source-file", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "data/splits/v2_split.json"))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--procs", type=int, default=10)
    a = ap.parse_args()
    src = json.load(open(a.source_file))
    summ = {}
    for l in open(os.path.join(a.labels_dir, "summary.jsonl")):
        s = json.loads(l)
        summ[s["assembly_id"]] = s
    pool = sorted(k for k, s in summ.items() if s["status"] in ("complete", "stuck"))
    with mp.get_context("spawn").Pool(a.procs) as p:
        ks = p.map(keys, pool, chunksize=8)
    meta = {aid: {"n_parts": n, "source": src.get(aid, "v1"), "exact_key": e, "near_key": nk} for aid, n, e, nk in ks}
    sp = make_split(meta, a.seed)
    v1_ids = set(json.load(open(os.path.join(ROOT, "data/splits/v1_split.json")))["train"]) | \
        set(json.load(open(os.path.join(ROOT, "data/splits/v1_split.json")))["val"]) | \
        set(json.load(open(os.path.join(ROOT, "data/splits/v1_split.json")))["test"])
    assert not (set(sp["test"]) & v1_ids) and "00014" not in sp["test"]
    out = {"seed": a.seed, "test": sp["test"], "val": sp["val"], "train": sp["train"],
           "rule": "test = ~half of fresh-only duplicate groups, stratified by (source, part-count bin); rest 85/15 train/val",
           "dedup": "union-find over exact part-mesh-hash key and near (log-volume 0.05, bbox 0.01) key (run 03 #6)",
           "n_groups": sp["n_groups"], "groups": sp["groups"],
           "sources": {k: meta[k]["source"] for k in sorted(meta)}, "n_parts": {k: meta[k]["n_parts"] for k in sorted(meta)},
           "excluded_not_labelled": sorted(set(src) - set(pool))}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=0)
    for k in ("train", "val", "test"):
        print(k, len(out[k]), {s: sum(meta[x]["source"] == s for x in out[k]) for s in ("v1", "fresh-9to12", "fresh-allowance")})


if __name__ == "__main__":
    main()
