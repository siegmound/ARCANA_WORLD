from pathlib import Path
import argparse,json
from arcana_worldsim.scientific_engines.r410_precision_alternate_evidence_closure import audit
p=argparse.ArgumentParser();p.add_argument('--root',default='.');a=p.parse_args();out,_=audit(Path(a.root).resolve());print(json.dumps(out,indent=2));raise SystemExit(0 if out.get('status','').startswith('PASS_') else 3)
