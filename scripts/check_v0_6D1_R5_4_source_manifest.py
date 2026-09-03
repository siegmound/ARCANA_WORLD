from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]); a=ap.parse_args(); root=a.root.resolve(); mp=root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_4.json'
    if not mp.is_file(): print(json.dumps({'stage':'v0.6D1-R5.4','status':'BLOCKED_R54_SOURCE_MANIFEST','failed':['manifest_missing']},indent=2)); return 2
    doc=json.loads(mp.read_text(encoding='utf-8')); checks={}
    for rel,meta in (doc.get('files') or {}).items():
        p=root/rel; checks[rel]=p.is_file() and p.stat().st_size==int(meta.get('bytes',-1)) and sha256_file(p)==meta.get('sha256')
    semantic={
      'stage_exact':doc.get('stage')=='v0.6D1-R5.4',
      'nemo_version_exact':doc.get('nemo_required_version')=='2.4.2',
      'r53_plan_pin_exact':doc.get('r53_plan_sha256')=='3110e7ac031d12bb2e878b19df75edc5684b27aed2633224e7f889028f4a29c9',
      'micro_seal_forbidden':doc.get('micro_seal_created') is False,
    }
    checks.update({f'semantic::{k}':v for k,v in semantic.items()}); failed=[k for k,v in checks.items() if not v]
    r={'stage':'v0.6D1-R5.4','status':'PASS_R54_SOURCE_MANIFEST' if not failed else 'BLOCKED_R54_SOURCE_MANIFEST','checks_passed':sum(bool(v) for v in checks.values()),'checks_total':len(checks),'failed':failed}
    print(json.dumps(r,indent=2,sort_keys=True)); return 0 if not failed else 2
if __name__=='__main__': raise SystemExit(main())
