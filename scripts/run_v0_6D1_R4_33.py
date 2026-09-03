from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r433_target_binding_static_adjudication_geonomics_runtime_preflight import build

root = Path.cwd()
out = build(root)
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if str(out.get("status", "")).startswith("PASS_R433_") else 3)
