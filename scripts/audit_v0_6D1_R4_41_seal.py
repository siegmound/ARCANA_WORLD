from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r441_geonomics_domain_specific_execution_queue_single_transition_dry_run import final_seal

out = final_seal(Path.cwd())
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if out.get("verdict") == "SEALED" else 4)
