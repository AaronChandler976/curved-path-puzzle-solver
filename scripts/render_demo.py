#!/usr/bin/env python
"""R7 (run 03): demo asset for one live GNN-Surv disassembly (from experiments/2026-11-23_run03_live/results.jsonl).

Renders, for every state of the live run: the GNN-Surv query order with predicted p and c per part, each query's
logged outcome and planner time, and the extraction path of the part that succeeded (logged CMG-RRT path; the final
straight tree edge to the far goal is linearly interpolated for display, as in scripts/render_path.py).
Writes <out>.gif (imageio) and <out>_strip.png. All numbers drawn come from the live run's log.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def path_poses(path_file, n_tree_frames=10, n_edge_frames=14):
    raw = json.load(open(os.path.join(ROOT, path_file) if not os.path.isabs(path_file) else path_file))["path"]
    tree = raw[:-1]
    idx = np.linspace(0, len(tree) - 1, min(n_tree_frames, len(tree))).round().astype(int)
    poses = [np.asarray(tree[i]) for i in idx]
    a0, a1 = np.asarray(raw[-2]), np.asarray(raw[-1])
    for f in np.linspace(0, 1, n_edge_frames)[1:]:
        q = a0 + f * (a1 - a0)
        q[3:] /= np.linalg.norm(q[3:])
        poses.append(q)
    return poses


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live-dir", default=os.path.join(ROOT, "experiments/2026-11-23_run03_live"))
    ap.add_argument("--aid", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "reports/run03/figures/demo"))
    ap.add_argument("--max-faces", type=int, default=2500)
    args = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import imageio.v2 as imageio
    from taucgl_rrt.cspace import SE3
    from disasm.oracle.cmgrrt import load_assembly
    run = [json.loads(l) for l in open(os.path.join(args.live_dir, "results.jsonl"))]
    run = [r for r in run if r["assembly_id"] == args.aid and r["method"] == "gnn_surv"][0]
    asm = load_assembly(os.path.join(ROOT, "data/raw/multi_assembly/multi_assembly", args.aid))
    rng = np.random.default_rng(0)
    tris = {}
    for p, m in asm.meshes.items():
        F = m.faces if len(m.faces) <= args.max_faces else m.faces[rng.choice(len(m.faces), args.max_faces, replace=False)]
        tris[p] = (np.asarray(m.vertices), np.asarray(F))
    b = np.array([m.bounds for m in asm.meshes.values()])
    c0, span = (b[:, 0].min(0) + b[:, 1].max(0)) / 2, (b[:, 1].max(0) - b[:, 0].min(0)).max()
    cmap = plt.get_cmap("tab10")
    color = {p: cmap(i % 10) for i, p in enumerate(asm.part_ids)}

    def draw(ax, present, moving=None, pose=None):
        for p in present:
            V, F = tris[p]
            if p == moving and pose is not None:
                M = SE3(*pose).to_matrix()
                V = V @ M[:3, :3].T + M[:3, 3]
            fc = (*color[p][:3], 0.9 if p == moving else 0.35)
            ax.add_collection3d(Poly3DCollection(V[F], facecolor=fc, edgecolor=(0, 0, 0, 0.04), linewidths=0.1))
        r = span * 0.9
        ax.set_xlim(c0[0] - r, c0[0] + r); ax.set_ylim(c0[1] - r, c0[1] + r); ax.set_zlim(c0[2] - r, c0[2] + r)
        ax.set_axis_off(); ax.view_init(elev=22, azim=-55)

    def text_panel(ax, st, k, nst):
        ax.axis("off")
        lines = [f"assembly {args.aid}  state {k + 1}/{nst}  present: {st['state_key']}",
                 "GNN-Surv order (score p/c):"]
        outc = {q["part"]: q for q in st["queries"]}
        for i, p in enumerate(st["order"]):
            q = outc.get(p)
            res = "not queried" if q is None else (f"SUCCESS {q['time_s']:.2f} s" if q["outcome"] == "success"
                                                   else f"unsolved {q['time_s']:.1f} s")
            lines.append(f" {i + 1}. part {p}: p={st['p'][str(p)] if isinstance(next(iter(st['p'])), str) else st['p'][p]:.2f} "
                         f"c={st['c'][str(p)] if isinstance(next(iter(st['c'])), str) else st['c'][p]:.1f}s -> {res}")
        ax.text(0.0, 1.0, "\n".join(lines), va="top", family="monospace", fontsize=8)

    frames, strip = [], []
    nst = len(run["states"])
    removed = []
    for k, st in enumerate(run["states"]):
        present = [int(x) for x in st["state_key"].split("-")]
        ch = st["chosen"]
        q = [x for x in st["queries"] if x["part"] == ch][0] if ch is not None else None
        poses = path_poses(q["path_file"]) if q and q.get("path_file") else [None]
        for j, pose in enumerate(poses):
            fig = plt.figure(figsize=(9, 4.2))
            ax = fig.add_subplot(1, 2, 1, projection="3d")
            draw(ax, present, ch, pose)
            rot = 0.0 if pose is None else np.degrees(2 * np.arccos(min(1.0, abs(pose[3]))))
            ax.set_title(f"part {ch} leaving (rotation {rot:.0f}°)" if ch is not None else "stuck", fontsize=9)
            text_panel(fig.add_subplot(1, 2, 2), st, k, nst)
            fig.tight_layout()
            fig.canvas.draw()
            img = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
            frames.append(img)
            if j == len(poses) // 2:
                strip.append(img)
            plt.close(fig)
        removed.append(ch)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    imageio.mimsave(args.out + ".gif", frames, duration=0.12, loop=0)
    h = max(s.shape[0] for s in strip)
    imageio.imwrite(args.out + "_strip.png", np.concatenate([s[:h] for s in strip], 0))
    print(json.dumps({"gif": args.out + ".gif", "strip": args.out + "_strip.png", "frames": len(frames),
                      "states": nst, "planner_s": run["planner_s"], "calls": run["calls"], "status": run["status"]}))


if __name__ == "__main__":
    main()
