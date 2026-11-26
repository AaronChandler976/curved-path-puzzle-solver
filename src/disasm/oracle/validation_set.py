"""Run 04 T4.4: one validation-set query under one oracle config, plus an independent fine re-check of the saved
success path (path_validate.validate_path, exact union at eps, step <= eps/2, the query's own seeded samples).

configs: "v1"  = cmgrrt.query, exact detector, no pre-check, no fixes (run 02/03 oracle; seeded samples);
         "v2a" = oracle v2, fixes (fine_goal, validate), margin 0;
         "v2b" = oracle v2, fixes (fine_goal, validate), planning margin 0.1 eps.
v2 configs always run CMG-RRT too (label mode), so "CMG-RRT only" is measured as well."""
from __future__ import annotations

import json

import numpy as np

CONFIGS = {"v1": None, "v2a": 0.0, "v2b": 0.0005, "v2h": 0.0}
GRAD_DX = {"v2h": 0.005}      # run 04 T5 hybrid: exact decisions, guidance gradient smoothed over +-0.005
_ASM = {}


def val_job(job: dict) -> dict:
    import dataclasses
    from disasm.oracle.cmgrrt import _setup_cd, exact_union, load_assembly, query, robot_sample_seed
    from disasm.oracle.cmgrrt_core import PlannerParams, seed_all
    from disasm.oracle.oracle_v2 import query_v2
    from disasm.oracle.path_validate import validate_path
    d = job["asm_dir"]
    if d not in _ASM:
        _ASM.clear()
        _ASM[d] = load_assembly(d)
    asm = _ASM[d]
    cfg = job["config"]
    removed, part, seed = set(job["removed"]), job["part"], job["seed"]
    if cfg == "v1":
        r = query(asm, removed, part, job["T"], seed, job["workdir"], detector="exact", eps=0.005, save_path=True)
    else:
        r = query_v2(asm, removed, part, job["T"], seed, job["workdir"], eps=0.005, always_cmgrrt=True,
                     save_path=True, margin=CONFIGS[cfg], grad_dx=GRAD_DX.get(cfg))
    keep = ["outcome", "time_s", "iterations", "error", "start_valid", "start_min_sdf", "escape_dir", "path_file",
            "precheck_free", "precheck_dir", "precheck_time_s", "cmgrrt_outcome", "cmgrrt_time_s", "cmgrrt_iterations",
            "n_goal_edges_rejected_fine", "n_paths_rejected_fine", "fine_check_s", "stage", "path_file_precheck",
            "margin_relief_parts", "tree_hash", "path_max_rot_deg"]
    out = {k: r.get(k) for k in keep}
    out.update({"config": cfg, "assembly_id": asm.id, "state_key": job["state_key"], "part_id": part, "seed": seed,
                "set": job["set"]})
    # independent re-check of every saved success path
    params = dataclasses.replace(PlannerParams(), threshold=-0.005)
    present = set(asm.part_ids) - removed
    chk = {}
    files = {"main": None, "cmgrrt": None}
    if cfg == "v1":
        files["cmgrrt"] = r.get("path_file") if r.get("outcome") == "success" else None
    else:
        if r.get("precheck_free"):
            files["main"] = r.get("path_file_precheck")
        if r.get("cmgrrt_outcome") == "success":
            files["cmgrrt"] = r.get("path_file") if r.get("path_file") != r.get("path_file_precheck") else None
            if not r.get("precheck_free"):
                files["main"] = files["cmgrrt"]
    if any(files.values()):
        union, _, _ = exact_union(asm, present - {part})
        seed_all(seed)
        cd = _setup_cd(asm, part, union, job["workdir"], params, "cpu", exact=True, sample_seed=robot_sample_seed(seed))
        S = np.asarray(cd.robot["sampling"], dtype=np.float64)
        for k, f in files.items():
            if f:
                v = validate_path(union, S, json.load(open(f))["path"], 0.005)
                chk[k] = {"valid": v["valid"], "n_bad": v["n_bad"], "d_min": v["d_min"]}
    out["recheck"] = chk
    return out
