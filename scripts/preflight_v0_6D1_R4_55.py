from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r455_non_geonomics_80_stream_execution_evidence_capture import preflight
out=preflight(Path.cwd());print(json.dumps(out,indent=2))
raise SystemExit(0 if str(out.get("status","")).startswith("PASS_R455_") else 2)
