#!/usr/bin/env python
"""Run 04 T5: re-check every SOLVED bundled-puzzle path (learned or exact detector) with the EXACT SDF of 0.obj at
step <= |threshold|/2 (path_validate.validate_path), using the run's own seeded robot samples (same seed -> same draw).
Tells whether a learned-SDF success is also collision-free under the exact geometry. Untimed CPU work."""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EX_ROOT = os.path.join(ROOT, "external/cmg-rrt/resources/models")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True)
    a = ap.parse_args()
    import trimesh
    from scipy.spatial.transform import Rotation as Rr
    from disasm.oracle.cmgrrt import robot_sample_seed, seeded_surface_sampling
    from disasm.oracle.cmgrrt_core import PlannerParams
    from disasm.oracle.exact_sdf import ExactUnionSDF, PartSDF, make_detector
    from disasm.oracle.path_validate import validate_path
    from taucgl_rrt.cspace import SE3
    out = []
    for l in open(os.path.join(a.run_dir, "results.jsonl")):
        r = json.loads(l)
        if not r["success"]:
            continue
        tag = f"{r['example'].replace('/', '_')}_s{r['seed']}" + ("_exact" if r["detector"] == "exact" else "") + \
            (f"_gdx{r['grad_dx']:g}" if r.get("grad_dx") else "")
        pf = os.path.join(a.run_dir, f"{tag}_path.json")
        ex = os.path.join(EX_ROOT, r["example"])
        props = json.load(open(os.path.join(ex, "properties.json")))
        m0 = trimesh.load_mesh(os.path.join(ex, "0.obj"), process=True)
        union = ExactUnionSDF([PartSDF(m0.vertices, m0.faces)])
        q1 = SE3(*props["q1"])
        cd = make_detector(PlannerParams(threshold=r["threshold"], sampling=r["sampling"]), "cpu", union, q1=q1)
        cd.set_robot(os.path.join(ex, "1.obj"))
        np.random.seed(r["seed"])
        with seeded_surface_sampling(robot_sample_seed(r["seed"]) if r.get("seeded_samples", True) else None):
            cd.generate_robot_sampling(r["sampling"])
        S = np.asarray(cd.robot["sampling"], dtype=np.float64)
        Ainv = np.linalg.inv(q1.to_matrix())
        rel = []
        for p in json.load(open(pf)):
            M = Ainv @ SE3(*p).to_matrix()
            q = Rr.from_matrix(M[:3, :3]).as_quat()
            rel.append([*M[:3, 3], q[3], q[0], q[1], q[2]])
        v = validate_path(union, S, rel, abs(r["threshold"]))
        rec = {"tag": tag, "detector": r["detector"], "valid_exact_fine": v["valid"], "n_bad_edges": v["n_bad"],
               "n_edges": v["n_edges"], "d_min": v["d_min"]}
        print(json.dumps(rec), flush=True)
        out.append(rec)
    json.dump(out, open(os.path.join(a.run_dir, "path_recheck_exact.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
