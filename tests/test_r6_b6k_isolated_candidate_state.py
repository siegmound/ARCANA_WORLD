from __future__ import annotations

import math
import json
from pathlib import Path

import numpy as np
import pytest

from arcana_worldsim.r6.b6k_candidate import (
    DT_YEARS, TARGET_AGE_MA, build_plate_local_positions,
    candidate_identity, deterministic_payload, target_age, topology_identity,
)
from arcana_worldsim.r6.finite_rotation import rotate_vector_constant_euler

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "outputs/r6_b6k_isolated_first_candidate_state"


def test_b6j_binary_dt_reproduces_exact_planning_target():
    assert DT_YEARS.hex() == "0x1.a7cd9ee14b895p+14"
    assert target_age(210.0, DT_YEARS) == TARGET_AGE_MA


def test_positive_z_is_active_right_handed_and_exact():
    rotated = rotate_vector_constant_euler((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), math.pi / 2)
    assert rotated[0] == pytest.approx(0.0, abs=3e-16)
    assert rotated[1] == pytest.approx(1.0, abs=3e-16)
    assert rotated[2] == 0.0


def test_shared_interface_node_has_distinct_plate_local_side_coordinates():
    vertices = np.asarray([[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]])
    pairs, xyz = build_plate_local_positions(vertices_lat_lon=vertices,
        face_node_ids=((1, 2, 3), (2, 4, 3)), face_plate_ids=(1, 2),
        plate_omega={1: (0.0, 0.0, 1e-5), 2: (0.0, 0.0, -1e-5)}, elapsed_years=1000.0)
    lookup = {pair: xyz[index] for index, pair in enumerate(pairs)}
    assert (2, 1) in lookup and (2, 2) in lookup
    assert not np.array_equal(lookup[(2, 1)], lookup[(2, 2)])


def test_deterministic_binary_payload_and_candidate_identity():
    pairs = ((1, 1), (1, 2))
    xyz = np.asarray([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    first = deterministic_payload(pairs, xyz)
    second = deterministic_payload(pairs, xyz.copy())
    assert first == second
    common = dict(source_t0_identity="a" * 64, model_identity="b" * 64,
        dt_hex=DT_YEARS.hex(), target_age_ma=TARGET_AGE_MA,
        topology_id="c" * 64, candidate_payload_sha256="d" * 64)
    assert candidate_identity(**common) == candidate_identity(**common)


def test_candidate_binary_rejects_nonfinite_or_wrong_shape():
    with pytest.raises(ValueError):
        deterministic_payload(((1, 1),), np.asarray([[math.nan, 0.0, 0.0]]))
    with pytest.raises(ValueError):
        deterministic_payload(((1, 1),), np.zeros((2, 3)))


def test_topology_identity_is_independent_of_candidate_coordinates():
    kwargs = dict(triangles=np.asarray([[1, 2, 3]]), triangle_plate_ids=np.asarray([1]),
        boundary_descriptors=({"boundary_id": "B-1"},), junction_node_ids=(("J-1", 1),))
    assert topology_identity(**kwargs) == topology_identity(**kwargs)


def test_missing_plate_euler_authority_fails_closed():
    with pytest.raises(ValueError, match="no governed Euler vector"):
        build_plate_local_positions(vertices_lat_lon=np.asarray([[0.0, 0.0]]),
            face_node_ids=((1, 1, 1),), face_plate_ids=(99,), plate_omega={}, elapsed_years=1.0)


def test_retained_candidate_preserves_junction_sides_and_topology_hold():
    junctions = json.loads((EVIDENCE / "B6K_JUNCTION_CANDIDATE.json").read_text(encoding="utf-8"))
    topology = json.loads((EVIDENCE / "B6K_TOPOLOGY_HOLD.json").read_text(encoding="utf-8"))
    assert junctions["junction_count"] == 20
    assert junctions["side_count"] == 60
    assert all(len(row["incident_plate_ids"]) >= 3 and
               len(row["sides"]) == len(row["incident_plate_ids"]) for row in junctions["junctions"])
    assert topology["pre_transition_topology_identity"] == topology["candidate_topology_identity"]
    assert topology["transition_executed"] is False


def test_event_endpoint_is_candidate_only_and_transition_is_not_executed():
    event = json.loads((EVIDENCE / "B6K_EVENT_BOUNDARY.json").read_text(encoding="utf-8"))
    result = json.loads((EVIDENCE / "B6K_RESULT.json").read_text(encoding="utf-8"))
    assert event["predicate_status"] == "PREDICATE_SATISFIED_ACTIVATION_POSSIBLE"
    assert event["transition_status"] == "NOT_EXECUTED"
    assert result["dt_selected"] is True
    assert result["topology_transition_executed"] is False
    assert result["t1_created"] is False
    assert result["canonical_state_changed"] is False
    assert result["mechanics_authorized"] is False
    assert result["shellset_executed"] is False
    assert result["orbdata_mechanics_executed"] is False


def test_isolated_store_temporal_and_unknown_queries_are_retained():
    integration = json.loads((EVIDENCE / "B6K_WORLD_HISTORY_INTEGRATION.json").read_text(encoding="utf-8"))
    queries = json.loads((EVIDENCE / "B6K_QUERY_PREACCEPTANCE.json").read_text(encoding="utf-8"))
    assert integration["append_reopen"] is True
    assert integration["temporal_validity_record_status"] == "CANDIDATE_VALIDATED"
    assert queries["UNKNOWN"] == "PASS"
    assert queries["TEMPORAL_VALIDITY"] == "PASS"


def test_unknown_transfers_are_neither_imputed_nor_called_t1():
    transfer = json.loads((EVIDENCE / "B6K_STATE_TRANSFER.json").read_text(encoding="utf-8"))
    result = json.loads((EVIDENCE / "B6K_RESULT.json").read_text(encoding="utf-8"))
    assert transfer["no_interpolation"] is True
    assert transfer["no_imputation"] is True
    assert result["candidate_state_status"] == "PRE_TRANSITION_EVENT_BOUNDARY_CANDIDATE"
    assert result["candidate_acceptance_gate"] == "CANDIDATE_FIRST_STEP_VALIDATED"


def test_canonical_feg_and_runtime_artifacts_are_hash_frozen():
    frozen = json.loads((EVIDENCE / "B6K_SOURCE_FREEZE.json").read_text(encoding="utf-8"))
    immutability = json.loads((EVIDENCE / "B6K_CANONICAL_IMMUTABILITY.json").read_text(encoding="utf-8"))
    for relative in ("R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg",
                    "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"):
        assert frozen["source_snapshot_before"][relative] == frozen["source_snapshot_after"][relative]
    assert immutability["status"] == "CANONICAL_SOURCE_UNCHANGED"
    assert frozen["runtime_artifact_scope"] == "hashed_for_immutability_only; not read as candidate input"
