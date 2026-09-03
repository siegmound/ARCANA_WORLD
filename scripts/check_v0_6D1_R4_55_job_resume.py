from pathlib import Path
import argparse,json
from arcana_worldsim.scientific_engines.r455_non_geonomics_80_stream_execution_evidence_capture import resume_status
p=argparse.ArgumentParser();p.add_argument("--job-id",required=True);a=p.parse_args();out=resume_status(Path.cwd(),a.job_id);print(json.dumps(out))
raise SystemExit(0 if out.get("status")=="VALID" else (10 if out.get("status")=="ABSENT" else (11 if out.get("status")=="PARTIAL" else 12)))
