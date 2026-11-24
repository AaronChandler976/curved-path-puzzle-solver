#!/usr/bin/env python
"""Run 05: latency and memory profile of every ranker (one checkpoint each, the first seed), on val states.

Per model: parameter count; inference time per state on CPU (1 thread and all threads) and GPU, at batch 1 (one state
per forward, the deployment case: the ranker is called once per visited state) and batched (256 states per forward);
peak GPU memory (torch.cuda.max_memory_allocated) and peak CPU RSS increase. Feature extraction (contact graph +
features from the cached contact graph) is timed separately on CPU for 50 states. Timing = median of repeated runs
after warm-up, time.perf_counter, torch.cuda.synchronize around GPU calls.
Planner time saved (from the val replay results.json): (best heuristic total - model total) / number of scored states,
compared with the ranker's per-state latency.
Run alone (timing hygiene; load logged at start/end).
"""
import argparse
import json
import os
import resource
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def timeit(fn, reps, sync=False):
    for _ in range(3):
        fn()
    ts = []
    for _ in range(reps):
        if sync:
            torch.cuda.synchronize()
        t0 = time.perf_counter(); fn()
        if sync:
            torch.cuda.synchronize()
        ts.append(time.perf_counter() - t0)
    return float(np.median(ts))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--methods", required=True)
    ap.add_argument("--val-results", required=True, help="eval_v2.py results.json on val")
    ap.add_argument("--redmax", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--md", required=True)
    ap.add_argument("--n-states", type=int, default=200)
    a = ap.parse_args()
    from disasm.util.runlog import log_load
    os.makedirs(a.outdir, exist_ok=True)
    log_load(a.outdir, "start")
    P = os.path.join(ROOT, "data/processed/run05")
    G = [g for g in torch.load(os.path.join(P, "graphs_train_val.pt"), weights_only=False) if g["split"] == "val" and g["succ"].any()]
    rng = np.random.default_rng(0)
    G = [G[i] for i in sorted(rng.choice(len(G), min(a.n_states, len(G)), replace=False))]
    methods = json.load(open(a.methods))
    clouds = torch.load(os.path.join(P, "clouds_train_val.pt"), weights_only=False)
    from train_v2 import Batcher, build_model, forward, VARIANTS
    from train_asap_v2 import load_inputs, make_data
    from torch_geometric.data import Batch
    C = load_inputs({g["aid"] for g in G}, a.redmax, os.path.join(P, "asap_inputs_val.pt"), 10)
    R = json.load(open(a.val_results))["configs"]["main"]
    heur = R["best_heuristic"]
    n_scored = R["n_scored"]
    rows = []
    for var, cks in list(methods.items()) + [("asap_zs", None)]:
        row = {"variant": var}
        if var in ("asap_zs", "asap_retrained"):
            from disasm.search.asap_baseline import load_asap_model
            m = load_asap_model()[0]
            if var == "asap_retrained":
                from disasm.models.asap_train import new_asap_model
                m = new_asap_model(0)
                m.load_state_dict(torch.load(os.path.join(ROOT, cks[0]), weights_only=False, map_location="cpu")["model_state_dict"])
            data = make_data(G, C, False)

            def mk(dev, items):
                return Batch.from_data_list(items).to(dev)

            def fwd(model, b):
                return model.forward_logits(b)
            items = data
        else:
            d = torch.load(os.path.join(ROOT, cks[0]), weights_only=False, map_location="cpu")
            m = build_model(var, d["cfg"], G[0]["T"]); m.load_state_dict(d["state_dict"])
            norm = [t.cpu() for t in d["norm"]]
            cl = clouds if VARIANTS[var][3] else None

            def mk(dev, items, norm=norm, cl=cl):
                return Batcher(norm, dev, cl)(items)

            def fwd(model, b):
                return forward(model, b)
            items = G
        m.eval()
        row["n_params"] = int(sum(p.numel() for p in m.parameters()))
        with torch.no_grad():
            for dev, threads in (("cpu", 1), ("cpu", os.cpu_count()), ("cuda", None)):
                if threads:
                    torch.set_num_threads(threads)
                mm = m.to(dev)
                tag = f"{dev}{'' if threads is None else f'_t{threads}'}"
                sync = dev == "cuda"
                if sync:
                    torch.cuda.reset_peak_memory_stats()
                b1 = [mk(dev, [x]) for x in items[:50]]
                k = [0]

                def one():
                    fwd(mm, b1[k[0] % len(b1)]); k[0] += 1
                row[f"{tag}_batch1_ms"] = 1000 * timeit(one, 100, sync)
                bb = mk(dev, items[:256])
                row[f"{tag}_batch256_ms_per_state"] = 1000 * timeit(lambda: fwd(mm, bb), 10, sync) / len(items[:256])
                if sync:
                    row["gpu_peak_mem_MB"] = torch.cuda.max_memory_allocated() / 2**20
        row["cpu_maxrss_MB_process"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        key = var
        if key in R["all"]:
            saved = (R["all"][heur]["total"][0] - R["all"][key]["total"][0]) / n_scored
            row["planner_s_saved_per_state_vs_best_heuristic"] = saved
            row["planner_s_saved_per_state_vs_random"] = (R["all"]["random"]["total"][0] - R["all"][key]["total"][0]) / n_scored
        rows.append(row)
        print(json.dumps(row), flush=True)
    # feature extraction (CPU): contact graph from cache + state features
    from disasm.oracle.cmgrrt import load_assembly
    from disasm.data.graph import state_graph_v3
    RAW = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly")
    fe = []
    for g in G[:50]:
        asm = load_assembly(os.path.join(RAW, g["aid"]))
        t0 = time.perf_counter(); state_graph_v3(asm, list(g["present"])); fe.append(time.perf_counter() - t0)
    feat_ms = 1000 * float(np.median(fe))
    json.dump({"rows": rows, "feature_extraction_ms_median": feat_ms, "n_states": len(G), "best_heuristic": heur},
              open(os.path.join(a.outdir, "profile.json"), "w"), indent=1)
    L = ["# Run 05: ranker latency and memory (val states)\n",
         f"Script `scripts/profile_rankers.py`; raw `{os.path.relpath(a.outdir, ROOT)}/profile.json`; load at start/end in "
         f"`{os.path.relpath(a.outdir, ROOT)}/load_info.txt`. {len(G)} val states (seeded sample); median over repeats. "
         f"Feature extraction (state graph from the cached contact graph, CPU): **{feat_ms:.2f} ms** per state (median, 50 states).\n",
         f"| model | params | CPU 1 thread, batch 1 (ms/state) | CPU {os.cpu_count()} threads, batch 1 | CPU batched (ms/state) | GPU batch 1 (ms/state) | GPU batched (ms/state) | GPU peak mem (MB) | planner s saved / state vs {heur} |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        sv = r.get("planner_s_saved_per_state_vs_best_heuristic")
        L.append(f"| {r['variant']} | {r['n_params']:,} | {r['cpu_t1_batch1_ms']:.2f} | {r[f'cpu_t{os.cpu_count()}_batch1_ms']:.2f} | "
                 f"{r[f'cpu_t{os.cpu_count()}_batch256_ms_per_state']:.3f} | {r['cuda_batch1_ms']:.2f} | {r['cuda_batch256_ms_per_state']:.4f} | "
                 f"{r['gpu_peak_mem_MB']:.0f} | {'' if sv is None else f'{sv:+.2f}'} |")
    open(a.md, "w").write("\n".join(L) + "\n")
    log_load(a.outdir, "end")
    print("\n".join(L))


if __name__ == "__main__":
    main()
