"""Evidence-based B6C decision tests; no scientific execution is performed."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from _git_test_env import isolated_git_environment

from scripts.r6_b6c_targeted_model_decision import B6CError, ROOT, adjudicate, validate
from arcana_worldsim.r6.finite_rotation import rotate_vector_constant_euler


@pytest.fixture(scope="module")
def decision() -> dict:
    return adjudicate(ROOT, mode="regression")


def test_rotation_action_is_uniquely_derived_and_internal_only(decision: dict) -> None:
    r = decision["rotation"]
    assert r["status"] == "UNIQUELY_DERIVABLE"
    assert r["action"] == "ACTIVE_ROTATION_OF_COLUMN_POSITION_VECTOR"
    assert "omega cross x" in r["differential_definition"]
    assert r["axis_orientation"]["handedness"].startswith("right-handed")
    assert r["coordinates"]["omega"] == "rad/year"
    assert "not Earth/mantle fixed" in r["coordinates"]["internal_frame"]
    # Synthetic algebra fixture: positive +Z is an active right-hand rotation.
    turned = rotate_vector_constant_euler((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), 1.5707963267948966)
    assert turned == pytest.approx((0.0, 1.0, 0.0), abs=1e-12)


def test_no_topology_option_is_selected_and_rift_horizon_is_not_topology(decision: dict) -> None:
    t = decision["topology"]
    assert t["decision"].startswith("AUTHORIAL_MODEL_CHOICE_REQUIRED")
    assert all(x["status"] == "NOT_SELECTED" for x in t["options"])
    assert "supplies no topology invariance" in t["interaction_with_rift_horizon"]


def test_boundary_models_preserve_unknown_type_and_require_authority(decision: dict) -> None:
    b = decision["boundary"]
    assert b["current_support"]["geological_type"] == "UNKNOWN"
    assert b["current_support"]["polarity"] == "UNKNOWN"
    duplicate = next(x for x in b["options"] if x["model"] == "DUPLICATED_BOUNDARY_GEOMETRY")
    assert duplicate["physical_closure_by_itself"] is False
    assert b["decision"] == "AUTHORIAL_DECISION_REQUIRED"


def test_junction_requires_explicit_multi_interface_compatibility(decision: dict) -> None:
    j = decision["junction"]
    assert j["count"] == 20
    assert "explicitly includes a multi-interface compatibility closure" in j["decision"]
    assert "unique plate owner" in j["forbidden"]


def test_transfer_numerics_and_first_dt_remain_blocked(decision: dict) -> None:
    assert len(decision["state_transfer"]["families"]) == 15
    assert decision["state_transfer"]["decision"].startswith("BLOCKED")
    assert decision["numerical"]["decision"] == "REQUIRED_LIMITS_UNBOUND; NO_NUMERICAL_VALUE_SELECTED"
    assert decision["prereqs"]["first_dt_readiness"] == "NOT_READY_FOR_FIRST_DT"
    assert decision["result"]["shellset_decision"] == "SHELLSET_DECISION_STILL_BLOCKED_BY_AUTHORIAL_MODEL_CHOICE"
    assert validate(decision)


def test_wrong_checkout_identity_fails_closed(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-b", "wrong-branch", str(tmp_path)], check=True,
                   capture_output=True, text=True, env=isolated_git_environment())
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=B6C test",
                    "-c", "user.email=b6c@example.invalid", "commit", "--allow-empty",
                    "-m", "fixture"], check=True, capture_output=True, text=True,
                   env=isolated_git_environment())
    with pytest.raises(B6CError, match="expected .* found"):
        adjudicate(tmp_path)
