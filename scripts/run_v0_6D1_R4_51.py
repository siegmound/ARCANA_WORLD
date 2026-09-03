from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r451_multi_engine_23_job_reconciliation_revalidation_gap_census import build

out = build(Path.cwd())
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if str(out.get("status", "")).startswith("PASS_R451_") else 3)
