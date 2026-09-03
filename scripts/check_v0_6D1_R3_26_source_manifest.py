from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def main():
 p=ROOT/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_26.json';m=json.loads(p.read_text());checks=[]
 for n,x in m['files'].items():
  f=ROOT/n;checks.append(f.is_file() and f.stat().st_size==x['bytes'] and sha(f)==x['sha256'])
 ok=all(checks);print(json.dumps({'status':'PASS_R326_SOURCE_MANIFEST' if ok else 'FAIL_R326_SOURCE_MANIFEST','checks_passed':sum(checks),'checks_total':len(checks),'failed':[n for (n,_),v in zip(m['files'].items(),checks) if not v]},indent=2));return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
