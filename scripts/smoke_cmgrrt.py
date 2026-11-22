#!/usr/bin/env python
"""Run one bundled CMG-RRT example without editing its files.

1. Trains the obstacle neural SDF for <example>/0.obj (vertex-merged) into a cache dir
   outside external/ (upstream ships no .pth files), unless it is already cached.
2. Runs CMG-RRT from properties.json q1/q2_start/q2_end with test_list.json parameters.
3. Writes one JSON result line (success, iterations, wall time, ...) to --out.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from disasm.oracle.cmgrrt_core import PlannerParams, run_cmgrrt  # noqa: E402
from disasm.oracle.sdf_train import SDFTrainConfig, load_obj_merged, train_sdf, train_sdf_union  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--example", required=True, help="e.g. puzzle/elk or general/06397")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--iterations", type=int, default=5000, help="RRT iteration cap (test_list.json: 5000)")
    ap.add_argument("--timeout", type=float, default=600.0, help="wall-clock cap in seconds")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--sdf-cache", default=os.path.join(ROOT, "data/processed/cmgrrt_bundled_sdf"))
    ap.add_argument("--sdf-epochs", type=int, default=30)
    ap.add_argument("--sdf-samples", type=int, default=2_000_000)
    ap.add_argument("--sdf-batch", type=int, default=8192)
    ap.add_argument("--sdf-sign", default="quicksdf", choices=["quicksdf", "robust"],
                    help="quicksdf = upstream labelling; robust = |quicksdf| with winding-number sign")
    ap.add_argument("--threads", type=int, default=0, help="torch CPU threads (0 = torch default)")
    ap.add_argument("--out", required=True, help="jsonl file to append the result to")
    args = ap.parse_args()

    if args.threads:
        import torch
        torch.set_num_threads(args.threads)
    ex_dir = os.path.join(ROOT, "external/cmg-rrt/resources/models", args.example)
    props = json.load(open(os.path.join(ex_dir, "properties.json")))
    params = PlannerParams()
    if "sampling" in props:
        params.sampling = props["sampling"]

    cache = os.path.join(args.sdf_cache, args.example.replace("/", "_"))
    os.makedirs(cache, exist_ok=True)
    tag = "" if (args.sdf_batch == 8192 and args.sdf_sign == "quicksdf") else f"_b{args.sdf_batch}_{args.sdf_sign}"
    pth = os.path.join(cache, f"0_e{args.sdf_epochs}_n{args.sdf_samples}{tag}.pth")
    sdf_stats = None
    if not os.path.exists(pth):
        cfg = SDFTrainConfig(epochs=args.sdf_epochs, num_samples=args.sdf_samples, batch_size=args.sdf_batch)
        if args.sdf_sign == "robust":
            sdf_stats = train_sdf_union([load_obj_merged(os.path.join(ex_dir, "0.obj"))], pth, cfg,
                                        device="cuda", far_frac=0.0)
        else:
            sdf_stats = train_sdf(load_obj_merged(os.path.join(ex_dir, "0.obj")), pth, cfg, device="cuda")
        json.dump(sdf_stats, open(pth + ".json", "w"), indent=1)
        print("SDF trained:", json.dumps({k: v for k, v in sdf_stats.items() if k != "cfg"}), flush=True)
    else:
        sdf_stats = json.load(open(pth + ".json")) if os.path.exists(pth + ".json") else None
        print("SDF cached:", pth, flush=True)

    t0 = time.time()
    res = run_cmgrrt(os.path.join(ex_dir, "1.obj"), pth, props["q1"], props["q2_start"], props["q2_end"],
                     params, device=args.device, timeout_s=args.timeout,
                     max_iterations=args.iterations, seed=args.seed)
    res.update({"example": args.example, "sdf_path": pth, "sdf_stats": sdf_stats,
                "total_wall_s": time.time() - t0, "threads": args.threads,
                "sdf_epochs": args.sdf_epochs, "sdf_samples": args.sdf_samples, "sdf_batch": args.sdf_batch,
                "sdf_sign": args.sdf_sign})
    path = res.pop("path")
    if path:
        pp = os.path.splitext(args.out)[0] + f"_{args.example.replace('/', '_')}_{args.device}_path.json"
        json.dump(path, open(pp, "w"))
        res["path_file"] = pp
    print(json.dumps({k: v for k, v in res.items() if k != "sdf_stats"}), flush=True)
    with open(args.out, "a") as f:
        f.write(json.dumps(res) + "\n")


if __name__ == "__main__":
    main()
