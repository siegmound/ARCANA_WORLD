from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r451_multi_engine_23_job_reconciliation_revalidation_gap_census import final_seal

out = final_seal(Path.cwd())
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if out.get("verdict") == "SEALED" else 4)
