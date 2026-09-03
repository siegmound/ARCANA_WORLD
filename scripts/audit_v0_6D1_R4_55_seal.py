from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r455_non_geonomics_80_stream_execution_evidence_capture import final_seal
out=final_seal(Path.cwd());print(json.dumps(out,indent=2))
raise SystemExit(0 if out.get("verdict")=="SEALED" else 4)
