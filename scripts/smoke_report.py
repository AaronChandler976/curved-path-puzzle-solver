#!/usr/bin/env python
"""Build reports/smoke_test.md from CMG-RRT smoke results (scripts/smoke_sweep.py / smoke_cmgrrt.py)."""
import argparse
import json
import os

import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", nargs="+", required=True, help="results.jsonl files")
    ap.add_argument("--out", required=True)
    ap.add_argument("--notes", default="", help="markdown file appended verbatim (hand-written notes)")
    args = ap.parse_args()
    rows = []
    for p in args.results:
        d = os.path.dirname(p)
        for l in open(p):
            r = json.loads(l)
            r["_log"] = os.path.join(d, f"{r['example'].replace('/', '_')}_{r['device']}.log")
            if not os.path.exists(r["_log"]):
                r["_log"] = os.path.join(d, "stdout.log")
            rows.append(r)
    rows.sort(key=lambda r: (r["example"], r["device"]))
    L = ["# CMG-RRT smoke test on bundled examples (S1)\n",
         "Each row is one real run of `scripts/smoke_cmgrrt.py`: library CMG-RRT, unmodified example files, test_list.json "
         "parameters (eta 0.002, threshold -0.005, steps 50; sampling from properties.json, else 4000), our fast obstacle "
         "SDF (see DECISIONS #3). Cap: --iterations and --timeout (wall s). `start_sdf` = min SDF of the robot samples at "
         "q2_start; the start is valid when it is >= -0.005.\n",
         "| example | device | outcome | iterations | planner wall s | s/iter | start_sdf | SDF (epochs, samples, sign) | log |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        sdf = f"{r.get('sdf_epochs', 30)}, {r.get('sdf_samples', 2000000) / 1e6:.0f}M, {r.get('sdf_sign', 'quicksdf')}"
        L.append(f"| {r['example']} | {r['device']} | **{r['outcome']}** | {r['iterations']} | {r['time_s']:.1f} | "
                 f"{r['time_s'] / max(1, r['iterations']):.3f} | {r['start_min_sdf']:+.4f} | {sdf} | `{r['_log']}` |")
    succ = [r for r in rows if r["outcome"] == "success"]
    L.append(f"\n**Successes: {len(succ)} / {len(rows)} runs.**")
    for dev in ("cpu", "cuda"):
        x = [r["time_s"] / max(1, r["iterations"]) for r in rows if r["device"] == dev]
        if x:
            L.append(f"- {dev}: s/iteration median {np.median(x):.3f} (min {min(x):.3f}, max {max(x):.3f}) over {len(x)} runs")
    if succ:
        t = [r["time_s"] for r in succ]
        L.append(f"- success times (s): median {np.median(t):.1f}, min {min(t):.1f}, max {max(t):.1f}")
    if args.notes and os.path.exists(args.notes):
        L.append("\n" + open(args.notes).read())
    open(args.out, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
