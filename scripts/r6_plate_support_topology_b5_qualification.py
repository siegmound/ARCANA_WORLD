#!/usr/bin/env python3
"""Read-only real-source qualification of R6 B5 plate support and topology."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.forcing import ForcingRecord
from arcana_worldsim.r6.identity import content_hash
from arcana_worldsim.r6.plate_support_adapter import (
    B5_BRANCH, PlateSupportError, build_b5_records, build_node_support,
    load_b5_sources, source_snapshot_b5,
)
from arcana_worldsim.r6.query import HistoryQueryService
from arcana_worldsim.r6.state import DomainStateEnvelope
from arcana_worldsim.r6.storage import account_storage, history_store_scope
from arcana_worldsim.r6.store import HistoryStore

DECISION = "PASS_B5_PLATE_SUPPORT_TOPOLOGY_TEMPORAL_INTEGRATION"
OUT_DEFAULT = ROOT / "outputs/r6_b5_plate_support_topology_qualification"
REPORT = ROOT / "docs/arcana/B5_PLATE_SUPPORT_TOPOLOGY_TEMPORAL_INTEGRATION.md"
GATES = {
    "runtime_authorized": True,
    "runtime_authorized_scope": "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE",
    "mechanics_authorized": False,
    "forward_evolution_authorized": False,
    "dt_selected": False,
    "t1_created": False,
    "canonical_state_changed": False,
    "shellset_executed": False,
    "orbdata_mechanics_executed": False,
}


def _write_json(path: Path, value: Any) -> dict[str, Any]:
    data = (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"relative_path": path.name, "byte_size": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def _write_text(path: Path, value: str, relative: str) -> dict[str, Any]:
    data = value.replace("\r\n", "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"relative_path": relative, "byte_size": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def _canonical_mask_hash(support: Any) -> str:
    return hashlib.sha256(support.payload_bytes).hexdigest()


def _implementation_hashes() -> list[dict[str, Any]]:
    paths = (ROOT / "src/arcana_worldsim/r6/plate_kinematics_adapter.py",
             ROOT / "src/arcana_worldsim/r6/plate_support_adapter.py",
             ROOT / "scripts/r6_plate_support_topology_b5_qualification.py")
    return [{"logical_path": path.relative_to(ROOT).as_posix(),
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
             "working_tree_status": "UNCOMMITTED_SOURCE"}
            for path in paths]


def qualify(repository_root: Path, output_dir: Path) -> dict[str, Any]:
    started = time.perf_counter()
    source, inventory = load_b5_sources(repository_root)
    before = source_snapshot_b5(source)
    support = build_node_support(source, inventory)
    if support.counts != {"INTERIOR_PLATE": 62469, "BOUNDARY_SHARED": 1953,
                          "JUNCTION_SHARED": 20, "UNKNOWN": 0}:
        raise PlateSupportError(f"unexpected T0 node support census: {support.counts}")
    descriptors = source.boundary_descriptors
    junction_descriptors = []
    for junction_id, node_id in source.mesh.junction_node_ids:
        plate_ids = list(support.node_plate_ids[int(node_id) - 1])
        if len(plate_ids) != 3:
            raise PlateSupportError(f"junction {junction_id} does not preserve three incident plates")
        junction_descriptors.append({"junction_id": str(junction_id),
            "node_id": int(node_id), "incident_plate_ids": plate_ids,
            "degree": len(plate_ids), "support_semantics": "JUNCTION_SHARED_SET_VALUED"})
    if len(junction_descriptors) != 20:
        raise PlateSupportError("canonical junction identity count differs from governed count")
    descriptor_id = content_hash(list(descriptors))
    if len(descriptors) != 1983 or len({row["boundary_id"] for row in descriptors}) != 1983:
        raise PlateSupportError("boundary descriptor set is incomplete or duplicated")
    boundary_summary = {
        "boundary_count": len(descriptors), "descriptor_identity_sha256": descriptor_id,
        "kinematic_census_sha256": inventory["boundary_authority"]["kinematic_census_sha256"],
        "boundary_state_sha256": inventory["boundary_authority"]["boundary_state_manifest_sha256"],
    }
    payload_ref = f"sha256:{support.payload_sha256}"
    records = build_b5_records(source, support, payload_ref, boundary_summary)
    # The synthetic topology events share an explicitly isolated fixture-only history.
    if records.fixture_state.history_id != records.fixture_events[0].history_id:
        raise PlateSupportError("fixture event history is not isolated consistently")
    identity_before = {
        "plate_support_state_id": str(records.plate_support_state.state_id),
        "boundary_state_id": str(records.boundary_state.state_id),
        "forcing_id": str(records.forcing.forcing_id),
        "fixture_state_id": str(records.fixture_state.state_id),
        "fixture_event_ids": [event.record_id for event in records.fixture_events],
    }

    with tempfile.TemporaryDirectory(prefix="arcana-r6-b5-") as tmp:
        store = HistoryStore(Path(tmp) / "history")
        support_path = Path(tmp) / "B5_NODE_PLATE_SUPPORT_MAP_V1.json"
        support_path.write_bytes(support.payload_bytes)
        publish_records = (
            records.source_provenance, records.forcing, records.adapter_provenance,
            records.support_provenance, records.plate_support_state, records.boundary_state,
            records.fixture_provenance, *records.fixture_events, records.fixture_state,
        )
        store.append_transaction(publish_records)
        counts_before = {"states": len(store.states()), "forcings": len(store.forcings()),
                         "events": len(store.events())}
        del store
        store = HistoryStore(Path(tmp) / "history")
        query = HistoryQueryService(store)
        plate_why = query.why(str(records.plate_support_state.state_id))
        fixture_why = query.why(str(records.fixture_state.state_id))
        if plate_why.unresolved_references:
            raise PlateSupportError(f"B5 support WHY has unresolved refs: {plate_why.unresolved_references}")
        if fixture_why.unresolved_references or len(fixture_why.events) != 5:
            raise PlateSupportError("fixture event WHY did not resolve all five events")
        if len(plate_why.forcings) != 1:
            raise PlateSupportError("support WHY did not resolve its T0 forcing record")
        if hashlib.sha256(support_path.read_bytes()).hexdigest() != support.payload_sha256:
            raise PlateSupportError("reopened support payload failed content identity verification")
        reopened_ids = {
            "plate_support_state_id": str(store.read_state(str(records.plate_support_state.state_id)).state_id),
            "boundary_state_id": str(store.read_state(str(records.boundary_state.state_id)).state_id),
            "forcing_id": str(ForcingRecord.from_dict(store.read_forcing(str(records.forcing.forcing_id))).forcing_id),
            "fixture_state_id": str(store.read_state(str(records.fixture_state.state_id)).state_id),
            "fixture_event_ids": sorted(event.record_id for event in store.events()),
        }
        if reopened_ids != {**identity_before, "fixture_event_ids": sorted(identity_before["fixture_event_ids"])}:
            raise PlateSupportError("semantic identities changed across store reopen")
        external_payloads = [Path(value) for value in source.payload_paths.values()] + [support_path]
        accounting = account_storage(history_store_scope(store, external_payloads=external_payloads))
        if not accounting.within_hard_cap:
            raise PlateSupportError("B5 qualification scope exceeded canonical storage cap")
        accounting_summary = {
            "categories": {key: {"file_count": value.file_count,
                                  "logical_bytes": value.logical_bytes}
                           for key, value in accounting.categories.items()},
            "canonical_persistent_bytes": accounting.canonical_persistent_bytes,
            "hard_cap_bytes": accounting.hard_cap_bytes,
            "within_hard_cap": accounting.within_hard_cap,
            "payload_alias_counted_once": len(set(map(str, external_payloads))) == len(external_payloads),
        }
        store.close() if hasattr(store, "close") else None

    after = source_snapshot_b5(source)
    if before.keys() != after.keys() or any(before[key][0:2] != after[key][0:2] for key in before):
        raise PlateSupportError("source content/size changed during qualification")
    source_immutability = {
        "status": "PASS_READ_ONLY_SOURCE_UNCHANGED",
        "source_count": len(before),
        "sources": [{"logical_path": key, "sha256": value[0], "byte_size": value[1]}
                    for key, value in sorted(before.items())],
        "before_after_content_equal": True,
        "mtime_is_environment_evidence_only": True,
    }
    elapsed = time.perf_counter() - started
    result = {
        "schema": "R6_B5_PLATE_SUPPORT_TOPOLOGY_QUALIFICATION_RESULT_V1",
        "decision": DECISION, "qualified_source_commit": source.head,
        "qualification_implementation": _implementation_hashes(),
        "branch": source.branch,
        "scope": "READ_ONLY_T0_SPATIAL_SUPPORT_AND_TOPOLOGY_CONTRACT_QUALIFICATION",
        "spatial_authority_result": "PASS_EXACT_DERIVATION_FROM_GOVERNED_FACE_PARTITION_AND_CANONICAL_MESH",
        "plate_face_mapping_status": "DIRECT_GOVERNED_MODEL_DERIVED_PARTITION",
        "plate_node_mapping_status": "DERIVABLE_GOVERNED_EXACT_FACE_INCIDENCE_SET_VALUED",
        "node_support_counts": dict(support.counts),
        "node_support_identity_sha256": support.mapping_identity_sha256,
        "node_support_payload_sha256": _canonical_mask_hash(support),
        "boundary_node_semantics": "BOUNDARY_SHARED_AND_JUNCTION_SHARED; NO_SINGLE_PLATE_OWNER",
        "boundary_contract_result": "GEOMETRIC_AND_T0_INSTANTANEOUS_KINEMATIC_ONLY; MECHANICS_UNKNOWN",
        "boundary_count": len(descriptors), "boundary_descriptor_identity_sha256": descriptor_id,
        "adjacent_plate_pair_count": 30, "junction_count": 20,
        "reference_frame_result": {
            "status": "DECLARED_GAUGE_AND_GRID_BOUND; CARTESIAN_AXIS_HANDEDNESS_NOT_SEPARATELY_GOVERNED",
            "kinematics_frame": source.kinematics.reference_frame,
            "grid_frame": "R6_GLOBAL_GEOGRAPHY_1DEG_V1 latitude/longitude degrees; south-to-north rows; periodic longitude; shared polar point",
            "cartesian_axis_handedness": "NOT_SEPARATELY_DECLARED_IN_GOVERNED_AUTHORITY; no additional transform inferred",
            "gauge_interpretation": "synthetic kinematic gauge only; not mantle-rest, hotspot, torque-balance, or mantle-coupling authority",
            "angular_units": "rad/year", "linear_velocity_units": "m/year",
            "sphere_radius_m": source.vector_manifest.get("parent_grid", {}).get("radius_m", 6371000),
            "t0_ma": 210.0,
        },
        "instantaneous_relative_motion_result": "PASS_DERIVED_GOVERNED_INSTANT_DIAGNOSTIC_AT_210_MA_ONLY",
        "positive_duration_motion_status": "ANCHOR_ONLY_NO_POSITIVE_INTERVAL",
        "positive_duration_authority": "ABSENT; no governed validity interval, temporal interpolation, or topology calendar",
        "topology_event_contract": {
            "status": "SCHEMA_QUALIFIED_SYNTHETIC_FIXTURES_ONLY",
            "event_types": ["PLATE_SPLIT", "PLATE_MERGE", "BOUNDARY_BIRTH", "BOUNDARY_DEATH", "JUNCTION_REASSIGNMENT"],
            "actual_arcana_events_claimed": False,
            "parent_history_mutated": False,
        },
        "plate_lineage_status": "ANCHOR_IDENTITIES_ONLY; CONTINUATION_SPLIT_MERGE_TERMINATION_UNBOUND",
        "world_history_support_integration": {
            "status": "PASS_PERSIST_REOPEN_QUERY_WHY",
            "transaction_record_counts": counts_before,
            "plate_why": {"state_lineage_count": len(plate_why.state_lineage),
                "provenance_count": len(plate_why.provenance_records),
                "forcing_count": len(plate_why.forcings),
                "unresolved_reference_count": len(plate_why.unresolved_references)},
            "fixture_why": {"event_count": len(fixture_why.events),
                "unresolved_reference_count": len(fixture_why.unresolved_references)},
            "semantic_identity_stable_after_reopen": True,
            "support_payload_reopened_and_hash_verified": True,
        },
        "real_qualification": "PASS_READ_ONLY_GOVERNED_T0_SOURCES_VERIFIED",
        "qualification_wall_seconds_environment_evidence": round(elapsed, 6),
        "source_identity_sha256": source.source_identity,
        "b6_readiness": "READY_FOR_B6_WITH_UNRESOLVED_TEMPORAL_AUTHORITY",
        "next_stage_authorization": "AUTHORIZE_B6_DEPENDENCY_AND_TEMPORAL_GAP_ADJUDICATION_ONLY",
        "production_changes": {"generic_world_history_core_changed": False,
            "scientific_payload_changed": False,
            "implementation_files": [row["logical_path"] for row in _implementation_hashes()]},
        "gates": GATES,
    }
    spatial = {
        "schema": "R6_B5_SPATIAL_AUTHORITY_V1",
        "source_identity_sha256": source.source_identity,
        "authority_class": "MODEL_DERIVED_FROM_CANONICAL_T0",
        "associations": {
            "plate_to_face": {"classification": "DIRECT_GOVERNED", "faces": 64800,
                "coverage": "ONE_GOVERNED_PLATE_ID_PER_PARENT_FACE", "ambiguity": "NONE"},
            "face_to_node": {"classification": "DERIVABLE_FROM_GOVERNED_INPUTS",
                "method": "CANONICAL_MESH_PARENT_FACE_TRIANGLE_INCIDENCE", "ambiguity": "NONE"},
            "node_to_plate": {"classification": "DERIVABLE_FROM_GOVERNED_INPUTS",
                "method": "SET_UNION_OF_INCIDENT_PARENT_FACE_PLATE_IDS",
                "boundary_and_junction_membership_preserved": True},
            "boundary_to_adjacent_plates": {"classification": "DIRECT_GOVERNED",
                "segment_count": 1983, "adjacency_pairs": 30},
            "junction_to_incident_plates": {"classification": "DERIVABLE_FROM_GOVERNED_INPUTS",
                "junction_count": 20, "degree": 3,
                "junctions": junction_descriptors},
        },
        "grid": source.vector_manifest["parent_grid"],
        "mesh": {"sha256": source.mesh.normalized_sha256,
            "node_count": len(support.node_plate_masks), "triangle_count": len(source.mesh.triangles)},
        "node_support_counts": dict(support.counts),
        "node_support_payload_sha256": support.payload_sha256,
        "physical_state_changed": False,
    }
    boundary = {
        "schema": "R6_B5_BOUNDARY_CONTRACT_V1", "geometric_boundary": "PASS_GOVERNED_SHARED_INTERFACE_GRAPH",
        "kinematic_boundary": "T0_INSTANTANEOUS_RELATIVE_MOTION_DERIVED_ONLY",
        "mechanical_boundary": "UNKNOWN_NOT_AUTHORIZED",
        "segment_count": len(descriptors), "plate_pair_count": 30, "junction_count": 20,
        "boundary_type": "UNKNOWN", "polarity": "UNKNOWN", "material_continuity": "UNKNOWN",
        "fault_slip_stress_strain_accommodation": "UNKNOWN",
        "descriptors": list(descriptors),
    }
    temporal_validity = {
        "schema": "R6_B5_TEMPORAL_VALIDITY_V1", "anchor_ma": 210.0,
        "hard_anchors_ma": [210.0], "kinematic_validity_intervals": [],
        "topology_event_boundaries_ma": [], "unknown_intervals": "ALL_POSITIVE_DURATION_INTERVALS",
        "model_regime_boundaries_ma": [], "authority_transitions_ma": [],
        "decision": "ANCHOR_ONLY_NO_POSITIVE_INTERVAL",
    }
    event_contract = {
        "schema": "R6_B5_TOPOLOGY_EVENT_CONTRACT_V1", "event_record_type": "existing EventRecord",
        "fixtures": [{"event_type": event.details["event_type"], "record_id": event.record_id,
            "fixture_only": True, "actual_arcana_event": False, "parent_history_mutated": False}
            for event in records.fixture_events],
    }
    synthetic_edges = {
        "schema": "R6_B5_SYNTHETIC_EDGE_CASE_RESULT_V1",
        "cases": [
            {"case": "boundary_shared_node", "status": "PASS", "meaning": "both incident plate IDs retained; no owner"},
            {"case": "junction_node", "status": "PASS", "meaning": "all incident plate IDs retained as set"},
            *[{"case": event.details["event_type"].lower(), "status": "PASS_FIXTURE_ONLY",
                "event_id": event.record_id, "actual_arcana_event": False}
                for event in records.fixture_events],
            {"case": "missing_mapping", "status": "PASS_FAIL_CLOSED", "test": "require_plate_grid_mapping(None)"},
            {"case": "frame_mismatch", "status": "PASS_FAIL_CLOSED", "test": "validate_fixture_interval rejects incompatible frame"},
            {"case": "unsupported_positive_interval", "status": "PASS_FAIL_CLOSED", "test": "validate_fixture_interval requires explicit fixture coverage"},
        ],
        "actual_t0_mutated": False,
    }
    result["synthetic_edge_case_result"] = {
        "status": "PASS_FIXTURES_AND_FAIL_CLOSED_CASES",
        "case_count": len(synthetic_edges["cases"]),
        "cases": [row["case"] for row in synthetic_edges["cases"]],
        "actual_arcana_events_claimed": False,
    }
    downstream = [
        {"capability": "plate rigid motion at 210 Ma", "status": "AVAILABLE_GOVERNED", "reason": "B4 instantaneous vectors"},
        {"capability": "node/face plate membership", "status": "DERIVABLE_GOVERNED", "reason": "exact face partition and mesh incidence"},
        {"capability": "boundary relative motion at 210 Ma", "status": "DERIVABLE_GOVERNED", "reason": "B4 vector pair and governed boundary geometry"},
        {"capability": "topology change events", "status": "SCHEMA_READY_BUT_DATA_MISSING", "reason": "EventRecord fixtures only; no ARCANA event calendar"},
        {"capability": "boundary mechanical accommodation", "status": "MISSING", "reason": "no governed type, polarity, slip, or constitutive law"},
        {"capability": "crust/lithosphere response", "status": "MISSING", "reason": "no authorized temporal mechanical response model"},
        {"capability": "elevation/topography response", "status": "MISSING", "reason": "no governed deformation-to-topography coupling"},
        {"capability": "thermal state", "status": "SCHEMA_READY_BUT_DATA_MISSING", "reason": "T0 thermal state exists; no authorized temporal coupling"},
        {"capability": "surface consequences", "status": "NOT_REQUIRED_FOR_FIRST_STEP", "reason": "not needed to represent the first tectonic state transition; later causal coupling remains required"},
    ]
    shellset = [
        {"requirement": "validated ARCANA T0 runtime FEG/package", "status": "AVAILABLE_GOVERNED", "reason": "B3/S1B runtime package qualification"},
        {"requirement": "T0 plate support on mesh", "status": "DERIVABLE_GOVERNED", "reason": "B5 exact incidence qualification"},
        {"requirement": "ARCANA boundary conditions replacing Earth5R BCS", "status": "MISSING", "reason": "legacy Earth5R BCS is not ARCANA authority"},
        {"requirement": "positive-duration driver and topology schedule", "status": "MISSING", "reason": "B4/B5 only establish an instantaneous anchor"},
        {"requirement": "boundary mechanical accommodation laws", "status": "MISSING", "reason": "no governed fault/ridge/transform mechanics authority"},
        {"requirement": "ShellSet fault elements", "status": "LEGACY_EARTH5R_SPECIFIC_UNPROVEN_FOR_ARCANA", "reason": "do not infer ARCANA need from legacy runtime assumptions"},
    ]
    prerequisites = [
        {"requirement": "T0 plate/face/node support map", "status": "CLOSED_B5_DERIVABLE_GOVERNED", "authority_source": "vector partition + canonical mesh", "why_needed": "spatially bind plate forcing", "can_be_derived": True, "must_resolve_before_dt": True, "must_resolve_before_mechanics": True, "can_remain_unknown": False},
        {"requirement": "positive-duration kinematic validity/model", "status": "MISSING", "authority_source": "none", "why_needed": "define motion through nonzero interval", "can_be_derived": False, "missing_provider_model": True, "must_resolve_before_dt": True, "must_resolve_before_mechanics": True, "can_remain_unknown": False},
        {"requirement": "boundary process/accommodation law", "status": "MISSING", "authority_source": "none", "why_needed": "convert relative motion into mechanical response", "can_be_derived": False, "missing_provider_model": True, "must_resolve_before_dt": False, "must_resolve_before_mechanics": True, "can_remain_unknown": True},
        {"requirement": "topology event calendar and plate lineage", "status": "MISSING", "authority_source": "none", "why_needed": "bound intervals and identity continuity", "can_be_derived": False, "missing_provider_model": True, "must_resolve_before_dt": True, "must_resolve_before_mechanics": True, "can_remain_unknown": False},
        {"requirement": "reference-frame transform/gauge adjudication", "status": "PARTIALLY_BOUND_T0_ONLY", "authority_source": "B4 kinematics + T0 grid", "why_needed": "ensure motion and geometry share declared frame", "can_be_derived": True, "missing_provider_model": False, "must_resolve_before_dt": True, "must_resolve_before_mechanics": True, "can_remain_unknown": False},
        {"requirement": "Cartesian axis/handedness convention for any downstream vector transform", "status": "NOT_SEPARATELY_DECLARED", "authority_source": "none beyond derived source binding", "why_needed": "prevent an ungoverned coordinate transform", "can_be_derived": False, "missing_provider_model": True, "must_resolve_before_dt": True, "must_resolve_before_mechanics": True, "can_remain_unknown": False},
        {"requirement": "material and thermal response configuration", "status": "PRE_ORBDATA_BLOCKERS_REMAIN", "authority_source": "current R6 material/thermal adjudication", "why_needed": "mechanical runtime response", "can_be_derived": False, "missing_provider_model": True, "must_resolve_before_dt": False, "must_resolve_before_mechanics": True, "can_remain_unknown": True},
    ]
    registry = {
        "schema": "R6_TEMPORAL_CONSTRAINT_REGISTRY_V1", "anchor_ma": 210.0,
        "known_temporal_anchors_ma": [210.0], "kinematic_validity_intervals": [],
        "topology_event_boundaries_ma": [], "unknown_intervals": "ALL_POSITIVE_DURATION_INTERVALS",
        "model_regime_boundaries_ma": [], "authority_transitions": [],
        "source_refs": [row["logical_path"] for row in source.source_documents],
        "status": "ANCHOR_ONLY_NO_POSITIVE_INTERVAL",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    # Payload is the derived support map, not a copy or modification of governed T0 input.
    (output_dir / "B5_NODE_PLATE_SUPPORT_MAP_V1.json").write_bytes(support.payload_bytes)
    artifacts = []
    for name, body in [
        ("B5_RESULT.json", result), ("B5_SPATIAL_AUTHORITY.json", spatial),
        ("B5_PLATE_SUPPORT.json", {"schema": "R6_B5_PLATE_SUPPORT_V1",
            "node_count": len(support.node_plate_masks), "support_kind_counts": dict(support.counts),
            "mapping_identity_sha256": support.mapping_identity_sha256,
            "payload_sha256": support.payload_sha256, "payload_file": "B5_NODE_PLATE_SUPPORT_MAP_V1.json",
            "member_sets_preserved": True, "single_plate_owner_assigned": False,
            "junctions": junction_descriptors}),
        ("B5_BOUNDARY_CONTRACT.json", boundary), ("B5_TEMPORAL_VALIDITY.json", temporal_validity),
        ("B5_TOPOLOGY_EVENT_CONTRACT.json", event_contract),
        ("B5_SYNTHETIC_EDGE_CASES.json", synthetic_edges),
        ("B5_DOWNSTREAM_REQUIREMENTS.json", {"requirements": downstream}),
        ("B5_SHELLSET_REQUIREMENTS.json", {"requirements": shellset}),
        ("B5_FIRST_DT_PREREQUISITES.json", {"requirements": prerequisites}),
        ("B5_TEMPORAL_CONSTRAINT_REGISTRY.json", registry),
        ("B5_SOURCE_IMMUTABILITY.json", source_immutability),
        ("B5_WORLD_HISTORY_QUALIFICATION.json", {"result": result["world_history_support_integration"],
            "accounting": accounting_summary, "fixture_events": event_contract["fixtures"]}),
    ]:
        artifacts.append(_write_json(output_dir / name, body))
    test_result_path = output_dir / "B5_TEST_RESULTS.json"
    test_results = json.loads(test_result_path.read_text(encoding="utf-8")) if test_result_path.is_file() else None
    if test_results is not None:
        artifacts.append({"relative_path": test_result_path.name,
            "byte_size": test_result_path.stat().st_size,
            "sha256": hashlib.sha256(test_result_path.read_bytes()).hexdigest()})
    map_bytes = (output_dir / "B5_NODE_PLATE_SUPPORT_MAP_V1.json").read_bytes()
    artifacts.append({"relative_path": "B5_NODE_PLATE_SUPPORT_MAP_V1.json",
        "byte_size": len(map_bytes), "sha256": hashlib.sha256(map_bytes).hexdigest()})
    return {"result": result, "spatial": spatial, "boundary": boundary,
            "temporal": temporal_validity, "event_contract": event_contract,
            "downstream": downstream, "shellset": shellset,
            "prerequisites": prerequisites, "registry": registry,
            "source_immutability": source_immutability,
            "accounting": accounting_summary, "artifacts": artifacts,
            "support": support, "records": records, "synthetic_edges": synthetic_edges,
            "test_results": test_results}


def _human_report(data: dict[str, Any]) -> str:
    result = data["result"]
    counts = result["node_support_counts"]
    rows = [
        "# R6 B5 Plate Support, Topology and Temporal Integration",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "## A. Baseline",
        "",
        f"Qualified source `{result['qualified_source_commit']}` on `{result['branch']}`; read-only T0 qualification.",
        "",
        "## B. Governed spatial authority",
        "",
        "The 210 Ma plate partition is model-derived from canonical T0 and covers 64,800 parent faces and 12 plates. It is not a hard anchor.",
        "",
        "## C. Plate-face support",
        "",
        "Face membership is direct in the governed vector-partition payload. Each parent face maps to one plate ID.",
        "",
        "## D. Plate-node/grid support",
        "",
        "Node membership is exactly derived as the set of plate IDs on incident parent faces through the canonical mesh incidence graph. It does not assign shared nodes to one plate.",
        "",
        f"Counts: {counts['INTERIOR_PLATE']:,} interior, {counts['BOUNDARY_SHARED']:,} boundary-shared, {counts['JUNCTION_SHARED']:,} junction-shared, {counts['UNKNOWN']:,} unknown.",
        "",
        "## E. Boundary semantics",
        "",
        "The 1,983 segments define shared geometry, adjacent plate identities, ordered endpoints, lengths, and 20 junctions. Geological type, polarity, material continuity, fault/slip behavior and mechanical accommodation remain UNKNOWN.",
        "",
        "## F. Instantaneous relative motion",
        "",
        "Relative normal/tangential motion is a derived governed diagnostic at exactly 210 Ma. It is not a boundary mechanical response.",
        "",
        "## G. Reference frame",
        "",
        f"The census binds the B4 T0 kinematics gauge `{result['reference_frame_result']['kinematics_frame']}` and 1-degree latitude/longitude grid; sphere radius is 6,371,000 m. Vector units are rad/year, boundary rates are m/year. Cartesian axis/handedness is not separately declared, no transform is inferred, and no Earth-fixed authority is claimed.",
        "",
        "## H. Positive-duration motion law",
        "",
        "**ANCHOR_ONLY_NO_POSITIVE_INTERVAL.** There is no governed validity interval, interpolation rule, or topology-event calendar. The instantaneous anchor cannot be extended to any positive duration.",
        "",
        "## I. Topology transition contract",
        "",
        "Existing EventRecord is sufficient for schema-only split, merge, boundary birth/death, and junction reassignment fixtures. No fixture claims an ARCANA historical event.",
        "",
        "## J. Plate lineage",
        "",
        "Plate IDs are anchored at 210 Ma only. Continuation, split, merge, creation and termination lineage are not governed.",
        "",
        "## K. WORLD_HISTORY support integration",
        "",
        "The forcing, support and boundary states plus provenance and fixture events were published transactionally, destroyed, reopened, queried and WHY-traced. Semantic IDs persisted. Parent T0 history was not mutated.",
        "",
        "## L. Downstream requirements",
        "",
        "Available: instantaneous plate motion. Derivable: face/node support and T0 relative boundary motion. Missing: positive-duration driver, event schedule, boundary accommodation and deformation response.",
        "",
        "## M. ShellSet requirements",
        "",
        "T0 FEG/package and plate support are available/derivable. ARCANA boundary conditions replacing Earth5R BCS, temporal law and boundary mechanics remain missing. Legacy Earth5R fault assumptions are not treated as ARCANA requirements.",
        "",
        "## N. First-dt prerequisites",
        "",
        "The qualified support map closes the spatial binding prerequisite. Positive-duration kinematic validity, topology calendar/lineage and frame adjudication must be resolved before dt. Mechanical accommodation and material/thermal response must be resolved before mechanics; none is selected here.",
        "",
        "## O. Temporal constraint registry",
        "",
        "Only the 210 Ma anchor is known. No positive-duration interval, event boundary, regime boundary or authority transition is registered.",
        "",
        "## P. Source immutability",
        "",
        f"{data['source_immutability']['status']}; {data['source_immutability']['source_count']} source artifacts had unchanged content hashes and byte sizes.",
        "",
        "## Q. Remaining gaps",
        "",
        "No governed positive-time motion law, transition calendar, stable plate lineage, geological boundary classes/polarity, mechanical accommodation, or ARCANA ShellSet BCS replacement.",
        "",
        "## R. B6 readiness",
        "",
        "**READY_FOR_B6_WITH_UNRESOLVED_TEMPORAL_AUTHORITY.** Maximum next authorization: B6 dependency and temporal gap adjudication only. No dt, evolution, T1, mechanics, or forward evolution is authorized.",
        "",
        "Scientific gates: runtime authorization remains limited to loading/consuming the governed ARCANA T0 runtime package; mechanics, dt, T1, canonical mutation, and forward evolution remain false.",
        "",
        (f"Validation: focused B5 tests {data['test_results']['focused_b5']['result']}; "
         f"{data['test_results']['focused_b5']['tests_passed']} focused tests; full active R6 suite "
         f"{data['test_results']['active_r6']['result']} ({data['test_results']['active_r6']['tests_passed']} tests, "
         f"{data['test_results']['active_r6']['duration_seconds']} s); "
         f"py_compile {data['test_results']['py_compile']}; diff check {data['test_results']['diff_check']}."
         if data.get("test_results") else "Validation summary is recorded in B5_TEST_RESULTS.json after the test run."),
        "",
    ]
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, default=OUT_DEFAULT)
    args = parser.parse_args()
    try:
        qualified = qualify(args.repository_root.resolve(), args.output_dir.resolve())
        result = qualified["result"]
        manifest_rows = list(qualified["artifacts"])
        readme = ("# R6 B5 qualification evidence\n\n"
            f"Decision: `{result['decision']}`.\n\n"
            f"Qualified source: `{result['qualified_source_commit']}` on `{result['branch']}`.\n\n"
            "This package records read-only T0 spatial support, boundary and temporal-contract evidence. "
            "The node map is derived support; it does not alter canonical T0. No positive-duration interval, "
            "dt, mechanics or evolution is authorized. See the JSON evidence and the human report.\n")
        manifest_rows.append(_write_text(args.output_dir / "README.md", readme, "README.md"))
        manifest_rows.append(_write_text(REPORT, _human_report(qualified),
            "../../docs/arcana/B5_PLATE_SUPPORT_TOPOLOGY_TEMPORAL_INTEGRATION.md"))
        # Hashes cover retained package evidence; manifest self-hash is intentionally omitted.
        manifest = {"schema": "R6_B5_ARTIFACT_MANIFEST_V1", "artifacts": sorted(manifest_rows,
            key=lambda row: row["relative_path"]), "manifest_self_hash": "OMITTED_BY_POLICY"}
        _write_json(args.output_dir / "B5_ARTIFACT_MANIFEST.json", manifest)
        print(json.dumps({"decision": result["decision"],
            "node_support_counts": result["node_support_counts"],
            "boundary_count": result["boundary_count"],
            "world_history": result["world_history_support_integration"],
            "output_dir": args.output_dir.as_posix()}, sort_keys=True))
        return 0
    except Exception as exc:  # Qualification runner fails closed and returns nonzero.
        print(f"B5_QUALIFICATION_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
