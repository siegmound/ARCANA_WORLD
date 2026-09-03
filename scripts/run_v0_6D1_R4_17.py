from pathlib import Path
import argparse,json
from arcana_worldsim.scientific_engines.r417_target_extractor_promotion_closure import build
p=argparse.ArgumentParser();p.add_argument('--root',default='.');a=p.parse_args();o=build(Path(a.root).resolve());print(json.dumps(o,indent=2));raise SystemExit(0 if str(o.get('status','')).startswith('PASS_') else 1)
