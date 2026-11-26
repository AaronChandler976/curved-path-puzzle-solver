#!/usr/bin/env python
"""Compute (and cache) the assembled-pose contact graph for every ATA multi-part assembly with
--min-parts..--max-parts parts: contact pairs, and the max penetration depth (deepest surface
sample of one part inside another, unit frame, winding-number sign). CMG-RRT's start pose is only
valid if the obstacle SDF at the assembled pose is >= threshold (-0.005), so assemblies whose
meshes interpenetrate deeper than that can never produce a success. Output: results.jsonl."""
import argparse
import json
import os
import sys
import time
from multiprocessing import get_context

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def one(aid):
    from disasm.oracle.cmgrrt import load_assembly, contact_graph
    t = time.time()
    try:
        a = load_assembly(os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly", aid))
        cg = contact_graph(a)
        return {"id": aid, "n_parts": len(a.part_ids), "contact_pairs": len(cg["pairs"]) // 2,
                "contact_pairs_directed": len(cg["pairs"]), "max_penetration": cg["max_penetration"],
                "bbox_diag": a.bbox_diag, "time_s": time.time() - t, "error": None}
    except Exception as e:  # noqa: BLE001
        return {"id": aid, "error": f"{type(e).__name__}: {e}", "time_s": time.time() - t}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--inspect", default=os.path.join(ROOT, "experiments/2026-11-21_inspect_multi/assemblies.jsonl"))
    ap.add_argument("--min-parts", type=int, default=3)
    ap.add_argument("--max-parts", type=int, default=8)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    out = os.path.join(args.outdir, "results.jsonl")
    done = {json.loads(l)["id"] for l in open(out)} if os.path.exists(out) else set()
    ids = sorted(r["id"] for r in map(json.loads, open(args.inspect))
                 if args.min_parts <= len(r["parts"]) <= args.max_parts and r["id"] not in done)
    print(len(ids), "to scan", flush=True)
    with get_context("spawn").Pool(args.workers) as pool, open(out, "a") as f:
        for i, r in enumerate(pool.imap_unordered(one, ids, chunksize=4)):
            f.write(json.dumps(r) + "\n")
            if i % 100 == 0:
                f.flush()
                print(i, r, flush=True)
    print("SCAN DONE", flush=True)


if __name__ == "__main__":
    main()
