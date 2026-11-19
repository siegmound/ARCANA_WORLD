#!/usr/bin/env python3
"""Prepared bounded child probe. Not executed by the P1 preparation gate."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["native", "pair"], required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-input-sha256", required=True)
    parser.add_argument("--target-year", type=int, choices=[3, 10], required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(root / "experiments"), str(root / "src")]
    from hr2_p1.checkpoint import PairStore, load_native, save_native
    from hr2_p1.manufactured import advance_annual
    from hr2_p1.model import Parameters, require
    file = args.input if args.mode == "native" else args.input / "CONTEXT.json"
    require(hashlib.sha256(file.read_bytes()).hexdigest() == args.expected_input_sha256,
            "CHILD_INPUT_IDENTITY_MISMATCH")
    if args.mode == "native":
        case = load_native(args.input)
    else:
        context = json.loads(file.read_bytes())
        store = PairStore(args.input, Parameters(**context["parameters"]),
                          context["mesh_sha256"], context["run_id"],
                          initial_identity_sha256=context["initial_identity_sha256"], reopen=True)
        case = store.read_latest()
    require(case.parameters.planned_end_year == args.target_year, "CHILD_PLANNED_HORIZON_MISMATCH")
    advance_annual(case, args.target_year)
    save_native(args.output, case)
    print(json.dumps({"status": "PASS_BOUNDED_MANUFACTURED_CHILD_CONTINUATION",
                      "year": case.year, "accepted_steps": case.accepted_steps,
                      "native_sha256": case.checkpoint()["sha256"],
                      "scientific_authority": False}))


if __name__ == "__main__":
    main()
