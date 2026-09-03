from pathlib import Path
import argparse, json
from arcana_worldsim.scientific_engines.r37a_validation import analyze_r37a_parent_reference

p=argparse.ArgumentParser()
p.add_argument('raw_results_zip')
p.add_argument('--out',default='reference_results/R3_7A_PARENT_NEMO_DRIFT_AND_KEFF_REFERENCE.json')
a=p.parse_args()
r=analyze_r37a_parent_reference(a.raw_results_zip)
out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'stage':'v0.6D1-R3.7A','verdict':r['verdict'],'out':str(out)},indent=2))
