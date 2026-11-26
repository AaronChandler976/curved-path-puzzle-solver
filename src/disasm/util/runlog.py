"""Run-folder load/provenance logging (CLAUDE.md timing hygiene).

log_load(run_dir, tag) appends uptime, nvidia-smi utilisation/memory, the power profile,
the git hash and the command line to <run_dir>/load_info.txt. Call it with tag="start"
and tag="end" in every experiment script.
"""
from __future__ import annotations

import datetime as _dt
import os
import shlex
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception as e:  # tool missing / timeout: record it, never crash the run
        return f"<error: {e!r}>"


def load_snapshot() -> dict:
    return {
        "time": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "uptime": _run(["uptime"]),
        "nvidia_smi": _run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv"]),
        "power_profile": _run(["powerprofilesctl", "get"]),
        "git_hash": _run(["git", "-C", ROOT, "rev-parse", "HEAD"]),
        "git_dirty": bool(_run(["git", "-C", ROOT, "status", "--porcelain", "--untracked-files=no"])),
        "cmd": " ".join(shlex.quote(a) for a in sys.argv),
        "pid": os.getpid(),
    }


def log_load(run_dir: str, tag: str) -> dict:
    os.makedirs(run_dir, exist_ok=True)
    s = load_snapshot()
    with open(os.path.join(run_dir, "load_info.txt"), "a") as f:
        f.write(f"=== {tag} ===\n")
        for k, v in s.items():
            f.write(f"{k}: {v}\n")
    if tag == "start":
        if not os.path.exists(os.path.join(run_dir, "git_hash.txt")):
            with open(os.path.join(run_dir, "git_hash.txt"), "w") as f:
                f.write(s["git_hash"] + ("  (dirty)" if s["git_dirty"] else "") + "\n")
        with open(os.path.join(run_dir, "cmd.txt"), "a") as f:
            f.write(s["cmd"] + "\n")
    return s
