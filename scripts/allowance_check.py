#!/usr/bin/env python
"""Run 04 T6.2: allowance validation (src/disasm/data/allowance_check.py) on the success paths of fresh-allowance
assemblies in a v2 labels.jsonl. Untimed CPU work. Output <outdir>/paths.jsonl + summary.json."""
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
    ap.add_argument("--labels", required=True)
    ap.add_argument("--allowance", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--max-assemblies", type=int, default=50)
    a = ap.parse_args()
    from disasm.util.guarded_pool import run_guarded
    allow = json.load(open(a.allowance))
    items = defaultdict(list)
    for l in open(a.labels):
        x = json.loads(l)
        if x.get("source") != "fresh-allowance" or x["outcome"] != "success":
            continue
        pf = x.get("path_file_precheck") if x.get("stage") == "precheck" else x.get("path_file")
        if not pf:
            continue
        items[x["assembly_id"]].append({"id": f"{x['assembly_id']}|{x['state_key']}|{x['part_id']}", "removed": x["removed"],
                                        "part": x["part_id"], "seed": x["seed"], "path_file": pf, "stage": x["stage"]})
    aids = sorted(items)[: a.max_assemblies]
    jobs = [{"key": aid, "asm_dir": os.path.join(RAW, aid), "items": items[aid], "allowance": allow[aid],
             "workdir": os.path.join(a.outdir, "work")} for aid in aids]
    att = run_guarded("disasm.data.allowance_check:check_job", jobs, a.outdir, out_name="jobs.jsonl", workers=10,
                      idle_wait=0, max_reruns=0, guard=False, slot_tag="allowance_check", log=lambda m: print(m, flush=True))
    P = [it for xs in att.values() for it in xs[0].get("items", [])]
    with open(os.path.join(a.outdir, "paths.jsonl"), "w") as f:
        for p in P:
            f.write(json.dumps(p) + "\n")
    s = {"assemblies": len(aids), "paths": len(P), **{k: sum(p[k] for p in P) for k in ("A_start_valid", "B_ok", "C_ok", "D_ok", "all_ok")},
         "errors": sum(1 for xs in att.values() if xs[0].get("error"))}
    json.dump(s, open(os.path.join(a.outdir, "summary.json"), "w"), indent=1)
    print(json.dumps(s))


if __name__ == "__main__":
    main()
