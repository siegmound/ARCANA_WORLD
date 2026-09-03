from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from arcana_worldsim.state_query.r52_corridors import STAGE, SOURCE_MANIFEST_REL, validate_parent_authority


def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024), b''): h.update(c)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--allow-non-scientific-dev-parent',action='store_true'); args=ap.parse_args()
    root=args.root.resolve(); mp=root/SOURCE_MANIFEST_REL
    checks={"manifest_present":mp.is_file()}; files={}
    if mp.is_file():
        m=json.loads(mp.read_text(encoding='utf-8')); files=dict(m.get('files') or {})
        checks['manifest_stage_exact']=m.get('stage')==STAGE
        checks['manifest_count_exact']=int(m.get('source_authority_file_count',-1))==len(files)
        for rel,rec in files.items():
            p=root/rel
            checks[f'source::{rel}']=p.is_file() and p.stat().st_size==int(rec.get('bytes',-1)) and sha256_file(p)==rec.get('sha256')
    else:
        checks['manifest_stage_exact']=checks['manifest_count_exact']=False
    failed=[k for k,v in checks.items() if not v]
    auth=validate_parent_authority(root,args.allow_non_scientific_dev_parent)
    out={
      "stage":STAGE,
      "status":"PASS_R52_SOURCE_AND_IMMUTABLE_PARENT_AUTHORITY" if not failed and not auth['failed'] else "BLOCKED_R52_SOURCE_OR_PARENT_AUTHORITY",
      "source_manifest_checks_passed":sum(bool(v) for v in checks.values()),
      "source_manifest_checks_total":len(checks),
      "source_manifest_failed":failed,
      "parent_authority":auth,
    }
    print(json.dumps(out,indent=2))
    raise SystemExit(0 if out['status'].startswith('PASS_') else 2)
if __name__=='__main__': main()
