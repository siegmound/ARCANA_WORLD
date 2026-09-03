from pathlib import Path
import argparse,json
from arcana_worldsim.scientific_engines.r43_historical_revalidation import prepare,PREPARED
p=argparse.ArgumentParser(); p.add_argument('--root',required=True); a=p.parse_args()
r,_=prepare(Path(a.root)); print(json.dumps(r,indent=2)); raise SystemExit(0 if r['status']==PREPARED else 3)
