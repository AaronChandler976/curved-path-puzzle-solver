#!/usr/bin/env python
"""R2 clean CMG-RRT reproduction on a bundled example (one process, one example, one seed).

Two phases, both faithful to upstream (external/cmg-rrt, unmodified):

1. SDF ("their default learned SDF"): upstream ships no .pth, so we train one with the
   hyper-parameters of taucgl_sdf/train.py's argparse defaults: deepsdf sampling (10M train /
   100k valid, alpha 0.8, boundary sigma 0.05, normal sigma 0.7, quicksdf labels), SDFModel(12, 64),
   clamp 0.1, L1(sum), Adam lr 1e-4 constant, batch 2048, 100 epochs, NO shuffle (upstream
   DataLoader default). Only difference: the tensors sit on the GPU and are sliced in the same
   order instead of going through a CPU DataLoader (same batches, same math, faster).
   Per-epoch train/valid loss is logged (convergence check). Cached; trained once per example.
2. Plan: the loop of scripts/test_all.py with scripts/test_list.json settings (eta 0.002,
   threshold -0.005, steps 50, iterations 5000, sampling 4000 unless properties.json overrides,
   sdf N=12 H=64, device cuda). Constructor signatures as in scripts/debug_rrt.py (test_all.py's
   are stale): CollisionDetector(N, H, dev, threshold, eta, |threshold|), RRT(cd, q1, qs, qe).
   Extra: a wall-clock cap (--cap-min); seeds for random/numpy/torch (upstream does not seed).
"""
import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EX_ROOT = os.path.join(ROOT, "external/cmg-rrt/resources/models")
TEST_LIST = os.path.join(ROOT, "external/cmg-rrt/scripts/test_list.json")
SDF_DIR = os.path.join(ROOT, "data/processed/cmgrrt_bundled_sdf/upstream_defaults")


def train_upstream_sdf(mesh_path, out_path, log, device="cuda", threads=12, seed=0):
    import numpy as np
    import torch
    import torch.nn as nn
    import trimesh
    from taucgl_sdf.sampling import deepsdf_sampling
    from taucgl_sdf.model import SDFModel
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    a = dict(num_samples=10_000_000, valid_samples=100_000, deepsdf_alpha=0.8, boundary_mu=0.0,
             boundary_sigma=5e-2, normal_mu=0.0, normal_sigma=0.7, batch_size=2048, learning_rate=1e-4,
             num_epochs=100, clamping_delta=0.1, N=12, H=64)
    mesh = trimesh.load_mesh(mesh_path)
    t0 = time.time()
    s, s_sdf = deepsdf_sampling(mesh, a["num_samples"], a["deepsdf_alpha"], a["boundary_mu"], a["boundary_sigma"],
                                a["normal_mu"], a["normal_sigma"], threads)
    v, v_sdf = deepsdf_sampling(mesh, a["valid_samples"], a["deepsdf_alpha"], a["boundary_mu"], a["boundary_sigma"],
                                a["normal_mu"], a["normal_sigma"], threads)
    t_samp = time.time() - t0
    log(f"sampling {t_samp:.1f}s (mesh {mesh_path}, watertight={mesh.is_watertight}, faces={len(mesh.faces)})")
    dev = torch.device(device)
    d = a["clamping_delta"]
    X = torch.tensor(s).float().to(dev); Y = torch.clamp(torch.tensor(s_sdf).float(), -d, d).to(dev)
    VX = torch.tensor(v).float().to(dev); VY = torch.clamp(torch.tensor(v_sdf).float(), -d, d).to(dev)
    model = SDFModel(a["N"], a["H"]).to(dev)
    crit = nn.L1Loss(reduction="sum")
    opt = torch.optim.Adam(model.parameters(), lr=a["learning_rate"])
    B = a["batch_size"]
    hist = []
    for ep in range(a["num_epochs"]):
        te = time.time()
        tot, nb = 0.0, 0
        for i in range(0, X.shape[0], B):
            xyz, sdf = X[i:i + B], Y[i:i + B]
            model.zero_grad()
            out = torch.clamp(model(xyz), -d, d).flatten()
            loss = crit(out, sdf)
            loss.backward()
            opt.step()
            tot += loss.detach() / out.shape[0]
            nb += 1
        with torch.no_grad():
            vl = 0.0
            for i in range(0, VX.shape[0], B):
                out = torch.clamp(model(VX[i:i + B]), -d, d).flatten()
                vl += float(crit(out, VY[i:i + B]))
            vl /= VX.shape[0]
            near = VY.abs() < 0.02
            vo = torch.cat([torch.clamp(model(VX[i:i + 65536]), -d, d).flatten() for i in range(0, VX.shape[0], 65536)])
            sign_agree = float(((vo[near] > 0) == (VY[near] > 0)).float().mean())
        hist.append({"epoch": ep, "train_l1": float(tot) / nb, "valid_l1": vl, "near_sign_agree": sign_agree,
                     "epoch_s": time.time() - te})
        log(f"epoch {ep} train {float(tot) / nb:.6f} valid {vl:.6f} near-surface sign agree {sign_agree:.4f} "
            f"({time.time() - te:.1f}s)")
    tmp = out_path + ".tmp"
    torch.save(model.state_dict(), tmp)
    os.replace(tmp, out_path)
    st = {"hyper": a, "mesh": mesh_path, "sampling_s": t_samp, "train_s": time.time() - t0 - t_samp,
          "total_s": time.time() - t0, "history": hist, "seed": seed, "device": device}
    json.dump(st, open(out_path + ".json", "w"), indent=1)
    return st


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--example", required=True, help="e.g. puzzle/elk")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--cap-min", type=float, required=True, help="wall-clock cap for the planner (minutes)")
    ap.add_argument("--sdf-mesh", default="0_sdf.obj", choices=["0_sdf.obj", "0.obj"])
    ap.add_argument("--threshold", type=float, default=None, help="override (diagnostics only)")
    ap.add_argument("--steps", type=int, default=None, help="override (diagnostics only)")
    ap.add_argument("--sampling", type=int, default=None, help="override (diagnostics only)")
    ap.add_argument("--train-only", action="store_true")
    ap.add_argument("--detector", default="learned", choices=["learned", "exact"],
                    help="exact = run 02 exact SDF of 0.obj (src/disasm/oracle/exact_sdf.py), same planner")
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--iterations", type=int, default=None, help="override test_list.json iterations (run 04 T9 elk)")
    ap.add_argument("--idle-wait", type=float, default=0.0, help="s of non-busy before planning (run 04: 300)")
    ap.add_argument("--no-guard", action="store_true", help="no idle sampler (pre-run-04 behaviour)")
    ap.add_argument("--unseeded-samples", action="store_true", help="library behaviour: unseeded robot samples")
    ap.add_argument("--grad-dx", type=float, default=None,
                    help="run 04 T5 hybrid: exact SDF decisions, guidance gradient by central differences over +-grad_dx")
    args = ap.parse_args()
    from disasm.util.runlog import log_load
    from disasm.util.slots import acquire_slot
    os.makedirs(args.run_dir, exist_ok=True)
    tag = f"{args.example.replace('/', '_')}_s{args.seed}" + ("_exact" if args.detector == "exact" else "") + \
        (f"_gdx{args.grad_dx:g}" if args.grad_dx else "")
    logf = open(os.path.join(args.run_dir, f"{tag}.log"), "a")

    def log(m):
        line = f"[{time.strftime('%H:%M:%S')}] {m}"
        print(line, flush=True)
        logf.write(line + "\n"); logf.flush()

    slot = acquire_slot(tag=f"repro_{tag}")
    guard = None
    if not args.no_guard:   # run 04: single long timed run -> busy samples logged throughout
        from disasm.util.idle_guard import IdleSampler, IdleClient
        gdir = os.path.join(args.run_dir, f"guard_{tag}")
        guard = IdleSampler(gdir, tag=tag).start()
        if args.idle_wait > 0:
            log(f"waiting for {args.idle_wait:.0f} s non-busy")
            guard.wait_idle(args.idle_wait, log=log)
    log_load(args.run_dir, f"start {tag}")
    cfg = json.load(open(TEST_LIST))
    if args.iterations:
        cfg["iterations"] = args.iterations
    ex = os.path.join(EX_ROOT, args.example)
    props = json.load(open(os.path.join(ex, "properties.json")))
    sampling = props.get("sampling", cfg["sampling"])
    if args.sampling:
        sampling = args.sampling
    eta = cfg["eta"]
    threshold = cfg["threshold"] if args.threshold is None else args.threshold
    steps = cfg["steps"] if args.steps is None else args.steps
    device = cfg["device"]
    sdf_dir = os.path.join(SDF_DIR, args.example.replace("/", "_"))
    os.makedirs(sdf_dir, exist_ok=True)
    pth = os.path.join(sdf_dir, args.sdf_mesh.replace(".obj", ".pth"))
    if not os.path.exists(pth) and args.detector == "learned":
        log(f"training upstream-default SDF -> {pth}")
        st = train_upstream_sdf(os.path.join(ex, args.sdf_mesh), pth, log, device=device)
        log(f"SDF done total {st['total_s']:.0f}s final valid {st['history'][-1]['valid_l1']:.6f}")
    if args.train_only:
        log_load(args.run_dir, f"end {tag}")
        return

    import numpy as np
    import torch
    from taucgl_rrt.cspace import SE3
    from taucgl_rrt.collision_detection import CollisionDetector
    from taucgl_rrt.rrt import RRT
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    dev = torch.device(device)
    q1, qs, qe = SE3(*props["q1"]), SE3(*props["q2_start"]), SE3(*props["q2_end"])
    t_s = time.time()
    if args.detector == "exact":
        import trimesh
        from disasm.oracle.exact_sdf import ExactUnionSDF, PartSDF, make_detector
        from disasm.oracle.cmgrrt_core import PlannerParams
        m0 = trimesh.load_mesh(os.path.join(ex, "0.obj"), process=True)
        part = PartSDF(m0.vertices, m0.faces, name=args.example)
        log(f"exact SDF of 0.obj: {json.dumps(part.meta())}")
        pp = PlannerParams(eta=eta, threshold=threshold, steps=steps, sampling=sampling)
        cd = make_detector(pp, device, ExactUnionSDF([part]), q1=q1, grad_dx=args.grad_dx)
        pth = "exact:0.obj"
    else:
        cd = CollisionDetector(cfg["sdf-N"], cfg["sdf-H"], dev, threshold, eta, abs(threshold))
    cd.set_robot(os.path.join(ex, "1.obj"))
    from disasm.oracle.cmgrrt import robot_sample_seed, seeded_surface_sampling
    with seeded_surface_sampling(None if args.unseeded_samples else robot_sample_seed(args.seed)):
        cd.generate_robot_sampling(sampling)
    if args.detector == "learned":
        cd.set_obstacles(pth, q1)
    start_sdf = float(cd.distance_between_objects(qs))
    goal_sdf = float(cd.distance_between_objects(qe))
    setup_s = time.time() - t_s
    rrt = RRT(cd, q1, qs, qe)
    t_plan0 = time.time()
    log(f"plan {args.example} seed {args.seed} eta {eta} thr {threshold} steps {steps} sampling {sampling} "
        f"iters {cfg['iterations']} cap {args.cap_min} min device {device}; start_sdf {start_sdf:.5f} "
        f"goal_sdf {goal_sdf:.5f}")
    idx, t0, solved = 1, time.time(), False
    while True:
        solved = bool(rrt.step(eta, threshold, steps))
        idx += 1
        el = time.time() - t0
        if idx % 50 == 0:
            log(f"iter {idx} {el:.0f}s nodes {rrt.tree.number_of_nodes()}")
        if solved or idx > cfg["iterations"] or el > args.cap_min * 60:
            break
    wall = time.time() - t0
    path = rrt.get_path() if solved else []
    if solved:
        json.dump([p.to_numpy().tolist() for p in path], open(os.path.join(args.run_dir, f"{tag}_path.json"), "w"))
    t_plan1 = time.time()
    stop = "solved" if solved else ("iterations" if idx > cfg["iterations"] else "wall_cap")
    busy = {}
    if guard is not None:
        import time as _t
        _t.sleep(6)
        bf, nb = IdleClient(guard.run_dir).busy_frac(t_plan0, t_plan1)
        busy = {"busy_frac": bf, "busy_samples": nb, "confounded": bf > 0.05, "guard_dir": guard.run_dir}
    fine = None
    if solved and args.detector == "exact":   # run 04: fine re-check of the path (exact SDF, step <= |thr|/2)
        from disasm.oracle.path_validate import validate_path
        S = np.asarray(cd.robot["sampling"], dtype=np.float64)
        # obstacle frame q1: express the robot poses relative to q1 (Aq2 = inv(A(q1)) A(q2)) -> map samples by q1^-1 q2
        Ainv = np.linalg.inv(q1.to_matrix())
        rel = []
        from scipy.spatial.transform import Rotation as Rr
        for p_ in path:
            M = Ainv @ p_.to_matrix()
            qx = Rr.from_matrix(M[:3, :3]).as_quat()
            rel.append([*M[:3, 3], qx[3], qx[0], qx[1], qx[2]])
        v = validate_path(cd.obstacles["sdf"], S, rel, abs(threshold))
        fine = {"valid": v["valid"], "n_bad": v["n_bad"], "d_min": v["d_min"]}
    res = {"example": args.example, "seed": args.seed, "success": solved, "stop": stop,
           "iterations": idx - 1 if solved else idx - 1, "upstream_idx_counter": idx, "planner_wall_s": wall,
           "setup_s": setup_s, "start_sdf": start_sdf, "goal_sdf": goal_sdf, "tree_nodes": rrt.tree.number_of_nodes(),
           "path_nodes": len(path), "eta": eta, "threshold": threshold, "steps": steps, "sampling": sampling,
           "max_iterations": cfg["iterations"], "cap_min": args.cap_min, "device": device, "sdf": pth,
           "sdf_mesh": args.sdf_mesh, "detector": args.detector, "load_info": os.path.join(args.run_dir, "load_info.txt"),
           "seeded_samples": not args.unseeded_samples, "fine_path_check": fine, "grad_dx": args.grad_dx, **busy}
    log("RESULT " + json.dumps(res))
    with open(os.path.join(args.run_dir, "results.jsonl"), "a") as f:
        f.write(json.dumps(res) + "\n")
    log_load(args.run_dir, f"end {tag}")
    if guard is not None:
        guard.stop()
    slot.release()


if __name__ == "__main__":
    main()
