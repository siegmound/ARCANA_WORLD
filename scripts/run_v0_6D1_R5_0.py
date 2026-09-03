from pathlib import Path
import argparse
import json
import sys

from arcana_worldsim.state_query.r50_query import STAGE, run_demonstration

p = argparse.ArgumentParser()
p.add_argument("--root", required=True)
p.add_argument("--out")
p.add_argument("--dev-allow-unverified-r456", action="store_true")
a = p.parse_args()
root = Path(a.root)
out = Path(a.out) if a.out else root / "outputs" / "v0_6D1_R5_0"

try:
    result = run_demonstration(root, out_dir=out, allow_unverified_r456=a.dev_allow_unverified_r456)
    audit = result["audit"]
    print(json.dumps({
        "stage": STAGE,
        "status": audit["status"],
        "scientific_candidate_eligible": audit["scientific_candidate_eligible"],
        "checks_passed": audit["checks_passed"],
        "checks_total": audit["checks_total"],
        "output_dir": str(result["out_dir"]),
        "summary": audit["summary"],
    }, indent=2))
    sys.exit(0 if audit["checks_failed"] == 0 else 1)
except Exception as e:
    print(json.dumps({"stage": STAGE, "status": "FAIL_CLOSED", "error": repr(e)}, indent=2))
    sys.exit(1)
