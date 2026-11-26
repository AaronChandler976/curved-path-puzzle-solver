#!/usr/bin/env python
"""Campaign Phase 2: 5-fold GROUP cross-validation over train+val (never test) as a robustness check of the val
ranking. It does not change the registered selection (docs/PREREG_run05.md §3).

Folds: the duplicate groups of data/splits/v2_split.json restricted to train+val assemblies, stratified by
(source, part-count bin) of the group's largest member, dealt round-robin after a seeded shuffle (seed 0).
For each fold k and each variant (its val-chosen config from <train-dir>/<variant>/selection.json) and each seed:
train on 3 folds, early-stop on the INNER fold (k + 1) mod 5 with the registered rule (5-epoch trailing mean of replay
cost, min 10, patience 25, <= 150 epochs; the same for every variant), and replay the held-out fold k, which selected
nothing. So fold-k costs are unbiased for the trained models as well as the heuristics (Phase 1 audit, MAJOR 1). The
configs are the val-chosen ones; val assemblies sit in the folds, so config choice still saw some held-out data
(reported). Per-fold totals and the ratio to fewest contacts are reported (mean ± std over folds and seeds).
Resumable (train_v2.train_one skips finished runs).
"""
import argparse
import json
import os
import sys
from collections import defaultdict

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def pbin(n):
    return "3-4" if n <= 4 else "5-6" if n <= 6 else "7-8" if n <= 8 else "9-10" if n <= 10 else "11-12"


def folds(split, K=5, seed=0):
    keep = set(split["train"]) | set(split["val"])
    strata = defaultdict(list)
    for gid, mem in sorted(split["groups"].items(), key=lambda kv: int(kv[0])):
        mem = [a for a in mem if a in keep]
        if not mem:
            continue
        big = max(mem, key=lambda a: (split["n_parts"][a], a))
        strata[(split["sources"][big], pbin(split["n_parts"][big]))].append(mem)
    rng = np.random.default_rng(seed)
    fold_of = {}
    i = 0
    for s in sorted(strata):
        gs = strata[s]
        order = rng.permutation(len(gs))
        for j in order:
            for a in gs[j]:
                fold_of[a] = i % K
            i += 1
    return fold_of


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train-dir", required=True, help="Phase 1/2 training dir with <variant>/selection.json")
    ap.add_argument("--variants", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--seeds", default="100,101,102")
    ap.add_argument("--folds", default="0,1,2,3,4")
    ap.add_argument("--device", default="cuda")
    a = ap.parse_args()
    from train_v2 import Batcher, norm_stats, train_one, predict, order_score, VARIANTS
    from disasm.models.ranker3 import replay_cost
    from disasm.eval.replay3 import heuristic_orders, random_expectation
    os.makedirs(a.outdir, exist_ok=True)
    from disasm.util.runlog import log_load
    log_load(a.outdir, "start")
    split = json.load(open(os.path.join(ROOT, "data/splits/v2_split.json")))
    fold_of = folds(split)
    json.dump(fold_of, open(os.path.join(a.outdir, "folds.json"), "w"))
    P = os.path.join(ROOT, "data/processed/run05")
    G = [g for g in torch.load(os.path.join(P, "graphs_train_val.pt"), weights_only=False) if g["succ"].any()]
    assert all(g["split"] in ("train", "val") for g in G)
    clouds = torch.load(os.path.join(P, "clouds_train_val.pt"), weights_only=False)
    logf = open(os.path.join(a.outdir, "cv_log.txt"), "a")

    def log(s):
        print(s, flush=True); logf.write(s + "\n"); logf.flush()

    res = []
    for k in [int(x) for x in a.folds.split(",")]:
        kin = (k + 1) % 5
        tr = [g for g in G if fold_of[g["aid"]] not in (k, kin)]
        inner = [g for g in G if fold_of[g["aid"]] == kin]
        va = [g for g in G if fold_of[g["aid"]] == k]
        st = norm_stats(tr)
        heur = defaultdict(float)
        for g in va:
            t, s = g["time_s"].numpy().astype(float), g["succ"].numpy().astype(bool)
            heur["random"] += random_expectation(t, s)[0]
            for name, o in heuristic_orders(g).items():
                c = 0.0
                for i in o:
                    c += t[i]
                    if s[i]:
                        break
                heur[name] += c
        heur["optimal"] = sum(float(g["time_s"][g["succ"]].min()) for g in va)
        res.append({"fold": k, "n_states": len(va), "n_assemblies": len({g["aid"] for g in va}), "variant": "heuristics", **heur})
        log(f"fold {k}: {len(tr)} train / {len(inner)} inner (fold {kin}) / {len(va)} held-out states; heuristics {dict((x, round(v)) for x, v in heur.items())}")
        for var in a.variants.split(","):
            sel = json.load(open(os.path.join(a.train_dir, var, "selection.json")))
            base = {"wd": 1e-4, "dropout": 0.1, "batch": 32, "max_epochs": 150, "patience": 25, "smooth": 5, "min_epochs": 10,
                    "tau": 0.1, **sel["chosen"]}
            b = Batcher(st, a.device, clouds if VARIANTS[var][3] else None)
            rule = "p" if VARIANTS[var][1] == "bce" else "p_over_c"
            for sd in [int(x) for x in a.seeds.split(",")]:
                r = train_one(var, {**base, "seed": sd}, tr, inner, b, os.path.join(a.outdir, var, f"fold{k}_s{sd}"), a.device, log)
                d = torch.load(os.path.join(a.outdir, var, f"fold{k}_s{sd}", "best.pt"), weights_only=False)
                from train_v2 import build_model
                m = build_model(var, d["cfg"], va[0]["T"]); m.load_state_dict(d["state_dict"]); m.to(a.device)
                tot = sum(replay_cost(order_score(p, c, rule), g["time_s"].numpy(), g["succ"].numpy())[0]
                          for (p, c), g in zip(predict(m, va, b), va))
                res.append({"fold": k, "variant": var, "seed": sd, "total": tot, "ratio_vs_fewest": tot / heur["fewest_contacts"],
                            "best_epoch": r["best_epoch"]})
                log(f"fold {k} {var} s{sd}: total {tot:.0f} (fewest {heur['fewest_contacts']:.0f}, ratio {tot / heur['fewest_contacts']:.3f})")
                json.dump(res, open(os.path.join(a.outdir, "cv_results.json"), "w"), indent=1)
    log_load(a.outdir, "end")


if __name__ == "__main__":
    main()
