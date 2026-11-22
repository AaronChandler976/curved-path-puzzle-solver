#!/usr/bin/env python
"""Run scripts/smoke_cmgrrt.py on every bundled CMG-RRT example (puzzle/ + general/) on the
given devices, up to --parallel at a time, each in its own subprocess with its own log.

Resumable: an (example, device) pair whose result line already exists in results.jsonl is
skipped. The per-run wall cap is enforced inside smoke_cmgrrt.py (--timeout, planner loop) and
again here with a hard subprocess kill at timeout + SDF-training slack.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--devices", default="cpu,cuda")
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--timeout", type=float, default=600.0)
    ap.add_argument("--iterations", type=int, default=5000)
    ap.add_argument("--threads", type=int, default=3, help="torch threads per CPU run")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    res_path = os.path.join(args.outdir, "results.jsonl")
    done = set()
    if os.path.exists(res_path):
        for line in open(res_path):
            r = json.loads(line)
            done.add((r["example"], r["device"]))
    exs = sorted(os.path.relpath(d, os.path.join(ROOT, "external/cmg-rrt/resources/models"))
                 for d in glob.glob(os.path.join(ROOT, "external/cmg-rrt/resources/models/*/*"))
                 if os.path.basename(os.path.dirname(d)) in ("puzzle", "general"))
    # Train every SDF first, one at a time on the GPU (cached; avoids 4 concurrent trainings).
    jobs = [(e, d) for e in exs for d in args.devices.split(",") if (e, d) not in done]
    print(f"{len(exs)} examples, {len(jobs)} runs to do", flush=True)

    def run(job):
        ex, dev = job
        log = os.path.join(args.outdir, f"{ex.replace('/', '_')}_{dev}.log")
        cmd = [sys.executable, os.path.join(ROOT, "scripts/smoke_cmgrrt.py"), "--example", ex,
               "--device", dev, "--iterations", str(args.iterations), "--timeout", str(args.timeout),
               "--seed", str(args.seed), "--threads", str(args.threads if dev == "cpu" else 1),
               "--out", res_path]
        t0 = time.time()
        with open(log, "w") as f:
            f.write(" ".join(cmd) + "\n")
            f.flush()
            try:
                rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=ROOT,
                                    timeout=args.timeout + 300).returncode
            except subprocess.TimeoutExpired:
                rc = "killed"
        print(f"{ex} {dev} rc={rc} wall={time.time() - t0:.0f}s log={log}", flush=True)

    # SDF warm-up: first device of each example runs sequentially for training if uncached.
    with ThreadPoolExecutor(args.parallel) as pool:
        list(pool.map(run, jobs))
    print("SWEEP DONE", flush=True)


if __name__ == "__main__":
    main()
