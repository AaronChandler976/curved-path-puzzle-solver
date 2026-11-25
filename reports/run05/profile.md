# Run 05: ranker latency and memory (val states)

Script `scripts/profile_rankers.py`; raw `experiments/2026-11-25_run05_profile/profile.json`; load at start/end in `experiments/2026-11-25_run05_profile/load_info.txt`. 200 val states (seeded sample); median over repeats. Busy samples during the run: 27/62 (busy_frac 0.435; `idle_samples.jsonl`). **Outside load never exceeded 0.36 cores** (threshold 0.5) in any sample. Every busy flag comes from the load-average criterion while our own 24-thread benchmark ran: the sampler's own-load estimate lags multithreaded bursts (run 04 DECISIONS #22), and the first sample is busy by design. So these timings are not confounded by outside load.

**What is timed:** the model forward pass only, on inputs already collated into tensors (median over repeats; batch 1 = one state per forward, 100 repeats; batched = all 200 sampled states in one forward, 30 repeats, divided by the state count). Not included: building the state's contact-graph features (timed separately: **2.41 ms** per state, median of 50, from the per-assembly contact graph that is computed once per assembly and cached), the per-assembly contact graph itself, PointNet's point-cloud sampling, and ASAP's point-cloud sampling and redmax contact graph (both per assembly, once).

| model | params | CPU 1 thread, batch 1 (ms/state) | CPU 24 threads, batch 1 | CPU 24 threads, batched (ms/state) | GPU batch 1 (ms/state) | GPU batched (ms/state) | GPU peak mem, batched (MB) | planner s saved / state vs fewest_contacts (val, descriptive) |
|---|---|---|---|---|---|---|---|---|
| mlp_bce | 22,337 | 0.04 | 0.08 | 0.002 | 0.08 | 0.0004 | 10 | +0.07 |
| mlp_survival | 22,792 | 0.04 | 0.08 | 0.002 | 0.08 | 0.0004 | 10 | +0.25 |
| gnn_bce | 23,105 | 0.08 | 0.20 | 0.003 | 0.18 | 0.0009 | 11 | +0.37 |
| gnn_survival | 32,392 | 0.12 | 0.28 | 0.005 | 0.24 | 0.0013 | 11 | +0.44 |
| gnn_survival_tail | 88,072 | 0.10 | 0.21 | 0.005 | 0.17 | 0.0010 | 13 | +0.63 |
| pn_gnn_survival | 61,192 | 1.89 | 0.81 | 1.157 | 0.23 | 0.0267 | 904 | +0.59 |
| asap_retrained | 1,703,681 | 7.07 | 2.88 | 5.601 | 0.72 | 0.1894 | 3849 | -0.86 |
| asap_zs | 1,703,681 | 7.04 | 2.28 | 5.563 | 0.71 | 0.1894 | 3849 | -1.26 |
