from __future__ import annotations

import json
import os
from pathlib import Path
import shutil

import pytest

from arcana_worldsim.r6.b6n8a_shadow import (
    LABELS,
    OBSERVABLE_REGISTRY,
    REVALIDATION_HORIZON_YEARS,
    POST_EVENT_ID,
    _preflight_live_canonical_store,
    canonical_snapshot,
    compute_multiresolution,
)


def _fixture():
    # Unit-sphere synthetic inputs only; not a substitute for governed B6K run.
    nodes = [
        (10, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        (11, (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
    ]
    omega = {1: (0.0, 0.0, 1.0e-8), 3: (0.0, 0.0, -2.0e-8)}
    return nodes, omega


def test_resolutions_restart_from_identical_initial_state_and_internal_dt_is_not_interval():
    nodes, omega = _fixture()
    result = compute_multiresolution(nodes, omega, horizon_years=1000.0, window_fraction=0.2)
    levels = result["resolution_ladder"]
    assert [row["step_count"] for row in levels] == [4, 8, 16, 32]
    assert len({row["initial_state_coordinate_sha256"] for row in levels}) == 1
    assert all(row["internal_dt_is_persistent_interval"] is False for row in levels)
    assert len({row["internal_dt_years"] for row in levels}) == 4
    assert all(row["sample_count"] == 5 for row in levels)


def test_shadow_scope_is_noncanonical_conditional_and_physically_limited():
    nodes, omega = _fixture()
    result = compute_multiresolution(nodes, omega, horizon_years=1000.0)
    assert result["semantic_labels"] == LABELS
    assert result["physical_state_semantics"].startswith("NONE")
    assert result["physical_event_free_horizon_claimed"] is False
    assert result["physical_positive_duration_authorized"] is False
    assert result["publication_performed"] is False
    assert result["convergence_closes_model_or_authority_gap"] is False
    assert "rift process state" in result["unavailable_or_unknown_physical_outputs"]


def test_diagnostic_window_cannot_exceed_or_equal_authority_bound():
    nodes, omega = _fixture()
    for fraction in (1.0, 1.1, 0.0, -0.1):
        with pytest.raises(ValueError):
            compute_multiresolution(nodes, omega, window_fraction=fraction)
    result = compute_multiresolution(nodes, omega, window_fraction=0.25)
    assert result["diagnostic_window_years"] < REVALIDATION_HORIZON_YEARS
    assert result["maximum_model_scope_revalidation_years"] == REVALIDATION_HORIZON_YEARS


def test_resolution_comparison_is_deterministic_and_has_no_tolerance_authority():
    nodes, omega = _fixture()
    first = compute_multiresolution(nodes, omega, horizon_years=1000.0)
    second = compute_multiresolution(nodes, omega, horizon_years=1000.0)
    assert first == second
    assert [row["trajectory_sample_coordinates_sha256"] for row in
            first["resolution_ladder"]] == [row["trajectory_sample_coordinates_sha256"] for row in
            second["resolution_ladder"]]
    assert all(row["tolerance_authority"] == "ABSENT" and
               row["compression_acceptance_claim"] is False
               for row in first["sparse_checkpoint_reconstruction"])
    assert all("max_position_difference_to_finest_m" in row
               for comp in first["cross_resolution_comparison"] for row in comp["samples"])


def test_temporary_refinement_neither_creates_events_nor_closes_authority_gap():
    nodes, omega = _fixture()
    result = compute_multiresolution(nodes, omega, horizon_years=1000.0)
    refined = result["temporal_refinement"]
    assert refined["event_or_transition_created"] is False
    assert refined["temporary_trajectory_only"] is True
    assert result["convergence_closes_model_or_authority_gap"] is False
    assert all(row["compression_acceptance_claim"] is False
               for row in result["sparse_checkpoint_reconstruction"])
    assert result["temporal_refinement"]["numerical_error_decreased"] is False
    assert "MODEL_AUTHORITY_REMAINS_UNRESOLVED" in result[
        "numerical_pattern_analysis"]["numerical_vs_model_authority_classification"]


def test_discrete_topology_is_not_evolved_and_no_world_history_publication_occurs():
    nodes, omega = _fixture()
    result = compute_multiresolution(nodes, omega, horizon_years=1000.0)
    assert result["plate_pair"] == [1, 3]
    assert result["publication_performed"] is False
    assert result["unavailable_or_unknown_physical_outputs"]
    assert result["temporal_refinement"]["spatial_scope_semantics"].startswith(
        "IDENTIFIED_INPUT_NODE_ONLY")


def _canonical_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    source = os.environ.get("ARCANA_WORLD_HISTORY_ROOT")
    if not source or not Path(source).is_dir():
        pytest.skip("configured canonical WORLD_HISTORY fixture is unavailable")
    destination = tmp_path / "canonical"
    shutil.copytree(Path(source), destination)
    monkeypatch.setenv("ARCANA_WORLD_HISTORY_ROOT", str(destination))
    return destination


def test_live_view_overrides_genesis_descriptor_and_is_read_only(tmp_path, monkeypatch):
    root = _canonical_copy(tmp_path, monkeypatch)
    before = canonical_snapshot(root)
    result = _preflight_live_canonical_store(root)
    after = canonical_snapshot(root)
    assert result["status"] == "PASS_CANONICAL_LIVE_VIEW_PREFLIGHT"
    assert result["descriptor_temporal_state_count_informational_only"] == 1
    assert result["live_physical_geometry_epoch_count"] == 2
    assert result["post_event_visible_and_queryable"] is True
    assert result["canonical_current_view_id"].startswith("view_")
    assert before == after


def test_preflight_fails_closed_when_current_view_is_wrong(tmp_path, monkeypatch):
    root = _canonical_copy(tmp_path, monkeypatch)
    pointer_path = root / ".history_visibility" / "CURRENT.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    pointer["view_id"] = "view_missing"
    pointer_path.write_text(json.dumps(pointer), encoding="utf-8")
    before = canonical_snapshot(root)
    with pytest.raises(ValueError, match="preflight failed closed"):
        _preflight_live_canonical_store(root)
    assert canonical_snapshot(root) == before


def test_preflight_fails_closed_when_post_event_is_not_visible(tmp_path, monkeypatch):
    root = _canonical_copy(tmp_path, monkeypatch)
    (root / "states" / f"{POST_EVENT_ID}.json").unlink()
    before = canonical_snapshot(root)
    with pytest.raises(ValueError, match="preflight failed closed"):
        _preflight_live_canonical_store(root)
    assert canonical_snapshot(root) == before


def test_preflight_fails_closed_when_post_event_payload_identity_is_wrong(tmp_path, monkeypatch):
    root = _canonical_copy(tmp_path, monkeypatch)
    path = root / "states" / f"{POST_EVENT_ID}.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["payload_ref"] = "sha256:" + "0" * 64
    path.write_text(json.dumps(record), encoding="utf-8")
    before = canonical_snapshot(root)
    with pytest.raises(ValueError, match="preflight failed closed"):
        _preflight_live_canonical_store(root)
    assert canonical_snapshot(root) == before


def test_preflight_rejects_non_authorized_canonical_root(tmp_path, monkeypatch):
    root = _canonical_copy(tmp_path, monkeypatch)
    monkeypatch.setenv("ARCANA_WORLD_HISTORY_ROOT", str(tmp_path / "another-root"))
    before = canonical_snapshot(root)
    with pytest.raises(ValueError, match="does not match ARCANA_WORLD_HISTORY_ROOT"):
        _preflight_live_canonical_store(root)
    assert canonical_snapshot(root) == before


def test_diagnostic_records_observable_authority_and_temporary_scale():
    nodes, omega = _fixture()
    result = compute_multiresolution(nodes, omega, horizon_years=1000.0)
    assert result["temporary_trajectory_accounting"] == {
        "resolution_count": 4,
        "sample_times_per_resolution": 5,
        "identified_interface_nodes": 2,
        "plate_side_coordinate_representations_per_node": 2,
        "temporary_sample_coordinate_triples": 80,
        "temporary_sample_scalar_coordinates": 240,
        "full_coordinate_trajectory_files_written": 0,
        "coordinate_arrays_retained_in_result": False,
        "per_resolution_coordinate_sha256_retained": True,
    }
    registry = OBSERVABLE_REGISTRY
    assert all({"derivation", "authority", "scope", "adaptive_signal",
                "state_extraction"} <= row.keys() for row in registry)

