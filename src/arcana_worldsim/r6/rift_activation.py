"""B6N1 same-time, zero-duration rift-process activation records.

This module constructs immutable records only. Canonical publication is kept in
the explicit script entry point and requires a precondition-checked apply.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping

from .checkpoint import CheckpointEnvelope
from .identity import PayloadIdentity, content_hash, thaw_json
from .replay import ReplayRecipe
from .state import (AuthorityClass, DomainStateEnvelope, SpatialSupport,
                    SupportClass, TimeSupport)
from .temporal import EventRecord

MODEL_ID = "MINIMAL_RIFT_PROCESS_ACTIVATION_V1"
ACTIVATION_EVENT_ID = "r6event_e357241de43a1d58c627f029fa1193b788fa02ca83aa1d28d79604949fa17fc6"
EVENT_TIME_KEY = "209.97287659484368Ma"
CAUSAL_PROTOCOL_ID = "SAME_TIME_CAUSAL_STATE_PROTOCOL_V1"
REPLAY_ADAPTER_ID = "arcana:r6-b6n1-rift-activation-v1"
REPLAY_SCHEMA = "B6N1_RIFT_PROCESS_ACTIVATION_REPLAY_V1"


@dataclass(frozen=True, slots=True)
class ActivationBundle:
    post_state: DomainStateEnvelope
    memory_state: DomainStateEnvelope
    application_event: EventRecord
    checkpoint: CheckpointEnvelope
    replay_recipe: ReplayRecipe
    process_version_id: str

    @property
    def records(self) -> tuple[Any, ...]:
        return (self.post_state, self.memory_state, self.application_event,
                self.checkpoint, self.replay_recipe)


def _predecessor_process_version_id(*, predecessor_state_id: str) -> str:
    return "r6process_" + content_hash({"predecessor_state_id": predecessor_state_id,
        "phase": "PRE_ACTIVATION"})


def _process_version_id(*, predecessor_state_id: str, activation_event_id: str) -> str:
    payload = {"activation_event_id": activation_event_id,
        "transition_model_id": MODEL_ID, "plate_pair": [1, 3],
        "phase": "RIFT_PROCESS_ACTIVE", "predecessor_process_version_id":
            _predecessor_process_version_id(predecessor_state_id=predecessor_state_id)}
    return "r6process_" + content_hash(payload)


def build_activation_bundle(pre_state: DomainStateEnvelope, *,
                            predecessor_event: EventRecord,
                            contract_hashes: Mapping[str, str],
                            async_domain_validity: tuple[Mapping[str, Any], ...] = ()) -> ActivationBundle:
    """Build one deterministic immutable application bundle from verified T1."""
    if str(pre_state.state_id) != predecessor_event.after_state_ids[0]:
        raise ValueError("pre-event state does not match canonical activation boundary")
    if predecessor_event.details.get("event_class") != "RIFT_PROCESS_ACTIVATION":
        raise ValueError("predicate record is not the governed rift activation")
    if predecessor_event.details.get("predicate") != "SATISFIED" or predecessor_event.details.get("transition") != "NOT_EXECUTED":
        raise ValueError("rift activation predicate is not satisfied and pending")
    if pre_state.time_support.time_key != EVENT_TIME_KEY:
        raise ValueError("pre-event state has a different physical time")
    if pre_state.domain != "tectonic_geometry":
        raise ValueError("pre-event state is not the governed tectonic geometry state")
    if not pre_state.payload_ref or pre_state.value.get("topology_identity") != predecessor_event.event_contract.get("spatial_support", {}).get("topology_identity"):
        raise ValueError("pre-event payload/topology binding is incomplete")

    activation_event_id = str(predecessor_event.record_id)
    causal_key = {"physical_time_key": EVENT_TIME_KEY,
        "causal_event_id": activation_event_id,
        "causal_sequence": 2, "causal_phase": "POST_EVENT"}
    version_id = _process_version_id(predecessor_state_id=str(pre_state.state_id),
                                     activation_event_id=activation_event_id)
    successor_value = thaw_json(pre_state.value)
    successor_value.update({"process_state": "RIFT_PROCESS_ACTIVE",
        "process_state_version_id": version_id,
        "transition_model_id": MODEL_ID,
        "activation_event_id": activation_event_id})
    applicability = thaw_json(pre_state.applicability)
    validity_matrix = [dict(row) for row in async_domain_validity]
    applicability.update({"causal_order_key": causal_key,
        "causal_protocol_id": CAUSAL_PROTOCOL_ID,
        "async_domain_validity": validity_matrix,
        "async_domain_validity_scope": "PRESERVED_AT_SOURCE_VALID_TIME; NO_RECOMPUTE",
        "post_event_kinematic_authority": "REQUIRES_REEVALUATION_BEFORE_DT2",
        "refinement_checkpoint_policy": "GEOMETRY_REUSABLE_WITH_EXPLICIT_CAUSAL_TOPOLOGY_VERSION",
        "pinned_pre_event_refinement_checkpoint":
            "r6checkpoint_5d090d52b1c495a81deb7c445e151e9cb72ccefd8c165846e77f31ded9589109"})
    post = DomainStateEnvelope.create(
        history_id=pre_state.history_id, branch_id=pre_state.branch_id,
        domain=pre_state.domain, time_support=pre_state.time_support,
        spatial_support=pre_state.spatial_support,
        support_class=pre_state.support_class, authority_class=pre_state.authority_class,
        value=successor_value, uncertainty=thaw_json(pre_state.uncertainty),
        provenance_ids=pre_state.provenance_ids,
        parent_state_ids=(str(pre_state.state_id),), payload_ref=pre_state.payload_ref,
        model_derived=pre_state.model_derived, applicability=applicability,
        conflict_flags=pre_state.conflict_flags,
        event_refs=(activation_event_id,),
        refinement_lineage=thaw_json(pre_state.refinement_lineage))

    event = EventRecord.create(history_id=pre_state.history_id,
        branch_id=pre_state.branch_id, time_key=EVENT_TIME_KEY,
        domain_ids=("tectonic_geometry", "system_memory"),
        authority_refs=(MODEL_ID, CAUSAL_PROTOCOL_ID),
        validation_status="VALIDATED",
        details={"event_class": "RIFT_PROCESS_ACTIVATION", "pair": [1, 3],
            "application_status": "EXECUTED", "transition_model_id": MODEL_ID,
            "activation_predicate_event_id": activation_event_id,
            "geometry_displacement": "ZERO", "plate_identity_change": "NONE",
            "support_graph_mutation": "NONE", "mechanics_executed": False,
            "cleared_continuation_guard": "CONTINUATION_BLOCKED_PENDING_RIFT_TRANSITION",
            "opening_distance": 0, "new_plate_created": False,
            "existing_plate_split": False, "oceanic_crust_created": False,
            "junction_rewire": False,
            "physical_temporal_epoch_created": False,
            "continuation_guard_after_publication":
                "CONTINUATION_BLOCKED_PENDING_POST_EVENT_KINEMATIC_AUTHORITY",
            "second_dt_selected": False, "t2_created": False,
            "contract_hashes": dict(sorted(contract_hashes.items()))},
        temporal_support={"time_key": EVENT_TIME_KEY,
            "causal_order_key": {"physical_time_key": EVENT_TIME_KEY,
                "causal_event_id": activation_event_id,
                "causal_sequence": 1, "causal_phase": "EVENT"}},
        spatial_support={"scope": "GLOBAL_CANONICAL_MESH",
            "topology_identity": pre_state.value["topology_identity"]},
        trigger_ref=predecessor_event.trigger_ref,
        cause_ref=activation_event_id,
        before_state_ids=(str(pre_state.state_id),),
        after_state_ids=(str(post.state_id),))

    memory_value = {
        "event_class": "RIFT_PROCESS_ACTIVATION", "activation_event_id": activation_event_id,
        "plate_pair": [1, 3], "physical_time_key": EVENT_TIME_KEY,
        "transition_model_id": MODEL_ID,
        "predecessor_topology_identity": pre_state.value["topology_identity"],
        "successor_topology_identity": post.value["topology_identity"],
        "predecessor_process_version_id": _predecessor_process_version_id(
            predecessor_state_id=str(pre_state.state_id)),
        "successor_process_version_id": version_id,
        "geometry_displacement_zero": True, "plate_identity_change_none": True,
        "support_graph_mutation_none": True, "mechanics_executed_false": True,
        "before_state_ids": [str(pre_state.state_id)],
        "after_state_ids": [str(post.state_id)],
        "causal_order_key": {"physical_time_key": EVENT_TIME_KEY,
            "causal_event_id": activation_event_id,
            "causal_sequence": 1, "causal_phase": "EVENT"},
        "continuation_guard":
            "CONTINUATION_BLOCKED_PENDING_POST_EVENT_KINEMATIC_AUTHORITY",
        "cleared_continuation_guard": "CONTINUATION_BLOCKED_PENDING_RIFT_TRANSITION",
        "second_dt_selected": False, "t2_created": False,
    }
    memory = DomainStateEnvelope.create(
        history_id=pre_state.history_id, branch_id=pre_state.branch_id,
        domain="system_memory", time_support=pre_state.time_support,
        spatial_support=SpatialSupport(None, selector_kind="GLOBAL"),
        support_class=SupportClass.DERIVED_SUPPORTED,
        authority_class=AuthorityClass.DIRECT_AUTHORITY,
        value=memory_value, provenance_ids=pre_state.provenance_ids,
        parent_state_ids=(str(pre_state.state_id), str(post.state_id)),
        event_refs=(str(event.record_id),),
        applicability={"causal_order_key": dict(memory_value["causal_order_key"]),
                       "causal_protocol_id": CAUSAL_PROTOCOL_ID})

    runtime = {"adapter": REPLAY_ADAPTER_ID, "schema": REPLAY_SCHEMA}
    configuration = {"transition_model_id": MODEL_ID,
        "causal_protocol_id": CAUSAL_PROTOCOL_ID,
        "contract_hashes": dict(sorted(contract_hashes.items()))}
    config_sha = content_hash(configuration)
    checkpoint = CheckpointEnvelope.create(
        history_id=pre_state.history_id, branch_id=pre_state.branch_id,
        time_key=EVENT_TIME_KEY, restart_state_ids=(str(pre_state.state_id),),
        retained_history_state_ids=(str(pre_state.state_id), str(post.state_id)),
        runtime_identity=runtime, configuration=configuration,
        seed_lineage={"determinism": "NO_RANDOMNESS",
            "activation_event_id": activation_event_id},
        validation_status="VALIDATED",
        restart_compatibility={"physical_time_unchanged": True,
            "geometry_payload_reused": True, "causal_phase": "PRE_EVENT"},
        authority_input_refs=(MODEL_ID, CAUSAL_PROTOCOL_ID))
    recipe = ReplayRecipe.create(
        history_id=pre_state.history_id, branch_id=pre_state.branch_id,
        base_checkpoint_id=str(checkpoint.checkpoint_id), runtime_identity=runtime,
        configuration_sha256=config_sha,
        seed_lineage={"determinism": "NO_RANDOMNESS",
            "activation_event_id": activation_event_id},
        forcing_ids=(), event_ids=(str(event.record_id),),
        expected_output_state_id=str(post.state_id),
        model_adapter_id=REPLAY_ADAPTER_ID,
        upstream_dependency_ids=(), provenance_ids=pre_state.provenance_ids,
        expected_payload_identity=(None if pre_state.payload_reference is None
            else pre_state.payload_reference.identity))
    return ActivationBundle(post, memory, event, checkpoint, recipe, version_id)


def replay_activation(pre_state: DomainStateEnvelope, *,
                      predecessor_event: EventRecord,
                      contract_hashes: Mapping[str, str],
                      async_domain_validity: tuple[Mapping[str, Any], ...] = ()) -> DomainStateEnvelope:
    """Deterministic zero-displacement replay of the frozen process activation."""
    return build_activation_bundle(pre_state, predecessor_event=predecessor_event,
        contract_hashes=contract_hashes,
        async_domain_validity=async_domain_validity).post_state


def validate_contract_attestation(repo_root: str) -> dict[str, str]:
    """Fail closed unless the committed B6NA attestation matches all contracts."""
    from pathlib import Path
    root = Path(repo_root)
    attestation = __import__("json").loads(
        (root / "docs/arcana/qualifications/R6_B6NA_ATTESTATION.json").read_text(encoding="utf-8"))
    if attestation.get("verdict") != "PASS_B6NA_TARGETED_RIFT_PROCESS_ACTIVATION_MODEL_DECISION":
        raise ValueError("B6NA attestation is not a PASS")
    hashes = {}
    for key in ("activation_model", "same_time_protocol", "second_dt_gate"):
        entry = attestation[key]
        path = root / entry["path"]
        actual = sha256(path.read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            raise ValueError(f"B6NA contract hash mismatch: {entry['path']}")
        hashes[entry["path"]] = actual
    return hashes
