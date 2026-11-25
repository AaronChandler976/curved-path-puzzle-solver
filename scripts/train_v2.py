#!/usr/bin/env python
"""Run 05: train one pre-registered ranker variant on v2 (docs/PREREG_run05.md §1-§3), val only.

Variants: mlp_bce, mlp_survival, gnn_bce, gnn_survival, gnn_survival_tail, pn_gnn_survival.
Fixed (§3): AdamW, weight decay 1e-4, dropout 0.1, grad-clip 1.0, batch 32 states, <= 150 epochs.
Grid: hidden {64,128} x lr {1e-3,3e-4} x layers {2,3}; gnn_survival_tail adds lambda {0.1, 1.0} (16 configs).
Selection metric: total replay planner cost on val (MAIN config; order by p for BCE, p/c for survival), read as the
5-epoch trailing mean; min 10 epochs, patience 25; the best (smoothed) epoch's checkpoint is kept. A config is ranked
by the mean over grid seeds 0,1,2 of its best smoothed val cost; the chosen config is retrained with seeds 100-104.
Training uses only states with >= 1 main-config success (§0 "a state counts"); every node of those states is a target.
The test split is never loaded (graphs_train_val.pt holds train and val only).
Resumable: a run whose result.json exists is skipped.
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
VARIANTS = {"mlp_bce": ("mlp", "bce", False, False), "mlp_survival": ("mlp", "survival", False, False),
            "gnn_bce": ("gnn", "bce", False, False), "gnn_survival": ("gnn", "survival", False, False),
            "gnn_survival_tail": ("gnn", "survival", True, False), "pn_gnn_survival": ("gnn", "survival", False, True),
            # campaign Phase 2, exploratory (post-registration): stronger encoders, same head, grid and budget rule
            "gatv2_survival": ("gatv2", "survival", False, False), "gt_survival": ("transformer", "survival", False, False),
            "gnn_survival_listnet": ("gnn", "survival", "listnet", False)}


def norm_stats(train):
    X = torch.cat([g["x"] for g in train])
    E = torch.cat([g["ea"] for g in train if g["ea"].shape[0]])
    return X.mean(0), X.std(0) + 1e-6, E.mean(0), E.std(0) + 1e-6


class Batcher:
    def __init__(self, st, dev, clouds=None):
        self.st, self.dev, self.clouds = st, dev, clouds

    def __call__(self, items):
        mu, sd, emu, esd = self.st
        xs, eis, eas, ss, cs, ts, bs, pcs, off, ptr = [], [], [], [], [], [], [], [], 0, [0]
        for k, g in enumerate(items):
            n = g["x"].shape[0]
            xs.append((g["x"] - mu) / sd); eis.append(g["ei"] + off); eas.append((g["ea"] - emu) / esd)
            ss.append(g["succ"]); cs.append(g["cens_t"]); ts.append(g["time_s"]); bs.append(torch.full((n,), k))
            if self.clouds is not None:
                c = self.clouds[g["aid"]]
                pcs.append(torch.stack([c[p] for p in g["present"]]))
            off += n; ptr.append(off)
        d = self.dev
        out = {"x": torch.cat(xs).to(d), "ei": torch.cat(eis, 1).to(d), "ea": torch.cat(eas).to(d),
               "succ": torch.cat(ss).to(d), "cens_t": torch.cat(cs).to(d), "time_s": torch.cat(ts).to(d),
               "batch": torch.cat(bs).to(d), "ptr": ptr}
        if pcs:
            out["pc"] = torch.cat(pcs).to(d)
        return out


def build_model(var, cfg, T):
    from disasm.data.graph import NODE_DIM, EDGE_DIM_V3
    enc, head, _, pn = VARIANTS[var]
    if pn:
        from disasm.models.pointnet import PointNetRanker
        return PointNetRanker(NODE_DIM, EDGE_DIM_V3, head, h=cfg["hidden"], layers=cfg["layers"],
                              dropout=cfg["dropout"], K=8, T=T)
    from disasm.models.ranker3 import Ranker3
    return Ranker3(enc, NODE_DIM, EDGE_DIM_V3, head, h=cfg["hidden"], layers=cfg["layers"], dropout=cfg["dropout"],
                   K=8, T=T)


def forward(model, b):
    if "pc" in b:
        return model(b["x"], b["pc"], b["ei"], b["ea"])
    return model(b["x"], b["ei"], b["ea"])


def core(model):
    return model.ranker if hasattr(model, "ranker") else model


def diff_p_c(model, out):
    """p and c from the survival head WITH gradients (same formulas as Ranker3.predict)."""
    m = core(model)
    h = torch.sigmoid(out)
    S = torch.cumprod(1 - h, 1)
    S_prev = torch.cat([torch.ones_like(S[:, :1]), S[:, :-1]], 1)
    return 1 - S[:, -1], (m.widths[None, :] * (S_prev + S) / 2).sum(1)


@torch.no_grad()
def predict(model, graphs, batcher, bs=256):
    """-> list of (p, c or None) numpy per graph."""
    model.eval()
    out = []
    for i in range(0, len(graphs), bs):
        b = batcher(graphs[i:i + bs])
        p, c = core(model).predict(forward(model, b))
        p = p.cpu().numpy(); c = None if c is None else c.cpu().numpy()
        ptr = b["ptr"]
        for j in range(len(ptr) - 1):
            out.append((p[ptr[j]:ptr[j + 1]], None if c is None else c[ptr[j]:ptr[j + 1]]))
    return out


def order_score(p, c, rule):
    return p if rule == "p" else p / np.maximum(c, 1e-3)


def val_cost(preds, graphs, rule):
    from disasm.models.ranker3 import replay_cost
    tot, nq = 0.0, 0
    for (p, c), g in zip(preds, graphs):
        cost, n = replay_cost(order_score(p, c, rule), g["time_s"].numpy(), g["succ"].numpy())
        tot += cost; nq += n
    return tot, nq


def train_one(var, cfg, tr, va, batcher, outdir, dev, log):
    res_path = os.path.join(outdir, "result.json")
    if os.path.exists(res_path):
        r = json.load(open(res_path))
        log(f"{os.path.basename(outdir)}: exists (best {r['best_val_cost']:.1f}), skipped")
        return r
    from disasm.models.tail_loss import tail_term_grouped as tail_term   # = tail_term, batched by state size
    from disasm.models.tail_loss import listnet_term
    torch.manual_seed(cfg["seed"]); np.random.seed(cfg["seed"])
    T = tr[0]["T"]
    model = build_model(var, cfg, T).to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"])
    rule = "p" if VARIANTS[var][1] == "bce" else "p_over_c"
    tail = VARIANTS[var][2]
    rng = np.random.default_rng(cfg["seed"])
    os.makedirs(outdir, exist_ok=True)
    rows, best, best_ep, bad, hist = [], float("inf"), -1, 0, []
    t0 = time.time()
    for ep in range(cfg["max_epochs"]):
        model.train()
        perm = rng.permutation(len(tr))
        tl, ttl, n = 0.0, 0.0, 0
        for i in range(0, len(perm), cfg["batch"]):
            b = batcher([tr[j] for j in perm[i:i + cfg["batch"]]])
            out = forward(model, b)
            loss = core(model).loss(out, b["succ"], b["cens_t"])
            if tail == "listnet":
                p, c = diff_p_c(model, out)
                s = torch.log(p.clamp_min(1e-6)) - torch.log(c.clamp_min(1e-3))
                tt = listnet_term(s, b["succ"], b["time_s"], b["batch"])
                loss = loss + cfg["lam"] * tt
                ttl += float(tt.detach()) * (len(b["ptr"]) - 1)
            elif tail:
                p, c = diff_p_c(model, out)
                s = torch.log(p.clamp_min(1e-6)) - torch.log(c.clamp_min(1e-3))
                tt = tail_term(s, b["succ"], b["time_s"], b["batch"], T, tau=cfg["tau"])
                loss = loss + cfg["lam"] * tt
                ttl += float(tt.detach()) * (len(b["ptr"]) - 1)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            tl += float(loss.detach()) * (len(b["ptr"]) - 1); n += len(b["ptr"]) - 1
        model.eval()
        with torch.no_grad():
            vl, vn = 0.0, 0
            for i in range(0, len(va), 256):
                b = batcher(va[i:i + 256])
                vl += float(core(model).loss(forward(model, b), b["succ"], b["cens_t"])) * int(b["succ"].numel()); vn += int(b["succ"].numel())
        vm, vq = val_cost(predict(model, va, batcher), va, rule)
        W = cfg["smooth"]
        hist.append(vm)
        sm = float(np.mean(hist[-W:])) if len(hist) >= W else float("inf")
        rows.append({"epoch": ep, "train_loss": tl / n, "train_tail": ttl / n if tail else "", "val_loss": vl / vn,
                     "val_cost": vm, "val_queries": vq, "val_cost_smoothed": sm if np.isfinite(sm) else ""})
        if not np.isfinite(sm):
            continue
        if sm < best - 1e-9:
            best, best_ep, bad = sm, ep, 0
            torch.save({"state_dict": model.state_dict(), "cfg": cfg, "variant": var, "norm": [t.cpu() for t in batcher.st],
                        "epoch": ep, "val_cost": vm, "val_cost_smoothed": sm}, os.path.join(outdir, "best.pt"))
        else:
            bad += 1
        if bad >= cfg["patience"] and ep + 1 >= cfg["min_epochs"]:
            break
    with open(os.path.join(outdir, "metrics.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    res = {**cfg, "variant": var, "best_val_cost": best, "best_epoch": best_ep, "epochs_run": len(rows),
           "train_s": time.time() - t0, "n_params": sum(p.numel() for p in model.parameters())}
    json.dump(res, open(res_path, "w"), indent=1)
    log(f"{os.path.basename(outdir)}: best smoothed val cost {best:.1f} s at epoch {best_ep} ({len(rows)} epochs, {time.time() - t0:.0f} s)")
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--variant", required=True, choices=sorted(VARIANTS))
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--graphs", default=os.path.join(ROOT, "data/processed/run05/graphs_train_val.pt"))
    ap.add_argument("--clouds", default=os.path.join(ROOT, "data/processed/run05/clouds_train_val.pt"))
    ap.add_argument("--grid-seeds", default="0,1,2")
    ap.add_argument("--seeds", default="100,101,102,103,104")
    ap.add_argument("--max-epochs", type=int, default=150)
    ap.add_argument("--patience", type=int, default=25)
    ap.add_argument("--min-epochs", type=int, default=10)
    ap.add_argument("--smooth", type=int, default=5)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--quick", action="store_true", help="dev: 1 grid point, 1 grid seed, 3 epochs, 1 final seed")
    a = ap.parse_args()
    vdir = os.path.join(a.outdir, a.variant)
    os.makedirs(vdir, exist_ok=True)
    logf = open(os.path.join(vdir, "train_log.txt"), "a")

    def log(s):
        s = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {s}"
        print(s, flush=True); logf.write(s + "\n"); logf.flush()

    from disasm.util.runlog import log_load
    log_load(vdir, "start")
    G = torch.load(a.graphs, weights_only=False)
    assert all(g["split"] in ("train", "val") for g in G), "test graphs present: refusing"
    tr = [g for g in G if g["split"] == "train" and bool(g["succ"].any())]
    va = [g for g in G if g["split"] == "val" and bool(g["succ"].any())]
    st = norm_stats(tr)
    clouds = torch.load(a.clouds, weights_only=False) if VARIANTS[a.variant][3] else None
    batcher = Batcher(st, a.device, clouds)
    log(f"{a.variant}: train {len(tr)} states ({len({g['aid'] for g in tr})} asm), val {len(va)} states "
        f"({len({g['aid'] for g in va})} asm), states with >= 1 success only")
    base = {"wd": 1e-4, "dropout": 0.1, "batch": 32, "max_epochs": 3 if a.quick else a.max_epochs,
            "patience": a.patience, "smooth": 1 if a.quick else a.smooth, "min_epochs": 0 if a.quick else a.min_epochs,
            "tau": 0.1}
    lams = [0.1, 1.0] if VARIANTS[a.variant][2] else [None]
    grid = list(itertools.product([64, 128], [1e-3, 3e-4], [2, 3], lams))
    gseeds = [int(x) for x in a.grid_seeds.split(",")]
    fseeds = [int(x) for x in a.seeds.split(",")]
    if a.quick:
        grid, gseeds, fseeds = grid[:1], gseeds[:1], fseeds[:1]

    def name(h, lr, L, lam):
        return f"h{h}_lr{lr:g}_L{L}" + ("" if lam is None else f"_lam{lam:g}")

    gres = []
    for h, lr, L, lam in grid:
        runs = [train_one(a.variant, {**base, "hidden": h, "lr": lr, "layers": L, "lam": lam, "seed": s}, tr, va, batcher,
                          os.path.join(vdir, f"grid_{name(h, lr, L, lam)}_s{s}"), a.device, log) for s in gseeds]
        gres.append({"hidden": h, "lr": lr, "layers": L, "lam": lam,
                     "mean_val_cost": float(np.mean([r["best_val_cost"] for r in runs])),
                     "per_seed": [r["best_val_cost"] for r in runs], "best_epoch": [r["best_epoch"] for r in runs]})
    best = min(gres, key=lambda r: r["mean_val_cost"])
    sel = {"variant": a.variant, "grid_seeds": gseeds, "smooth": base["smooth"], "min_epochs": base["min_epochs"],
           "patience": a.patience, "max_epochs": base["max_epochs"], "grid": gres,
           "chosen": {k: best[k] for k in ("hidden", "lr", "layers", "lam")}, "chosen_mean_val_cost": best["mean_val_cost"]}
    json.dump(sel, open(os.path.join(vdir, "selection.json"), "w"), indent=1)
    log(f"{a.variant}: chosen {sel['chosen']} (mean val cost {best['mean_val_cost']:.1f})")
    sres = [train_one(a.variant, {**base, **sel["chosen"], "seed": s}, tr, va, batcher, os.path.join(vdir, f"seed{s}"),
                      a.device, log) for s in fseeds]
    sel["seeds"] = [{"seed": r["seed"], "best_val_cost": r["best_val_cost"], "best_epoch": r["best_epoch"],
                     "ckpt": os.path.relpath(os.path.join(vdir, f"seed{r['seed']}", "best.pt"), ROOT)} for r in sres]
    json.dump(sel, open(os.path.join(vdir, "selection.json"), "w"), indent=1)
    log_load(vdir, "end")
    log(f"{a.variant}: DONE")


if __name__ == "__main__":
    main()
