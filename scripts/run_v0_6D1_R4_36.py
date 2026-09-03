from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r436_geonomics_native_parameter_model_construction_injection_preflight import build

root=Path.cwd()
out=build(root)
print(json.dumps(out,indent=2,ensure_ascii=False))
raise SystemExit(0 if str(out.get("status","")).startswith("PASS_R436_") else 3)
