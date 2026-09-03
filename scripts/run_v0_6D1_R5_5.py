from __future__ import annotations
import argparse, json
from pathlib import Path
from arcana_worldsim.state_query.r55_contact_history import build_contact_history

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=Path('.')); ap.add_argument('--allow-non-scientific-dev-parent',action='store_true'); a=ap.parse_args()
    out=build_contact_history(a.root.resolve(),allow_non_scientific_dev_parent=a.allow_non_scientific_dev_parent)
    print(json.dumps(out['audit'],indent=2,sort_keys=True))
    return 0 if not out['audit']['failed'] else 2
if __name__=='__main__': raise SystemExit(main())
