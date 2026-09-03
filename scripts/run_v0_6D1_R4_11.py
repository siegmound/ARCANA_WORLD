from pathlib import Path
import argparse, json
from arcana_worldsim.scientific_engines.r411_cdmetapop_population_metric_repair import prepare, execute_reextraction_and_readjudicate
p=argparse.ArgumentParser(); p.add_argument('--root',default='.'); a=p.parse_args(); root=Path(a.root).resolve()
prep,_=prepare(root); print(json.dumps(prep,indent=2))
if not prep.get('status','').startswith('PASS_'): raise SystemExit(3)
out,_=execute_reextraction_and_readjudicate(root); print(json.dumps(out,indent=2)); raise SystemExit(0 if out.get('status','').startswith('PASS_') else 3)
