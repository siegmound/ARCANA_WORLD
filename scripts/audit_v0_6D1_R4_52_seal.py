from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r452_non_geonomics_job_specific_evidence_adjudication_execution_plan import final_seal

out = final_seal(Path.cwd())
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if out.get("verdict") == "SEALED" else 4)
