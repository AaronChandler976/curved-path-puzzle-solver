#!/usr/bin/env python
"""Run 04 T7: reports/run04/labels_v2.md from data/labels/pilot_v2 (labels.jsonl = first clean attempt per query,
attempts.jsonl = every attempt, states.jsonl, summary.jsonl), compared with pilot_v1 on the same assemblies."""
import argparse
import json
import os
from collections import Counter, defaultdict

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def pbin(n):
    return "3-4" if n <= 4 else "5-6" if n <= 6 else "7-8" if n <= 8 else "9-10" if n <= 10 else "11-12"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default=os.path.join(ROOT, "data/labels/pilot_v2"))
    ap.add_argument("--v1", default=os.path.join(ROOT, "data/labels/pilot_v1"))
    ap.add_argument("--planned", required=True, help="text file: planned assembly ids (the T7 order file)")
    ap.add_argument("--run-dir", required=True, help="experiments folder of the labelling run")
    ap.add_argument("--out", default=os.path.join(ROOT, "reports/run04/labels_v2.md"))
    a = ap.parse_args()
    L = [json.loads(l) for l in open(os.path.join(a.dir, "labels.jsonl"))]
    S = {}
    for l in open(os.path.join(a.dir, "summary.jsonl")):
        s = json.loads(l)
        S[s["assembly_id"]] = s
    natt = sum(1 for _ in open(os.path.join(a.dir, "attempts.jsonl")))
    planned = [l.strip() for l in open(a.planned) if l.strip()]
    missing = [x for x in planned if x not in S]
    src = {x["assembly_id"]: x["source"] for x in L}
    for aid, s in S.items():
        src.setdefault(aid, s.get("source", "v1"))
    out = ["# Run 04 T7: pilot_v2 labels (oracle v2)\n",
           f"Labels `{os.path.relpath(a.dir, ROOT)}/` (labels.jsonl = first clean attempt per query; attempts.jsonl = every "
           f"attempt, {natt} lines); run folder `{os.path.relpath(a.run_dir, ROOT)}/` (stdout.log, idle_samples.jsonl, "
           "load_info.txt). Report: `scripts/labels_v2_report.py`.\n",
           f"- planned assemblies: {len(planned)}; with a summary line: {len(planned) - len(missing)}; "
           f"**missing: {len(missing)}**" + (f" ({', '.join(missing[:20])}{' …' if len(missing) > 20 else ''})" if missing else ""),
           f"- summary status: {dict(Counter(s['status'] for s in S.values()))}",
           "- skipped reasons: " + json.dumps(dict(Counter(s.get('reason', '')[:40] for s in S.values() if s['status'] == 'skipped'))),
           f"- queries: {len(L)}; still confounded after 2 re-runs: {sum(x.get('still_confounded', False) for x in L)} "
           f"(**{100 * sum(x.get('still_confounded', False) for x in L) / max(1, len(L)):.2f}%**); fixed by a re-run: "
           f"{sum(1 for x in L if x.get('label_attempt', 0) > 0)}; errors: {sum(bool(x.get('error')) for x in L)}\n",
           "## Per source and part-count bin (main config = pre-check → CMG-RRT)\n",
           "| source | bin | assemblies (complete / stuck) | states | queries | success rate | pre-check share of successes | CMG-RRT-only success rate | main-config planner h | CMG-RRT-only planner h |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    by = defaultdict(list)
    for x in L:
        by[(x["source"], pbin(x["n_parts"]))].append(x)
    for k in sorted(by, key=lambda k: (k[0], ["3-4", "5-6", "7-8", "9-10", "11-12"].index(k[1]))):
        xs = by[k]
        aids = {x["assembly_id"] for x in xs}
        st = Counter(S[i]["status"] for i in aids if i in S)
        succ = [x for x in xs if x["outcome"] == "success"]
        out.append(f"| {k[0]} | {k[1]} | {len(aids)} ({st.get('complete', 0)} / {st.get('stuck', 0)}) | "
                   f"{len({(x['assembly_id'], x['state_key']) for x in xs})} | {len(xs)} | {len(succ) / len(xs):.3f} | "
                   f"{sum(x['stage'] == 'precheck' for x in succ) / max(1, len(succ)):.3f} | "
                   f"{np.mean([x['cmgrrt_outcome'] == 'success' for x in xs]):.3f} | {sum(x['time_s'] or 0 for x in xs) / 3600:.2f} | "
                   f"{sum(x['cmgrrt_time_s'] or 0 for x in xs) / 3600:.2f} |")
    # v1 vs v2 on the same assemblies
    V1 = {}
    for l in open(os.path.join(a.v1, "labels.jsonl")):
        x = json.loads(l)
        V1[(x["assembly_id"], x["state_key"], x["part_id"])] = x
    S1 = {}
    for l in open(os.path.join(a.v1, "summary.jsonl")):
        s = json.loads(l)
        S1[s["assembly_id"]] = s
    both = [x for x in L if (x["assembly_id"], x["state_key"], x["part_id"]) in V1]
    tab = Counter((V1[(x["assembly_id"], x["state_key"], x["part_id"])]["outcome"], x["outcome"]) for x in both)
    tabc = Counter((V1[(x["assembly_id"], x["state_key"], x["part_id"])]["outcome"], x["cmgrrt_outcome"]) for x in both)
    v1a = [i for i in S if src.get(i) == "v1" and i in S1]
    tr = Counter((S1[i]["status"], S[i]["status"]) for i in v1a)
    out += ["\n## v1 vs v2 on the same queries (identical state, part and seed; v1 = pilot_v1 label)\n",
            f"Queries present in both: {len(both)} (v2 states follow v2's own removals, so only the shared states match).\n",
            "| v1 outcome → v2 main outcome | count |", "|---|---|"] + \
           [f"| {k[0]} → {k[1]} | {v} |" for k, v in sorted(tab.items())] + \
           ["\n| v1 outcome → v2 CMG-RRT-only outcome | count |", "|---|---|"] + \
           [f"| {k[0]} → {k[1]} | {v} |" for k, v in sorted(tabc.items())] + \
           [f"\nv1 assemblies, status v1 → v2: {dict((f'{k[0]}→{k[1]}', v) for k, v in sorted(tr.items()))}",
            f"\nv1 total planner time on the shared queries: {sum(V1[(x['assembly_id'], x['state_key'], x['part_id'])]['time_s'] or 0 for x in both) / 3600:.2f} h; "
            f"v2 main config: {sum(x['time_s'] or 0 for x in both) / 3600:.2f} h; v2 CMG-RRT only: {sum(x['cmgrrt_time_s'] or 0 for x in both) / 3600:.2f} h."]
    lp = os.path.join(a.run_dir, "load_info.txt")
    if os.path.exists(lp):
        out += ["\n## Load info\n", "```", open(lp).read().strip(), "```"]
    open(a.out, "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
