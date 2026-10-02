from __future__ import annotations

import json
from hashlib import sha256
from io import BytesIO

import pytest

from arcana_worldsim.r6.adapters.climate import ClimateProviderAdapter
from arcana_worldsim.r6.checkpoint import CheckpointEnvelope, RefinementBranchEnvelope
from arcana_worldsim.r6.identity import (
    BranchId, HistoryId, PayloadIdentity, PayloadIntegrityError, PayloadReference,
    ProviderBindingId, verify_payload,
)
from arcana_worldsim.r6.identity import canonical_bytes
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.query import HistoryQueryService
from arcana_worldsim.r6.state import (
    AuthorityClass, DomainStateEnvelope, SpatialSupport, SupportClass, TimeSupport,
)
from arcana_worldsim.r6.store import HistoryStore, RecordIntegrityError, StoreSchemaError
from arcana_worldsim.r6.temporal import EventRecord, HistoricalSnapshot, RefinementAnchor


HISTORY = str(HistoryId.from_payload({"fixture": "b0-b-history"}))
BRANCH = str(BranchId.from_payload({"fixture": "b0-b-branch"}))
TIME = TimeSupport("b0-b:t0", "fixture-clock")
SPACE = SpatialSupport("fixture-grid", ("cell-1",), "native", "CELL_SET")


def make_state(*, domain="fixture", value=1, support=SupportClass.DIRECT_SUPPORTED,
               payload_ref=None, spatial=SPACE):
    return DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=BRANCH, domain=domain,
        time_support=TIME, spatial_support=spatial, support_class=support,
        authority_class=(AuthorityClass.NONE if support in {
            SupportClass.UNKNOWN, SupportClass.NOT_APPLICABLE, SupportClass.OUTSIDE_SCOPE
        } else AuthorityClass.DIRECT_AUTHORITY),
        value=None if support in {SupportClass.UNKNOWN, SupportClass.NOT_APPLICABLE,
                                  SupportClass.OUTSIDE_SCOPE} else value,
        uncertainty={}, payload_ref=payload_ref,
    )


def make_checkpoint():
    return CheckpointEnvelope.create(
        history_id=HISTORY, branch_id=BRANCH, time_key=TIME.time_key,
        restart_state_ids=(), retained_history_state_ids=(),
        runtime_identity={"fixture": "runtime"}, configuration={"mode": "fixture"},
        seed_lineage={"seed": 1},
    )


def test_store_manifest_created_reopened_and_incompatible_schema_rejected(tmp_path):
    root = tmp_path / "store"
    state = make_state()
    # A pre-manifest store containing an existing record is upgraded by adding
    # metadata only; the record body and semantic identity remain untouched.
    legacy_states = root / "states"
    legacy_states.mkdir(parents=True)
    legacy_record = legacy_states / f"{state.state_id}.json"
    legacy_record.write_bytes(canonical_bytes(state.to_dict()) + b"\n")
    original = HistoryStore(root)
    assert original.read_state(str(state.state_id)) == state
    assert json.loads(legacy_record.read_text())["state_id"] == str(state.state_id)
    original.append_state(state)
    manifest = json.loads((root / "metadata" / "store_manifest.json").read_text())
    assert manifest == HistoryStore.MANIFEST
    assert str(root) not in json.dumps(manifest)

    del original
    reopened = HistoryStore(root)
    assert reopened.read_state(str(state.state_id)) == state

    manifest["record_layout_version"] += 1
    (root / "metadata" / "store_manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(StoreSchemaError, match="incompatible"):
        HistoryStore(root)


def test_corrupt_typed_records_fail_on_direct_reads(tmp_path):
    store = HistoryStore(tmp_path / "store")
    state = make_state()
    store.append_state(state)
    provenance = ProvenanceRecord.create(activity="fixture", source_refs=("source",))
    store.append_provenance(provenance)
    event = EventRecord.create(history_id=HISTORY, branch_id=BRANCH,
                               time_key=TIME.time_key, details={"kind": "fixture"})
    store.append_event(event)
    checkpoint = make_checkpoint()
    store.append_checkpoint(checkpoint)
    temporal = HistoricalSnapshot.create(history_id=HISTORY, branch_id=BRANCH,
                                         time_key=TIME.time_key)
    store.append_temporal(temporal)
    refinement_anchor = RefinementAnchor.create(history_id=HISTORY, branch_id=BRANCH,
        time_key=TIME.time_key, details={"region_id": "r1"})
    branch = RefinementBranchEnvelope.create(history_id=HISTORY,
        parent_branch_id=BRANCH, base_history_id=HISTORY,
        refinement_anchor_id=refinement_anchor.record_id, region_id="r1",
        time_interval=("t0", "t1"), requested_domains=("fixture",),
        requested_resolution="native")
    store.append_refinement_branch(branch)

    binding_body = {
        "provider_id": "fixture-provider", "source_sha256": sha256(b"source").hexdigest(),
        "source_semantics": "fixture", "time_key": TIME.time_key,
        "coordinate_system": TIME.coordinate_system, "grid_id": SPACE.grid_id,
        "cell_ids": list(SPACE.cell_ids), "variables": {"x": {"units": "1"}},
        "authority_class": AuthorityClass.FIXTURE_ONLY.value,
        "support_class": SupportClass.FIXTURE_ONLY.value,
        "authority_refs": [], "applicability": {},
    }
    binding_id = str(ProviderBindingId.from_payload(binding_body))
    store.append_provider_binding(binding_id, binding_body)

    corruptions = [
        ("states", str(state.state_id), "value", {"changed": True},
         lambda: store.read_state(str(state.state_id))),
        ("events", event.record_id, "details", {"changed": True},
         lambda: store.read_event(event.record_id)),
        ("provenance", str(provenance.record_id), "attributes", {"changed": True},
         lambda: store.read_provenance(str(provenance.record_id))),
        ("checkpoints", str(checkpoint.checkpoint_id), "time_key", "changed",
         lambda: store.read_checkpoint(str(checkpoint.checkpoint_id))),
        ("provider_bindings", binding_id, "provider_id", "changed",
         lambda: store.read_provider_binding(binding_id)),
        ("temporal", temporal.record_id, "time_key", "changed",
         lambda: store.read_temporal(temporal.record_id)),
        ("refinement_branches", str(branch.branch_id), "region_id", "changed",
         lambda: store.read_refinement_branch(str(branch.branch_id))),
    ]
    for bucket, key, field, changed, read in corruptions:
        path = tmp_path / "store" / bucket / f"{key}.json"
        body = json.loads(path.read_text())
        body[field] = changed
        path.write_text(json.dumps(body))
        with pytest.raises(RecordIntegrityError):
            read()


def test_payload_identity_is_distinct_and_verification_is_explicit(tmp_path):
    payload = b"same immutable fixture payload"
    digest = sha256(payload).hexdigest()
    ref = PayloadReference.parse(f"payload://sha256/{digest}#fields-a")
    assert ref.identity == PayloadIdentity("sha256", digest)
    assert verify_payload(ref, payload) == ref.identity
    assert verify_payload(ref, BytesIO(payload)) == ref.identity
    payload_path = tmp_path / "payload.bin"
    payload_path.write_bytes(payload)
    assert verify_payload(ref, payload_path) == ref.identity
    with pytest.raises(PayloadIntegrityError, match="digest"):
        verify_payload(ref, b"different")
    with pytest.raises(PayloadIntegrityError, match="no verifiable"):
        verify_payload("legacy-opaque-payload-ref", payload)

    legacy = f"sha256:{digest}"
    by_string = make_state(domain="domain-a", value={"a": 1}, payload_ref=legacy)
    by_typed_ref = make_state(domain="domain-a", value={"a": 1},
                              payload_ref=PayloadReference.parse(legacy))
    state_b = make_state(domain="domain-b", value={"b": 2}, payload_ref=legacy)
    assert by_string.state_id == by_typed_ref.state_id
    assert by_string.state_id != state_b.state_id

    store = HistoryStore(tmp_path / "records")
    store.append_state(by_string)
    store.append_state(state_b)
    reopened = HistoryStore(tmp_path / "records")
    loaded_a = reopened.read_state(str(by_string.state_id))
    loaded_b = reopened.read_state(str(state_b.state_id))
    assert loaded_a.state_id == by_string.state_id
    assert loaded_b.state_id == state_b.state_id
    assert loaded_a.payload_reference.identity == PayloadIdentity("sha256", digest)
    assert PayloadReference.parse(loaded_a.payload_ref).identity == PayloadReference.parse(
        loaded_b.payload_ref).identity


@pytest.mark.parametrize("value", [0, 0.0, False])
def test_known_zero_and_false_remain_known_query_values(tmp_path, value):
    store = HistoryStore(tmp_path / f"store-{type(value).__name__}")
    state = make_state(domain=f"known-{type(value).__name__}", value=value)
    store.append_state(state)
    result = HistoryQueryService(store).state_at(
        history_id=HISTORY, branch_id=BRANCH, domain=state.domain,
        time_key=TIME.time_key, cell_id="cell-1")
    assert result.status == "FOUND"
    assert result.state.value == value
    assert result.state.support_class is SupportClass.DIRECT_SUPPORTED


def test_query_distinguishes_missing_unknown_and_outside_declared_support(tmp_path):
    store = HistoryStore(tmp_path / "store")
    store.append_state(make_state(domain="known", value=0))
    store.append_state(make_state(domain="unknown", support=SupportClass.UNKNOWN))
    store.append_state(make_state(domain="na", support=SupportClass.NOT_APPLICABLE))
    store.append_state(make_state(domain="outside-scope", support=SupportClass.OUTSIDE_SCOPE))
    grid_state = make_state(domain="grid", value={"x": 1}, spatial=SpatialSupport(
        "grid", (), "native", "GRID"))
    store.append_state(grid_state)
    query = HistoryQueryService(store)
    def get(domain, cell="cell-1", time=TIME.time_key):
        return query.state_at(history_id=HISTORY, branch_id=BRANCH,
                              domain=domain, time_key=time, cell_id=cell).status
    assert get("absent") == "MISSING_DOMAIN"
    assert get("known", time="missing-time") == "MISSING_TIMESTAMP"
    assert get("known", cell="outside-cell") == "OUTSIDE_SUPPORT"
    assert get("grid", cell="cell-1") == "SUPPORT_MISMATCH"
    assert get("unknown") == "UNKNOWN"
    assert get("na") == "NOT_APPLICABLE"
    assert get("outside-scope") == "OUTSIDE_SCOPE"
    assert get("known") == "FOUND"
