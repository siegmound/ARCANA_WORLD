from pathlib import Path
import argparse, hashlib, json

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');a=ap.parse_args();root=Path(a.root).resolve();p=root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_13.json';m=json.loads(p.read_text(encoding='utf-8'));checks=[]
 for n,x in (m.get('files') or {}).items():
  q=root/n;checks.append((f'present::{n}',q.is_file()));checks.append((f'hash::{n}',q.is_file() and q.stat().st_size==int(x['bytes']) and sha(q)==x['sha256']))
 failed=[n for n,v in checks if not v];out={'stage':'v0.6D1-R5.13','status':'PASS_R513_SOURCE_MANIFEST' if not failed else 'BLOCKED_R513_SOURCE_MANIFEST','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'failed':failed};print(json.dumps(out,indent=2,sort_keys=True));return 0 if not failed else 2
if __name__=='__main__':raise SystemExit(main())
