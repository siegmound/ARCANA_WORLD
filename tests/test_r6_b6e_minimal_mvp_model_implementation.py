"""B6E representational regression; no physical evolution is executed."""
from __future__ import annotations

import pytest
import json

from scripts.r6_b6e_minimal_mvp_model_implementation import (
    BRANCH,
    HEAD,
    ROOT,
    B6EError,
    _result,
    _validate_source_identity,
    adjudicate,
)
from arcana_worldsim.r6.mvp_model import (
    MVPModelError,
    asynchronous_validity_fixture,
    materialize_t0_representation,
    transfer_declarations_from_matrix,
)


@pytest.fixture(scope="module")
def b6e() -> dict:
    return adjudicate(ROOT, mode="regression")


def test_governed_t0_scale_and_read_only_materialization(b6e: dict) -> None:
    assert b6e["t0"] == {
        "node_count": 64442,
        "face_count": 64800,
        "triangle_count": 128880,
        "boundary_segment_count": 1983,
        "junction_count": 20,
        "support_counts": {
            "INTERIOR_PLATE": 62469,
            "BOUNDARY_SHARED": 1953,
            "JUNCTION_SHARED": 20,
            "UNKNOWN": 0,
        },
    }
    summary = b6e["summary"]
    assert summary["interior_entities"] == 62469
    assert summary["boundary_side_entities"] == 3966
    assert summary["boundary_vertex_representatives"] == 7932
    assert summary["junction_side_entities"] == 60
    assert summary["interfaces"] == 1983
    assert summary["junction_relations"] == 20
    assert summary["arbitrary_owner_assignment_count"] == 0
    assert summary["node_motion_count"] == summary["topology_mutation_count"] == 0


def test_boundary_interfaces_keep_two_distinct_plate_sides_and_unknown_physics(b6e: dict) -> None:
    rep = b6e["representation"]
    assert len(rep.interfaces) == 1983
    for interface in rep.interfaces:
        assert interface.side_a.plate_id != interface.side_b.plate_id
        assert interface.side_a.source_boundary_id == interface.side_b.source_boundary_id
        assert interface.side_a.source_endpoint_node_ids == interface.side_b.source_endpoint_node_ids
        assert interface.physical_response_status == "UNKNOWN"
        assert interface.to_dict()["polarity"] == "UNKNOWN"


def test_junctions_preserve_all_incident_sides_without_unique_owner(b6e: dict) -> None:
    rep = b6e["representation"]
    assert len(rep.junction_relations) == 20
    for junction in rep.junction_relations:
        assert len(junction.incident_plate_ids) >= 3
        assert junction.incident_interface_ids
        assert len(junction.plate_local_side_ids) == len(junction.incident_plate_ids)
        assert junction.unique_plate_owner is None
        assert junction.compatibility_status == "REQUIRED_NOT_QUALIFIED"


def test_lineage_and_representation_identity_are_deterministic(b6e: dict) -> None:
    rep = b6e["representation"]
    summary = b6e["summary"]
    source = b6e["b5"]
    repeated = materialize_t0_representation(
        source_semantic_identity=str(source["spatial"]["source_identity_sha256"]),
        source_payload_ref=f"sha256:{source['support']['payload_sha256']}",
        source_mesh_identity=str(source["spatial"]["mesh"]["sha256"]),
        node_plate_ids=source["node_plates"],
        support_kind_by_node=source["support_kinds"],
        boundary_descriptors=source["descriptors"],
        junctions=source["junctions"],
    )
    assert rep.identity_digest() == repeated.identity_digest()
    assert summary["identity_collision_count"] == 0
    assert summary["representative_count"] == summary["unique_representation_identity_count"]
    assert summary["semantic_record_identity_count"] == summary["unique_semantic_record_identity_count"]
    assert all(x.lineage.source_semantic_identity == rep.source_semantic_identity
               and x.lineage.source_payload_ref == rep.source_payload_ref
               and x.lineage.physical_state_created is False
               for x in rep.all_representatives)
    assert all(x.lineage.derived_representation_id == x.interface_id
               for x in rep.interfaces)
    assert all(x.side_a.lineage.derived_representation_id == x.side_a.side_id
               for x in rep.interfaces)
    assert all(x.side_b.lineage.derived_representation_id == x.side_b.side_id
               for x in rep.interfaces)
    assert all(x.lineage.derived_representation_id == x.relation_id
               for x in rep.junction_relations)
    assert all(x.lineage.source_semantic_identity == rep.source_semantic_identity
               and x.lineage.source_payload_ref == rep.source_payload_ref
               and x.lineage.physical_state_created is False
               for x in (*rep.interfaces, *rep.junction_relations))
    assert json.loads(json.dumps(rep.interfaces[0].to_dict()))["lineage"]["physical_state_created"] is False
    assert rep.to_dict()["representation_identity_digest"] == rep.identity_digest()
    tiny = materialize_t0_representation(
        source_semantic_identity="fixture-source", source_payload_ref="sha256:fixture",
        source_mesh_identity="fixture-mesh", node_plate_ids=((1, 2), (1, 2)),
        support_kind_by_node=("BOUNDARY_SHARED", "BOUNDARY_SHARED"),
        boundary_descriptors=({"boundary_id": "fixture-boundary", "adjacent_plate_ids": (1, 2),
                              "endpoint_node_ids": (1, 2)},), junctions=())
    serialized = json.loads(json.dumps(tiny.to_dict(include_records=True)))
    assert len(serialized["interfaces"]) == 1
    assert len(serialized["boundary_vertex_representatives"]) == 4


def test_transfer_classes_are_declarations_only_and_preserve_unresolved_authority(b6e: dict) -> None:
    declarations = b6e["transfer_declarations"]
    assert len(declarations) == 15
    assert all(x.missing_authority_behavior == "PRESERVE_UNKNOWN_OR_MODEL_REQUIRED__NO_IMPUTATION"
               for x in declarations)
    assert all(x.target_support_class == "PLATE_LOCAL_OR_DOMAIN_SUPPORT_NOT_MATERIALIZED_AS_T1"
               for x in declarations)
    assert b6e["world_history"]["candidate_t1_created"] is False
    assert b6e["summary"]["node_motion_count"] == 0


def test_unknown_transfer_policy_does_not_become_executable_remap() -> None:
    matrix = {"families": [{"family": "unresolved field", "transfer_class": "UNKNOWN_OR_REMAP",
                            "support": "governed T0", "conservation_requirement": "UNKNOWN"}]}
    declaration, = transfer_declarations_from_matrix(matrix)
    assert declaration.transfer_class.value == "UNKNOWN"
    assert declaration.missing_authority_behavior == "PRESERVE_UNKNOWN_OR_MODEL_REQUIRED__NO_IMPUTATION"


def test_async_validity_stays_symbolic_and_does_not_create_future_state() -> None:
    rows = asynchronous_validity_fixture()
    assert {row.domain for row in rows} == {"tectonics", "climate", "hydrology", "ecology", "Deep"}
    assert all(row.query_time.startswith("FIXTURE_QUERY_CANDIDATE") for row in rows)
    assert all(row.candidate_state_time is None and not row.candidate_state_present for row in rows)
    assert all(row.latest_valid_time == row.state_time == "210Ma" for row in rows)
    assert {row.domain: row.query_role for row in rows} == {
        "tectonics": "TECTONIC_ADVANCE_CANDIDATE",
        "climate": "LATEST_VALID_STATE_CARRY_FORWARD",
        "hydrology": "LATEST_VALID_STATE_CARRY_FORWARD",
        "ecology": "LATEST_VALID_STATE_CARRY_FORWARD",
        "Deep": "LATEST_VALID_STATE_CARRY_FORWARD",
    }


def test_malformed_set_valued_boundary_fails_closed() -> None:
    with pytest.raises(MVPModelError, match="endpoint support omits adjacent plate"):
        materialize_t0_representation(
            source_semantic_identity="source",
            source_payload_ref="sha256:fixture",
            source_mesh_identity="mesh",
            node_plate_ids=((1, 2), (1, 3)),
            support_kind_by_node=("BOUNDARY_SHARED", "BOUNDARY_SHARED"),
            boundary_descriptors=({"boundary_id": "b0", "adjacent_plate_ids": (1, 2),
                                  "endpoint_node_ids": (1, 2)},),
            junctions=(),
        )


def test_scientific_authorization_scope_is_preserved(b6e: dict) -> None:
    gates = _result(b6e)["scientific_side_effect_check"]
    assert gates["runtime_authorized"] is True
    assert gates["runtime_authorized_scope"] == "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE"
    for gate in ("mechanics_authorized", "forward_evolution_authorized", "dt_selected",
                 "t1_created", "canonical_state_changed", "canonical_node_motion_executed",
                 "canonical_topology_mutated", "shellset_executed", "orbdata_mechanics_executed"):
        assert gates[gate] is False


def test_qualification_is_pinned_and_regression_accepts_descendant_checkout() -> None:
    _validate_source_identity(BRANCH, HEAD, "qualification")
    _validate_source_identity("r6/b6e-descendant", "f" * 40, "regression")
    with pytest.raises(B6EError, match="expected .* found"):
        _validate_source_identity("wrong-branch", HEAD, "qualification")
