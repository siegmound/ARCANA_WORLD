from pathlib import Path
import argparse,json
from arcana_worldsim.scientific_engines.r330_census_group_abm import validate_inputs,census_calibration,build_group_abm,summarize,build_outputs,write_manifest,CANDIDATE_PASS
p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();root=Path(a.root);cfg=json.loads((root/'configs/world1_r330_census_group_abm_v0_6D1_R3_30.json').read_text())
inp=validate_inputs(root);cal=census_calibration(inp,cfg);abm=build_group_abm(inp,cfg,cal);outcomes,sens,hist=summarize(inp,cfg,cal,abm);out=root/'outputs'/'v0_6D1_R3_30';audit=build_outputs(inp,cfg,cal,abm,outcomes,sens,hist,out);write_manifest(out,'CANDIDATE_OUTPUT_MANIFEST')
if audit['status']!=CANDIDATE_PASS: raise SystemExit(2)
print(json.dumps({'stage':'v0.6D1-R3.30','status':CANDIDATE_PASS,'output_dir':str(out),'summary':audit['summary']},indent=2))
