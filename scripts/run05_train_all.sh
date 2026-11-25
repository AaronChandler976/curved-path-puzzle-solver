#!/usr/bin/env bash
# Run 05 (campaign Phase 1): train every PREREG variant (grid seeds 0,1,2; final seeds 100-104), val only.
# Usage: scripts/run05_train_all.sh <outdir> <redmax_jsonl>. Each variant runs as its own background process (GPU shared).
# Resumable: train_v2.py / train_asap_v2.py skip runs whose result.json exists.
set -u
OUT=$1; RM=$2
mkdir -p "$OUT"
git rev-parse HEAD > "$OUT/git_hash.txt"
: > "$OUT/pids.txt"
for V in mlp_bce mlp_survival gnn_bce gnn_survival gnn_survival_tail pn_gnn_survival; do
  CMD="env -u PYTHONPATH OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run --no-capture-output -n disasm python scripts/train_v2.py --variant $V --outdir $OUT"
  echo "$CMD" >> "$OUT/cmd.txt"
  setsid nohup bash -c "$CMD" > "$OUT/stdout_$V.log" 2>&1 &
  echo "$! $V" >> "$OUT/pids.txt"
done
CMD="env -u PYTHONPATH OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 conda run --no-capture-output -n disasm python scripts/train_asap_v2.py --outdir $OUT --redmax $RM --procs 4"
echo "$CMD" >> "$OUT/cmd.txt"
setsid nohup bash -c "$CMD" > "$OUT/stdout_asap_retrained.log" 2>&1 &
echo "$! asap_retrained" >> "$OUT/pids.txt"
