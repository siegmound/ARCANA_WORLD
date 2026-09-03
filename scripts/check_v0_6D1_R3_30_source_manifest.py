from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parents[1];p=root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_30.json';m=json.loads(p.read_text());bad=[]
for n,meta in m['files'].items():
 f=root/n
 if not f.is_file():bad.append([n,'missing']);continue
 h=hashlib.sha256(f.read_bytes()).hexdigest()
 if f.stat().st_size!=meta['bytes'] or h!=meta['sha256']:bad.append([n,'mismatch'])
print(json.dumps({'status':'PASS_R330_SOURCE_MANIFEST' if not bad else 'FAIL_R330_SOURCE_MANIFEST','checks_passed':len(m['files'])-len(bad),'checks_total':len(m['files']),'failed':bad},indent=2));sys.exit(1 if bad else 0)
