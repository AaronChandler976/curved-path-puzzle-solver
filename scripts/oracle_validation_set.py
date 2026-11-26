#!/usr/bin/env python
"""Run 04 T4.4: validation set = the 124 run 03 misses (linear-free but unsolved) + 500 random v1 queries (seed 0),
each run under configs v1, v2a, v2b (src/disasm/oracle/validation_set.py), through the idle guard, interleaved
per query. Output <outdir>/results.jsonl (+ idle_samples.jsonl)."""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--n-random", type=int, default=500)
    ap.add_argument("--configs", default="v1,v2a,v2b")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--idle-wait", type=float, default=300)
    ap.add_argument("--no-misses", action="store_true", help="random queries only (run 04 T5 ATA sample)")
    ap.add_argument("--sample-seed", type=int, default=0)
    a = ap.parse_args()
    from diagnose_misses import misses
    from disasm.util.guarded_pool import run_guarded
    from disasm.util.runlog import log_load
    ms = misses()
    mk = {(m["assembly_id"], m["state_key"], m["part_id"]) for m in ms}
    lab = [json.loads(l) for l in open(os.path.join(ROOT, "data/labels/pilot_v1/labels.jsonl"))]
    pool = [x for x in lab if (x["assembly_id"], x["state_key"], x["part_id"]) not in mk]
    rnd = random.Random(a.sample_seed).sample(pool, a.n_random)
    if a.no_misses:
        ms = []
    qs = [("miss", m["assembly_id"], m["state_key"], m["part_id"], m["removed"], m["seed"]) for m in ms] + \
         [("random", x["assembly_id"], x["state_key"], x["part_id"], x["removed"], x["seed"]) for x in rnd]
    qs.sort(key=lambda q: (q[1], q[2], q[3]))
    jobs = []
    for s, aid, sk, p, rm, seed in qs:
        for c in a.configs.split(","):
            jobs.append({"key": f"{c}|{aid}|{sk}|{p}", "config": c, "set": s, "asm_dir": os.path.join(RAW, aid),
                         "removed": rm, "part": p, "seed": seed, "state_key": sk, "T": 30.0,
                         "workdir": os.path.join(a.outdir, "work", c)})
    os.makedirs(a.outdir, exist_ok=True)
    json.dump([list(q) for q in qs], open(os.path.join(a.outdir, "queries.json"), "w"))
    print(f"{len(qs)} queries x {len(a.configs.split(','))} configs = {len(jobs)} jobs", flush=True)
    log_load(a.outdir, "start")
    run_guarded("disasm.oracle.validation_set:val_job", jobs, a.outdir, workers=a.workers, idle_wait=a.idle_wait,
                slot_tag="oracle_validation", log=lambda m: print(m, flush=True))
    log_load(a.outdir, "end")


if __name__ == "__main__":
    main()
