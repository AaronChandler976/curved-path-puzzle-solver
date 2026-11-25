# Run 05: ranker latency and memory (val states)

Script `scripts/profile_rankers.py`; raw `experiments/2026-11-24_run05_profile/profile.json`; load at start/end in `experiments/2026-11-24_run05_profile/load_info.txt`. 200 val states (seeded sample); median over repeats. Feature extraction (state graph from the cached contact graph, CPU): **2.50 ms** per state (median, 50 states).

| model | params | CPU 1 thread, batch 1 (ms/state) | CPU 24 threads, batch 1 | CPU batched (ms/state) | GPU batch 1 (ms/state) | GPU batched (ms/state) | GPU peak mem (MB) | planner s saved / state vs fewest_contacts |
|---|---|---|---|---|---|---|---|---|
| mlp_bce | 22,337 | 0.04 | 0.08 | 0.002 | 0.08 | 0.0004 | 10 | +0.07 |
| mlp_survival | 22,792 | 0.04 | 0.08 | 0.002 | 0.08 | 0.0004 | 10 | +0.25 |
| gnn_bce | 23,105 | 0.08 | 0.20 | 0.003 | 0.18 | 0.0009 | 11 | +0.37 |
| gnn_survival | 32,392 | 0.12 | 0.29 | 0.005 | 0.24 | 0.0013 | 11 | +0.44 |
| gnn_survival_tail | 88,072 | 0.09 | 0.21 | 0.005 | 0.17 | 0.0010 | 13 | +0.63 |
| pn_gnn_survival | 61,192 | 1.88 | 0.76 | 1.423 | 0.22 | 0.0267 | 904 | +0.59 |
| asap_retrained | 1,703,681 | 7.06 | 2.36 | 5.685 | 0.72 | 0.1894 | 3849 | -0.90 |
| asap_zs | 1,703,681 | 7.00 | 2.42 | 5.606 | 0.72 | 0.1896 | 3849 | -1.26 |
