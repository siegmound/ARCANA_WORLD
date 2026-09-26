"""Governance and cardinality contracts for the P2.2 topology probe."""
from __future__ import annotations

from typing import Any

EXPECTED_PLATES = 12
EXPECTED_FACES = 64_800
EXPECTED_BOUNDARIES = 1_983
EXPECTED_JUNCTIONS = 20


def validate_topology_input(data: Any) -> dict[str, int]:
    """Validate the manifested P2 input without interpreting its physics."""
    inventory = data.inventory
    expected = {
        "plate_count": EXPECTED_PLATES,
        "face_count": EXPECTED_FACES,
        "boundary_segment_count": EXPECTED_BOUNDARIES,
        "junction_count": EXPECTED_JUNCTIONS,
    }
    for key, count in expected.items():
        if inventory.get(key) != count:
            raise ValueError(f"{key} expected {count}, found {inventory.get(key)}")
    if any(record.get("degree") != 3 for record in data.junction_census["junctions"]):
        raise ValueError("canonical junction census contains a non-degree-3 record")
    if any(len(record.get("incident_plate_ids", ())) != 3
           for record in data.junction_census["junctions"]):
        raise ValueError("canonical junction record does not identify three incident plates")
    return {
        "plate_count": EXPECTED_PLATES,
        "face_count": EXPECTED_FACES,
        "boundary_segment_count": EXPECTED_BOUNDARIES,
        "junction_count": EXPECTED_JUNCTIONS,
    }


def governance_flags() -> dict[str, bool]:
    """Hard-coded false guards: this diagnostic cannot advance canonical R6."""
    return {
        "canonical_state_changed": False,
        "rotations_assigned": False,
        "velocity_field_created": False,
        "strain_created": False,
        "w_model_selected": False,
        "dt_authorized": False,
        "forward_evolution": False,
        "pygplates_scientific_authority": False,
    }
