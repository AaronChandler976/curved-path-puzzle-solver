#!/usr/bin/env python
"""Run 04 T5: table of bundled-puzzle runs (scripts/repro_cmgrrt.py results.jsonl)."""
import argparse
import json
from collections import defaultdict


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", required=True)
    a = ap.parse_args()
    R = [json.loads(l) for l in open(a.results)]
    print("| example | detector | seed | solved | stop | iterations | planner s | s / iteration | path fine-valid | busy_frac | confounded |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    agg = defaultdict(list)
    for r in sorted(R, key=lambda r: (r["example"], r["detector"], r.get("grad_dx") or 0, r["seed"])):
        det = r["detector"] + (f" (grad dx {r['grad_dx']:g})" if r.get("grad_dx") else "")
        fp = r.get("fine_path_check")
        print(f"| {r['example']} | {det} | {r['seed']} | {'yes' if r['success'] else 'no'} | {r['stop']} | {r['iterations']} | "
              f"{r['planner_wall_s']:.0f} | {r['planner_wall_s'] / max(1, r['iterations']):.3f} | "
              f"{'-' if fp is None else ('yes' if fp['valid'] else 'no (d_min %.4f)' % fp['d_min'])} | "
              f"{r.get('busy_frac', float('nan')):.3f} | {r.get('confounded')} |")
        agg[(r["example"], det)].append(r)
    print("\n| example | detector | solved / runs | mean iterations (solved) | mean planner s (all runs) |")
    print("|---|---|---|---|---|")
    for (ex, det), rs in sorted(agg.items()):
        sv = [r for r in rs if r["success"]]
        print(f"| {ex} | {det} | {len(sv)} / {len(rs)} | {sum(r['iterations'] for r in sv) / max(1, len(sv)):.0f} | "
              f"{sum(r['planner_wall_s'] for r in rs) / len(rs):.0f} |")


if __name__ == "__main__":
    main()
