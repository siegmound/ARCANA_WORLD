from __future__ import annotations

import pytest

from arcana_worldsim.r6.plate_support_adapter import (
    PlateNodeMappingError, build_fixture_topology_events,
    derive_node_plate_support,
)
from arcana_worldsim.r6.plate_kinematics_adapter import (
    PlateGridMappingUnavailable, ReferenceFrameMismatch, SyntheticKinematicSegment,
    UnsupportedTemporalSupport, require_plate_grid_mapping, validate_fixture_interval,
)


def _tiny_support():
    return derive_node_plate_support(
        face_plate_ids=(0, 1, 2),
        face_node_ids=((1, 2, 3), (1, 3, 4), (3, 4, 5)),
        boundary_edges=((1, 3), (3, 4)),
        junction_node_ids=(3,), node_count=6,
        expected_plate_ids=(0, 1, 2),
    )


def test_node_support_keeps_boundary_junction_sets_and_unknown():
    result = _tiny_support()
    assert result.node_plate_ids == ((0, 1), (0,), (0, 1, 2), (1, 2), (2,), ())
    assert result.counts == {
        "INTERIOR_PLATE": 2,
        "BOUNDARY_SHARED": 2,
        "JUNCTION_SHARED": 1,
        "UNKNOWN": 1,
    }
    assert result.payload_sha256
    assert result.mapping_identity_sha256


def test_node_support_rejects_unmarked_multiplate_ambiguity():
    with pytest.raises(PlateNodeMappingError, match="ambiguous node support"):
        derive_node_plate_support(
            face_plate_ids=(0, 1), face_node_ids=((1, 2, 3), (1, 4, 5)),
            boundary_edges=(), junction_node_ids=(), node_count=5,
            expected_plate_ids=(0, 1),
        )


def test_node_support_rejects_junction_not_in_boundary_graph():
    with pytest.raises(PlateNodeMappingError, match="junction identities"):
        derive_node_plate_support(
            face_plate_ids=(0,), face_node_ids=((1, 2, 3),),
            boundary_edges=(), junction_node_ids=(2,), node_count=3,
            expected_plate_ids=(0,),
        )


def test_topology_event_cases_are_deterministic_and_fixture_only():
    events_a, provenance_a, state_a = build_fixture_topology_events()
    events_b, provenance_b, state_b = build_fixture_topology_events()
    types = [event.details["event_type"] for event in events_a]
    assert types == ["PLATE_SPLIT", "PLATE_MERGE", "BOUNDARY_BIRTH",
                     "BOUNDARY_DEATH", "JUNCTION_REASSIGNMENT"]
    assert [event.record_id for event in events_a] == [event.record_id for event in events_b]
    assert str(provenance_a.record_id) == str(provenance_b.record_id)
    assert str(state_a.state_id) == str(state_b.state_id)
    assert set(state_a.event_refs) == {event.record_id for event in events_a}
    assert all(event.details["fixture_only"] is True for event in events_a)
    assert all(event.details["actual_arcana_event"] is False for event in events_a)
    assert all(event.details["parent_history_mutated"] is False for event in events_a)


def test_node_support_serialization_preserves_set_valued_membership():
    result = _tiny_support()
    decoded = __import__("json").loads(result.payload_bytes)
    assert decoded["node_plate_masks"][0] == (1 << 0) | (1 << 1)
    assert decoded["physical_node_assignment"] is False
    assert decoded["support_kind_code_by_node"][-1] == 3


def test_missing_plate_grid_mapping_fails_closed():
    with pytest.raises(PlateGridMappingUnavailable, match="not provided"):
        require_plate_grid_mapping(None)


def test_fixture_interval_rejects_frame_mismatch_and_unsupported_interval():
    segment = SyntheticKinematicSegment(211.0, 210.0, "FIXTURE_SEGMENT",
        "FIXTURE_GAUGE", {0: (0.0, 0.0, 0.0)})
    with pytest.raises(ReferenceFrameMismatch):
        validate_fixture_interval(211.0, 210.0, (segment,), (0,), "OTHER_GAUGE")
    with pytest.raises(UnsupportedTemporalSupport):
        validate_fixture_interval(212.0, 210.0, (segment,), (0,), "FIXTURE_GAUGE")
