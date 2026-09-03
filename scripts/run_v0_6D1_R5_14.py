from pathlib import Path
import argparse, json
from arcana_worldsim.state_query.r514_r333_holocene_domestication_reconciliation import run_reconciliation
ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');a=ap.parse_args();o=run_reconciliation(Path(a.root),True);print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['scientific_candidate_eligible'] else 2)
