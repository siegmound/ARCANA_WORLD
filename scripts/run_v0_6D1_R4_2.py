from pathlib import Path
import argparse,json
from arcana_worldsim.scientific_engines.r42_historical_materialization import validate
p=argparse.ArgumentParser(); p.add_argument('--root',required=True); a=p.parse_args()
r,_=validate(Path(a.root)); print(json.dumps(r,indent=2)); raise SystemExit(0 if r['checks_failed']==0 else 3)
