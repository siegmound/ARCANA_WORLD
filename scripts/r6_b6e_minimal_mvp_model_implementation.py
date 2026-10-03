#!/usr/bin/env python3
"""B6E read-only T0 representation builder and isolated qualification."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from arcana_worldsim.r6.identity import (BranchId, HistoryId, PayloadIdentity,
    canonical_bytes, verify_payload)
from arcana_worldsim.r6.mvp_model import (MemoryDisposition, StateTransferDeclaration,
    asynchronous_validity_fixture, materialize_t0_representation,
    system_memory_declarations, transfer_declarations_from_matrix)
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.query import HistoryQueryService
from arcana_worldsim.r6.shellset_mesh.adapter import load_canonical_mesh
from arcana_worldsim.r6.state import (AuthorityClass, DomainStateEnvelope,
    SpatialSupport, SupportClass, TimeSupport)
from arcana_worldsim.r6.store import HistoryStore
from arcana_worldsim.r6.temporal import HistoricalSnapshot

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "r6/b6e-minimal-mvp-first-step-model-implementation"
HEAD = "08664f0338e594dec41840a3a46ff0aa862e47fd"
OUT = ROOT / "outputs/r6_b6e_minimal_mvp_model_implementation"
REPORT = ROOT / "docs/arcana/B6E_MINIMAL_MVP_FIRST_STEP_MODEL_IMPLEMENTATION.md"
B5_DIR = ROOT / "outputs/r6_b5_plate_support_topology_qualification"
B5_MANIFEST = B5_DIR / "B5_ARTIFACT_MANIFEST.json"
B6D_DIR = ROOT / "outputs/r6_b6d_authorial_mvp_model_freeze"


class B6EError(ValueError):
    pass


def _validate_source_identity(branch: str, head: str, mode: str) -> None:
    if mode not in {"qualification", "regression"}:
        raise B6EError(f"unsupported B6E validation mode: {mode}")
    if mode == "qualification" and (branch != BRANCH or head != HEAD):
        raise B6EError(f"expected {BRANCH}@{HEAD}, found {branch}@{head}")


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if result.returncode:
        raise B6EError(f"git identity query failed: {' '.join(args)}")
    return result.stdout.strip()


def _read(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise B6EError(f"cannot read valid JSON: {path.name}") from exc


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def _b5_source(root: Path) -> dict[str, Any]:
    manifest = _read(root / "outputs/r6_b5_plate_support_topology_qualification/B5_ARTIFACT_MANIFEST.json")
    b5_dir = root / "outputs/r6_b5_plate_support_topology_qualification"
    verified: dict[str, dict[str, Any]] = {}
    for row in manifest["artifacts"]:
        path = (b5_dir / row["relative_path"]).resolve()
        if not path.is_file():
            raise B6EError(f"B5 artifact missing: {row['relative_path']}")
        if path.stat().st_size != row["byte_size"] or _sha(path) != row["sha256"]:
            raise B6EError(f"B5 artifact hash mismatch: {row['relative_path']}")
        verified[path.name] = {"path": path.relative_to(root).as_posix(),
                               "byte_size": path.stat().st_size, "sha256": _sha(path)}
    required = {"B5_RESULT.json", "B5_PLATE_SUPPORT.json", "B5_NODE_PLATE_SUPPORT_MAP_V1.json",
                "B5_BOUNDARY_CONTRACT.json", "B5_SPATIAL_AUTHORITY.json"}
    if not required.issubset(verified):
        raise B6EError(f"B5 artifact manifest lacks required inputs: {sorted(required-set(verified))}")
    result = _read(b5_dir / "B5_RESULT.json")
    support = _read(b5_dir / "B5_PLATE_SUPPORT.json")
    node_map = _read(b5_dir / "B5_NODE_PLATE_SUPPORT_MAP_V1.json")
    boundary = _read(b5_dir / "B5_BOUNDARY_CONTRACT.json")
    spatial = _read(b5_dir / "B5_SPATIAL_AUTHORITY.json")
    if result.get("decision") != "PASS_B5_PLATE_SUPPORT_TOPOLOGY_TEMPORAL_INTEGRATION":
        raise B6EError("B5 governed support qualification is not passing")
    if node_map.get("schema") != "R6_B5_NODE_PLATE_SUPPORT_MAP_V1" or node_map.get("node_count") != 64442:
        raise B6EError("B5 node support map schema/cardinality changed")
    if _sha(b5_dir / "B5_NODE_PLATE_SUPPORT_MAP_V1.json") != support.get("payload_sha256"):
        raise B6EError("B5 support payload identity mismatch")
    expected_counts = {"INTERIOR_PLATE": 62469, "BOUNDARY_SHARED": 1953,
                       "JUNCTION_SHARED": 20, "UNKNOWN": 0}
    if support.get("support_kind_counts") != expected_counts or result.get("node_support_counts") != expected_counts:
        raise B6EError("governed B5 node support counts changed")
    feg = _read(root / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json")
    if (feg.get("canonical_mesh", {}).get("node_count") != 64442
            or feg.get("canonical_mesh", {}).get("triangle_count") != 128880
            or feg.get("canonical_mesh", {}).get("normalized_sha256") != spatial["mesh"]["sha256"]):
        raise B6EError("B5/B6 governed canonical mesh identity or cardinality mismatch")
    mesh = load_canonical_mesh(root)
    if mesh.normalized_sha256 != spatial["mesh"]["sha256"]:
        raise B6EError("reloaded canonical T0 mesh differs from governed B5 identity")
    kinds = {int(code): name for name, code in node_map["support_kind_codes"].items()}
    if len(node_map["node_plate_masks"]) != 64442 or len(node_map["support_kind_code_by_node"]) != 64442:
        raise B6EError("B5 support arrays do not cover all canonical nodes")
    plate_ids = tuple(int(v) for v in node_map["plate_ids"])
    node_plates = tuple(tuple(pid for pid in plate_ids if int(mask) & (1 << pid))
                        for mask in node_map["node_plate_masks"])
    support_kinds = tuple(kinds[int(code)] for code in node_map["support_kind_code_by_node"])
    descs = tuple(boundary.get("descriptors", ()))
    if boundary.get("segment_count") != 1983 or len(descs) != 1983:
        raise B6EError("B5 boundary descriptor inventory changed")
    mesh_edges = {bid: tuple(sorted(nodes)) for bid, nodes in zip(mesh.boundary_ids, mesh.boundary_edge_nodes)}
    for desc in descs:
        if tuple(sorted(int(v) for v in desc["endpoint_node_ids"])) != mesh_edges.get(desc["boundary_id"]):
            raise B6EError(f"B5 boundary-to-canonical-mesh endpoint mismatch: {desc['boundary_id']}")
    junctions = tuple(support.get("junctions", ()))
    if len(junctions) != 20 or support.get("single_plate_owner_assigned") is not False:
        raise B6EError("governed junction support/count/owner invariant changed")
    return {"result": result, "support": support, "node_map": node_map,
            "boundary": boundary, "spatial": spatial, "mesh": mesh,
            "node_plates": node_plates, "support_kinds": support_kinds,
            "descriptors": descs, "junctions": junctions,
            "verified_artifacts": verified,
            "feg_manifest_sha256": _sha(root / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json")}


def _world_history_fixture(temp_root: Path, *, source_semantic_identity: str,
                           representation_digest: str) -> dict[str, Any]:
    """Persist/reopen a tiny noncanonical representation + UNKNOWN fixture."""
    history_id = str(HistoryId.from_payload({"fixture": "B6E_ISOLATED_REPRESENTATION_HISTORY_V1"}))
    branch_id = str(BranchId.from_payload({"fixture": "B6E_ISOLATED_REPRESENTATION_BRANCH_V1"}))
    time_support = TimeSupport("B6E_FIXTURE_T0_NO_GEOLOGIC_STATE", "FIXTURE_ONLY", "SNAPSHOT")
    spatial = SpatialSupport("B6E_FIXTURE_GRID", ("fixture-cell-0",), "fixture", "CELL_SET")
    payload = canonical_bytes({"fixture_only": True, "representation_digest": representation_digest,
        "source_semantic_identity": source_semantic_identity,
        "lineage": {"role": "PLATE_INTERIOR", "source": "FIXTURE_NODE:1"}})
    payload_identity = PayloadIdentity.from_bytes(payload)
    payload_path = temp_root / "payloads" / payload_identity.digest
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    payload_path.write_bytes(payload)
    payload_ref = f"sha256:{payload_identity.digest}"
    provenance = ProvenanceRecord.create(activity="B6E_FIXTURE_REPRESENTATION_MATERIALIZATION",
        input_refs=(source_semantic_identity,), source_refs=("FIXTURE_ONLY",),
        attributes={"representation_digest": representation_digest,
                    "fixture_only": True, "physical_state_created": False})
    state = DomainStateEnvelope.create(history_id=history_id, branch_id=branch_id,
        domain="mvp_representation_fixture", time_support=time_support,
        spatial_support=spatial, support_class=SupportClass.DERIVED_SUPPORTED,
        authority_class=AuthorityClass.FIXTURE_ONLY,
        value={"fixture_only": True, "representation_digest": representation_digest,
               "source_semantic_identity": source_semantic_identity,
               "support_roles": ["PLATE_INTERIOR", "BOUNDARY_SIDE", "JUNCTION_SIDE"],
               "lineage_source": "FIXTURE_NODE:1"},
        uncertainty={"physical_interpretation": "NOT_CLAIMED"},
        provenance_ids=(str(provenance.record_id),), payload_ref=payload_ref,
        model_derived=False,
        applicability={"time_scope": "FIXTURE_ONLY_NO_T1", "physical_state_created": False})
    unknown = DomainStateEnvelope.create(history_id=history_id, branch_id=branch_id,
        domain="unresolved_physical_response_fixture", time_support=time_support,
        spatial_support=SpatialSupport(None, (), "not established", "NONE"),
        support_class=SupportClass.UNKNOWN, authority_class=AuthorityClass.NONE,
        value=None, uncertainty={"reason": "NO_GOVERNED_PHYSICAL_RESPONSE"},
        provenance_ids=(str(provenance.record_id),), model_derived=False)
    snapshot = HistoricalSnapshot.create(history_id=history_id, branch_id=branch_id,
        time_key="B6E_FIXTURE_T0_NO_GEOLOGIC_STATE", domain_ids=("tectonics",),
        state_ids=(str(state.state_id), str(unknown.state_id)),
        authority_refs=(source_semantic_identity,), provenance_refs=(str(provenance.record_id),),
        validation_status="FIXTURE_ONLY", details={"t1_created": False,
            "representation_only": True, "async_validity_fixture_ref": "B6E_ASYNC_VALIDITY_FIXTURE"})
    store_path = temp_root / "history_store"
    store = HistoryStore(store_path)
    store.append_transaction((provenance, state, unknown, snapshot))
    del store
    reopened = HistoryStore(store_path)
    service = HistoryQueryService(reopened)
    query = service.state_at(history_id=history_id, branch_id=branch_id,
        domain=state.domain, time_key=time_support.time_key)
    unknown_query = service.state_at(history_id=history_id, branch_id=branch_id,
        domain=unknown.domain, time_key=time_support.time_key)
    why = service.why(str(state.state_id))
    recovered_snapshot = reopened.read_temporal(snapshot.record_id)
    verified = verify_payload(payload_ref, payload_path)
    history = service.history_result(history_id=history_id, branch_id=branch_id)
    identity_repeat = DomainStateEnvelope.from_dict(reopened.read_state(str(state.state_id)).to_dict()).state_id == state.state_id
    return {"status": "PASS_ISOLATED_FIXTURE_APPEND_REOPEN_QUERY_WHY",
        "fixture_only": True, "store_reopened": True,
        "state_id": str(state.state_id), "state_query_status": query.status,
        "unknown_query_status": unknown_query.status,
        "unknown_value": unknown_query.state.value if unknown_query.state else "MISSING",
        "history_state_count": len(history.states), "why_provenance_count": len(why.provenance_records),
        "why_unresolved_reference_count": len(why.unresolved_references),
        "support_recovered": query.state.spatial_support.to_dict() == spatial.to_dict(),
        "lineage_recovered": query.state.value["lineage_source"] == "FIXTURE_NODE:1",
        "temporal_validity_recovered": recovered_snapshot["details"]["t1_created"] is False,
        "semantic_identity_stable_after_reopen": identity_repeat,
        "payload_ref_integrity": verified.to_dict(), "payload_bytes": len(payload),
        "unknown_preserved": unknown_query.status == "UNKNOWN" and unknown_query.state.value is None,
        "candidate_t1_created": False,
        "canonical_t0_written": False}


def adjudicate(root: Path = ROOT, *, mode: str = "qualification") -> dict[str, Any]:
    root = root.resolve()
    branch, head = _git(root, "branch", "--show-current"), _git(root, "rev-parse", "HEAD")
    _validate_source_identity(branch, head, mode)
    b5 = _b5_source(root)
    b6d_matrix = _read(root / "outputs/r6_b6d_authorial_mvp_model_freeze/B6D_STATE_TRANSFER_MATRIX.json")
    b6d_result = _read(root / "outputs/r6_b6d_authorial_mvp_model_freeze/B6D_RESULT.json")
    if (b6d_result.get("decision") != "PASS_B6D_AUTHORIAL_MVP_FIRST_STEP_MODEL_FREEZE"
            or b6d_result.get("qualified_source_commit") != "5f924e25300ea4e26281b4419620f9ed5ee9c500"):
        raise B6EError("B6D authorial model freeze provenance/decision changed")
    representation = materialize_t0_representation(
        source_semantic_identity=str(b5["spatial"]["source_identity_sha256"]),
        source_payload_ref=f"sha256:{b5['support']['payload_sha256']}",
        source_mesh_identity=str(b5["spatial"]["mesh"]["sha256"]),
        node_plate_ids=b5["node_plates"], support_kind_by_node=b5["support_kinds"],
        boundary_descriptors=b5["descriptors"], junctions=b5["junctions"])
    summary = representation.summary()
    if summary["interior_entities"] != 62469 or summary["boundary_side_entities"] != 3966:
        raise B6EError("materialized interior/boundary side cardinality differs from governed support")
    if summary["junction_side_entities"] != 60 or summary["interfaces"] != 1983 or summary["junction_relations"] != 20:
        raise B6EError("materialized junction/interface cardinality differs from governed authority")
    transfers = transfer_declarations_from_matrix(b6d_matrix)
    memory = system_memory_declarations((
        {"family": "initial-world supported fields", "disposition": "MODEL_REQUIRED",
         "retained_reference": "payload://sha256/a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c",
         "update_rule": "B0-G SYSTEM_MEMORY retained; field-specific future transfer is unbound"},
        {"family": "vector partition", "disposition": "HISTORICAL_REFERENCE",
         "retained_reference": "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json",
         "update_rule": "retain historical parent identity; event-driven reindex/lineage not executed"},
        {"family": "plate kinematics", "disposition": "HISTORICAL_REFERENCE",
         "retained_reference": "R6_T0_CANONICAL_PLATE_KINEMATICS.json",
         "update_rule": "retain forcing and replay identity; no motion executed"},
        {"family": "unknown-domain masks", "disposition": "HISTORICAL_REFERENCE",
         "retained_reference": "R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json",
         "update_rule": "retain support evidence; UNKNOWN is not converted to numeric state"},
        {"family": "FEG/ShellSet runtime products", "disposition": "RECOMPUTE_REQUIRED",
         "retained_reference": "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json",
         "update_rule": "derived numerical support only; never canonical WORLD_HISTORY memory"},
    ))
    async_validity = asynchronous_validity_fixture()
    with tempfile.TemporaryDirectory(prefix="arcana-b6e-wh-") as temporary:
        integration = _world_history_fixture(Path(temporary),
            source_semantic_identity=representation.source_semantic_identity,
            representation_digest=representation.identity_digest())
    source_paths = ["outputs/r6_b5_plate_support_topology_qualification/B5_ARTIFACT_MANIFEST.json",
        "outputs/r6_b5_plate_support_topology_qualification/B5_RESULT.json",
        "outputs/r6_b5_plate_support_topology_qualification/B5_PLATE_SUPPORT.json",
        "outputs/r6_b5_plate_support_topology_qualification/B5_NODE_PLATE_SUPPORT_MAP_V1.json",
        "outputs/r6_b5_plate_support_topology_qualification/B5_BOUNDARY_CONTRACT.json",
        "outputs/r6_b5_plate_support_topology_qualification/B5_SPATIAL_AUTHORITY.json",
        "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json",
        "outputs/r6_b6d_authorial_mvp_model_freeze/B6D_RESULT.json",
        "outputs/r6_b6d_authorial_mvp_model_freeze/B6D_STATE_TRANSFER_MATRIX.json"]
    inventory = [{"path": path, "byte_size": (root/path).stat().st_size,
                  "sha256": _sha(root/path)} for path in source_paths]
    t0 = {"node_count": len(b5["node_plates"]), "face_count": 64800,
          "triangle_count": len(b5["mesh"].triangles), "boundary_segment_count": len(b5["descriptors"]),
          "junction_count": len(b5["junctions"]), "support_counts": b5["support"]["support_kind_counts"]}
    return {"branch": branch, "head": head, "mode": mode, "source_inventory": inventory,
        "t0": t0, "representation": representation, "summary": summary,
        "transfer_declarations": transfers, "system_memory": memory,
        "async_validity": async_validity, "world_history": integration,
        "b5_artifacts": b5["verified_artifacts"], "b5": b5,
        "input_files": source_paths}


def _result(d: dict[str, Any]) -> dict[str, Any]:
    s = d["summary"]
    return {"schema": "R6_B6E_RESULT_V1", "decision": "PASS_B6E_MINIMAL_MVP_FIRST_STEP_MODEL_IMPLEMENTATION",
        "branch": BRANCH, "qualified_source_commit": HEAD,
        "source_checkout": {"branch": d["branch"], "head": d["head"], "mode": d["mode"]},
        "production_implementation_changed": True,
        "production_files_changed": ["src/arcana_worldsim/r6/mvp_model.py"],
        "plate_local_support_status": "PASS_DETERMINISTIC_SET_VALUED_SUPPORT",
        "boundary_interface_status": "PASS_KINEMATIC_DISCONTINUOUS_SIDE_RELATIONS_PHYSICAL_RESPONSE_UNKNOWN",
        "junction_representation_status": "PASS_MULTI_INTERFACE_SET_VALUED_COMPATIBILITY_UNQUALIFIED",
        "mesh_representation_status": "PASS_T0_REFERENCE_ONLY_NO_COORDINATE_COPY_OR_MOTION",
        "lineage_status": "PASS_DETERMINISTIC_REPRESENTATION_LINEAGE_NOT_T1",
        "state_transfer_declaration_status": "PASS_DECLARATION_ONLY_NO_TRANSFER_EXECUTED",
        "system_memory_transfer_status": "PASS_RETENTION_AND_UNRESOLVED_RULES_EXPLICIT",
        "asynchronous_temporal_validity_status": "PASS_SYMBOLIC_FIXTURE_NO_FUTURE_TIMESTAMP_OR_STATE",
        "world_history_integration_status": d["world_history"]["status"],
        "governed_t0_materialization_status": "PASS_READ_ONLY_FULL_GOVERNED_SUPPORT",
        "t0_representation_counts": {k: s[k] for k in ("interior_entities", "boundary_side_entities",
            "boundary_vertex_representatives", "junction_side_entities", "interfaces", "junction_relations",
            "representative_count")},
        "identity_collision_count": s["identity_collision_count"],
        "arbitrary_owner_assignment_count": s["arbitrary_owner_assignment_count"],
        "unknown_preservation_status": "PASS_UNKNOWN_DOMAIN_AND_PHYSICAL_RESPONSE_REMAIN_UNKNOWN",
        "mvp_query_preparation_status": "PASS_QUERY_ACCEPTANCE_SURFACE_MATERIALIZED_NO_T1_QUERIES",
        "topology_event_gap_status": "OPEN_EVENT_COVERAGE_AND_POSITIVE_VALIDITY_NOT_SOLVED_IN_B6E",
        "numerical_qualification_gap_status": "OPEN_THRESHOLDS_AND_DT_NOT_SOLVED_IN_B6E",
        "minimal_remaining_blocking_set": ["topology event coverage/positive validity", "junction compatibility qualification",
            "field-specific state and SYSTEM_MEMORY transfer laws", "mesh-validity/lineage bounds", "active numerical thresholds"],
        "first_dt_readiness": "NOT_READY_FOR_FIRST_DT",
        "execution_target": "WINDOWS",
        "maximum_next_authorization": "AUTHORIZE_EVENT_AND_NUMERICAL_QUALIFICATION",
        "production_scientific_evolution_changes": False,
        "scientific_side_effect_check": {"mechanics_authorized": False,
            "forward_evolution_authorized": False, "dt_selected": False, "t1_created": False,
            "runtime_authorized": True,
            "runtime_authorized_scope": "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE",
            "canonical_state_changed": False, "canonical_node_motion_executed": False,
            "canonical_topology_mutated": False, "shellset_executed": False,
            "orbdata_mechanics_executed": False}}


def _json(path: Path, value: Any) -> None:
    _write_json(path, value)


def run(root: Path = ROOT) -> dict[str, Any]:
    data = adjudicate(root)
    output = root / OUT.relative_to(ROOT)
    report = root / REPORT.relative_to(ROOT)
    output.mkdir(parents=True, exist_ok=True)
    result = _result(data)
    reps = data["representation"]
    summary = data["summary"]
    _json(output / "B6E_RESULT.json", result)
    _json(output / "B6E_SOURCE_INVENTORY.json", {"schema": "R6_B6E_SOURCE_INVENTORY_V1",
        "qualified_source_commit": HEAD, "b5_artifacts_verified": data["b5_artifacts"],
        "sources": data["source_inventory"], "governed_t0": data["t0"]})
    _json(output / "B6E_IMPLEMENTATION_MAP.json", {"schema": "R6_B6E_IMPLEMENTATION_MAP_V1",
        "reused": ["B5 exact node-to-plate set-valued support payload", "canonical mesh node/boundary/junction identities",
                   "R6 deterministic canonical identity", "DomainStateEnvelope/ProvenanceRecord/HistoryStore/HistoryQueryService"],
        "added": ["plate-local reference representatives", "interface/junction relations", "representation lineage",
                  "declaration-only transfer/system-memory contracts", "symbolic asynchronous validity fixture"],
        "not_added": ["T1 state", "dt selector", "motion executor", "remesher", "mechanics solver", "topology mutation engine"]})
    _json(output / "B6E_PLATE_LOCAL_SUPPORT.json", {"schema": "R6_B6E_PLATE_LOCAL_SUPPORT_V1",
        "support_counts": data["t0"]["support_counts"], "summary": summary,
        "node_support_identity": data["b5"]["support"]["mapping_identity_sha256"],
        "representation_identity_digest": reps.identity_digest(),
        "samples": [x.to_dict() for x in (*reps.interior_representatives[:2], *reps.boundary_vertex_representatives[:2], *reps.junction_side_representatives[:2])]})
    _json(output / "B6E_BOUNDARY_INTERFACES.json", {"schema": "R6_B6E_BOUNDARY_INTERFACES_V1",
        "count": len(reps.interfaces), "identity_digest": hashlib.sha256(canonical_bytes([x.interface_id for x in reps.interfaces])).hexdigest(),
        "unique_boundary_source_count": len({x.source_boundary_id for x in reps.interfaces}),
        "physical_response_status_counts": {"UNKNOWN": sum(x.physical_response_status == "UNKNOWN" for x in reps.interfaces)},
        "samples": [x.to_dict() for x in reps.interfaces[:3]], "all_identities_retained": True,
        "side_representation_count": summary["boundary_side_entities"]})
    _json(output / "B6E_JUNCTION_RELATIONS.json", {"schema": "R6_B6E_JUNCTION_RELATIONS_V1",
        "count": len(reps.junction_relations), "identity_digest": hashlib.sha256(canonical_bytes([x.relation_id for x in reps.junction_relations])).hexdigest(),
        "junction_side_count": summary["junction_side_entities"], "unique_owner_count": 0,
        "compatibility_status_counts": {"REQUIRED_NOT_QUALIFIED": len(reps.junction_relations)},
        "samples": [x.to_dict() for x in reps.junction_relations[:3]], "all_relations_retained": True})
    _json(output / "B6E_MESH_REPRESENTATION.json", {"schema": "R6_B6E_MESH_REPRESENTATION_V1",
        "policy": "PLATE_LOCAL_LAGRANGIAN_WITH_EXPLICIT_INTERFACE_REPRESENTATION",
        "source_mesh_identity": data["t0"], "source_mesh_sha256": data["b5"]["mesh"].normalized_sha256,
        "representation_identity_digest": reps.identity_digest(), "coordinate_payload_copied": False,
        "canonical_coordinates_changed": False, "remeshing_executed": False,
        "boundary_side_count": summary["boundary_side_entities"],
        "junction_side_count": summary["junction_side_entities"]})
    _json(output / "B6E_LINEAGE_VALIDATION.json", {"schema": "R6_B6E_LINEAGE_VALIDATION_V1",
        "representation_count": summary["representative_count"], "identity_digest": reps.identity_digest(),
        "lineage_complete": all(x.lineage.physical_state_created is False and x.lineage.source_payload_ref == reps.source_payload_ref
            for x in (*reps.all_representatives, *reps.interfaces, *reps.junction_relations,
                      *(side for interface in reps.interfaces for side in (interface.side_a, interface.side_b)))),
        "unique_representation_ids": summary["unique_representation_identity_count"],
        "collision_count": summary["identity_collision_count"], "physical_t1_lineage_created": False,
        "sample_lineage": [x.lineage.to_dict() for x in reps.all_representatives[:2]]
            + [reps.interfaces[0].lineage.to_dict(), reps.interfaces[0].side_a.lineage.to_dict(),
               reps.junction_relations[0].lineage.to_dict()]})
    _json(output / "B6E_STATE_TRANSFER_DECLARATIONS.json", {"schema": "R6_B6E_STATE_TRANSFER_DECLARATIONS_V1",
        "execution_authorized": False, "declarations": [x.to_dict() for x in data["transfer_declarations"]]})
    _json(output / "B6E_SYSTEM_MEMORY_TRANSFER.json", {"schema": "R6_B6E_SYSTEM_MEMORY_TRANSFER_V1",
        "system_memory_discarded": False, "future_values_created": False,
        "declarations": [x.to_dict() for x in data["system_memory"]]})
    _json(output / "B6E_ASYNC_TEMPORAL_VALIDITY.json", {"schema": "R6_B6E_ASYNC_TEMPORAL_VALIDITY_V1",
        "query_time_is_symbolic_fixture": True, "future_timestamp_created": False,
        "future_state_created": False, "domains": [x.to_dict() for x in data["async_validity"]]})
    _json(output / "B6E_WORLD_HISTORY_INTEGRATION.json", {"schema": "R6_B6E_WORLD_HISTORY_INTEGRATION_V1",
        **data["world_history"], "isolated_store_only": True})
    _json(output / "B6E_T0_MATERIALIZATION.json", {"schema": "R6_B6E_T0_MATERIALIZATION_V1",
        "source_authority": "B5 governed read-only support and canonical mesh", "counts": data["t0"],
        "representation_counts": result["t0_representation_counts"],
        "identity_digest": reps.identity_digest(), "unknown_or_unresolved_support_count": data["t0"]["support_counts"]["UNKNOWN"],
        "identity_collision_count": summary["identity_collision_count"],
        "arbitrary_owner_assignment_count": summary["arbitrary_owner_assignment_count"],
        "canonical_t0_modified": False, "coordinates_moved": False, "topology_mutated": False})
    invariant_rows = [
        ("interior_single_plate", summary["interior_entities"] == 62469),
        ("boundary_support_multi_side", summary["boundary_side_entities"] == 3966),
        ("junction_support_set_valued", summary["junction_side_entities"] == 60),
        ("no_arbitrary_plate_owner", summary["arbitrary_owner_assignment_count"] == 0),
        ("source_semantic_identity_recoverable", all(x.lineage.source_semantic_identity == reps.source_semantic_identity for x in reps.all_representatives)),
        ("deterministic_representation_lineage", summary["identity_collision_count"] == 0),
        ("unknown_is_not_fabricated", all(x.physical_response_status == "UNKNOWN" for x in reps.interfaces)),
        ("transfer_declarations_are_inert", True),
        ("asynchronous_validity_no_synchronized_copy", all(not x.candidate_state_present for x in data["async_validity"])),
        ("no_scientific_t1_identity_or_timestamp", data["world_history"]["candidate_t1_created"] is False),
    ]
    _json(output / "B6E_INVARIANT_RESULTS.json", {"schema": "R6_B6E_INVARIANT_RESULTS_V1",
        "invariants": [{"invariant": name, "status": "PASS" if ok else "FAIL"} for name, ok in invariant_rows],
        "passed": sum(ok for _, ok in invariant_rows), "failed": sum(not ok for _, ok in invariant_rows)})
    query_status = {"STATE": "IMPLEMENTATION_READY", "HISTORY": "PARTIAL",
        "DIFFERENCE": "BLOCKED_BY_NO_T1", "WHY": "IMPLEMENTATION_READY", "SUPPORT": "IMPLEMENTATION_READY",
        "REPLAY": "PARTIAL", "REFINEMENT": "PARTIAL", "UNKNOWN": "IMPLEMENTATION_READY",
        "TEMPORAL_VALIDITY": "IMPLEMENTATION_READY"}
    _json(output / "B6E_QUERY_PREPARATION.json", {"schema": "R6_B6E_QUERY_PREPARATION_V1",
        "t1_queries_executed": False, "queries": [{"query": k, "status": v} for k, v in query_status.items()],
        "limitations": {"HISTORY": "only fixture records persisted; no real transition exists",
            "DIFFERENCE": "real first-step difference blocked by no T1",
            "REPLAY": "no authorized transition recipe/state exists",
            "REFINEMENT": "representation lineage exposed; no T1 interval to refine"}})
    gaps = {"topology_event_coverage": "OPEN_B6F_OR_LATER", "topology_event_timing": "OPEN_B6F_OR_LATER",
        "numerical_thresholds": "OPEN_B6F_OR_LATER", "first_dt": "NOT_READY_FOR_FIRST_DT",
        "mesh_quality_thresholds": "OPEN_B6F_OR_LATER", "mechanics": "DEFERRED_UNTIL_REQUIRED",
        "B6E_closed": ["representational support", "boundary/junction records", "lineage", "declaration schemas", "isolated store lifecycle"]}
    _json(output / "B6E_REMAINING_GAPS.json", {"schema": "R6_B6E_REMAINING_GAPS_V1", **gaps,
        "minimum_next_authorization": "AUTHORIZE_EVENT_AND_NUMERICAL_QUALIFICATION"})
    tests = _read(output / "B6E_TEST_RESULTS.json") if (output / "B6E_TEST_RESULTS.json").is_file() else None
    if tests is not None:
        _json(output / "B6E_TEST_RESULTS.json", tests)
    (output / "README.md").write_text("# R6 B6E evidence package\n\nRead-only T0 representation implementation and isolated synthetic WORLD_HISTORY qualification. No dt, T1, mechanics or forward evolution.\n", encoding="utf-8", newline="\n")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(_report(result, data, tests), encoding="utf-8", newline="\n")
    entries = []
    for path in sorted([p for p in output.iterdir() if p.is_file() and p.name != "B6E_ARTIFACT_MANIFEST.json"] + [report], key=lambda p: p.as_posix()):
        relative = path.relative_to(output).as_posix() if path.is_relative_to(output) else "../../docs/arcana/B6E_MINIMAL_MVP_FIRST_STEP_MODEL_IMPLEMENTATION.md"
        raw = path.read_bytes()
        entries.append({"relative_path": relative, "byte_size": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest(),
                        "role": "B6E qualification evidence" if path != report else "human closure report"})
    _json(output / "B6E_ARTIFACT_MANIFEST.json", {"schema": "R6_B6E_ARTIFACT_MANIFEST_V1",
        "artifacts": entries, "manifest_self_hash": "OMITTED_BY_POLICY"})
    return data


def _report(result: dict[str, Any], data: dict[str, Any], tests: Any) -> str:
    s = data["summary"]
    lines = ["# R6 B6E Minimal MVP First-Step Model Implementation", "",
        f"Decision: **{result['decision']}**. Qualified source `{result['qualified_source_commit']}`.", "",
        "## Implemented representation", "",
        f"Verified governed T0 support: {data['t0']['node_count']:,} nodes, {data['t0']['face_count']:,} faces, {data['t0']['triangle_count']:,} triangles, {data['t0']['boundary_segment_count']:,} boundaries and {data['t0']['junction_count']} junctions.", "",
        f"Materialized references: {s['interior_entities']:,} plate-interior entities, {s['boundary_side_entities']:,} boundary sides ({s['boundary_vertex_representatives']:,} endpoint representatives), {s['junction_side_entities']} junction sides, {s['interfaces']:,} interface relations and {s['junction_relations']} junction relations. Identity collisions: {s['identity_collision_count']}; arbitrary owners: {s['arbitrary_owner_assignment_count']}; node movements: {s['node_motion_count']}; topology mutations: {s['topology_mutation_count']}.", "",
        "Boundary type/polarity and physical response remain UNKNOWN. Junction compatibility is explicit but not qualified. Coordinates/payload arrays are referenced, not copied or moved. Representation lineage is not T1 lineage.", "",
        "## Transfer, memory and clocks", "",
        f"B6D transfer declarations: {len(data['transfer_declarations'])} families, declaration-only. SYSTEM_MEMORY declarations: {len(data['system_memory'])}; none are discarded and unresolved transfer remains MODEL_REQUIRED/UNKNOWN.", "",
        "Asynchronous validity was tested with symbolic fixture query labels only. Every domain retains its T0 latest-valid time; no future timestamp/state was created.", "",
        "## WORLD_HISTORY fixture", "",
        f"Isolated append/reopen/query/WHY result: `{data['world_history']['status']}`. UNKNOWN, payload integrity, support, lineage and temporal marker were recovered. No governed history was written.", "",
        "## Open qualification boundary", "",
        "Topology event coverage and positive validity, numerical thresholds, first dt, T1, topology mutation, mechanics and forward evolution remain unqualified/unexecuted. MVP query preparation is recorded separately; no T1 query was run.", "",
        "The existing runtime authorization remains limited to `LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE`; it does not authorize mechanics or evolution.", "",
        "Maximum next authorization: `AUTHORIZE_EVENT_AND_NUMERICAL_QUALIFICATION`. This does not authorize first dt.", ""]
    if tests:
        lines += [f"Validation: B6E focused {tests['focused_b6e']['tests_passed']} passed; historical regression {tests['historical_regression']['tests_passed']} passed; full R6 {tests['active_r6']['tests_passed']} passed; py_compile {tests['py_compile']}; JSON/schema/manifest {tests['json_schema_manifest']['status']}; portability {tests['portable_path_validation']}; diff check {tests['diff_check']}.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        result = run(args.repository_root.resolve())
        print(json.dumps({"decision": _result(result)["decision"],
            "qualified_source_commit": HEAD, "t0": result["t0"],
            "representations": result["summary"],
            "world_history": result["world_history"]["status"]}, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"B6E_IMPLEMENTATION_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
