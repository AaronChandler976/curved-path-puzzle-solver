#!/usr/bin/env python
"""S4 pilot labelling: assembly-by-disassembly with EVERY remaining part queried at every
visited state (CMG-RRT adapter, src/disasm/oracle/cmgrrt.py).

Per assembly: start at the assembled state; query all present parts (parallel workers); pick
one successful part uniformly at random (random.Random(f"{seed}-{assembly}-{depth}")), remove
it, repeat until one part is left ("complete") or no part succeeds ("stuck"). Unsolved queries
are censored labels (budget exhausted), never "infeasible".

Several assemblies are processed concurrently so the worker pool stays full.
Checkpointing: after every state a line goes to states.jsonl (and its queries to labels.jsonl);
finished assemblies go to summary.jsonl. On restart, finished assemblies are skipped and
unfinished ones resume from their last completed state.
Order: 3-5 part assemblies first (by id), then 6-8. Skipped (logged in summary.jsonl):
non-watertight parts, mesh interpenetration > --max-pen (start pose would be in collision),
no contact pairs at all (floating parts), mesh load errors, or any
obstacle SDF prep > --max-prep-s.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import random
import signal
import subprocess
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
import multiprocessing as mp

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STOP = False


def _sig(*_):
    global STOP
    STOP = True


def qseed(seed, aid, depth, part):
    """Deterministic per-query planner seed (logged with every label)."""
    return int.from_bytes(hashlib.sha1(f"{seed}-{aid}-{depth}-{part}".encode()).digest()[:4], "little")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir", required=True, help="experiments/<date>_pilot_labels")
    ap.add_argument("--labels-dir", default=os.path.join(ROOT, "data/labels/pilot_v0"))
    ap.add_argument("--inspect", default=os.path.join(ROOT, "experiments/2026-11-21_inspect_multi/assemblies.jsonl"))
    ap.add_argument("--T", type=float, required=True, help="per-query timeout (s)")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--concurrent-assemblies", type=int, default=4)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--groups", default="3-5,6-8")
    ap.add_argument("--max-assemblies", type=int, default=100000)
    ap.add_argument("--max-prep-s", type=float, default=120.0)
    ap.add_argument("--scan", required=True, help="contact scan results.jsonl (scripts/scan_contacts.py)")
    ap.add_argument("--max-pen", type=float, default=0.002, help="skip assemblies with deeper mesh interpenetration")
    ap.add_argument("--stop-at", default="", help="ISO time: start no new state after this")
    ap.add_argument("--detector", default="learned", choices=["learned", "exact"],
                    help="exact = run 02 exact union SDF (pilot_v1); learned = run 01 neural SDF (pilot_v0)")
    ap.add_argument("--eps", type=float, default=None, help="contact tolerance (threshold = -eps); default 0.005")
    ap.add_argument("--order-file", default="", help="text file of assembly ids: label these first, in this order")
    ap.add_argument("--only-order", action="store_true", help="label only the ids in --order-file")
    args = ap.parse_args()
    signal.signal(signal.SIGTERM, _sig)
    signal.signal(signal.SIGINT, _sig)
    from disasm.oracle.cmgrrt import load_assembly, contact_graph
    from disasm.oracle import pool as P

    os.makedirs(args.outdir, exist_ok=True)
    from disasm.util.runlog import log_load
    log_load(args.outdir, "start")
    os.makedirs(args.labels_dir, exist_ok=True)
    lab_p = os.path.join(args.labels_dir, "labels.jsonl")
    st_p = os.path.join(args.labels_dir, "states.jsonl")
    sum_p = os.path.join(args.labels_dir, "summary.jsonl")
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    stop_at = dt.datetime.fromisoformat(args.stop_at) if args.stop_at else None

    finished = {json.loads(l)["assembly_id"] for l in open(sum_p)} if os.path.exists(sum_p) else set()
    progress = {}
    if os.path.exists(st_p):
        for l in open(st_p):
            s = json.loads(l)
            progress.setdefault(s["assembly_id"], []).append(s)

    scan = {j["id"]: j for j in map(json.loads, open(args.scan)) if not j.get("error")}
    rows = [json.loads(l) for l in open(args.inspect)]
    order = []
    for g in args.groups.split(","):
        lo, hi = map(int, g.split("-"))
        order += sorted((r for r in rows if lo <= len(r["parts"]) <= hi), key=lambda r: r["id"])
    if args.order_file:
        first = [l.strip() for l in open(args.order_file) if l.strip()]
        byid = {r["id"]: r for r in order}
        rank = {a: i for i, a in enumerate(first)}
        head = [byid[a] for a in first if a in byid]
        order = head if args.only_order else head + [r for r in order if r["id"] not in rank]
    queue = [r for r in order if r["id"] not in finished][: max(0, args.max_assemblies - len(finished))]
    root = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly")
    print(f"{len(finished)} finished, {len(queue)} queued, T={args.T}, git={git}", flush=True)

    def log_summary(d):
        d.update({"T": args.T, "seed": args.seed, "git": git, "timestamp": dt.datetime.now().isoformat()})
        with open(sum_p, "a") as f:
            f.write(json.dumps(d) + "\n")
        print("SUMMARY", json.dumps(d), flush=True)

    P.pin_threads(1)
    os.environ.setdefault("DISASM_SDF_THREADS", "2")
    ex = ProcessPoolExecutor(args.workers, mp_context=mp.get_context("spawn"), initializer=P._init,
                             initargs=({"workdir": os.path.join(args.outdir, "work"), "device": args.device,
                                        "threads": 1},))
    active = {}      # aid -> dict(asm, removed, depth, pending:set(futures), results:list, t0)
    fut2aid = {}
    t_start = time.time()
    nq = 0

    def start_state(aid):
        a = active[aid]
        present = sorted(set(a["asm"].part_ids) - set(a["removed"]))
        a["pending"], a["results"], a["t_state0"] = set(), [], time.time()
        for p in present:
            job = {"asm_dir": a["asm"].dir, "removed": list(a["removed"]), "part": p, "timeout_s": args.T,
                   "seed": qseed(args.seed, aid, a["depth"], p), "assembly_id": aid,
                   "detector": args.detector, "eps": args.eps}
            f = ex.submit(P.run_job, job)
            a["pending"].add(f)
            fut2aid[f] = aid

    while (queue or active) and not STOP:
        while queue and len(active) < args.concurrent_assemblies and not STOP:
            if stop_at and dt.datetime.now(stop_at.tzinfo) > stop_at:
                queue = []
                break
            r = queue.pop(0)
            aid = r["id"]
            if not all(p["watertight"] for p in r["parts"]):
                log_summary({"assembly_id": aid, "status": "skipped", "reason": "non_watertight", "n_parts": len(r["parts"])})
                continue
            sc = scan.get(aid)
            if sc is None:
                continue  # not scanned (yet); not logged, may be labelled by a later run
            if sc["max_penetration"] > args.max_pen:
                log_summary({"assembly_id": aid, "status": "skipped", "n_parts": len(r["parts"]),
                             "reason": f"mesh_interpenetration {sc['max_penetration']:.4f} > {args.max_pen}"})
                continue
            try:
                asm = load_assembly(os.path.join(root, aid))
                npairs = len(contact_graph(asm)["pairs"])
            except Exception as e:  # noqa: BLE001
                log_summary({"assembly_id": aid, "status": "skipped", "reason": f"load_error: {e}", "n_parts": len(r["parts"])})
                continue
            if npairs == 0:
                log_summary({"assembly_id": aid, "status": "skipped", "reason": "no_contacts", "n_parts": len(asm.part_ids)})
                continue
            prev = sorted(progress.get(aid, []), key=lambda s: s["depth"])
            removed, depth = [], 0
            if prev:
                last = prev[-1]
                removed, depth = last["removed"] + [last["chosen"]], last["depth"] + 1
            active[aid] = {"asm": asm, "removed": removed, "depth": depth, "t0": time.time(),
                           "n_states": len(prev), "n_queries": sum(s["n_queries"] for s in prev),
                           "planner_s": sum(s["planner_s"] for s in prev)}
            if len(asm.part_ids) - len(removed) <= 1:
                pass  # finished but summary missing; handled below
            start_state(aid)
        if not fut2aid:
            break
        done, _ = wait(list(fut2aid), return_when=FIRST_COMPLETED, timeout=60)
        for f in done:
            aid = fut2aid.pop(f)
            a = active[aid]
            a["pending"].discard(f)
            a["results"].append(f.result())
            nq += 1
            if a["pending"]:
                continue
            # ---- state complete: write labels, choose next part
            present = sorted(set(a["asm"].part_ids) - set(a["removed"]))
            skey = "-".join(map(str, present))
            ts = dt.datetime.now().isoformat()
            res = sorted(a["results"], key=lambda r: r["part_id"])
            with open(lab_p, "a") as lf:
                for r in res:
                    lab = {"assembly_id": aid, "state_key": skey, "removed": a["removed"], "depth": a["depth"],
                           "n_present": len(present), "n_parts": len(a["asm"].part_ids), "part_id": r["part_id"],
                           "outcome": r["outcome"], "time_s": r.get("time_s"), "iterations": r.get("iterations"),
                           "goal_candidate": r.get("escape_dir"), "escape_vec": r.get("escape_vec"),
                           "n_goal_candidates_tried": r.get("n_goal_candidates_tried"),
                           "prep_s": r.get("prep_s"), "sdf_train_s": r.get("sdf_train_s"),
                           "start_min_sdf": r.get("start_min_sdf"), "sdf_sign_agreement": r.get("sdf_sign_agreement"),
                           "path_max_rot_deg": r.get("path_max_rot_deg"), "path_file": r.get("path_file"),
                           "error": r.get("error"), "seed": r.get("seed"), "T": args.T, "device": args.device,
                           "sdf_file": os.path.basename(r.get("sdf_path") or ""), "start_valid": r.get("start_valid"),
                           "sdf_p95_err": r.get("sdf_p95_err"),
                           "detector": r.get("detector", args.detector), "epsilon": r.get("epsilon"),
                           "setup_time_s": (sum(r["part_setup_s_first"].values()) / len(r["part_setup_s_first"])
                                            if r.get("part_setup_s_first") else r.get("sdf_train_s")),
                           "part_setup_s_first": r.get("part_setup_s_first"), "union_build_s": r.get("union_build_s"),
                           "worker_wall_s": r.get("worker_wall_s"),
                           "git_hash": git, "timestamp": ts}
                    lf.write(json.dumps(lab) + "\n")
            succ = [r["part_id"] for r in res if r["outcome"] == "success"]
            slow = [r["part_id"] for r in res if (r.get("sdf_train_s") or 0) > args.max_prep_s]
            chosen = random.Random(f"{args.seed}-{aid}-{a['depth']}").choice(succ) if succ else None
            planner_s = sum(r.get("time_s") or 0 for r in res)
            st = {"assembly_id": aid, "depth": a["depth"], "removed": a["removed"], "state_key": skey,
                  "n_queries": len(res), "n_success": len(succ), "successes": succ, "chosen": chosen,
                  "planner_s": planner_s, "wall_s": time.time() - a["t_state0"],
                  "errors": [r["part_id"] for r in res if r.get("error")], "slow_prep": slow,
                  "choice_rng": f"random.Random('{args.seed}-{aid}-{a['depth']}')", "timestamp": ts}
            with open(st_p, "a") as sf:
                sf.write(json.dumps(st) + "\n")
            a["n_states"] += 1
            a["n_queries"] += len(res)
            a["planner_s"] += planner_s
            print(f"[{(time.time() - t_start) / 60:6.1f} min] {aid} depth {a['depth']} present={len(present)} "
                  f"succ={succ} chosen={chosen} planner={planner_s:.0f}s wall={st['wall_s']:.0f}s total_q={nq}", flush=True)
            base = {"assembly_id": aid, "n_parts": len(a["asm"].part_ids), "n_states": a["n_states"],
                    "n_queries": a["n_queries"], "planner_s": a["planner_s"], "wall_s": time.time() - a["t0"]}
            if slow:
                log_summary({**base, "status": "skipped", "reason": f"obstacle_prep_gt_{args.max_prep_s:.0f}s", "slow_parts": slow})
                del active[aid]
            elif chosen is None:
                log_summary({**base, "status": "stuck", "removed": a["removed"]})
                del active[aid]
            elif len(present) - 1 <= 1:
                log_summary({**base, "status": "complete", "removed": a["removed"] + [chosen]})
                del active[aid]
            elif STOP or (stop_at and dt.datetime.now(stop_at.tzinfo) > stop_at):
                del active[aid]   # resumable from states.jsonl
            else:
                a["removed"] = a["removed"] + [chosen]
                a["depth"] += 1
                start_state(aid)
    log_load(args.outdir, "end")
    print(f"LABEL RUN EXIT stop={STOP} queries_this_run={nq} wall={time.time() - t_start:.0f}s", flush=True)
    ex.shutdown(wait=False, cancel_futures=True)
    # terminate pool workers explicitly: os._exit skips executor cleanup, and orphaned workers would keep
    # holding their planner slots (found in run 02 R3 dev test; see reports/run02/DECISIONS.md #10)
    for pr in list(getattr(ex, "_processes", {}).values()):
        try:
            pr.terminate()
        except Exception:  # noqa: BLE001
            pass
    os._exit(0)


if __name__ == "__main__":
    main()
