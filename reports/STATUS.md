STATE: RUNNING
DEADLINE: 2026-11-22T07:00:00-08:00
CURRENT STAGE: S3 adapter gate (oracle_check_v2 running); S1 sweep still running
BACKGROUND JOBS:
15635 smoke sweep (4 parallel, 600 s cap) experiments/2026-11-22_smoke_sweep/stdout.log
(pgrep -f scan_contacts) contact/penetration scan 3-8 parts experiments/2026-11-22_contact_scan/stdout.log
(pgrep -f smoke_hifi) hi-fi SDF diagnostic general/06397 cuda experiments/2026-11-22_smoke_hifi_sdf/stdout.log
(pgrep -f oracle_check) oracle check v2 experiments/2026-11-22_oracle_check_v2/stdout.log
DONE SO FAR:
- S0 PASS: reports/environment.md
- S2 PASS: reports/data_sources.md (4196 assemblies load)
- S3 adapter written: src/disasm/oracle/cmgrrt.py; tests in tests/; decisions in reports/DECISIONS_FOR_AARON.md
- oracle_check v1 (killed by me at ~4 min, resumable): 00008 all 5 done parts unsolved because start pose in collision (mesh interpenetration) -> filter added
NEXT ACTION: when oracle_check_v2 done -> check S3 gate, choose T, launch scripts/label_abd.py (filter by contact scan max_pen<=0.002); write reports/smoke_test.md when sweep done
