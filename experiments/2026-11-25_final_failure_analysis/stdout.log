# Failure analysis on the test set (after the single evaluation; selects nothing)

Script `scripts/failure_analysis.py`; raw `experiments/2026-11-25_final_failure_analysis/failure_analysis.json`. Main configuration, 2195 scored test states. GNN-Surv = val-best seed 101 (`experiments/2026-11-24_run05_train/gnn_survival/seed101/best.pt`), scored on CPU.

## Cost is concentrated in a few states

| ordering | total (s) | share in costliest 1% of states | 5% | 10% |
|---|---|---|---|---|
| random | 22186 | 0.10 | 0.33 | 0.52 |
| outside_in | 9130 | 0.34 | 0.81 | 0.97 |
| fewest_contacts | 7202 | 0.38 | 0.89 | 0.97 |
| asap_zs | 12387 | 0.25 | 0.67 | 0.95 |
| gnn_survival | 7595 | 0.31 | 0.77 | 0.94 |
| pn_gnn_survival | 7771 | 0.27 | 0.72 | 0.93 |
| gnn_survival_tail | 7415 | 0.26 | 0.70 | 0.91 |
| optimal | 416 | 0.65 | 0.82 | 0.88 |

## GNN-Surv (seed 101) vs fewest contacts, state by state

- GNN-Surv cheaper on 436 states (saving 3240 s), costlier on 368 (losing 3404 s), equal on 1391.
- Causes of the costlier states (state count, extra seconds):
  - slower success (wrong c): 283 states, +251 s
  - timeout first (wrong p): 85 states, +3153 s
- The 20 largest losses: Counter({'fresh-allowance': 12, 'fresh-9to12': 8}) by source; part counts [4, 6, 7, 7, 8, 9, 9, 9, 10, 10, 10, 10, 10, 11, 11, 12, 12, 12, 12, 12].

## The 10 costliest states for GNN-Surv

| assembly | state (present parts) | n | GNN-Surv cost (s) | fewest contacts (s) | first-queried parts: p, c → outcome, cost |
|---|---|---|---|---|---|
| 02925 | 0-1-2-3-4-5-6-7 | 8 | 213.4 | 181.9 | 3: p 0.99, c 0.9 → unsolved 31.5; 1: p 0.97, c 1.4 → unsolved 30.3; 4: p 0.97, c 1.4 → unsolved 34.4 |
| 02512 | 0-1-3-4-5-6-7-8-9-10-11 | 11 | 160.0 | 0.9 | 0: p 1.00, c 0.2 → unsolved 32.3; 1: p 1.00, c 0.3 → unsolved 33.6; 11: p 0.99, c 0.6 → unsolved 30.8 |
| 02512 | 0-1-3-4-5-6-7-9-10-11 | 10 | 154.8 | 218.6 | 1: p 1.00, c 0.2 → unsolved 31.2; 0: p 1.00, c 0.2 → unsolved 31.1; 11: p 0.99, c 0.5 → unsolved 30.8 |
| 03618 | 0-1-2-3-4-5-6-7-8 | 9 | 136.7 | 136.7 | 6: p 0.90, c 3.7 → unsolved 36.5; 4: p 0.86, c 5.3 → unsolved 33.7; 2: p 0.74, c 8.8 → unsolved 32.3 |
| 02002 | 0-1-2-3-4-5-6-7-8-9-10 | 11 | 130.3 | 163.8 | 0: p 1.00, c 0.1 → unsolved 33.9; 6: p 1.00, c 0.2 → unsolved 32.7; 9: p 1.00, c 0.2 → unsolved 31.7 |
| 02869 | 0-1-2-3-4-5-6-7-8-9-10-11 | 12 | 125.5 | 218.8 | 6: p 0.94, c 2.6 → unsolved 31.4; 8: p 0.92, c 3.5 → unsolved 30.7; 5: p 0.92, c 3.8 → unsolved 31.2 |
| 02869 | 0-1-2-3-4-5-6-8-9-10-11 | 11 | 124.3 | 217.5 | 5: p 0.93, c 3.2 → unsolved 30.5; 8: p 0.90, c 4.1 → unsolved 30.7; 4: p 0.90, c 4.5 → unsolved 31.6 |
| 03268 | 0-1-2-3-4-5-6 | 7 | 99.1 | 99.2 | 0: p 0.99, c 0.4 → unsolved 32.8; 1: p 0.95, c 2.2 → unsolved 31.5; 3: p 0.94, c 2.5 → unsolved 34.3 |
| 00675 | 1-2-3-4-5-7-8-9-10-11 | 10 | 98.5 | 0.1 | 8: p 0.95, c 2.4 → unsolved 33.3; 7: p 0.82, c 6.2 → unsolved 30.5; 5: p 0.80, c 6.7 → unsolved 34.7 |
| 03268 | 0-1-2-3-5-6 | 6 | 98.0 | 98.0 | 0: p 0.99, c 0.3 → unsolved 31.7; 3: p 0.92, c 3.4 → unsolved 34.1; 1: p 0.92, c 3.5 → unsolved 30.8 |
