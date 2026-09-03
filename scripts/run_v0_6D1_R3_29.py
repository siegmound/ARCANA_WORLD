from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r329_population_settlement_culture import *
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=ROOT);a=ap.parse_args();root=a.root.resolve();out=root/'outputs'/'v0_6D1_R3_29'
 try:
  inp=validate_inputs(root);cfg=load_json(root/'configs'/'world1_r329_population_settlement_cultural_preconditions_v0_6D1_R3_29.json');r=run_stage(inp,cfg);o,s=evaluate(inp,cfg,r);build_outputs(inp,cfg,r,o,s,out);audit=load_json(out/'R3_29_INTEGRATED_AUDIT.json');write_manifest(out,'CANDIDATE_OUTPUT_MANIFEST' if audit['checks_failed']==0 else 'FAILED_OUTPUT_MANIFEST');print(json.dumps({'stage':STAGE,'status':audit['status'],'output_dir':str(out),'summary':audit['summary']},indent=2));return 0 if audit['checks_failed']==0 else 1
 except Exception as e:print(json.dumps({'stage':STAGE,'status':'FAIL_CLOSED','error':str(e)},indent=2));return 1
if __name__=='__main__':raise SystemExit(main())
