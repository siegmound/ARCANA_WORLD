from pathlib import Path
import argparse, json
from arcana_worldsim.scientific_engines.r37d_selection_closure import analyze_r37c_r1_selection_evidence

p=argparse.ArgumentParser()
p.add_argument('results_zip')
p.add_argument('--out', default='outputs/v0_6D1_R3_7D/R3_7D_DIRECTIONAL_SELECTION_EVIDENCE_CLOSURE.json')
a=p.parse_args()
report=analyze_r37c_r1_selection_evidence(a.results_zip)
out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ('stage','verdict','chain_count','geometric_K_eff_all','high_N_dynamic_selection_shadow_envelope')},indent=2))
