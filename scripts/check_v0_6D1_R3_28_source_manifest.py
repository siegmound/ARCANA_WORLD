from __future__ import annotations
from pathlib import Path
import argparse,hashlib,json

def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);a=ap.parse_args();root=a.root.resolve();p=root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_28.json';m=json.loads(p.read_text(encoding='utf-8'));checks=[]
 for n,meta in m['files'].items():
  fp=root/n;checks.append((n,fp.is_file() and fp.stat().st_size==meta['bytes'] and sha(fp)==meta['sha256']))
 ok=all(x[1] for x in checks);print(json.dumps({'status':'PASS_R328_SOURCE_MANIFEST' if ok else 'FAIL_R328_SOURCE_MANIFEST','checks_passed':sum(x[1] for x in checks),'checks_total':len(checks),'failed':[x[0] for x in checks if not x[1]]},indent=2));return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
