STATE: RUNNING
DEADLINE: 2026-11-22T07:00:00-08:00
CURRENT STAGE: S4 pilot labelling (running) ; S1 sweep still running
BACKGROUND JOBS:
15635 smoke sweep (pgid: see `ps -o pgid= -p 15635`) experiments/2026-11-22_smoke_sweep/stdout.log
793161 label_abd.py (6 workers; conda parent 793145; stop with: kill -TERM <label_abd pid>, workers are its children) experiments/2026-11-22_pilot_labels/stdout.log
DONE SO FAR:
- S0 PASS: reports/environment.md
- S2 PASS: reports/data_sources.md (4196 assemblies load)
- contact/penetration scan: experiments/2026-11-22_contact_scan/results.jsonl (2446 scanned; 1104 kept at max_pen<=0.002)
- S3 PASS: experiments/2026-11-22_oracle_check_v2/results.jsonl: 6 assemblies, 22 queries, 9 successes in 4 assemblies (00017,00026,00072,00085); median success 1.34 s; figure reports/figures/s3_path_00026_part0.png
- hi-fi SDF diagnostic (general/06397 cuda) running/finished: experiments/2026-11-22_smoke_hifi_sdf/
- T=30 s (DECISIONS #10); labelling SDF = narrow-band 4M (DECISIONS #11)
NEXT ACTION: when smoke sweep ends: write reports/smoke_test.md (scripts/smoke_report.py); restart label_abd with --workers 10 (kill -TERM pid, relaunch same cmd.txt with --workers 10; resumable). Run replay (scripts/replay_pilot.py) once >=20 states. Final stage S7 at 06:15.
