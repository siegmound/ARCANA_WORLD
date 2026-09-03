from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r445_geonomics_scientific_execution_authorization_first_governed_revalidation_preflight import final_seal

out = final_seal(Path.cwd())
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if out.get("verdict") == "SEALED" else 4)
