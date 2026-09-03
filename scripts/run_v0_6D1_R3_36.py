from pathlib import Path
import argparse,json,sys
from arcana_worldsim.scientific_engines.r336_producer_selection_ecology import *
p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();root=Path(a.root)
try:
 inp=validate_inputs(root);cfg=load_json(root/'configs/world1_r336_producer_selection_ecology_v0_6D1_R3_36.json');rep=replay_selection_ecology(inp,cfg);out=root/'outputs'/'v0_6D1_R3_36';audit=build_outputs(inp,cfg,rep,out);write_manifest(out,audit['status']);print(json.dumps({'stage':STAGE,'status':audit['status'],'output_dir':str(out),'summary':audit['summary']},indent=2));sys.exit(0 if audit['checks_failed']==0 else 1)
except Exception as e:
 print(json.dumps({'stage':STAGE,'status':'FAIL_CLOSED','error':repr(e)},indent=2));sys.exit(1)
