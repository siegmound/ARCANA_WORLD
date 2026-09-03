from pathlib import Path
import argparse, json
from arcana_worldsim.scientific_engines.r415_retained_metric_target_semantics import build
p=argparse.ArgumentParser(); p.add_argument('--root',default='.'); a=p.parse_args(); out=build(Path(a.root).resolve()); print(json.dumps(out,indent=2)); raise SystemExit(0 if str(out.get('status','')).startswith('PASS_') else 1)
