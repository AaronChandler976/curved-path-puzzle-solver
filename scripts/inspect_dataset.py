#!/usr/bin/env python
"""Inspect an Assemble-Them-All style dataset: one folder per assembly, <k>.obj per part.

Counts assemblies, prints the part-count histogram, and loads every mesh with trimesh
(reports load failures, empty meshes, watertightness, and per-assembly bounding boxes).
Writes one JSON line per assembly to --out, and a summary JSON to --summary.
"""
import argparse
import collections
import glob
import json
import os
from multiprocessing import Pool

import numpy as np
import trimesh


def inspect_one(adir):
    rec = {"id": os.path.basename(adir), "dir": adir, "parts": [], "ok": True, "errors": []}
    objs = sorted(glob.glob(os.path.join(adir, "*.obj")), key=lambda p: os.path.basename(p))
    lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
    for p in objs:
        name = os.path.splitext(os.path.basename(p))[0]
        try:
            m = trimesh.load_mesh(p, process=True)
            if isinstance(m, trimesh.Scene):
                m = m.to_mesh()
            if len(m.faces) == 0:
                raise ValueError("empty mesh")
            lo, hi = np.minimum(lo, m.bounds[0]), np.maximum(hi, m.bounds[1])
            rec["parts"].append({"name": name, "n_faces": int(len(m.faces)),
                                 "watertight": bool(m.is_watertight),
                                 "volume": float(m.volume) if m.is_watertight else None})
        except Exception as e:  # noqa: BLE001
            rec["ok"] = False
            rec["errors"].append(f"{name}: {type(e).__name__}: {e}")
    rec["n_parts"] = len(objs)
    rec["bounds"] = [lo.tolist(), hi.tolist()] if objs else None
    rec["all_watertight"] = all(p["watertight"] for p in rec["parts"]) and rec["ok"]
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True, help="dataset folder containing assembly folders")
    ap.add_argument("--out", required=True, help="per-assembly jsonl output")
    ap.add_argument("--summary", required=True, help="summary json output")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--limit", type=int, default=0, help="inspect only the first N assemblies (0 = all)")
    args = ap.parse_args()

    dirs = sorted(d for d in glob.glob(os.path.join(args.root, "*")) if os.path.isdir(d))
    if args.limit:
        dirs = dirs[: args.limit]
    with Pool(args.workers) as pool:
        recs = pool.map(inspect_one, dirs, chunksize=8)
    with open(args.out, "w") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    hist = collections.Counter(r["n_parts"] for r in recs)
    ok = [r for r in recs if r["ok"] and r["n_parts"] > 0]
    summ = {
        "root": args.root,
        "n_assemblies": len(recs),
        "n_all_meshes_load": len(ok),
        "n_all_watertight": sum(r["all_watertight"] for r in recs),
        "n_load_failures": len(recs) - len(ok),
        "part_count_hist": dict(sorted(hist.items())),
        "n_parts_3_to_6_loadable": sum(1 for r in ok if 3 <= r["n_parts"] <= 6),
        "n_parts_3_to_8_loadable": sum(1 for r in ok if 3 <= r["n_parts"] <= 8),
        "example_failures": [(r["id"], r["errors"][:2]) for r in recs if not r["ok"]][:10],
    }
    json.dump(summ, open(args.summary, "w"), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
