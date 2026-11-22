#!/usr/bin/env python
"""Render a logged CMG-RRT extraction path for a multi-part assembly as a PNG strip
(matplotlib 3D, headless). The obstacle parts are grey; the moving part is drawn at evenly spaced
poses along the path, using the same SE3 -> matrix conversion as CMG-RRT (taucgl_rrt.cspace.SE3).

Usage: render_path.py --assembly-dir DIR --part P --removed 1,2 --path-file F --out PNG
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--assembly-dir", required=True)
    ap.add_argument("--part", type=int, required=True)
    ap.add_argument("--removed", default="")
    ap.add_argument("--path-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", type=int, default=5)
    args = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from taucgl_rrt.cspace import SE3
    from disasm.oracle.cmgrrt import load_assembly

    a = load_assembly(args.assembly_dir)
    removed = {int(x) for x in args.removed.split(",") if x}
    path = json.load(open(args.path_file))["path"]
    # keep only the part of the path near the assembly (the last edge jumps to the far goal)
    idx = np.linspace(0, len(path) - 1, args.frames).round().astype(int)
    obst = [p for p in a.part_ids if p not in removed and p != args.part]
    b = np.array([a.meshes[p].bounds for p in a.part_ids if p not in removed])
    lo, hi = b[:, 0].min(0), b[:, 1].max(0)
    span = (hi - lo).max()
    fig = plt.figure(figsize=(3.2 * args.frames, 3.4))
    for k, i in enumerate(idx):
        ax = fig.add_subplot(1, args.frames, k + 1, projection="3d")
        for p in obst:
            m = a.meshes[p]
            ax.add_collection3d(Poly3DCollection(m.vertices[m.faces], facecolor=(0.7, 0.7, 0.7, 0.25),
                                                 edgecolor=(0.4, 0.4, 0.4, 0.05), linewidths=0.1))
        m = a.meshes[args.part].copy()
        m.apply_transform(SE3(*path[i]).to_matrix())
        ax.add_collection3d(Poly3DCollection(m.vertices[m.faces], facecolor=(0.85, 0.3, 0.2, 0.8),
                                             edgecolor=(0.5, 0.1, 0.1, 0.2), linewidths=0.1))
        c = (lo + hi) / 2
        r = span * (0.9 if k < args.frames - 1 else 1.6)
        last = np.asarray(path[i][:3])
        if k == args.frames - 1:
            c = (c + last + m.centroid - a.meshes[args.part].centroid) / 2 if np.linalg.norm(last) < 3 * span else c
        for setlim, j in ((ax.set_xlim, 0), (ax.set_ylim, 1), (ax.set_zlim, 2)):
            setlim(c[j] - r, c[j] + r)
        ax.set_axis_off()
        rot = np.degrees(2 * np.arccos(min(1.0, abs(path[i][3]))))
        ax.set_title(f"node {i}/{len(path) - 1}\nt=({path[i][0]:+.2f},{path[i][1]:+.2f},{path[i][2]:+.2f}) rot {rot:.0f} deg",
                     fontsize=7)
    fig.suptitle(f"assembly {a.id}: part {args.part} leaves (removed {sorted(removed)}); CMG-RRT logged path "
                 f"{os.path.basename(args.path_file)}", fontsize=8)
    fig.tight_layout()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fig.savefig(args.out, dpi=110)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
