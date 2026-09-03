from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r440_geonomics_domain_specific_carrier_dynamics_authority_execution_queue import build

out = build(Path.cwd())
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if str(out.get("status", "")).startswith("PASS_R440_") else 3)
