#!/usr/bin/env python
"""Campaign Phase 3: live full-disassembly results on the v2 test set (PREREG §6; addendum B).

Input: <dir>/results.jsonl from scripts/live_abd.py (every attempt). Per (assembly, method) the reported attempt is the
first clean one (not confounded), else attempt 0, flagged (PREREG §0/§6, CLAUDE.md).
Per-assembly cost = total planner time of the whole disassembly attempt (complete or stuck; a stuck run's
unsolved queries count, which is what that ordering cost). Trained variants: per-assembly seed-mean over the seeds
present (PREREG §5); a variant with fewer than 5 seeds on an assembly is reported with its seed count.
Registered comparisons: GNN-Surv vs the 9 + 2 intervention pairs, one Holm family of 11 (as in replay). The §7 rule
is applied to live separately (heuristic = fewest contacts, chosen on val). Assemblies enter a comparison only if both
methods have a result there. Exploratory rows (GT-Surv, ListNet, @b3 budget policy) get their own table with uncorrected
p-values. Sensitivity: the §7 rule on the 306 clean test assemblies (addendum A).
"""
import argparse
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REG = ["random", "outside_in", "fewest_contacts", "asap_zs", "asap_retrained", "mlp_bce", "mlp_survival", "gnn_bce",
       "gnn_survival", "gnn_survival_tail", "pn_gnn_survival"]
EXPL = ["gt_survival", "gnn_survival_listnet", "fewest_contacts@b3", "gnn_survival@b3"]
MAIN = "gnn_survival"
COMP = [(MAIN, b) for b in ("random", "outside_in", "fewest_contacts", "asap_zs", "asap_retrained", "mlp_survival",
                            "gnn_bce", "gnn_survival_tail", "pn_gnn_survival")] + [("gnn_bce", "mlp_bce"), ("mlp_survival", "mlp_bce")]


def base(m):
    """'gnn_survival#s101@b3' -> ('gnn_survival@b3', 101); 'fewest_contacts' -> ('fewest_contacts', None)."""
    pol = ""
    if "@b" in m:
        m, p = m.split("@b"); pol = "@b" + p
    if "#s" in m:
        v, s = m.split("#s")
        return v + pol, int(s)
    return m + pol, None


def pbin(n):
    return "3-4" if n <= 4 else "5-6" if n <= 6 else "7-8" if n <= 8 else "9-10" if n <= 10 else "11-12"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--md", required=True)
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--clean", default=os.path.join(ROOT, "experiments/2026-11-24_run04_t8_split/t6_test_overlap.json"))
    a = ap.parse_args()
    from disasm.eval.stats import holm, paired
    att = defaultdict(list)
    for l in open(os.path.join(a.dir, "results.jsonl")):
        r = json.loads(l)
        att[(r["assembly_id"], r["method"])].append(r)
    rep, flags = {}, defaultdict(int)
    for k, rs in att.items():
        rs = sorted(rs, key=lambda r: r.get("attempt", 0))
        clean = [r for r in rs if not r.get("confounded") and not r.get("error")]
        rep[k] = clean[0] if clean else rs[0]
        if not clean:
            flags["still_confounded_or_error"] += 1
        if len(rs) > 1:
            flags["re-run"] += 1
    split = json.load(open(os.path.join(ROOT, "data/splits/v2_split.json")))
    test = sorted(split["test"])
    cost = defaultdict(dict)        # method(base) -> aid -> list of per-seed planner_s
    status = defaultdict(lambda: defaultdict(int))
    for (aid, m), r in rep.items():
        if r.get("error"):
            status[base(m)[0]]["error"] += 1
            continue
        b, s = base(m)
        cost[b].setdefault(aid, []).append(float(r["planner_s"]))
        status[b][r.get("status")] += 1
    per = {m: {aid: float(np.mean(v)) for aid, v in d.items()} for m, d in cost.items()}
    nseeds = {m: {aid: len(v) for aid, v in d.items()} for m, d in cost.items()}
    L = ["# Final live evaluation on the v2 test set (PREREG §6; evaluated once)\n",
         f"Source `{os.path.relpath(a.dir, ROOT)}/results.jsonl` (every attempt), summarised by `scripts/live_report_v2.py`. "
         "Fresh queries with oracle v2 (pre-check → CMG-RRT only when the pull fails), T = 30 s, planner seed per query = "
         "sha1(\"run05-live\", assembly, state, part), idle guard on, confounded runs re-run up to 2× (first clean attempt "
         f"reported). Per-assembly cost = total planner time of the disassembly. CIs: bootstrap over assemblies ({a.boot}).\n",
         f"- (assembly, method) runs: {len(rep)}; re-run at least once: {flags['re-run']}; still confounded or errored after "
         f"re-runs (reported, flagged): {flags['still_confounded_or_error']}.\n",
         "| ordering | assemblies | seeds per assembly | complete / stuck / error | total planner time (s) [95% CI over assemblies] |",
         "|---|---|---|---|---|"]
    res = {"n_runs": len(rep), "flags": dict(flags), "methods": {}}
    for m in [x for x in REG + EXPL if x in per]:
        aids = sorted(per[m])
        v = np.array([per[m][i] for i in aids])
        idx = np.random.default_rng(0).integers(0, len(v), (a.boot, len(v)))
        bs = v[idx].sum(1)
        ns = sorted(set(nseeds[m].values()))
        L.append(f"| {m}{' [expl.]' if m in EXPL else ''} | {len(aids)} | {ns} | {status[m]['complete']} / {status[m]['stuck']} / "
                 f"{status[m]['error']} | {v.sum():.0f} [{np.percentile(bs, 2.5):.0f}, {np.percentile(bs, 97.5):.0f}] |")
        res["methods"][m] = {"n": len(aids), "total": float(v.sum()), "seeds": ns, "status": dict(status[m])}

    def family(pairs, aids_ok, label, correct=True):
        out = []
        for x, y in pairs:
            if x not in per or y not in per:
                continue
            ids = sorted(set(per[x]) & set(per[y]) & aids_ok)
            pr = paired([per[x][i] for i in ids], [per[y][i] for i in ids], a.boot)
            pr.update({"a": x, "b": y}); out.append(pr)
        if correct and out:
            for pr, ph in zip(out, holm([q["p"] for q in out])):
                pr["p_holm"] = float(ph)
        L.append(f"\n### {label}\n")
        L.append("| A vs B | n | ratio of totals [95% CI] | HL (s) [95% CI] | W / T / L | Wilcoxon p" + (" | Holm p |" if correct else " (uncorrected) |"))
        L.append("|---|---|---|---|---|---|" + ("---|" if correct else ""))
        for pr in out:
            L.append(f"| {pr['a']} vs {pr['b']} | {pr['n']} | {pr['ratio']:.3f} [{pr['ratio_ci'][0]:.3f}, {pr['ratio_ci'][1]:.3f}] | "
                     f"{pr['hl']:+.2f} [{pr['hl_ci'][0]:+.2f}, {pr['hl_ci'][1]:+.2f}] | {pr['wins']} / {pr['ties']} / {pr['losses']} | "
                     f"{pr['p']:.2g} |" + (f" {pr['p_holm']:.2g} |" if correct else ""))
        return out

    allids = set(test)
    res["registered"] = family(COMP, allids, "Registered comparisons (Holm family of 11)")
    pr = next((q for q in res["registered"] if q["a"] == MAIN and q["b"] == "fewest_contacts"), None)
    if pr:
        ca, cb = pr["ratio_ci"][1] < 1.0, pr["p_holm"] < 0.05 and pr["hl"] < 0
        v = "beats" if (ca and cb) else ("cheaper on the typical assembly, not on total time" if cb else "does not beat")
        res["s7_live"] = {"a": ca, "b": cb, "verdict": v}
        L.append(f"\n**§7 rule applied to LIVE (separately, PREREG §7):** GNN-Surv / fewest contacts = {pr['ratio']:.3f} "
                 f"[{pr['ratio_ci'][0]:.3f}, {pr['ratio_ci'][1]:.3f}], HL {pr['hl']:+.2f} s, Holm p {pr['p_holm']:.2g} → (a) {ca}, "
                 f"(b) {cb}: **{v}**")
    clean = set(json.load(open(a.clean))["clean_test"])
    res["sensitivity_clean"] = family(COMP, clean, f"Sensitivity (addendum A): same family on the {len(clean)} clean test assemblies")
    res["exploratory"] = family([("gt_survival", "fewest_contacts"), ("gnn_survival_listnet", "fewest_contacts"),
                                 ("gt_survival", MAIN), ("gnn_survival_listnet", MAIN),
                                 ("fewest_contacts@b3", "fewest_contacts"), ("gnn_survival@b3", "gnn_survival"),
                                 ("gnn_survival@b3", "fewest_contacts@b3")], allids,   # gnn_survival@b3 = val-best seed only (addendum B.2)
                                "Exploratory (post-registration; uncorrected p)", correct=False)
    # subsets: GNN-Surv vs fewest contacts
    L.append("\n### Subsets (GNN-Surv vs fewest contacts; reported, never used for selection; < 30 assemblies = underpowered)\n")
    L.append("| subset | n | ratio [95% CI] | HL (s) | W/T/L | p (uncorrected) |\n|---|---|---|---|---|---|")
    res["subsets"] = {}
    subs = {f"source={s}": {x for x in test if split["sources"][x] == s} for s in ("fresh-9to12", "fresh-allowance")}
    subs.update({f"parts={b}": {x for x in test if pbin(split["n_parts"][x]) == b} for b in ("3-4", "5-6", "7-8", "9-10", "11-12")})
    if MAIN in per and "fewest_contacts" in per:
        for k, ids in subs.items():
            ids = sorted(ids & set(per[MAIN]) & set(per["fewest_contacts"]))
            if len(ids) < 2:
                continue
            q = paired([per[MAIN][i] for i in ids], [per["fewest_contacts"][i] for i in ids], a.boot)
            res["subsets"][k] = q
            L.append(f"| {k}{' (UNDERPOWERED)' if len(ids) < 30 else ''} | {len(ids)} | {q['ratio']:.3f} [{q['ratio_ci'][0]:.3f}, "
                     f"{q['ratio_ci'][1]:.3f}] | {q['hl']:+.2f} | {q['wins']}/{q['ties']}/{q['losses']} | {q['p']:.2g} |")
    json.dump(res, open(os.path.join(a.dir, "live_summary.json"), "w"), indent=1, default=float)
    open(a.md, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
