from __future__ import annotations

import copy
from pathlib import Path

import pytest

from r6_int2a_historical_query import load_sources
from r6_int2b_history_adapter import (
    AdapterError, DOMAIN, build_observation_records, exact_time_key,
    probe_hardlink_capability, query_and_measure,
)
from arcana_worldsim.r6.functional_development import state_from_payload
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.query import HistoryQueryService
from arcana_worldsim.r6.state import DomainStateEnvelope
from arcana_worldsim.r6.store import HistoryStore


ROOT = Path(__file__).resolve().parents[1]
R4 = ROOT / "outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04"
INT1D = ROOT / "outputs/r6_functional_development/INT1D_TF2B_5_11_R094C025_C026_20261014_02"


@pytest.fixture(scope="module")
def sources():
    return load_sources(R4, INT1D)


def test_verified_observations_map_to_distinct_noncanonical_b0_identities(sources):
    records, summary = build_observation_records(sources)
    states = [record for record in records if isinstance(record, DomainStateEnvelope)]
    provenances = [record for record in records if isinstance(record, ProvenanceRecord)]
    assert len(states) == 26
    assert len(provenances) == 2
    assert summary["R4"]["history_id"] != summary["INT1D"]["history_id"]
    assert summary["R4"]["branch_id"] != summary["INT1D"]["branch_id"]
    assert {state.authority_class.value for state in states} == {"NONE"}
    assert {state.support_class.value for state in states} == {"DERIVED_SUPPORTED"}
    assert all(state.applicability["canonical_publication"] is False for state in states)
    assert all(state.domain == DOMAIN and state.model_derived for state in states)
    assert len({state.state_id for state in states}) == 26


def test_observed_time_keys_preserve_round_trip_and_reject_invalid_values():
    exact = 129.57192262500018
    key = exact_time_key(exact)
    assert float(key.split(":", 1)[1]) == exact
    for invalid in (True, float("nan"), float("inf"), -0.1, "200"):
        with pytest.raises(AdapterError):
            exact_time_key(invalid)


def test_interpolated_rows_and_identity_mismatches_fail_closed(sources):
    modified = copy.deepcopy(sources)
    rows = modified["R4"]["rows"]
    rows["R6G1D-R091-C029"][1]["record_type"] = "DIAGNOSTIC_RECONSTRUCTION"
    with pytest.raises(AdapterError, match="NON_OBSERVED_OR_RECONSTRUCTED"):
        build_observation_records(modified)


def test_mismatched_support_and_experiment_identity_fail_closed(sources):
    modified = copy.deepcopy(sources)
    modified["INT1D"]["experiment"] = "R4"
    with pytest.raises(AdapterError, match="SOURCE_EXPERIMENT_IDENTITY_MISMATCH"):
        build_observation_records(modified)


def test_candidate_checkpoint_payloads_deserialize_but_are_not_replay_authority(sources):
    for key in ("R4", "INT1D"):
        checkpoint = sources[key]["documents"]["CANDIDATE_CHECKPOINT.json"]
        assert len(checkpoint["candidate_states"]) == 2
        for payload in checkpoint["candidate_states"]:
            state = state_from_payload(payload)
            assert len(state.material_coordinate) == len(state.temperature_k) == len(state.materials)


def test_real_filesystem_probe_cleans_only_its_probe_files(tmp_path):
    supported, reason = probe_hardlink_capability(tmp_path)
    assert isinstance(supported, bool)
    assert (reason is None) is supported
    assert list(tmp_path.iterdir()) == []


def test_b0_store_registration_queries_provenance_and_semantics_when_supported(tmp_path, sources):
    supported, reason = probe_hardlink_capability(tmp_path)
    if not supported:
        pytest.skip(f"B0 atomic hard-link publication unavailable: {reason}")
    records, summary = build_observation_records(sources)
    store = HistoryStore(tmp_path / "isolated-b0-store")
    store.append_transaction(records)
    metric = query_and_measure(store, records, sources, summary)
    assert metric["readback_state_count"] == 26
    assert metric["store_file_count"] > 26
    assert metric["store_bytes"] > 0
    first_source = sources["R4"]
    binding = summary["R4"]
    support = first_source["supports"][0]
    sample = first_source["rows"][support][0]
    query = HistoryQueryService(store).state_at(
        history_id=binding["history_id"], branch_id=binding["branch_id"], domain=DOMAIN,
        time_key=exact_time_key(sample["elapsed_years"]), cell_id=support)
    assert query.status == "FOUND"
    assert query.state.value["record_type"] in {"DIAGNOSTIC_SAMPLE", "ENDPOINT_STATE"}
    assert len(query.provenance["provenance_records"]) == 1
