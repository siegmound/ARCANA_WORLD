from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r434_geonomics_selector_authority_native_parameter_preflight import build

root = Path.cwd()
out = build(root)
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if str(out.get("status", "")).startswith("PASS_R434_") else 3)
