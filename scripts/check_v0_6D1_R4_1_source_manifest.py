from pathlib import Path
from hashlib import sha256
import json,sys
ROOT=Path(__file__).resolve().parents[1]
MAN=ROOT/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_1.json'

def h(p):
 x=sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): x.update(b)
 return x.hexdigest()
try:
 m=json.loads(MAN.read_text(encoding='utf-8')); failed=[]
 for rel,exp in m['files'].items():
  p=ROOT/rel
  got={'bytes':p.stat().st_size,'sha256':h(p)} if p.exists() else None
  if got!=exp: failed.append([rel,got,exp])
 out={'status':'PASS_R41_SOURCE_MANIFEST' if not failed else 'FAIL_R41_SOURCE_MANIFEST','checks_passed':len(m['files'])-len(failed),'checks_total':len(m['files']),'failed':failed}
 print(json.dumps(out,indent=2)); sys.exit(0 if not failed else 1)
except Exception as e:
 print(json.dumps({'status':'FAIL_R41_SOURCE_MANIFEST','error':repr(e)},indent=2)); sys.exit(1)
