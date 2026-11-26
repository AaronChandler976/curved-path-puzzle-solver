#!/usr/bin/env python
"""Vector (PDF) qualitative figure for the paper: one state of the demo disassembly (experiments/2026-11-26_demo_01310),
the removed part shown at 4 poses along its logged CMG-RRT path, with the GNN-Surv order and predicted p, c.
All drawn values come from that run's results.jsonl and saved path file."""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live-dir", default=os.path.join(ROOT, "experiments/2026-11-26_demo_01310"))
    ap.add_argument("--aid", default="01310")
    ap.add_argument("--method", default="gnn_survival#s101")
    ap.add_argument("--state", type=int, default=-1)
    ap.add_argument("--max-faces", type=int, default=700)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from taucgl_rrt.cspace import SE3
    from disasm.oracle.cmgrrt import load_assembly
    from render_demo import path_poses
    plt.rcParams.update({"pdf.fonttype": 42, "font.size": 7})
    run = [json.loads(l) for l in open(os.path.join(a.live_dir, "results.jsonl"))]
    run = [r for r in run if r["assembly_id"] == a.aid and r["method"] == a.method][0]
    st = run["states"][a.state]
    ch = st["chosen"]
    q = [x for x in st["queries"] if x["part"] == ch][0]
    poses = path_poses(q["path_file"], n_tree_frames=12, n_edge_frames=6)[:12]     # the rotating tree part of the path
    pick = [poses[int(i)] for i in np.linspace(0, len(poses) - 1, 4).round()]
    asm = load_assembly(os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly", a.aid))
    rng = np.random.default_rng(0)
    present = [int(x) for x in st["state_key"].split("-")]
    tris = {}
    ch = st["chosen"]
    for p in present:
        m = asm.meshes[p]
        F = m.faces if (len(m.faces) <= a.max_faces or p == ch) else m.faces[rng.choice(len(m.faces), a.max_faces, replace=False)]
        tris[p] = (np.asarray(m.vertices), np.asarray(F))
    b = np.array([asm.meshes[p].bounds for p in present])
    c0, span = (b[:, 0].min(0) + b[:, 1].max(0)) / 2, (b[:, 1].max(0) - b[:, 0].min(0)).max()
    fig = plt.figure(figsize=(7.0, 2.1))
    for k, pose in enumerate(pick):
        ax = fig.add_subplot(1, 4, k + 1, projection="3d")
        for p in present:
            V, F = tris[p]
            if p == ch:
                M = SE3(*pose).to_matrix(); V = V @ M[:3, :3].T + M[:3, 3]
            fc = (0.165, 0.471, 0.839, 0.9) if p == ch else (0.62, 0.62, 0.60, 0.25)
            ax.add_collection3d(Poly3DCollection(V[F], facecolor=fc, edgecolor="none"))
        r = span * 0.6
        ax.set_xlim(c0[0] - r, c0[0] + r); ax.set_ylim(c0[1] - r, c0[1] + r); ax.set_zlim(c0[2] - r, c0[2] + r)
        ax.set_axis_off(); ax.view_init(elev=22, azim=-55); ax.set_box_aspect(None, zoom=1.6)
        rot = np.degrees(2 * np.arccos(min(1.0, abs(pose[3]))))
        ax.set_title(f"rotation {rot:.0f}°", fontsize=7)
    order = "; ".join(f"part {p}: p={st['p'][str(p)]:.2f}, c={st['c'][str(p)]:.1f} s" for p in st["order"])
    fig.suptitle(f"Test assembly {a.aid}, last state (parts {st['state_key']}); GNN-Surv order: {order}\n"
                 f"part {ch} (blue) succeeded in {q['time_s']:.2f} s: straight pull blocked, CMG-RRT path with rotation",
                 fontsize=6.5, y=0.99)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=0.80, wspace=0)
    fig.savefig(a.out)
    print(a.out, q["time_s"], q.get("stage"))


if __name__ == "__main__":
    main()
