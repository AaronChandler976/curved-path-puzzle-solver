# Run 03 dataset (R2)

Built by `scripts/build_dataset_v1.py` (seed 0) from `data/labels/pilot_v1/labels.jsonl` (17116 queries) and `data/labels/pilot_v1/precheck.jsonl`. Graphs: `data/processed/run03/graphs.pt`; split: `data/splits/v1_split.json`.

- states with a complete query set: **4685** over **1328** assemblies; states with >= 1 success: 4606
- duplicate groups: 1310 groups for 1328 assemblies (13 groups with > 1 member, largest 4); assemblies sharing an exact part-mesh key with an earlier one: 6; sharing a near key: 18
- node features (18, model inputs): log volume, area, bbox extents (3), centroid relative to the sub-assembly bbox centre (3) and its norm, # present contact neighbours, total contact fraction, 6-bin contact-normal histogram, n_present. Edge features (5): mean away direction (3), contact fraction, contact area.
- `queried` flag: stored per node as a target mask. It is 1 for every node in v1 (every remaining part was queried), so it is not used as a model input (a constant input carries no information).
- rotation flags (`linear_free`, `needs_rot`, `rot_state`, `rot_assembly`) are evaluation-only fields and are never model inputs.

| split | groups | assemblies | states | states >= 1 success | queries | rot_assembly | rot_state states | 3-4 / 5-6 / 7-8 part asm |
|---|---|---|---|---|---|---|---|---|
| train | 916 | 924 | 3261 | 3207 | 11890 | 145 | 272 | 503 / 278 / 143 |
| val | 197 | 200 | 708 | 697 | 2585 | 33 | 68 | 109 / 61 / 30 |
| test | 197 | 204 | 716 | 702 | 2641 | 33 | 65 | 113 / 61 / 30 |

Group-disjointness is asserted in the builder and in `tests/test_split.py`.
