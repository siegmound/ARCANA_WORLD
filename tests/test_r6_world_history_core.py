from __future__ import annotations

import json
from pathlib import Path

from arcana_worldsim.r6.checkpoint import CheckpointEnvelope, RefinementBranchEnvelope
from arcana_worldsim.r6.identity import BranchId, DomainStateId, HistoryId
from arcana_worldsim.r6.planning import (
    DOMAIN_REGISTRY_SERVICE, ENGINE_ROLE_REGISTRY, RECORD_RETENTION,
    RetentionClass, required_dependencies,
)
from arcana_worldsim.r6.query import HistoryQueryService
from arcana_worldsim.r6.state import (
    AuthorityClass, DomainStateEnvelope, SpatialSupport, SupportClass, TimeSupport,
)
from arcana_worldsim.r6.store import HistoryStore
from arcana_worldsim.r6.temporal import EventRecord, RefinementAnchor

HISTORY = str(HistoryId.from_payload({"test": "world-history"}))
BRANCH = str(BranchId.from_payload({"test": "main"}))


def state(**kwargs):
    return DomainStateEnvelope.create(history_id=HISTORY, branch_id=BRANCH,
        domain="climate", time_support=TimeSupport("t0", "fixture-clock"),
        spatial_support=SpatialSupport("grid", ("cell-a",), "native", "CELL_SET"),
        support_class=SupportClass.FIXTURE_ONLY,
        authority_class=AuthorityClass.FIXTURE_ONLY,
        value={"temperature": 3}, **kwargs)


def test_state_extension_roundtrip_and_legacy_identity_read():
    current = state(model_derived=True, applicability={"status": "regional"},
        conflict_flags=("fixture-conflict",), event_refs=("event-x",),
        refinement_lineage={"parent": "state-y"})
    restored = DomainStateEnvelope.from_dict(current.to_dict())
    assert restored == current
    assert restored.model_derived is True
    legacy_body = {"schema_version": "ARCANA_R6_DOMAIN_STATE_V0",
        "history_id": HISTORY, "branch_id": BRANCH, "domain": "climate",
        "time_support": current.time_support.to_dict(),
        "spatial_support": current.spatial_support.to_dict(),
        "support_class": current.support_class.value,
        "authority_class": current.authority_class.value,
        "value": {"temperature": 3}, "uncertainty": {},
        "provenance_ids": [], "parent_state_ids": [], "payload_ref": None}
    legacy_body["uncertainty"] = {}
    from arcana_worldsim.r6.identity import thaw_json
    legacy_body["uncertainty"] = thaw_json(current.uncertainty)
    legacy = {**legacy_body, "state_id": str(DomainStateId.from_payload(legacy_body))}
    assert DomainStateEnvelope.from_dict(legacy).to_dict()["schema_version"] == "ARCANA_R6_DOMAIN_STATE_V0"


def test_event_checkpoint_and_refinement_metadata_roundtrip(tmp_path):
    event = EventRecord.create(history_id=HISTORY, branch_id=BRANCH, time_key="t0",
        temporal_support={"window": ["t0", "t1"]}, spatial_support={"region": "r1"},
        trigger_ref="trigger-1", cause_ref="cause-1", before_state_ids=("s0",),
        after_state_ids=("s1",), causal_dependency_ids=("dep-1",))
    assert event.event_contract["cause_ref"] == "cause-1"
    checkpoint = CheckpointEnvelope.create(history_id=HISTORY, branch_id=BRANCH,
        time_key="t0", restart_state_ids=(), retained_history_state_ids=(),
        runtime_identity={"python": "fixture"}, configuration={}, seed_lineage={},
        parent_checkpoint_id="parent", authority_input_refs=("authority",),
        provider_manifest_refs=("provider-manifest",), engine_versions={"ARCANA": "v0"},
        output_manifest={"outputs": []})
    assert CheckpointEnvelope.from_dict(checkpoint.to_dict()) == checkpoint
    anchor = RefinementAnchor.create(history_id=HISTORY, branch_id=BRANCH,
        time_key="t0", domain_ids=("climate",), details={"region_id": "r1"})
    branch = RefinementBranchEnvelope.create(history_id=HISTORY,
        parent_branch_id=BRANCH, base_history_id=HISTORY,
        refinement_anchor_id=anchor.record_id, region_id="r1", time_interval=("t0", "t1"),
        requested_domains=("climate",), requested_resolution="native",
        parent_boundary_conditions={"status": "unspecified"},
        provenance_refs=("prov-1",))
    store = HistoryStore(tmp_path / "history")
    store.append_event(event)
    store.append_checkpoint(checkpoint)
    store.append_temporal(anchor)
    store.append_refinement_branch(branch)
    assert store.events() == (event,)
    assert store.checkpoints() == (checkpoint,)
    assert store.read_refinement_branch(str(branch.branch_id)) == branch
    candidates = HistoryQueryService(store).refinement_candidates(
        history_id=HISTORY, branch_id=BRANCH, domain="climate", region_id="r1")
    assert str(branch.branch_id) in {row["record_id"] for row in candidates}


def test_query_surface_and_non_scientific_planning(tmp_path):
    store = HistoryStore(tmp_path / "history")
    item = state()
    store.append_state(item)
    query = HistoryQueryService(store)
    assert query.history(history_id=HISTORY) == (item,)
    assert query.search(history_id=HISTORY, equals={"temperature": 3}) == (item,)
    assert query.lineage(str(item.state_id))["state_lineage"][0]["event_refs"] == []
    assert query.available_resolution(history_id=HISTORY)["native_resolutions"] == ["native"]
    assert DOMAIN_REGISTRY_SERVICE.get("climate").domain_id == "climate"
    assert len(DOMAIN_REGISTRY_SERVICE.all()) == 13
    root = Path(__file__).parents[1]
    architecture = json.loads((root / "docs/strategy/R6_WORLD_HISTORY_ARCHITECTURE_CONTRACT.json").read_text(encoding="utf-8"))
    assert {row.domain_id for row in DOMAIN_REGISTRY_SERVICE.all()} == {
        row["id"] for row in architecture["domain_registry"]}
    cone = required_dependencies(("human_demography",), region="r1", time_interval=("t0", "t1"))
    assert cone == required_dependencies(("human_demography",), region="r1", time_interval=("t0", "t1"))
    assert "physical_world" in cone.required_domains
    assert cone.feedback_groups
    assert RECORD_RETENTION["canonical_state"] is RetentionClass.RETAIN_ALWAYS
    assert all(engine.scientific_authority == "ARCANA" for engine in ENGINE_ROLE_REGISTRY)
    assert cone.to_dict()["scientific_execution"] is False
