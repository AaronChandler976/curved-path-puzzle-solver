#!/usr/bin/env python
"""R3 validation of the exact union-SDF detector (src/disasm/oracle/exact_sdf.py).

Subcommands (each appends to <outdir>/<sub>.jsonl and logs load info):
  start_valid   assembled-state start validity of every part of N v0 assemblies, exact detector, same robot
                sampling as the planner; the learned side is read from the v0 labels (the detector v0 used).
  poses         bundled examples: exact vs learned (R2 upstream-default SDF) validity at random poses near q2_start.
  s3            run 01's S3 query set (oracle_check_v2) re-run side by side: learned (cached SDFs) and exact.
  eps           epsilon sensitivity: assembled-state queries of N assemblies at several eps (exact detector).
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MULTI = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly")
V0 = os.path.join(ROOT, "data/labels/pilot_v0")


def v0_assemblies():
    ids, seen = [], set()
    for l in open(os.path.join(V0, "summary.jsonl")):
        r = json.loads(l)
        if r["status"] in ("complete", "stuck") and r["assembly_id"] not in seen:
            seen.add(r["assembly_id"]); ids.append(r["assembly_id"])
    return ids


# ------------------------------------------------------------------ workers (run inside slot-holding pool)
def w_start(job):
    import numpy as np
    from disasm.oracle.cmgrrt import load_assembly, exact_union, _setup_cd
    from disasm.oracle.cmgrrt_core import PlannerParams, seed_all
    from taucgl_rrt.cspace import SE3
    import dataclasses
    seed_all(job["seed"])
    asm = load_assembly(os.path.join(MULTI, job["asm"]))
    out = []
    for p in asm.part_ids:
        obst = set(asm.part_ids) - {p}
        t0 = time.time()
        union, t_u, first = exact_union(asm, obst)
        params = dataclasses.replace(PlannerParams(), threshold=-job["eps"])
        cd = _setup_cd(asm, p, union, job["workdir"], params, "cpu", exact=True)
        smin = float(cd.distance_between_objects(SE3()))
        out.append({"assembly_id": asm.id, "part_id": p, "start_min_sdf": smin, "start_valid": smin >= -job["eps"],
                    "eps": job["eps"], "setup_s": time.time() - t0, "part_setup_first": first,
                    "sign_modes": [ps.sign_mode for ps in union.parts]})
    return out


def w_query(job):
    from disasm.oracle.cmgrrt import load_assembly, query
    asm = load_assembly(os.path.join(MULTI, job["asm"]))
    t0 = time.time()
    r = query(asm, set(job["removed"]), job["part"], job["T"], job["seed"], job["workdir"], device="cpu",
              detector=job["detector"], eps=job.get("eps"), save_path=True)
    r["worker_wall_s"] = time.time() - t0
    r["tag"] = job.get("tag")
    r.pop("traceback", None) if not r.get("error") else None
    return r


def pool(n):
    from disasm.oracle import pool as P
    P.pin_threads(1)
    return ProcessPoolExecutor(n, mp_context=mp.get_context("spawn"), initializer=P._init,
                               initargs=({"workdir": "/tmp", "device": "cpu", "threads": 1,
                                          "slot_tag": "exact_sdf_validation"},))


def run_jobs(fn, jobs, outp, workers, log):
    n = 0
    with pool(workers) as ex:
        futs = [ex.submit(fn, j) for j in jobs]
        for f in as_completed(futs):
            r = f.result()
            rows = r if isinstance(r, list) else [r]
            with open(outp, "a") as fo:
                for x in rows:
                    fo.write(json.dumps(x) + "\n")
            n += 1
            log(f"{n}/{len(jobs)} " + json.dumps({k: rows[0].get(k) for k in ("assembly_id", "part_id", "outcome",
                                                                                  "time_s", "start_valid", "tag")}))


# ------------------------------------------------------------------ poses (bundled, single process)
def poses(args, log):
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation as Rot
    from disasm.oracle.exact_sdf import ExactUnionSDF, PartSDF, make_detector
    from disasm.oracle.cmgrrt_core import PlannerParams, seed_all
    from disasm.util.slots import acquire_slot
    from taucgl_rrt.cspace import SE3
    from taucgl_rrt.collision_detection import CollisionDetector
    import trimesh
    slot = acquire_slot(tag="exact_sdf_validation_poses")
    outp = os.path.join(args.outdir, "poses.jsonl")
    for ex in args.examples:
        seed_all(0)
        d = os.path.join(ROOT, "external/cmg-rrt/resources/models", ex)
        props = json.load(open(os.path.join(d, "properties.json")))
        pth = os.path.join(ROOT, "data/processed/cmgrrt_bundled_sdf/upstream_defaults", ex.replace("/", "_"), "0_sdf.pth")
        if not os.path.exists(pth):
            log(f"{ex}: no R2 SDF at {pth}, skipped"); continue
        q1, qs = SE3(*props["q1"]), SE3(*props["q2_start"])
        P = PlannerParams()
        lcd = CollisionDetector(P.sdf_N, P.sdf_H, torch.device("cuda"), P.threshold, P.eta, abs(P.threshold))
        lcd.set_robot(os.path.join(d, "1.obj")); lcd.generate_robot_sampling(P.sampling); lcd.set_obstacles(pth, q1)
        m0 = trimesh.load_mesh(os.path.join(d, "0.obj"), process=True)
        t0 = time.time()
        part = PartSDF(m0.vertices, m0.faces, name=ex)
        setup = time.time() - t0
        union = ExactUnionSDF([part])
        ecd = make_detector(P, "cpu", union, q1=q1)
        ecd.robot = lcd.robot                                  # identical robot samples for both detectors
        for k in ("sampling_tensor", "reduced_sampling_tensor", "radii_tensor"):
            ecd.robot[k] = lcd.robot[k]
        samp = lcd.robot["sampling_tensor"]
        rng = np.random.default_rng(0)
        rows = []
        tl = te = 0.0
        for i in range(args.n_poses):
            dt = rng.normal(0, args.sigma_t, 3)
            rv = Rot.from_rotvec(rng.normal(0, np.radians(args.sigma_deg), 3))
            Rs = Rot.from_quat([qs.b, qs.c, qs.d, qs.a])
            R = rv * Rs
            x, y, z, w = R.as_quat()
            q = SE3(*(qs.pos() + dt), w, x, y, z)
            a = time.time(); fl = lcd.eval_sampling(q); tl += time.time() - a
            a = time.time(); fe = union(lcd.transform_sampling(q, samp).cpu()).numpy(); te += time.time() - a
            rows.append((float(fl.min()), float(fe.min())))
        L = np.array(rows)
        vl, ve = L[:, 0] >= P.threshold, L[:, 1] >= P.threshold
        bins = {}
        for lo, hi in [(-1e9, -0.02), (-0.02, -0.005), (-0.005, 0.0), (0.0, 0.005), (0.005, 0.02), (0.02, 1e9)]:
            s = (L[:, 1] >= lo) & (L[:, 1] < hi)
            bins[f"[{lo},{hi})"] = {"n": int(s.sum()), "agree": float((vl[s] == ve[s]).mean()) if s.any() else None}
        res = {"example": ex, "n_poses": args.n_poses, "sigma_t": args.sigma_t, "sigma_deg": args.sigma_deg,
               "threshold": P.threshold, "agreement": float((vl == ve).mean()), "valid_learned": float(vl.mean()),
               "valid_exact": float(ve.mean()), "learned_valid_exact_invalid": int((vl & ~ve).sum()),
               "learned_invalid_exact_valid": int((~vl & ve).sum()),
               "start_min_sdf_learned": float(lcd.distance_between_objects(qs)),
               "start_min_sdf_exact": float(union(lcd.transform_sampling(qs, samp).cpu()).min()),
               "min_sdf_abs_diff_p50_p95": [float(np.percentile(np.abs(L[:, 0] - L[:, 1]), q)) for q in (50, 95)],
               "agreement_by_exact_min_sdf": bins, "exact_setup_s": setup, "eval_s_learned_cuda": tl,
               "eval_s_exact_cpu": te, "sign_mode": part.sign_mode, "sign_check": part.sign_check,
               "obstacle_mesh": "0.obj", "learned_sdf": pth}
        log(json.dumps(res))
        with open(outp, "a") as f:
            f.write(json.dumps(res) + "\n")
    slot.release()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sub", choices=["start_valid", "poses", "s3", "eps"])
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--eps", type=float, nargs="+", default=[0.005])
    ap.add_argument("--T", type=float, default=30.0)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--examples", nargs="+", default=["general/11356", "general/06397", "puzzle/key_light_1"])
    ap.add_argument("--n-poses", type=int, default=10000)
    ap.add_argument("--sigma-t", type=float, default=0.01)
    ap.add_argument("--sigma-deg", type=float, default=2.0)
    args = ap.parse_args()
    from disasm.util.runlog import log_load
    os.makedirs(args.outdir, exist_ok=True)
    work = os.path.join(args.outdir, "work"); os.makedirs(work, exist_ok=True)
    logf = open(os.path.join(args.outdir, f"{args.sub}.log"), "a")

    def log(m):
        line = f"[{time.strftime('%H:%M:%S')}] {m}"
        print(line, flush=True); logf.write(line + "\n"); logf.flush()

    log_load(args.outdir, f"start {args.sub}")
    t0 = time.time()
    outp = os.path.join(args.outdir, f"{args.sub}.jsonl")
    if args.sub == "start_valid":
        jobs = [{"asm": a, "eps": e, "seed": 0, "workdir": work} for a in v0_assemblies()[: args.n] for e in args.eps]
        run_jobs(w_start, jobs, outp, args.workers, log)
    elif args.sub == "poses":
        poses(args, log)
    elif args.sub == "s3":
        s3 = [json.loads(l) for l in open(os.path.join(ROOT, "experiments/2026-11-22_oracle_check_v2/results.jsonl"))]
        jobs = []
        for det in ("learned", "exact"):
            for r in s3:
                jobs.append({"asm": r["assembly_id"], "removed": r["removed"], "part": r["part_id"], "T": r["timeout_s"],
                             "seed": r["seed"], "workdir": work, "detector": det, "eps": None, "tag": det})
        # one detector at a time (timing hygiene): learned block first, then exact
        for det in ("learned", "exact"):
            run_jobs(w_query, [j for j in jobs if j["detector"] == det], outp, args.workers, log)
    elif args.sub == "eps":
        ids = v0_assemblies()[: args.n]
        from disasm.oracle.cmgrrt import load_assembly
        for e in args.eps:
            jobs = []
            for a in ids:
                asm = load_assembly(os.path.join(MULTI, a))
                for p in asm.part_ids:
                    jobs.append({"asm": a, "removed": [], "part": p, "T": args.T, "seed": 0, "workdir": work,
                                 "detector": "exact", "eps": e, "tag": f"eps{e:g}"})
            run_jobs(w_query, jobs, outp, args.workers, log)
    log(f"DONE {args.sub} in {time.time() - t0:.0f}s")
    log_load(args.outdir, f"end {args.sub}")


if __name__ == "__main__":
    main()
