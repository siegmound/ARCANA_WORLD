from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
from arcana_worldsim.state_query.r54_nemo_genetics import analyze_nemo_evidence

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=ROOT); ap.add_argument('--allow-non-scientific-dev-parent',action='store_true'); a=ap.parse_args()
    r=analyze_nemo_evidence(a.root.resolve(),allow_non_scientific_dev_parent=a.allow_non_scientific_dev_parent); print(json.dumps(r['audit'],indent=2,sort_keys=True)); return 0 if not r['audit']['failed'] else 2
if __name__=='__main__': raise SystemExit(main())
