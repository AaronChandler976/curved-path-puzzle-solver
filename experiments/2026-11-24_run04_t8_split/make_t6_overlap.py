"""Provenance for t6_test_overlap.json (campaign Phase 0 audit fix): test assemblies that appear in run 04 T6
development label folders. Run: env -u PYTHONPATH conda run -n disasm python experiments/2026-11-24_run04_t8_split/make_t6_overlap.py"""
import json, os
sp = json.load(open('data/splits/v2_split.json')); test = set(sp['test'])
out = {}
for d in sorted(os.listdir('data/labels')):
    if d in ('pilot_v2', 'pilot_v1', 'pilot_v0'):
        continue
    ids = set()
    for f in ('summary.jsonl', 'labels.jsonl', 'attempts.jsonl', 'states.jsonl'):
        p = f'data/labels/{d}/{f}'
        if os.path.exists(p):
            for l in open(p):
                try:
                    ids.add(json.loads(l)['assembly_id'])
                except Exception:
                    pass
    out[d] = sorted(ids & test); print(d, len(ids), 'in test', len(out[d]))
allv = sorted(set().union(*out.values())); print('union', len(allv))
json.dump({'per_dir': out, 'union': allv, 'clean_test': sorted(test - set(allv))},
          open('experiments/2026-11-24_run04_t8_split/t6_test_overlap.json', 'w'), indent=0)
