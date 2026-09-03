from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parents[1];m=json.loads((root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_36.json').read_text());failed=[]
for n,meta in m['files'].items():
 p=root/n
 if not p.is_file():failed.append([n,'missing']);continue
 b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
 if len(b)!=meta['bytes'] or h!=meta['sha256']:failed.append([n,'mismatch'])
res={'status':'PASS_R336_SOURCE_MANIFEST' if not failed else 'FAIL_R336_SOURCE_MANIFEST','checks_passed':len(m['files'])-len(failed),'checks_total':len(m['files']),'failed':failed};print(json.dumps(res,indent=2));sys.exit(1 if failed else 0)
