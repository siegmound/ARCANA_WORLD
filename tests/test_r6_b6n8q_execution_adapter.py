from __future__ import annotations

import ast
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from arcana_worldsim.r6 import pre_orbdata_t0_initializer as provider
from arcana_worldsim.r6.b6n8q_execution_adapter import (
    AdapterError,
    ExecutionAuthorization,
    ExecutionMode,
    EXPECTED_ADMITTED_SUPPORT_MEMBERSHIP_SHA,
    EXPECTED_O_SOURCE,
    EXPECTED_P_CANDIDATE_CONTRACT_ID,
    EXPECTED_P_RUN_CONTRACT_ID,
    ScenarioEntry,
    ScenarioRoster,
    canonical_text_sha256,
    candidate_identity,
    metadata_preflight,
    request_real_execution,
    run_synthetic_candidates,
    validate_candidate_set,
    validate_roster,
    verify_authority,
    verify_authority_hashes,
)
from arcana_worldsim.r6.pre_orbdata_heat_flow import HWR2


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "docs/arcana/research/B6N8N_PROPERTY_TUPLE_BINDING_REGISTRY.json").read_text(encoding="utf-8"))


def _fixture(kind: str) -> provider.SyntheticColumnFixture:
    ocean = kind == "ocean"
    crust_role = "OCEANIC_CRUST_REFERENCE" if ocean else "CONTINENTAL_CRUST_REFERENCE"
    crust = provider.role_binding_from_registry(REGISTRY, crust_role)
    mantle = provider.role_binding_from_registry(REGISTRY, "LITHOSPHERIC_MANTLE_REFERENCE")
    hwr = HWR2()
    age = 70.0 if ocean else None
    scenario = "HWR2_POSITIVE_AGE_BOUNDARY_V1" if ocean else "CONTINENTAL_AUTHORED_Q_AND_T0_REFERENCE_V1"
    binding = provider.ColumnBinding(
        support_id=f"TEST_Q_{'OCEANIC' if ocean else 'CONTINENTAL'}_001",
        support_class="OCEAN_POSITIVE_AGE_ADMITTED" if ocean else "CONTINENTAL_NORMAL",
        geometry_reference="SYNTHETIC_FIXTURE_GEOMETRY",
        surface_datum="LOCAL_MODEL_SURFACE_Z0",
        crust_depth_m=6500.0 if ocean else 35000.0,
        model_base_depth_m=hwr.zp_m if ocean else 100000.0,
        model_base_semantics="HWR_FINITE_PLATE_BASE_NOT_PHYSICAL_LAB" if ocean else "AUTHORED_TOTAL_THERMAL_THICKNESS_NOT_PHYSICAL_LAB",
        physical_lab_depth_m=None,
        material_role_sequence=(crust_role, "LITHOSPHERIC_MANTLE_REFERENCE"),
        crust=crust,
        mantle=mantle,
        t0_world_age_ma=210.0,
        surface_temperature_k=hwr.t0_k,
        surface_heat_flow_w_m2=hwr.flux(age) if ocean else 0.060,
        physical_ocean_age_ma=age,
        hwr_model=hwr,
        gravity_m_s2=9.82,
        initializer_family=provider.INITIALIZER_FAMILY,
        boundary_scenario_id=scenario,
        configuration_identities={"fixture_config_sha256": "a" * 64},
        support_lineage={"fixture": "NON_CANONICAL_TEST_ONLY"},
        uncertainty={"kind": "TEST_RANGE_ONLY", "probability_distribution": False},
        binding_status="EXACTLY_ONE_INITIALIZER_BINDING",
        units={"depth": "m", "temperature": "K", "heat_flow": "W m-2",
               "conductivity": "W m-1 K-1", "density": "kg m-3",
               "heat_capacity": "J kg-1 K-1", "diffusivity": "m2 s-1",
               "radiogenic_source": "W m-3", "age": "Ma", "gravity": "m s-2",
               "thermal_expansion": "K-1"},
    )
    return provider.SyntheticColumnFixture(True, "NON_CANONICAL_B6N8Q_FIXTURE", binding)


def _roster(fixture: provider.SyntheticColumnFixture, *, qualified=True) -> ScenarioRoster:
    entry = ScenarioEntry(fixture.binding.boundary_scenario_id, "a" * 64,
                          fixture.binding.boundary_scenario_id,
                          (fixture.binding.support_id,))
    return ScenarioRoster("TEST_ROSTER_Q", "TEST_ONLY", (entry,), "b" * 64,
                          qualified, "QUALIFIED" if qualified else "UNQUALIFIED", True)


def _auth(mode: ExecutionMode, *, roster: ScenarioRoster | None = None,
          root: Path | None = None, support_sha=EXPECTED_ADMITTED_SUPPORT_MEMBERSHIP_SHA):
    return ExecutionAuthorization(
        EXPECTED_P_RUN_CONTRACT_ID, EXPECTED_O_SOURCE, support_sha,
        EXPECTED_P_CANDIDATE_CONTRACT_ID,
        roster.identity_sha256 if roster else None,
        mode, str(root) if root else None,
        "CANDIDATE_ONLY_NO_CANONICAL_PUBLICATION", False,
    )


def test_p_o_authorities_and_all_input_hashes_are_revalidated():
    verified = verify_authority(ROOT)
    assert verified["p_source_commit"] == "f79ccef337a72152bdbf13369d01960f3df8cb2d"
    assert verified["o_source_commit"] == EXPECTED_O_SOURCE
    assert verified["authority_snapshot_count"] == 16
    assert verified["p_decision"] == "BLOCKED_B6N8P_EXECUTION_CONFIGURATION_INCOMPLETE"
    assert verified["real_t0_execution_ready"] is False


def test_metadata_preflight_plans_all_real_support_without_evaluator_or_writes(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("real support numerical evaluation is forbidden in Q preflight")

    monkeypatch.setattr(provider, "continental_column", forbidden)
    monkeypatch.setattr(provider, "ocean_column", forbidden)
    monkeypatch.setattr(provider, "evaluate_synthetic_fixture", forbidden)
    preflight, plans = metadata_preflight(ROOT, authorization=_auth(ExecutionMode.METADATA_PREFLIGHT))
    assert (preflight.native_support_count, preflight.admitted_count) == (64800, 63620)
    assert (preflight.continental_count, preflight.positive_age_ocean_count) == (14258, 49362)
    assert (preflight.unresolved_positive_age_ocean_excluded, preflight.zero_age_ridge_excluded) == (1072, 108)
    assert (preflight.admitted_unresolved, preflight.admitted_ambiguous) == (0, 0)
    assert len(plans) == preflight.support_plan_count == 63620
    assert preflight.scenario_roster_status == "REQUIRED_BUT_UNBOUND"
    assert not preflight.numerical_profile_evaluation and not preflight.candidate_output_write
    assert all(not plan.numerical_profile_evaluation and not plan.candidate_output_write for plan in plans)
    assert sum(plan.support_class.startswith("CONTINENTAL_") for plan in plans) == 14258
    assert sum(plan.support_class == "OCEAN_POSITIVE_AGE_ADMITTED" for plan in plans) == 49362


def test_metadata_authorization_fails_closed_on_scope_mismatch():
    bad = _auth(ExecutionMode.METADATA_PREFLIGHT, support_sha="0" * 64)
    with pytest.raises(AdapterError, match="EXECUTION_NOT_AUTHORIZED"):
        metadata_preflight(ROOT, authorization=bad)


@pytest.mark.parametrize("roster,code", [(None, "SCENARIO_ROSTER_REQUIRED"),
                                           ("unqualified", "SCENARIO_ROSTER_NOT_QUALIFIED")])
def test_real_execution_requires_external_roster_then_stays_unauthorized(roster, code):
    actual = None if roster is None else _roster(_fixture("continental"), qualified=False)
    with pytest.raises(AdapterError, match=code):
        request_real_execution(_auth(ExecutionMode.REAL_CANDIDATE_EXECUTION), actual)


def test_qualified_roster_still_cannot_authorize_real_execution():
    fixture = _fixture("continental")
    test_entry = _roster(fixture).entries[0]
    real_roster = ScenarioRoster(
        "UNBOUND_REAL_ROSTER_TEST_SHAPE", "TEST_AUTHORITY_SHAPE_ONLY",
        (replace(test_entry, support_ids=("R6G1D-R000-C000",)),),
        "b" * 64, True, "QUALIFIED", False,
    )
    with pytest.raises(AdapterError, match="EXECUTION_NOT_AUTHORIZED"):
        request_real_execution(_auth(ExecutionMode.REAL_CANDIDATE_EXECUTION), real_roster)


def test_test_roster_and_only_test_support_are_accepted():
    fixture = _fixture("continental")
    roster = _roster(fixture)
    validate_roster(roster, synthetic=True)
    assert roster.scenario_count == 1
    with pytest.raises(AdapterError, match="TEST_ROSTER_MARKER_REQUIRED"):
        validate_roster(replace(roster, non_canonical_test_roster=False), synthetic=True)


@pytest.mark.parametrize("excluded_class", ["UNRESOLVED_POSITIVE_AGE_OCEAN", "ZERO_AGE_RIDGE"])
def test_o_provider_rejects_excluded_support_classes(excluded_class):
    fixture = _fixture("continental")
    invalid = replace(fixture.binding, support_id="R6G1D-R000-C000", support_class=excluded_class)
    with pytest.raises(provider.InitializerError, match="UNAUTHORIZED_SUPPORT"):
        provider.build_initializer_plan(invalid)


def test_hashes_distinguish_checkout_bytes_from_canonical_text():
    lf = b"alpha\nbeta\n"
    crlf = b"alpha\r\nbeta\r\n"
    assert hashlib.sha256(lf).hexdigest() != hashlib.sha256(crlf).hexdigest()
    assert canonical_text_sha256(lf) == canonical_text_sha256(crlf)
    verify_authority_hashes("fixture.txt", crlf,
                            expected_file_sha256=hashlib.sha256(crlf).hexdigest(),
                            expected_canonical_text_sha256=canonical_text_sha256(lf))
    with pytest.raises(AdapterError, match="FILE_SHA256"):
        verify_authority_hashes("fixture.txt", crlf,
                                expected_file_sha256=hashlib.sha256(lf).hexdigest(),
                                expected_canonical_text_sha256=canonical_text_sha256(lf))
    with pytest.raises(AdapterError, match="CANONICAL_TEXT_SHA256"):
        verify_authority_hashes("fixture.txt", crlf,
                                expected_file_sha256=hashlib.sha256(crlf).hexdigest(),
                                expected_canonical_text_sha256="0" * 64)


def test_provider_metadata_plan_is_repeatable():
    fixture = _fixture("continental")
    first = provider.build_initializer_plan(fixture.binding)
    second = provider.build_initializer_plan(fixture.binding)
    assert first.plan_identity_sha256 == second.plan_identity_sha256


def test_candidate_identity_binds_every_semantic_key():
    base = dict(run_id="run", support_id="TEST_Q_X_1", scenario_id="scn",
                configuration_identity_sha256="a" * 64, time_ma=210.0,
                provider_source_commit=EXPECTED_O_SOURCE,
                output_contract_identity_sha256=EXPECTED_P_CANDIDATE_CONTRACT_ID)
    original = candidate_identity(**base)
    for field, value in (("run_id", "run2"), ("support_id", "TEST_Q_X_2"),
                         ("scenario_id", "scn2"), ("time_ma", 209.0),
                         ("provider_source_commit", "f" * 40),
                         ("configuration_identity_sha256", "c" * 64)):
        assert candidate_identity(**{**base, field: value}) != original


@pytest.mark.parametrize("kind", ["continental", "ocean"])
def test_synthetic_full_path_writes_valid_candidate_and_manifest(tmp_path, kind, monkeypatch):
    fixture = _fixture(kind)
    roster = _roster(fixture)
    import arcana_worldsim.r6.b6n8q_execution_adapter as adapter
    observed_states = []
    original_write_manifest = adapter._write_manifest

    def track_states(*args, **kwargs):
        observed_states.append(kwargs["status"])
        return original_write_manifest(*args, **kwargs)

    monkeypatch.setattr(adapter, "_write_manifest", track_states)
    manifest = run_synthetic_candidates(
        repository_root=ROOT,
        authorization=_auth(ExecutionMode.SYNTHETIC_TEST, roster=roster, root=tmp_path),
        roster=roster, fixtures=(fixture,), chunk_size=1,
    )
    assert manifest["status"] == "COMPLETE_CANDIDATE_SET"
    assert manifest["candidate_count"] == 1
    assert manifest["publication_status"] == "UNPUBLISHED_NO_CANONICAL_PUBLICATION"
    assert manifest["real_t0_execution_ready"] is False
    assert observed_states == ["PLANNED", "RUNNING", "VALIDATION_PENDING", "COMPLETE_CANDIDATE_SET"]
    assert len(list(tmp_path.rglob("*.json"))) == 2
    replayed = run_synthetic_candidates(
        repository_root=ROOT,
        authorization=_auth(ExecutionMode.SYNTHETIC_TEST, roster=roster, root=tmp_path),
        roster=roster, fixtures=(fixture,), chunk_size=9,
    )
    assert replayed["run_id"] == manifest["run_id"]
    assert replayed["candidate_ids"] == manifest["candidate_ids"]


def test_missing_roster_or_real_support_cannot_reach_evaluator(tmp_path, monkeypatch):
    fixture = _fixture("continental")
    auth = _auth(ExecutionMode.SYNTHETIC_TEST, root=tmp_path)
    monkeypatch.setattr(provider, "evaluate_synthetic_fixture",
                        lambda *a, **k: pytest.fail("must fail before evaluator"))
    with pytest.raises(AdapterError, match="SCENARIO_ROSTER_REQUIRED"):
        run_synthetic_candidates(repository_root=ROOT, authorization=auth,
                                 roster=None, fixtures=(fixture,))
    real = replace(fixture, binding=replace(fixture.binding, support_id="R6G1D-R000-C000"))
    roster = _roster(fixture)
    with pytest.raises(AdapterError, match="UNAUTHORIZED_SUPPORT"):
        run_synthetic_candidates(repository_root=ROOT,
                                 authorization=_auth(ExecutionMode.SYNTHETIC_TEST, roster=roster, root=tmp_path),
                                 roster=roster, fixtures=(real,))


def test_candidate_root_firewall_rejects_repository_and_history_paths(tmp_path):
    fixture = _fixture("continental")
    roster = _roster(fixture)
    for forbidden in (ROOT / "outputs" / "candidate", tmp_path / "WORLD_HISTORY" / "candidate"):
        with pytest.raises(AdapterError, match="EXECUTION_NOT_AUTHORIZED"):
            run_synthetic_candidates(repository_root=ROOT,
                                     authorization=_auth(ExecutionMode.SYNTHETIC_TEST, roster=roster, root=forbidden),
                                     roster=roster, fixtures=(fixture,))


def test_interruption_is_incomplete_and_same_identity_resumes(tmp_path):
    fixture = _fixture("continental")
    roster = _roster(fixture)
    auth = _auth(ExecutionMode.SYNTHETIC_TEST, roster=roster, root=tmp_path)
    with pytest.raises(AdapterError, match="INCOMPLETE_RUN"):
        run_synthetic_candidates(repository_root=ROOT, authorization=auth, roster=roster,
                                 fixtures=(fixture,), fail_after=1)
    manifest = next(tmp_path.rglob("RUN_MANIFEST.json"))
    assert json.loads(manifest.read_text())["status"] == "INCOMPLETE"
    resumed = run_synthetic_candidates(repository_root=ROOT, authorization=auth, roster=roster,
                                        fixtures=(fixture,))
    assert resumed["status"] == "COMPLETE_CANDIDATE_SET"
    assert resumed["candidate_count"] == 1


def test_cross_run_resume_and_corrupted_candidate_fail_closed(tmp_path):
    fixture = _fixture("continental")
    roster = _roster(fixture)
    auth = _auth(ExecutionMode.SYNTHETIC_TEST, roster=roster, root=tmp_path)
    manifest = run_synthetic_candidates(repository_root=ROOT, authorization=auth,
                                        roster=roster, fixtures=(fixture,))
    separate_run = run_synthetic_candidates(repository_root=ROOT,
                                             authorization=replace(auth, support_binding_identity_sha256="c" * 64),
                                             roster=roster, fixtures=(fixture,))
    assert separate_run["run_id"] != manifest["run_id"]
    candidate = tmp_path / manifest["run_id"] / f"{manifest['candidate_ids'][0]}.json"
    candidate.write_text("{}", encoding="utf-8")
    with pytest.raises(AdapterError, match="MANIFEST_MISMATCH"):
        run_synthetic_candidates(repository_root=ROOT, authorization=auth,
                                 roster=roster, fixtures=(fixture,))


def test_manifest_validator_rejects_duplicate_and_wrong_count(tmp_path):
    fixture = _fixture("continental")
    roster = _roster(fixture)
    from arcana_worldsim.r6.b6n8q_execution_adapter import CandidateRecord
    record = CandidateRecord("x", "r", fixture.binding.support_id,
                             roster.entries[0].scenario_id, "a" * 64, 210.0,
                             EXPECTED_O_SOURCE, EXPECTED_P_CANDIDATE_CONTRACT_ID,
                             "b" * 64, {"canonical_publication": False, "support_id": fixture.binding.support_id})
    with pytest.raises(AdapterError, match="INCOMPLETE_RUN"):
        validate_candidate_set((record,), expected_count=2, roster=roster)
    with pytest.raises(AdapterError, match="MANIFEST_MISMATCH"):
        validate_candidate_set((record, record), expected_count=2, roster=roster)


def test_adapter_has_no_world_history_or_canonical_writer_reachability():
    path = ROOT / "src/arcana_worldsim/r6/b6n8q_execution_adapter.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = {(node.module or "") for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    imports.update(alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
    assert not any("world_history" in item.lower() for item in imports)
    assert not any("checkpoint" in item.lower() or "history_store" in item.lower() for item in imports)
    source = path.read_text(encoding="utf-8")
    assert "HistoryStore" not in source and "WORLD_HISTORY_ROOT" not in source
    assert "canonical_publication" in source
