from __future__ import annotations
from pathlib import Path
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_6.json'
d=json.loads(p.read_text(encoding='utf-8'))
failed=[]
for row in d.get('files',[]):
    f=ROOT/row['path']
    if not f.exists(): failed.append({'path':row['path'],'reason':'MISSING'}); continue
    h=hashlib.sha256(f.read_bytes()).hexdigest()
    if h!=row['sha256']: failed.append({'path':row['path'],'reason':'SHA256_MISMATCH','expected':row['sha256'],'observed':h})
out={'stage':'v0.6D1-R4.6','status':'PASS_R46_SOURCE_MANIFEST' if not failed else 'BLOCKED_R46_SOURCE_MANIFEST','checks_passed':len(d.get('files',[]))-len(failed),'checks_total':len(d.get('files',[])),'failed':failed}
print(json.dumps(out,indent=2)); raise SystemExit(0 if not failed else 3)
