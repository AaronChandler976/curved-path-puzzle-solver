#!/usr/bin/env python
"""S3 gate: query EVERY part of each selected assembly at the assembled state through the
CMG-RRT adapter (src/disasm/oracle/cmgrrt.py) and log every call.

Selection is deterministic: the first --n assemblies (sorted by id) from the inspection list
with --min-parts..--max-parts parts, all parts watertight, and at least one contact pair
(assemblies whose parts do not touch at all, like 00013, are skipped and logged).
Resumable: (assembly, part) pairs already in results.jsonl are skipped.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--inspect", default=os.path.join(ROOT, "experiments/2026-11-21_inspect_multi/assemblies.jsonl"))
    ap.add_argument("--ids", default="", help="comma list of assembly ids (overrides selection)")
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--min-parts", type=int, default=3)
    ap.add_argument("--max-parts", type=int, default=6)
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    from disasm.oracle.cmgrrt import load_assembly, contact_graph
    from disasm.oracle.pool import make_pool
    os.makedirs(args.outdir, exist_ok=True)
    res_path = os.path.join(args.outdir, "results.jsonl")
    sel_path = os.path.join(args.outdir, "selection.jsonl")
    root = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly")
    rows = [json.loads(l) for l in open(args.inspect)]
    if args.ids:
        cand = [r for r in rows if r["id"] in args.ids.split(",")]
    else:
        cand = sorted((r for r in rows if args.min_parts <= len(r["parts"]) <= args.max_parts
                       and all(p["watertight"] for p in r["parts"])), key=lambda r: r["id"])
    chosen = []
    with open(sel_path, "a") as sf:
        for r in cand:
            if len(chosen) >= args.n:
                break
            a = load_assembly(os.path.join(root, r["id"]))
            npairs = len(contact_graph(a)["pairs"])
            ok = npairs > 0
            sf.write(json.dumps({"id": r["id"], "n_parts": len(a.part_ids), "contact_pairs": npairs,
                                 "selected": ok, "reason": None if ok else "no_contacts"}) + "\n")
            if ok:
                chosen.append(a)
    done = set()
    if os.path.exists(res_path):
        for l in open(res_path):
            j = json.loads(l)
            done.add((j["assembly_id"], j["part_id"]))
    jobs = [{"asm_dir": a.dir, "removed": [], "part": p, "timeout_s": args.timeout, "seed": args.seed,
             "assembly_id": a.id} for a in chosen for p in a.part_ids if (a.id, p) not in done]
    print(f"{len(chosen)} assemblies {[a.id for a in chosen]}, {len(jobs)} queries", flush=True)
    pool = make_pool(args.workers, os.path.join(args.outdir, "work"), device=args.device)
    t0 = time.time()
    with open(res_path, "a") as f:
        for r in pool.imap_unordered(__import__("disasm.oracle.pool", fromlist=["run_job"]).run_job, jobs):
            r.pop("traceback", None) if r.get("error") is None else None
            f.write(json.dumps(r) + "\n")
            f.flush()
            print(f"[{time.time() - t0:7.1f}s] {r.get('assembly_id')} part {r.get('part_id')}: {r['outcome']} "
                  f"t={r.get('time_s', 0):.1f}s it={r.get('iterations')} prep={r.get('prep_s', 0):.1f}s "
                  f"dir={r.get('escape_dir')} start_sdf={r.get('start_min_sdf')} err={r.get('error')}", flush=True)
    pool.close()
    pool.join()
    print("ORACLE CHECK DONE", flush=True)


if __name__ == "__main__":
    main()
