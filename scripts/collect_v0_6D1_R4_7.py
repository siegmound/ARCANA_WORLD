from pathlib import Path
import argparse, json
from arcana_worldsim.scientific_engines.r47_cdmetapop_forcing_parity import collect_and_readjudicate
p=argparse.ArgumentParser(); p.add_argument('--root',default='.')
a=p.parse_args(); out,_=collect_and_readjudicate(Path(a.root).resolve()); print(json.dumps(out,indent=2)); raise SystemExit(0 if out.get('status','').startswith('PASS_') else 3)
