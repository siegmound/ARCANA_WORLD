"""Input and governance contracts for the R6 pyGPlates mapping diagnostic."""
from __future__ import annotations

import numpy as np

EXPECTED_PLATE_COUNT = 12
EXPECTED_BOUNDARY_COUNT = 1983
EXPECTED_JUNCTION_COUNT = 20
EXPECTED_FACE_COUNT = 64800

REQUIRED_ARRAYS = {
    "face_row", "face_col", "face_vertex_latlon_deg", "face_plate_id",
    "boundary_edge_row", "boundary_edge_col", "boundary_edge_axis",
    "boundary_plate_a", "boundary_plate_b", "boundary_length_m",
}


def validate_mapping_inventory(manifest: dict, arrays: dict, census: dict) -> dict[str, int]:
    """Validate the source partition inventory without assigning physics."""
    missing = REQUIRED_ARRAYS.difference(arrays)
    if missing:
        raise ValueError(f"partition arrays missing required fields: {sorted(missing)}")

    face_count = len(arrays["face_plate_id"])
    boundary_count = len(arrays["boundary_plate_a"])
    if face_count != EXPECTED_FACE_COUNT:
        raise ValueError(f"expected {EXPECTED_FACE_COUNT} faces, found {face_count}")
    if boundary_count != EXPECTED_BOUNDARY_COUNT:
        raise ValueError(f"expected {EXPECTED_BOUNDARY_COUNT} boundaries, found {boundary_count}")
    if any(len(arrays[key]) != boundary_count for key in (
        "boundary_edge_row", "boundary_edge_col", "boundary_edge_axis",
        "boundary_plate_b", "boundary_length_m",
    )):
        raise ValueError("boundary arrays have inconsistent lengths")
    if arrays["face_vertex_latlon_deg"].shape != (face_count, 5, 2):
        raise ValueError("face vertex array has an unexpected geometry shape")

    plate_ids = {int(value) for value in arrays["face_plate_id"]}
    if len(plate_ids) != EXPECTED_PLATE_COUNT:
        raise ValueError(f"expected {EXPECTED_PLATE_COUNT} plates, found {len(plate_ids)}")
    junctions = census.get("junctions", [])
    junction_count = len(junctions)
    if junction_count != EXPECTED_JUNCTION_COUNT or census.get("junction_count") != junction_count:
        raise ValueError(f"expected {EXPECTED_JUNCTION_COUNT} junctions, found {junction_count}")
    if manifest.get("schema") != "R6_T0_VECTOR_PLATE_PARTITION_V1":
        raise ValueError("unexpected canonical partition schema")
    if manifest.get("topology", {}).get("plate_count") != EXPECTED_PLATE_COUNT:
        raise ValueError("manifest plate count does not match the expected R6 t0 inventory")
    if manifest.get("topology", {}).get("positive_length_boundary_edge_count") != boundary_count:
        raise ValueError("manifest boundary count does not match payload")
    if not np.isfinite(arrays["face_vertex_latlon_deg"]).all():
        raise ValueError("face vertex array contains nonfinite coordinates")
    lengths = arrays["boundary_length_m"]
    if not np.isfinite(lengths).all() or (lengths <= 0).any():
        raise ValueError("boundary lengths must be finite and positive")
    if not set(map(int, arrays["boundary_edge_axis"])).issubset({0, 1}):
        raise ValueError("boundary edge axis contains unsupported values")
    if not set(map(int, arrays["boundary_plate_a"])).issubset(plate_ids):
        raise ValueError("boundary side A references an unknown plate")
    if not set(map(int, arrays["boundary_plate_b"])).issubset(plate_ids):
        raise ValueError("boundary side B references an unknown plate")
    return {
        "face_count": face_count,
        "plate_count": len(plate_ids),
        "boundary_segment_count": boundary_count,
        "junction_count": junction_count,
    }


def governance_flags() -> dict[str, bool]:
    """Return immutable non-evolution guards for this diagnostic."""
    return {
        "canonical_state_changed": False,
        "forward_evolution": False,
        "dt_first_authorized": False,
        "w_model_selected": False,
        "rift_advanced": False,
        "pygplates_scientific_authority": False,
    }
