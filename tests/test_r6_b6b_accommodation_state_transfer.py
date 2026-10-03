"""Small fixture and source-authority checks for the B6B adjudication."""
from __future__ import annotations

from pathlib import Path

import pytest
import subprocess

from scripts.r6_b6b_accommodation_state_transfer import (
    B6BError,
    ROOT,
    adjudicate,
    rigid_rotate,
    shared_coordinate_compatible,
    validate_result,
)


def test_synthetic_rigid_interior_transform_is_deterministic() -> None:
    quarter_turn = ((0, -1, 0), (1, 0, 0), (0, 0, 1))
    assert rigid_rotate((1, 0, 0), quarter_turn) == (0.0, 1.0, 0.0)
    assert rigid_rotate((1, 0, 0), quarter_turn) == rigid_rotate((1, 0, 0), quarter_turn)


def test_rigid_transform_rejects_malformed_dimensions() -> None:
    with pytest.raises(B6BError):
        rigid_rotate((1, 0), ((1, 0), (0, 1)))


def test_shared_boundary_does_not_choose_or_average_incompatible_positions() -> None:
    assert not shared_coordinate_compatible(((1, 0, 0), (0, 1, 0)))
    assert shared_coordinate_compatible(((1, 0, 0), (1, 0, 0)))
    assert not shared_coordinate_compatible(())


def test_current_governed_authority_keeps_global_first_state_blocked() -> None:
    data = adjudicate(ROOT, mode="regression")
    assert data["result"]["decision"] == "PASS_B6B_FIRST_STEP_ACCOMMODATION_STATE_TRANSFER"
    assert data["result"]["first_dt_status_after_B6B"] == "NOT_READY_FOR_FIRST_DT"
    assert data["result"]["boundary_accommodation_status"].startswith("BLOCKING")
    assert data["result"]["junction_accommodation_status"].startswith("BLOCKING")
    assert data["result"]["maximum_next_authorization"] == "AUTHORIZE_TARGETED_MODEL_DECISION"
    assert data["result"]["qualified_source_commit"] == "66ff83a8cf8b86b483c60a75b12d1da9594d1740"
    assert data["result"]["current_regression_checkout"]["branch"] == subprocess.run(
        ["git", "-C", str(ROOT), "branch", "--show-current"], check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    interior = next(item for item in data["transformations"]["transformations"]
                    if item["item"] == "strictly interior node coordinates")
    assert "CARTESIAN_ACTION_CONVENTION_MUST_BE_EXPLICIT" in interior["status"]
    assert "handedness is not separately declared" in interior["frame_orientation_evidence"]
    mesh = data["mesh_transfer"]["t0_mesh"]
    assert mesh["node_count"] == 64442
    assert mesh["triangle_count"] == 128880
    assert mesh["canonical_normalized_sha256"] != mesh["production_runtime_normalized_sha256"]


def test_source_identity_mismatch_fails_closed(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-b", "wrong-branch", str(tmp_path)], check=True,
                   capture_output=True, text=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=B6B test",
                    "-c", "user.email=b6b@example.invalid", "commit", "--allow-empty",
                    "-m", "fixture"], check=True, capture_output=True, text=True)
    with pytest.raises(B6BError, match="expected .* found"):
        adjudicate(tmp_path)


def test_result_validator_rejects_open_scientific_gate() -> None:
    data = adjudicate(ROOT, mode="regression")
    data["result"]["scientific_side_effect_check"]["dt_selected"] = True
    with pytest.raises(B6BError, match="safety gate opened"):
        validate_result(data)
