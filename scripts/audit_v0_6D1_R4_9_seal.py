from pathlib import Path
import argparse,json
from arcana_worldsim.scientific_engines.r49_additional_matched_control_replicates import final_seal
p=argparse.ArgumentParser();p.add_argument('--root',default='.');a=p.parse_args();out,_=final_seal(Path(a.root).resolve());print(json.dumps(out,indent=2));raise SystemExit(0 if out.get('verdict')=='SEALED' else 3)
