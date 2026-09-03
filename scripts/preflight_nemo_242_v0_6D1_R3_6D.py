from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
from arcana_worldsim.scientific_engines.nemo242_r36d import preflight_nemo242
p=preflight_nemo242(); print(json.dumps({'available':p.available,'executable':p.executable,'resolved_path':p.resolved_path,'exact_version_name':p.exact_version_name,'reason':p.reason,'pass_exact_242':p.pass_exact_242},indent=2)); raise SystemExit(0 if p.pass_exact_242 else 2)
