#!/usr/bin/env python3
"""Materialize production ShellSet FEG support; never execute ShellSet."""
from __future__ import annotations

from pathlib import Path

from arcana_worldsim.r6.shellset_mesh.materialization import write_production_feg

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    result = write_production_feg(ROOT)
    print(result["decision"])
    print(f"FEG={ROOT / 'R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
