from __future__ import annotations
import argparse, json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.scientific_engines.r324_h1_candidate_discovery import (
    R324GateError, validate_inputs, run_discovery, build_outputs, audit_result, write_manifest
)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args()
    root = args.root.resolve()
    out = root / "outputs" / "v0_6D1_R3_24"
    try:
        inputs = validate_inputs(root)
        result = run_discovery(inputs)
        build_outputs(inputs, result, out)
        audit = audit_result(inputs, result, out)
        write_manifest(out, "CANDIDATE_OUTPUT_MANIFEST" if audit["checks_failed"] == 0 else "FAILED_OUTPUT_MANIFEST")
        payload = {
            "stage": "v0.6D1-R3.24",
            "status": audit["status"],
            "output_dir": str(out),
            "summary": audit["summary"],
        }
        print(json.dumps(payload, indent=2))
        return 0 if audit["checks_failed"] == 0 else 1
    except (R324GateError, Exception) as e:
        print(json.dumps({"stage":"v0.6D1-R3.24","status":"FAIL_CLOSED","error":str(e)}, indent=2))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
