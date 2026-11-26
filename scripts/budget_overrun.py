#!/usr/bin/env python
"""Campaign Phase 3 (after the single test evaluation; reads saved outputs only): how soft the planner budgets are.

Definitions (stated in the output):
- TEST LABELS (data/processed/run05/graphs_test.pt, built by the one test evaluation; every query of every test state,
  first clean attempt, 12,444 queries): main-config cost = pre-check + CMG-RRT when the pull did not clear; unsolved =
  no main-config success. Reported: unsolved count, median and max cost; total main-config cost beyond 30 s over ALL
  queries (sum of max(0, cost - 30)); main-config successes with cost > 30 s; CMG-RRT-only successes with CMG-RRT time
  > 30 s.
- LIVE BUDGET POLICY (experiments/2026-11-24_final_eval_live/results.jsonl, methods with "@b3", the reported attempt
  per (assembly, method) = first clean, else attempt 0): pass-1 queries (budget 3 s) that did not succeed and ran
  CMG-RRT. Reported: count, median and max CMG-RRT time, CMG-RRT time beyond 3 s (sum of max(0, cmgrrt_time - 3)),
  the same for the whole query (pre-check + CMG-RRT), and the total planner time of the two policy rows.
Cause (code): the adapter checks the time limit once per RRT iteration (src/disasm/oracle/cmgrrt.py, `el > timeout_s`).
"""
import argparse
import json
import os
from collections import defaultdict

import numpy as np
import torch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--graphs", default=os.path.join(ROOT, "data/processed/run05/graphs_test.pt"))
    ap.add_argument("--live", default=os.path.join(ROOT, "experiments/2026-11-24_final_eval_live/results.jsonl"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    G = torch.load(a.graphs, weights_only=False)
    t = np.concatenate([g["time_s"].numpy() for g in G]).astype(float)
    s = np.concatenate([g["succ"].numpy() for g in G]).astype(bool)
    tc = np.concatenate([g["time_cm"].numpy() for g in G]).astype(float)
    sc = np.concatenate([g["succ_cm"].numpy() for g in G]).astype(bool)
    res = {"labels": {"n_queries": int(len(t)), "n_unsolved": int((~s).sum()),
                      "unsolved_median_s": float(np.median(t[~s])), "unsolved_max_s": float(t[~s].max()),
                      "cost_beyond_30s_all_queries_s": float(np.maximum(t - 30, 0).sum()),
                      "main_successes_over_30s": int((s & (t > 30)).sum()), "main_success_max_s": float(t[s].max()),
                      "cmgrrt_only_successes_over_30s": int((sc & (tc > 30)).sum()),
                      "cmgrrt_only_success_max_s": float(tc[sc].max())}}
    att = defaultdict(list)
    for l in open(a.live):
        r = json.loads(l)
        if "@b3" in r["method"]:
            att[(r["assembly_id"], r["method"])].append(r)
    rep = []
    for k, rs in att.items():
        rs = sorted(rs, key=lambda r: r.get("attempt", 0))
        clean = [r for r in rs if not r.get("confounded") and not r.get("error")]
        rep.append(clean[0] if clean else rs[0])
    cm, whole, total = [], [], 0.0
    for r in rep:
        total += float(r["planner_s"])
        for st in r["states"]:
            for q in st["queries"]:
                if q.get("pass") == 0 and q["outcome"] != "success" and q.get("cmgrrt_time_s") is not None:
                    cm.append(float(q["cmgrrt_time_s"])); whole.append(float(q["time_s"]))
    cm, whole = np.array(cm), np.array(whole)
    res["live_policy"] = {"n_runs": len(rep), "n_pass1_failed_cmgrrt_queries": int(len(cm)),
                          "cmgrrt_median_s": float(np.median(cm)), "cmgrrt_max_s": float(cm.max()),
                          "cmgrrt_beyond_3s_s": float(np.maximum(cm - 3, 0).sum()),
                          "whole_query_beyond_3s_s": float(np.maximum(whole - 3, 0).sum()),
                          "total_planner_s_policy_rows": total}
    json.dump(res, open(os.path.join(a.out, "budget_overrun.json"), "w"), indent=1)
    print(__doc__.split("Cause")[0])
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
