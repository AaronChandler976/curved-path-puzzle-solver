#!/usr/bin/env python
"""Run 04 T4.4 summary of experiments/<...>_oracle_validation/results.jsonl (first clean attempt per job)."""
import argparse
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", required=True)
    a = ap.parse_args()
    from disasm.util.guarded_pool import first_clean
    att = defaultdict(list)
    for l in open(os.path.join(a.dir, "results.jsonl")):
        r = json.loads(l)
        att[r["key"]].append(r)
    R = first_clean(att)
    by = defaultdict(dict)
    for r in R.values():
        by[(r["assembly_id"], r["state_key"], r["part_id"])][r["config"]] = r
    out = {"n_jobs": len(R), "still_confounded": sum(r["still_confounded"] for r in R.values()),
           "errors": sum(bool(r.get("error")) for r in R.values())}
    for s in ("miss", "random", "all"):
        qs = [q for q, c in by.items() if s == "all" or next(iter(c.values()))["set"] == s]
        row = {"n": len(qs)}
        for cfg in ("v1", "v2a", "v2b"):
            rs = [by[q][cfg] for q in qs if cfg in by[q]]
            if not rs:
                continue
            succ = [r["outcome"] == "success" for r in rs]
            d = {"success": int(sum(succ)), "rate": float(np.mean(succ)), "total_time_s": float(sum(r["time_s"] or 0 for r in rs)),
                 "median_time_s": float(np.median([r["time_s"] or 0 for r in rs]))}
            chk = [r["recheck"].get("main" if cfg != "v1" else "cmgrrt") for r in rs if r["outcome"] == "success"]
            d["recheck_invalid_main"] = int(sum(1 for c in chk if c is not None and not c["valid"]))
            d["recheck_missing"] = int(sum(1 for c in chk if c is None))
            if cfg != "v1":
                d["precheck_free"] = int(sum(bool(r["precheck_free"]) for r in rs))
                d["stage_precheck"] = int(sum(r["stage"] == "precheck" for r in rs))
                d["stage_cmgrrt"] = int(sum(r["stage"] == "cmgrrt" for r in rs))
                cm = [r["cmgrrt_outcome"] == "success" for r in rs]
                d["cmgrrt_only_success"] = int(sum(cm))
                d["cmgrrt_only_total_time_s"] = float(sum(r["cmgrrt_time_s"] or 0 for r in rs))
                d["cmgrrt_recheck_invalid"] = int(sum(1 for r in rs if r["recheck"].get("cmgrrt") and not r["recheck"]["cmgrrt"]["valid"]))
                d["paths_rejected_fine"] = int(sum(r.get("n_paths_rejected_fine") or 0 for r in rs))
                d["goal_edges_rejected_fine"] = int(sum(r.get("n_goal_edges_rejected_fine") or 0 for r in rs))
                d["precheck_time_total_s"] = float(sum(r["precheck_time_s"] or 0 for r in rs))
                d["start_invalid"] = int(sum(not r["start_valid"] for r in rs if r["start_valid"] is not None))
            row[cfg] = d
        out[s] = row
    # misses still unsolved under v2a/v2b, with reasons
    left = []
    for q, c in by.items():
        if next(iter(c.values()))["set"] != "miss":
            continue
        for cfg in ("v2a", "v2b"):
            r = c.get(cfg)
            if r and r["outcome"] != "success":
                left.append({"q": q, "config": cfg, "start_valid": r["start_valid"], "start_min_sdf": r["start_min_sdf"],
                             "precheck_free": r["precheck_free"], "error": r.get("error")})
    out["misses_unsolved_v2"] = left
    json.dump(out, open(os.path.join(a.dir, "summary.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
