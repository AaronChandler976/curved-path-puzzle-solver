# Run 03 R3: training (validation numbers only)

Val metric = total replay planner cost (s) over the 697 val states with >= 1 success; lower is better. Val references (same metric): random 3667, outside-in 2515, fewest contacts 2215, hindsight-optimal 386 (`experiments/2026-11-23_run03_train/val_baselines.json`). The val metric was used for selection, so model val numbers are optimistically biased. Test results are in `results_replay.md`.

Fixed for every variant: AdamW, weight decay 1e-4, dropout 0.1, grad-clip 1.0, batch 32 states, ≤ 150 epochs, K = 8 survival bins. Grid: hidden {64, 128} × lr {1e-3, 3e-4} × layers {2, 3}; the MLP uses the same residual block count as the GNN's message-passing layers.

## Protocol v1 (development iteration, NOT evaluated on test): grid seed 0, raw per-epoch val metric, patience 20

Folder `experiments/2026-11-23_run03_train`; per-run `metrics.csv` + `curve.png`; per-variant `selection.json`, `train_log.txt`.

| variant | chosen config (hidden, lr, layers) | chosen config val metric (s) | final seeds: best val metric (s) | mean ± std | best epochs |
|---|---|---|---|---|---|
| mlp_bce | 64, 0.001, 2 | 1984 | 1984, 2176, 2007, 2074, 2229 | 2094 ± 106 | 41, 0, 11, 11, 9 |
| mlp_survival | 64, 0.001, 2 | 1919 | 1919, 2081, 1704, 1896, 2078 | 1936 ± 156 | 24, 1, 9, 1, 1 |
| gnn_bce | 64, 0.0003, 3 | 2018 | 1903, 2114, 2190, 2344, 1937 | 2098 ± 182 | 41, 0, 10, 6, 8 |
| gnn_survival | 128, 0.0003, 2 | 1862 | 1997, 1948, 2021, 1758, 1981 | 1941 ± 106 | 15, 23, 0, 27, 0 |

Grid (val metric per config; v2 = mean of 3 seeds):

| variant | h64 lr0.001 L2 | h64 lr0.001 L3 | h64 lr0.0003 L2 | h64 lr0.0003 L3 | h128 lr0.001 L2 | h128 lr0.001 L3 | h128 lr0.0003 L2 | h128 lr0.0003 L3 |
|---|---|---|---|---|---|---|---|---|
| mlp_bce | 1984 | 2178 | 2238 | 2211 | 2224 | 2074 | 2124 | 2072 |
| mlp_survival | 1919 | 2022 | 2042 | 2091 | 2128 | 2081 | 1926 | 1950 |
| gnn_bce | 2222 | 2218 | 2248 | 2018 | 2153 | 2025 | 2232 | 2227 |
| gnn_survival | 1904 | 2021 | 1880 | 2185 | 1971 | 1867 | 1862 | 1995 |

Why v2 replaced v1: the per-epoch val metric's noise SD is 98 s (`experiments/2026-11-23_run03_train/val_noise.txt`), about the size of the gaps between configs, and v1 picked epoch 0–1 checkpoints for 7/20 seeds. See DECISIONS #8.

## Protocol v2 (frozen, evaluated on test): grid seeds 0-2 averaged, 5-epoch trailing-mean val metric, min 10 epochs, patience 25, final seeds 100-104

Folder `experiments/2026-11-23_run03_train_v2`; per-run `metrics.csv` + `curve.png`; per-variant `selection.json`, `train_log.txt`.

| variant | chosen config (hidden, lr, layers) | chosen config val metric (s) | final seeds: best val metric (s) | mean ± std | best epochs |
|---|---|---|---|---|---|
| mlp_bce | 64, 0.0003, 2 | 2170 | 2085, 2309, 2415, 2229, 2291 | 2266 ± 121 | 5, 7, 5, 5, 19 |
| mlp_survival | 128, 0.0003, 3 | 1962 | 2069, 1913, 2162, 2057, 2053 | 2051 ± 89 | 21, 6, 4, 9, 4 |
| gnn_bce | 128, 0.001, 3 | 2128 | 2206, 2220, 2147, 2420, 2213 | 2241 ± 104 | 15, 4, 14, 10, 19 |
| gnn_survival | 128, 0.001, 3 | 1994 | 2255, 2077, 2339, 2122, 2175 | 2194 ± 105 | 7, 16, 8, 17, 12 |

Grid (val metric per config; v2 = mean of 3 seeds):

| variant | h64 lr0.001 L2 | h64 lr0.001 L3 | h64 lr0.0003 L2 | h64 lr0.0003 L3 | h128 lr0.001 L2 | h128 lr0.001 L3 | h128 lr0.0003 L2 | h128 lr0.0003 L3 |
|---|---|---|---|---|---|---|---|---|
| mlp_bce | 2182 | 2239 | 2170 | 2263 | 2290 | 2208 | 2261 | 2208 |
| mlp_survival | 2001 | 2080 | 2042 | 2079 | 2149 | 2054 | 1986 | 1962 |
| gnn_bce | 2288 | 2339 | 2239 | 2253 | 2160 | 2128 | 2266 | 2251 |
| gnn_survival | 2174 | 2080 | 2100 | 2137 | 2060 | 1994 | 2063 | 2005 |

GNN-Surv checkpoint for R6 live evaluation (lowest val metric among the 5 v2 seeds): seed 101.
