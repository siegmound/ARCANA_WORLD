from pathlib import Path
import argparse,json
from arcana_worldsim.scientific_engines.r455_non_geonomics_80_stream_execution_evidence_capture import extract_job,extract_slim_job
p=argparse.ArgumentParser();p.add_argument("--job-id",required=True);p.add_argument("--slim",action="store_true");a=p.parse_args()
out=(extract_slim_job if a.slim else extract_job)(Path.cwd(),a.job_id);print(json.dumps(out,indent=2))
raise SystemExit(0 if out.get("status")=="PASS_R455_JOB_EVIDENCE_CAPTURE" else 3)
