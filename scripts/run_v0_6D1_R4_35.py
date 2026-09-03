from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r435_geonomics_native_schema_initial_state_seed_closure import build

root = Path.cwd()
out = build(root)
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if str(out.get("status", "")).startswith("PASS_R435_") else 3)
