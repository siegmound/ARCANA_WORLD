"""B6E plate-local MVP representation and declaration-only transfer contracts.

This module materializes semantic references to governed T0 support. It never
copies or changes coordinates, executes motion, mutates topology, or creates T1.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence

from .identity import canonical_bytes, content_hash


class MVPModelError(ValueError):
    """Invalid or ambiguous MVP representation input."""


class RepresentationRole(str, Enum):
    PLATE_INTERIOR = "PLATE_INTERIOR"
    BOUNDARY_SIDE = "BOUNDARY_SIDE"
    JUNCTION_SIDE = "JUNCTION_SIDE"


class TransferClass(str, Enum):
    IDENTITY_REFERENCE = "IDENTITY_REFERENCE"
    RIGID_ADVECT = "RIGID_ADVECT"
    REINDEX_ONLY = "REINDEX_ONLY"
    RECOMPUTE = "RECOMPUTE"
    REPLAY = "REPLAY"
    CONSERVATIVE_REMAP_REQUIRED = "CONSERVATIVE_REMAP_REQUIRED"
    MODEL_REQUIRED = "MODEL_REQUIRED"
    UNKNOWN = "UNKNOWN"


class MemoryDisposition(str, Enum):
    MATERIAL_SUPPORT_FOLLOWS = "MATERIAL_SUPPORT_FOLLOWS"
    HISTORICAL_REFERENCE = "HISTORICAL_REFERENCE"
    RECOMPUTE_REQUIRED = "RECOMPUTE_REQUIRED"
    MODEL_REQUIRED = "MODEL_REQUIRED"
    UNKNOWN = "UNKNOWN"


def _semantic_id(role: str, body: Mapping[str, Any]) -> str:
    return f"r6rep_{content_hash({'role': role, 'body': dict(body)})}"


@dataclass(frozen=True, slots=True)
class RepresentationLineage:
    source_semantic_identity: str
    source_payload_ref: str
    derived_representation_id: str
    representation_role: str
    source_support: tuple[str, ...]
    derivation_contract: str
    provenance_stage: str = "B6E_REPRESENTATION_ONLY"
    physical_state_created: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"source_semantic_identity": self.source_semantic_identity,
                "source_payload_ref": self.source_payload_ref,
                "derived_representation_id": self.derived_representation_id,
                "representation_role": self.representation_role,
                "source_support": list(self.source_support),
                "derivation_contract": self.derivation_contract,
                "provenance_stage": self.provenance_stage,
                "physical_state_created": self.physical_state_created}


@dataclass(frozen=True, slots=True)
class PlateLocalRepresentative:
    representation_id: str
    role: RepresentationRole
    source_entity_id: str
    plate_id: int
    source_support: tuple[int, ...]
    lineage: RepresentationLineage
    coordinate_action: str = "NONE_T0_COORDINATES_REFERENCED_ONLY"

    def to_dict(self) -> dict[str, Any]:
        return {"representation_id": self.representation_id, "role": self.role.value,
                "source_entity_id": self.source_entity_id, "plate_id": self.plate_id,
                "source_support": list(self.source_support),
                "lineage": self.lineage.to_dict(), "coordinate_action": self.coordinate_action}


@dataclass(frozen=True, slots=True)
class BoundarySide:
    side_id: str
    plate_id: int
    source_boundary_id: str
    source_endpoint_node_ids: tuple[int, int]
    representative_vertex_ids: tuple[str, str]
    lineage: RepresentationLineage

    def to_dict(self) -> dict[str, Any]:
        return {"side_id": self.side_id, "plate_id": self.plate_id,
                "source_boundary_id": self.source_boundary_id,
                "source_endpoint_node_ids": list(self.source_endpoint_node_ids),
                "representative_vertex_ids": list(self.representative_vertex_ids),
                "lineage": self.lineage.to_dict()}


@dataclass(frozen=True, slots=True)
class BoundaryInterface:
    interface_id: str
    source_boundary_id: str
    side_a: BoundarySide
    side_b: BoundarySide
    lineage: RepresentationLineage
    topological_relation: str = "T0_SHARED_EDGE__PLATE_LOCAL_SIDES_DISTINCT"
    physical_response_status: str = "UNKNOWN"

    @property
    def plate_ids(self) -> tuple[int, int]:
        return self.side_a.plate_id, self.side_b.plate_id

    def to_dict(self) -> dict[str, Any]:
        return {"interface_id": self.interface_id, "source_boundary_id": self.source_boundary_id,
                "side_a": self.side_a.to_dict(), "side_b": self.side_b.to_dict(),
                "lineage": self.lineage.to_dict(),
                "topological_relation": self.topological_relation,
                "physical_response_status": self.physical_response_status,
                "fault_type": "UNKNOWN", "polarity": "UNKNOWN", "stress": "UNKNOWN",
                "strain": "UNKNOWN", "rheology": "UNKNOWN", "slip_law": "UNKNOWN",
                "subduction": "UNKNOWN", "uplift": "UNKNOWN"}


@dataclass(frozen=True, slots=True)
class JunctionRelation:
    relation_id: str
    source_junction_id: str
    source_node_id: int
    incident_plate_ids: tuple[int, ...]
    incident_interface_ids: tuple[str, ...]
    plate_local_side_ids: tuple[str, ...]
    lineage: RepresentationLineage
    compatibility_status: str = "REQUIRED_NOT_QUALIFIED"
    physical_accommodation: str = "UNKNOWN"
    unique_plate_owner: None = None

    def to_dict(self) -> dict[str, Any]:
        return {"relation_id": self.relation_id, "source_junction_id": self.source_junction_id,
                "source_node_id": self.source_node_id,
                "incident_plate_ids": list(self.incident_plate_ids),
                "incident_interface_ids": list(self.incident_interface_ids),
                "plate_local_side_ids": list(self.plate_local_side_ids),
                "lineage": self.lineage.to_dict(),
                "compatibility_status": self.compatibility_status,
                "physical_accommodation": self.physical_accommodation,
                "unique_plate_owner": self.unique_plate_owner}


@dataclass(frozen=True, slots=True)
class StateTransferDeclaration:
    state_family: str
    transfer_class: TransferClass
    source_support: str
    target_support_class: str
    conservation_requirement: str
    recompute_or_replay_requirement: str
    temporal_validity_behavior: str
    missing_authority_behavior: str

    def to_dict(self) -> dict[str, str]:
        return {"state_family": self.state_family, "transfer_class": self.transfer_class.value,
                "source_support": self.source_support,
                "target_support_class": self.target_support_class,
                "conservation_requirement": self.conservation_requirement,
                "recompute_or_replay_requirement": self.recompute_or_replay_requirement,
                "temporal_validity_behavior": self.temporal_validity_behavior,
                "missing_authority_behavior": self.missing_authority_behavior}


@dataclass(frozen=True, slots=True)
class SystemMemoryTransferDeclaration:
    memory_family: str
    disposition: MemoryDisposition
    retained_reference: str | None
    update_rule: str
    missing_authority_behavior: str = "UNKNOWN_OR_MODEL_REQUIRED__NO_FABRICATED_VALUE"

    def to_dict(self) -> dict[str, Any]:
        return {"memory_family": self.memory_family, "disposition": self.disposition.value,
                "retained_reference": self.retained_reference,
                "update_rule": self.update_rule,
                "missing_authority_behavior": self.missing_authority_behavior}


@dataclass(frozen=True, slots=True)
class DomainTemporalValidity:
    domain: str
    state_time: str
    query_time: str
    latest_valid_time: str
    candidate_state_time: str | None
    candidate_state_present: bool
    query_role: str

    def __post_init__(self) -> None:
        if self.candidate_state_present or self.candidate_state_time is not None:
            raise MVPModelError("B6E temporal-validity fixture must not create a future state/time")
        if not self.state_time or not self.query_time or not self.latest_valid_time:
            raise MVPModelError("state, query and latest-valid time labels are required")
        if self.query_role not in {"TECTONIC_ADVANCE_CANDIDATE", "LATEST_VALID_STATE_CARRY_FORWARD"}:
            raise MVPModelError("unsupported asynchronous temporal query role")

    def to_dict(self) -> dict[str, Any]:
        return {"domain": self.domain, "state_time": self.state_time,
                "query_time": self.query_time, "latest_valid_time": self.latest_valid_time,
                "candidate_state_time": self.candidate_state_time,
                "candidate_state_present": self.candidate_state_present,
                "query_role": self.query_role}


@dataclass(frozen=True, slots=True)
class T0MVPRepresentation:
    source_semantic_identity: str
    source_payload_ref: str
    source_mesh_identity: str
    interior_representatives: tuple[PlateLocalRepresentative, ...]
    boundary_vertex_representatives: tuple[PlateLocalRepresentative, ...]
    junction_side_representatives: tuple[PlateLocalRepresentative, ...]
    interfaces: tuple[BoundaryInterface, ...]
    junction_relations: tuple[JunctionRelation, ...]
    identity_collision_count: int
    arbitrary_owner_assignment_count: int = 0
    node_motion_count: int = 0
    topology_mutation_count: int = 0

    @property
    def all_representatives(self) -> tuple[PlateLocalRepresentative, ...]:
        return self.interior_representatives + self.boundary_vertex_representatives + self.junction_side_representatives

    def summary(self) -> dict[str, Any]:
        ids = [row.representation_id for row in self.all_representatives]
        relation_ids = [row.interface_id for row in self.interfaces]
        relation_ids.extend(side.side_id for row in self.interfaces for side in (row.side_a, row.side_b))
        relation_ids.extend(row.relation_id for row in self.junction_relations)
        all_ids = ids + relation_ids
        return {"source_semantic_identity": self.source_semantic_identity,
                "source_payload_ref": self.source_payload_ref,
                "source_mesh_identity": self.source_mesh_identity,
                "interior_entities": len(self.interior_representatives),
                "boundary_side_entities": sum(2 for _ in self.interfaces),
                "boundary_vertex_representatives": len(self.boundary_vertex_representatives),
                "junction_side_entities": sum(len(row.plate_local_side_ids) for row in self.junction_relations),
                "interfaces": len(self.interfaces), "junction_relations": len(self.junction_relations),
                "representative_count": len(ids),
                "unique_representation_identity_count": len(set(ids)),
                "semantic_record_identity_count": len(all_ids),
                "unique_semantic_record_identity_count": len(set(all_ids)),
                "identity_collision_count": len(all_ids) - len(set(all_ids)),
                "arbitrary_owner_assignment_count": self.arbitrary_owner_assignment_count,
                "node_motion_count": self.node_motion_count,
                "topology_mutation_count": self.topology_mutation_count,
                "physical_state_created": False}

    def to_dict(self, *, include_records: bool = False) -> dict[str, Any]:
        """Return a portable deterministic representation document.

        The compact default supports manifests/diagnostics. Callers can request
        the full semantic record inventory when persistence actually needs it.
        """
        result: dict[str, Any] = {
            "schema": "R6_B6E_T0_MVP_REPRESENTATION_V1",
            "source_semantic_identity": self.source_semantic_identity,
            "source_payload_ref": self.source_payload_ref,
            "source_mesh_identity": self.source_mesh_identity,
            "representation_identity_digest": self.identity_digest(),
            "summary": self.summary(),
            "physical_state_created": False,
        }
        if include_records:
            result["interior_representatives"] = [x.to_dict() for x in self.interior_representatives]
            result["boundary_vertex_representatives"] = [x.to_dict() for x in self.boundary_vertex_representatives]
            result["junction_side_representatives"] = [x.to_dict() for x in self.junction_side_representatives]
            result["interfaces"] = [x.to_dict() for x in self.interfaces]
            result["junction_relations"] = [x.to_dict() for x in self.junction_relations]
        return result

    def identity_digest(self) -> str:
        return content_hash({"source": self.source_semantic_identity,
            "mesh": self.source_mesh_identity,
            "interior": [x.representation_id for x in self.interior_representatives],
            "boundary_vertices": [x.representation_id for x in self.boundary_vertex_representatives],
            "junction_sides": [x.representation_id for x in self.junction_side_representatives],
            "interfaces": [x.interface_id for x in self.interfaces],
            "junctions": [x.relation_id for x in self.junction_relations]})


def materialize_t0_representation(*, source_semantic_identity: str, source_payload_ref: str,
                                  source_mesh_identity: str, node_plate_ids: Sequence[Sequence[int]],
                                  support_kind_by_node: Sequence[str],
                                  boundary_descriptors: Sequence[Mapping[str, Any]],
                                  junctions: Sequence[Mapping[str, Any]]) -> T0MVPRepresentation:
    """Build deterministic support/side records from already governed T0 identities."""
    if len(node_plate_ids) != len(support_kind_by_node) or not node_plate_ids:
        raise MVPModelError("node set-valued support and support-kind arrays must align")
    plate_sets = [tuple(sorted({int(v) for v in plates})) for plates in node_plate_ids]
    if any(tuple(plates) != tuple(sorted(set(plates))) for plates in node_plate_ids):
        raise MVPModelError("node plate support must be unique and sorted")
    node_kinds = tuple(str(kind) for kind in support_kind_by_node)
    node_count = len(plate_sets)
    def node_plates(node_id: int) -> tuple[int, ...]:
        if not 1 <= node_id <= node_count:
            raise MVPModelError(f"source node outside governed support: {node_id}")
        return plate_sets[node_id - 1]

    registry: dict[str, bytes] = {}
    def make_lineage(identity: str, role: str, source_entity_id: str,
                     support: Sequence[str], contract: str) -> RepresentationLineage:
        return RepresentationLineage(source_semantic_identity, source_payload_ref,
            identity, role, tuple(support), contract)

    def make_rep(role: RepresentationRole, source_entity_id: str, plate_id: int,
                 support: tuple[int, ...], contract: str) -> PlateLocalRepresentative:
        lineage_body = {"source_semantic_identity": source_semantic_identity,
            "source_payload_ref": source_payload_ref, "representation_role": role.value,
            "source_entity_id": source_entity_id, "plate_id": plate_id,
            "source_support": list(support), "derivation_contract": contract,
            "provenance_stage": "B6E_REPRESENTATION_ONLY", "physical_state_created": False}
        identity = _semantic_id(role.value, lineage_body)
        encoded = canonical_bytes(lineage_body)
        prior = registry.setdefault(identity, encoded)
        if prior != encoded:
            raise MVPModelError("deterministic representation identity collision")
        lineage = make_lineage(identity, role.value, source_entity_id, (source_entity_id,), contract)
        return PlateLocalRepresentative(identity, role, source_entity_id, plate_id, support, lineage)

    boundary_nodes: set[int] = set()
    junction_nodes: set[int] = set()
    interior: list[PlateLocalRepresentative] = []
    for node_id, (plates, kind) in enumerate(zip(plate_sets, node_kinds), 1):
        if kind == "INTERIOR_PLATE":
            if len(plates) != 1:
                raise MVPModelError(f"interior node {node_id} does not have single-plate support")
            interior.append(make_rep(RepresentationRole.PLATE_INTERIOR, f"T0_NODE:{node_id}",
                                    plates[0], plates, "B5_EXACT_INCIDENT_FACE_SUPPORT"))
        elif kind == "BOUNDARY_SHARED":
            if len(plates) < 2:
                raise MVPModelError(f"boundary node {node_id} is not set-valued")
            boundary_nodes.add(node_id)
        elif kind == "JUNCTION_SHARED":
            if len(plates) < 3:
                raise MVPModelError(f"junction node {node_id} lacks multi-plate support")
            junction_nodes.add(node_id)
        else:
            raise MVPModelError(f"unsupported/unknown T0 node support at node {node_id}: {kind}")

    by_id: dict[str, Mapping[str, Any]] = {}
    interfaces: list[BoundaryInterface] = []
    boundary_vertices: list[PlateLocalRepresentative] = []
    node_interface_ids: dict[int, set[str]] = {}
    node_interface_sides: dict[int, set[str]] = {}
    for desc in sorted(boundary_descriptors, key=lambda item: str(item["boundary_id"])):
        bid = str(desc["boundary_id"])
        if bid in by_id:
            raise MVPModelError(f"duplicate governed boundary identity: {bid}")
        by_id[bid] = desc
        pair = tuple(int(v) for v in desc["adjacent_plate_ids"])
        endpoints = tuple(int(v) for v in desc["endpoint_node_ids"])
        if len(pair) != 2 or pair != tuple(sorted(set(pair))) or len(endpoints) != 2 or endpoints[0] == endpoints[1]:
            raise MVPModelError(f"malformed governed boundary {bid}")
        sides = []
        for plate in pair:
            if any(plate not in node_plates(node) for node in endpoints):
                raise MVPModelError(f"boundary endpoint support omits adjacent plate: {bid}/{plate}")
            vertex_ids = []
            for node in endpoints:
                rep = make_rep(RepresentationRole.BOUNDARY_SIDE,
                    f"T0_BOUNDARY:{bid}:NODE:{node}", plate,
                    node_plates(node), "B5_BOUNDARY_ENDPOINT_PLATE_LOCAL_SIDE")
                boundary_vertices.append(rep)
                vertex_ids.append(rep.representation_id)
                node_interface_ids.setdefault(node, set()).add(bid)
                node_interface_sides.setdefault(node, set()).add(rep.representation_id)
            side_body = {"boundary_id": bid, "plate_id": plate,
                         "source_endpoint_node_ids": list(endpoints)}
            side_id = _semantic_id("BOUNDARY_SIDE_ENTITY", side_body)
            side_lineage = make_lineage(side_id, "BOUNDARY_SIDE_ENTITY", f"T0_BOUNDARY:{bid}",
                (f"BOUNDARY:{bid}", *(f"NODE:{node}" for node in endpoints), f"PLATE:{plate}"),
                "B5_GOVERNED_BOUNDARY_SIDE_RELATION")
            sides.append(BoundarySide(side_id, plate, bid, endpoints, tuple(vertex_ids), side_lineage))
        interface_body = {"source_boundary_id": bid, "side_ids": [s.side_id for s in sides],
                          "source_endpoints": list(endpoints)}
        interface_id = _semantic_id("INTERFACE_RELATION", interface_body)
        interface_lineage = make_lineage(interface_id, "INTERFACE_RELATION", f"T0_BOUNDARY:{bid}",
            (f"BOUNDARY:{bid}", *(f"NODE:{node}" for node in endpoints),
             *(f"PLATE:{plate}" for plate in pair)),
            "B5_GOVERNED_KINEMATIC_INTERFACE_RELATION")
        interfaces.append(BoundaryInterface(interface_id, bid, sides[0], sides[1], interface_lineage))
    missing_boundary_relations = sorted(boundary_nodes - set(node_interface_ids))
    if missing_boundary_relations:
        raise MVPModelError(
            f"boundary support node lacks boundary relation: {missing_boundary_relations[:5]}"
        )

    junction_side_reps: list[PlateLocalRepresentative] = []
    junction_relations: list[JunctionRelation] = []
    seen_junction_ids: set[str] = set()
    seen_junction_nodes: set[int] = set()
    for row in sorted(junctions, key=lambda item: str(item["junction_id"])):
        jid, node_id = str(row["junction_id"]), int(row["node_id"])
        plates = tuple(sorted(int(v) for v in row["incident_plate_ids"]))
        if jid in seen_junction_ids or node_id in seen_junction_nodes:
            raise MVPModelError("duplicate governed junction identity or node")
        seen_junction_ids.add(jid); seen_junction_nodes.add(node_id)
        if node_id not in junction_nodes or plates != node_plates(node_id):
            raise MVPModelError(f"junction support differs from B5 node support: {jid}")
        interface_ids = tuple(sorted(node_interface_ids.get(node_id, ())))
        side_ids = []
        for plate in plates:
            touching = tuple(sorted(rep.representation_id for rep in boundary_vertices
                if rep.plate_id == plate and rep.source_entity_id.startswith(f"T0_BOUNDARY:")
                and rep.source_entity_id.endswith(f":NODE:{node_id}")
                and rep.source_entity_id.split(":")[1] in interface_ids))
            if not touching:
                raise MVPModelError(f"junction plate side has no incident interface link: {jid}/{plate}")
            source_entity = f"T0_JUNCTION:{jid}:NODE:{node_id}"
            rep = make_rep(RepresentationRole.JUNCTION_SIDE, source_entity, plate,
                           plates, "B5_SET_VALUED_JUNCTION_PLATE_LOCAL_SIDE")
            junction_side_reps.append(rep)
            side_ids.append(rep.representation_id)
        relation_body = {"junction_id": jid, "node_id": node_id,
                          "plate_ids": list(plates), "interfaces": list(interface_ids),
                          "side_ids": sorted(side_ids)}
        relation_id = _semantic_id("JUNCTION_RELATION", relation_body)
        relation_lineage = make_lineage(relation_id, "JUNCTION_RELATION", f"T0_JUNCTION:{jid}",
            (f"JUNCTION:{jid}", f"NODE:{node_id}",
             *(f"PLATE:{plate}" for plate in plates),
             *(f"INTERFACE:{interface_id}" for interface_id in interface_ids)),
            "B5_SET_VALUED_JUNCTION_RELATION")
        junction_relations.append(JunctionRelation(relation_id,
            jid, node_id, plates, interface_ids, tuple(sorted(side_ids)), relation_lineage))
    if seen_junction_nodes != junction_nodes:
        raise MVPModelError("B5 support map and governed junction inventory differ")
    identities = [rep.representation_id for rep in (*interior, *boundary_vertices, *junction_side_reps)]
    identities.extend(interface.interface_id for interface in interfaces)
    identities.extend(side.side_id for interface in interfaces for side in (interface.side_a, interface.side_b))
    identities.extend(relation.relation_id for relation in junction_relations)
    if len(identities) != len(set(identities)):
        # Two semantically identical inputs indicate duplicate source support, not a benign alias.
        raise MVPModelError("representation identities collide across support roles")
    return T0MVPRepresentation(source_semantic_identity, source_payload_ref,
        source_mesh_identity, tuple(interior), tuple(boundary_vertices),
        tuple(junction_side_reps), tuple(interfaces), tuple(junction_relations), 0)


def transfer_declarations_from_matrix(matrix: Mapping[str, Any]) -> tuple[StateTransferDeclaration, ...]:
    """Validate and materialize B6D transfer declarations without executing them."""
    rows = matrix.get("families")
    if not isinstance(rows, list) or not rows:
        raise MVPModelError("B6D state-transfer matrix is absent or empty")
    output = []
    for row in rows:
        raw = str(row["transfer_class"]).strip()
        try:
            transfer = TransferClass(raw)
        except ValueError:
            # Multi-option/conditional authority remains unresolved. Preserve
            # an explicit UNKNOWN where it leads the governed declaration.
            transfer = TransferClass.UNKNOWN if raw.startswith("UNKNOWN") else TransferClass.MODEL_REQUIRED
        output.append(StateTransferDeclaration(str(row["family"]), transfer,
            str(row["support"]), "PLATE_LOCAL_OR_DOMAIN_SUPPORT_NOT_MATERIALIZED_AS_T1",
            str(row.get("conservation_requirement", "NOT_GOVERNED")),
            str(row.get("recompute_or_replay", "MODEL_REQUIRED")),
            str(row.get("temporal_validity", "LATEST_VALID_STATE_PER_DOMAIN")),
            "PRESERVE_UNKNOWN_OR_MODEL_REQUIRED__NO_IMPUTATION"))
    if len({x.state_family for x in output}) != len(output):
        raise MVPModelError("duplicate B6D state family declaration")
    return tuple(sorted(output, key=lambda row: row.state_family))


def system_memory_declarations(memory_families: Iterable[Mapping[str, Any]]) -> tuple[SystemMemoryTransferDeclaration, ...]:
    result = []
    for row in memory_families:
        family = str(row["family"])
        disposition = MemoryDisposition(str(row["disposition"]))
        reference = row.get("retained_reference")
        if disposition is MemoryDisposition.HISTORICAL_REFERENCE and not reference:
            raise MVPModelError(f"historical memory requires an existing reference: {family}")
        result.append(SystemMemoryTransferDeclaration(family, disposition,
            None if reference is None else str(reference), str(row["update_rule"])))
    if len({x.memory_family for x in result}) != len(result):
        raise MVPModelError("duplicate SYSTEM_MEMORY family")
    return tuple(sorted(result, key=lambda row: row.memory_family))


def asynchronous_validity_fixture() -> tuple[DomainTemporalValidity, ...]:
    """Symbolic query-time fixture; it deliberately contains no future timestamp/state."""
    query = "FIXTURE_QUERY_CANDIDATE_AFTER_T0__NO_GEOLOGIC_TIME"
    t0 = "210Ma"
    rows = [DomainTemporalValidity("tectonics", t0, query, t0, None, False,
                                   "TECTONIC_ADVANCE_CANDIDATE")]
    rows.extend(DomainTemporalValidity(domain, t0, query, t0, None, False,
                                       "LATEST_VALID_STATE_CARRY_FORWARD")
                for domain in ("climate", "hydrology", "ecology", "Deep"))
    return tuple(rows)
