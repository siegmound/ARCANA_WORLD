from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r438_geonomics_exact_initialization_adapter_probe_elimination_preflight import build
out=build(Path.cwd()); print(json.dumps(out,indent=2,ensure_ascii=False)); raise SystemExit(0 if str(out.get('status','')).startswith('PASS_R438_') else 3)
