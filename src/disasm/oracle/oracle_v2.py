"""Oracle v2 (run 04 T4; CLAUDE.md hard rule 2 "Oracle v2"; docs/PLAN.md Run 04 additions).

One query = (assembly state, part). Two stages share one setup (exact union SDF of the other remaining parts, seeded
robot surface samples, the CMG-RRT collision detector):
1. **Straight-pull pre-check** (``linear_precheck.sweep_direction``): translate the part along each goal-candidate
   direction (adapter order) to the goal distance, certified at step <= eps/2 near contact. This is also the start
   pose's straight connection to every goal, which the v1 adapter never tested (reports/run04/oracle_v2.md).
   Its time counts as query cost.
2. **CMG-RRT** (library tree search, unchanged) with the v2 adapter fixes ``FIX_V2`` (cmgrrt.query docstring): every
   goal connection confirmed at step <= eps/2, every found path validated edge by edge at step <= eps/2.

Configurations (both replayable from one label):
- **main = "pre-check -> CMG-RRT"**: success iff the pull clears or CMG-RRT succeeds;
  cost = precheck_time_s + (cmgrrt_time_s if the pull did not clear).
- **secondary = "CMG-RRT only"**: the CMG-RRT stage alone (cost = cmgrrt_time_s).
For labels (``always_cmgrrt=True``) CMG-RRT runs even when the pull clears. In live evaluation
(``always_cmgrrt=False``) it runs only when needed. A non-success is "unsolved" (censored), never "infeasible".
"""
from __future__ import annotations

FIX_V2 = ("fine_goal", "validate")
MARGIN_V2 = 0.0          # set by the T4.4 decision (reports/run04/oracle_v2.md)

LABEL_KEYS = ["precheck_free", "precheck_dir", "precheck_vec", "precheck_time_s", "precheck_dirs_checked",
              "cmgrrt_ran", "cmgrrt_outcome", "cmgrrt_time_s", "cmgrrt_iterations", "cmgrrt_escape_dir",
              "cmgrrt_path_valid", "cmgrrt_path_max_rot_deg", "n_goal_edges_rejected_fine", "n_paths_rejected_fine",
              "fine_check_s", "stage", "cmgrrt_only_outcome", "cmgrrt_only_time_s", "fix", "tree_hash",
              "path_file_precheck", "margin", "margin_relief_parts", "allowance_offsets", "start_min_sdf"]


def combine(r: dict, always_cmgrrt: bool) -> dict:
    """Map a cmgrrt.query(precheck=True, ...) result to the v2 fields (in place)."""
    ran = r.get("cmgrrt_ran", False)
    r["cmgrrt_outcome"] = r.get("outcome") if ran else None
    r["cmgrrt_time_s"] = r.get("time_s") if ran else None
    r["cmgrrt_iterations"] = r.get("iterations") if ran else None
    r["cmgrrt_escape_dir"] = r.get("escape_dir") if ran else None
    r["cmgrrt_path_max_rot_deg"] = r.get("path_max_rot_deg") if ran else None
    # with "validate" in the fixes a reported CMG-RRT success passed the fine path check by construction
    r["cmgrrt_path_valid"] = (r["cmgrrt_outcome"] == "success") if (ran and "validate" in (r.get("fix") or [])) else None
    pre = bool(r.get("precheck_free"))
    cm = r["cmgrrt_outcome"] == "success"
    r["outcome"] = "success" if (pre or cm) else "unsolved"
    r["stage"] = "precheck" if pre else ("cmgrrt" if cm else None)
    r["time_s"] = (r.get("precheck_time_s") or 0.0) + (0.0 if pre else (r["cmgrrt_time_s"] or 0.0))
    r["cmgrrt_only_outcome"] = r["cmgrrt_outcome"] if ran else None
    r["cmgrrt_only_time_s"] = r["cmgrrt_time_s"] if ran else None
    if pre:
        r["escape_dir"] = r.get("precheck_dir")
        r["escape_vec"] = r.get("precheck_vec")
        if not ran or not cm:
            r["path_max_rot_deg"] = 0.0
            r["path_file"] = r.get("path_file_precheck", r.get("path_file"))
    r["oracle"] = "v2"
    return r


def query_v2(asm, removed, part, T, seed, workdir, eps=0.005, always_cmgrrt=True, save_path=True,
             max_iterations=None, fix=FIX_V2, allowance=None, margin=MARGIN_V2) -> dict:
    from disasm.oracle.cmgrrt import query
    r = query(asm, set(removed), part, T, seed, workdir, device="cpu", detector="exact", eps=eps,
              precheck=True, cmgrrt_if_free=always_cmgrrt, fix=tuple(fix), save_path=save_path,
              max_iterations=max_iterations, allowance=allowance, margin=margin)
    return combine(r, always_cmgrrt)
