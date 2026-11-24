#!/usr/bin/env python
"""R6 (run 03): live full-disassembly evaluation with FRESH CMG-RRT queries (exact union SDF, eps 0.005, T = 30 s).

For each (assembly, method): start at the assembled state; the method orders the present parts; query them in that order
with CMG-RRT until one succeeds; remove it; repeat until one part is left ("complete") or every present part is
unsolved ("stuck"). Planner seed per query = sha1(assembly, state_key, part) -> the same query gets the same seed under
every method. (trimesh draws the robot surface samples with an unseeded generator, so the same query is still not
bit-identical across methods; see reports/run03/DECISIONS.md.)

Methods: random (order = random.Random(sha1(aid, state_key)) shuffle), fewest_contacts (ties: outside-in, part id),
asap (released weights, zero-shot), gnn_surv (p/c, one checkpoint chosen on val).
Jobs are interleaved per assembly (a1: m1..m4, a2: m1..m4, ...). <= --workers worker processes, each holding one planner
slot (disasm.util.slots) for its lifetime. Resumable: finished (assembly, method) pairs in results.jsonl are skipped.

Run 04 additions:
- seeded robot sampling (cmgrrt.query default): the same query is reproducible across methods (up to the wall-clock T).
- idle guard (CLAUDE.md Run 04 rules): refuses to start while other planner slots are held; waits for 5 min non-busy;
  every worker waits for non-busy before dispatching each query; each query stores busy_frac / confounded; a run
  (assembly, method) is confounded if any of its queries is. Confounded runs are re-run at the end with the same seeds
  (up to --max-reruns = 2). Every attempt is a line in results.jsonl (field "attempt"); reports use the first clean
  attempt per (assembly, method), else attempt 0 flagged. The re-run unit is the whole disassembly because a re-run
  query inside it could change the trajectory.
- --oracle v2: straight-pull pre-check -> CMG-RRT (src/disasm/oracle/oracle_v2.py); default v1 = CMG-RRT only.
"""
import argparse
import hashlib
import json
import multiprocessing as mp
import os
import random
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly")
METHODS = ["random", "fewest_contacts", "asap", "gnn_surv"]
_W = {}


def qseed(aid, skey, part, prefix="run03-live"):
    return int.from_bytes(hashlib.sha1(f"{prefix}-{aid}-{skey}-{part}".encode()).digest()[:4], "little")


def _init(cfg):
    from disasm.oracle import pool as P
    P._init(cfg)                       # planner slot + 1 thread
    _W.update(cfg)


def _gnn():
    if "gnn" not in _W:
        import torch
        from disasm.models.ranker3 import Ranker3
        from disasm.data.graph import NODE_DIM, EDGE_DIM_V3
        ck = torch.load(_W["gnn_ckpt"], weights_only=False, map_location="cpu")
        c = ck["cfg"]
        m = Ranker3(c["enc"], NODE_DIM, EDGE_DIM_V3, c["head"], h=c["hidden"], layers=c["layers"], dropout=c["dropout"], K=8, T=30.0)
        m.load_state_dict(ck["state_dict"]); m.eval()
        _W["gnn"] = (m, ck["norm"])
    return _W["gnn"]


def _asap():
    if "asap" not in _W:
        from disasm.search.asap_baseline import load_asap_model
        _W["asap"] = load_asap_model()[0]
    return _W["asap"]


def order_parts(method, asm, present, aid, skey, cache):
    import torch
    from disasm.data.graph import state_graph_v3
    pres, X, ei, ea = state_graph_v3(asm, present)
    info = {}
    if method == "random":
        o = list(pres)
        random.Random(hashlib.sha1(f"run03-live-random-{aid}-{skey}".encode()).hexdigest()).shuffle(o)
        return o, info
    if method == "fewest_contacts":
        idx = sorted(range(len(pres)), key=lambda i: (X[i, 9], -X[i, 8], pres[i]))
        return [pres[i] for i in idx], info
    if method == "asap":
        from disasm.search.asap_baseline import asap_contact_pairs, asap_node_inputs, asap_scores
        if "asap_in" not in cache:
            cache["asap_in"] = (asap_contact_pairs(asm), asap_node_inputs(os.path.join(RAW, aid), aid))
        pairs, ni = cache["asap_in"]
        s = asap_scores(_asap(), ni, pairs, pres)
        info["score"] = dict(zip(pres, map(float, s)))
        idx = np.lexsort((np.arange(len(pres)), -s))
        return [pres[i] for i in idx], info
    if method == "gnn_surv":
        m, (mu, sd, emu, esd) = _gnn()
        with torch.no_grad():
            x = (torch.tensor(X) - mu) / sd
            e = (torch.tensor(ea) - emu) / esd
            p, c = m.predict(m(x, torch.tensor(ei), e))
        p, c = p.numpy(), c.numpy()
        s = p / np.maximum(c, 1e-3)
        info["p"] = dict(zip(pres, map(float, p))); info["c"] = dict(zip(pres, map(float, c)))
        idx = np.lexsort((np.arange(len(pres)), -s))
        return [pres[i] for i in idx], info
    raise ValueError(method)


def _query(job, asm, removed, p, seed):
    from disasm.oracle.cmgrrt import query
    if job.get("oracle", "v1") == "v2":
        from disasm.oracle.oracle_v2 import query_v2
        return query_v2(asm, set(removed), p, job["T"], seed, job["workdir"], eps=job["eps"], always_cmgrrt=False,
                        save_path=job.get("save_paths", False), allowance=job.get("allowance"))
    return query(asm, set(removed), p, job["T"], seed, job["workdir"], device="cpu",
                 detector="exact", eps=job["eps"], save_path=job.get("save_paths", False),
                 allowance=job.get("allowance"))


def run_abd(job):
    import traceback
    from disasm.oracle.cmgrrt import load_assembly
    from disasm.util.idle_guard import IdleClient, SAMPLE_S
    client = IdleClient(job["guard_dir"]) if job.get("guard_dir") else None
    aid, method = job["aid"], job["method"]
    t_wall0 = time.time()
    out = {"assembly_id": aid, "method": method, "states": [], "error": None}
    try:
        asm = load_assembly(os.path.join(RAW, aid))
        cache, removed = {}, []
        planner_s = prep_s = order_s = busy_wait_s = 0.0
        calls = 0
        while True:
            present = sorted(set(asm.part_ids) - set(removed))
            if len(present) <= 1:
                out["status"] = "complete"
                break
            skey = "-".join(map(str, present))
            t0 = time.time()
            order, info = order_parts(method, asm, present, aid, skey, cache)
            o_s = time.time() - t0
            order_s += o_s
            st = {"state_key": skey, "order": order, "order_s": o_s, "queries": [], **info}
            chosen = None
            for p in order:
                w = client.wait_not_busy() if client else 0.0
                busy_wait_s += w
                tq0 = time.time()
                r = _query(job, asm, removed, p, qseed(aid, skey, p, job.get("seed_prefix", "run03-live")))
                tq1 = time.time()
                calls += 1
                planner_s += r["time_s"] or 0.0
                prep_s += r.get("prep_s") or 0.0
                st["queries"].append({"part": p, "outcome": r["outcome"], "time_s": r["time_s"], "iterations": r["iterations"],
                                      "prep_s": r.get("prep_s"), "seed": r["seed"], "error": r["error"],
                                      "escape_dir": r.get("escape_dir"), "path_max_rot_deg": r.get("path_max_rot_deg"),
                                      "path_file": r.get("path_file"), "t_query_start": tq0, "t_query_end": tq1,
                                      "busy_wait_s": w, "robot_sample_seed": r.get("robot_sample_seed"),
                                      "tree_hash": r.get("tree_hash"),
                                      **{k: r.get(k) for k in ("stage", "precheck_free", "precheck_time_s",
                                                               "cmgrrt_outcome", "cmgrrt_time_s") if k in r}})
                if r["outcome"] == "success":
                    chosen = p
                    break
            st["chosen"] = chosen
            out["states"].append(st)
            if chosen is None:
                out["status"] = "stuck"
                break
            removed.append(chosen)
        out.update({"planner_s": planner_s, "prep_s": prep_s, "order_s": order_s, "calls": calls,
                    "n_parts": len(asm.part_ids), "removed": removed, "busy_wait_s": busy_wait_s})
        if client is not None:
            qs = [q for st in out["states"] for q in st["queries"]]
            if qs:   # wait until a 5 s sample covers the last query, then score every query
                while time.time() < qs[-1]["t_query_end"] + SAMPLE_S + 1.0:
                    time.sleep(0.5)
            for q in qs:
                q["busy_frac"], q["busy_samples"] = client.busy_frac(q["t_query_start"], q["t_query_end"])
                q["confounded"] = q["busy_frac"] > 0
            out["n_confounded_queries"] = sum(q["confounded"] for q in qs)
            out["confounded"] = out["n_confounded_queries"] > 0
            out["busy_frac"] = (sum(q["busy_frac"] * (q["t_query_end"] - q["t_query_start"]) for q in qs)
                                / max(1e-9, sum(q["t_query_end"] - q["t_query_start"] for q in qs))) if qs else 0.0
    except Exception as e:  # noqa: BLE001
        out["error"] = f"{type(e).__name__}: {e}"
        out["traceback"] = traceback.format_exc()
    out["wall_s"] = time.time() - t_wall0          # setup + ordering + planner, this (assembly, method)
    out["worker_pid"] = os.getpid()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--assemblies", required=True, help="json list of test assembly ids (the R6 sample)")
    ap.add_argument("--gnn-ckpt", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--methods", default=",".join(METHODS))
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--T", type=float, default=30.0)
    ap.add_argument("--eps", type=float, default=0.005)
    ap.add_argument("--save-paths", action="store_true")
    ap.add_argument("--oracle", default="v1", choices=["v1", "v2"])
    ap.add_argument("--seed-prefix", default="run03-live", help="planner seed = sha1(prefix, assembly, state, part)")
    ap.add_argument("--idle-wait", type=float, default=300.0, help="s of non-busy before the first query (0 = none)")
    ap.add_argument("--max-reruns", type=int, default=2)
    ap.add_argument("--no-guard", action="store_true", help="DEV ONLY: no idle guard")
    ap.add_argument("--allowance-file", default="", help="json {assembly_id: {pair: allowance}} (run 04 T6)")
    args = ap.parse_args()
    from disasm.oracle import pool as P
    from disasm.util.runlog import log_load
    from disasm.util.slots import slots_in_use
    from disasm.util.idle_guard import IdleSampler
    os.makedirs(args.outdir, exist_ok=True)
    held = slots_in_use()
    if held:
        print(f"REFUSING TO START: {held} planner slots are held by another job (CLAUDE.md)", flush=True)
        sys.exit(2)
    log_load(args.outdir, "start")
    guard = None
    if not args.no_guard:
        guard = IdleSampler(args.outdir, tag="live_abd").start()
        if args.idle_wait > 0:
            print(f"waiting for {args.idle_wait:.0f} s non-busy ...", flush=True)
            guard.wait_idle(args.idle_wait, log=lambda m: print(m, flush=True))
    res_p = os.path.join(args.outdir, "results.jsonl")
    attempts = {}
    if os.path.exists(res_p):
        for l in open(res_p):
            r = json.loads(l)
            attempts.setdefault((r["assembly_id"], r["method"]), []).append(r)
    aids = json.load(open(args.assemblies))
    methods = args.methods.split(",")
    base = {"T": args.T, "eps": args.eps, "workdir": os.path.join(args.outdir, "work"), "save_paths": args.save_paths,
            "oracle": args.oracle, "seed_prefix": args.seed_prefix,
            "guard_dir": None if args.no_guard else os.path.abspath(args.outdir)}
    allow = json.load(open(args.allowance_file)) if args.allowance_file else {}
    jobs = [{**base, "aid": a, "method": m, "attempt": 0, "allowance": allow.get(a)} for a in aids for m in methods
            if (a, m) not in attempts]
    print(f"{len(jobs)} (assembly, method) runs to do, {len(attempts)} done; workers {args.workers}", flush=True)
    P.pin_threads(1)
    ex = ProcessPoolExecutor(args.workers, mp_context=mp.get_context("spawn"), initializer=_init,
                             initargs=({"workdir": os.path.join(args.outdir, "work"), "device": "cpu", "threads": 1,
                                        "slot_tag": "live_abd", "gnn_ckpt": os.path.abspath(args.gnn_ckpt)},))
    t0 = time.time()
    n = 0

    def run_all(jobs, label):
        nonlocal n
        pending = set()
        queue = list(jobs)
        fut_job = {}
        with open(res_p, "a") as f:
            while queue or pending:
                while queue and len(pending) < args.workers:
                    j = queue.pop(0)
                    fu = ex.submit(run_abd, j)
                    fut_job[fu] = j
                    pending.add(fu)
                fin, pending = wait(pending, return_when=FIRST_COMPLETED)
                for fu in fin:
                    r = fu.result()
                    r["attempt"] = fut_job.pop(fu)["attempt"]
                    f.write(json.dumps(r) + "\n"); f.flush()
                    attempts.setdefault((r["assembly_id"], r["method"]), []).append(r)
                    n += 1
                    print(f"[{(time.time() - t0) / 60:6.1f} min] {label} {n} {r['assembly_id']} {r['method']:16s} "
                          f"{r.get('status')} planner={r.get('planner_s', 0):.1f}s calls={r.get('calls')} "
                          f"wall={r['wall_s']:.1f}s conf={r.get('confounded')} busy_frac={r.get('busy_frac')} "
                          f"err={r['error']}", flush=True)

    run_all(jobs, "main")
    if guard is not None:
        for rnd in range(1, args.max_reruns + 1):
            rj = [{**base, "aid": a, "method": m, "attempt": rnd, "allowance": allow.get(a)} for (a, m), atts in attempts.items()
                  if a in aids and m in methods and len(atts) == rnd and all(x.get("confounded", True) for x in atts)]
            print(f"RERUN round {rnd}: {len(rj)} confounded runs", flush=True)
            if not rj:
                break
            run_all(rj, f"rerun{rnd}")
    ex.shutdown(wait=True)
    if guard is not None:
        guard.stop()
    log_load(args.outdir, "end")
    print(f"LIVE EXIT runs={n} wall={time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
