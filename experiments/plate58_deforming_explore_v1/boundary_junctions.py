"""Read-only source-velocity compatibility audit at plate 5:8 N/S cut exits.

Not a boundary condition builder. In particular no Euler velocities are
prescribed at shared nodes and no basal/material loads are assigned.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from arcana_worldsim.r6.shellset_mesh.adapter import load_canonical_mesh
from experiments.plate58_deforming_explore_v1.check_envelope import verify
from experiments.plate58_deforming_explore_v1.prepare import (
    EULER, ROOT, SECONDS_YEAR, _frame_velocity, require, sha,
)

STATUS = "PASS_G3_EXIT_NODE_INCOMPATIBILITY_IDENTIFIED__SOLVE_BLOCKED"
NUMERICAL_IDENTITY_TOL_M_YEAR = 1.0e-10  # rounding guard, NOT geological tolerance


def compare_euler_at_one_node(velocity_8_south_east_m_s, velocity_5_south_east_m_s):
    """Check whether two source Euler DOF prescriptions can share one FEG node."""
    v8 = np.asarray(velocity_8_south_east_m_s, dtype=float)
    v5 = np.asarray(velocity_5_south_east_m_s, dtype=float)
    require(v8.shape == (2,) and v5.shape == (2,) and
            bool(np.all(np.isfinite(v8))) and bool(np.all(np.isfinite(v5))),
            "INVALID_PLATE_EULER_VELOCITY")
    delta = v5 - v8
    speed_m_year = float(np.linalg.norm(delta) * SECONDS_YEAR)
    return {
        "source_plate_8_south_east_m_s": [float(x) for x in v8],
        "source_plate_5_south_east_m_s": [float(x) for x in v5],
        "plate5_minus_plate8_south_east_m_s": [float(x) for x in delta],
        "relative_euler_speed_m_per_year": speed_m_year,
        "dual_euler_dirichlet_at_single_node_compatible":
            speed_m_year <= NUMERICAL_IDENTITY_TOL_M_YEAR,
        "tolerance_only_for_numerical_identity_m_per_year":
            NUMERICAL_IDENTITY_TOL_M_YEAR,
    }


def audit(envelope_folder: Path):
    """Verify existing immutable evidence and examine, never prescribe, exit DOFs."""
    verify(envelope_folder)
    report = json.loads((envelope_folder / "NEIGHBORHOOD.json").read_text())
    source = report["boundary_analysis"]
    mesh = load_canonical_mesh(ROOT)
    require(mesh.normalized_sha256 == report["source_mesh_identity_sha256"],
            "SOURCE_MESH_CHANGED")
    require(sha(ROOT / EULER) == report["source_euler_sha256"],
            "SOURCE_EULER_CHANGED")
    euler = json.loads((ROOT / EULER).read_text())
    omega = {int(row["plate_id"]): row["euler_vector_rad_per_year"]
             for row in euler["plates"]}
    require(5 in omega and 8 in omega, "PLATE58_EULER_MISSING")

    junctions = []
    for side in ("north", "south"):
        end_nodes = source["source_interface_meets_outer_cut_parent_nodes"][side]
        require(len(end_nodes) == 1, "CONTACT_EXIT_MULTIPLE_OR_MISSING:" + side)
        parent_node_id = int(end_nodes[0])
        adjacent = [row for row in source["side_segments"][side]
                    if parent_node_id in row["parent_node_ids"]]
        owners = {int(row["adjacent_plate_id"]) for row in adjacent}
        require(owners == {5, 8} and len(adjacent) == 2,
                "CONTACT_EXIT_NOT_DUAL_PLATE:" + side)
        lat_lon = [float(x) for x in mesh.vertices_lat_lon[parent_node_id - 1]]
        frame8, speed8 = _frame_velocity(omega[8], [lat_lon])
        frame5, speed5 = _frame_velocity(omega[5], [lat_lon])
        require(bool(np.allclose(frame8, frame5, rtol=0, atol=1e-12)),
                "NUMERICAL_FRAME_INCONSISTENT")
        difference = compare_euler_at_one_node(speed8[0], speed5[0])
        require(not difference["dual_euler_dirichlet_at_single_node_compatible"],
                "EXPECTED_SOURCE_DIFFERENTIAL_MOTION_ABSENT:" + side)
        junctions.append({
            "side": side,
            "parent_node_id": parent_node_id,
            "canonical_lat_lon_deg": lat_lon,
            "SHELLS_lat_lon_deg": [float(x) for x in frame8[0]],
            "adjacent_plate_ids": sorted(owners),
            **difference,
            "single_shared_FEG_node": True,
            "prescribed_velocity": None,
            "exterior_traction": None,
        })
    require(len(junctions) == 2 and
            source["side_plate_ownership"]["north"] == [8, 5, 5, 5] and
            source["side_plate_ownership"]["south"] == [8, 8, 8, 5],
            "SOURCE_BOUNDARY_OWNERSHIP_CHANGED")
    return {
        "status": STATUS,
        "input_evidence": str(envelope_folder),
        "source_euler_sha256": report["source_euler_sha256"],
        "north_south_junctions": junctions,
        "diagnostic_conclusion":
            "A continuous FEG node cannot accept two distinct Euler Dirichlet vectors",
        "allowed_mechanical_boundary_condition": None,
        "north_south_traction": None,
        "basal_normal_support": None,
        "G2_material_coefficients": None,
        "mechanical_solve_authorized": False,
        "solver_runs": 0,
        "first_deforming_T1": None,
        "next_physical_requirement":
            "Specify exterior continuum continuation and constitutive/basal "
            "closure; alternatively authorize an explicit discontinuity law. "
            "Kinematic Euler samples do not supply these conditions.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("envelope_folder", type=Path)
    print(json.dumps(audit(parser.parse_args().envelope_folder), indent=2,
                     sort_keys=True, allow_nan=False))
