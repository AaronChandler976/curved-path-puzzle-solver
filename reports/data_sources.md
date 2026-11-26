# Data sources (S2, 2026-11-21)

Download logs: `experiments/2026-11-21_downloads/stdout.log` (ATA), `experiments/2026-11-21_downloads_asap/stdout.log` (ASAP).
Checksums: sha256, computed locally on the downloaded files (ATA list also in `data/raw/ata_zips.sha256`).

| dataset | source URL | size (bytes) | sha256 | on disk |
|---|---|---|---|---|
| ATA multi-part | https://people.csail.mit.edu/yunsheng/Assemble-Them-All/dataset_2403/multi_assembly.zip | 778,421,804 | c41a2ed9d1d4f4bd91dd4ed3a6722e917bf296acfce1a0953b2a33030590cfa3 | `data/raw/multi_assembly/multi_assembly/` (4196 assemblies, 2.5 GB extracted) |
| ATA two-part rotational | https://people.csail.mit.edu/yunsheng/Assemble-Them-All/dataset_2403/joint_assembly_rotation.zip | 5,350,863 | cea592bc010801de9cbbeabe53125ea91478bd4a1f9c8db2a1476fdd28a7af3b | `data/raw/joint_assembly_rotation/` |
| ATA two-part main (optional) | https://people.csail.mit.edu/yunsheng/Assemble-Them-All/dataset_2403/joint_assembly.zip | 221,126,914 | f8ab553d318ef1baa67a688972ec1f8ed1f7fc8b04b4cc86d8505fe903de760a | `data/raw/joint_assembly/` |
| ASAP training set (1906 assemblies) | https://people.csail.mit.edu/yunsheng/ASAP/dataset_2404/training_assembly.zip | 618,781,705 | 0f21fa9642877c69078b5489bb6a86db3a5e786024cc2fdd19dfb25384a64968 | `data/raw/asap_zips/` (zip only, not extracted tonight) |
| ASAP test set (240 assemblies) | https://people.csail.mit.edu/yunsheng/ASAP/dataset_2404/test_assembly.zip | 129,192,316 | c89ea240b1962e3230b00487bf23f3fcbb8b5cd7b6ce1a6816e043a31cac09c2 | `data/raw/asap_zips/` (zip only) |
| ASAP pretrained GNN checkpoint | https://people.csail.mit.edu/yunsheng/ASAP/pretrained_model.pt (URL from `external/ASAP/plan_sequence/generator/learning.py:46`) | 20,516,715 | 430a51253c25170e8f845ee21834a1e33714225fdf5f87b7cb687e4fe260d99a | `data/raw/asap_ckpt/pretrained_model.pt` |

## Which ASAP repo
Chosen: **github.com/yunshengtian/ASAP** (commit 3727e716, 2025-02-13), cloned to `external/ASAP`.
Its README says it holds "the official code and dataset of ASAP (ICRA 2024)", links to asap.csail.mit.edu,
and its owner is the first author (Yunsheng Tian), who also maintains Assemble-Them-All. The dataset and checkpoint URLs
in it point at the authors' MIT CSAIL pages. github.com/makolon/ASAP calls itself official, but it is a third-party
account. Using the author's repo avoids depending on a fork that may diverge. See `reports/DECISIONS_FOR_AARON.md`.

## Licenses
- **Assemble-Them-All code:** MIT (Copyright 2022 Yunsheng Tian), `external/Assemble-Them-All/LICENSE`.
- **ASAP code:** MIT (Copyright 2024 Yunsheng Tian), `external/ASAP/LICENSE`.
- **CMG-RRT code:** MIT, `external/cmg-rrt/LICENSE`.
- **Datasets:** the ATA README (line 57) says that most of the dataset is modified from the Fusion 360 Gallery Dataset
  and that the **Fusion 360 Gallery Dataset License** governs legal use:
  https://github.com/AutodeskAILab/Fusion360GalleryDataset/blob/master/LICENSE.md (read 2026-11-21, "Updated 11/2021").
  It is a custom license, not open source. Key terms:
  - Item 1: "You may access, use, reproduce and modify the Dataset, in each case, only for non-commercial research purposes."
  - Item 2: no redistribution of the Dataset in its entirety (pointing people to the repo is fine).
  - Item 3: a portion or modification may be shared only if it is marked as such, attributed, and passed on under
    the same non-commercial terms.
  - Item 4: no attempts to re-identify model creators. Item 5: attribution to "Fusion 360 Gallery Dataset" is expected
    if the dataset contributed substantially to the research.
  - **Consequence for us:** course research use is fine. Do **not** commit or publish meshes, and cite the dataset in the final report.
    The ASAP dataset has no separate license file that we found. We treat it under the same Fusion 360 terms
    because it is derived from the same source (an assumption; see DECISIONS).

## Inspection (scripts/inspect_dataset.py)
Log: `experiments/2026-11-21_inspect_multi/stdout.log`, summary `experiments/2026-11-21_inspect_multi/summary.json`.
- ATA multi-part: **4196 assemblies, all meshes load with trimesh (0 failures)**. 4192/4196 have every part watertight.
- Part-count histogram (head): 3 parts: 755, 4: 488, 5: 466, 6: 306, 7: 246, 8: 185, ... (full histogram in summary.json).
- Coordinates: each assembly is stored in assembled pose, normalized so that max |coord| = 5 (checked on 00000 and 00003).

Gate S2: **PASS**. The multi-part set is on disk and 4196 ≥ 100 assemblies load (summary.json above).
