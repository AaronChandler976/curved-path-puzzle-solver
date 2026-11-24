"""Idle guard for timed planner work (CLAUDE.md "Run 04 rules").

Definition (exactly as CLAUDE.md states it):
- **busy** = processes outside this project (not our runner, not our workers, not ``claude``) use more than
  ``CPU_CORES_MAX`` = 0.5 CPU core on average over the last ``WINDOW_S`` = 30 s, OR the 1-min load average minus our
  own planner workers is above ``LOAD_MAX`` = 1.5. GPU utilisation is logged but is NOT a criterion.
- Samples are taken every ``SAMPLE_S`` = 5 s. Before a timed batch starts the machine must be non-busy for 5 min.
- A query's ``busy_frac`` = fraction of the 5 s samples overlapping the query that were busy;
  ``confounded = busy_frac > 0``.

"Ours" = the runner process (the one that owns the sampler) and every descendant of it, plus processes whose command
name is ``claude``. "Our planner workers" in the load criterion = the number of our threads in run state R/D, smoothed
with the kernel's own 1-min exponential (factor exp(-5/60) per 5 s sample), so it is directly comparable with
/proc/loadavg's first field.

Sharing with workers: the sampler (a thread inside the runner) appends every sample to ``<run_dir>/idle_samples.jsonl``
and atomically rewrites ``<run_dir>/idle_state.json``. Worker processes use :class:`IdleClient` on the same run dir
(``wait_not_busy()`` before dispatching a query, ``busy_frac(t0, t1)`` after it). Times are ``time.time()`` (same
clock in every process).

CLI::

    python -m disasm.util.idle_guard --wait-idle 300 [--run-dir DIR] [--max-wait 7200]

exits 0 once the machine has been non-busy for 300 s (samples logged to DIR/idle_samples.jsonl), 3 on --max-wait.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import threading
import time

SAMPLE_S = 5.0
WINDOW_S = 30.0
CPU_CORES_MAX = 0.5
LOAD_MAX = 1.5
OURS_COMM = ("claude",)
_CLK = os.sysconf("SC_CLK_TCK")
_EXP = math.exp(-SAMPLE_S / 60.0)          # kernel load-average decay per 5 s


# ------------------------------------------------------------------------------------------- /proc readers
def _read_stat(pid: str):
    """(ppid, comm, utime+stime ticks, state) or None."""
    try:
        with open(f"/proc/{pid}/stat", "rb") as f:
            s = f.read().decode("utf-8", "replace")
    except OSError:
        return None
    l, r = s.find("("), s.rfind(")")
    comm = s[l + 1:r]
    rest = s[r + 2:].split()
    # rest[0] = state, rest[1] = ppid, rest[11] = utime, rest[12] = stime
    return int(rest[1]), comm, int(rest[11]) + int(rest[12]), rest[0]


def _running_threads(pid: str) -> int:
    n = 0
    try:
        for tid in os.listdir(f"/proc/{pid}/task"):
            try:
                with open(f"/proc/{pid}/task/{tid}/stat", "rb") as f:
                    s = f.read().decode("utf-8", "replace")
                if s[s.rfind(")") + 2] in "RD":
                    n += 1
            except OSError:
                pass
    except OSError:
        pass
    return n


def proc_table() -> dict:
    out = {}
    for pid in os.listdir("/proc"):
        if pid.isdigit():
            st = _read_stat(pid)
            if st is not None:
                out[int(pid)] = st
    return out


def descendants(table: dict, root: int) -> set:
    kids = {}
    for pid, (ppid, *_r) in table.items():
        kids.setdefault(ppid, []).append(pid)
    out, stack = {root}, [root]
    while stack:
        for c in kids.get(stack.pop(), []):
            if c not in out:
                out.add(c)
                stack.append(c)
    return out


def loadavg1() -> float:
    with open("/proc/loadavg") as f:
        return float(f.read().split()[0])


def gpu_util() -> float | None:
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=5)
        return float(r.stdout.strip().splitlines()[0])
    except Exception:  # noqa: BLE001 - logged as missing, never a criterion
        return None


# ------------------------------------------------------------------------------------------- criterion
def is_busy(outside_cores: float, load1: float, our_load: float) -> bool:
    """CLAUDE.md busy criterion (pure function, unit-tested)."""
    return outside_cores > CPU_CORES_MAX or (load1 - our_load) > LOAD_MAX


class IdleSampler:
    """5 s sampler. ``root_pid`` = the runner; its descendants are "ours"."""

    def __init__(self, run_dir: str, root_pid: int | None = None, sample_s: float = SAMPLE_S, gpu: bool = True,
                 tag: str = ""):
        self.run_dir = run_dir
        os.makedirs(run_dir, exist_ok=True)
        self.root = root_pid or os.getpid()
        self.sample_s = sample_s
        self.gpu = gpu
        self.tag = tag
        self.samples_path = os.path.join(run_dir, "idle_samples.jsonl")
        self.state_path = os.path.join(run_dir, "idle_state.json")
        self.hist = []                       # (t, outside_ticks_total) for the 30 s window
        self.prev = {}                       # pid -> (comm, ticks) at the previous sample
        self.our_load = None
        self.last = None
        self._stop = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self.outside_cum = 0.0               # cumulative outside CPU seconds since the sampler started

    def sample(self) -> dict:
        t = time.time()
        tab = proc_table()
        ours = descendants(tab, self.root)
        ours |= {p for p, (_pp, comm, _t, _s) in tab.items() if comm in OURS_COMM}
        # outside CPU = sum over outside processes of tick deltas since the previous sample (new processes count from 0;
        # their ticks before the first sample are only partially in-window, which slightly over-counts -> conservative)
        d_out, top = 0, {}
        cur = {}
        for p, (_pp, comm, ticks, _s) in tab.items():
            cur[p] = (comm, ticks)
            if p in ours:
                continue
            _pc, pt = self.prev.get(p, (comm, None))
            if pt is None:
                if not self.prev:          # very first sample: no baseline
                    continue
                delta = ticks
            else:
                delta = max(0, ticks - pt)
            if delta:
                d_out += delta
                top[f"{comm}:{p}"] = delta
        self.prev = cur
        self.outside_cum += d_out / _CLK
        self.hist.append((t, self.outside_cum))
        while len(self.hist) > 1 and t - self.hist[0][0] > WINDOW_S + 1e-6:
            self.hist.pop(0)
        span = t - self.hist[0][0]
        if span < self.sample_s * 0.5:       # first sample: not enough history
            outside_cores = d_out / _CLK / self.sample_s
        else:
            outside_cores = (self.outside_cum - self.hist[0][1]) / span
        our_run = sum(_running_threads(str(p)) for p in ours if p in tab and tab[p][1] not in OURS_COMM)
        # exclude the sampler's own momentary run state (the sampler thread is running while it reads /proc)
        our_run = max(0, our_run - 1)
        self.our_load = our_run if self.our_load is None else self.our_load * _EXP + our_run * (1 - _EXP)
        l1 = loadavg1()
        first = len(self.hist) == 1
        busy = True if first else is_busy(outside_cores, l1, self.our_load)   # no baseline yet -> busy
        rec = {"t": t, "iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t)),
               "outside_cores_30s": round(outside_cores, 4), "load1": l1, "our_load": round(self.our_load, 3),
               "our_running": our_run, "n_ours": len(ours), "busy": bool(busy),
               "top_outside": sorted(top.items(), key=lambda kv: -kv[1])[:3], "tag": self.tag}
        if self.gpu:
            rec["gpu_util"] = gpu_util()
        with self._lock:
            self.last = rec
            with open(self.samples_path, "a") as f:
                f.write(json.dumps(rec) + "\n")
            tmp = self.state_path + f".tmp{os.getpid()}"
            with open(tmp, "w") as f:
                json.dump(rec, f)
            os.replace(tmp, self.state_path)
        return rec

    # background thread
    def _loop(self):
        nxt = time.time()
        while not self._stop.is_set():
            try:
                self.sample()
            except Exception as e:  # noqa: BLE001 - a failed sample is logged as busy (conservative)
                with open(self.samples_path, "a") as f:
                    f.write(json.dumps({"t": time.time(), "busy": True, "error": repr(e)}) + "\n")
            nxt += self.sample_s
            self._stop.wait(max(0.0, nxt - time.time()))

    def start(self) -> "IdleSampler":
        self._thread = threading.Thread(target=self._loop, daemon=True, name="idle_sampler")
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=10)

    def alive(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def busy_now(self) -> bool:
        return IdleClient(self.run_dir).busy_now()

    def wait_idle(self, need_s: float = 300.0, max_wait_s: float | None = None, log=print) -> bool:
        """Block until `need_s` consecutive seconds of non-busy samples (sampler thread must be running)."""
        return IdleClient(self.run_dir).wait_idle(need_s, max_wait_s, log)


class IdleClient:
    """Read-only view of a sampler's files; safe to use from worker processes."""

    STALE_S = 30.0

    def __init__(self, run_dir: str):
        self.samples_path = os.path.join(run_dir, "idle_samples.jsonl")
        self.state_path = os.path.join(run_dir, "idle_state.json")
        self._off = 0
        self._cache = []

    def state(self) -> dict | None:
        try:
            with open(self.state_path) as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    def busy_now(self) -> bool:
        s = self.state()
        if s is None or time.time() - s.get("t", 0) > self.STALE_S:
            return True                      # no fresh sample = unknown = treat as busy (conservative)
        return bool(s["busy"])

    def wait_not_busy(self, poll_s: float = 1.0, max_wait_s: float | None = None) -> float:
        """Block until the latest sample is non-busy. Returns seconds waited."""
        t0 = time.time()
        while self.busy_now():
            if max_wait_s is not None and time.time() - t0 > max_wait_s:
                break
            time.sleep(poll_s)
        return time.time() - t0

    def _load(self):
        try:
            with open(self.samples_path) as f:
                f.seek(self._off)
                data = f.read()
        except OSError:
            return self._cache
        last_nl = data.rfind("\n")
        if last_nl >= 0:
            for line in data[:last_nl].splitlines():
                try:
                    r = json.loads(line)
                    if "t" in r:
                        self._cache.append((float(r["t"]), bool(r.get("busy", True))))
                except ValueError:
                    pass
            self._off += len(data[:last_nl + 1].encode())
        return self._cache

    def busy_frac(self, t0: float, t1: float, sample_s: float = SAMPLE_S) -> tuple:
        """(busy_frac, n_samples). Sample at time s covers (s - sample_s, s]; every sample overlapping [t0, t1]
        counts. If none overlaps (a query shorter than the gap), the nearest sample is used."""
        h = self._load()
        sel = [b for (s, b) in h if s > t0 and s - sample_s < t1]
        if not sel and h:
            s, b = min(h, key=lambda x: abs(x[0] - t1))
            sel = [b]
        if not sel:
            return 1.0, 0                     # no samples at all: unknown -> confounded
        return sum(sel) / len(sel), len(sel)

    def wait_idle(self, need_s: float = 300.0, max_wait_s: float | None = None, log=print) -> bool:
        t_start = time.time()
        idle_since = None
        last_log = 0
        while True:
            s = self.state()
            now = time.time()
            fresh = s is not None and now - s.get("t", 0) <= self.STALE_S
            if fresh and not s["busy"]:
                idle_since = idle_since or s["t"]
                if s["t"] - idle_since >= need_s:
                    log(f"[idle_guard] non-busy for {s['t'] - idle_since:.0f} s -> go")
                    return True
            else:
                if idle_since is not None and fresh:
                    log(f"[idle_guard] busy at {s.get('iso')}: outside={s.get('outside_cores_30s')} "
                        f"load1={s.get('load1')} our={s.get('our_load')} top={s.get('top_outside')}")
                idle_since = None
            if max_wait_s is not None and now - t_start > max_wait_s:
                log(f"[idle_guard] gave up after {now - t_start:.0f} s")
                return False
            if now - last_log > 60:
                last_log = now
                log(f"[idle_guard] waiting; idle streak {0 if idle_since is None else now - idle_since:.0f}/{need_s:.0f} s;"
                    f" last={json.dumps({k: (s or {}).get(k) for k in ('outside_cores_30s', 'load1', 'our_load', 'busy')})}")
            time.sleep(1.0)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wait-idle", type=float, default=300.0, help="seconds of continuous non-busy required")
    ap.add_argument("--run-dir", default="logs/idle_guard", help="where idle_samples.jsonl / idle_state.json go")
    ap.add_argument("--max-wait", type=float, default=None, help="give up after this many seconds (exit 3)")
    ap.add_argument("--root-pid", type=int, default=None, help="pid whose process tree counts as ours (default: self)")
    a = ap.parse_args(argv)
    s = IdleSampler(a.run_dir, root_pid=a.root_pid, tag="cli").start()
    ok = s.wait_idle(a.wait_idle, a.max_wait, log=lambda m: print(m, flush=True))
    s.stop()
    raise SystemExit(0 if ok else 3)


if __name__ == "__main__":
    main()
