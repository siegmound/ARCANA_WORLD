from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r435_geonomics_native_schema_initial_state_seed_closure import final_seal

root = Path.cwd()
out = final_seal(root)
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if out.get("verdict") == "SEALED" else 4)
