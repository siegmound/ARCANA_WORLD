from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers import final_seal

out=final_seal(Path.cwd())
print(json.dumps(out,indent=2,ensure_ascii=False))
raise SystemExit(0 if out.get("verdict")=="SEALED" else 4)
