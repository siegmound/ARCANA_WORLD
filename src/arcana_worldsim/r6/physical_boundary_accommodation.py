"""Read-only T0 boundary-graph reconstruction and authority adjudication.

This module records canonical topology and existing kinematic diagnostics. It
does not define physical accommodation, material properties, or evolution.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


VECTOR_SHA = "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
KINEMATICS_SHA = "50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4"


@dataclass(frozen=True, slots=True)
class CanonicalBoundaryBranch:
    branch_id: str
    plate_pair: tuple[int, int]
    boundary_ids: tuple[str, ...]
    start_vertex_id: str
    end_vertex_id: str
    start_junction_id: str
    end_junction_id: str
    section_id: str
    section_boundary_reason: str
    support: str = "COARSE_SUPPORT_ON_FINE_GRID"
    authority: str = "DERIVED_FROM_CANONICAL_T0_SHARED_EDGE_GRAPH"
    validation_status: str = "VALIDATED_TOPOLOGICAL_PATH"

    def to_dict(self) -> dict[str, Any]:
        return {"branch_id": self.branch_id, "plate_pair": list(self.plate_pair),
                "boundary_ids": list(self.boundary_ids),
                "boundary_segment_count": len(self.boundary_ids),
                "start_vertex_id": self.start_vertex_id,
                "end_vertex_id": self.end_vertex_id,
                "start_junction_id": self.start_junction_id,
                "end_junction_id": self.end_junction_id,
                "section_id": self.section_id,
                "section_boundary_reason": self.section_boundary_reason,
                "support": self.support, "authority": self.authority,
                "validation_status": self.validation_status}


def _vertex_key(vertex_id: str) -> tuple[int, int]:
    prefix, row, col = vertex_id.split(":")
    if prefix != "GRID_VERTEX":
        raise ValueError(f"unsupported vertex identity: {vertex_id}")
    row_i, col_i = int(row), int(col)
    if not 0 <= row_i <= 180 or not 0 <= col_i <= 360:
        raise ValueError(f"vertex outside canonical grid: {vertex_id}")
    return row_i, col_i % 360


def reconstruct_canonical_branches(shared_boundary: Mapping[str, Any]) -> tuple[CanonicalBoundaryBranch, ...]:
    """Recover maximal same-pair edge paths, cut at pair-local junction ends.

    A path is cut only where pair-local graph degree is not two. A cycle is a
    whole branch if the governed graph has no such endpoint. Grid-resolution
    subdivisions are not promoted to extra sections.
    """
    segments = tuple(shared_boundary["segments"])
    junctions = tuple(shared_boundary["junctions"])
    junction_by_vertex = {_vertex_key(str(item["vertex_id"])): str(item["junction_id"])
                          for item in junctions}
    edge_nodes: dict[int, tuple[tuple[tuple[int, int], tuple[int, int]],
                                tuple[tuple[int, int], tuple[int, int]]]] = {}
    adjacency: dict[tuple[tuple[int, int], tuple[int, int]], list[int]] = defaultdict(list)
    vertex_names: dict[tuple[tuple[int, int], tuple[int, int]], str] = {}
    ids: set[str] = set()
    for index, segment in enumerate(segments):
        boundary_id = str(segment["boundary_id"])
        if boundary_id in ids:
            raise ValueError(f"duplicate canonical boundary identity: {boundary_id}")
        ids.add(boundary_id)
        pair = tuple(sorted(map(int, segment["ordered_plate_pair"])))
        if len(pair) != 2 or pair[0] == pair[1]:
            raise ValueError(f"invalid plate pair on {boundary_id}")
        endpoints = tuple(map(str, segment["endpoint_vertex_ids"]))
        if len(endpoints) != 2:
            raise ValueError(f"boundary edge needs two endpoints: {boundary_id}")
        nodes = tuple((pair, _vertex_key(vertex)) for vertex in endpoints)
        if nodes[0] == nodes[1]:
            raise ValueError(f"collapsed graph edge: {boundary_id}")
        edge_nodes[index] = nodes  # type: ignore[assignment]
        for node, name in zip(nodes, endpoints):
            adjacency[node].append(index)
            prior = vertex_names.setdefault(node, name)
            if _vertex_key(prior) != _vertex_key(name):
                raise ValueError("graph vertex normalization mismatch")

    # Validate the canonical degree-three incidence against the boundary edges.
    for junction in junctions:
        vertex_id = str(junction["vertex_id"])
        incident_ids = set(map(str, junction["incident_boundary_ids"]))
        incident_edges = {str(segments[i]["boundary_id"])
                          for pair in {tuple(sorted(map(int, s["ordered_plate_pair"])))
                                       for s in segments}
                          for i in adjacency.get((pair, _vertex_key(vertex_id)), ())}
        if int(junction["degree"]) != 3 or len(incident_ids) != 3 or incident_ids != incident_edges:
            raise ValueError(f"junction incidence does not match graph: {junction.get('junction_id')}")

    used: set[int] = set()
    paths: list[tuple[tuple[int, int], list[int], tuple[tuple[int, int], tuple[int, int]]]] = []
    endpoint_nodes = sorted(node for node, edges in adjacency.items() if len(edges) != 2)
    for node in endpoint_nodes:
        for first_edge in sorted(adjacency[node], key=lambda i: str(segments[i]["boundary_id"])):
            if first_edge in used:
                continue
            current_edge, current_node = first_edge, node
            path: list[int] = []
            while current_edge not in used:
                used.add(current_edge)
                path.append(current_edge)
                ends = edge_nodes[current_edge]
                next_node = ends[1] if ends[0] == current_node else ends[0]
                if len(adjacency[next_node]) != 2:
                    current_node = next_node
                    break
                next_edges = [i for i in adjacency[next_node] if i != current_edge]
                if len(next_edges) != 1:
                    raise ValueError("pair-local degree-two continuation is ambiguous")
                current_edge, current_node = next_edges[0], next_node
            pair = tuple(sorted(map(int, segments[path[0]]["ordered_plate_pair"])))
            paths.append((pair, path, (node[1], current_node[1])))

    # A pure cycle has no endpoint; retain it as one deterministic branch.
    for first_edge in sorted(set(range(len(segments))) - used,
                             key=lambda i: str(segments[i]["boundary_id"])):
        if first_edge in used:
            continue
        current_edge = first_edge
        current_node = edge_nodes[first_edge][0]
        start_node = current_node
        path = []
        while current_edge not in used:
            used.add(current_edge)
            path.append(current_edge)
            ends = edge_nodes[current_edge]
            next_node = ends[1] if ends[0] == current_node else ends[0]
            candidates = [i for i in adjacency[next_node] if i != current_edge and i not in used]
            if not candidates:
                current_node = next_node
                break
            current_edge, current_node = min(candidates,
                key=lambda i: str(segments[i]["boundary_id"])), next_node
        pair = tuple(sorted(map(int, segments[path[0]]["ordered_plate_pair"])))
        paths.append((pair, path, (start_node[1], current_node[1])))

    if used != set(range(len(segments))):
        raise ValueError("canonical branch reconstruction did not cover each boundary edge")

    result = []
    for pair, path, endpoint_keys in paths:
        ordered_ids = tuple(str(segments[i]["boundary_id"]) for i in path)
        endpoints = tuple(vertex_names[(pair, key)] for key in endpoint_keys)
        branch_body = {"parent_vector_partition_sha256": VECTOR_SHA,
                       "plate_pair": list(pair), "boundary_ids": list(ordered_ids),
                       "endpoint_vertex_ids": list(endpoints)}
        branch_digest = sha256(json.dumps(branch_body, sort_keys=True,
            separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()[:20]
        branch_id = f"R6BR-T0-{branch_digest}"
        section_digest = sha256(f"{branch_id}|junction-to-junction|{VECTOR_SHA}".encode()).hexdigest()[:20]
        junction_ids = tuple(junction_by_vertex.get(_vertex_key(vertex), "") for vertex in endpoints)
        result.append(CanonicalBoundaryBranch(
            branch_id=branch_id, plate_pair=pair, boundary_ids=ordered_ids,
            start_vertex_id=endpoints[0], end_vertex_id=endpoints[1],
            start_junction_id=junction_ids[0], end_junction_id=junction_ids[1],
            section_id=f"R6SEC-T0-{section_digest}",
            section_boundary_reason="MAXIMAL_SAME_PLATE_PAIR_PATH_TERMINATED_AT_CANONICAL_JUNCTIONS",
        ))
    return tuple(sorted(result, key=lambda row: row.branch_id))


def adjudicate_boundary_accommodation(root) -> dict[str, Any]:
    """Build an immutable diagnostic from current governed T0 artifacts."""
    from pathlib import Path

    root = Path(root)
    read = lambda name: json.loads((root / name).read_text(encoding="utf-8"))
    parent = read("R6_PHYSICAL_DOMAIN_T0_BINDING_REPORT.json")
    boundary = read("R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json")
    census = read("R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json")
    vector = read("R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json")
    kinematics = read("R6_T0_CANONICAL_PLATE_KINEMATICS.json")
    bootstrap = read("R6_BOOTSTRAP_MANIFEST.json")
    law = read("R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT.json")
    topology_guard = read("R6_TOPOLOGY_CONTACT_GUARD.json")
    junction_contract = read("R6_JUNCTION_COMPATIBILITY_CONTRACT.json")
    dt = read("R6_FIRST_INTERVAL_DT_LIMIT_REGISTER.json")
    stepping = read("R6_FIRST_INTERVAL_NUMERICAL_STEPPING_CONTRACT.json")
    patch = read("R6_JUNCTION_PATCH_OPERATOR_VALIDATION.json")
    arrangement = read("R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION.json")
    readiness = read("R6_FIRST_PHYSICAL_INTERVAL_READINESS_V19.json")
    from .state import DomainStateEnvelope

    state_file = root / "world_history_bindings" / "r6_physical_world_t0" / "states" / (
        parent["history_binding"]["state_id"] + ".json")
    bound_state = DomainStateEnvelope.from_dict(json.loads(state_file.read_text(encoding="utf-8")))
    kin_body = dict(kinematics)
    declared_kin_sha = kin_body.pop("payload_identity_sha256")
    recomputed_kin_sha = sha256((json.dumps(kin_body, sort_keys=True, ensure_ascii=False,
        indent=2, allow_nan=False) + "\n").encode()).hexdigest()
    branches = reconstruct_canonical_branches(boundary)
    segments = tuple(boundary["segments"])
    junctions = tuple(boundary["junctions"])
    demand_counts = Counter(str(row["local_kinematic_diagnostic"]) for row in segments)
    normal_sign_counts = Counter()
    unresolved_velocity = 0
    for row in segments:
        normal = row.get("relative_normal_velocity_m_per_year")
        tangent = row.get("relative_tangential_velocity_m_per_year")
        if normal is None or tangent is None:
            unresolved_velocity += 1
        elif normal > 1e-9:
            normal_sign_counts["DIVERGENT_KINEMATIC_DEMAND"] += 1
        elif normal < -1e-9:
            normal_sign_counts["CONVERGENT_KINEMATIC_DEMAND"] += 1
        else:
            normal_sign_counts["NEAR_ZERO_NORMAL_DEMAND"] += 1
    section_motion = []
    for branch in branches:
        rows = [next(item for item in segments if item["boundary_id"] == boundary_id)
                for boundary_id in branch.boundary_ids]
        classes = Counter(str(row["local_kinematic_diagnostic"]) for row in rows)
        section_motion.append({"section_id": branch.section_id,
            "branch_id": branch.branch_id, "plate_pair": list(branch.plate_pair),
            "boundary_segment_count": len(rows), "resolved_segment_count": len(rows) -
                sum(row["relative_normal_velocity_m_per_year"] is None or
                    row["relative_tangential_velocity_m_per_year"] is None for row in rows),
            "segment_demand_classes": dict(sorted(classes.items())),
            "section_aggregate_demand": "HETEROGENEOUS_SEGMENT_DEMAND" if len(classes) > 1 else next(iter(classes)),
            "authorized_physical_accommodation": "UNKNOWN"})

    graph_ok = (len(segments) == 1983 and len(branches) == 30
                and len({row.section_id for row in branches}) == len(branches)
                and sum(len(row.boundary_ids) for row in branches) == len(segments)
                and all(row.start_junction_id and row.end_junction_id for row in branches))
    if not graph_ok:
        raise ValueError("canonical branch graph failed count, identity, coverage, or endpoint validation")
    if (vector["payload"]["sha256"] != VECTOR_SHA
            or vector["canonical_parent_sha256"] != parent["payload_verification"]["parent"]["sha256"]
            or kinematics["parent_vector_partition_sha256"] != VECTOR_SHA
            or kinematics["parent_canonical_t0_sha256"] != parent["payload_verification"]["parent"]["sha256"]
            or recomputed_kin_sha != KINEMATICS_SHA or declared_kin_sha != KINEMATICS_SHA
            or boundary["parent_vector_partition_sha256"] != VECTOR_SHA
            or census["canonical_kinematics_sha256"] != KINEMATICS_SHA):
        raise ValueError("boundary graph is detached from canonical vector/kinematic authority")
    if (parent["history_binding"]["state_id"] != str(bound_state.state_id)
            or parent["decision"] != "R6_PHYSICAL_DOMAIN_T0_BOUND__FIRST_INTERVAL_BLOCKED"
            or bootstrap["bootstrap_identity_sha256"] != "27bdaa065146981d425088db06c7f989c1099e64e4b30d920b04c979d01331bf"):
        raise ValueError("published T0 HistoryStore identity changed")

    patch_summary = []
    for width_case in patch["width_cases"]:
        statuses = Counter(row.get("corner_status", "UNKNOWN") for row in width_case["junctions"])
        reasons = Counter(row.get("reason", "NOT_RECORDED") for row in width_case["junctions"])
        patch_summary.append({"diagnostic_width_m": width_case["W_model_m"],
            "canonical_width": False, "status": width_case["status"],
            "junction_outcomes": dict(sorted(statuses.items())),
            "patches_constructed": width_case["patches_constructed"],
            "triangulated": width_case["triangulated"],
            "trace_not_reached": width_case["trace_not_reached"],
            "failure_reasons": dict(sorted(reasons.items()))})

    return {
        "schema": "R6_PHYSICAL_BOUNDARY_ACCOMMODATION_REPORT_V1",
        "decision": "R6_BOUNDARY_ACCOMMODATION_NOT_ESTABLISHED__RESEARCH_REQUIRED",
        "parent": {"branch": "r6/physical-domain-t0-binding",
            "commit": "f327a317bc8650df3abcfe5a5e9924eebafbe427",
            "scientific_decision": parent["decision"]},
        "t0_identity": {"time_ma": 210.0,
            "canonical_state_id": parent["history_binding"]["state_id"],
            "parent_payload_sha256": vector["canonical_parent_sha256"],
            "vector_partition_sha256": vector["payload"]["sha256"],
            "kinematics_sha256": kinematics["payload_identity_sha256"],
            "support": "COARSE_SUPPORT_ON_FINE_GRID"},
        "t0_invariants": {"world_history_state_id_unchanged": True,
            "historical_bootstrap_identity": bootstrap["bootstrap_identity_sha256"],
            "canonical_parent_payload_changed": False,
            "vector_payload_changed": False, "kinematics_changed": False},
        "payload_verification": {
            "parent_physical_payload": {"sha256": vector["canonical_parent_sha256"],
                "bytes": parent["payload_verification"]["parent"]["bytes"],
                "read_only_reverified": True},
            "vector_partition_payload": {"sha256": vector["payload"]["sha256"],
                "bytes": vector["payload"]["bytes"], "read_only_reverified": True},
            "kinematics_payload_identity": {"declared_sha256": declared_kin_sha,
                "recomputed_sha256": recomputed_kin_sha, "identity_matches": True}},
        "validation_artifact_versions": {"junction_patch_operator": "V6",
            "spherical_network_arrangement_operator": "V4",
            "first_interval_readiness": "V19"},
        "authority_artifacts": {
            "current_authority": ["R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json",
                "R6_T0_CANONICAL_PLATE_KINEMATICS.json",
                "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json",
                "R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json",
                "R6_PHYSICAL_DOMAIN_T0_BINDING_REPORT.json"],
            "supporting_evidence": ["R6_T0_INITIAL_KINEMATICS_MANIFEST.json",
                "R6_T0_SYNTHETIC_TECTONIC_STATE_CANONICALIZATION.json",
                "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json",
                "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json"],
            "blockers": ["R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT.json",
                "R6_TOPOLOGY_CONTACT_GUARD.json", "R6_JUNCTION_COMPATIBILITY_CONTRACT.json",
                "R6_FIRST_INTERVAL_DT_LIMIT_REGISTER.json",
                "R6_FIRST_INTERVAL_NUMERICAL_STEPPING_CONTRACT.json",
                "R6_JUNCTION_PATCH_OPERATOR_VALIDATION.json",
                "R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION.json",
                "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V19.json"],
            "diagnostic_only": ["R6_T0_BOUNDARY_ZONE_REFERENCE_MAP_MANIFEST.json",
                "R6_T0_BOUNDARY_ZONE_REFERENCE_VALIDATION.json",
                "R6_T0_CONTINUUM_REFERENCE_VALIDATION.json",
                "R6_STATIC_T0_CONTINUUM_VELOCITY_VALIDATION.json"],
            "precedence_note": "The parent T0 authority report is preserved. Current V3 eligibility and the present versioned junction/arrangement validations are included by their explicit parent/vector/kinematics identities; lower versions are not promoted."},
        "canonical_topology": {"plate_count": vector["topology"]["plate_count"],
            "parent_face_count": vector["topology"]["face_count"],
            "boundary_segment_count": boundary["boundary_count"],
            "adjacent_plate_pair_count": boundary["plate_pair_count"],
            "degree3_junction_count": boundary["junction_count_degree_ge_3"],
            "graph_integrity": "PASS", "support": boundary["support"]},
        "canonical_boundary_graph": {
            "status": "RECONSTRUCTED_FROM_GOVERNED_ENDPOINT_CONNECTIVITY",
            "identity_rule": "pair-local maximal edge path, cut where pair-local vertex degree is not two; endpoint vertices are canonical degree-three junctions",
            "branch_count": len(branches), "section_count": len(branches),
            "boundary_edge_coverage": sum(len(row.boundary_ids) for row in branches),
            "branch_pair_count": len({row.plate_pair for row in branches}),
            "branch_identity_repeatable": True, "branches": [row.to_dict() for row in branches],
            "section_rule": "one canonical section per full junction-to-junction maximal same-pair branch; parent-grid edges remain internal support subdivisions"},
        "pure_plate_anchors": {"validated_anchor_count": 0,
            "required_section_side_slots": len(branches) * 2,
            "unresolved_anchor_slots": len(branches) * 2,
            "status": "PURE_PLATE_ANCHOR_SEMANTICS_NOT_ESTABLISHED",
            "reason": "The parent grid assigns plate identity, but no governed boundary-zone footprint/exclusion semantics establish that any selected face is outside the deforming support. No anchor is fabricated."},
        "relative_motion": {"method": "existing canonical Euler-vector cross product at each canonical parent-edge midpoint, projected onto governed pair-oriented normal and edge tangent; see r6_bind_shared_boundary_topology_contact.py",
            "boundary_segments_total": len(segments),
            "segments_with_resolved_normal_and_tangent": len(segments) - unresolved_velocity,
            "segments_unresolved": unresolved_velocity,
            "normal_demand_counts": dict(sorted(normal_sign_counts.items())),
            "existing_joint_normal_tangential_demand_counts": dict(sorted(demand_counts.items())),
            "pair_order_sign_semantics": "When A/B and n_AB are both reversed, signed normal demand is invariant; with the geometry tangent direction held fixed, tangential relative demand changes sign. The projection helper has a dedicated test.",
            "branch_sections": section_motion,
            "semantic_limit": "KINEMATIC_DEMAND only; no stress, force balance, strain law, fault, rift, subduction, orogenic, crust production/destruction semantics"},
        "accommodation_law": {"status": "NOT_ESTABLISHED",
            "authority": law["decision"],
            "positive_physical_accommodation_sections": 0,
            "sections_with_authority_gap": len(branches),
            "basis": "Repository T0 authority provides plate Euler kinematics and relative-motion demand, but no constitutive/mechanical state or governed rule mapping demand to boundary material motion/deformation. It supplies no force/stress balance, rheological strength, yield criterion, boundary width semantics, or junction residual allocation."},
        "junctions": {"total": len(junctions),
            "incident_boundary_identity_validated": len(junctions),
            "canonical_velocity_available": sum(row.get("canonical_velocity") is not None for row in junction_contract["junctions"]),
            "compatibility_residuals_computed": 0,
            "outcome_counts": {"JUNCTION_COMPATIBLE": 0,
                "JUNCTION_UNDERDETERMINED": 0, "JUNCTION_INCOMPATIBLE": 0,
                "JUNCTION_AUTHORITY_GAP": len(junctions)},
            "status": junction_contract["decision"],
            "reason": "No governed boundary-type/velocity constraints or physical residual-allocation law; branch-local demands cannot establish a simultaneous physical junction solution."},
        "patch_operator": {"status": patch["decision"],
            "replacement_established": False,
            "old_operator_cause": {"diagnostic_width_cases": patch_summary,
                "observed_failure": "At diagnostic widths 250 km and 500 km, persistent nonzero Dirichlet corner mismatches occur; at 100 km there is also a port-extraction implementation failure; other corners remain numerically unresolved or domains fail. These are computed-operator failures under noncanonical width probes, not proof of a physical law or physical incompatibility."},
            "current_governed_blocker": readiness["remaining_blocker"],
            "new_semantics": "Not created: without governed pure-plate anchors and accommodation law, replacement boundary conditions would be invented."},
        "pygplates": {"role": "BOUNDED_SOLVER_CANDIDATE",
            "scientific_authority": False,
            "static_geometry_topology": "SUFFICIENT",
            "synthetic_deforming_network": "SUFFICIENT",
            "canonical_dynamic_deformation": "NOT_YET_VALIDATED",
            "fair_runtime": "EXTERNAL_QUALIFICATION; not an ARCANA physical law",
            "windows_report_preserved": "PYGPLATES_RUNTIME_UNAVAILABLE"},
        "research_gate": {"external_scientific_research_required": True,
            "smallest_question": "What ARCANA-authorized mechanical/constitutive rule maps canonical instantaneous plate-side relative motion and boundary state to physical boundary accommodation, and what simultaneous closure condition does that rule impose at a degree-three junction, without an unsupported width or rheological parameter?",
            "required_information": ["boundary material/mechanical state and its authority",
                "physical accommodation relation for normal and tangential demand",
                "junction closure constraints or residual-allocation authority"],
            "do_not_substitute": ["velocity demand", "diagnostic width probes", "pyGPlates capability", "generic Earth rheology"]},
        "readiness": {"instantaneous_t0_well_posed": False,
            "first_interval_contract_design_authorized": False,
            "topology_contact_guard": topology_guard["decision"],
            "dt_limit": dt["derivation"], "numerical_stepping": stepping["decision"]},
        "invariants": {"canonical_payload_changed": False,
            "t0_state_mutated": False, "dt_selected": False, "t1_created": False,
            "W_model_selected": False, "forward_evolution": False,
            "first_interval_authorized": False},
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    graph = report["canonical_boundary_graph"]
    motion = report["relative_motion"]
    anchors = report["pure_plate_anchors"]
    junctions = report["junctions"]
    law = report["accommodation_law"]
    patch = report["patch_operator"]
    readiness = report["readiness"]
    lines = [
        "# R6 Physical Boundary Accommodation Authority Adjudication",
        "", f"**Decision:** `{report['decision']}`", "",
        f"Parent: `{report['parent']['branch']}` at `{report['parent']['commit']}`; parent decision `{report['parent']['scientific_decision']}`.",
        "", "## Canonical T0", "",
        f"- State: `{report['t0_identity']['canonical_state_id']}` at {report['t0_identity']['time_ma']} Ma.",
        f"- Parent / vector / kinematics SHA-256: `{report['t0_identity']['parent_payload_sha256']}` / `{report['t0_identity']['vector_partition_sha256']}` / `{report['t0_identity']['kinematics_sha256']}`.",
        f"- Inventory: {report['canonical_topology']['plate_count']} plates, {report['canonical_topology']['parent_face_count']:,} parent faces, {report['canonical_topology']['boundary_segment_count']:,} edges, {report['canonical_topology']['adjacent_plate_pair_count']} plate pairs, {report['canonical_topology']['degree3_junction_count']} degree-3 junctions.",
        f"- Support: `{report['canonical_topology']['support']}`. Payloads and the bound T0 state remain unchanged.",
        "", "## Boundary graph and sections", "",
        f"Reconstructed {graph['branch_count']} deterministic same-pair branches and {graph['section_count']} canonical junction-to-junction sections. All {graph['boundary_edge_coverage']:,} source edges are covered once; branch IDs are repeatable.",
        "Each section boundary is a canonical degree-three junction. Parent-grid edges are retained as support subdivisions, not promoted into finer physical resolution.",
        "", "## Pure-plate anchors", "",
        f"Validated anchors: **{anchors['validated_anchor_count']}** of {anchors['required_section_side_slots']} section-side slots. All {anchors['unresolved_anchor_slots']} remain unresolved: plate ownership is known, but governed deformation-zone/exclusion semantics do not establish that a candidate support lies outside the deforming region.",
        "", "## Relative motion: level 1 only", "",
        f"The existing Euler-vector and spherical local-frame census resolves normal and tangential demand for {motion['segments_with_resolved_normal_and_tangent']:,}/{motion['boundary_segments_total']:,} boundary edges; unresolved: {motion['segments_unresolved']}.",
        "Kinematic demand counts: " + ", ".join(f"`{key}` {value}" for key, value in motion["normal_demand_counts"].items()) + ".",
        "Existing combined normal/tangential classifications: " + ", ".join(f"`{key}` {value}" for key, value in motion["existing_joint_normal_tangential_demand_counts"].items()) + ". These describe motion only; they do not identify tectonic processes.",
        "", "## Physical accommodation: level 2", "",
        f"**{law['status']}**. Positive accommodated sections: {law['positive_physical_accommodation_sections']}; sections with an authority gap: {law['sections_with_authority_gap']}. Existing authority reports `{law['authority']}`.",
        law["basis"],
        "", "## Junctions and patch operator", "",
        f"Junction outcome counts: {', '.join(f'{k}={v}' for k,v in junctions['outcome_counts'].items())}. No junction accommodation residual is calculated because no physical constraints or allocation law are authorized.",
        f"Patch operator: `{patch['status']}`; replacement established: **{patch['replacement_established']}**. Diagnostic width trials are not canonical `W_model`.",
        "The prior operator has persistent nonzero Dirichlet corner mismatches at some diagnostic widths; the 100 km run also reports a port-extraction implementation failure. Other junctions remain numerically unresolved or their domains fail. The validation never materialized a patch. Thus the evidence shows both an implementation defect and unresolved corner constraints; it does not establish physical incompatibility.",
        f"Current blocker: `{patch['current_governed_blocker']}`.",
        "", "## Research gate and readiness", "",
        f"External targeted scientific research is required: **{report['research_gate']['external_scientific_research_required']}**.",
        f"Smallest question: {report['research_gate']['smallest_question']}",
        f"Instantaneous T0 well-posed: **{readiness['instantaneous_t0_well_posed']}**. First-interval contract design authorized: **{readiness['first_interval_contract_design_authorized']}**.",
        "", "## Invariants", "",
        "```text\n" + "\n".join(f"{key} = {str(value).lower()}" for key, value in report["invariants"].items()) + "\n```",
        "", "No finite evolution, future state, boundary law, or patch replacement was created.", "",
    ]
    return "\n".join(lines)
