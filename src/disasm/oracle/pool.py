"""Process pool for CMG-RRT queries (spawned workers, one torch thread each, assemblies cached
per worker). Used by scripts/oracle_check.py and scripts/label_abd.py."""
from __future__ import annotations

import multiprocessing as mp
import os
import time
import traceback

_ASM = {}
_CFG = {}
THREAD_VARS = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS",
               "VECLIB_MAXIMUM_THREADS")


def pin_threads(n: int = 1) -> None:
    """Set BLAS/OpenMP thread caps in THIS process's environment so that spawned workers inherit
    them before numpy/torch/sklearn load (setting them inside a worker after import is too late).
    Without this each worker ran ~24 BLAS/KMeans threads and the machine load hit ~88."""
    os.environ["IGL_NUM_THREADS"] = str(n)
    for v in THREAD_VARS:
        os.environ[v] = str(n)


def _init(cfg):
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    _CFG.update(cfg)
    # CLAUDE.md: every planner worker holds one of the 10 global planner slots for its lifetime
    # (released by the kernel when the worker exits).
    from disasm.util.slots import acquire_slot
    _CFG["_slot"] = acquire_slot(tag=cfg.get("slot_tag", "pool_worker"))
    import torch
    torch.set_num_threads(cfg.get("threads", 1))
    os.environ.setdefault("OMP_NUM_THREADS", str(cfg.get("threads", 1)))
    os.environ.setdefault("IGL_NUM_THREADS", str(cfg.get("threads", 1)))


def _run(job):
    from disasm.oracle.cmgrrt import load_assembly, query
    t0 = time.time()
    try:
        d = job["asm_dir"]
        if d not in _ASM:
            if len(_ASM) > 4:
                _ASM.clear()
            _ASM[d] = load_assembly(d)
        t_q0 = time.time()
        if job.get("oracle", "v1") == "v2":
            from disasm.oracle.oracle_v2 import query_v2
            r = query_v2(_ASM[d], set(job["removed"]), job["part"], job["timeout_s"], job["seed"], _CFG["workdir"],
                         eps=job.get("eps") or 0.005, always_cmgrrt=job.get("always_cmgrrt", True),
                         save_path=job.get("save_path", True), max_iterations=_CFG.get("max_iterations"),
                         allowance=job.get("allowance"))
        else:
            r = query(_ASM[d], set(job["removed"]), job["part"], job["timeout_s"], job["seed"],
                      _CFG["workdir"], device=_CFG.get("device", "cpu"),
                      max_iterations=_CFG.get("max_iterations"),
                      detector=job.get("detector", _CFG.get("detector", "learned")),
                      eps=job.get("eps", _CFG.get("eps")), allowance=job.get("allowance"))
        r["t_query_start"], r["t_query_end"] = t_q0, time.time()
    except Exception as e:  # noqa: BLE001
        r = {"outcome": "unsolved", "error": f"{type(e).__name__}: {e}", "traceback": traceback.format_exc(),
             "part_id": job["part"], "removed": sorted(job["removed"])}
    r["worker_wall_s"] = time.time() - t0
    r["worker_pid"] = os.getpid()
    r["job"] = {k: v for k, v in job.items() if k != "asm_dir"}
    return r


def make_pool(n_workers: int, workdir: str, device: str = "cpu", threads: int = 1,
              max_iterations: int | None = None):
    pin_threads(threads)
    ctx = mp.get_context("spawn")
    return ctx.Pool(n_workers, initializer=_init,
                    initargs=({"workdir": workdir, "device": device, "threads": threads,
                               "max_iterations": max_iterations},),
                    maxtasksperchild=50)


run_job = _run
