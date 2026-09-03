from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[1]
mp=root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_5.json'
m=json.loads(mp.read_text(encoding='utf-8-sig'))
failed=[]
for row in m['files']:
    p=root/row['path']
    if not p.exists():
        failed.append({'path':row['path'],'error':'MISSING'}); continue
    obs=hashlib.sha256(p.read_bytes()).hexdigest()
    if obs!=row['sha256']:
        failed.append({'path':row['path'],'error':'SHA256_MISMATCH','expected':row['sha256'],'observed':obs})
out={'stage':'v0.6D1-R4.5','status':'PASS_R45_SOURCE_MANIFEST' if not failed else 'FAIL_R45_SOURCE_MANIFEST','checks_passed':len(m['files'])-len(failed),'checks_total':len(m['files']),'failed':failed}
print(json.dumps(out,indent=2))
raise SystemExit(0 if not failed else 2)
