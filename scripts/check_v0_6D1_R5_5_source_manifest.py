from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=Path('.')); a=ap.parse_args(); root=a.root.resolve()
    mpath=root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_5.json'
    try: doc=json.loads(mpath.read_text(encoding='utf-8'))
    except Exception as e:
        print(json.dumps({'stage':'v0.6D1-R5.5','status':'BLOCKED_R55_SOURCE_MANIFEST','checks_passed':0,'checks_total':1,'failed':[f'manifest:{e}']},indent=2)); return 2
    checks={}
    for rel,meta in (doc.get('files') or {}).items():
        p=root/rel
        checks[f'present::{rel}']=p.is_file()
        checks[f'bytes::{rel}']=p.is_file() and p.stat().st_size==int(meta.get('bytes',-1))
        checks[f'sha256::{rel}']=p.is_file() and sha(p)==meta.get('sha256')
    checks['stage_exact']=doc.get('stage')=='v0.6D1-R5.5'
    checks['status_exact']=doc.get('status')=='R55_SOURCE_AUTHORITY_MANIFEST'
    checks['no_new_external_engine_execution']=doc.get('new_external_engine_execution') is False
    checks['micro_seal_created_false']=doc.get('micro_seal_created') is False
    failed=[k for k,v in checks.items() if not v]
    out={'stage':'v0.6D1-R5.5','status':'PASS_R55_SOURCE_MANIFEST' if not failed else 'BLOCKED_R55_SOURCE_MANIFEST','checks_passed':sum(bool(v) for v in checks.values()),'checks_total':len(checks),'failed':failed}
    print(json.dumps(out,indent=2,sort_keys=True)); return 0 if not failed else 2
if __name__=='__main__': raise SystemExit(main())
