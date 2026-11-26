#!/usr/bin/env python
"""Run 04 T3: report for the unconfounded rerun of run 03 R6 ("run 03 models, development test set").

Same tables as reports/run03/results_live.md (scripts/live_report.py), computed on the FIRST CLEAN ATTEMPT of every
(assembly, method) run (attempt 0 if clean, else the first clean re-run; runs still confounded after 2 re-runs are
kept and counted). Added (run 04 write-up standard): Hodges-Lehmann median paired difference with a bootstrap CI and
wins/ties/losses, next to the ratio of totals. Then a side-by-side with the confounded run 03 numbers on the same
assemblies. CIs: bootstrap over assemblies (10,000 resamples, seed 0). Tests: Wilcoxon signed-rank, Holm over the 3
comparisons of each table.
"""
import argparse
import json
import os
from collections import defaultdict

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
METHODS = [("random", "random"), ("fewest_contacts", "fewest contacts"), ("asap", "ASAP GNN (released weights, zero-shot)"),
           ("gnn_surv", "GNN-Surv (p/c), seed 101")]
MAIN = "gnn_surv"


def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); adj = np.empty_like(p); run = 0.0
    for k, i in enumerate(o):
        run = max(run, min(1.0, (len(p) - k) * p[i])); adj[i] = run
    return adj


def hl(d):
    """Hodges-Lehmann estimator of the median paired difference (median of Walsh averages)."""
    d = np.asarray(d, float)
    i, j = np.triu_indices(len(d))
    return float(np.median((d[i] + d[j]) / 2))


def load_runs(path):
    att = defaultdict(list)
    for l in open(path):
        r = json.loads(l)
        att[(r["assembly_id"], r["method"])].append(r)
    by, stats = defaultdict(dict), {"runs": 0, "clean_first": 0, "fixed_by_rerun": 0, "still_confounded": 0,
                                    "attempts": 0, "no_guard": 0}
    for (a, m), xs in att.items():
        xs = sorted(xs, key=lambda r: r.get("attempt", 0))
        stats["runs"] += 1
        stats["attempts"] += len(xs)
        if "confounded" not in xs[0]:
            stats["no_guard"] += 1
            pick = xs[0]
        else:
            clean = [x for x in xs if not x["confounded"]]
            pick = clean[0] if clean else xs[0]
            pick = dict(pick)
            pick["still_confounded"] = not clean
            stats["clean_first"] += (not xs[0]["confounded"])
            stats["fixed_by_rerun"] += bool(clean) and xs[0]["confounded"]
            stats["still_confounded"] += not clean
        by[a][m] = pick
    return by, stats


def paired_rows(by, sub, rng):
    A = np.array([by[a][MAIN]["planner_s"] for a in sub])
    rows, pv = [], []
    from scipy.stats import wilcoxon
    for m, name in METHODS:
        if m == MAIN:
            continue
        B = np.array([by[a][m]["planner_s"] for a in sub])
        d = A - B
        idx = rng.integers(0, len(d), (10000, len(d)))
        ci = np.percentile(d[idx].mean(1), [2.5, 97.5])
        rr = np.percentile(A[idx].sum(1) / B[idx].sum(1), [2.5, 97.5])
        hls = np.array([hl(d[k]) for k in idx[:2000]])
        hci = np.percentile(hls, [2.5, 97.5])
        try:
            p = float(wilcoxon(A, B).pvalue)
        except ValueError:
            p = 1.0
        pv.append(p)
        ca = sum(by[a][MAIN]["calls"] for a in sub); cb = sum(by[a][m]["calls"] for a in sub)
        rows.append({"m": m, "name": name, "A": A.sum(), "B": B.sum(), "md": d.mean(), "ci": ci, "r": A.sum() / B.sum(),
                     "rr": rr, "hl": hl(d), "hci": hci,
                     "wtl": (int((d < -0.01).sum()), int((abs(d) <= 0.01).sum()), int((d > 0.01).sum())),
                     "p": p, "ca": ca, "cb": cb})
    for r, pa in zip(rows, holm(pv)):
        r["holm"] = pa
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default=os.path.join(ROOT, "experiments/2026-11-23_run04_live_rerun"))
    ap.add_argument("--run03", default=os.path.join(ROOT, "experiments/2026-11-23_run03_live"))
    ap.add_argument("--out", default=os.path.join(ROOT, "reports/run04/live_rerun.md"))
    args = ap.parse_args()
    meta = json.load(open(os.path.join(ROOT, "data/processed/run03/asm_meta.json")))
    by, st = load_runs(os.path.join(args.dir, "results.jsonl"))
    old, _ = load_runs(os.path.join(args.run03, "results.jsonl"))
    aids = sorted(by)
    rng = np.random.default_rng(0)
    rel = os.path.relpath(args.dir, ROOT)
    errs = [r for a in aids for r in by[a].values() if r.get("error")]
    nq = sum(len(s["queries"]) for a in aids for r in by[a].values() for s in r.get("states", []))
    nqc = sum(q.get("confounded", False) for a in aids for r in by[a].values() for s in r.get("states", []) for q in s["queries"])
    L = ["# Run 04 T3: unconfounded rerun of run 03 R6 — **run 03 models, development test set**\n",
         "These are run 03's frozen models on run 03's (spent) test split. This is a development result, NOT the final "
         "test (the final test is the v2 test split, evaluated once in run 05).\n",
         f"Run folder `{rel}/` (`results.jsonl`: one line per attempt of each assembly x method run; `idle_samples.jsonl`: "
         f"every 5 s idle-guard sample; `stdout.log`; `load_info.txt`). Script `scripts/live_abd.py` (command in `launch_cmd.txt`), "
         "report `scripts/live_rerun_report.py`. Identical to run 03 R6: the same 60 assemblies, the same 4 methods, the same "
         "GNN-Surv checkpoint (seed 101), the same planner seeds (sha1('run03-live', assembly, state, part)), exact union-SDF "
         "oracle v1 (CMG-RRT only), ε = 0.005, T = 30 s, 10 workers. New in run 04: seeded robot sampling (the same query is "
         "reproducible across methods up to the wall-clock T) and the idle guard (CLAUDE.md Run 04 rules).\n",
         f"- runs: {st['runs']} (attempts incl. re-runs: {st['attempts']}); clean on the first attempt: {st['clean_first']}; "
         f"confounded then clean on a re-run: {st['fixed_by_rerun']}; **still confounded after 2 re-runs: {st['still_confounded']}** "
         "(kept, flagged).",
         f"- queries in the reported attempts: {nq}; confounded among them: {nqc} ({100 * nqc / max(1, nq):.2f}%).",
         f"- assemblies: {len(aids)} ({sum(meta[a]['rot_assembly'] for a in aids)} rot_assembly); runs with errors: {len(errs)}\n",
         "## Per-method summary (all sampled assemblies)\n",
         "| method | complete / stuck | total planner time (s) | mean planner s per assembly [95% CI] | planner calls (total) | mean wall s per assembly incl. setup |",
         "|---|---|---|---|---|---|"]
    for m, name in METHODS:
        rs = [by[a][m] for a in aids if m in by[a]]
        pl = np.array([r.get("planner_s", np.nan) for r in rs])
        idx = rng.integers(0, len(pl), (10000, len(pl)))
        ci = np.nanpercentile(np.nanmean(pl[idx], 1), [2.5, 97.5])
        L.append(f"| {name} | {sum(r.get('status') == 'complete' for r in rs)} / {sum(r.get('status') == 'stuck' for r in rs)} | "
                 f"{np.nansum(pl):.0f} | {np.nanmean(pl):.1f} [{ci[0]:.1f}, {ci[1]:.1f}] | {sum(r.get('calls') or 0 for r in rs)} | "
                 f"{np.mean([r['wall_s'] for r in rs]):.1f} |")
    allc = [a for a in aids if all(by[a].get(m, {}).get("status") == "complete" for m, _ in METHODS)]

    def table(sub, label):
        out = [f"\n## Paired comparison: {label} ({len(sub)} assemblies completed by all methods)\n"]
        if len(sub) < 2:
            return out + ["too few assemblies"]
        if len(sub) < 30:
            out.append(f"**Underpowered** (n = {len(sub)} < 30).\n")
        out += ["GNN-Surv minus each method; total planner time per full disassembly (negative = GNN-Surv cheaper). "
                "Primary: ratio of totals; co-reported: per-assembly Hodges–Lehmann median difference.\n",
                "| vs | GNN-Surv total / other total (s) | ratio of totals [95% CI] | HL median diff per assembly (s) [95% CI] | mean diff (s) [95% CI] | GNN-Surv wins / ties / losses | Wilcoxon p | Holm p | calls: GNN-Surv / other |",
                "|---|---|---|---|---|---|---|---|---|"]
        for r in paired_rows(by, sub, rng):
            out.append(f"| {r['name']} | {r['A']:.0f} / {r['B']:.0f} | {r['r']:.3f} [{r['rr'][0]:.3f}, {r['rr'][1]:.3f}] | "
                       f"{r['hl']:+.2f} [{r['hci'][0]:+.2f}, {r['hci'][1]:+.2f}] | {r['md']:+.1f} [{r['ci'][0]:+.1f}, {r['ci'][1]:+.1f}] | "
                       f"{r['wtl'][0]} / {r['wtl'][1]} / {r['wtl'][2]} | {r['p']:.2g} | {r['holm']:.2g} | {r['ca']} / {r['cb']} |")
        return out

    L += table(allc, "all")
    L += table([a for a in allc if meta[a]["rot_assembly"]], "rot_assembly subset")
    L += table([a for a in allc if not meta[a]["rot_assembly"]], "non-rot subset")

    # ------------------------------------------------------------- side by side with run 03 (confounded)
    both = [a for a in allc if a in old and all(old[a].get(m, {}).get("status") == "complete" for m, _ in METHODS)]
    L += ["\n## Side by side: run 04 rerun (unconfounded) vs run 03 R6 (confounded)\n",
          f"Same assemblies in both: {len(both)} (completed by all methods in both runs). Run 03 timings were all confounded "
          "(reports/run03/DECISIONS.md #12) and drew unseeded robot samples.\n",
          "| method | run 03 total planner s (all 60) | run 04 total planner s (all 60) | run 03 complete/stuck | run 04 complete/stuck |",
          "|---|---|---|---|---|"]
    for m, name in METHODS:
        o = [old[a][m] for a in sorted(old) if m in old[a]]
        n = [by[a][m] for a in aids if m in by[a]]
        L.append(f"| {name} | {sum(r.get('planner_s', 0) for r in o):.0f} | {sum(r.get('planner_s', 0) for r in n):.0f} | "
                 f"{sum(r.get('status') == 'complete' for r in o)}/{sum(r.get('status') == 'stuck' for r in o)} | "
                 f"{sum(r.get('status') == 'complete' for r in n)}/{sum(r.get('status') == 'stuck' for r in n)} |")
    if len(both) >= 2:
        r_old = {r["m"]: r for r in paired_rows(old, both, rng)}
        r_new = {r["m"]: r for r in paired_rows(by, both, rng)}
        L += [f"\nGNN-Surv vs each method on the {len(both)} assemblies completed by all methods in BOTH runs:\n",
              "| vs | run 03 ratio of totals [CI] | run 04 ratio of totals [CI] | run 03 HL diff (s) [CI] | run 04 HL diff (s) [CI] | run 03 W/T/L | run 04 W/T/L | run 03 Holm p | run 04 Holm p |",
              "|---|---|---|---|---|---|---|---|---|"]
        for m, name in METHODS:
            if m == MAIN:
                continue
            a, b = r_old[m], r_new[m]
            L.append(f"| {name} | {a['r']:.3f} [{a['rr'][0]:.3f}, {a['rr'][1]:.3f}] | {b['r']:.3f} [{b['rr'][0]:.3f}, {b['rr'][1]:.3f}] | "
                     f"{a['hl']:+.2f} [{a['hci'][0]:+.2f}, {a['hci'][1]:+.2f}] | {b['hl']:+.2f} [{b['hci'][0]:+.2f}, {b['hci'][1]:+.2f}] | "
                     f"{'/'.join(map(str, a['wtl']))} | {'/'.join(map(str, b['wtl']))} | {a['holm']:.2g} | {b['holm']:.2g} |")
    # outcome agreement per query between the runs (same seeds, different robot samples)
    L.append("\n## Load info (start / end)\n\n```")
    L.append(open(os.path.join(args.dir, "load_info.txt")).read().strip())
    L.append("```")
    if errs:
        L.append("\nErrors: " + "; ".join(f"{r['assembly_id']}/{r['method']}: {r['error']}" for r in errs))
    open(args.out, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
