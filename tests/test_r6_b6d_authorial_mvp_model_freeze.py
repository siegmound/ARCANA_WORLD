"""B6D contract materialization tests; no scientific execution."""
from __future__ import annotations

from pathlib import Path

import hashlib
import json
import pytest

from scripts.r6_b6d_authorial_mvp_model_freeze import B6DError, HEAD, ROOT, validate


@pytest.fixture(scope="module")
def freeze() -> dict:
    out = ROOT / "outputs/r6_b6d_authorial_mvp_model_freeze"
    manifest = json.loads((out / "B6D_ARTIFACT_MANIFEST.json").read_text(encoding="utf-8"))
    for row in manifest["artifacts"]:
        path = (out / row["relative_path"]).resolve()
        raw = path.read_bytes()
        assert len(raw) == row["byte_size"]
        assert hashlib.sha256(raw).hexdigest() == row["sha256"]
    names = {
        "result": "B6D_RESULT.json",
        "decisions": "B6D_AUTHORIAL_DECISIONS.json",
        "consistency": "B6D_MODEL_CONSISTENCY.json",
        "transfer": "B6D_STATE_TRANSFER_MATRIX.json",
        "event": "B6D_TOPOLOGY_EVENT_POLICY.json",
        "numeric": "B6D_NUMERICAL_CONSTRAINT_CONTRACT.json",
        "query": "B6D_MVP_QUERY_ACCEPTANCE_CONTRACT.json",
        "gaps": "B6D_REMAINING_GAPS.json",
        "mechanics": "B6D_MECHANICS_DECISION.json",
    }
    evidence = {key: json.loads((out / name).read_text(encoding="utf-8"))
                for key, name in names.items()}
    assert validate(evidence)
    return evidence


def test_current_source_and_all_eight_authorial_decisions_are_pinned(freeze: dict) -> None:
    assert freeze["result"]["qualified_source_commit"] == HEAD
    assert freeze["result"]["branch"] == "r6/b6d-authorial-mvp-first-step-model-freeze"
    assert [x["id"] for x in freeze["decisions"]["decisions"]] == [f"D{i}" for i in range(1, 9)]
    assert freeze["decisions"]["decisions"][0]["policy"] == "EVENT_DRIVEN_TOPOLOGY_HOLD"
    assert freeze["decisions"]["decisions"][7]["policy"] == "ADAPTIVE_CONSTRAINT_DRIVEN_TIMESTEP"


def test_consistency_preserves_gaps_without_fabricating_closure(freeze: dict) -> None:
    assert freeze["consistency"]["status"] == "MODEL_CONTRACT_CONSISTENT"
    assert freeze["consistency"]["scientific_contradictions"] == []
    assert freeze["event"]["absence_of_detector_means_absence"] is False
    assert freeze["event"]["status"] == "BLOCKS_FIRST_DT_ADJUDICATION"


def test_transfer_matrix_covers_b6c_families_and_unknowns(freeze: dict) -> None:
    assert len(freeze["transfer"]["families"]) == 15
    assert all(x["unknown_behavior"] for x in freeze["transfer"]["families"])
    assert "SYSTEM_MEMORY" in freeze["transfer"]["global_rule"]


def test_mvp_defers_mechanics_and_keeps_dt_unselected(freeze: dict) -> None:
    r = freeze["result"]
    assert r["mvp_mechanics_decision"] == "MVP_FIRST_STEP_KINEMATIC_NO_MECHANICS_REQUIRED"
    assert r["shellset_status"] == "SHELLSET_DEFERRED_UNTIL_MECHANICAL_RESPONSE_REQUIRED"
    assert r["first_dt_readiness"] == "NOT_READY_FOR_FIRST_DT"
    assert r["maximum_next_authorization"] == "AUTHORIZE_MINIMAL_MVP_MODEL_IMPLEMENTATION"
    assert validate(freeze)


def test_safety_gate_validator_rejects_dt_or_motion() -> None:
    bad = {"result": {"decision": "PASS_B6D_AUTHORIAL_MVP_FIRST_STEP_MODEL_FREEZE", "qualified_source_commit": HEAD,
                       "first_dt_readiness": "NOT_READY_FOR_FIRST_DT", "scientific_side_effect_check": {
                           "canonical_state_changed": False, "canonical_node_motion_executed": True,
                           "canonical_topology_mutated": False, "dt_selected": False, "t1_created": False,
                           "mechanics_authorized": False, "shellset_executed": False,
                           "orbdata_mechanics_executed": False, "forward_evolution_authorized": False}},
           "decisions": {"decisions": [{} for _ in range(8)]}, "consistency": {"scientific_contradictions": []},
           "transfer": {}, "numeric": {}, "event": {}, "query": {}, "gaps": {}, "mechanics": {}}
    with pytest.raises(B6DError, match="safety gate opened"):
        validate(bad)


def test_shellset_is_deferred_not_removed(freeze: dict) -> None:
    assert freeze["mechanics"]["shellset_status"] == "SHELLSET_DEFERRED_UNTIL_MECHANICAL_RESPONSE_REQUIRED"
    assert freeze["mechanics"]["not_a_claim"] == "mechanics is never required"

