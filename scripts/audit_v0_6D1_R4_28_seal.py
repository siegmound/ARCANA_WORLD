from pathlib import Path
import argparse, json
from arcana_worldsim.scientific_engines.r428_target_selector_design_authority_j14_preflight import final_seal
p=argparse.ArgumentParser(); p.add_argument('--root',default='.'); a=p.parse_args(); o=final_seal(Path(a.root).resolve()); print(json.dumps(o,indent=2)); raise SystemExit(0 if o.get('verdict')=='SEALED' else 3)
