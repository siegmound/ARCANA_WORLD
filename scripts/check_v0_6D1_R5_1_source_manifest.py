from __future__ import annotations
import argparse, json
from pathlib import Path
from arcana_worldsim.state_query.r51_cradle import validate_authority, engine_utility_review, sha256_file

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--allow-non-scientific-dev-parent',action='store_true')
    a=ap.parse_args(); root=a.root.resolve()
    m=json.loads((root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_1.json').read_text(encoding='utf-8'))
    sf=[]
    for rel,meta in m.get('files',{}).items():
        p=root/rel
        ok=p.is_file() and p.stat().st_size==int(meta['bytes']) and sha256_file(p)==meta['sha256']
        sf.append((rel,ok))
    r=validate_authority(root,a.allow_non_scientific_dev_parent)
    r['source_manifest_checks_passed']=sum(1 for _,ok in sf if ok)
    r['source_manifest_checks_total']=len(sf)
    r['source_manifest_failed']=[rel for rel,ok in sf if not ok]
    r['engine_review']=engine_utility_review()
    print(json.dumps(r,indent=2))
    raise SystemExit(0 if not r['failed'] and not r['source_manifest_failed'] else 2)
if __name__=='__main__': main()
