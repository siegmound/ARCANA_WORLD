from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r325_h2_detailed_biology import R325GateError,validate_inputs,run_h2,build_outputs,write_manifest

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=ROOT);a=ap.parse_args();root=a.root.resolve();out=root/'outputs'/'v0_6D1_R3_25'
 try:
  inp=validate_inputs(root);r=run_h2(inp);build_outputs(inp,r,out);audit=json.loads((out/'R3_25_INTEGRATED_AUDIT.json').read_text());write_manifest(out,'CANDIDATE_OUTPUT_MANIFEST' if audit['checks_failed']==0 else 'FAILED_OUTPUT_MANIFEST');print(json.dumps({'stage':'v0.6D1-R3.25','status':audit['status'],'output_dir':str(out),'summary':audit['summary']},indent=2));return 0 if audit['checks_failed']==0 else 1
 except Exception as e:
  print(json.dumps({'stage':'v0.6D1-R3.25','status':'FAIL_CLOSED','error':str(e)},indent=2));return 1
if __name__=='__main__':raise SystemExit(main())
