#!/usr/bin/env python
"""Run 04 T2 pipeline checks (NOT results): (a) ASAP's GNN retrained with ASAP's objective for 2 epochs on 50 run 03
TRAIN assemblies (pilot_v1 states); (b) one forward/backward pass of PointNet+GNN (survival head) on a batch of 32
run 03 TRAIN states. No val/test assembly is touched (asserted)."""
import argparse
import json
import os
import random
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--n-asm", type=int, default=50)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    from disasm.util.runlog import log_load
    log_load(a.outdir, "start")
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    split = json.load(open(os.path.join(ROOT, "data/splits/v1_split.json")))
    train = sorted(split["train"])
    held = set(split["val"]) | set(split["test"])
    rng = random.Random(a.seed)
    aids = sorted(rng.sample(train, a.n_asm))
    assert not (set(aids) & held)
    from disasm.oracle.cmgrrt import load_assembly
    res = {"assemblies": aids, "device": str(dev)}

    # ---------------------------------------------------------------- (a) ASAP retraining dry run
    from disasm.models.asap_train import build_dataset, new_asap_model, train_epoch
    states = {}
    for l in open(os.path.join(ROOT, "data/labels/pilot_v1/states.jsonl")):
        s = json.loads(l)
        states.setdefault(s["assembly_id"], []).append(s)
    t0 = time.time()
    data = build_dataset(aids, states, RAW, load_assembly)
    res["asap_build_s"] = time.time() - t0
    res["asap_states"] = len(data)
    torch.manual_seed(a.seed)
    model = new_asap_model(a.seed).to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=a.lr)
    res["asap_epochs"] = []
    for ep in range(a.epochs):
        t1 = time.time()
        loss, acc = train_epoch(model, data, opt, a.batch, rng, dev)
        res["asap_epochs"].append({"epoch": ep, "loss": loss, "top1": acc, "s": time.time() - t1})
        print(f"ASAP epoch {ep}: loss {loss:.4f} top1 {acc:.3f} ({time.time() - t1:.1f}s)", flush=True)

    # ---------------------------------------------------------------- (b) PointNet+GNN forward/backward
    from disasm.data.graph import NODE_DIM, EDGE_DIM_V3
    from disasm.data.pointcloud import assembly_clouds
    from disasm.models.pointnet import PointNetRanker
    graphs = torch.load(os.path.join(ROOT, "data/processed/run03/graphs.pt"), weights_only=False)
    tr = [g for g in graphs if g["aid"] in set(train)]
    batch = random.Random(a.seed).sample(tr, 32)
    assert not ({g["aid"] for g in batch} & held)
    clouds = {}
    xs, pcs, eis, eas, succ, cens, off = [], [], [], [], [], [], 0
    t2 = time.time()
    for g in batch:
        if g["aid"] not in clouds:
            clouds[g["aid"]] = assembly_clouds(load_assembly(os.path.join(RAW, g["aid"])))
        present = [int(p) for p in g["skey"].split("-")]
        pcs.append(torch.from_numpy(np.stack([clouds[g["aid"]][p] for p in present])))
        xs.append(g["x"]); eis.append(g["ei"] + off); eas.append(g["ea"])
        succ.append(g["succ"].bool()); cens.append(g["cens_t"])
        off += len(present)
    res["pn_cloud_s"] = time.time() - t2
    x = torch.cat(xs).float(); x = (x - x.mean(0)) / (x.std(0) + 1e-6)
    ea = torch.cat(eas).float(); ea = (ea - ea.mean(0)) / (ea.std(0) + 1e-6)
    m = PointNetRanker(NODE_DIM, EDGE_DIM_V3, "survival", h=64, layers=2, dropout=0.1, K=8, T=30.0).to(dev)
    out = m(x.to(dev), torch.cat(pcs).to(dev), torch.cat(eis, 1).to(dev), ea.to(dev))
    loss = m.loss(out, torch.cat(succ).to(dev), torch.cat(cens).float().to(dev))
    loss.backward()
    gpn = float(sum(p.grad.norm() ** 2 for p in m.pn.parameters() if p.grad is not None) ** 0.5)
    res.update({"pn_nodes": int(off), "pn_points_shape": list(torch.cat(pcs).shape), "pn_loss": float(loss),
                "pn_grad_norm_pointnet": gpn, "pn_params": sum(p.numel() for p in m.parameters())})
    print(f"PointNet+GNN: nodes {off}, clouds {list(torch.cat(pcs).shape)}, loss {float(loss):.4f}, "
          f"|grad PN| {gpn:.4g}", flush=True)
    json.dump(res, open(os.path.join(a.outdir, "results.json"), "w"), indent=1)
    log_load(a.outdir, "end")


if __name__ == "__main__":
    main()
