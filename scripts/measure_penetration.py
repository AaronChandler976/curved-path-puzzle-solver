#!/usr/bin/env python
"""Run 04 T6.2: per-pair start penetration (src/disasm/data/penetration.py) for a list of assemblies.
Untimed CPU work (planner slots, no idle guard). Output: <outdir>/results.jsonl (key = assembly id)."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ids", required=True, help="json list of assembly ids")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--workers", type=int, default=10)
    a = ap.parse_args()
    from disasm.util.guarded_pool import run_guarded
    from disasm.util.runlog import log_load
    ids = json.load(open(a.ids))
    log_load(a.outdir, "start")
    run_guarded("disasm.data.penetration:measure_job", [{"key": i, "asm_dir": os.path.join(RAW, i)} for i in ids],
                a.outdir, workers=a.workers, idle_wait=0, max_reruns=0, slot_tag="penetration", guard=False,
                log=lambda m: print(m, flush=True))
    log_load(a.outdir, "end")


if __name__ == "__main__":
    main()
