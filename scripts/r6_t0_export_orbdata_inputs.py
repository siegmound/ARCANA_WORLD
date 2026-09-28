#!/usr/bin/env python3
"""Export governed T0 field package grids for OrbData input staging."""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np

from arcana_worldsim.r6.shellset_mesh.orbdata import write_orbdata_grids

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE_SURFACE_CLOSED.npz"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    with np.load(PACKAGE, allow_pickle=False) as archive:
        fields = {key: archive[key].copy() for key in (
            "oceanic_lithosphere_age_ma", "crustal_thickness_m", "physical_crust_domain_id",
            "continental_reference_lithosphere_thickness_m")}
    report = write_orbdata_grids(fields, args.output_dir)
    print(f"Exported numerical OrbData support; replay_identity={report['replay_identity']}")
    print("PRE_ORBDATA remains false; qArray/configuration and FEG materialization remain gated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
