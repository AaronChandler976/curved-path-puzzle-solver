"""Run 04 T1: idle guard (CLAUDE.md Run 04 rules)."""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
BURN = [sys.executable, "-c", "import time\nt=time.time()\nwhile time.time()-t<30: pass"]


def test_criterion():
    from disasm.util.idle_guard import is_busy
    assert not is_busy(0.3, 0.5, 0.0)
    assert is_busy(0.51, 0.5, 0.0)                 # > 0.5 outside core
    assert not is_busy(0.0, 11.0, 10.0)            # load from our own 10 workers is subtracted
    assert is_busy(0.0, 12.0, 10.0)                # 2.0 > 1.5 beyond our workers
    assert not is_busy(0.5, 1.5, 0.0)              # thresholds are strict ">"


def _run_sampler(tmp_path, root_pid, n=4, dt=2.0):
    from disasm.util.idle_guard import IdleSampler
    s = IdleSampler(str(tmp_path), root_pid=root_pid, sample_s=dt, gpu=False)
    recs = []
    for _ in range(n):
        recs.append(s.sample())
        time.sleep(dt)
    return recs


def test_outside_burner_is_busy(tmp_path):
    """A CPU burner that is NOT in the runner's tree counts as outside -> busy."""
    root = subprocess.Popen(["sleep", "60"])       # pretend runner; this test process + burner are outside it
    burn = subprocess.Popen(BURN)
    try:
        recs = _run_sampler(tmp_path, root.pid)
    finally:
        burn.kill(); root.kill()
    assert recs[0]["busy"]                          # first sample: no baseline -> conservatively busy
    assert recs[-1]["outside_cores_30s"] > 0.8
    assert recs[-1]["busy"]


def test_own_burner_not_outside(tmp_path):
    """The same burner as a descendant of the runner is ours: not counted as outside CPU."""
    burn = subprocess.Popen(BURN)
    try:
        recs = _run_sampler(tmp_path, os.getpid())
    finally:
        burn.kill()
    assert recs[-1]["our_running"] >= 1
    # the burner (~1 core) is excluded; whatever remains is other desktop activity
    assert recs[-1]["outside_cores_30s"] < 0.8


def test_busy_frac_and_stale(tmp_path):
    from disasm.util.idle_guard import IdleClient
    now = time.time()
    with open(tmp_path / "idle_samples.jsonl", "w") as f:
        for i, b in enumerate([False, False, True, False, True, False]):
            f.write(json.dumps({"t": now - 30 + 5 * i, "busy": b}) + "\n")
    c = IdleClient(str(tmp_path))
    # samples at -30 F, -25 F, -20 T, -15 F, -10 T, -5 F; a query over [-27, -13] overlaps -25, -20, -15, -10 (covers (-15,-10])
    frac, n = c.busy_frac(now - 27, now - 13)
    assert n == 4 and abs(frac - 0.5) < 1e-9
    frac, n = c.busy_frac(now - 9, now - 6)        # only the sample at now-5 overlaps
    assert n == 1 and frac == 0.0
    # state file missing -> unknown -> busy; stale -> busy; fresh non-busy -> not busy
    assert c.busy_now()
    with open(tmp_path / "idle_state.json", "w") as f:
        json.dump({"t": now - 100, "busy": False}, f)
    assert c.busy_now()
    with open(tmp_path / "idle_state.json", "w") as f:
        json.dump({"t": time.time(), "busy": False}, f)
    assert not c.busy_now()


def test_cli_help():
    r = subprocess.run([sys.executable, "-m", "disasm.util.idle_guard", "--help"], capture_output=True, text=True,
                       env={**os.environ, "PYTHONPATH": os.path.join(os.path.dirname(__file__), "..", "src")})
    assert r.returncode == 0 and "--wait-idle" in r.stdout


def test_own_multithreaded_burner_not_load(tmp_path):
    """A multithreaded burner in OUR tree must not make the load criterion busy (run 04 T5 artefact)."""
    code = ("import threading,time\n"
            "def f():\n t=time.time()\n while time.time()-t<40: pass\n"
            "ts=[threading.Thread(target=f) for _ in range(4)]\n[x.start() for x in ts]\n[x.join() for x in ts]")
    burn = subprocess.Popen([sys.executable, "-c", code])
    try:
        recs = _run_sampler(tmp_path, os.getpid(), n=8, dt=2.0)
    finally:
        burn.kill()
    r = recs[-1]
    assert r["our_cores"] > 0.8                    # our CPU use is measured (the GIL burner uses >= 1 core)
    assert r["our_load"] >= r["our_load_cpu"] > 0.2   # and enters the load criterion (1-min EMA, still rising)
