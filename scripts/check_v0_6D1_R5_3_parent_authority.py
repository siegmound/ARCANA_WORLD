from __future__ import annotations
import argparse, json
from pathlib import Path
from arcana_worldsim.state_query.r53_demography import validate_parent_authority

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--allow-non-scientific-dev',action='store_true'); a=ap.parse_args()
    r=validate_parent_authority(a.root,a.allow_non_scientific_dev); print(json.dumps(r,indent=2)); raise SystemExit(0 if not r['failed'] else 3)
if __name__=='__main__': main()
