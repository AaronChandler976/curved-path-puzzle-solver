"""Run independent timed jobs through the idle guard (CLAUDE.md Run 04 rules) on <= 10 slot-holding workers.

``run_guarded(fn_path, jobs, outdir, out_name, workers, idle_wait, max_reruns)``
- refuses to start while other planner slots are held;
- starts an IdleSampler in this process (run dir = outdir) and waits ``idle_wait`` s of non-busy;
- dispatches a job only while non-busy; every result line gets ``attempt``, ``t_job_start/end``, ``busy_frac``,
  ``busy_samples``, ``confounded``;
- resumable: jobs whose key already has a line in the output are skipped;
- at the end re-runs jobs whose every attempt is confounded (same job dict = same seed), up to ``max_reruns``.
``fn_path`` = "module:function"; the function takes the job dict and returns a json-able dict. Each job needs a
unique "key" (str).
"""
from __future__ import annotations

import importlib
import json
import multiprocessing as mp
import os
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait


def _call(fn_path, job):
    import traceback
    mod, fn = fn_path.split(":")
    t0 = time.time()
    try:
        r = getattr(importlib.import_module(mod), fn)(job)
    except Exception as e:  # noqa: BLE001 - logged, never hidden
        r = {"error": f"{type(e).__name__}: {e}", "traceback": traceback.format_exc()}
    r["t_job_start"], r["t_job_end"] = t0, time.time()
    r["worker_pid"] = os.getpid()
    return r


def run_guarded(fn_path, jobs, outdir, out_name="results.jsonl", workers=10, idle_wait=300.0, max_reruns=2,
                slot_tag="guarded_pool", log=print, guard=True):
    from disasm.oracle import pool as P
    from disasm.util.idle_guard import IdleClient, IdleSampler, SAMPLE_S
    from disasm.util.slots import slots_in_use
    os.makedirs(outdir, exist_ok=True)
    held = slots_in_use()
    if held:
        raise RuntimeError(f"{held} planner slots held by another job; refusing to start (CLAUDE.md)")
    sampler = client = None
    if guard:
        sampler = IdleSampler(outdir, tag=slot_tag).start()
        client = IdleClient(outdir)
        if idle_wait > 0:
            log(f"waiting for {idle_wait:.0f} s non-busy")
            sampler.wait_idle(idle_wait, log=log)
    out_p = os.path.join(outdir, out_name)
    att = {}
    if os.path.exists(out_p):
        for l in open(out_p):
            r = json.loads(l)
            att.setdefault(r["key"], []).append(r)
    P.pin_threads(1)
    ex = ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn"), initializer=P._init,
                             initargs=({"workdir": os.path.join(outdir, "work"), "device": "cpu", "threads": 1,
                                        "slot_tag": slot_tag},))
    t_start = time.time()

    def run(batch, attempt):
        queue, infl, n = list(batch), {}, 0
        with open(out_p, "a") as f:
            while queue or infl:
                while queue and len(infl) < workers and not (client and client.busy_now()):
                    j = queue.pop(0)
                    infl[ex.submit(_call, fn_path, j)] = j
                if not infl:
                    time.sleep(1.0)
                    continue
                done, _ = wait(list(infl), return_when=FIRST_COMPLETED, timeout=2)
                for fu in done:
                    j = infl.pop(fu)
                    r = fu.result()
                    if client:
                        while time.time() < r["t_job_end"] + SAMPLE_S + 1.0:
                            time.sleep(0.25)
                        r["busy_frac"], r["busy_samples"] = client.busy_frac(r["t_job_start"], r["t_job_end"])
                        r["confounded"] = r["busy_frac"] > 0
                    else:
                        r["busy_frac"], r["busy_samples"], r["confounded"] = None, None, None
                    r["key"], r["attempt"] = j["key"], attempt
                    f.write(json.dumps(r) + "\n")
                    f.flush()
                    att.setdefault(j["key"], []).append(r)
                    n += 1
                    if n % 25 == 0 or not (queue or infl):
                        log(f"[{(time.time() - t_start) / 60:6.1f} min] attempt {attempt}: {n}/{len(batch)} done")

    run([j for j in jobs if j["key"] not in att], 0)
    if client:
        for rnd in range(1, max_reruns + 1):
            rj = [j for j in jobs if len(att.get(j["key"], [])) == rnd and all(x.get("confounded") for x in att[j["key"]])]
            log(f"RERUN round {rnd}: {len(rj)} confounded jobs")
            if not rj:
                break
            run(rj, rnd)
    procs = list((getattr(ex, "_processes", None) or {}).values())
    ex.shutdown(wait=False, cancel_futures=True)
    for pr in procs:
        try:
            pr.terminate()
        except Exception:  # noqa: BLE001
            pass
    if sampler:
        sampler.stop()
    return att


def first_clean(att: dict) -> dict:
    """key -> the first non-confounded attempt (else attempt 0, flagged still_confounded)."""
    out = {}
    for k, xs in att.items():
        xs = sorted(xs, key=lambda r: r["attempt"])
        clean = [x for x in xs if not x.get("confounded")]
        r = dict(clean[0] if clean else xs[0])
        r["still_confounded"] = not clean
        r["n_attempts"] = len(xs)
        out[k] = r
    return out
