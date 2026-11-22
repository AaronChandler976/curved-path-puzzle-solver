STATE: RUNNING
DEADLINE: 2026-11-22T07:00:00-08:00
CURRENT STAGE: S1 CMG-RRT smoke test and timing (sweep running) + S2 paperwork + S3 adapter dev
BACKGROUND JOBS:
15635 smoke sweep (17 examples x cpu,cuda, 4 parallel, 600 s cap; parent conda pid 15629) experiments/2026-11-22_smoke_sweep/stdout.log
DONE SO FAR:
- S0 env audit PASS: reports/environment.md, experiments/2026-11-21_env_audit/stdout.log
- S1 elk cpu 500 iters: unsolved in 330 s: experiments/2026-11-21_smoke_elk_cpu500/results.jsonl
- S2 downloads done (ATA multi/rot/joint, ASAP train/test): experiments/2026-11-21_downloads*/stdout.log
- S2 inspect: 4196 multi assemblies all load; experiments/2026-11-21_inspect_multi/summary.json
- NOTE 23:50: STATUS.md was found deleted from working tree (cause unknown); reconstructed from logs.
- Finding: bundled general/* = ATA joint_assembly_rotation x 0.2 (ATA normalized to max|coord|=5); 0_sdf.obj = watertight remesh of 0.obj same scale.
NEXT ACTION: write reports/data_sources.md; write src/disasm/oracle/cmgrrt.py adapter (scale 0.2, q1=q2_start=identity, union-SDF = min over parts); when sweep done write reports/smoke_test.md
