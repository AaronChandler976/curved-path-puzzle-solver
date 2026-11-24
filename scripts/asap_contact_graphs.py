#!/usr/bin/env python
"""Run 04 T2.1: ASAP's OWN contact graphs (redmax ``body_in_contact``, eps = CONTACT_EPS = 0.1 raw units), computed
with ASAP's unmodified ``plan_sequence.feasibility_check.get_contact_graph``. Runs in the ``asap`` conda env (Python
3.8, redmax built from a copy of external/ASAP/simulation in build/asap_simulation; see reports/run04/DECISIONS.md).
Use PYTHONDONTWRITEBYTECODE=1 so nothing is written under external/.

Output: one json line per assembly {assembly_id, edges: [[a, b], ...], n_parts, time_s, error}.
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASAP = os.path.join(ROOT, "external/ASAP")
sys.path.insert(0, ASAP)
RAW = os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ids", required=True, help="json list of assembly ids")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from plan_sequence.physics_planner import get_contact_graph, CONTACT_EPS
    ids = json.load(open(a.ids))
    with open(a.out, "w") as f:
        for aid in ids:
            t0 = time.time()
            rec = {"assembly_id": aid, "contact_eps": CONTACT_EPS}
            try:
                G = get_contact_graph(os.path.join(ASAP, "assets"), os.path.join(RAW, aid))
                rec.update({"edges": sorted([sorted([int(u), int(v)]) for u, v in G.edges]),
                            "n_parts": G.number_of_nodes(), "error": None})
            except Exception as e:  # noqa: BLE001
                rec.update({"edges": None, "error": f"{type(e).__name__}: {e}"})
            rec["time_s"] = time.time() - t0
            f.write(json.dumps(rec) + "\n")
            f.flush()
            print(aid, rec.get("n_parts"), len(rec["edges"] or []), rec["error"], f"{rec['time_s']:.1f}s", flush=True)


if __name__ == "__main__":
    main()
