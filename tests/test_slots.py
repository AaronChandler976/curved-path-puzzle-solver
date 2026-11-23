"""The planner-slot semaphore enforces the 10-process cap across processes (CLAUDE.md)."""
import multiprocessing as mp
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from disasm.util.slots import HARD_CAP, PlannerSlot, SlotTimeout, max_slots, slots_in_use  # noqa: E402


def _hold(slot_dir, ready, stop):
    s = PlannerSlot(slot_dir=slot_dir, timeout=5).acquire()
    ready.put(s.index)
    stop.wait(30)
    s.release()


def test_cap_is_10_and_env_cannot_raise_it(monkeypatch):
    assert HARD_CAP == 10
    monkeypatch.setenv("DISASM_MAX_SLOTS", "50")
    assert max_slots() == 10
    monkeypatch.setenv("DISASM_MAX_SLOTS", "3")
    assert max_slots() == 3


def test_eleventh_acquire_blocks(tmp_path, monkeypatch):
    monkeypatch.delenv("DISASM_MAX_SLOTS", raising=False)
    d = str(tmp_path / "slots")
    ctx = mp.get_context("spawn")
    ready, stop = ctx.Queue(), ctx.Event()
    procs = [ctx.Process(target=_hold, args=(d, ready, stop)) for _ in range(10)]
    for p in procs:
        p.start()
    try:
        idx = sorted(ready.get(timeout=30) for _ in procs)
        assert idx == list(range(10))
        assert slots_in_use(d) == 10
        # 11th acquire (another process: this one) must block; with a timeout it raises
        t0 = time.time()
        with pytest.raises(SlotTimeout):
            PlannerSlot(slot_dir=d, timeout=1.0).acquire()
        assert time.time() - t0 >= 1.0
        # free one slot -> the 11th acquire now succeeds
        stop.set()
        for p in procs:
            p.join(10)
        with PlannerSlot(slot_dir=d, timeout=5.0) as s:
            assert s.index is not None
    finally:
        stop.set()
        for p in procs:
            if p.is_alive():
                p.terminate()


def test_slot_freed_when_holder_dies(tmp_path):
    d = str(tmp_path / "slots")
    ctx = mp.get_context("spawn")
    ready, stop = ctx.Queue(), ctx.Event()
    p = ctx.Process(target=_hold, args=(d, ready, stop))
    p.start()
    ready.get(timeout=30)
    assert slots_in_use(d) == 1
    p.kill()
    p.join(10)
    assert slots_in_use(d) == 0
