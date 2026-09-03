from pathlib import Path
import argparse,json
from arcana_worldsim.scientific_engines.r43_historical_revalidation import final_seal,SEALED
p=argparse.ArgumentParser(); p.add_argument('--root',required=True); a=p.parse_args()
r=final_seal(Path(a.root)); print(json.dumps(r,indent=2)); raise SystemExit(0 if r['status']==SEALED else 3)
