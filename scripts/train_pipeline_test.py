#!/usr/bin/env python
"""S6 PIPELINE TEST (not a result): build per-state contact graphs from pilot labels, then
(1) overfit 20 states with each model/head (the loss must go near zero) and
(2) run one train/val split by assembly (fixed seed) and log the loss curves.

Models: MLP (same node features, no message passing) and GNN (GINE), each with a BCE head or a
discrete-time survival head with censoring (src/disasm/models/nets.py).
Nothing here is a model comparison. Results only show that the training loop runs and the loss goes down.
"""
import argparse
import json
import os
import sys
import time
from collections import defaultdict

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def build(labels_path):
    from disasm.oracle.cmgrrt import load_assembly
    from disasm.data.graph import state_graph
    labs = [json.loads(l) for l in open(labels_path)]
    states = defaultdict(list)
    for r in labs:
        states[(r["assembly_id"], r["state_key"])].append(r)
    asms, data = {}, []
    for (aid, skey), qs in sorted(states.items()):
        if aid not in asms:
            asms[aid] = load_assembly(os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly", aid))
        present, X, ei, ea = state_graph(asms[aid], [int(x) for x in skey.split("-")])
        by = {q["part_id"]: q for q in qs}
        if sorted(by) != present:
            continue
        succ = np.array([by[p]["outcome"] == "success" for p in present])
        t = np.array([min(by[p]["time_s"] or 0.0, by[p]["T"]) for p in present], dtype=np.float32)
        data.append({"aid": aid, "skey": skey, "x": torch.tensor(X), "ei": torch.tensor(ei), "ea": torch.tensor(ea),
                     "succ": torch.tensor(succ), "t": torch.tensor(t), "T": float(qs[0]["T"])})
    return data


def batches(data, bs, rng):
    idx = rng.permutation(len(data))
    for i in range(0, len(idx), bs):
        yield [data[j] for j in idx[i:i + bs]]


def collate(items, mu, sd):
    xs, eis, eas, ss, ts, off = [], [], [], [], [], 0
    for d in items:
        xs.append((d["x"] - mu) / sd); eis.append(d["ei"] + off); eas.append(d["ea"])
        ss.append(d["succ"]); ts.append(d["t"]); off += d["x"].shape[0]
    return torch.cat(xs), torch.cat(eis, 1), torch.cat(eas), torch.cat(ss), torch.cat(ts)


def run(model, train, val, epochs, lr, mu, sd, T, seed, log, tag):
    rng = np.random.default_rng(seed)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    hist = []
    for ep in range(epochs):
        model.train()
        tl, n = 0.0, 0
        for b in batches(train, 16, rng):
            x, ei, ea, s, t = collate(b, mu, sd)
            loss = model.loss(model(x, ei, ea), s, t, T)
            opt.zero_grad(); loss.backward(); opt.step()
            tl += float(loss) * len(b); n += len(b)
        vl = None
        if val:
            model.eval()
            with torch.no_grad():
                x, ei, ea, s, t = collate(val, mu, sd)
                vl = float(model.loss(model(x, ei, ea), s, t, T))
        hist.append({"epoch": ep, "train_loss": tl / n, "val_loss": vl})
        if ep % max(1, epochs // 10) == 0 or ep == epochs - 1:
            log(f"[{tag}] epoch {ep} train_loss {tl / n:.4f}" + (f" val_loss {vl:.4f}" if vl is not None else ""))
    return hist


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--labels", default=os.path.join(ROOT, "data/labels/pilot_v0/labels.jsonl"))
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--overfit-states", type=int, default=20)
    ap.add_argument("--overfit-epochs", type=int, default=400)
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--val-frac", type=float, default=0.2)
    args = ap.parse_args()
    from disasm.models.nets import Ranker
    from disasm.data.graph import NODE_DIM, EDGE_DIM
    os.makedirs(args.outdir, exist_ok=True)
    logf = open(os.path.join(args.outdir, "train_log.txt"), "a")

    def log(s):
        print(s, flush=True); logf.write(s + "\n"); logf.flush()

    torch.manual_seed(args.seed)
    t0 = time.time()
    data = build(args.labels)
    T = data[0]["T"]
    log(f"PIPELINE TEST: {len(data)} states, {sum(len(d['succ']) for d in data)} part-queries, "
        f"{len(set(d['aid'] for d in data))} assemblies, T={T}, build {time.time() - t0:.0f}s")
    X = torch.cat([d["x"] for d in data])
    mu, sd = X.mean(0), X.std(0) + 1e-6
    rng = np.random.default_rng(args.seed)
    # (1) overfit 20 states
    sub = [data[i] for i in rng.choice(len(data), min(args.overfit_states, len(data)), replace=False)]
    results = {}
    for enc in ("mlp", "gnn"):
        for head in ("bce", "survival"):
            torch.manual_seed(args.seed)
            m = Ranker(enc, NODE_DIM, EDGE_DIM, head)
            h = run(m, sub, None, args.overfit_epochs, 3e-3, mu, sd, T, args.seed, log, f"overfit {enc}/{head}")
            results[f"overfit_{enc}_{head}"] = {"first": h[0]["train_loss"], "last": h[-1]["train_loss"], "hist": h}
    # (2) split by assembly
    aids = sorted(set(d["aid"] for d in data))
    rng2 = np.random.default_rng(args.seed)
    val_a = set(rng2.choice(aids, max(1, int(round(args.val_frac * len(aids)))), replace=False).tolist())
    tr = [d for d in data if d["aid"] not in val_a]
    va = [d for d in data if d["aid"] in val_a]
    log(f"split by assembly (seed {args.seed}): train {len(tr)} states / {len(aids) - len(val_a)} asm, "
        f"val {len(va)} states / {len(val_a)} asm")
    for enc in ("mlp", "gnn"):
        for head in ("bce", "survival"):
            torch.manual_seed(args.seed)
            m = Ranker(enc, NODE_DIM, EDGE_DIM, head)
            h = run(m, tr, va, args.epochs, 1e-3, mu, sd, T, args.seed, log, f"split {enc}/{head}")
            results[f"split_{enc}_{head}"] = {"first_train": h[0]["train_loss"], "last_train": h[-1]["train_loss"],
                                              "first_val": h[0]["val_loss"], "last_val": h[-1]["val_loss"], "hist": h}
    json.dump({"val_assemblies": sorted(val_a), "results": results, "seed": args.seed},
              open(os.path.join(args.outdir, "results.json"), "w"))
    L = ["# S6 PIPELINE TEST (not a result)\n",
         f"Labels: `{os.path.relpath(args.labels, ROOT)}`; {len(data)} states; log `{os.path.relpath(logf.name, ROOT)}`. "
         "This only checks that the training loop runs and the loss goes down. It is **not** a model comparison.\n",
         "## PIPELINE TEST: overfit 20 states (loss should go near zero)\n", "| model/head | first loss | last loss |", "|---|---|---|"]
    for k, v in results.items():
        if k.startswith("overfit"):
            L.append(f"| {k[8:]} | {v['first']:.4f} | {v['last']:.4f} |")
    L += ["\n## PIPELINE TEST: one split by assembly (loss curves only)\n",
          "| model/head | train loss first -> last | val loss first -> last |", "|---|---|---|"]
    for k, v in results.items():
        if k.startswith("split"):
            L.append(f"| {k[6:]} | {v['first_train']:.4f} -> {v['last_train']:.4f} | {v['first_val']:.4f} -> {v['last_val']:.4f} |")
    open(os.path.join(args.outdir, "pipeline_test.md"), "w").write("\n".join(L) + "\n")
    log("\n".join(L))


if __name__ == "__main__":
    main()
