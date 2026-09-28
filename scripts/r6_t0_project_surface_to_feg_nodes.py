#!/usr/bin/env python3
"""Prepare deterministic NUMERICAL_DERIVED_SUPPORT FEG nodal projections."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

from arcana_worldsim.r6.repository_context import resolve_external_payload_path
from arcana_worldsim.r6.shellset_mesh.adapter import load_canonical_mesh, project_cell_field_to_nodes

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE_SURFACE_CLOSED.npz"
PACKAGE_SHA = "31cf4fb77e6fc12df1716805eeb4b46059ca35bbcd7b3bc305efa2e8afef3534"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "R6_T0_ORBDATA_FEG_NODE_PROJECTIONS.json")
    args = parser.parse_args()
    package = ROOT / PACKAGE_NAME
    if hashlib.sha256(package.read_bytes()).hexdigest() != PACKAGE_SHA:
        raise SystemExit("surface-closed field package SHA mismatch")
    mesh = load_canonical_mesh(ROOT)
    manifest = json.loads((ROOT / "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json").read_text())
    payload = resolve_external_payload_path(ROOT, manifest["payload"]["path"])
    with np.load(payload, allow_pickle=False) as archive:
        rows, cols = archive["face_row"].copy(), archive["face_col"].copy()
    with np.load(package, allow_pickle=False) as fields:
        surface = project_cell_field_to_nodes(
            mesh, rows, cols, fields["total_surface_elevation_m"].copy(),
            unknown_mask=fields["unknown_total_ocean_elevation_mask"].copy())
        domain = project_cell_field_to_nodes(
            mesh, rows, cols, fields["physical_crust_domain_id"].copy(), categorical=True)
    result = {
        "schema": "R6_T0_ORBDATA_FEG_NODE_PROJECTION_PACKAGE_V1",
        "classification": "NUMERICAL_DERIVED_SUPPORT",
        "mesh_sha256": "6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad",
        "field_package_sha256": PACKAGE_SHA,
        "node_count": 64442,
        "total_surface_elevation_m": surface,
        "physical_crust_domain_id": domain,
        "limitations": ["source-cell lineage retained per node", "UNKNOWN and mixed category support retained",
                        "no resolution increase", "no smoothing", "existing mesh projection only"],
    }
    result["replay_sha256"] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Projection materialized; replay_sha256={result['replay_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
