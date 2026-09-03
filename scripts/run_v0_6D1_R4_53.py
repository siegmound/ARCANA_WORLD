from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r453_non_geonomics_scientific_execution_interface_readout_authority_preflight import build

out = build(Path.cwd())
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if str(out.get("status", "")).startswith("PASS_R453_") else 3)
