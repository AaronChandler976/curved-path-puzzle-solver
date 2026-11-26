#!/bin/bash
# R3 validation, every step alone and sequential (timing hygiene)
cd "$(dirname "$0")/../.."
E=experiments/2026-11-22_exact_sdf_validation
PY="env -u PYTHONPATH conda run --no-capture-output -n disasm python"
V="$PY scripts/exact_sdf_validation.py"
echo "[$(date +%T)] start_valid"; $V start_valid --outdir $E --n 50 --eps 0.005 > /dev/null 2>&1
echo "[$(date +%T)] poses"; $V poses --outdir $E --examples general/11356 puzzle/key_light_1 general/16505 > /dev/null 2>&1
echo "[$(date +%T)] s3"; $V s3 --outdir $E --workers 5 > /dev/null 2>&1
echo "[$(date +%T)] eps"; $V eps --outdir $E --n 30 --eps 0.0025 0.005 0.01 --T 30 > /dev/null 2>&1
for e in general/16505 puzzle/mobius_light puzzle/alpha general/11356; do
  echo "[$(date +%T)] bundled exact $e"; $PY scripts/repro_cmgrrt.py --example $e --seed 0 --cap-min 20 --detector exact --run-dir $E/bundled > /dev/null 2>&1; tail -1 $E/bundled/results.jsonl
done
echo "[$(date +%T)] R3 DONE"
