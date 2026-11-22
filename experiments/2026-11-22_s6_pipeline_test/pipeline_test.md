# S6 PIPELINE TEST (not a result)

Labels: `experiments/2026-11-22_s6_pipeline_test/labels_snapshot.jsonl`; 496 states; log `experiments/2026-11-22_s6_pipeline_test/train_log.txt`. This only checks that the training loop runs and the loss goes down. It is **not** a model comparison.

## PIPELINE TEST: overfit 20 states (loss should go near zero)

| model/head | first loss | last loss |
|---|---|---|
| mlp_bce | 0.6714 | 0.0000 |
| mlp_survival | 2.4141 | 0.0001 |
| gnn_bce | 0.7732 | 0.0000 |
| gnn_survival | 2.4208 | 0.0001 |

## PIPELINE TEST: one split by assembly (loss curves only)

| model/head | train loss first -> last | val loss first -> last |
|---|---|---|
| mlp_bce | 0.6025 -> 0.0233 | 0.5514 -> 2.1494 |
| mlp_survival | 1.9385 -> 0.1046 | 1.4185 -> 1.8394 |
| gnn_bce | 0.6238 -> 0.1957 | 0.5464 -> 0.9991 |
| gnn_survival | 1.3901 -> 0.0813 | 0.8470 -> 1.4124 |
