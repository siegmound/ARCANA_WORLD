from pathlib import Path
import argparse,json
from arcana_worldsim.scientific_engines.r42_historical_materialization import final_seal
p=argparse.ArgumentParser(); p.add_argument('--root',required=True); a=p.parse_args()
r=final_seal(Path(a.root)); print(json.dumps(r,indent=2)); raise SystemExit(0 if r['verdict']=='SEALED' else 3)
