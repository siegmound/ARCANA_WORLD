from pathlib import Path
import json,hashlib,sys
root=Path(__file__).resolve().parents[1];m=json.loads((root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_33.json').read_text());checks=[]
def sha(p):
 h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
for n,meta in m['files'].items():
 p=root/n;checks.append(p.is_file() and p.stat().st_size==meta['bytes'] and sha(p)==meta['sha256'])
res={'status':'PASS_R333_SOURCE_MANIFEST' if all(checks) else 'FAIL_R333_SOURCE_MANIFEST','checks_passed':sum(checks),'checks_total':len(checks),'failed':[n for (n,_),ok in zip(m['files'].items(),checks) if not ok]};print(json.dumps(res,indent=2));sys.exit(0 if all(checks) else 1)
