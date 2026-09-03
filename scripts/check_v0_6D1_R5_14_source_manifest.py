from pathlib import Path
import argparse,hashlib,json
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');a=ap.parse_args();root=Path(a.root).resolve();m=json.loads((root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_14.json').read_text());checks=[]
for n,x in (m.get('files') or {}).items():
 p=root/n;checks += [(f'present::{n}',p.is_file()),(f'hash::{n}',p.is_file() and p.stat().st_size==int(x['bytes']) and sha(p)==x['sha256'])]
failed=[n for n,v in checks if not v];o={'stage':'v0.6D1-R5.14','status':'PASS_R514_SOURCE_MANIFEST' if not failed else 'BLOCKED_R514_SOURCE_MANIFEST','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'failed':failed};print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if not failed else 2)
