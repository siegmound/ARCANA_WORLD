from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def main():
 p=ROOT/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_25.json';m=json.loads(p.read_text());bad=[]
 for n,meta in m['files'].items():
  f=ROOT/n
  if not f.is_file() or f.stat().st_size!=meta['bytes'] or sha(f)!=meta['sha256']:bad.append(n)
 out={'status':'PASS_R325_SOURCE_MANIFEST' if not bad else 'FAIL_R325_SOURCE_MANIFEST','checks_passed':len(m['files'])-len(bad),'checks_total':len(m['files']),'failed':bad};print(json.dumps(out,indent=2));return 0 if not bad else 1
if __name__=='__main__':raise SystemExit(main())
