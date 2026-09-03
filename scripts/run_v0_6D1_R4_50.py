from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r450_geonomics_full_job_revalidation_evidence_review_final_closure import build

out = build(Path.cwd())
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if str(out.get("status", "")).startswith("PASS_R450_") else 3)
