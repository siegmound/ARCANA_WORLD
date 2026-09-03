from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def sha(p):
    h=hashlib.sha256();
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); a=ap.parse_args(); root=a.root.resolve()
    m=json.loads((root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_3.json').read_text(encoding='utf-8'))
    checks={}
    for rel,meta in (m.get('files') or {}).items():
        p=root/rel; checks[rel]=p.is_file() and p.stat().st_size==int(meta['bytes']) and sha(p)==meta['sha256']
    failed=[k for k,v in checks.items() if not v]
    out={'stage':'v0.6D1-R5.3','status':'PASS_R53_SOURCE_MANIFEST' if not failed else 'BLOCKED_R53_SOURCE_MANIFEST','checks_passed':sum(checks.values()),'checks_total':len(checks),'failed':failed}
    print(json.dumps(out,indent=2)); raise SystemExit(0 if not failed else 3)
if __name__=='__main__': main()
