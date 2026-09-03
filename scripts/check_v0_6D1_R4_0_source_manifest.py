from pathlib import Path
import json,hashlib,sys
root=Path(__file__).resolve().parents[1]; p=root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_0.json'; m=json.loads(p.read_text())
failed=[]
for rel,spec in m['files'].items():
 q=root/rel
 if not q.exists(): failed.append([rel,'missing']); continue
 b=q.read_bytes(); h=hashlib.sha256(b).hexdigest()
 if len(b)!=spec['bytes'] or h!=spec['sha256']: failed.append([rel,{'bytes':len(b),'sha256':h},spec])
res={'status':'PASS_R40_SOURCE_MANIFEST' if not failed else 'FAIL_R40_SOURCE_MANIFEST','checks_passed':len(m['files'])-len(failed),'checks_total':len(m['files']),'failed':failed};print(json.dumps(res,indent=2));sys.exit(1 if failed else 0)
