#!/usr/bin/env python
"""Run 05: one graph per labelled pilot_v2 state, for the requested splits ONLY (default train,val).

The test split's labels are never read unless --splits includes "test", and that is refused unless the marker
data/splits/.v2_test_evaluated exists (campaign Phase 3 writes it at the first read of test labels).

Per state (complete query set: every present part has a label without error):
  aid, skey, depth, n_parts, source, present (sorted), x (n,18), ei (2,E), ea (E,5)     [model inputs: x, ei, ea]
  MAIN config ("pre-check -> CMG-RRT", docs/PREREG_run05.md §0):
    succ (n,) bool, time_s (n,) = precheck_time_s + (cmgrrt_time_s if the pull did not clear), cens_t = min(time_s, T)
  SECONDARY config ("CMG-RRT only"): succ_cm (n,), time_cm (n,) = cmgrrt_time_s
  chosen = the part removed at this state (states.jsonl; ASAP's one-positive target), T
  EVAL-ONLY (never model inputs): pre_free (n,), needs_rot (n,) = main success & no free straight pull,
  rot_state = any(needs_rot), confounded (n,) (label still confounded after re-runs)
Optional --clouds: per-part point clouds (src/disasm/data/pointcloud.py, 1,024 x 6, seed 0) for every assembly in the
requested splits -> <out-dir>/clouds_<splits>.pt {aid: {part: tensor}}.
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly")
MARKER = os.path.join(ROOT, "data/splits/.v2_test_evaluated")


def main_cost(q):
    pre = bool(q.get("precheck_free"))
    return (q.get("precheck_time_s") or 0.0) + (0.0 if pre else (q.get("cmgrrt_time_s") or 0.0))


def _build_one(args):
    aid, states, chosen, source, want_clouds = args
    import torch
    from disasm.oracle.cmgrrt import load_assembly
    from disasm.data.graph import state_graph_v3
    asm = load_assembly(os.path.join(RAW, aid))
    graphs, skipped = [], Counter()
    for skey, qs in states:
        present = [int(x) for x in skey.split("-")]
        by = {q["part_id"]: q for q in qs}
        if sorted(by) != sorted(present):
            skipped["incomplete"] += 1
            continue
        if any(q.get("error") for q in qs):
            skipped["error"] += 1
            continue
        pres, X, ei, ea = state_graph_v3(asm, present)
        T = float(qs[0]["T"])
        succ = np.array([by[p]["outcome"] == "success" for p in pres])
        t = np.array([main_cost(by[p]) for p in pres], dtype=np.float32)
        assert np.allclose(t, [float(by[p]["time_s"] or 0.0) for p in pres], atol=1e-4), (aid, skey)
        scm = np.array([by[p].get("cmgrrt_outcome") == "success" for p in pres])
        tcm = np.array([float(by[p].get("cmgrrt_time_s") or 0.0) for p in pres], dtype=np.float32)
        pre = np.array([bool(by[p].get("precheck_free")) for p in pres])
        needs = succ & ~pre
        graphs.append({"aid": aid, "skey": skey, "depth": int(qs[0]["depth"]), "n_parts": len(asm.part_ids),
                       "source": source, "present": pres, "x": torch.tensor(X), "ei": torch.tensor(ei),
                       "ea": torch.tensor(ea), "succ": torch.tensor(succ), "time_s": torch.tensor(t),
                       "cens_t": torch.tensor(np.minimum(t, T)), "succ_cm": torch.tensor(scm),
                       "time_cm": torch.tensor(tcm), "chosen": chosen.get(skey), "T": T,
                       "pre_free": torch.tensor(pre), "needs_rot": torch.tensor(needs), "rot_state": bool(needs.any()),
                       "confounded": torch.tensor([bool(by[p].get("confounded")) for p in pres])})
    clouds = None
    if want_clouds:
        from disasm.data.pointcloud import assembly_clouds
        clouds = {p: torch.tensor(v) for p, v in assembly_clouds(asm).items()}
    return aid, graphs, skipped, clouds


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--labels-dir", default=os.path.join(ROOT, "data/labels/pilot_v2"))
    ap.add_argument("--split", default=os.path.join(ROOT, "data/splits/v2_split.json"))
    ap.add_argument("--splits", default="train,val")
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "data/processed/run05"))
    ap.add_argument("--clouds", action="store_true")
    ap.add_argument("--procs", type=int, default=10)
    a = ap.parse_args()
    import torch
    which = a.splits.split(",")
    if "test" in which and not os.path.exists(MARKER):
        raise SystemExit("refusing to read v2 test labels: marker data/splits/.v2_test_evaluated is absent")
    sp = json.load(open(a.split))
    keep = {aid: k for k in which for aid in sp[k]}
    states = defaultdict(lambda: defaultdict(list))
    n = 0
    def aid_of(line):          # assembly id from the raw line, so other splits' records are never parsed
        return line.split('"assembly_id": "', 1)[1][:5]

    for l in open(os.path.join(a.labels_dir, "labels.jsonl")):
        if aid_of(l) not in keep:
            continue
        r = json.loads(l)
        n += 1
        states[r["assembly_id"]][r["state_key"]].append(r)
    chosen = defaultdict(dict)
    for l in open(os.path.join(a.labels_dir, "states.jsonl")):
        if aid_of(l) not in keep:
            continue
        r = json.loads(l)
        if True:
            chosen[r["assembly_id"]][r["state_key"]] = r.get("chosen")
    jobs = [(aid, sorted(st.items()), chosen[aid], sp["sources"].get(aid, "v1"), a.clouds) for aid, st in sorted(states.items())]
    with mp.get_context("spawn").Pool(a.procs) as pool:
        res = pool.map(_build_one, jobs, chunksize=4)
    os.makedirs(a.out_dir, exist_ok=True)
    tag = "_".join(which)
    graphs = [g for _, gs, _, _ in res for g in gs]
    skipped = sum((s for _, _, s, _ in res), Counter())
    for g in graphs:
        g["split"] = keep[g["aid"]]
    torch.save(graphs, os.path.join(a.out_dir, f"graphs_{tag}.pt"))
    if a.clouds:
        torch.save({aid: c for aid, _, _, c in res}, os.path.join(a.out_dir, f"clouds_{tag}.pt"))
    summ = {"splits": which, "queries_read": n, "assemblies": len(jobs), "states": len(graphs),
            "states_with_success": sum(int(g["succ"].any()) for g in graphs), "skipped_states": dict(skipped),
            "per_split": {k: {"assemblies": len({g["aid"] for g in graphs if g["split"] == k}),
                              "states": sum(g["split"] == k for g in graphs),
                              "states_with_success": sum(int(g["succ"].any()) for g in graphs if g["split"] == k),
                              "queries": sum(len(g["present"]) for g in graphs if g["split"] == k)} for k in which}}
    json.dump(summ, open(os.path.join(a.out_dir, f"summary_{tag}.json"), "w"), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
