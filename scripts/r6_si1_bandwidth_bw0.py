#!/usr/bin/env python3
"""Run the read-only SI1-BW0 mesh bandwidth diagnostic."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from arcana_worldsim.r6.si1_bandwidth import (
    DEFAULT_FEG,
    DEFAULT_FEG_MANIFEST,
    DEFAULT_OUTPUT,
    DEFAULT_PACKAGE,
    REPO_ROOT,
    analyze,
    write_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feg", type=Path, default=DEFAULT_FEG)
    parser.add_argument("--runtime-package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_FEG_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        report = analyze(args.feg, args.runtime_package, args.manifest, REPO_ROOT)
        json_path, markdown_path = write_report(report, args.output_dir)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(2, f"BW0_FAIL_CLOSED: {exc}\n")
    original = report["shellset_ksize"]["original"]
    rcm = report["shellset_ksize"]["rcm"]
    print(f"BW0_NUM_NOD={report['counts']['numNod']}")
    print(f"BW0_NUM_EL={report['counts']['numEl']}")
    print(f"BW0_NFL={report['counts']['nFl']}")
    print(f"BW0_ORIGINAL_NCODIAGONALS={original['nCodiagonals']}")
    print(f"BW0_ORIGINAL_MATRIX_BYTES={original['matrix_bytes']}")
    print(f"BW0_RCM_NCODIAGONALS={rcm['nCodiagonals']}")
    print(f"BW0_RCM_MATRIX_BYTES={rcm['matrix_bytes']}")
    print(f"BW0_JSON={json_path}")
    print(f"BW0_MARKDOWN={markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
