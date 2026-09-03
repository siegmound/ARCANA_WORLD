from pathlib import Path
import argparse,json
from arcana_worldsim.scientific_engines.r45_causal_diagnosis import diagnose
p=argparse.ArgumentParser(); p.add_argument("--root",default="."); a=p.parse_args()
r,_=diagnose(Path(a.root).resolve()); print(json.dumps(r,indent=2)); raise SystemExit(0 if r["status"].startswith("PASS_") else 3)
