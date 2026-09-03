from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r446_geonomics_first_governed_revalidation_cohort_execution_evidence_capture import build

out = build(Path.cwd())
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if str(out.get("status", "")).startswith("PASS_R446_") else 3)
