from __future__ import annotations
import argparse, json
from pathlib import Path
from arcana_worldsim.state_query.r56_slim_ancestry import validate_parent_authority

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=Path('.')); ap.add_argument('--allow-non-scientific-dev',action='store_true'); a=ap.parse_args()
    out=validate_parent_authority(a.root.resolve(),allow_non_scientific_dev=a.allow_non_scientific_dev)
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if not out['failed'] else 2
if __name__=='__main__': raise SystemExit(main())
