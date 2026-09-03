from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
from arcana_worldsim.state_query.r54_nemo_genetics import validate_parent_authority

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=ROOT); ap.add_argument('--allow-non-scientific-dev',action='store_true'); a=ap.parse_args()
    r=validate_parent_authority(a.root.resolve(),allow_non_scientific_dev=a.allow_non_scientific_dev)
    print(json.dumps(r,indent=2,sort_keys=True)); return 0 if not r['failed'] else 2
if __name__=='__main__': raise SystemExit(main())
