from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r440_geonomics_domain_specific_carrier_dynamics_authority_execution_queue import final_seal

out = final_seal(Path.cwd())
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if out.get("verdict") == "SEALED" else 4)
