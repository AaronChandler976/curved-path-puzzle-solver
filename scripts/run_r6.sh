#!/bin/bash
# R6 (run 03): wait until the machine is idle (load avg < 2 and GPU util < 10% for 5 consecutive minutes, sampled every 15 s;
# re-checked every 10 min for up to 2 h), then run the live evaluation. If it never goes idle, run anyway and mark confounded.
E=$1; CKPT=$2
cd "$(dirname "$0")/.."
log=$E/idle_wait.log
idle=0
for attempt in $(seq 1 12); do
  ok=1
  for i in $(seq 1 20); do
    l=$(cut -d' ' -f1 /proc/loadavg); g=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -1)
    echo "$(date -Iseconds) attempt $attempt sample $i load1=$l gpu=$g" >> $log
    if awk "BEGIN{exit !($l >= 2 || $g >= 10)}"; then ok=0; break; fi
    sleep 15
  done
  if [ $ok = 1 ]; then idle=1; echo "$(date -Iseconds) IDLE for 5 min -> start" >> $log; break; fi
  echo "$(date -Iseconds) not idle; next check in 10 min" >> $log
  sleep 600
done
[ $idle = 1 ] || echo "$(date -Iseconds) NEVER IDLE within 2 h -> running anyway; all timings CONFOUNDED" >> $log
echo "idle=$idle" > $E/idle_status.txt
env -u PYTHONPATH conda run --no-capture-output -n disasm python scripts/live_abd.py --assemblies $E/assemblies.json \
  --gnn-ckpt $CKPT --outdir $E --workers 10 --T 30 --eps 0.005 --save-paths
