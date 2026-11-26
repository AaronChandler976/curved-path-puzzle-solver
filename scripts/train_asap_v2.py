#!/usr/bin/env python
"""Run 05: ASAP-retrained (docs/PREREG_run05.md §1, §3). ASAP's ModelGraph, fresh init, ASAP's objective
(BCEWithLogits, one positive = the removed part, 90-degree random-axis rotation augmentation; src/disasm/models/asap_train.py),
ASAP inputs with ASAP's own redmax contact graph (scripts/asap_contact_graphs.py output, --redmax).

Fixed: ASAP architecture constants (feat 512, batch norm, dropout 0), Adam, <= 150 epochs.
Grid: lr {1e-3, 3e-4, 1e-4} x batch {16, 32} (6 configs). Same early stopping as every variant: val total replay
planner cost (MAIN config) ordering by sigmoid(logit), 5-epoch trailing mean, min 10 epochs, patience 25.
Configs ranked by the mean over grid seeds 0,1,2; the chosen config is retrained with seeds 100-104.
Training states: train states with a removal (= >= 1 main-config success). Val metric: val states with >= 1 success.
The test split is never loaded. Resumable (a run with result.json is skipped).
"""
import argparse
import csv
import itertools
import json
import multiprocessing as mp
import os
import random
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly")


def _ni(aid):
    torch.set_num_threads(1)
    from disasm.search.asap_baseline import asap_node_inputs
    return aid, asap_node_inputs(os.path.join(RAW, aid), aid)


def load_inputs(aids, redmax_path, cache, procs):
    if os.path.exists(cache):
        C = torch.load(cache, weights_only=False)
        if set(aids) <= set(C):
            return C
    pairs = {}
    for l in open(redmax_path):
        r = json.loads(l)
        if r.get("error"):
            raise SystemExit(f"redmax error for {r['assembly_id']}: {r['error']}")
        pairs[r["assembly_id"]] = {tuple(sorted(e)) for e in r["edges"]}
    missing = sorted(set(aids) - set(pairs))
    if missing:
        raise SystemExit(f"no redmax contact graph for {len(missing)} assemblies, e.g. {missing[:5]}")
    with mp.get_context("spawn").Pool(procs) as p:
        ni = dict(p.map(_ni, sorted(aids), chunksize=8))
    C = {aid: {"ni": ni[aid], "pairs": pairs[aid]} for aid in aids}
    torch.save(C, cache)
    return C


def make_data(graphs, C, with_y):
    from disasm.models.asap_train import state_data
    out = []
    for g in graphs:
        ch = g["chosen"] if with_y else -1
        d = state_data(C[g["aid"]]["ni"], C[g["aid"]]["pairs"], list(g["present"]), ch)
        out.append(d)
    return out


@torch.no_grad()
def predict(model, data, dev, bs=64):
    from torch_geometric.data import Batch
    model.eval()
    out = []
    for i in range(0, len(data), bs):
        b = Batch.from_data_list(data[i:i + bs]).to(dev)
        lg = model.forward_logits(b).reshape(-1)
        s = torch.sigmoid(lg).cpu().numpy()
        ptr = b.ptr.cpu().numpy()
        for j in range(len(ptr) - 1):
            out.append(s[ptr[j]:ptr[j + 1]])
    return out


def val_cost(scores, graphs):
    from disasm.models.ranker3 import replay_cost
    tot, nq = 0.0, 0
    for s, g in zip(scores, graphs):
        c, n = replay_cost(s, g["time_s"].numpy(), g["succ"].numpy())
        tot += c; nq += n
    return tot, nq


def train_one(cfg, trd, vad, va, outdir, dev, log):
    from disasm.models.asap_train import new_asap_model, train_epoch
    rp = os.path.join(outdir, "result.json")
    if os.path.exists(rp):
        r = json.load(open(rp))
        log(f"{os.path.basename(outdir)}: exists (best {r['best_val_cost']:.1f}), skipped")
        return r
    os.makedirs(outdir, exist_ok=True)
    model = new_asap_model(cfg["seed"]).to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=cfg["lr"])
    rng = random.Random(cfg["seed"])
    rows, best, best_ep, bad, hist = [], float("inf"), -1, 0, []
    t0 = time.time()
    for ep in range(cfg["max_epochs"]):
        loss, acc = train_epoch(model, trd, opt, cfg["batch"], rng, dev, rotate=True)
        vm, vq = val_cost(predict(model, vad, dev), va)
        hist.append(vm)
        W = cfg["smooth"]
        sm = float(np.mean(hist[-W:])) if len(hist) >= W else float("inf")
        rows.append({"epoch": ep, "train_loss": loss, "train_top1": acc, "val_cost": vm, "val_queries": vq,
                     "val_cost_smoothed": sm if np.isfinite(sm) else ""})
        if not np.isfinite(sm):
            continue
        if sm < best - 1e-9:
            best, best_ep, bad = sm, ep, 0
            torch.save({"model_state_dict": model.state_dict(), "cfg": cfg, "variant": "asap_retrained", "epoch": ep,
                        "val_cost": vm, "val_cost_smoothed": sm}, os.path.join(outdir, "best.pt"))
        else:
            bad += 1
        if bad >= cfg["patience"] and ep + 1 >= cfg["min_epochs"]:
            break
    with open(os.path.join(outdir, "metrics.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    res = {**cfg, "variant": "asap_retrained", "best_val_cost": best, "best_epoch": best_ep, "epochs_run": len(rows),
           "train_s": time.time() - t0, "n_params": sum(p.numel() for p in model.parameters())}
    json.dump(res, open(rp, "w"), indent=1)
    log(f"{os.path.basename(outdir)}: best smoothed val cost {best:.1f} s at epoch {best_ep} ({len(rows)} epochs, {time.time() - t0:.0f} s)")
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--graphs", default=os.path.join(ROOT, "data/processed/run05/graphs_train_val.pt"))
    ap.add_argument("--redmax", required=True, help="asap_contact_graphs.py jsonl covering train+val assemblies")
    ap.add_argument("--cache", default=os.path.join(ROOT, "data/processed/run05/asap_inputs_train_val.pt"))
    ap.add_argument("--grid-seeds", default="0,1,2")
    ap.add_argument("--seeds", default="100,101,102,103,104")
    ap.add_argument("--max-epochs", type=int, default=150)
    ap.add_argument("--patience", type=int, default=25)
    ap.add_argument("--min-epochs", type=int, default=10)
    ap.add_argument("--smooth", type=int, default=5)
    ap.add_argument("--procs", type=int, default=10)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    vdir = os.path.join(a.outdir, "asap_retrained")
    os.makedirs(vdir, exist_ok=True)
    logf = open(os.path.join(vdir, "train_log.txt"), "a")

    def log(s):
        s = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {s}"
        print(s, flush=True); logf.write(s + "\n"); logf.flush()

    from disasm.util.runlog import log_load
    log_load(vdir, "start")
    G = torch.load(a.graphs, weights_only=False)
    assert all(g["split"] in ("train", "val") for g in G), "test graphs present: refusing"
    tr = [g for g in G if g["split"] == "train" and g["chosen"] is not None]
    va = [g for g in G if g["split"] == "val" and bool(g["succ"].any())]
    C = load_inputs({g["aid"] for g in tr + va}, a.redmax, a.cache, a.procs)
    trd, vad = make_data(tr, C, True), make_data(va, C, False)
    log(f"asap_retrained: train {len(trd)} states, val {len(vad)} states")
    base = {"max_epochs": 3 if a.quick else a.max_epochs, "patience": a.patience,
            "smooth": 1 if a.quick else a.smooth, "min_epochs": 0 if a.quick else a.min_epochs,
            "feat_len": 512, "batch_norm": 1, "dropout": 0.0, "optimizer": "Adam"}
    grid = list(itertools.product([1e-3, 3e-4, 1e-4], [16, 32]))
    gseeds = [int(x) for x in a.grid_seeds.split(",")]
    fseeds = [int(x) for x in a.seeds.split(",")]
    if a.quick:
        grid, gseeds, fseeds = grid[:1], gseeds[:1], fseeds[:1]
    gres = []
    for lr, bs in grid:
        runs = [train_one({**base, "lr": lr, "batch": bs, "seed": s}, trd, vad, va,
                          os.path.join(vdir, f"grid_lr{lr:g}_b{bs}_s{s}"), a.device, log) for s in gseeds]
        gres.append({"lr": lr, "batch": bs, "mean_val_cost": float(np.mean([r["best_val_cost"] for r in runs])),
                     "per_seed": [r["best_val_cost"] for r in runs], "best_epoch": [r["best_epoch"] for r in runs]})
    best = min(gres, key=lambda r: r["mean_val_cost"])
    sel = {"variant": "asap_retrained", "grid_seeds": gseeds, "grid": gres, "chosen": {"lr": best["lr"], "batch": best["batch"]},
           "chosen_mean_val_cost": best["mean_val_cost"], **{k: base[k] for k in ("smooth", "min_epochs", "max_epochs")},
           "patience": a.patience}
    json.dump(sel, open(os.path.join(vdir, "selection.json"), "w"), indent=1)
    log(f"asap_retrained: chosen {sel['chosen']} (mean val cost {best['mean_val_cost']:.1f})")
    sres = [train_one({**base, **sel["chosen"], "seed": s}, trd, vad, va, os.path.join(vdir, f"seed{s}"), a.device, log)
            for s in fseeds]
    sel["seeds"] = [{"seed": r["seed"], "best_val_cost": r["best_val_cost"], "best_epoch": r["best_epoch"],
                     "ckpt": os.path.relpath(os.path.join(vdir, f"seed{r['seed']}", "best.pt"), ROOT)} for r in sres]
    json.dump(sel, open(os.path.join(vdir, "selection.json"), "w"), indent=1)
    log_load(vdir, "end")
    log("asap_retrained: DONE")


if __name__ == "__main__":
    main()
