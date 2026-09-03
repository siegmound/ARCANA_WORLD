from __future__ import annotations
import argparse, json
from pathlib import Path
from arcana_worldsim.state_query.r56_slim_ancestry import analyze_ancestry_challenges

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=Path('.')); ap.add_argument('--allow-non-scientific-dev-parent',action='store_true'); a=ap.parse_args()
    audit=analyze_ancestry_challenges(a.root.resolve(),allow_non_scientific_dev_parent=a.allow_non_scientific_dev_parent)
    print(json.dumps(audit,indent=2,sort_keys=True)); return 0 if not audit['failed'] else 2
if __name__=='__main__': raise SystemExit(main())
