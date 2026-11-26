#!/usr/bin/env python
"""Assembly-by-disassembly labelling with EVERY remaining part queried at every visited state.

Per assembly: start at the assembled state; query all present parts (parallel workers); pick one successful part
uniformly at random (random.Random(f"{seed}-{assembly}-{depth}")), remove it, repeat until one part is left
("complete") or no part succeeds ("stuck"). Unsolved queries are censored labels (budget exhausted), never
"infeasible".

Oracles: ``--oracle v1`` = CMG-RRT adapter only (pilot_v0/v1); ``--oracle v2`` = run 04 oracle (straight-pull pre-check
and CMG-RRT, both always run for labels; a query "succeeds" under v2 if either stage succeeds; see
src/disasm/oracle/oracle_v2.py). With v2 the removal choice uses the v2 success set.

Run 04 timing hygiene (CLAUDE.md "Run 04 rules", src/disasm/util/idle_guard.py):
- refuses to start if any planner slot is held by another job;
- waits for 5 min of non-busy before the first query (``--idle-wait``);
- dispatches a new query only while the machine is non-busy;
- every attempt gets ``busy_frac`` (fraction of 5 s samples overlapping it that were busy) and ``confounded``;
- after the main pass, confounded queries are re-run with the same seed (up to ``--max-reruns`` = 2 times). Every
  attempt is kept in ``attempts.jsonl``; ``labels.jsonl`` (written by the consolidation step at the end, or with
  ``--consolidate-only``) uses the first clean attempt, else attempt 0 flagged ``confounded``.
  The visited trajectory (removal choices) is fixed by attempt 0, whose success was planner-verified.

Checkpointing: states.jsonl (one line per finished state) and summary.jsonl (finished assemblies). On restart, finished
assemblies are skipped and unfinished ones resume from their last completed state; re-runs already in attempts.jsonl
are not repeated. Skipped assemblies (logged in summary.jsonl): non-watertight parts, mesh interpenetration > --max-pen
(unless --allowance-file gives the assembly a per-pair allowance), no contact pairs, mesh load errors.
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
# result keys copied into every label record (v1 keys first; v2 adds its own, see oracle_v2.LABEL_KEYS)
V1_KEYS = ["outcome", "time_s", "iterations", "n_goal_candidates_tried", "prep_s", "sdf_train_s", "start_min_sdf",
           "sdf_sign_agreement", "path_max_rot_deg", "path_file", "error", "seed", "start_valid", "sdf_p95_err",
           "epsilon", "part_setup_s_first", "union_build_s", "worker_wall_s", "robot_sample_seed", "tree_nodes",
           "t_query_start", "t_query_end"]


def _sig(*_):
    global STOP
    STOP = True


def qseed(seed, aid, depth, part):
    """Deterministic per-query planner seed (logged with every label)."""
    return int.from_bytes(hashlib.sha1(f"{seed}-{aid}-{depth}-{part}".encode()).digest()[:4], "little")


def is_success(r, oracle):
    return r.get("outcome") == "success"


def consolidate(labels_dir):
    """attempts.jsonl -> labels.jsonl: per (assembly, state, part) the first clean attempt, else attempt 0 (flagged)."""
    att_p = os.path.join(labels_dir, "attempts.jsonl")
    by = {}
    order = []
    for l in open(att_p):
        a = json.loads(l)
        k = (a["assembly_id"], a["state_key"], a["part_id"])
        if k not in by:
            by[k] = []
            order.append(k)
        by[k].append(a)
    n_conf = n_rerun_fixed = 0
    tmp = os.path.join(labels_dir, "labels.jsonl.tmp")
    with open(tmp, "w") as f:
        for k in order:
            atts = sorted(by[k], key=lambda a: a["attempt"])
            clean = [a for a in atts if not a["confounded"]]
            pick = clean[0] if clean else atts[0]
            rec = dict(pick)
            rec["n_attempts"] = len(atts)
            rec["label_attempt"] = pick["attempt"]
            rec["attempt0_outcome"] = atts[0]["outcome"]
            rec["still_confounded"] = not clean
            n_conf += (not clean)
            n_rerun_fixed += bool(clean) and pick["attempt"] > 0
            f.write(json.dumps(rec) + "\n")
    os.replace(tmp, os.path.join(labels_dir, "labels.jsonl"))
    return {"queries": len(order), "still_confounded": n_conf, "fixed_by_rerun": n_rerun_fixed}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", required=True, help="experiments/<date>_<name>")
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
    ap.add_argument("--allowance-file", default="", help="json {assembly_id: {pair: allowance}} (run 04 T6); "
                    "assemblies listed here bypass --max-pen and use per-pair allowances")
    ap.add_argument("--source-file", default="", help="json {assembly_id: source label} recorded in every label")
    ap.add_argument("--stop-at", default="", help="ISO time: start no new state after this")
    ap.add_argument("--detector", default="learned", choices=["learned", "exact"],
                    help="exact = run 02 exact union SDF (pilot_v1); learned = run 01 neural SDF (pilot_v0)")
    ap.add_argument("--oracle", default="v1", choices=["v1", "v2"])
    ap.add_argument("--eps", type=float, default=None, help="contact tolerance (threshold = -eps); default 0.005")
    ap.add_argument("--order-file", default="", help="text file of assembly ids: label these first, in this order")
    ap.add_argument("--only-order", action="store_true", help="label only the ids in --order-file")
    ap.add_argument("--idle-wait", type=float, default=300.0, help="s of non-busy required before the first query "
                    "(0 = no wait; dev only, then every timing is flagged by busy_frac anyway)")
    ap.add_argument("--max-reruns", type=int, default=2)
    ap.add_argument("--no-guard", action="store_true", help="DEV ONLY: no idle sampler (busy_frac = null)")
    ap.add_argument("--consolidate-only", action="store_true")
    args = ap.parse_args()
    if args.consolidate_only:
        print(json.dumps(consolidate(args.labels_dir)))
        return
    signal.signal(signal.SIGTERM, _sig)
    signal.signal(signal.SIGINT, _sig)
    from disasm.oracle.cmgrrt import load_assembly, contact_graph
    from disasm.oracle import pool as P
    from disasm.util.runlog import log_load
    from disasm.util.slots import slots_in_use
    from disasm.util.idle_guard import IdleSampler, IdleClient, SAMPLE_S

    os.makedirs(args.outdir, exist_ok=True)
    held = slots_in_use()
    if held:
        print(f"REFUSING TO START: {held} planner slots are held by another job (CLAUDE.md)", flush=True)
        sys.exit(2)
    log_load(args.outdir, "start")
    guard = client = None
    if not args.no_guard:
        guard = IdleSampler(args.outdir, tag="label_abd").start()
        client = IdleClient(args.outdir)
        if args.idle_wait > 0:
            print(f"waiting for {args.idle_wait:.0f} s non-busy ...", flush=True)
            guard.wait_idle(args.idle_wait, log=lambda m: print(m, flush=True))
    os.makedirs(args.labels_dir, exist_ok=True)
    att_p = os.path.join(args.labels_dir, "attempts.jsonl")
    st_p = os.path.join(args.labels_dir, "states.jsonl")
    sum_p = os.path.join(args.labels_dir, "summary.jsonl")
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    stop_at = dt.datetime.fromisoformat(args.stop_at) if args.stop_at else None
    allow = json.load(open(args.allowance_file)) if args.allowance_file else {}
    source = json.load(open(args.source_file)) if args.source_file else {}

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
        byid = {r["id"]: r for r in rows}
        rank = {a: i for i, a in enumerate(first)}
        head = [byid[a] for a in first if a in byid]
        order = head if args.only_order else head + [r for r in order if r["id"] not in rank]
    queue = [r for r in order if r["id"] not in finished][: max(0, args.max_assemblies - len(finished))]
    root = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly")
    print(f"{len(finished)} finished, {len(queue)} queued, T={args.T}, oracle={args.oracle}, git={git}", flush=True)

    deferred = []    # FIFO of (ready_time, fn) — label/state/summary writes wait until a 5 s sample covers the queries

    def flush(force=False):
        while deferred and (force or time.time() >= deferred[0][0]):
            deferred.pop(0)[1]()

    def defer(ready, fn):
        ready = max([ready] + [d[0] for d in deferred])     # keep FIFO order
        deferred.append((ready, fn))

    def busy_of(r):
        if client is None or r.get("t_query_start") is None:
            return None, None, True
        bf, n = client.busy_frac(r["t_query_start"], r["t_query_end"])
        return bf, n, bf > 0

    def log_summary(d):
        d.update({"T": args.T, "seed": args.seed, "git": git, "oracle": args.oracle,
                  "timestamp": dt.datetime.now().isoformat()})
        with open(sum_p, "a") as f:
            f.write(json.dumps(d) + "\n")
        print("SUMMARY", json.dumps(d), flush=True)

    def label_record(aid, a, present, r, attempt, skey, removed, depth, ts):
        bf, n, conf = busy_of(r)
        lab = {"assembly_id": aid, "state_key": skey, "removed": removed, "depth": depth,
               "n_present": len(present), "n_parts": len(a["asm"].part_ids) if a else r.get("n_parts"),
               "part_id": r["part_id"], "attempt": attempt, "oracle": args.oracle,
               "source": source.get(aid, "v1"), "allowance": allow.get(aid),
               **{k: r.get(k) for k in V1_KEYS},
               "goal_candidate": r.get("escape_dir"), "escape_vec": r.get("escape_vec"),
               "busy_frac": bf, "busy_samples": n, "confounded": conf,
               "T": args.T, "device": args.device, "detector": r.get("detector", args.detector),
               "setup_time_s": (sum(r["part_setup_s_first"].values()) / len(r["part_setup_s_first"])
                                if r.get("part_setup_s_first") else r.get("sdf_train_s")),
               "git_hash": git, "timestamp": ts}
        if args.oracle == "v2":
            from disasm.oracle.oracle_v2 import LABEL_KEYS
            lab.update({k: r.get(k) for k in LABEL_KEYS})
        return lab

    P.pin_threads(1)
    os.environ.setdefault("DISASM_SDF_THREADS", "2")
    ex = ProcessPoolExecutor(args.workers, mp_context=mp.get_context("spawn"), initializer=P._init,
                             initargs=({"workdir": os.path.join(args.outdir, "work"), "device": args.device,
                                        "threads": 1, "slot_tag": "label_abd"},))
    active = {}      # aid -> dict(asm, removed, depth, n_pending, results, t0)
    todo = []        # jobs not yet submitted (dispatched only while non-busy)
    fut2aid = {}
    t_start = time.time()
    nq = 0
    busy_wait_s = 0.0

    def job_for(aid, a, p):
        return {"asm_dir": a["asm"].dir, "removed": list(a["removed"]), "part": p, "timeout_s": args.T,
                "seed": qseed(args.seed, aid, a["depth"], p), "assembly_id": aid,
                "detector": args.detector, "eps": args.eps, "oracle": args.oracle,
                "allowance": allow.get(aid)}

    def start_state(aid):
        a = active[aid]
        present = sorted(set(a["asm"].part_ids) - set(a["removed"]))
        a["n_pending"], a["results"], a["t_state0"] = len(present), [], time.time()
        for p in present:
            todo.append((aid, job_for(aid, a, p)))

    def dispatch():
        nonlocal busy_wait_s
        while todo and len(fut2aid) < args.workers:
            if client is not None and client.busy_now():
                t0 = time.time()
                time.sleep(1.0)
                busy_wait_s += time.time() - t0
                return
            aid, job = todo.pop(0)
            f = ex.submit(P.run_job, job)
            fut2aid[f] = aid

    def finish_state(aid):
        a = active[aid]
        present = sorted(set(a["asm"].part_ids) - set(a["removed"]))
        skey = "-".join(map(str, present))
        ts = dt.datetime.now().isoformat()
        res = sorted(a["results"], key=lambda r: r["part_id"])
        removed, depth = list(a["removed"]), a["depth"]
        succ = [r["part_id"] for r in res if is_success(r, args.oracle)]
        slow = [r["part_id"] for r in res if (r.get("sdf_train_s") or 0) > args.max_prep_s]
        chosen = random.Random(f"{args.seed}-{aid}-{depth}").choice(succ) if succ else None
        planner_s = sum(r.get("time_s") or 0 for r in res)
        st = {"assembly_id": aid, "depth": depth, "removed": removed, "state_key": skey,
              "n_queries": len(res), "n_success": len(succ), "successes": succ, "chosen": chosen,
              "planner_s": planner_s, "wall_s": time.time() - a["t_state0"], "oracle": args.oracle,
              "errors": [r["part_id"] for r in res if r.get("error")], "slow_prep": slow,
              "choice_rng": f"random.Random('{args.seed}-{aid}-{depth}')", "timestamp": ts}
        ready = max(r.get("t_query_end") or 0 for r in res) + SAMPLE_S + 1.0

        def write(res=res, st=st, present=present, skey=skey, removed=removed, depth=depth, ts=ts, a=a):
            recs = [label_record(aid, a, present, r, 0, skey, removed, depth, ts) for r in res]
            st["n_confounded"] = sum(x["confounded"] for x in recs)
            with open(att_p, "a") as lf:
                for x in recs:
                    lf.write(json.dumps(x) + "\n")
            with open(st_p, "a") as sf:
                sf.write(json.dumps(st) + "\n")
        defer(ready, write)
        a["n_states"] += 1
        a["n_queries"] += len(res)
        a["planner_s"] += planner_s
        print(f"[{(time.time() - t_start) / 60:6.1f} min] {aid} depth {depth} present={len(present)} "
              f"succ={succ} chosen={chosen} planner={planner_s:.0f}s wall={st['wall_s']:.0f}s total_q={nq} "
              f"busy_wait={busy_wait_s:.0f}s", flush=True)
        base = {"assembly_id": aid, "n_parts": len(a["asm"].part_ids), "n_states": a["n_states"],
                "n_queries": a["n_queries"], "planner_s": a["planner_s"], "wall_s": time.time() - a["t0"],
                "source": source.get(aid, "v1")}
        if slow:
            defer(ready, lambda b=base: log_summary({**b, "status": "skipped",
                                                     "reason": f"obstacle_prep_gt_{args.max_prep_s:.0f}s", "slow_parts": slow}))
            del active[aid]
        elif chosen is None:
            defer(ready, lambda b=base, rm=removed: log_summary({**b, "status": "stuck", "removed": rm}))
            del active[aid]
        elif len(present) - 1 <= 1:
            defer(ready, lambda b=base, rm=removed + [chosen]: log_summary({**b, "status": "complete", "removed": rm}))
            del active[aid]
        elif STOP or (stop_at and dt.datetime.now(stop_at.tzinfo) > stop_at):
            del active[aid]   # resumable from states.jsonl
        else:
            a["removed"] = removed + [chosen]
            a["depth"] += 1
            start_state(aid)

    while (queue or active or todo or fut2aid) and not STOP:
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
            if sc["max_penetration"] > args.max_pen and aid not in allow:
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
            start_state(aid)
        dispatch()
        flush()
        if not fut2aid:
            if todo:
                continue           # waiting for non-busy
            if not queue and not active:
                break
            continue
        done, _ = wait(list(fut2aid), return_when=FIRST_COMPLETED, timeout=2)
        for f in done:
            aid = fut2aid.pop(f)
            a = active[aid]
            a["results"].append(f.result())
            nq += 1
            if len(a["results"]) == a["n_pending"]:
                finish_state(aid)
    # drain in-flight jobs if stopping (their states are not written; they are redone on resume)
    if STOP:
        print("STOP requested; in-flight queries discarded (state not written, resumable)", flush=True)
    else:
        # wait for the sampler to cover the last queries, then write everything
        while deferred:
            flush()
            time.sleep(0.5)
    flush(force=STOP)

    # ------------------------------------------------------------------ re-run confounded queries (same seed)
    if not STOP and client is not None and os.path.exists(att_p):
        for rnd in range(1, args.max_reruns + 1):
            by = {}
            for l in open(att_p):
                x = json.loads(l)
                by.setdefault((x["assembly_id"], x["state_key"], x["part_id"]), []).append(x)
            jobs = []
            for k, atts in by.items():
                if any(not x["confounded"] for x in atts) or len(atts) > rnd:
                    continue
                a0 = min(atts, key=lambda x: x["attempt"])
                jobs.append((a0, {"asm_dir": os.path.join(root, a0["assembly_id"]), "removed": a0["removed"],
                                  "part": a0["part_id"], "timeout_s": args.T, "seed": a0["seed"],
                                  "assembly_id": a0["assembly_id"], "detector": args.detector, "eps": args.eps,
                                  "oracle": args.oracle, "allowance": allow.get(a0["assembly_id"])}))
            print(f"RERUN round {rnd}: {len(jobs)} confounded queries", flush=True)
            if not jobs:
                break
            infl = {}
            while (jobs or infl) and not STOP:
                while jobs and len(infl) < args.workers and not client.busy_now():
                    a0, job = jobs.pop(0)
                    infl[ex.submit(P.run_job, job)] = a0
                if not infl:
                    time.sleep(1.0)
                    continue
                done, _ = wait(list(infl), return_when=FIRST_COMPLETED, timeout=2)
                for f in done:
                    a0 = infl.pop(f)
                    r = f.result()
                    while time.time() < (r.get("t_query_end") or 0) + SAMPLE_S + 1.0:
                        time.sleep(0.5)
                    rec = label_record(a0["assembly_id"], None, a0["state_key"].split("-"), {**r, "n_parts": a0["n_parts"]},
                                       rnd, a0["state_key"], a0["removed"], a0["depth"], dt.datetime.now().isoformat())
                    rec["n_present"] = a0["n_present"]
                    with open(att_p, "a") as lf:
                        lf.write(json.dumps(rec) + "\n")
                    nq += 1
    if not STOP and os.path.exists(att_p):
        c = consolidate(args.labels_dir)
        print("CONSOLIDATED", json.dumps(c), flush=True)
    log_load(args.outdir, "end")
    if guard:
        guard.stop()
    print(f"LABEL RUN EXIT stop={STOP} queries_this_run={nq} wall={time.time() - t_start:.0f}s "
          f"busy_wait={busy_wait_s:.0f}s", flush=True)
    procs = list((getattr(ex, "_processes", None) or {}).values())  # grab before shutdown() sets it to None
    ex.shutdown(wait=False, cancel_futures=True)
    # terminate pool workers explicitly: os._exit skips executor cleanup, and orphaned workers would keep
    # holding their planner slots (found in run 02 R3 dev test; see reports/run02/DECISIONS.md #10)
    for pr in procs:
        try:
            pr.terminate()
        except Exception:  # noqa: BLE001
            pass
    os._exit(0)


if __name__ == "__main__":
    main()
