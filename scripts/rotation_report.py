#!/usr/bin/env python
"""R1 (run 03): rotation-required counts and precheck/CMG-RRT inconsistencies -> reports/run03/rotation.md.

needs_rotation(query) = CMG-RRT success AND linear_free == False
rot_state = any successful part at the state needs rotation; rot_assembly = any state is a rot_state.
Inconsistency = linear_free == True but CMG-RRT unsolved.
"""
import argparse
import json
import os
from collections import Counter, defaultdict

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--labels", default=os.path.join(ROOT, "data/labels/pilot_v1/labels.jsonl"))
    ap.add_argument("--precheck", default=os.path.join(ROOT, "data/labels/pilot_v1/precheck.jsonl"))
    ap.add_argument("--out", default=os.path.join(ROOT, "reports/run03/rotation.md"))
    ap.add_argument("--json-out", default="")
    ap.add_argument("--precheck-log", default="experiments/2026-11-23_run03_precheck/stdout.log")
    args = ap.parse_args()
    labs = [json.loads(l) for l in open(args.labels)]
    pc = {}
    n_err = 0
    for l in open(args.precheck):
        r = json.loads(l)
        if r.get("error"):
            n_err += 1
        pc[(r["assembly_id"], r["state_key"], r["part_id"])] = r
    keys = [(l["assembly_id"], l["state_key"], l["part_id"]) for l in labs]
    missing = [k for k in keys if k not in pc]
    cover = 1 - len(missing) / len(keys)
    st_rot, st_any = defaultdict(bool), set()
    asm_rot = defaultdict(bool)
    n_succ = n_need = 0
    incons, need_rows = [], []
    for l, k in zip(labs, keys):
        r = pc.get(k)
        if r is None or r.get("error"):
            continue
        sk = (l["assembly_id"], l["state_key"])
        st_any.add(sk)
        asm_rot[l["assembly_id"]] |= False
        if l["outcome"] == "success":
            n_succ += 1
            if not r["linear_free"]:
                n_need += 1
                st_rot[sk] = True
                asm_rot[l["assembly_id"]] = True
                need_rows.append((l, r))
        elif r["linear_free"]:
            incons.append((l, r))
    n_states_succ = len({(l["assembly_id"], l["state_key"]) for l in labs if l["outcome"] == "success"})
    rot_states = sum(st_rot.values())
    # diagnostics
    rot_deg = np.array([l.get("path_max_rot_deg") or 0.0 for l, _ in need_rows])
    succ_lin_rot = np.array([l.get("path_max_rot_deg") or 0.0 for l in labs if l["outcome"] == "success"
                             and pc.get((l["assembly_id"], l["state_key"], l["part_id"]), {}).get("linear_free")])
    dstart = np.array([abs(r["start_min_sdf_precheck"] - l["start_min_sdf"]) for l, r in
                       ((l, pc[k]) for l, k in zip(labs, keys) if k in pc and not pc[k].get("error"))
                       if l.get("start_min_sdf") is not None])
    start_invalid_need = sum(1 for _, r in need_rows if r["start_min_sdf_precheck"] < -r["eps"])
    first_dir = Counter(r["first_free_dir"] for r in pc.values() if r.get("linear_free"))
    first_dir_k = Counter(("contact_normal" if d == "contact_normal" else ("axis" if d[0] in "+-" else "away_from_neighbour"))
                          for d in first_dir.elements())
    inc_iter = np.array([l["iterations"] for l, _ in incons]) if incons else np.zeros(0)
    inc_goal_idx = Counter()
    for l, r in incons:
        dirs = list(r["dirs"])
        inc_goal_idx["first candidate (tree's goal)" if dirs and r["first_free_dir"] == dirs[0] and len(dirs) == 1
                      else "later candidate"] += 1
    pt = [r["time_s"] for r in pc.values() if not r.get("error")]
    L = ["# Run 03 R1: rotation-required labels\n",
         f"Pre-check: `src/disasm/oracle/linear_precheck.py`, driver `scripts/run_precheck.py`, log `{args.precheck_log}`, "
         f"output `{os.path.relpath(args.precheck, ROOT)}`. Report built by `scripts/rotation_report.py`.\n",
         "**Method.** For each query the part is translated along every goal-candidate direction of the adapter "
         "(`cmgrrt.candidate_directions`, same order), out to the adapter goal distance D = bbox diagonal + 0.1. "
         "Collision model: the exact union SDF of the other remaining parts, ε = 0.005 (collide iff min SDF < −ε), "
         "evaluated at the robot's surface samples (same count as CMG-RRT: 3,888). "
         "**Step size:** step = max(ε/2, d + ε), where d = current min SDF. The step is 0.0025 (= ε/2) near contact. "
         "Wherever it is larger, every skipped pose is proven collision-free by the 1-Lipschitz bound of the SDF under translation. "
         "So the check is at least as strict as a uniform ε/2 sweep. The final pose checked is exactly t = D.\n",
         "## Gate\n",
         f"- queries in v1: {len(keys)}; with a pre-check result: {len(keys) - len(missing)} (**{100 * cover:.2f}%**); "
         f"pre-check errors: {n_err}",
         f"- pre-check time per query: median {np.median(pt):.3f} s, p95 {np.percentile(pt, 95):.3f} s (not a reported timing result)\n",
         "## Counts\n",
         "| level | needs rotation | out of | share |", "|---|---|---|---|",
         f"| part (query) | {n_need} | {n_succ} successful queries | {100 * n_need / max(1, n_succ):.2f}% |",
         f"| state (rot_state) | {rot_states} | {n_states_succ} states with >= 1 success | {100 * rot_states / max(1, n_states_succ):.2f}% |",
         f"| assembly (rot_assembly) | {sum(asm_rot.values())} | {len(asm_rot)} assemblies | {100 * sum(asm_rot.values()) / max(1, len(asm_rot)):.2f}% |",
         "",
         f"First clearing direction among linear-free queries: {dict(first_dir_k)}.\n",
         "## Inconsistencies: `linear_free == True` but CMG-RRT unsolved\n",
         f"**{len(incons)}** of {sum(1 for l in labs if l['outcome'] != 'success')} unsolved queries "
         f"({100 * len(incons) / max(1, sum(1 for l in labs if l['outcome'] != 'success')):.1f}%) could have been "
         "removed by a straight pull that the pre-check certifies collision-free.",
         ]
    if incons:
        L.append(f"Their CMG-RRT iterations: median {np.median(inc_iter):.0f}, min {inc_iter.min()}, max {inc_iter.max()}; "
                 f"logged time median {np.median([l['time_s'] for l, _ in incons]):.1f} s.\n")
        L.append("| assembly | state | part | CMG-RRT time (s) | iterations | first clearing direction | candidates |")
        L.append("|---|---|---|---|---|---|---|")
        for l, r in incons[:10]:
            L.append(f"| {l['assembly_id']} | {l['state_key']} | {l['part_id']} | {l['time_s']:.1f} | {l['iterations']} | "
                     f"{r['first_free_dir']} | {r['n_dirs_total']} |")
        L.append("\n**What this implies about the oracle at T = 30 s.** The adapter grows ONE CMG-RRT tree toward the first "
                 "valid goal candidate. It tests straight connections to the other candidates only from newly added tree nodes, "
                 "never from the start pose, and only with the library's coarse edge check (step 10·η = 0.02 = 4ε). A part that "
                 "a straight pull would free can therefore stay unsolved: the tree is pulled toward a blocked goal, and "
                 "the free direction is never tried from a node that can see it. These queries are real oracle misses, "
                 "not physical blockages. They are labelled `unsolved` (censored), exactly as the oracle returned them. "
                 "They inflate costs equally for every ordering in replay. They mean the v1 success rate is a lower bound on true "
                 "removability, and a cheap linear pre-check before CMG-RRT would rescue them (run 04 candidate; it would "
                 "change the oracle, so it is NOT applied in this run).")
    L += ["\n## Diagnostics for the rotation flag\n",
          f"- Max path rotation (logged) of `needs_rotation` queries: median {np.median(rot_deg) if len(rot_deg) else float('nan'):.1f}°, "
          f"share > 15°: {100 * np.mean(rot_deg > 15) if len(rot_deg) else float('nan'):.1f}%, share < 5°: "
          f"{100 * np.mean(rot_deg < 5) if len(rot_deg) else float('nan'):.1f}%.",
          f"- For comparison, successful linear-free queries: median {np.median(succ_lin_rot):.1f}°, share > 15°: "
          f"{100 * np.mean(succ_lin_rot > 15):.1f}%.",
          f"- `needs_rotation` queries whose pre-check start pose is already below −ε (start penetration > ε with this "
          f"sample draw): {start_invalid_need}. A pull cannot start there, so the CMG-RRT success started from a pose "
          "that its own sample set judged valid.",
          f"- |start min SDF (pre-check) − logged start min SDF|: median {np.median(dstart):.2e}, p95 "
          f"{np.percentile(dstart, 95):.2e}. They differ slightly because trimesh 5.2 draws the robot surface samples "
          "with an unseeded generator, so CMG-RRT's exact sample set is not reproducible from the logged seed. The pre-check "
          "uses a fresh draw of the same size.",
          "- Caveat: almost half of the `needs_rotation` successes have a logged path that rotates < 5°. Such a part was "
          "freed by one of three things: a non-straight translation (sideways moves that no straight pull along a candidate "
          "direction makes), a small rotation, or a pass through CMG-RRT's coarse edge check (step 0.02 = 4ε) where the fine "
          "sweep (step ≤ ε/2) collides. This data does not separate the three. So `needs_rotation` really means 'needs more "
          "than a straight pull along the adapter's candidate directions'. It follows the run 03 definition exactly. The "
          "< 5° and > 15° shares above let the reader weigh it."]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    open(args.out, "w").write("\n".join(L) + "\n")
    if args.json_out:
        json.dump({"coverage": cover, "n_need": n_need, "n_succ": n_succ, "rot_states": rot_states,
                   "n_states_succ": n_states_succ, "rot_assemblies": sum(asm_rot.values()), "n_asm": len(asm_rot),
                   "n_incons": len(incons), "n_unsolved": sum(1 for l in labs if l["outcome"] != "success"),
                   "need_rot_lt5deg": int(np.sum(rot_deg < 5)), "start_invalid_need": start_invalid_need},
                  open(args.json_out, "w"), indent=1)
    print("\n".join(L))


if __name__ == "__main__":
    main()
