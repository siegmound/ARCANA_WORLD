from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
import json

import pytest

from arcana_worldsim.r6.adapters.climate import ClimateProviderAdapter
from arcana_worldsim.r6.adapters.hydrology import HydrologyAdapterError, HydrologyAdapterV0
from arcana_worldsim.r6.bootstrap import create_bootstrap_manifest
from arcana_worldsim.r6.checkpoint import CheckpointEnvelope
from arcana_worldsim.r6.consumer import ConsumerStateRequest
from arcana_worldsim.r6.identity import BranchId, HistoryId, R6RunId
from arcana_worldsim.r6.provenance import ProvenanceIntegrityError, ProvenanceRecord
from arcana_worldsim.r6.registry import ProviderDescriptor, ProviderRegistry, TemporalAuthorityRegistry
from arcana_worldsim.r6.query import HistoryQueryService
from arcana_worldsim.r6.state import (
    AuthorityClass, DomainStateEnvelope, SpatialSupport, SupportClass, TimeSupport,
)
from arcana_worldsim.r6.store import HistoryStore, ImmutableRecordConflict
from arcana_worldsim.r6.temporal import (
    AuthorityAnchor, ConsumerCheckpoint, EventRecord, HistoricalSnapshot, ProviderTimestamp,
    RefinementAnchor, SimulationCheckpoint,
)


HISTORY = str(HistoryId.from_payload({"fixture": "wave1-history"}))
BRANCH = str(BranchId.from_payload({"fixture": "mainline"}))
TIME = TimeSupport("fixture:t0", "fixture-clock")
SPACE = SpatialSupport("fixture-grid-v0", ("cell-1",), "fixture-native", "CELL_SET")


def make_state(domain="climate", *, support=SupportClass.FIXTURE_ONLY,
               authority=AuthorityClass.FIXTURE_ONLY, value=None, branch=BRANCH,
               time=TIME, spatial=SPACE, provenance=(), parents=(), history=HISTORY):
    if value is None and support == SupportClass.FIXTURE_ONLY:
        value = {"fixture_value": 1.25}
    return DomainStateEnvelope.create(
        history_id=history, branch_id=branch, domain=domain, time_support=time,
        spatial_support=spatial, support_class=support, authority_class=authority,
        value=value, uncertainty={"fixture": "not scientific uncertainty estimate"},
        provenance_ids=tuple(provenance), parent_state_ids=tuple(parents),
    )


def climate_binding(*, time=TIME, cell_ids=("cell-1",), support=SupportClass.FIXTURE_ONLY):
    return ClimateProviderAdapter().bind(
        history_id=HISTORY, branch_id=BRANCH, provider_id="fixture-climate-provider",
        source_sha256=sha256(b"local synthetic metadata fixture").hexdigest(),
        source_semantics="SYNTHETIC_FIXTURE_NOT_PROVIDER_EVIDENCE",
        time_key=time.time_key, coordinate_system=time.coordinate_system,
        grid_id="fixture-grid-v0", cell_ids=tuple(cell_ids),
        variable_metadata={"temperature_c": {
            "source_variable": "tas_fixture", "units": "degC",
            "dimensions": ["time", "cell"], "temporal_semantics": "annual_fixture_mean",
        }}, values={"temperature_c": [12.0] * len(cell_ids)},
        required_units={"temperature_c": "degC"},
        authority_class=AuthorityClass.FIXTURE_ONLY, support_class=support,
        native_resolution="one synthetic fixture cell",
    )


def test_identity_is_deterministic_versioned_and_path_independent():
    assert R6RunId.from_payload({"seed": 8, "config": "abc"}) == R6RunId.from_payload(
        {"config": "abc", "seed": 8}
    )
    assert str(R6RunId.from_payload({"x": 1})).startswith("r6run_")
    assert str(HistoryId.from_payload({"x": 1})) != str(BranchId.from_payload({"x": 1}))
    with pytest.raises(ValueError, match="absolute machine path"):
        R6RunId.from_payload({"cache": r"C:\data\provider.nc"})


def test_bootstrap_identity_is_deterministic_and_explicitly_unbound():
    body = {
        "canonical_initial_binding_ref": "R6_CANONICAL_INITIAL_STATE_BINDING.json",
        "canonical_initial_binding_status": "BLOCKED_UNBOUND",
        "canonical_law_refs": [], "cha_contract_refs": [], "provider_refs": [],
        "dependency_sha256": {"contract": "a" * 64}, "engine_registry": {},
        "seed_ensemble_lineage": {"status": "UNSET"}, "grid_ref": "UNKNOWN",
        "time_ref": "R6_TBD", "runtime_environment_identity": {"python": "3"},
        "known_gaps": ["NO_CANONICAL_INITIAL_PACKAGE"], "unknown_policy": "PRESERVE_UNKNOWN",
        "repository_identity": {"commit": "test-id"},
    }
    first = create_bootstrap_manifest(body)
    assert first == create_bootstrap_manifest(dict(reversed(list(body.items()))))
    assert first["canonical_initial_state_bound"] is False
    assert first["scientific_execution_authorized"] is False


def test_provider_registry_and_temporal_roles_are_deterministic():
    provider = ProviderDescriptor(
        provider_id="krapp-2021-local-reference", product_id="KRAPP_2021_800KA",
        version="OSF-8N43X", variables={"tas": {"units": "K", "semantic_role": "annual_temperature"}},
        native_grid="0.5-degree", native_resolution="0.5 degree", temporal_support="1 ka snapshots",
        semantics="statistical reconstruction; not direct transient GCM",
        authority_role="REFERENCE_ONLY", data_cache_sha256=None,
        provenance_ref="P7S-adjudication", applicability={"status": "COHORT_LIMITED"},
        missing_variables=("monthly_temperature", "sunshine"), adapter_id="climate-v0")
    registry = ProviderRegistry()
    registry.register(provider)
    registry.register(provider)
    assert registry.get(provider.provider_id).to_dict() == provider.to_dict()
    with pytest.raises(ValueError, match="already bound"):
        registry.register(replace(provider, version="other"))
    temporal = TemporalAuthorityRegistry()
    provider_time = ProviderTimestamp.create(history_id=HISTORY, branch_id=BRANCH,
                                             time_key="provider:200ka")
    anchor = AuthorityAnchor.create(history_id=HISTORY, branch_id=BRANCH,
                                    time_key="provider:200ka", details={"role": "source-time"})
    checkpoint = ConsumerCheckpoint.create(history_id=HISTORY, branch_id=BRANCH,
                                           time_key="consumer:200ka", details={"role": "consumer-request"})
    temporal.register(provider_time)
    temporal.register(anchor)
    temporal.register(checkpoint)
    assert temporal.records("PROVIDER_TIMESTAMP") == (provider_time,)
    assert temporal.records("AUTHORITY_ANCHOR") == (anchor,)
    assert temporal.records("CONSUMER_CHECKPOINT") == (checkpoint,)


def test_typed_consumer_request_accepts_matching_climate_upstream():
    climate = make_state(domain="climate", value={"variables": {"tas": [1.0]}},
                         support=SupportClass.SPARSE_AUTHORITY,
                         authority=AuthorityClass.SPARSE_AUTHORITY)
    request = ConsumerStateRequest(
        consumer_id="hydrology-v0", upstream_domains=("climate",), time_key=TIME.time_key,
        region_id="region-1", grid_id=SPACE.grid_id, cell_ids=SPACE.cell_ids,
        variables=("tas",), minimum_authority=AuthorityClass.SPARSE_AUTHORITY,
        unknown_policy="REJECT", minimum_resolution="NATIVE_OR_COARSER_EXPLICIT", reason="hydrology dependency")
    request.validate_inputs((climate,))
    with pytest.raises(ValueError, match="time"):
        request.validate_inputs((make_state(domain="climate", time=TimeSupport("other", TIME.coordinate_system)),))


def test_state_schema_and_value_do_not_imply_authority():
    state = DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=BRANCH, domain="climate", time_support=TIME,
        spatial_support=SPACE, support_class=SupportClass.FIXTURE_ONLY,
        authority_class=AuthorityClass.NONE, value={"numeric": 42},
        uncertainty={}, payload_ref="payload:sha256:" + "a" * 64,
    )
    assert state.value["numeric"] == 42
    assert state.authority_class is AuthorityClass.NONE
    assert DomainStateEnvelope.from_dict(state.to_dict()).payload_ref == state.payload_ref
    with pytest.raises(FrozenInstanceError):
        state.domain = "changed"
    with pytest.raises(TypeError):
        state.value["numeric"] = 0
    bad = state.to_dict()
    bad["schema_version"] = "R5"
    with pytest.raises(ValueError, match="schema"):
        DomainStateEnvelope.from_dict(bad)


@pytest.mark.parametrize("support", [SupportClass.UNKNOWN, SupportClass.NOT_APPLICABLE,
                                      SupportClass.OUTSIDE_SCOPE])
def test_unknown_na_and_outside_scope_round_trip_without_values(support):
    state = make_state(support=support, authority=AuthorityClass.NONE, value=None)
    assert DomainStateEnvelope.from_dict(state.to_dict()) == state
    with pytest.raises(ValueError, match="must not carry"):
        make_state(support=support, authority=AuthorityClass.NONE, value={"x": 0})


def test_temporal_roles_are_distinct_record_types():
    common = {"history_id": HISTORY, "branch_id": BRANCH, "time_key": "fixture:t1"}
    records = [
        AuthorityAnchor.create(**common), SimulationCheckpoint.create(**common),
        HistoricalSnapshot.create(**common), EventRecord.create(**common),
        RefinementAnchor.create(**common), ConsumerCheckpoint.create(**common),
    ]
    assert len({type(item) for item in records}) == 6
    assert len({item.ROLE for item in records}) == 6
    assert records[3].record_id.startswith("r6event_")


def test_history_event_and_checkpoint_round_trip_after_store_reopen(tmp_path):
    store = HistoryStore(tmp_path / "history")
    state = make_state(domain="hydrology")
    assert store.append_state(state) == str(state.state_id)
    event = EventRecord.create(history_id=HISTORY, branch_id=BRANCH, time_key="fixture:t0",
                               domain_ids=("hydrology",), state_ids=(str(state.state_id),),
                               details={"event_type": "fixture-boundary"})
    store.append_event(event)
    snapshot = HistoricalSnapshot.create(history_id=HISTORY, branch_id=BRANCH,
                                         time_key="fixture:t0", state_ids=(str(state.state_id),))
    store.append_temporal(snapshot)
    checkpoint = CheckpointEnvelope.create(
        history_id=HISTORY, branch_id=BRANCH, time_key="fixture:t0",
        restart_state_ids=(str(state.state_id),),
        retained_history_state_ids=(str(state.state_id),),
        runtime_identity={"adapter": "fixture-v0", "python": "test-runtime"},
        configuration={"mode": "fixture"}, seed_lineage={"seed": 17},
        upstream_dependency_ids=("fixture-source",),
        restart_compatibility={"schema": "v0"},
    )
    store.append_checkpoint(checkpoint)
    reopened = HistoryStore(tmp_path / "history")
    assert reopened.read_state(str(state.state_id)) == state
    assert reopened.read_event(event.record_id)["details"]["event_type"] == "fixture-boundary"
    assert reopened.read_temporal(snapshot.record_id)["role"] == "HISTORICAL_SNAPSHOT"
    loaded = CheckpointEnvelope.from_dict(reopened.read_checkpoint(str(checkpoint.checkpoint_id)))
    assert loaded == checkpoint
    assert loaded.compatible_with(
        runtime_identity={"adapter": "fixture-v0", "python": "test-runtime"},
        configuration_sha256=checkpoint.configuration_sha256,
        seed_lineage={"seed": 17},
        required_dependencies=("fixture-source",),
        restart_compatibility={"schema": "v0"},
    )
    assert not loaded.compatible_with(
        runtime_identity={"adapter": "different"},
        configuration_sha256=checkpoint.configuration_sha256,
        seed_lineage={"seed": 17},
        required_dependencies=("fixture-source",),
        restart_compatibility={"schema": "v0"},
    )
    altered = checkpoint.to_dict()
    altered["time_key"] = "tampered"
    with pytest.raises(ValueError, match="identity"):
        CheckpointEnvelope.from_dict(altered)
    assert loaded.restart_state_ids == loaded.retained_history_state_ids
    record_path = tmp_path / "history" / "states" / f"{state.state_id}.json"
    tampered = json.loads(record_path.read_text(encoding="utf-8"))
    tampered["value"] = {"altered": True}
    record_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ImmutableRecordConflict):
        reopened.append_state(state)


def test_history_and_branch_scoped_query_including_missing_cases(tmp_path):
    store = HistoryStore(tmp_path / "query")
    known_prov = ProvenanceRecord.create(activity="known-fixture", source_refs=("fixture-source",))
    known = make_state(domain="climate", value={"temperature_c": 12.0},
                       provenance=(str(known_prov.record_id),))
    unknown = make_state(domain="fauna", support=SupportClass.UNKNOWN,
                         authority=AuthorityClass.NONE, value=None)
    not_applicable = make_state(domain="marine_ecology", support=SupportClass.NOT_APPLICABLE,
                                authority=AuthorityClass.NONE, value=None)
    other_branch = str(BranchId.from_payload({"fixture": "separate-branch"}))
    isolated = make_state(domain="climate", value={"temperature_c": -9.0}, branch=other_branch)
    other_history = str(HistoryId.from_payload({"fixture": "other-history"}))
    isolated_history = make_state(domain="climate", value={"temperature_c": -7.0},
                                  history=other_history)
    store.append_provenance(known_prov)
    for state in (known, unknown, not_applicable, isolated, isolated_history):
        store.append_state(state)
    query = HistoryQueryService(store)
    result = query.state_at(history_id=HISTORY, branch_id=BRANCH, domain="climate",
                            time_key=TIME.time_key, cell_id="cell-1")
    assert result.status == "FOUND" and result.state.value["temperature_c"] == 12.0
    assert result.state.authority_class is AuthorityClass.FIXTURE_ONLY
    assert result.state.support_class is SupportClass.FIXTURE_ONLY
    assert "fixture-source" in result.provenance["source_refs"]
    assert query.state_at(history_id=HISTORY, branch_id=BRANCH, domain="fauna",
                          time_key=TIME.time_key, cell_id="cell-1").status == "UNKNOWN"
    assert query.state_at(history_id=HISTORY, branch_id=BRANCH, domain="marine_ecology",
                          time_key=TIME.time_key, cell_id="cell-1").status == "NOT_APPLICABLE"
    assert query.state_at(history_id=HISTORY, branch_id=BRANCH, domain="absent",
                          time_key=TIME.time_key, cell_id="cell-1").status == "MISSING_DOMAIN"
    assert query.state_at(history_id=HISTORY, branch_id=BRANCH, domain="climate",
                          time_key="fixture:missing", cell_id="cell-1").status == "MISSING_TIMESTAMP"
    assert [s.branch_id for s in store.find_states(history_id=HISTORY, branch_id=BRANCH,
                                                    domain="climate")] == [BRANCH]


def test_query_returns_conflict_instead_of_arbitrary_candidate(tmp_path):
    store = HistoryStore(tmp_path / "conflict")
    store.append_state(make_state(domain="climate", value={"temperature_c": 1.0}))
    store.append_state(make_state(domain="climate", value={"temperature_c": 2.0}))
    result = HistoryQueryService(store).state_at(
        history_id=HISTORY, branch_id=BRANCH, domain="climate",
        time_key=TIME.time_key, cell_id="cell-1",
    )
    assert result.status == "CONFLICT"
    assert len(result.provenance["candidate_state_ids"]) == 2


def test_climate_provider_adapter_validates_semantics_and_persists_binding(tmp_path):
    result = climate_binding()
    store = HistoryStore(tmp_path / "provider")
    result.persist(store)
    assert store.read_provider_binding(str(result.binding_id))["provider_id"] == "fixture-climate-provider"
    assert store.read_state(str(result.state.state_id)) == result.state
    assert result.state.support_class is SupportClass.FIXTURE_ONLY
    assert result.state.authority_class is AuthorityClass.FIXTURE_ONLY
    with pytest.raises(ValueError, match="unit mismatch"):
        ClimateProviderAdapter().bind(
            history_id=HISTORY, branch_id=BRANCH, provider_id="fixture",
            source_sha256="a" * 64, source_semantics="fixture",
            time_key=TIME.time_key, coordinate_system=TIME.coordinate_system,
            grid_id="grid", cell_ids=("cell-1",),
            variable_metadata={"temperature_c": {"units": "K", "dimensions": ["time"],
                                                   "temporal_semantics": "instant"}},
            values={"temperature_c": 2.0}, required_units={"temperature_c": "degC"},
        )
    with pytest.raises(ValueError, match="authority refs and applicability"):
        ClimateProviderAdapter().bind(
            history_id=HISTORY, branch_id=BRANCH, provider_id="unverified-real-source",
            source_sha256="b" * 64, source_semantics="unadjudicated",
            time_key=TIME.time_key, coordinate_system=TIME.coordinate_system,
            grid_id="grid", cell_ids=("cell-1",),
            variable_metadata={"temperature_c": {"units": "degC", "dimensions": ["time"],
                                                   "temporal_semantics": "instant"}},
            values={"temperature_c": 2.0}, required_units={"temperature_c": "degC"},
            authority_class=AuthorityClass.DIRECT_AUTHORITY,
        )


def test_climate_governed_binding_requires_and_records_authority():
    result = ClimateProviderAdapter().bind(
        history_id=HISTORY, branch_id=BRANCH, provider_id="bounded-provider",
        source_sha256="c" * 64, source_semantics="governed annual variable",
        time_key=TIME.time_key, coordinate_system=TIME.coordinate_system,
        grid_id=SPACE.grid_id, cell_ids=SPACE.cell_ids,
        variable_metadata={"temperature_c": {"source_variable": "tas", "units": "degC",
                                               "dimensions": ["time", "cell"],
                                               "temporal_semantics": "annual_snapshot"}},
        values={"temperature_c": [10.0]}, required_units={"temperature_c": "degC"},
        authority_class=AuthorityClass.SPARSE_AUTHORITY,
        support_class=SupportClass.SPARSE_AUTHORITY,
        authority_refs=("adjudication:bounded-proof",),
        applicability={"time_key": TIME.time_key, "cell_ids": ["cell-1"]})
    assert result.state.authority_class is AuthorityClass.SPARSE_AUTHORITY
    assert "adjudication:bounded-proof" in result.binding_record["authority_refs"]


def test_hydrology_adapter_fixture_normalization_and_unknown_propagation():
    climate = climate_binding().state
    geography = make_state(domain="geography", value={"land": True})
    shoreline = make_state(domain="shoreline", value={"applicable": True})
    adapter = HydrologyAdapterV0()
    state, provenance = adapter.normalize_fixture(
        climate=climate, geography=geography, shoreline=shoreline,
        output_values={"annual_runoff": [3.0]}, output_units={"annual_runoff": "mm/year"},
    )
    assert state.domain == "hydrology"
    assert state.support_class is SupportClass.FIXTURE_ONLY
    assert state.authority_class is AuthorityClass.FIXTURE_ONLY
    assert state.value["units"]["annual_runoff"] == "mm/year"
    assert provenance.attributes["scientific_execution"] is False
    unknown_shore = make_state(domain="shoreline", support=SupportClass.UNKNOWN,
                               authority=AuthorityClass.NONE, value=None)
    unknown, _ = adapter.normalize_fixture(
        climate=climate, geography=geography, shoreline=unknown_shore,
        output_values={"annual_runoff": [3.0]}, output_units={"annual_runoff": "mm/year"},
    )
    assert unknown.support_class is SupportClass.UNKNOWN and unknown.value is None
    wrong_grid = make_state(domain="shoreline", value={"x": 1},
                            spatial=SpatialSupport("other-grid", ("cell-1",)))
    with pytest.raises(HydrologyAdapterError, match="align exactly"):
        adapter.normalize_fixture(climate=climate, geography=geography, shoreline=wrong_grid,
                                  output_values={"x": [1]}, output_units={"x": "unit"})


def test_hydrology_adapter_binds_only_preexisting_governed_result():
    inputs = []
    for domain in ("climate", "geography", "shoreline"):
        inputs.append(make_state(domain=domain, support=SupportClass.SPARSE_AUTHORITY,
                                 authority=AuthorityClass.SPARSE_AUTHORITY,
                                 value={"variables": {"tas": [1.0]}}))
    state, provenance = HydrologyAdapterV0().bind_governed_result(
        climate=inputs[0], geography=inputs[1], shoreline=inputs[2],
        result_values={"annual_runoff": [2.0]}, result_units={"annual_runoff": "mm year-1"},
        expected_units={"annual_runoff": "mm year-1"},
        result_sha256="d" * 64, authority_refs=("adjudication:bounded-result",),
        temporal_semantics="preexisting snapshot output")
    assert state.authority_class is AuthorityClass.DERIVED_AUTHORITY
    assert state.support_class is SupportClass.DERIVED_SUPPORTED
    assert provenance.attributes["scientific_execution"] is False
    assert state.payload_ref == "sha256:" + "d" * 64
    with pytest.raises(HydrologyAdapterError, match="units do not match"):
        HydrologyAdapterV0().bind_governed_result(
            climate=inputs[0], geography=inputs[1], shoreline=inputs[2],
            result_values={"annual_runoff": [2.0]}, result_units={"annual_runoff": "mm"},
            expected_units={"annual_runoff": "mm year-1"}, result_sha256="d" * 64,
            authority_refs=("adjudication:bounded-result",), temporal_semantics="snapshot")


def test_provenance_graph_explains_state_back_to_provider_source(tmp_path):
    store = HistoryStore(tmp_path / "prov")
    climate_prov = ProvenanceRecord.create(activity="provider-bind",
                                           source_refs=("provider:fixture-id", "sha256:abc"))
    hydro_prov = ProvenanceRecord.create(activity="hydrology-adapter",
                                         parent_provenance_ids=(str(climate_prov.record_id),),
                                         source_refs=("R5_17_B6_D3_CANONICAL_PALEOHYDROLOGY_REPLAY.json",))
    state = make_state(domain="hydrology", provenance=(str(hydro_prov.record_id),))
    store.append_provenance(climate_prov)
    store.append_provenance(hydro_prov)
    trace = store.trace_provenance(state)
    assert [r["activity"] for r in trace["provenance_records"]] == ["hydrology-adapter", "provider-bind"]
    assert "provider:fixture-id" in trace["source_refs"]


def test_dangling_provenance_fails_loudly(tmp_path):
    store = HistoryStore(tmp_path / "dangling")
    state = make_state(domain="climate", provenance=("missing_provenance_record",))
    with pytest.raises(ProvenanceIntegrityError, match="missing provenance"):
        store.trace_provenance(state)
