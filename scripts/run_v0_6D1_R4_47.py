from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r447_geonomics_first_governed_revalidation_evidence_review_cohort_adjudication_closure import build

out = build(Path.cwd())
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if str(out.get("status", "")).startswith("PASS_R447_") else 3)
