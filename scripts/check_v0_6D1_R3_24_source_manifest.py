from pathlib import Path
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_24.json'
def sha(p):
    h=hashlib.sha256();
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()
def main():
    d=json.loads(P.read_text(encoding='utf-8')); ok=0; total=0
    for name,meta in d['files'].items():
        total+=1; p=ROOT/name
        good=p.is_file() and p.stat().st_size==meta['bytes'] and sha(p)==meta['sha256']
        ok+=int(good)
        if not good: print('FAIL',name)
    print(json.dumps({'status':'PASS_R324_SOURCE_MANIFEST' if ok==total else 'FAIL_R324_SOURCE_MANIFEST','checks_passed':ok,'checks_total':total},indent=2))
    return 0 if ok==total else 1
if __name__=='__main__': raise SystemExit(main())
