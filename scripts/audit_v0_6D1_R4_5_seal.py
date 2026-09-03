from pathlib import Path
import argparse,json
from arcana_worldsim.scientific_engines.r45_causal_diagnosis import final_seal
p=argparse.ArgumentParser(); p.add_argument("--root",default="."); a=p.parse_args()
r,_=final_seal(Path(a.root).resolve()); print(json.dumps(r,indent=2)); raise SystemExit(0 if r.get("verdict")=="SEALED" else 3)
