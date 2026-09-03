from __future__ import annotations
import argparse, json
from pathlib import Path
from arcana_worldsim.scientific_engines.r36e_inference import analyze_r36d_results_zip

p=argparse.ArgumentParser()
p.add_argument('results_zip')
p.add_argument('--out', default='R3_6E_CAUSAL_INFERENCE.json')
a=p.parse_args()
res=analyze_r36d_results_zip(a.results_zip)
Path(a.out).write_text(json.dumps(res, indent=2, sort_keys=True)+"\n", encoding='utf-8')
print(json.dumps({k:res[k] for k in ['stage','verdict','source_job_count','source_executed_count','source_parsed_complete_count']}, indent=2))
