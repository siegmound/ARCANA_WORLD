from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r434_geonomics_selector_authority_native_parameter_preflight import final_seal

root = Path.cwd()
out = final_seal(root)
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if out.get("verdict") == "SEALED" else 4)
