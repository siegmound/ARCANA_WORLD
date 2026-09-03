from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from arcana_worldsim.state_query.r57_block_closure import run_integrated_audit


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    args = ap.parse_args()
    audit = run_integrated_audit(Path(args.root))
    print(json.dumps(audit, indent=2))
    return 0 if audit.get("scientific_block_seal_eligible") is True else 1


if __name__ == "__main__":
    sys.exit(main())
