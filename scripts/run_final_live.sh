#!/usr/bin/env bash
# Campaign Phase 3: live full disassembly on the v2 TEST set (PREREG §6 + addendum B.4 priority order).
# Usage: scripts/run_final_live.sh <outdir>. Runs P1..P4 in order in one resumable folder (live_abd.py skips finished
# (assembly, method) pairs and re-runs confounded ones). Model specs are generated from configs/final_frozen.yaml.
set -eu
OUT=$1
mkdir -p "$OUT"
git rev-parse HEAD > "$OUT/git_hash.txt"
PY="env -u PYTHONPATH conda run --no-capture-output -n disasm python"
$PY - "$OUT" <<'PYEOF'
import json, sys, yaml
out = sys.argv[1]
c = yaml.safe_load(open("configs/final_frozen.yaml"))
sp = json.load(open(c["data"]["split"]))
json.dump(sp["test"], open(f"{out}/test_ids.json", "w"))
spec, P = {}, {1: ["random", "outside_in", "fewest_contacts", "asap_zs"], 2: [], 3: [], 4: ["fewest_contacts@b3"]}
for grp in ("registered", "exploratory"):
    for v, cks in c[grp].items():
        best = c["val_best_seed"][v]
        for i, ck in enumerate(cks):
            seed = 100 + i
            assert f"seed{seed}/" in ck["ckpt"], ck
            name = f"{v}#s{seed}"
            spec[name] = {"variant": v, "ckpt": ck["ckpt"]}
            if grp == "registered":
                P[1 if seed == best else 2].append(name)
            elif v in c["live"]["exploratory_live"]:
                P[3].insert(0, name) if seed == best else P[3].append(name)    # val-best seed first
        if v == "gnn_survival":
            P[4].append(f"gnn_survival#s{best}@b3")
json.dump(spec, open(f"{out}/model_spec.json", "w"), indent=1)
for k, ms in P.items():
    open(f"{out}/methods_P{k}.txt", "w").write(",".join(ms))
print({k: len(v) for k, v in P.items()})
PYEOF
for K in 1 2 3 4; do
  CMD="$PY scripts/live_abd.py --assemblies $OUT/test_ids.json --outdir $OUT --methods $(cat $OUT/methods_P$K.txt) --model-spec $OUT/model_spec.json --redmax experiments/2026-11-24_run05_redmax/asap_graphs.jsonl --oracle v2 --seed-prefix run05-live --workers 10 --T 30 --idle-wait 300 --max-reruns 2 --allowance-file experiments/2026-11-23_run04_t6_pool/allowance.json"
  echo "P$K: $CMD" >> "$OUT/cmd.txt"
  $CMD > "$OUT/stdout_P$K.log" 2>&1
done
echo "FINAL LIVE DONE $(date)" >> "$OUT/cmd.txt"
