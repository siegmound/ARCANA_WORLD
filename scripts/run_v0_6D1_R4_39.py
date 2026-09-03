from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers import build

out=build(Path.cwd())
print(json.dumps(out,indent=2,ensure_ascii=False))
raise SystemExit(0 if str(out.get("status","")).startswith("PASS_R439_") else 3)
