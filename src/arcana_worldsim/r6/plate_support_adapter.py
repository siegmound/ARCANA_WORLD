"""Read-only B5 adapter for governed T0 plate, node, boundary and junction support.

Face membership is read directly from the model-derived canonical partition.
Node membership is derived by exact parent-grid face incidence through the
deterministic canonical mesh provider. Shared support is represented as a set,
never collapsed to one plate. No temporal transition or mechanical law is made.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from .identity import BranchId, HistoryId, canonical_bytes, content_hash
from .plate_kinematics_adapter import (
    B4_BRANCH, KinematicsAuthorityError, build_t0_records, load_governed_source,
    source_snapshot, _read_json, _tracked_identity, _hash_file,
)
from .provenance import ProvenanceRecord
from .repository_context import resolve_external_payload_path
from .shellset_mesh.adapter import CanonicalMesh, load_canonical_mesh
from .state import AuthorityClass, DomainStateEnvelope, SpatialSupport, SupportClass, TimeSupport
from .temporal import EventRecord

B5_BRANCH = "r6/b5-kinematic-support-topology-integration"
T0_MA = 210.0
GRID_ID = "R6_GLOBAL_GEOGRAPHY_1DEG_V1"
VECTOR_MANIFEST = "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json"
KINEMATIC_CENSUS = "R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json"
BOUNDARY_STATE = "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json"
FINITE_STEP = "R6_SHARED_BOUNDARY_FINITE_STEP_CENSUS.json"
CONTACT_RULE = "R6_SHARED_BOUNDARY_MOTION_AND_TOPOLOGY_CONTACT_RULE.json"
FEG_MANIFEST = "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json"
B4_DIR = "outputs/r6_b4_plate_kinematics_qualification"
B4_RESULT = f"{B4_DIR}/B4_RESULT.json"
B4_MANIFEST = f"{B4_DIR}/B4_ARTIFACT_MANIFEST.json"
B4_TEMPORAL = f"{B4_DIR}/B4_TEMPORAL_SUPPORT.json"
B5_TRACKED = (VECTOR_MANIFEST, KINEMATIC_CENSUS, BOUNDARY_STATE, FINITE_STEP,
              CONTACT_RULE, FEG_MANIFEST, B4_RESULT, B4_MANIFEST, B4_TEMPORAL)
SUPPORT_KIND_CODES = {"INTERIOR_PLATE": 0, "BOUNDARY_SHARED": 1,
                      "JUNCTION_SHARED": 2, "UNKNOWN": 3}


class PlateSupportError(ValueError):
    """Governed spatial support is inconsistent or cannot be qualified."""


class PlateNodeMappingError(PlateSupportError):
    """Node support could not be derived without ambiguity loss."""


@dataclass(frozen=True, slots=True)
class NodeSupportDerivation:
    node_plate_masks: tuple[int, ...]
    support_kind_codes: tuple[int, ...]
    node_plate_ids: tuple[tuple[int, ...], ...]
    counts: Mapping[str, int]
    mapping_identity_sha256: str
    payload_bytes: bytes
    payload_sha256: str


@dataclass(frozen=True, slots=True)
class B5Sources:
    root: Path
    branch: str
    head: str
    kinematics: Any
    kinematics_inventory: dict[str, Any]
    vector_manifest: dict[str, Any]
    kinematic_census: dict[str, Any]
    boundary_state: dict[str, Any]
    finite_step: dict[str, Any]
    contact_rule: dict[str, Any]
    feg_manifest: dict[str, Any]
    b4_result: dict[str, Any]
    b4_temporal: dict[str, Any]
    mesh: CanonicalMesh
    face_plate_ids: tuple[int, ...]
    boundary_descriptors: tuple[Mapping[str, Any], ...]
    source_documents: tuple[Mapping[str, Any], ...]
    payload_paths: Mapping[str, Path]
    source_identity: str


@dataclass(frozen=True, slots=True)
class B5Records:
    forcing: Any
    source_provenance: ProvenanceRecord
    adapter_provenance: ProvenanceRecord
    support_provenance: ProvenanceRecord
    plate_support_state: DomainStateEnvelope
    boundary_state: DomainStateEnvelope
    fixture_provenance: ProvenanceRecord
    fixture_state: DomainStateEnvelope
    fixture_events: tuple[EventRecord, ...]


def derive_node_plate_support(*, face_plate_ids: Sequence[int],
                              face_node_ids: Sequence[Sequence[int]],
                              boundary_edges: Iterable[Sequence[int]],
                              junction_node_ids: Iterable[int],
                              node_count: int,
                              expected_plate_ids: Iterable[int]) -> NodeSupportDerivation:
    """Derive set-valued node membership by exact incident face topology."""
    if node_count <= 0 or len(face_plate_ids) != len(face_node_ids):
        raise PlateNodeMappingError("face membership and topology cardinalities differ")
    expected = tuple(sorted({int(value) for value in expected_plate_ids}))
    if not expected or any(value < 0 for value in expected):
        raise PlateNodeMappingError("expected plate identity set is empty or invalid")
    expected_set = set(expected)
    node_plates = [set() for _ in range(node_count)]
    for plate_value, nodes in zip(face_plate_ids, face_node_ids):
        plate = int(plate_value)
        if plate not in expected_set:
            raise PlateNodeMappingError(f"face references unknown plate ID {plate}")
        unique_nodes = tuple(sorted({int(value) for value in nodes}))
        if len(unique_nodes) < 3 or any(value < 1 or value > node_count for value in unique_nodes):
            raise PlateNodeMappingError("face has invalid node incidence")
        for node_id in unique_nodes:
            node_plates[node_id - 1].add(plate)
    boundary_nodes: set[int] = set()
    for edge in boundary_edges:
        pair = tuple(int(value) for value in edge)
        if len(pair) != 2 or pair[0] == pair[1] or any(value < 1 or value > node_count for value in pair):
            raise PlateNodeMappingError("boundary edge has invalid endpoint identity")
        boundary_nodes.update(pair)
    junctions = {int(value) for value in junction_node_ids}
    if not junctions.issubset(boundary_nodes) or any(value < 1 or value > node_count for value in junctions):
        raise PlateNodeMappingError("junction identities are not supported by the boundary graph")

    masks: list[int] = []
    kinds: list[int] = []
    ids: list[tuple[int, ...]] = []
    counts = {key: 0 for key in SUPPORT_KIND_CODES}
    for node_id, plates in enumerate(node_plates, 1):
        ordered = tuple(sorted(plates))
        ids.append(ordered)
        if not ordered:
            kind = "UNKNOWN"
        elif node_id in junctions:
            kind = "JUNCTION_SHARED" if len(ordered) >= 3 else "UNKNOWN"
        elif node_id in boundary_nodes:
            kind = "BOUNDARY_SHARED" if len(ordered) >= 2 else "UNKNOWN"
        else:
            kind = "INTERIOR_PLATE" if len(ordered) == 1 else "UNKNOWN"
        mask = sum(1 << plate_id for plate_id in ordered)
        if kind == "UNKNOWN" and ordered:
            raise PlateNodeMappingError(f"ambiguous node support lacks boundary/junction incidence: {node_id}")
        masks.append(mask)
        kinds.append(SUPPORT_KIND_CODES[kind])
        counts[kind] += 1
    payload_body = {"schema": "R6_B5_NODE_PLATE_SUPPORT_MAP_V1",
        "node_id_base": 1, "node_count": node_count, "plate_ids": list(expected),
        "plate_mask_bit": "bit position equals plate_id; membership is set-valued",
        "support_kind_codes": SUPPORT_KIND_CODES,
        "node_plate_masks": masks, "support_kind_code_by_node": kinds,
        "physical_node_assignment": False}
    payload_bytes = canonical_bytes(payload_body) + b"\n"
    digest = hashlib.sha256(payload_bytes).hexdigest()
    semantic_id = content_hash(payload_body)
    return NodeSupportDerivation(tuple(masks), tuple(kinds), tuple(ids), counts,
                                 semantic_id, payload_bytes, digest)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], check=False,
                            capture_output=True, text=True)
    if result.returncode:
        raise PlateSupportError(f"git identity query failed: {' '.join(args)}")
    return result.stdout.strip()


def _verify_b4_evidence(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    result = _read_json(root / B4_RESULT)
    manifest = _read_json(root / B4_MANIFEST)
    temporal = _read_json(root / B4_TEMPORAL)
    if result.get("decision") != "PASS_B4_PLATE_KINEMATICS_TEMPORAL_ADAPTER_QUALIFICATION":
        raise PlateSupportError("B4 adapter qualification is not passing")
    if result.get("source_semantic_identity_sha256") != "50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4":
        raise PlateSupportError("B4 qualification is bound to a different kinematics identity")
    gates = result.get("scientific_side_effects", {})
    if any(gates.get(key) is not False for key in (
            "canonical_state_changed", "dt_selected", "t1_created", "mechanics_authorized",
            "forward_evolution_authorized", "shellset_executed", "orbdata_mechanics_executed")):
        raise PlateSupportError("B4 qualification has an unauthorized scientific side effect")
    for row in manifest.get("artifacts", []):
        rel = str(row.get("relative_path", ""))
        path = (root / rel).resolve()
        if not rel or root.resolve() not in path.parents or not path.is_file():
            raise PlateSupportError("B4 artifact manifest contains an invalid/missing path")
        digest, size, _ = _hash_file(path)
        if digest != row.get("sha256") or size != row.get("byte_size"):
            raise PlateSupportError(f"B4 evidence artifact hash mismatch: {rel}")
    if temporal.get("hard_anchors_ma") != [T0_MA] or temporal.get("positive_duration_intervals"):
        raise PlateSupportError("B4 temporal evidence no longer states anchor-only coverage")
    commit = str(result.get("qualified_source_commit", ""))
    ancestor = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor",
        commit, _git(root, "rev-parse", "HEAD")], check=False, capture_output=True)
    if not commit or ancestor.returncode:
        raise PlateSupportError("B4 qualified source commit is not an ancestor of B5 HEAD")
    return result, temporal


def _grid_vertex_node(vertex_id: str) -> int:
    if vertex_id == "SOUTH_POLE":
        return 1
    if vertex_id == "NORTH_POLE":
        return 2
    parts = vertex_id.split(":")
    if len(parts) != 3 or parts[0] != "GRID_VERTEX":
        raise PlateSupportError(f"unknown canonical grid vertex identity: {vertex_id}")
    row_line, col_line = int(parts[1]), int(parts[2]) % 360
    if row_line == 0:
        return 1
    if row_line == 180:
        return 2
    if not 1 <= row_line <= 179:
        raise PlateSupportError(f"grid vertex row outside canonical grid: {row_line}")
    return 3 + (row_line - 1) * 360 + col_line


def _build_boundary_descriptors(census: Mapping[str, Any], state: Mapping[str, Any],
                                mesh: CanonicalMesh,
                                face_lookup: Mapping[tuple[int, int], int],
                                plate_ids: set[int]) -> tuple[dict[str, Any], ...]:
    census_rows = {str(row["boundary_id"]): row for row in census.get("segments", [])}
    state_rows = {str(row["boundary_id"]): row for row in state.get("segments", [])}
    if len(census_rows) != 1_983 or len(state_rows) != 1_983 or census_rows.keys() != state_rows.keys():
        raise PlateSupportError("T0 boundary census and structural state do not share 1,983 unique IDs")
    mesh_edges = {boundary_id: tuple(sorted(edge))
                  for boundary_id, edge in zip(mesh.boundary_ids, mesh.boundary_edge_nodes)}
    if mesh_edges.keys() != census_rows.keys():
        raise PlateSupportError("canonical mesh boundary IDs differ from governed census")
    result = []
    for boundary_id in sorted(census_rows):
        row = census_rows[boundary_id]
        state_row = state_rows[boundary_id]
        pair = tuple(int(value) for value in row.get("ordered_plate_pair", ()))
        if len(pair) != 2 or pair[0] >= pair[1] or not set(pair).issubset(plate_ids):
            raise PlateSupportError(f"boundary has invalid adjacent plate identities: {boundary_id}")
        edge = row.get("parent_grid_edge", {})
        grid_row = int(edge["row"])
        grid_col = int(edge["column"])
        axis = str(edge["axis"])
        first_plate = face_lookup.get((grid_row, grid_col))
        if axis == "EAST":
            second_plate = face_lookup.get((grid_row, (grid_col + 1) % 360))
        elif axis == "NORTH":
            second_plate = face_lookup.get((grid_row + 1, grid_col))
        else:
            raise PlateSupportError(f"invalid boundary grid axis: {axis}")
        if first_plate is None or second_plate is None or tuple(sorted((first_plate, second_plate))) != pair:
            raise PlateSupportError(f"boundary adjacency differs from parent face labels: {boundary_id}")
        endpoint_ids = row.get("endpoint_vertex_ids", ())
        endpoints = tuple(sorted(_grid_vertex_node(str(value)) for value in endpoint_ids))
        if len(endpoints) != 2 or endpoints != mesh_edges[boundary_id]:
            raise PlateSupportError(f"boundary endpoint IDs differ from canonical mesh: {boundary_id}")
        if endpoints != tuple(sorted(_grid_vertex_node(str(value)) for value in state_row.get("endpoint_vertex_ids", ()))):
            raise PlateSupportError(f"boundary structural state endpoint mismatch: {boundary_id}")
        normal = float(row["relative_normal_velocity_m_per_year"])
        tangent = float(row["relative_tangential_velocity_m_per_year"])
        if not (math.isfinite(normal) and math.isfinite(tangent)):
            raise PlateSupportError(f"nonfinite T0 relative velocity diagnostic: {boundary_id}")
        if row.get("boundary_process_class") != "UNKNOWN_NOT_AUTHORIZED_BY_KINEMATICS_ALONE":
            raise PlateSupportError(f"boundary class was adjudicated outside B5: {boundary_id}")
        result.append({"boundary_id": boundary_id, "adjacent_plate_ids": list(pair),
            "parent_grid_edge": {"row": grid_row, "column": grid_col, "axis": axis},
            "endpoint_node_ids": list(endpoints), "length_m": float(row["length_m"]),
            "support": row["support"], "time_ma": T0_MA,
            "boundary_kind": "GEOMETRIC_SHARED_INTERFACE",
            "kinematic_descriptor": {"class": "DERIVED_GOVERNED_INSTANT_DIAGNOSTIC",
                "relative_normal_velocity_m_per_year": normal,
                "relative_tangential_velocity_m_per_year": tangent,
                "local_mode": row["local_kinematic_diagnostic"],
                "normal_convention": row["normal_convention"],
                "tangent_convention": row["tangent_convention"]},
            "geological_boundary_type": "UNKNOWN",
            "mechanical_accommodation": "UNKNOWN_NOT_MATERIALIZED",
            "positive_duration_validity": "UNKNOWN"})
    return tuple(result)


def load_b5_sources(repository_root: str | Path, *,
                    expected_branch: str = B5_BRANCH) -> tuple[B5Sources, dict[str, Any]]:
    """Load and verify the B5 source set on its owner or an explicit descendant.

    The default remains the original B5 branch. Later qualification stages may
    opt into their own branch while retaining every artifact/hash check below.
    """
    root = Path(repository_root).resolve()
    branch = _git(root, "branch", "--show-current")
    if branch != expected_branch:
        raise PlateSupportError(f"unexpected source branch: {branch}")
    head = _git(root, "rev-parse", "HEAD")
    kinematics, b4_inventory = load_governed_source(root, expected_branch=expected_branch)
    tracked = tuple(_tracked_identity(root, path) for path in B5_TRACKED)
    vector = _read_json(root / VECTOR_MANIFEST)
    census = _read_json(root / KINEMATIC_CENSUS)
    boundary = _read_json(root / BOUNDARY_STATE)
    finite = _read_json(root / FINITE_STEP)
    rule = _read_json(root / CONTACT_RULE)
    feg = _read_json(root / FEG_MANIFEST)
    b4_result, b4_temporal = _verify_b4_evidence(root)
    if vector.get("authority_class") != "MODEL_DERIVED_FROM_CANONICAL_T0":
        raise PlateSupportError("vector partition authority class changed")
    if (census.get("canonical_kinematics_sha256") != kinematics.canonical_identity_sha256
            or census.get("parent_vector_partition_sha256") != vector["payload"]["sha256"]
            or census.get("time_ma") != T0_MA or census.get("t0_only_diagnostic") is not True
            or census.get("time_evolution_executed") is not False):
        raise PlateSupportError("relative-motion census does not bind the governed T0 source pair")
    if (boundary.get("canonical_kinematics_sha256") != kinematics.canonical_identity_sha256
            or boundary.get("parent_vector_partition_sha256") != vector["payload"]["sha256"]
            or boundary.get("time_ma") != T0_MA
            or boundary.get("forward_evolution_executed") is not False):
        raise PlateSupportError("shared-boundary state does not bind the current T0 source pair")
    if (finite.get("parent_census") != Path(KINEMATIC_CENSUS).name
            or finite.get("time_ma") != T0_MA or finite.get("future_state_created") is not False
            or finite.get("segment_count") != 1_983):
        raise PlateSupportError("finite-step census no longer reports a blocked T0-only diagnostic")
    if (rule.get("decision") != "SHARED_BOUNDARY_NETWORK_BOUND_AS_MASTER_INTERFACE; TRANSITION_LAW_BLOCKED"
            or rule.get("pygplates_used") is not False
            or rule.get("no_forward_evolution") is not True
            or not str(rule.get("boundary_motion_rule", "")).startswith("UNBOUND_FOR_POSITIVE_DT")):
        raise PlateSupportError("shared-boundary motion/topology rule changed; B5 review required")
    topology = vector.get("topology", {})
    if (topology.get("face_count") != 64_800 or topology.get("plate_count") != 12
            or topology.get("positive_length_boundary_edge_count") != 1_983
            or topology.get("positive_length_adjacency_pair_count") != 30):
        raise PlateSupportError("canonical vector topology inventory changed")
    if (boundary.get("boundary_count") != 1_983
            or boundary.get("plate_pair_count") != 30
            or boundary.get("junction_count_degree_ge_3") != 20
            or boundary.get("state_class") != "STRUCTURAL_T0_INTERFACE_GRAPH_ONLY_NOT_A_DYNAMICAL_CHECKPOINT"):
        raise PlateSupportError("shared-boundary topology counts or role changed")
    if (feg.get("canonical_mesh", {}).get("normalized_sha256") != "6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad"
            or feg.get("canonical_mesh", {}).get("node_count") != 64_442
            or feg.get("canonical_mesh", {}).get("triangle_count") != 128_880
            or feg.get("canonical_mesh", {}).get("canonical_mesh_mutated") is not False
            or feg.get("production_feg", {}).get("node_id_alignment_with_runtime_package") is not True):
        raise PlateSupportError("FEG geometry/node identity binding changed")
    payload_path = resolve_external_payload_path(root, vector["payload"]["path"])
    mesh = load_canonical_mesh(root)
    with np.load(payload_path, allow_pickle=False) as archive:
        face_rows = archive["face_row"].astype(np.int64, copy=True)
        face_cols = archive["face_col"].astype(np.int64, copy=True)
        face_plate_ids = archive["face_plate_id"].astype(np.int64, copy=True)
        face_nodes_by_face: list[tuple[int, ...]] = []
        for triangles in mesh.parent_face_triangles:
            nodes = sorted({int(node) for tri_id in triangles
                            for node in mesh.triangles[tri_id - 1]})
            face_nodes_by_face.append(tuple(nodes))
    if mesh.normalized_sha256 != feg["canonical_mesh"]["normalized_sha256"]:
        raise PlateSupportError("reconstructed canonical mesh differs from FEG manifest identity")
    if len(face_plate_ids) != 64_800 or len(face_nodes_by_face) != 64_800:
        raise PlateSupportError("parent face support does not cover all canonical cells")
    face_lookup = {(int(row), int(col)): int(plate)
                   for row, col, plate in zip(face_rows, face_cols, face_plate_ids)}
    if len(face_lookup) != 64_800:
        raise PlateSupportError("canonical parent grid cell identities are duplicated")
    plate_ids = set(kinematics.plate_ids)
    if set(int(value) for value in np.unique(face_plate_ids)) != plate_ids:
        raise PlateSupportError("canonical face plate IDs differ from governed kinematics")
    boundary_descriptors = _build_boundary_descriptors(census, boundary, mesh, face_lookup, plate_ids)
    snapshot = source_snapshot(b4_inventory)
    snapshot.update({str(row["logical_path"]): _hash_file(root / str(row["logical_path"]))
                     for row in tracked})
    source_identity = content_hash({"head": head,
        "tracked_sources": [{"path": row["logical_path"], "sha256": row["sha256"]}
                            for row in sorted((*b4_inventory["tracked_authority_documents"], *tracked),
                                              key=lambda value: value["logical_path"])],
        "payloads": [{"path": row["logical_path"], "sha256": row["sha256"]}
                     for row in b4_inventory["payload_artifacts"]]})
    source = B5Sources(root, branch, head, kinematics, b4_inventory, vector, census,
        boundary, finite, rule, feg, b4_result, b4_temporal, mesh,
        tuple(int(value) for value in face_plate_ids), boundary_descriptors, tuple(tracked),
        b4_inventory["_payload_paths_internal"], source_identity)
    inventory = {"branch": branch, "head": head,
        "source_identity_sha256": source_identity,
        "source_documents": sorted((*b4_inventory["tracked_authority_documents"], *tracked),
                                    key=lambda value: value["logical_path"]),
        "payload_artifacts": list(b4_inventory["payload_artifacts"]),
        "plate_kinematics": {"authority_class": kinematics.authority_class,
            "semantic_identity_sha256": kinematics.canonical_identity_sha256,
            "time_ma": kinematics.time_ma, "reference_frame": kinematics.reference_frame,
            "plate_ids": list(kinematics.plate_ids)},
        "vector_partition": {"authority_class": vector["authority_class"],
            "payload_sha256": vector["payload"]["sha256"],
            "face_count": len(face_plate_ids), "plate_ids": sorted(plate_ids),
            "parent_grid": vector["parent_grid"]},
        "boundary_authority": {"boundary_count": len(boundary_descriptors),
            "plate_pair_count": boundary["plate_pair_count"],
            "junction_count": boundary["junction_count_degree_ge_3"],
            "kinematic_census_sha256": next(row["sha256"] for row in tracked
                if row["logical_path"] == KINEMATIC_CENSUS),
            "boundary_state_manifest_sha256": next(row["sha256"] for row in tracked
                if row["logical_path"] == BOUNDARY_STATE)},
        "mesh": {"normalized_sha256": mesh.normalized_sha256,
            "node_count": len(mesh.vertices_lat_lon), "triangle_count": len(mesh.triangles),
            "audit": mesh.audit},
        "B4": {"decision": b4_result["decision"],
            "source_commit": b4_result["qualified_source_commit"],
            "temporal_support": b4_temporal}}
    inventory["_snapshot"] = snapshot
    inventory["_face_node_ids"] = tuple(face_nodes_by_face)
    inventory["_face_plate_ids"] = tuple(int(value) for value in face_plate_ids)
    return source, inventory


def build_node_support(source: B5Sources, inventory: Mapping[str, Any]) -> NodeSupportDerivation:
    return derive_node_plate_support(face_plate_ids=inventory["_face_plate_ids"],
        face_node_ids=inventory["_face_node_ids"], boundary_edges=source.mesh.boundary_edge_nodes,
        junction_node_ids=(node_id for _junction_id, node_id in source.mesh.junction_node_ids),
        node_count=len(source.mesh.vertices_lat_lon), expected_plate_ids=source.kinematics.plate_ids)


def build_fixture_topology_events(*, history_id: str | None = None,
                                  branch_id: str | None = None) -> tuple[tuple[EventRecord, ...], ProvenanceRecord, DomainStateEnvelope]:
    """Create five schema-only events in an isolated FIXTURE_ONLY history/branch."""
    hid = history_id or str(HistoryId.from_payload({"fixture": "R6_B5_TOPOLOGY_EVENTS_V1"}))
    bid = branch_id or str(BranchId.from_payload({"fixture": "R6_B5_TOPOLOGY_EVENTS_V1"}))
    cases = (
        ("PLATE_SPLIT", {"parent_plate_ids": [4], "child_plate_ids": [40, 41]}),
        ("PLATE_MERGE", {"parent_plate_ids": [5, 6], "child_plate_ids": [56]}),
        ("BOUNDARY_BIRTH", {"boundary_id": "FIXTURE_BOUNDARY_NEW", "plate_ids": [4, 40]}),
        ("BOUNDARY_DEATH", {"boundary_id": "FIXTURE_BOUNDARY_OLD", "plate_ids": [4, 5]}),
        ("JUNCTION_REASSIGNMENT", {"junction_id": "FIXTURE_JUNCTION",
            "before_incident_plate_ids": [4, 5, 6], "after_incident_plate_ids": [4, 40, 6]}),
    )
    events = tuple(EventRecord.create(history_id=hid, branch_id=bid,
        time_key="FIXTURE_ONLY_NO_GEOLOGIC_TIME", domain_ids=("tectonic_topology",),
        authority_refs=("FIXTURE_ONLY",), validation_status="FIXTURE_ONLY_SCHEMA",
        details={"fixture_only": True, "event_type": kind, "lineage": data,
            "parent_history_mutated": False, "actual_arcana_event": False},
        temporal_support={"support_kind": "FIXTURE_ONLY", "time_key": "NO_GEOLOGIC_TIME"},
        spatial_support={"selector_kind": "FIXTURE_ONLY", "support": data})
        for kind, data in cases)
    provenance = ProvenanceRecord.create(activity="R6_B5_FIXTURE_TOPOLOGY_EVENT_SCHEMA_QUALIFICATION",
        input_refs=tuple(event.record_id for event in events),
        source_refs=("fixture-only:R6_B5_TOPOLOGY_EVENT_CONTRACT",),
        attributes={"fixture_only": True, "parent_history_mutated": False,
            "event_types": [kind for kind, _ in cases]})
    state = DomainStateEnvelope.create(history_id=hid, branch_id=bid,
        domain="synthetic_topology_event_contract",
        time_support=TimeSupport("FIXTURE_ONLY_NO_GEOLOGIC_TIME", "FIXTURE_ONLY", "SNAPSHOT"),
        spatial_support=SpatialSupport(None, (), "synthetic event-schema cases", "NONE"),
        support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
        value={"fixture_only": True, "event_count": len(events), "event_types": [kind for kind, _ in cases]},
        provenance_ids=(str(provenance.record_id),), model_derived=False,
        event_refs=tuple(event.record_id for event in events))
    return events, provenance, state


def build_b5_records(source: B5Sources, support: NodeSupportDerivation,
                     map_payload_reference: str,
                     boundary_summary: Mapping[str, Any]) -> B5Records:
    b4 = build_t0_records(source.kinematics)
    face_map_identity = content_hash({"face_plate_ids": list(source.face_plate_ids),
        "face_count": len(source.face_plate_ids), "source_sha256": source.vector_manifest["payload"]["sha256"]})
    support_prov = ProvenanceRecord.create(activity="R6_B5_DERIVE_SET_VALUED_NODE_PLATE_SUPPORT",
        input_refs=(str(b4.forcing.forcing_id),), source_refs=source.kinematics.source_refs + (
            f"artifact:{KINEMATIC_CENSUS}#sha256:{boundary_summary['kinematic_census_sha256']}",
            f"artifact:{BOUNDARY_STATE}#sha256:{boundary_summary['boundary_state_sha256']}",),
        parent_provenance_ids=(str(b4.adapter_provenance.record_id),),
        attributes={"source_identity_sha256": source.source_identity,
            "mesh_sha256": source.mesh.normalized_sha256,
            "face_support_identity_sha256": face_map_identity,
            "node_support_identity_sha256": support.mapping_identity_sha256,
            "node_support_payload_sha256": support.payload_sha256,
            "support_kind_codes": SUPPORT_KIND_CODES,
            "ambiguity_preserved": True, "physical_state_changed": False})
    plate_state = DomainStateEnvelope.create(history_id=source.kinematics.history_id,
        branch_id=source.kinematics.branch_id, domain="plate_spatial_support",
        time_support=TimeSupport("210Ma", "R6_GLOBAL_MA_OLDER_TO_YOUNGER", "INSTANT"),
        spatial_support=SpatialSupport(GRID_ID, (), "64,800 parent faces and 64,442 canonical mesh nodes", "GLOBAL"),
        support_class=SupportClass.DERIVED_SUPPORTED, authority_class=AuthorityClass.DERIVED_AUTHORITY,
        value={"schema": "R6_B5_PLATE_SPATIAL_SUPPORT_V1", "time_ma": T0_MA,
            "face_count": len(source.face_plate_ids), "face_support_identity_sha256": face_map_identity,
            "node_count": len(support.node_plate_masks),
            "node_support_identity_sha256": support.mapping_identity_sha256,
            "node_support_payload_ref": map_payload_reference,
            "node_support_counts": dict(support.counts),
            "membership_semantics": "SET_VALUED; BOUNDARY_AND_JUNCTION_AMBIGUITY_PRESERVED",
            "canonical_state_changed": False},
        uncertainty={"positive_duration_validity": "UNKNOWN",
            "node_plate_to_physical_process": "NOT_IMPLIED"},
        provenance_ids=(str(support_prov.record_id),),
        payload_ref=map_payload_reference, model_derived=True)
    boundary_state = DomainStateEnvelope.create(history_id=source.kinematics.history_id,
        branch_id=source.kinematics.branch_id, domain="boundary_kinematic_support",
        time_support=TimeSupport("210Ma", "R6_GLOBAL_MA_OLDER_TO_YOUNGER", "INSTANT"),
        spatial_support=SpatialSupport(GRID_ID, (), "1,983 canonical shared parent-grid edges", "GLOBAL"),
        support_class=SupportClass.DERIVED_SUPPORTED, authority_class=AuthorityClass.DERIVED_AUTHORITY,
        value={"schema": "R6_B5_BOUNDARY_KINEMATIC_SUPPORT_V1",
            "boundary_count": boundary_summary["boundary_count"],
            "boundary_descriptor_identity_sha256": boundary_summary["descriptor_identity_sha256"],
            "kinematic_class": "DERIVED_GOVERNED_INSTANT_DIAGNOSTIC",
            "geological_type": "UNKNOWN", "mechanical_accommodation": "UNKNOWN",
            "positive_duration_validity": "UNKNOWN"},
        provenance_ids=(str(support_prov.record_id),), parent_state_ids=(str(plate_state.state_id),),
        model_derived=True)
    fixture_events, fixture_provenance, fixture_state = build_fixture_topology_events()
    return B5Records(b4.forcing, b4.source_provenance, b4.adapter_provenance,
        support_prov, plate_state, boundary_state, fixture_provenance,
        fixture_state, fixture_events)


def source_snapshot_b5(source: B5Sources) -> dict[str, tuple[str, int, int]]:
    result = source_snapshot(source.kinematics_inventory)
    for row in source.source_documents:
        result[str(row["logical_path"])] = _hash_file(source.root / str(row["logical_path"]))
    return result
