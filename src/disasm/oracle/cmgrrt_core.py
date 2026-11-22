"""Thin runner around the CMG-RRT library (external/cmg-rrt, unmodified).

Mirrors the loop in external/cmg-rrt/scripts/test_all.py, but uses the constructor
signatures the library actually has (as in scripts/debug_rrt.py):
    CollisionDetector(sdf_N, sdf_H, device, threshold, eta, eps_contact=|threshold|)
    RRT(cd, q1, q2_start, q2_end)
and adds a wall-clock budget. No GUI. A run that does not reach the goal inside the budget
is reported as "unsolved" (a sampling planner cannot prove infeasibility).
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, asdict

import numpy as np
import torch

from taucgl_rrt.rrt import RRT
from taucgl_rrt.cspace import SE3
from taucgl_rrt.collision_detection import CollisionDetector


@dataclass
class PlannerParams:
    # defaults = external/cmg-rrt/scripts/test_list.json
    eta: float = 0.002
    threshold: float = -0.005
    steps: int = 50
    sampling: int = 4000
    sdf_N: int = 12
    sdf_H: int = 64


def seed_all(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def run_cmgrrt(robot_mesh_path: str, obstacle_sdf_path: str, q1, q2_start, q2_end,
               params: PlannerParams, device: str = "cpu", timeout_s: float = 600.0,
               max_iterations: int | None = None, seed: int = 0) -> dict:
    """Run one CMG-RRT query. q* are 7-lists [x, y, z, qw, qx, qy, qz] (CMG-RRT SE3 order)."""
    seed_all(seed)
    dev = torch.device(device)
    t_setup0 = time.time()
    cd = CollisionDetector(params.sdf_N, params.sdf_H, dev, params.threshold, params.eta,
                           abs(params.threshold))
    cd.set_robot(robot_mesh_path)
    cd.generate_robot_sampling(params.sampling)
    q1s, qs, qe = SE3(*q1), SE3(*q2_start), SE3(*q2_end)
    cd.set_obstacles(obstacle_sdf_path, q1s)
    start_valid = bool(cd.is_point_valid(qs, params.threshold))
    start_min_sdf = float(cd.distance_between_objects(qs))
    t_setup = time.time() - t_setup0

    rrt = RRT(cd, q1s, qs, qe)
    it = 0
    solved = False
    t0 = time.time()
    while True:
        it += 1
        solved = bool(rrt.step(params.eta, params.threshold, params.steps))
        el = time.time() - t0
        if solved or el > timeout_s or (max_iterations is not None and it >= max_iterations):
            break
    wall = time.time() - t0
    path = rrt.get_path() if solved else None
    return {
        "outcome": "success" if solved else "unsolved",
        "iterations": it,
        "time_s": wall,
        "setup_s": t_setup,
        "start_valid": start_valid,
        "start_min_sdf": start_min_sdf,
        "tree_nodes": rrt.tree.number_of_nodes(),
        "path": [p.to_numpy().tolist() for p in path] if path else None,
        "params": asdict(params),
        "device": device,
        "seed": seed,
        "timeout_s": timeout_s,
        "max_iterations": max_iterations,
    }
