from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r450_geonomics_full_job_revalidation_evidence_review_final_closure import final_seal

out = final_seal(Path.cwd())
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if out.get("verdict") == "SEALED" else 4)
