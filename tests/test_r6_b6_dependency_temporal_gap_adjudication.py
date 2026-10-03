from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "r6_b6_dependency_temporal_gap_adjudication",
    ROOT / "scripts/r6_b6_dependency_temporal_gap_adjudication.py",
)
assert SPEC is not None and SPEC.loader is not None
B6 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(B6)


def test_causal_graph_accepts_dependency_order() -> None:
    graph = {
        "nodes": [{"node_id": "STATE"}, {"node_id": "INPUT"}],
        "edges": [{"from": "STATE", "to": "INPUT", "kind": "REQUIRES"}],
    }
    assert B6.validate_causal_graph(graph)


def test_causal_graph_rejects_cycle() -> None:
    graph = {
        "nodes": [{"node_id": "STATE"}, {"node_id": "CHECKPOINT"}],
        "edges": [
            {"from": "STATE", "to": "CHECKPOINT", "kind": "REQUIRES"},
            {"from": "CHECKPOINT", "to": "STATE", "kind": "REQUIRES"},
        ],
    }
    with pytest.raises(B6.B6QualificationError, match="cycle"):
        B6.validate_causal_graph(graph)


def test_b6_decision_preserves_not_ready_safety_gates() -> None:
    result = {
        "decision": B6.EXPECTED_DECISION,
        "first_dt_readiness": "NOT_READY_FOR_FIRST_DT",
        "minimal_blocking_set": ["MOTION"],
        "scientific_side_effect_check": {
            key: False
            for key in (
                "mechanics_authorized",
                "forward_evolution_authorized",
                "dt_selected",
                "t1_created",
                "canonical_state_changed",
                "shellset_executed",
                "orbdata_mechanics_executed",
            )
        },
    }
    prerequisites = {
        "requirements": [{"requirement_id": "MOTION", "blocks_first_dt": True}]
    }
    graph = {"nodes": [{"node_id": "STATE"}], "edges": []}
    assert B6.validate_b6_decision(result, prerequisites, graph)


def test_b6_decision_rejects_authorized_dt() -> None:
    result = {
        "decision": B6.EXPECTED_DECISION,
        "first_dt_readiness": "READY_FOR_FIRST_DT_ADJUDICATION",
        "minimal_blocking_set": ["MOTION"],
        "scientific_side_effect_check": {
            key: False
            for key in (
                "mechanics_authorized",
                "forward_evolution_authorized",
                "dt_selected",
                "t1_created",
                "canonical_state_changed",
                "shellset_executed",
                "orbdata_mechanics_executed",
            )
        },
    }
    prerequisites = {
        "requirements": [{"requirement_id": "MOTION", "blocks_first_dt": True}]
    }
    graph = {"nodes": [{"node_id": "STATE"}], "edges": []}
    with pytest.raises(B6.B6QualificationError, match="cannot mark first dt ready"):
        B6.validate_b6_decision(result, prerequisites, graph)
