from __future__ import annotations

import subprocess
from pathlib import Path
from _git_test_env import isolated_git_environment

import pytest

from arcana_worldsim.r6.identity import BranchId, HistoryId
from arcana_worldsim.r6.plate_kinematics_adapter import (
    GovernedPlateKinematics,
    KinematicsAuthorityError,
    PlateGridMappingUnavailable,
    ReferenceFrameMismatch,
    SyntheticKinematicSegment,
    TIME_210,
    UnknownPlateSupport,
    UnsupportedTemporalSupport,
    _tracked_identity,
    build_t0_records,
    require_interval_coverage,
    require_plate_grid_mapping,
    synthetic_fixture_forcing,
    validate_fixture_interval,
)
from arcana_worldsim.r6.query import HistoryQueryService
from arcana_worldsim.r6.state import TimeSupport
from arcana_worldsim.r6.store import HistoryStore


FRAME = "FIXTURE_FRAME"


def _source() -> GovernedPlateKinematics:
    return GovernedPlateKinematics(
        repository_root=Path("."),
        branch="fixture", head="fixture", history_id=str(HistoryId.from_payload({"h": 4})),
        branch_id=str(BranchId.from_payload({"b": 4})), time_ma=210.0,
        reference_frame=FRAME, authority_class="STOCHASTIC_CANONICAL_MODEL_REALIZATION",
        canonical_identity_sha256="a" * 64, artifact_sha256="b" * 64,
        source_uncertainty={"class": "FIXTURE_UNCERTAINTY"}, plates=(
            {"plate_id": 3, "euler_vector_rad_per_year": [1e-9, 2e-9, 3e-9]},
            {"plate_id": 8, "euler_vector_rad_per_year": [-1e-9, 0.0, 2e-9]},
        ), topology_plate_ids=(3, 8), face_count=12, boundary_count=4,
        adjacent_pair_count=1, source_refs=("fixture-only:source",), payload_sources=())


def _segments():
    return (
        SyntheticKinematicSegment(210.0, 205.0, "older", FRAME,
            {3: (1e-9, 0.0, 0.0), 8: (0.0, 1e-9, 0.0)}),
        SyntheticKinematicSegment(205.0, 200.0, "younger", FRAME,
            {3: (2e-9, 0.0, 0.0), 8: (0.0, 2e-9, 0.0)}),
    )


def test_real_adapter_record_identity_and_authority_are_deterministic():
    source = _source()
    left = build_t0_records(source)
    right = build_t0_records(source)
    assert left.forcing.forcing_id == right.forcing.forcing_id
    assert left.driver_payload_identity_sha256 == right.driver_payload_identity_sha256
    assert left.forcing.time_support == TIME_210
    assert left.forcing.authority_class.value == "DERIVED_AUTHORITY"
    assert left.forcing.value["source_authority_class"] == source.authority_class
    assert left.forcing.value["temporal_validity"].startswith("EXACT_T0_INSTANT_ONLY")
    assert left.forcing.value["geometry_transform_performed"] is False
    assert left.forcing.value["canonical_state_changed"] is False
    assert left.forcing.value["spatial_plate_support"]["grid_or_mesh_node_membership"] == "NOT_PROVIDED"


def test_t0_adapter_rejects_unknown_plate_frame_and_interval():
    source = _source()
    with pytest.raises(UnknownPlateSupport):
        build_t0_records(source, requested_plate_ids=(3, 99))
    with pytest.raises(ReferenceFrameMismatch):
        build_t0_records(source, requested_reference_frame="EARTH_FIXED")
    with pytest.raises(UnsupportedTemporalSupport):
        build_t0_records(source, requested=TimeSupport(
            "210Ma/205Ma", "R6_GLOBAL_MA_OLDER_TO_YOUNGER", "INTERVAL"))
    with pytest.raises(UnsupportedTemporalSupport):
        require_interval_coverage(source, 210.0, 205.0)
    with pytest.raises(PlateGridMappingUnavailable):
        require_plate_grid_mapping(None)


def test_fixture_piecewise_regimes_and_boundary_are_explicitly_fixture_only():
    segments = _segments()
    older, = validate_fixture_interval(210.0, 205.0, segments, (3, 8), FRAME)
    younger, = validate_fixture_interval(205.0, 200.0, segments, (3,), FRAME)
    assert older.segment_id == "older"
    assert younger.segment_id == "younger"
    force1 = synthetic_fixture_forcing(older)
    force2 = synthetic_fixture_forcing(older)
    assert force1.forcing_id == force2.forcing_id
    assert force1.support_class.value == "FIXTURE_ONLY"
    assert force1.authority_class.value == "FIXTURE_ONLY"
    with pytest.raises(UnsupportedTemporalSupport):
        validate_fixture_interval(210.0, 200.0, segments, (3,), FRAME)
    with pytest.raises(UnknownPlateSupport):
        validate_fixture_interval(210.0, 205.0, segments, (44,), FRAME)
    with pytest.raises(ReferenceFrameMismatch):
        validate_fixture_interval(210.0, 205.0, segments, (3,), "OTHER_FRAME")
    altered_younger = SyntheticKinematicSegment(205.0, 200.0, "younger",
        "OTHER_FRAME", {8: (0.0, 2e-9, 0.0)})
    with pytest.raises(ReferenceFrameMismatch):
        validate_fixture_interval(205.0, 200.0, (segments[0], altered_younger), (8,), FRAME)
    with pytest.raises(UnknownPlateSupport):
        validate_fixture_interval(205.0, 200.0, (segments[0], altered_younger), (3,), "OTHER_FRAME")


def test_transaction_reopen_and_why_reaches_forcing(tmp_path):
    records = build_t0_records(_source())
    store = HistoryStore(tmp_path / "store")
    store.append_transaction((records.source_provenance, records.forcing,
                              records.adapter_provenance, records.index_state))
    del store
    reopened = HistoryStore(tmp_path / "store")
    state = reopened.read_state(str(records.index_state.state_id))
    why = HistoryQueryService(reopened).why(str(state.state_id))
    assert [str(item.forcing_id) for item in why.forcings] == [str(records.forcing.forcing_id)]
    assert not why.unresolved_references


def test_source_binding_tracks_git_blob_and_rejects_worktree_edit(tmp_path, monkeypatch):
    monkeypatch.delenv("GIT_OBJECT_DIRECTORY", raising=False)
    monkeypatch.delenv("GIT_ALTERNATE_OBJECT_DIRECTORIES", raising=False)
    isolated_env = isolated_git_environment()
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True,
                   env=isolated_env)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=Fixture",
                    "-c", "user.email=fixture@example.invalid", "config", "core.autocrlf", "false"],
                   check=True, capture_output=True, env=isolated_env)
    source = tmp_path / "authority.json"
    source.write_text('{"authority":"fixture"}\n', encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "authority.json"], check=True,
                   env=isolated_env)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=Fixture",
                    "-c", "user.email=fixture@example.invalid", "commit", "-m", "fixture"],
                   check=True, capture_output=True, env=isolated_env)
    row = _tracked_identity(tmp_path, "authority.json")
    assert row["role"] == "TRACKED_AUTHORITY_OR_EVIDENCE"
    source.write_text('{"authority":"changed"}\n', encoding="utf-8")
    with pytest.raises(KinematicsAuthorityError):
        _tracked_identity(tmp_path, "authority.json")
