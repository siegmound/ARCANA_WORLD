from __future__ import annotations

import json
from pathlib import Path

from arcana_worldsim.r6.physical_domain_t0 import bind_physical_t0
from arcana_worldsim.r6.planning import (
    Availability, BindingStatus, DOMAIN_REGISTRY_SERVICE,
)
from arcana_worldsim.r6.query import HistoryQueryService
from arcana_worldsim.r6.store import HistoryStore

ROOT = Path(__file__).parents[1]


def test_t0_binding_roundtrip_global_query_lineage_and_resolution(tmp_path):
    store_root = tmp_path / "physical-history"
    report = bind_physical_t0(ROOT, store_root)
    binding = report["history_binding"]
    store = HistoryStore(store_root)
    query = HistoryQueryService(store)

    found = query.state_at(history_id=binding["history_id"],
        branch_id=binding["branch_id"], domain="physical_world", time_key="210 Ma")
    assert found.status == "FOUND"
    state = found.state
    assert str(state.state_id) == binding["state_id"]
    assert state.authority_class.value == "DERIVED_AUTHORITY"
    assert state.model_derived is True
    assert found.provenance["source_refs"]
    assert state.uncertainty["kinematics_ensemble_size"] == 1
    assert "bathymetry" in state.value["unknown_fields"]
    assert state.applicability["forward_evolution"] is False

    lineage = query.lineage(str(state.state_id))
    assert lineage["missing_parent_state_ids"] == []
    assert len(lineage["state_lineage"]) == 1
    resolution = query.available_resolution(history_id=binding["history_id"],
        branch_id=binding["branch_id"], domain="physical_world", time_key="210 Ma")
    assert resolution["status"] == "AVAILABLE"
    assert resolution["native_resolutions"] == [
        "1-degree nominal parent grid; vector edges COARSE_SUPPORT_ON_FINE_GRID"]
    assert resolution["interpolation_performed"] is False
    assert {row["role"] for row in store.temporal_records()} == {
        "AUTHORITY_ANCHOR", "HISTORICAL_SNAPSHOT", "REFINEMENT_ANCHOR"}


def test_binding_reconciles_lineage_requirements_and_domain_registry(tmp_path):
    report = bind_physical_t0(ROOT, tmp_path / "physical-history")
    assert report["decision"] == "R6_PHYSICAL_DOMAIN_T0_BOUND__FIRST_INTERVAL_BLOCKED"
    assert all(report["authority_validation"].values())
    rows = {row["id"]: row for row in report["p01_p12"]}
    assert rows["P10"]["status"] == "CURRENT_CENSUS_COMPLETE"
    assert rows["P10"]["authority"] == "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json"
    assert rows["P05"]["required_before_first_finite_interval"] is False
    assert rows["P09"]["required_before_later_topology_event_only"] is True
    lineage = {row["artifact"]: row for row in report["authority_lineage"]}
    assert lineage["R6_T0_EVENT_ELIGIBILITY_CENSUS.json"]["classification"] == "HISTORICAL_SUPERSEDED"
    assert lineage["R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json"]["supersedes"] == [
        "R6_T0_EVENT_ELIGIBILITY_CENSUS.json"]
    assert report["history_binding"]["state_at_t0_query_status"] == "FOUND"
    assert report["history_binding"]["registry_entry"]["forward_execution_authorized"] is False
    physical = DOMAIN_REGISTRY_SERVICE.get("physical_world")
    assert physical.history_availability is Availability.CANONICAL_T0_BOUND
    assert physical.engine_binding_status is BindingStatus.T0_BOUND_FORWARD_BLOCKED
    assert physical.forward_execution_authorized is False


def test_report_json_contract_if_generated():
    report_path = ROOT / "R6_PHYSICAL_DOMAIN_T0_BINDING_REPORT.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["canonical_payload_changed"] is False
        assert report["scientific_execution"] is False
