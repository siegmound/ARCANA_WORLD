"""Pure source topology tests, no fabricated source/physics claims."""
from __future__ import annotations
import copy
import pytest
from experiments.plate58_deforming_explore_v1.g2_g3_junction_source_guard import (
    SourceJunctionError, certify_regional_junction,
)


def source(extent: int, *, has_34587: bool = True):
    ids = [100000 + i for i in range((extent + 1) ** 2)]
    if has_34587:
        ids[len(ids)//2] = 34587
    incidence = [] if extent == 8 else [
        {"parent_node_id": 34587, "incident_plates": [5, 8, 11]}]
    iface = {
        "extent_cells_per_side": extent,
        "actual_3plus_plate_junctions": incidence,
        "triple_plate_junction_exists": bool(incidence),
    }
    return ids, iface


@pytest.mark.parametrize("has_34587", [False, True])
def test_eight_by_eight_parent_membership_not_a_triple(has_34587):
    ids, iface = source(8, has_34587=has_34587)
    result = certify_regional_junction(ids, iface, 8)
    assert result["source_parent_34587_in_footprint"] is has_34587
    assert result["source_actual_3plus_plate_junctions"] == []
    assert result["local_triple_parent_id"] is None
    assert result["physical_T1"] is None


def test_sixteen_by_sixteen_true_source_three_plate_incidence():
    ids, iface = source(16)
    result = certify_regional_junction(ids, iface, 16)
    assert result["local_triple_parent_id"] == 34587
    assert result["source_actual_3plus_plate_junctions"][0]["incident_plates"] == [5, 8, 11]
    assert result["source_junction_is_not_fault_slip_dof"] is True
    assert result["mechanical_solve_authorized"] is False


@pytest.mark.parametrize("attack", [
    "wrong_extent", "inconsistent_boolean", "synthetic_8x8_triple",
    "missing_16x16_triple", "wrong_plates", "duplicate_plate",
    "missing_parent", "noninteger_id", "duplicate_parent",
    "missing_incident_plates", "fake_extra_key", "fake_fourth_plate",
])
def test_invalid_source_junction_cannot_pass(attack):
    extent = 8 if attack == "synthetic_8x8_triple" else 16
    ids, iface = source(extent)
    if attack == "wrong_extent":
        iface["extent_cells_per_side"] = 8
    elif attack == "inconsistent_boolean":
        iface["triple_plate_junction_exists"] = False
    elif attack == "synthetic_8x8_triple":
        iface["actual_3plus_plate_junctions"] = [{
            "parent_node_id": 34587, "incident_plates": [5, 8, 11]}]
        iface["triple_plate_junction_exists"] = True
    elif attack == "missing_16x16_triple":
        iface["actual_3plus_plate_junctions"] = []
        iface["triple_plate_junction_exists"] = False
    elif attack == "wrong_plates":
        iface["actual_3plus_plate_junctions"][0]["incident_plates"] = [5, 8, 12]
    elif attack == "duplicate_plate":
        iface["actual_3plus_plate_junctions"][0]["incident_plates"] = [5, 8, 8]
    elif attack == "missing_parent":
        ids[ids.index(34587)] = 77777
    elif attack == "noninteger_id":
        ids[0] = 1.0
    elif attack == "duplicate_parent":
        ids[0] = ids[1]
    elif attack == "missing_incident_plates":
        del iface["actual_3plus_plate_junctions"][0]["incident_plates"]
    elif attack == "fake_extra_key":
        iface["actual_3plus_plate_junctions"][0]["slip_dof"] = 1
    elif attack == "fake_fourth_plate":
        iface["actual_3plus_plate_junctions"][0]["incident_plates"] = [5, 8, 11, 12]
    with pytest.raises((SourceJunctionError, KeyError)):
        certify_regional_junction(ids, iface, extent)
