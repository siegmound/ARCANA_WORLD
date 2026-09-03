from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r456_multi_engine_23_job_full_evidence_review_final_revalidation_closure import build
out=build(Path.cwd())
print(json.dumps(out,indent=2))
raise SystemExit(0 if str(out.get("status","")).startswith("PASS_R456_") else 3)
