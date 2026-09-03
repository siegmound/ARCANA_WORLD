from __future__ import annotations
import argparse, json
from pathlib import Path
from arcana_worldsim.state_query.r52_corridors import validate_source_binding_probe

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); args=ap.parse_args()
    result=validate_source_binding_probe(args.root)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status'].startswith('PASS_') else 2)

if __name__=='__main__': main()
