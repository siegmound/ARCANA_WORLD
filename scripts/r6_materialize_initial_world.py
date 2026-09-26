#!/usr/bin/env python3
"""Generate, validate and register the governed R6 physical initial state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from arcana_worldsim.r6.initial_world.materialize import materialize_initial_world
from arcana_worldsim.r6.repository_context import external_root


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-root", type=Path,
                        help="External immutable payload root; defaults to sibling _ARCANA_EXTERNAL_SOURCES/r6/initial_world")
    parser.add_argument("--skip-sensitivity", action="store_true",
                        help="Do not run the required non-canonical alternate-seed sensitivity check")
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    output = args.output_root or (external_root(repo) / "r6" / "initial_world")
    result = materialize_initial_world(repo, output, perform_sensitivity=not args.skip_sensitivity)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
