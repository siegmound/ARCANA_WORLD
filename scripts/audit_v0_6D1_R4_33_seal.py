from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r433_target_binding_static_adjudication_geonomics_runtime_preflight import final_seal

root = Path.cwd()
out = final_seal(root)
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if out.get("verdict") == "SEALED" else 4)
