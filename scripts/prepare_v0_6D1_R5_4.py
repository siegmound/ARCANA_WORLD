from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
from arcana_worldsim.state_query.r54_nemo_genetics import prepare_genetic_challenges, sha256_file, OUT_REL

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=ROOT); ap.add_argument('--allow-non-scientific-dev-parent',action='store_true'); a=ap.parse_args()
    p=prepare_genetic_challenges(a.root.resolve(),allow_non_scientific_dev_parent=a.allow_non_scientific_dev_parent)
    path=a.root.resolve()/OUT_REL/'R5_4_NEMO_EXECUTION_PLAN.json'
    print(json.dumps({'stage':p['stage'],'status':p['status'],'family_count':p['family_count'],'group_count':p['group_count'],'planned_stream_count':p['planned_stream_count'],'variants':2,'seeds':p['seeds'],'plan_sha256':sha256_file(path)},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
