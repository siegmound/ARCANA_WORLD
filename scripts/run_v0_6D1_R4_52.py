from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r452_non_geonomics_job_specific_evidence_adjudication_execution_plan import build

out = build(Path.cwd())
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if str(out.get("status", "")).startswith("PASS_R452_") else 3)
