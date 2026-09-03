from pathlib import Path
import argparse, json
from arcana_worldsim.state_query.r511_r330_census_group_reconciliation import reconcile

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); a=ap.parse_args()
    out=reconcile(Path(a.root)); print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if out.get('scientific_candidate_eligible') else 2
if __name__=='__main__': raise SystemExit(main())
