from pathlib import Path
import json, hashlib
root=Path('.')
manifest=root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_15.json'
d=json.loads(manifest.read_text(encoding='utf-8-sig')); failed=[]
for rel in d['required_paths']:
 p=root/rel
 if not p.exists(): failed.append(rel)
out={'stage':'v0.6D1-R4.15','status':'PASS_R415_SOURCE_MANIFEST' if not failed else 'BLOCKED_R415_SOURCE_MANIFEST','checks_passed':len(d['required_paths'])-len(failed),'checks_total':len(d['required_paths']),'failed':failed}
print(json.dumps(out,indent=2)); raise SystemExit(0 if not failed else 1)
