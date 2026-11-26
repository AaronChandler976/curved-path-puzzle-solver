#!/bin/bash
# Run 04 T5: exact vs learned SDF on bundled puzzles 16505 and alpha, 3 seeds each, authors' test_list.json settings
# (5,000 iterations), ONE run at a time, idle guard: 300 s non-busy before the first run (one timed batch), 60 s
# before each later run; busy samples logged throughout each run (confounded if busy_frac > 0.05).
# Usage: scripts/run_t5.sh <run_dir> [cap_min]
E=$1; CAP=${2:-90}
cd "$(dirname "$0")/.."
mkdir -p $E
first=1
for seed in 0 1 2; do
  for ex in general/16505 puzzle/alpha; do
    for det in learned exact; do
      tag="${ex//\//_}_s${seed}"; [ $det = exact ] && tag="${tag}_exact"
      if [ -f $E/results.jsonl ] && grep -q "\"example\": \"$ex\", \"seed\": $seed," $E/results.jsonl && \
         grep "\"example\": \"$ex\", \"seed\": $seed," $E/results.jsonl | grep -q "\"detector\": \"$det\""; then
        echo "skip $tag (done)"; continue; fi
      W=60; [ $first = 1 ] && W=300; first=0
      echo "$(date -Iseconds) start $tag"
      env -u PYTHONPATH conda run --no-capture-output -n disasm python scripts/repro_cmgrrt.py --example $ex --seed $seed \
        --cap-min $CAP --detector $det --run-dir $E --idle-wait $W
      echo "$(date -Iseconds) end $tag"
    done
  done
done
echo "T5 DONE"
