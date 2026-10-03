from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "r6_b6a_positive_duration_authority",
    ROOT / "scripts/r6_b6a_positive_duration_authority.py",
)
assert SPEC is not None and SPEC.loader is not None
B6A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(B6A)


@pytest.fixture(scope="module")
def audit() -> dict:
    # Regression mode re-runs the scientific/source assertions on this
    # descendant checkout while retaining B6A's historical qualified source.
    return B6A.adjudicate(ROOT, mode="regression")


def test_current_authority_has_one_t0_anchor_and_conditional_first_segment(audit: dict) -> None:
    motion = audit["motion"]
    assert motion["multiple_temporal_anchor_status"]["status"] == "SINGLE_GOVERNED_ANCHOR_ONLY"
    assert motion["multiple_temporal_anchor_status"]["times_ma"] == [210.0]
    assert motion["positive_duration_motion_law_status"] == "GOVERNED_CONDITIONAL_CONSTANT_T0_EULER_FIRST_SEGMENT"
    assert motion["first_interval_contract_authorized"] is False


def test_rift_activation_bound_is_not_topology_transition_bound(audit: dict) -> None:
    topology = audit["topology"]
    assert topology["status"] == "NO_POSITIVE_BOUND"
    assert topology["positive_conditional_rift_activation_bound"]["eligibility_counts"] == {
        "ACTIVE": 0, "ELIGIBLE_QUIESCENT": 26, "INELIGIBLE": 4, "UNKNOWN": 0
    }
    assert topology["positive_conditional_rift_activation_bound"]["elapsed_years"] > 0
    assert "plate split" in topology["positive_conditional_rift_activation_bound"]["does_not_bound"]
    assert topology["topology_invariance_interval_ma"] is None


def test_joint_temporal_support_remains_blocked_without_topology_bound(audit: dict) -> None:
    assert audit["joint"]["status"] == "NO_JOINT_KINEMATIC_TOPOLOGY_SUPPORT"
    assert audit["joint"]["positive_interval_status"] == "POSITIVE_INTERVAL_REQUIRES_MODEL_DECISION"
    assert audit["result"]["first_dt_status_after_B6A"] == "NOT_READY_FOR_FIRST_DT"


def test_b6a_decision_keeps_scientific_safety_gates_closed(audit: dict) -> None:
    assert B6A.validate_regression_decision(audit)
    # Provenance remains the immutable historical qualification identity;
    # current checkout identity is recorded separately for regression.
    assert audit["result"]["branch"] == "r6/b6a-positive-duration-kinematic-authority"
    assert audit["result"]["qualified_source_commit"] == "8f53f1586413b1e2e3b6738185727e5b6314c30c"
    assert audit["result"]["current_regression_checkout"]["branch"] == B6A._git(ROOT, "branch", "--show-current")
    assert audit["result"]["current_regression_checkout"]["head"] == B6A._git(ROOT, "rev-parse", "HEAD")
    retained_path = ROOT / "outputs/r6_b6a_positive_duration_authority/B6A_RESULT.json"
    retained = json.loads(retained_path.read_text(encoding="utf-8"))
    assert retained["qualified_source_commit"] == "8f53f1586413b1e2e3b6738185727e5b6314c30c"
    manifest = json.loads((retained_path.parent / "B6A_ARTIFACT_MANIFEST.json").read_text(encoding="utf-8"))
    retained_entry = next(x for x in manifest["artifacts"] if x["relative_path"] == "B6A_RESULT.json")
    assert retained_entry["byte_size"] == retained_path.stat().st_size
    assert retained_entry["sha256"] == hashlib.sha256(retained_path.read_bytes()).hexdigest()
    gates = audit["result"]["scientific_side_effect_check"]
    assert gates["runtime_authorized"] is True
    assert gates["runtime_authorized_scope"] == "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE"
    for name in ("mechanics_authorized", "forward_evolution_authorized", "dt_selected",
                 "t1_created", "canonical_state_changed", "node_motion_executed",
                 "topology_mutation_executed", "shellset_executed", "orbdata_mechanics_executed"):
        assert gates[name] is False
