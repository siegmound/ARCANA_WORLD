from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r437_geonomics_canonical_layer_binding_exact_state_injection_dry_run import final_seal

root=Path.cwd()
out=final_seal(root)
print(json.dumps(out,indent=2,ensure_ascii=False))
raise SystemExit(0 if out.get("verdict")=="SEALED" else 4)
