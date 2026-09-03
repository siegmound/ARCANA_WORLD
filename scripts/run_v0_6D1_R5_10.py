from __future__ import annotations
import argparse, json
from pathlib import Path
from arcana_worldsim.state_query.r510_r329_settlement_cultural_reconciliation import reconcile

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root', required=True); a=ap.parse_args()
    result=reconcile(Path(a.root)); print(json.dumps(result, indent=2)); return 0 if result.get('scientific_candidate_eligible') else 1

if __name__=='__main__': raise SystemExit(main())
