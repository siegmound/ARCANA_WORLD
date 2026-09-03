from pathlib import Path
import argparse, json
from arcana_worldsim.scientific_engines.r44_discordance_adjudication import adjudicate
p=argparse.ArgumentParser(); p.add_argument('--root',default='.'); a=p.parse_args()
r,_=adjudicate(Path(a.root).resolve()); print(json.dumps(r,indent=2)); raise SystemExit(0 if r['status'].startswith('PASS_') else 3)
