#!/usr/bin/env python
"""Run 04 T4.2: instrumented v1-adapter re-run of the run 03 linear-free-but-unsolved queries (default: all 124),
through the idle guard. Output: <outdir>/results.jsonl (one line per query, see disasm.oracle.diagnose)."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly")


def misses():
    lab = {}
    for l in open(os.path.join(ROOT, "data/labels/pilot_v1/labels.jsonl")):
        x = json.loads(l)
        lab[(x["assembly_id"], x["state_key"], x["part_id"])] = x
    out = []
    for l in open(os.path.join(ROOT, "data/labels/pilot_v1/precheck.jsonl")):
        p = json.loads(l)
        k = (p["assembly_id"], p["state_key"], p["part_id"])
        if p.get("linear_free") and lab[k]["outcome"] == "unsolved":
            out.append({**p, "v1": lab[k]})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--idle-wait", type=float, default=300)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    from disasm.util.guarded_pool import run_guarded
    from disasm.util.runlog import log_load
    ms = misses()
    print(f"{len(ms)} linear-free-but-unsolved v1 queries", flush=True)
    if a.limit:
        ms = ms[:a.limit]
    jobs = [{"key": f"{m['assembly_id']}|{m['state_key']}|{m['part_id']}", "asm_dir": os.path.join(RAW, m["assembly_id"]),
             "removed": m["removed"], "part": m["part_id"], "seed": m["seed"], "state_key": m["state_key"],
             "free_dir": m["first_free_dir"], "T": 30.0, "eps": 0.005, "workdir": os.path.join(a.outdir, "work")}
            for m in ms]
    log_load(a.outdir, "start")
    run_guarded("disasm.oracle.diagnose:diagnose_job", jobs, a.outdir, workers=a.workers, idle_wait=a.idle_wait,
                slot_tag="diagnose", log=lambda m: print(m, flush=True))
    log_load(a.outdir, "end")


if __name__ == "__main__":
    main()
