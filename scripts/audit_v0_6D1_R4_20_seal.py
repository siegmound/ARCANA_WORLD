from pathlib import Path
import argparse,json
from arcana_worldsim.scientific_engines.r420_p2_adapter_preflight_target_protocol_repair import final_seal
p=argparse.ArgumentParser();p.add_argument('--root',default='.');a=p.parse_args();o=final_seal(Path(a.root).resolve());print(json.dumps(o,indent=2));raise SystemExit(0 if o.get('verdict')=='SEALED' else 1)
