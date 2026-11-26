#!/usr/bin/env python
"""R4 (run 03): ASAP GNN (released weights, zero-shot) scores for every labelled v1 state.

Uses only geometry (no labels). Output: <outdir>/scores.jsonl, one line per state:
{assembly_id, state_key, present, score (per present part), n_contact_pairs}. See src/disasm/search/asap_baseline.py.
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly")
_M = {}


def _init():
    import torch
    torch.set_num_threads(1)
    from disasm.search.asap_baseline import load_asap_model
    _M["m"], _M["meta"] = load_asap_model()


def _job(a):
    aid, skeys = a
    import traceback
    from disasm.oracle.cmgrrt import load_assembly
    from disasm.search.asap_baseline import asap_contact_pairs, asap_node_inputs, asap_scores
    try:
        asm = load_assembly(os.path.join(RAW, aid))
        pairs = asap_contact_pairs(asm)
        ni = asap_node_inputs(os.path.join(RAW, aid), aid)
        out = []
        for sk in skeys:
            present = [int(x) for x in sk.split("-")]
            s = asap_scores(_M["m"], ni, pairs, present)
            out.append({"assembly_id": aid, "state_key": sk, "present": present, "score": [float(v) for v in s],
                        "n_contact_pairs": len(pairs), "contact_pairs": sorted([list(p) for p in pairs])})
        return out
    except Exception as e:  # noqa: BLE001
        return [{"assembly_id": aid, "state_key": sk, "error": f"{type(e).__name__}: {e}",
                 "traceback": traceback.format_exc()} for sk in skeys]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--states", default=os.path.join(ROOT, "data/labels/pilot_v1/states.jsonl"))
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--procs", type=int, default=8)
    args = ap.parse_args()
    from disasm.util.runlog import log_load
    os.makedirs(args.outdir, exist_ok=True)
    log_load(args.outdir, "start")
    by = defaultdict(list)
    for l in open(args.states):
        r = json.loads(l)
        by[r["assembly_id"]].append(r["state_key"])
    jobs = sorted(by.items())
    t0 = time.time()
    n, nerr = 0, 0
    with open(os.path.join(args.outdir, "scores.jsonl"), "w") as f, \
            mp.get_context("spawn").Pool(args.procs, initializer=_init) as pool:
        for res in pool.imap_unordered(_job, jobs, chunksize=2):
            for r in res:
                f.write(json.dumps(r) + "\n"); n += 1; nerr += bool(r.get("error"))
    from disasm.search.asap_baseline import CKPT
    import hashlib
    meta = {"states": n, "errors": nerr, "assemblies": len(jobs), "wall_s": time.time() - t0,
            "ckpt": os.path.relpath(CKPT, ROOT), "ckpt_sha256": hashlib.sha256(open(CKPT, "rb").read()).hexdigest()}
    json.dump(meta, open(os.path.join(args.outdir, "meta.json"), "w"), indent=1)
    log_load(args.outdir, "end")
    print(json.dumps(meta), flush=True)


if __name__ == "__main__":
    main()
