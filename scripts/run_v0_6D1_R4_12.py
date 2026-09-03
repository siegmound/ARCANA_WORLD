from pathlib import Path
import argparse, json
from arcana_worldsim.scientific_engines.r412_cdmetapop_precision_comparability_diagnosis import diagnose
p=argparse.ArgumentParser();p.add_argument('--root',default='.');a=p.parse_args();out,_=diagnose(Path(a.root).resolve());print(json.dumps(out,indent=2));raise SystemExit(0 if out.get('status','').startswith('PASS_') else 3)
