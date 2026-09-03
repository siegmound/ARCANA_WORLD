from __future__ import annotations
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def main():
 p=ROOT/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_29.json';m=json.loads(p.read_text());checks=[]
 for n,meta in m['files'].items():
  q=ROOT/n;checks.append(q.is_file() and q.stat().st_size==meta['bytes'] and sha(q)==meta['sha256'])
 r={'status':'PASS_R329_SOURCE_MANIFEST' if all(checks) else 'FAIL_R329_SOURCE_MANIFEST','checks_passed':sum(checks),'checks_total':len(checks),'failed':[n for (n,_),ok in zip(m['files'].items(),checks) if not ok]};print(json.dumps(r,indent=2));return 0 if all(checks) else 1
if __name__=='__main__':raise SystemExit(main())
