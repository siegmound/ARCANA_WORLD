from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
manifest=root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_30.json'
d=json.loads(manifest.read_text(encoding='utf-8-sig')) if manifest.exists() else {'entries':[]}
failed=[]
for rec in d.get('entries') or []:
    p=root/rec['path']
    if not p.exists(): failed.append({'path':rec['path'],'reason':'MISSING'}); continue
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    if h!=rec.get('sha256'): failed.append({'path':rec['path'],'reason':'SHA256_MISMATCH','expected':rec.get('sha256'),'observed':h})
out={'stage':'v0.6D1-R4.30','status':'PASS_R430_SOURCE_MANIFEST' if not failed else 'BLOCKED_R430_SOURCE_MANIFEST','checks_passed':len((d.get('entries') or []))-len(failed),'checks_total':len(d.get('entries') or []),'failed':failed}
print(json.dumps(out,indent=2)); raise SystemExit(0 if not failed else 3)
