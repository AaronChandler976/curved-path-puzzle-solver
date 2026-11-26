# S6 PIPELINE TEST (not a result)

Labels: `experiments/2026-11-23_s6_pipeline_test_v1/labels_snapshot.jsonl`; 4685 states; log `experiments/2026-11-23_s6_pipeline_test_v1/train_log.txt`. This only checks that the training loop runs and the loss goes down. It is **not** a model comparison.

## PIPELINE TEST: overfit 20 states (loss should go near zero)

| model/head | first loss | last loss |
|---|---|---|
| mlp_bce | 0.6565 | 0.0000 |
| mlp_survival | 1.2071 | 0.0016 |
| gnn_bce | 0.9440 | 0.0000 |
| gnn_survival | 1.3113 | 0.0253 |

## PIPELINE TEST: one split by assembly (loss curves only)

| model/head | train loss first -> last | val loss first -> last |
|---|---|---|
| mlp_bce | 0.3503 -> 0.0401 | 0.3044 -> 1.1404 |
| mlp_survival | 0.9035 -> 0.3283 | 0.7095 -> 1.3253 |
| gnn_bce | 0.3538 -> 0.0090 | 0.2974 -> 1.0202 |
| gnn_survival | 0.8740 -> 0.0895 | 0.7265 -> 2.7192 |
