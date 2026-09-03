from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
    return h.hexdigest()

def main()->int:
    root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
    mp=root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_29.json'
    m=json.loads(mp.read_text(encoding='utf-8-sig'))
    failed=[]
    for rel,rec in (m.get('files') or {}).items():
        p=root/rel
        ok=p.exists() and p.stat().st_size==rec.get('bytes') and sha(p)==rec.get('sha256')
        if not ok: failed.append(rel)
    out={'stage':'v0.6D1-R4.29','status':'PASS_R429_SOURCE_MANIFEST' if not failed else 'BLOCKED_R429_SOURCE_MANIFEST','checks_passed':len((m.get('files') or {}))-len(failed),'checks_total':len(m.get('files') or {}),'failed':failed}
    print(json.dumps(out,indent=2)); return 0 if not failed else 3
if __name__=='__main__': raise SystemExit(main())
