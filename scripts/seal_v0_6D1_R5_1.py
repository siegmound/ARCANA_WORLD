from __future__ import annotations
import argparse
import json
from pathlib import Path
from arcana_worldsim.state_query.r51_seal import validate_and_build_seal, write_final_seal


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--allow-non-scientific-dev", action="store_true")
    args = ap.parse_args()
    seal = validate_and_build_seal(args.root.resolve(), allow_non_scientific_dev=args.allow_non_scientific_dev)
    path, digest = write_final_seal(args.root.resolve(), seal)
    print(json.dumps({
        "stage": seal["stage"],
        "status": seal["status"],
        "sealed": seal["sealed"],
        "checks_passed": seal["checks_passed"],
        "checks_total": seal["checks_total"],
        "failed": seal["failed"],
        "summary": seal["summary"],
        "r51_atlas_sha256": seal["authority"]["r51_atlas_sha256"],
        "candidate_output_manifest_sha256": seal["authority"]["r51_candidate_output_manifest_sha256"],
        "structure_adjudication_manifest_sha256": seal["authority"]["r51_structure_adjudication_manifest_sha256"],
        "final_seal_sha256": digest,
        "final_seal_path": str(path),
    }, indent=2))
    if seal["failed"]:
        raise SystemExit(2)
    if not args.allow_non_scientific_dev and not seal["sealed"]:
        raise SystemExit(3)
    print("PASS_R51_FINAL_SCIENTIFIC_SEAL_RUN" if seal["sealed"] else "PASS_R51_NON_SCIENTIFIC_DEV_SEAL_VALIDATION_RUN")


if __name__ == "__main__":
    main()
