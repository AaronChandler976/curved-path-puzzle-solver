"""Cross-process planner-slot semaphore (CLAUDE.md: at most 10 planner processes across ALL jobs).

Implementation: MAX_SLOTS lock files ``logs/slots/slot_<i>.lock``; holding a slot = holding an
exclusive ``fcntl.flock`` on one of them. The kernel drops flocks when the holding process dies,
so a crashed worker never leaks a slot. The cap is a hard constant; ``DISASM_MAX_SLOTS`` may only
LOWER it (values above 10 are clamped to 10).

Usage::

    from disasm.util.slots import PlannerSlot
    with PlannerSlot():              # blocks until a slot is free
        run_planner(...)

    slot = acquire_slot()            # long-lived worker: hold it for the process lifetime
    ...
    slot.release()

Every script that starts planner workers must take a slot per worker process
(pool workers do it in their initializer, see disasm/oracle/pool.py).
"""
from __future__ import annotations

import fcntl
import json
import os
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
HARD_CAP = 10
DEFAULT_DIR = os.path.join(ROOT, "logs", "slots")


def max_slots() -> int:
    v = os.environ.get("DISASM_MAX_SLOTS")
    n = HARD_CAP if not v else int(v)
    return max(1, min(HARD_CAP, n))


class SlotTimeout(TimeoutError):
    pass


class PlannerSlot:
    def __init__(self, timeout: float | None = None, slot_dir: str | None = None, poll_s: float = 0.2,
                 tag: str = ""):
        self.timeout = timeout
        self.slot_dir = slot_dir or os.environ.get("DISASM_SLOT_DIR", DEFAULT_DIR)
        self.poll_s = poll_s
        self.tag = tag
        self.fd = None
        self.index = None

    def acquire(self) -> "PlannerSlot":
        if self.fd is not None:
            return self
        os.makedirs(self.slot_dir, exist_ok=True)
        t0 = time.time()
        n = max_slots()
        while True:
            for i in range(n):
                path = os.path.join(self.slot_dir, f"slot_{i}.lock")
                fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    os.close(fd)
                    continue
                # owner info for humans (`cat logs/slots/*.lock`); the lock itself is the flock
                os.ftruncate(fd, 0)
                os.write(fd, json.dumps({"pid": os.getpid(), "tag": self.tag,
                                         "since": time.strftime("%Y-%m-%dT%H:%M:%S")}).encode())
                self.fd, self.index = fd, i
                return self
            if self.timeout is not None and time.time() - t0 >= self.timeout:
                raise SlotTimeout(f"no free planner slot (cap {n}) after {self.timeout:.1f} s")
            time.sleep(self.poll_s)

    def release(self) -> None:
        if self.fd is None:
            return
        try:
            os.ftruncate(self.fd, 0)
            fcntl.flock(self.fd, fcntl.LOCK_UN)
        finally:
            os.close(self.fd)
            self.fd, self.index = None, None

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *exc):
        self.release()
        return False


def acquire_slot(timeout: float | None = None, tag: str = "", slot_dir: str | None = None) -> PlannerSlot:
    return PlannerSlot(timeout=timeout, tag=tag, slot_dir=slot_dir).acquire()


def slots_in_use(slot_dir: str | None = None) -> int:
    """Number of slots currently held (by any process)."""
    d = slot_dir or os.environ.get("DISASM_SLOT_DIR", DEFAULT_DIR)
    used = 0
    for i in range(HARD_CAP):
        path = os.path.join(d, f"slot_{i}.lock")
        if not os.path.exists(path):
            continue
        fd = os.open(path, os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(fd, fcntl.LOCK_UN)
        except BlockingIOError:
            used += 1
        finally:
            os.close(fd)
    return used


if __name__ == "__main__":
    print(f"planner slots in use: {slots_in_use()} / {max_slots()}")
