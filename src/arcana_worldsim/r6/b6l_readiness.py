"""B6L candidate support, publication-plan, and continuation contracts.

This module contains query/plan helpers only. It has no canonical publication
entry point and never executes event transitions.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, Sequence


class CandidateSupportIndex:
    """Set-valued lookup over deterministic B6K (canonical node, plate) rows."""

    def __init__(self, *, candidate_id: str, pairs: Sequence[tuple[int, int]],
                 interfaces: Sequence[Mapping[str, Any]],
                 junctions: Sequence[Mapping[str, Any]],
                 source_t0_identity: str = "UNBOUND_FIXTURE_SOURCE"):
        if not candidate_id or len(set(pairs)) != len(pairs):
            raise ValueError("candidate identity and unique support pairs are required")
        self.candidate_id = candidate_id
        self._by_node: dict[int, list[dict[str, Any]]] = defaultdict(list)
        self._by_representation: dict[str, dict[str, Any]] = {}
        interface_membership: dict[tuple[int, int], list[str]] = defaultdict(list)
        for interface in interfaces:
            boundary_id = str(interface["boundary_id"])
            incident = tuple(int(value) for value in interface["incident_plate_ids"])
            endpoint_rows = interface["sides"]
            if len(incident) != 2 or len(endpoint_rows) != 2:
                raise ValueError("boundary interface must have two explicit plate sides")
            for side in endpoint_rows:
                plate = int(side["plate_id"])
                if plate not in incident:
                    raise ValueError("boundary side plate is outside its governed incident set")
                for row_index in side["coordinate_rows"]:
                    node_id, row_plate = pairs[int(row_index)]
                    if int(row_plate) != plate:
                        raise ValueError("boundary coordinate row has mismatched plate identity")
                    interface_membership[(int(node_id), plate)].append(boundary_id)
        junction_membership: dict[tuple[int, int], list[str]] = defaultdict(list)
        for junction in junctions:
            node_id = int(junction["canonical_node_id"])
            junction_id = str(junction["junction_id"])
            plates = tuple(int(v) for v in junction["incident_plate_ids"])
            if len(plates) < 3 or len(set(plates)) != len(plates):
                raise ValueError("junction support must retain a set of 3+ incident plates")
            for plate in plates:
                junction_membership[(node_id, plate)].append(junction_id)
        for node_id, plate_id in pairs:
            key = (int(node_id), int(plate_id))
            rep_id = "r6repr_" + sha256(
                f"{candidate_id}:{key[0]}:{key[1]}".encode("ascii")).hexdigest()
            row = {"representation_id": rep_id, "candidate_id": candidate_id,
                   "source_canonical_node_id": key[0], "representation_role": "PLATE_LOCAL_NODE",
                   "plate_support": key[1], "boundary_interface_ids": sorted(set(interface_membership[key])),
                   "junction_ids": sorted(set(junction_membership[key])),
                   "representation_lineage": {"source_t0_identity": source_t0_identity,
                       "source_canonical_node_id": key[0], "plate_support": key[1],
                       "candidate_id": candidate_id,
                       "lineage_reference": "outputs/r6_b6k_isolated_first_candidate_state/B6K_LINEAGE.json"},
                   "support_is_set_valued": True, "unique_owner": None}
            self._by_node[key[0]].append(row)
            if rep_id in self._by_representation:
                raise ValueError("candidate representation identity collision")
            self._by_representation[rep_id] = row
        for rows in self._by_node.values():
            rows.sort(key=lambda row: (row["plate_support"], row["representation_id"]))

    def representations_for_source(self, canonical_node_id: int) -> tuple[dict[str, Any], ...]:
        rows = self._by_node.get(int(canonical_node_id))
        if not rows:
            raise KeyError(f"unknown canonical source node: {canonical_node_id}")
        return tuple(dict(row) for row in rows)

    def source_for_representation(self, representation_id: str) -> dict[str, Any]:
        try:
            return dict(self._by_representation[representation_id])
        except KeyError as exc:
            raise KeyError(f"unknown candidate representation: {representation_id}") from exc

    def summary(self) -> dict[str, int | bool]:
        memberships = [len(rows) for rows in self._by_node.values()]
        return {"canonical_node_count": len(self._by_node),
                "candidate_representation_count": len(self._by_representation),
                "extra_multi_support_rows": sum(count - 1 for count in memberships),
                "nodes_with_multi_support": sum(count > 1 for count in memberships),
                "identity_collisions": 0, "unexplained_rows": 0,
                "lost_canonical_nodes": 0, "arbitrary_support_owners": 0}


def continuation_guard(*, event_transition_status: str,
                       ordinary_step_requested: bool) -> str:
    """Block ordinary continuation past an unreconciled event boundary."""
    if ordinary_step_requested and event_transition_status != "EXECUTED":
        return "CONTINUATION_BLOCKED_PENDING_RIFT_TRANSITION"
    return "CONTINUATION_ALLOWED"


def canonical_publication_plan(*, candidate_id: str, candidate_state_id: str,
                               payload_sha256: str, topology_identity: str,
                               replay_recipe_id: str, dt_hex: str,
                               target_age_ma: float) -> dict[str, Any]:
    """Describe the future transaction without executing canonical writes."""
    records = [
        {"record": "canonical_first_state_semantic_record", "action": "NEW_CANONICAL_RECORD"},
        {"record": "candidate_payload", "action": "PROMOTE_CANDIDATE_PAYLOAD_REFERENCE"},
        {"record": "source_T0_payloads", "action": "REFERENCE_EXISTING_PAYLOAD"},
        {"record": "dt_and_kinematic_provenance", "action": "NEW_CANONICAL_RECORD"},
        {"record": "ReplayRecipe", "action": "NEW_CANONICAL_RECORD"},
        {"record": "event_boundary_and_topology_hold", "action": "NEW_CANONICAL_RECORD"},
        {"record": "candidate lineage and support relation", "action": "NEW_CANONICAL_RECORD"},
        {"record": "async temporal validity and transfer declarations", "action": "NEW_CANONICAL_RECORD"},
        {"record": "existing required system memory", "action": "REFERENCE_EXISTING_PAYLOAD"},
        {"record": "candidate state duplicate", "action": "NO_ACTION_REQUIRED"},
    ]
    return {"schema": "R6_B6L_CANONICAL_PUBLICATION_PLAN_V1",
            "publication_executed": False,
            "canonical_state_class": "CANONICAL_FIRST_STATE_AT_RIFT_ACTIVATION_BOUNDARY_PRETRANSITION",
            "candidate_id": candidate_id, "candidate_state_id": candidate_state_id,
            "candidate_payload_sha256": payload_sha256, "topology_identity": topology_identity,
            "replay_recipe_id": replay_recipe_id, "dt_hex": dt_hex,
            "target_age_ma": target_age_ma,
            "semantic_constraints": {"rift_transition": "NOT_EXECUTED",
                "topology": "PRE_TRANSITION_IDENTITY_HELD",
                "asynchronous_domains": "RETAIN_PREVIOUS_LATEST_VALID_TIME",
                "model_scope_limitations": "PRESERVED",
                "continuation_prerequisite": "RIFT_TRANSITION_MUST_BE_AUTHORIZED_AND_EXECUTED"},
            "atomic_bundle_records": records,
            "payload_policy": "REFERENCE_OR_PROMOTE_EXISTING_CONTENT_ID; NO_COPY"}
