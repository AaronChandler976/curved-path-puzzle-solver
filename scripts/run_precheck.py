#!/usr/bin/env python
"""R1 (run 03): straight-line pull pre-check on every pilot_v1 query (successes and unsolved).

Writes one line per query to --out (default data/labels/pilot_v1/precheck.jsonl), keyed like the labels
(assembly_id, state_key, part_id). Resumable: keys already in --out are skipped. Workers take planner
slots (disasm.oracle.pool._init -> disasm.util.slots). One job = all queries of one assembly.
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--labels", default=os.path.join(ROOT, "data/labels/pilot_v1/labels.jsonl"))
    ap.add_argument("--out", default=os.path.join(ROOT, "data/labels/pilot_v1/precheck.jsonl"))
    ap.add_argument("--outdir", required=True, help="experiments/<date>_run03_precheck")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--eps", type=float, default=0.005)
    ap.add_argument("--limit", type=int, default=0, help="only the first N assemblies (dev)")
    args = ap.parse_args()
    from disasm.oracle import pool as P
    from disasm.oracle.linear_precheck import run_assembly_job
    from disasm.util.runlog import log_load
    os.makedirs(args.outdir, exist_ok=True)
    log_load(args.outdir, "start")
    done = set()
    if os.path.exists(args.out):
        for l in open(args.out):
            r = json.loads(l)
            done.add((r["assembly_id"], r["state_key"], r["part_id"]))
    by_asm = defaultdict(list)
    n_all = 0
    for l in open(args.labels):
        r = json.loads(l)
        n_all += 1
        if (r["assembly_id"], r["state_key"], r["part_id"]) in done:
            continue
        by_asm[r["assembly_id"]].append({"state_key": r["state_key"], "removed": r["removed"],
                                          "part_id": r["part_id"], "seed": r["seed"]})
    aids = sorted(by_asm)
    if args.limit:
        aids = aids[: args.limit]
    print(f"{n_all} label rows, {len(done)} already prechecked, {sum(len(by_asm[a]) for a in aids)} to do "
          f"in {len(aids)} assemblies, eps={args.eps}", flush=True)
    P.pin_threads(1)
    work = os.path.join(args.outdir, "work")
    ex = ProcessPoolExecutor(args.workers, mp_context=mp.get_context("spawn"), initializer=P._init,
                             initargs=({"workdir": work, "device": "cpu", "threads": 1, "slot_tag": "precheck"},))
    root = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly")
    pending, t0, nq = set(), time.time(), 0
    queue = list(aids)
    with open(args.out, "a") as fo:
        while queue or pending:
            while queue and len(pending) < 3 * args.workers:
                a = queue.pop(0)
                pending.add(ex.submit(run_assembly_job, {"asm_dir": os.path.join(root, a), "assembly_id": a,
                                                         "queries": by_asm[a], "workdir": work, "eps": args.eps}))
            fin, pending = wait(pending, return_when=FIRST_COMPLETED)
            for f in fin:
                for rec in f.result():
                    fo.write(json.dumps(rec) + "\n")
                    nq += 1
                fo.flush()
            if nq and nq % 500 < 40:
                print(f"[{(time.time() - t0) / 60:5.1f} min] {nq} queries prechecked, {len(queue)} asm queued", flush=True)
    ex.shutdown(wait=True)
    log_load(args.outdir, "end")
    print(f"PRECHECK EXIT queries={nq} wall={time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
