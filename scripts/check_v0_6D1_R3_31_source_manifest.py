from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parents[1];p=root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_31.json';m=json.loads(p.read_text());checks=[]
for n,meta in m['files'].items():
 q=root/n;ok=q.is_file()
 if ok:
  h=hashlib.sha256(q.read_bytes()).hexdigest();ok=(h==meta['sha256'] and q.stat().st_size==meta['bytes'])
 checks.append((n,ok))
res={'status':'PASS_R331_SOURCE_MANIFEST' if all(x[1] for x in checks) else 'FAIL_R331_SOURCE_MANIFEST','checks_passed':sum(x[1] for x in checks),'checks_total':len(checks),'failed':[x[0] for x in checks if not x[1]]};print(json.dumps(res,indent=2));sys.exit(0 if not res['failed'] else 1)
