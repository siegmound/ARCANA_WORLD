from pathlib import Path
import argparse
import json

from arcana_worldsim.scientific_engines.r449_geonomics_j14_j18_full_job_revalidation_coverage_expansion_execution_evidence_capture import execute_all, build

parser = argparse.ArgumentParser()
parser.add_argument("--parallel-jobs", type=int, default=2)
args = parser.parse_args()

root = Path.cwd()
progress = execute_all(root, parallel_jobs=args.parallel_jobs)
print(json.dumps(progress, indent=2, ensure_ascii=False))
if progress.get("status") != "R449_ALL_EXPANSION_SHARDS_COMPLETED":
    raise SystemExit(3)

out = build(root)
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(0 if str(out.get("status", "")).startswith("PASS_R449_") else 4)
