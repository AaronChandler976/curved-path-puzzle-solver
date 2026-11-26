#!/bin/bash
# R2 driver: (1) train upstream-default SDFs (setup; 4 concurrent, training time confounded),
# (2) planner runs strictly ONE AT A TIME: elk (60 min cap), then the others (20 min cap each),
# never starting a run that cannot finish before STOP_AT (R2 timebox).
set -u
cd "$(dirname "$0")/.."
R=experiments/2026-11-22_cmgrrt_repro_clean
STOP_AT=${STOP_AT:-"2026-11-22T23:20:00"}
PY="env -u PYTHONPATH conda run --no-capture-output -n disasm python"
OTHERS="general/11356 puzzle/key_light_1 general/06397 general/07631 general/08862 general/09301 general/11019 general/11780 general/16505 puzzle/mobius_light puzzle/abc_light puzzle/alpha puzzle/az puzzle/aj puzzle/doublealpha puzzle/duet-g1"
while pgrep -f "repro_cmgrrt.py --example puzzle/elk --seed 0 --cap-min 60 --train-only" >/dev/null; do sleep 10; done
echo "[$(date +%T)] phase 1: SDF training for 16 examples (4 concurrent)"
for e in $OTHERS; do echo $e; done | xargs -P 4 -I{} sh -c "OMP_NUM_THREADS=3 $PY scripts/repro_cmgrrt.py --example {} --seed 0 --cap-min 0 --train-only --run-dir $R/train > /dev/null 2>&1"
echo "[$(date +%T)] phase 2: planner runs, one at a time"
run() {  # example cap_min
  local now_s=$(date +%s) stop_s=$(date -d "$STOP_AT" +%s)
  if [ $((now_s + $2*60 + 120)) -gt $stop_s ]; then echo "[$(date +%T)] SKIP $1 (timebox)"; echo "{\"example\": \"$1\", \"skipped\": \"timebox\"}" >> $R/skipped.jsonl; return; fi
  echo "[$(date +%T)] RUN $1 cap $2"
  echo "$PY scripts/repro_cmgrrt.py --example $1 --seed 0 --cap-min $2 --run-dir $R" >> $R/cmd.txt
  $PY scripts/repro_cmgrrt.py --example $1 --seed 0 --cap-min $2 --run-dir $R > /dev/null 2>&1
  tail -1 $R/results.jsonl
}
run puzzle/elk 60
for e in $OTHERS; do run $e 20; done
echo "[$(date +%T)] R2 DRIVER DONE"
