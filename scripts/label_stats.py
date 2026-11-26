#!/usr/bin/env python
"""Print pilot label counts: assemblies by status, states, queries, success rate, time quantiles."""
import argparse
import json
import os
from collections import Counter

import numpy as np

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--dir", default="data/labels/pilot_v0")
ap.add_argument("--json", action="store_true")
a = ap.parse_args()
L = [json.loads(l) for l in open(os.path.join(a.dir, "labels.jsonl"))] if os.path.exists(os.path.join(a.dir, "labels.jsonl")) else []
S = [json.loads(l) for l in open(os.path.join(a.dir, "states.jsonl"))] if os.path.exists(os.path.join(a.dir, "states.jsonl")) else []
M = [json.loads(l) for l in open(os.path.join(a.dir, "summary.jsonl"))] if os.path.exists(os.path.join(a.dir, "summary.jsonl")) else []
succ = [r for r in L if r["outcome"] == "success"]
uns = [r for r in L if r["outcome"] != "success"]
q = lambda x, p: float(np.percentile(x, p)) if len(x) else float("nan")
out = {
    "assemblies_by_status": dict(Counter(m["status"] for m in M)),
    "skip_reasons": dict(Counter(m.get("reason", "").split(" ")[0] for m in M if m["status"] == "skipped")),
    "states": len(S), "states_with_success": sum(1 for s in S if s["n_success"] > 0),
    "queries": len(L), "successes": len(succ), "success_rate": len(succ) / max(1, len(L)),
    "errors": sum(1 for r in L if r.get("error")),
    "start_invalid_frac_of_unsolved": sum(1 for r in uns if r.get("start_valid") is False) / max(1, len(uns)),
    "success_time_s_p10_p50_p90_max": [q([r["time_s"] for r in succ], p) for p in (10, 50, 90, 100)],
    "success_iterations_p50_p90_max": [q([r["iterations"] for r in succ], p) for p in (50, 90, 100)],
    "prep_s_p50_p90": [q([r["prep_s"] or 0 for r in L], p) for p in (50, 90)],
    "planner_s_total": float(sum(r["time_s"] or 0 for r in L)),
}
print(json.dumps(out, indent=1))
