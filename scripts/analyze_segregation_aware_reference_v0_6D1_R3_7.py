from __future__ import annotations
import argparse, json
from pathlib import Path
from arcana_worldsim.scientific_engines.r37_validation import analyze_r37_reference_closure

p=argparse.ArgumentParser()
p.add_argument('raw_results_zip')
p.add_argument('r36e_json')
p.add_argument('--out',default='reference_results/R3_7_SEGREGATION_AWARE_REFERENCE_CLOSURE.json')
a=p.parse_args()
r=analyze_r37_reference_closure(a.raw_results_zip,a.r36e_json)
out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({k:r[k] for k in ['stage','verdict','max_relative_error_vs_analytic','minimum_legacy_over_repaired_factor','maximum_ancestry_post_over_pre']},indent=2))
