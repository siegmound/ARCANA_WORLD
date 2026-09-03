from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r449_geonomics_j14_j18_full_job_revalidation_coverage_expansion_execution_evidence_capture import final_seal

out = final_seal(Path.cwd())
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if out.get("verdict") == "SEALED" else 5)
