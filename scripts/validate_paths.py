#!/usr/bin/env python
"""Run 04 T4.1: re-check saved CMG-RRT success paths edge by edge with the exact union SDF at step <= eps/2
(src/disasm/oracle/path_validate.py). Sources: --labels (labels.jsonl with path_file, outcome success) and/or
--live (live_abd results.jsonl). Untimed CPU work (planner slots, no idle guard). Output: <outdir>/paths.jsonl."""
import argparse
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--labels", action="append", default=[])
    ap.add_argument("--live", action="append", default=[])
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--per-job", type=int, default=40)
    a = ap.parse_args()
    from disasm.util.guarded_pool import run_guarded
    from disasm.util.runlog import log_load
    items = defaultdict(list)
    n_missing = 0
    for lp in a.labels:
        tag = os.path.basename(os.path.dirname(lp))
        for l in open(lp):
            x = json.loads(l)
            if x["outcome"] != "success":
                continue
            pf = x.get("path_file")
            if not pf or not os.path.exists(os.path.join(ROOT, pf) if not os.path.isabs(pf) else pf):
                n_missing += 1
                continue
            items[x["assembly_id"]].append({"id": f"{tag}|{x['assembly_id']}|{x['state_key']}|{x['part_id']}",
                                            "removed": x["removed"], "part": x["part_id"], "seed": x["seed"],
                                            "path_file": pf if os.path.isabs(pf) else os.path.join(ROOT, pf)})
    for lp in a.live:
        tag = os.path.basename(os.path.dirname(lp))
        for l in open(lp):
            r = json.loads(l)
            removed = []
            for st in r.get("states", []):
                for q in st["queries"]:
                    if q["outcome"] == "success":
                        pf = q.get("path_file")
                        if not pf or not os.path.exists(pf):
                            n_missing += 1
                            continue
                        items[r["assembly_id"]].append({"id": f"{tag}|{r['assembly_id']}|{r['method']}|{r.get('attempt', 0)}|{st['state_key']}|{q['part']}",
                                                        "removed": list(removed), "part": q["part"], "seed": q["seed"],
                                                        "path_file": pf})
                if st.get("chosen") is not None:
                    removed.append(st["chosen"])
    jobs = []
    for aid, its in sorted(items.items()):
        for i in range(0, len(its), a.per_job):
            jobs.append({"key": f"{aid}#{i}", "asm_dir": os.path.join(RAW, aid), "items": its[i:i + a.per_job],
                         "eps": 0.005, "workdir": os.path.join(a.outdir, "work")})
    print(f"{sum(map(len, items.values()))} paths in {len(jobs)} jobs; {n_missing} successes without a saved path", flush=True)
    os.makedirs(a.outdir, exist_ok=True)
    json.dump({"n_missing_path": n_missing}, open(os.path.join(a.outdir, "missing.json"), "w"))
    log_load(a.outdir, "start")
    att = run_guarded("disasm.oracle.path_validate:validate_saved_job", jobs, a.outdir, out_name="jobs.jsonl",
                      workers=a.workers, idle_wait=0, max_reruns=0, slot_tag="validate_paths", guard=False,
                      log=lambda m: print(m, flush=True))
    with open(os.path.join(a.outdir, "paths.jsonl"), "w") as f:
        for k, xs in att.items():
            for it in xs[0].get("items", []):
                f.write(json.dumps(it) + "\n")
    log_load(a.outdir, "end")


if __name__ == "__main__":
    main()
