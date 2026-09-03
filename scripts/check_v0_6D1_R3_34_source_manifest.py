from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parents[1]; m=json.loads((root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_34.json').read_text())
failed=[]
for n,meta in m['files'].items():
 p=root/n
 if not p.is_file(): failed.append([n,'missing']); continue
 h=hashlib.sha256(p.read_bytes()).hexdigest()
 if p.stat().st_size!=meta['bytes'] or h!=meta['sha256']: failed.append([n,'mismatch'])
print(json.dumps({'status':'PASS_R334_SOURCE_MANIFEST' if not failed else 'FAIL_R334_SOURCE_MANIFEST','checks_passed':len(m['files'])-len(failed),'checks_total':len(m['files']),'failed':failed},indent=2));sys.exit(1 if failed else 0)
