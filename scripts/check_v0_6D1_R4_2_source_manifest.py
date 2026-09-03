from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parents[1]
m=json.loads((root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_2.json').read_text())
failed=[]
for row in m['files']:
 p=root/row['path']
 if not p.exists(): failed.append({'path':row['path'],'error':'MISSING'}); continue
 h=hashlib.sha256(p.read_bytes()).hexdigest()
 if h!=row['sha256']: failed.append({'path':row['path'],'error':'SHA256_MISMATCH','expected':row['sha256'],'observed':h})
out={'status':'PASS_R42_SOURCE_MANIFEST' if not failed else 'FAIL_R42_SOURCE_MANIFEST','checks_passed':len(m['files'])-len(failed),'checks_total':len(m['files']),'failed':failed}
print(json.dumps(out,indent=2)); raise SystemExit(0 if not failed else 2)
