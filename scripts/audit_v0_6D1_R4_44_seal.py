from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r444_geonomics_readout_extraction_dry_run_adjudication_input_validation import final_seal

out = final_seal(Path.cwd())
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if out.get("verdict") == "SEALED" else 4)
