#!/usr/bin/env python3
"""Create and verify the isolated SI1-BW1 reordered input pair."""

from __future__ import annotations

import argparse
from pathlib import Path

from arcana_worldsim.r6.si1_bandwidth_bw1 import (
    DEFAULT_FEG,
    DEFAULT_FEG_MANIFEST,
    DEFAULT_PACKAGE,
    OUTPUT_ROOT,
    materialize,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feg", type=Path, default=DEFAULT_FEG)
    parser.add_argument("--runtime-package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--feg-manifest", type=Path, default=DEFAULT_FEG_MANIFEST)
    parser.add_argument("--runtime-manifest", type=Path, default=DEFAULT_PACKAGE.with_suffix(".json"))
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()
    try:
        result = materialize(args.feg, args.runtime_package, args.feg_manifest, args.runtime_manifest, args.output_dir)
    except (OSError, ValueError, KeyError, IndexError) as exc:
        parser.exit(2, f"BW1_FAIL_CLOSED: {exc}\n")
    print(f"BW1_DECISION={result['decision']}")
    print(f"BW1_NODES={result['counts']['nodes']}")
    print(f"BW1_TRIANGLES={result['counts']['triangles']}")
    print(f"BW1_NCODIAGONALS={result['ksize']['reordered']['nCodiagonals']}")
    print(f"BW1_MATRIX_BYTES={result['ksize']['reordered']['matrix_bytes']}")
    print(f"BW1_REPORT={args.output_dir / 'reports' / 'BW1_REPORT.json'}")
    print(f"BW1_FAIR_CONTRACT={args.output_dir / 'fair_staging' / 'BW1_FAIR_PREFLIGHT_CONTRACT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
