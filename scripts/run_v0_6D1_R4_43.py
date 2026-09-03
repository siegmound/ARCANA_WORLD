from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r443_geonomics_scientific_readout_authority_metric_extraction_adjudication_schema import build

out = build(Path.cwd())
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if str(out.get("status", "")).startswith("PASS_R443_") else 3)
