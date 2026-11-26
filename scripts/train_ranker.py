#!/usr/bin/env python
"""R3 (run 03): train one ranker variant with an equal-budget grid on val, then 5 seeds of the chosen config.

Variant = encoder (mlp | gnn) x head (bce | survival). Grid (same for every variant):
hidden {64, 128} x lr {1e-3, 3e-4} x layers {2, 3} (MLP depth = same number of residual blocks), seed 0.
Fixed for all: AdamW, weight decay 1e-4, dropout 0.1, grad-clip 1.0, batch 32 states, max 150 epochs,
early stopping with patience 20 on the VALIDATION METRIC = total replay planner cost over val states with
>= 1 success (order parts by the variant's rule: BCE -> p, survival -> p/c; cost = logged time_s up to and
including the first success). The best-epoch checkpoint is kept. Config selection = lowest best val metric.
The test split is never loaded here.
"""
import argparse
import csv
import itertools
import json
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_split(graphs_path, split_path, which):
    G = torch.load(graphs_path, weights_only=False)
    s = json.load(open(split_path))
    keep = {k: set(s[k]) for k in which}
    return {k: [g for g in G if g["aid"] in keep[k]] for k in which}


def norm_stats(train):
    X = torch.cat([g["x"] for g in train])
    E = torch.cat([g["ea"] for g in train if g["ea"].shape[0]])
    return X.mean(0), X.std(0) + 1e-6, E.mean(0), E.std(0) + 1e-6


def collate(items, st, dev):
    mu, sd, emu, esd = st
    xs, eis, eas, ss, cs, off, ptr = [], [], [], [], [], 0, [0]
    for g in items:
        xs.append((g["x"] - mu) / sd); eis.append(g["ei"] + off); eas.append((g["ea"] - emu) / esd)
        ss.append(g["succ"]); cs.append(g["cens_t"]); off += g["x"].shape[0]; ptr.append(off)
    return (torch.cat(xs).to(dev), torch.cat(eis, 1).to(dev), torch.cat(eas).to(dev), torch.cat(ss).to(dev),
            torch.cat(cs).to(dev), ptr)


@torch.no_grad()
def predict_states(model, graphs, st, dev):
    """-> list of (p np, c np or None) per graph."""
    from disasm.models.ranker3 import Ranker3  # noqa: F401
    model.eval()
    out = []
    for i in range(0, len(graphs), 512):
        b = graphs[i:i + 512]
        x, ei, ea, s, c, ptr = collate(b, st, dev)
        p, cc = model.predict(model(x, ei, ea))
        p = p.cpu().numpy(); cc = None if cc is None else cc.cpu().numpy()
        for j in range(len(b)):
            out.append((p[ptr[j]:ptr[j + 1]], None if cc is None else cc[ptr[j]:ptr[j + 1]]))
    return out


def val_metric(preds, graphs, rule):
    from disasm.models.ranker3 import replay_cost
    tot, nq = 0.0, 0
    for (p, c), g in zip(preds, graphs):
        s = g["succ"].numpy()
        if not s.any():
            continue
        score = p if rule == "p" else p / np.maximum(c, 1e-3)
        cost, n = replay_cost(score, g["time_s"].numpy(), s)
        tot += cost; nq += n
    return tot, nq


def train_one(cfg, data, st, outdir, dev, log):
    from disasm.models.ranker3 import Ranker3
    from disasm.data.graph import NODE_DIM, EDGE_DIM_V3
    torch.manual_seed(cfg["seed"]); np.random.seed(cfg["seed"])
    T = data["train"][0]["T"]
    model = Ranker3(cfg["enc"], NODE_DIM, EDGE_DIM_V3, cfg["head"], h=cfg["hidden"], layers=cfg["layers"],
                    dropout=cfg["dropout"], K=8, T=T).to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"])
    rule = "p" if cfg["head"] == "bce" else "p_over_c"
    rng = np.random.default_rng(cfg["seed"])
    tr, va = data["train"], data["val"]
    os.makedirs(outdir, exist_ok=True)
    rows, best, best_ep, bad, hist_vm = [], float("inf"), -1, 0, []
    t0 = time.time()
    for ep in range(cfg["max_epochs"]):
        model.train()
        perm = rng.permutation(len(tr))
        tl, n = 0.0, 0
        for i in range(0, len(perm), cfg["batch"]):
            b = [tr[j] for j in perm[i:i + cfg["batch"]]]
            x, ei, ea, s, c, _ = collate(b, st, dev)
            loss = model.loss(model(x, ei, ea), s, c)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            tl += float(loss) * len(b); n += len(b)
        model.eval()
        with torch.no_grad():
            x, ei, ea, s, c, _ = collate(va, st, dev)
            vl = float(model.loss(model(x, ei, ea), s, c))
        vm, vq = val_metric(predict_states(model, va, st, dev), va, rule)
        W = cfg.get("smooth", 1)
        hist_vm.append(vm)
        sm = float(np.mean(hist_vm[-W:])) if len(hist_vm) >= W else float("inf")
        rows.append({"epoch": ep, "train_loss": tl / n, "val_loss": vl, "val_cost": vm, "val_queries": vq,
                     "val_cost_smoothed": sm if np.isfinite(sm) else ""})
        if not np.isfinite(sm):
            continue
        if sm < best - 1e-9:
            best, best_ep, bad = sm, ep, 0
            torch.save({"state_dict": model.state_dict(), "cfg": cfg, "norm": [t.cpu() for t in st], "epoch": ep,
                        "val_cost": vm}, os.path.join(outdir, "best.pt"))
        else:
            bad += 1
        if bad >= cfg["patience"] and ep + 1 >= cfg.get("min_epochs", 0):
            break
    with open(os.path.join(outdir, "metrics.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.3))
        e = [r["epoch"] for r in rows]
        ax[0].plot(e, [r["train_loss"] for r in rows], label="train", color="#4C72B0")
        ax[0].plot(e, [r["val_loss"] for r in rows], label="val", color="#DD8452")
        ax[0].set_xlabel("epoch"); ax[0].set_ylabel("loss"); ax[0].legend(frameon=False)
        ax[1].plot(e, [r["val_cost"] for r in rows], color="#55A868")
        ax[1].axvline(best_ep, color="#555555", ls="--", lw=1)
        ax[1].set_xlabel("epoch"); ax[1].set_ylabel("val total replay cost (s)")
        for a in ax:
            a.spines[["top", "right"]].set_visible(False)
        fig.suptitle(os.path.basename(outdir), fontsize=9)
        fig.tight_layout(); fig.savefig(os.path.join(outdir, "curve.png"), dpi=110); plt.close(fig)
    except Exception as ex:  # noqa: BLE001
        log(f"plot failed: {ex}")
    res = {**cfg, "best_val_cost": best, "best_epoch": best_ep, "epochs_run": len(rows), "train_s": time.time() - t0}
    json.dump(res, open(os.path.join(outdir, "result.json"), "w"), indent=1)
    log(f"{os.path.basename(outdir)}: best val cost {best:.1f} s at epoch {best_ep} ({len(rows)} epochs, {time.time() - t0:.0f} s)")
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--enc", required=True, choices=["mlp", "gnn"])
    ap.add_argument("--head", required=True, choices=["bce", "survival"])
    ap.add_argument("--outdir", required=True, help="experiments/<date>_run03_train")
    ap.add_argument("--graphs", default=os.path.join(ROOT, "data/processed/run03/graphs.pt"))
    ap.add_argument("--split", default=os.path.join(ROOT, "data/splits/v1_split.json"))
    ap.add_argument("--seeds", default="0,1,2,3,4")
    ap.add_argument("--max-epochs", type=int, default=150)
    ap.add_argument("--patience", type=int, default=20)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--quick", action="store_true", help="dev: 1 grid point, 3 epochs")
    ap.add_argument("--smooth", type=int, default=1, help="early stopping / checkpoint on the trailing mean of this many epochs' val cost")
    ap.add_argument("--min-epochs", type=int, default=0)
    ap.add_argument("--grid-seeds", default="0", help="grid configs are ranked by the mean best val metric over these seeds")
    args = ap.parse_args()
    var = f"{args.enc}_{args.head}"
    vdir = os.path.join(args.outdir, var)
    os.makedirs(vdir, exist_ok=True)
    logf = open(os.path.join(vdir, "train_log.txt"), "a")

    def log(s):
        s = f"[{time.strftime('%H:%M:%S')}] {s}"
        print(s, flush=True); logf.write(s + "\n"); logf.flush()

    from disasm.util.runlog import log_load
    log_load(vdir, "start")
    data = load_split(args.graphs, args.split, ["train", "val"])      # test is NOT loaded
    st = norm_stats(data["train"])
    log(f"{var}: train {len(data['train'])} states, val {len(data['val'])} states")
    base = {"enc": args.enc, "head": args.head, "wd": 1e-4, "dropout": 0.1, "batch": 32,
            "max_epochs": 3 if args.quick else args.max_epochs, "patience": args.patience,
            "smooth": args.smooth, "min_epochs": args.min_epochs}
    grid = list(itertools.product([64, 128], [1e-3, 3e-4], [2, 3]))
    if args.quick:
        grid = grid[:1]
    gres = []
    gseeds = [int(x) for x in args.grid_seeds.split(",")]
    for h, lr, L in grid:
        runs = []
        for gs in gseeds:
            cfg = {**base, "hidden": h, "lr": lr, "layers": L, "seed": gs}
            sub = f"grid_h{h}_lr{lr:g}_L{L}" + (f"_s{gs}" if len(gseeds) > 1 else "")
            runs.append(train_one(cfg, data, st, os.path.join(vdir, sub), args.device, log))
        gres.append({"hidden": h, "lr": lr, "layers": L, "best_val_cost": float(np.mean([r["best_val_cost"] for r in runs])),
                     "per_seed": [r["best_val_cost"] for r in runs], "best_epoch": [r["best_epoch"] for r in runs]})
    best = min(gres, key=lambda r: r["best_val_cost"])
    sel = {"variant": var, "grid_seeds": gseeds, "smooth": args.smooth, "min_epochs": args.min_epochs,
           "patience": args.patience, "grid": gres,
           "chosen": {k: best[k] for k in ("hidden", "lr", "layers")}, "chosen_val_cost": best["best_val_cost"]}
    json.dump(sel, open(os.path.join(vdir, "selection.json"), "w"), indent=1)
    log(f"{var}: chosen config {sel['chosen']} (val cost {best['best_val_cost']:.1f})")
    sres = []
    for sd in [int(x) for x in args.seeds.split(",")]:
        cfg = {**base, "hidden": best["hidden"], "lr": best["lr"], "layers": best["layers"], "seed": sd}
        sres.append(train_one(cfg, data, st, os.path.join(vdir, f"seed{sd}"), args.device, log))
    sel["seeds"] = [{"seed": r["seed"], "best_val_cost": r["best_val_cost"], "best_epoch": r["best_epoch"]} for r in sres]
    json.dump(sel, open(os.path.join(vdir, "selection.json"), "w"), indent=1)
    log_load(vdir, "end")
    log(f"{var}: DONE")


if __name__ == "__main__":
    main()
