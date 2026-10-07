from __future__ import annotations

from dataclasses import replace
import hashlib
import ast
import json
from pathlib import Path

import pytest

from arcana_worldsim.r6.pre_orbdata_heat_flow import HWR2
from arcana_worldsim.r6.pre_orbdata_t0_initializer import (
    ColumnBinding,
    FailureCode,
    InitializerError,
    SyntheticColumnFixture,
    build_initializer_plan,
    evaluate_synthetic_fixture,
    preflight_admitted_bindings,
    role_binding_from_registry,
    validate_column_binding,
    validate_initializer_result,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads(
    (ROOT / "docs/arcana/research/B6N8N_PROPERTY_TUPLE_BINDING_REGISTRY.json").read_text(
        encoding="utf-8"
    )
)


def _fixture(support_class: str) -> SyntheticColumnFixture:
    ocean = support_class == "OCEAN_POSITIVE_AGE_ADMITTED"
    crust_role = "OCEANIC_CRUST_REFERENCE" if ocean else "CONTINENTAL_CRUST_REFERENCE"
    crust = role_binding_from_registry(REGISTRY, crust_role)
    mantle = role_binding_from_registry(REGISTRY, "LITHOSPHERIC_MANTLE_REFERENCE")
    model = HWR2()
    age = 70.0 if ocean else None
    q = model.flux(age) if ocean else 0.060
    binding = ColumnBinding(
        support_id="TEST_OCEAN_COLUMN" if ocean else "TEST_CONTINENT_COLUMN",
        support_class=support_class,
        geometry_reference="SYNTHETIC_FIXTURE_GEOMETRY",
        surface_datum="LOCAL_MODEL_SURFACE_Z0",
        crust_depth_m=6500.0 if ocean else 35000.0,
        model_base_depth_m=model.zp_m if ocean else 100000.0,
        model_base_semantics=(
            "HWR_FINITE_PLATE_BASE_NOT_PHYSICAL_LAB" if ocean
            else "AUTHORED_TOTAL_THERMAL_THICKNESS_NOT_PHYSICAL_LAB"
        ),
        physical_lab_depth_m=None,
        material_role_sequence=(crust_role, "LITHOSPHERIC_MANTLE_REFERENCE"),
        crust=crust,
        mantle=mantle,
        t0_world_age_ma=210.0,
        surface_temperature_k=model.t0_k,
        surface_heat_flow_w_m2=q,
        physical_ocean_age_ma=age,
        hwr_model=model,
        gravity_m_s2=9.82,
        initializer_family="R6_PRE_ORBDATA_TRANSIENT_THERMAL_COUPLING",
        boundary_scenario_id=(
            "HWR2_POSITIVE_AGE_BOUNDARY_V1" if ocean
            else "CONTINENTAL_AUTHORED_Q_AND_T0_REFERENCE_V1"
        ),
        configuration_identities={"fixture_config_sha256": "a" * 64},
        support_lineage={"fixture": "NON_CANONICAL_TEST_ONLY"},
        uncertainty={"kind": "TEST_RANGE_ONLY", "probability_distribution": False},
        binding_status="EXACTLY_ONE_INITIALIZER_BINDING",
        units={
            "depth": "m", "temperature": "K", "heat_flow": "W m-2",
            "conductivity": "W m-1 K-1", "density": "kg m-3",
            "heat_capacity": "J kg-1 K-1", "diffusivity": "m2 s-1",
            "radiogenic_source": "W m-3", "age": "Ma", "gravity": "m s-2",
            "thermal_expansion": "K-1",
        },
    )
    return SyntheticColumnFixture(True, "NON_CANONICAL_TEST_FIXTURE", binding)


@pytest.mark.parametrize("support_class", [
    "CONTINENTAL_COLD_STABLE", "CONTINENTAL_NORMAL", "CONTINENTAL_HOT_EXTENDED",
    "OCEAN_POSITIVE_AGE_ADMITTED",
])
def test_synthetic_candidate_is_deterministic_and_hashes_serialized_bytes(support_class):
    fixture = _fixture(support_class)
    first = evaluate_synthetic_fixture(fixture)
    second = evaluate_synthetic_fixture(fixture)
    assert first.serialize() == second.serialize()
    assert first.result_sha256 == second.result_sha256
    assert hashlib.sha256(first.serialize()).hexdigest() == first.result_sha256
    validate_initializer_result(first)
    assert json.loads(first.serialize())["canonical_publication"] is False
    if support_class.startswith("CONTINENTAL"):
        assert first.effective_column_rate_k_s is not None
        assert first.effective_column_rate_k_s != 0.0
    else:
        assert first.effective_column_rate_k_s is None
    assert all(segment.z1_m > segment.z0_m for segment in first.segments)
    assert "NO_SELECTED_PRODUCTION_GRID" in json.loads(first.serialize())["vertical_coordinate"]["representation"]
    assert "T1" not in json.loads(first.serialize())
    assert "Buck" not in json.loads(first.serialize())


def test_continental_piecewise_profile_has_temperature_and_flux_continuity():
    result = evaluate_synthetic_fixture(_fixture("CONTINENTAL_NORMAL"))
    moho = result.crust_depth_m
    assert result.temperature_at(0.0) == 280.0
    assert result.temperature_at(moho - 1e-5) == pytest.approx(result.temperature_at(moho), abs=3e-7)
    assert result.flux_at(moho - 1e-5) == pytest.approx(result.flux_at(moho), abs=1e-7)
    assert result.temperature_at(result.thermal_lab_depth_m) == pytest.approx(
        result.thermal_lab_temperature_k, abs=1e-9
    )
    assert result.effective_column_rate_k_s != 0.0
    assert len(result.segments) == 2


def test_ocean_profile_uses_hwr_boundary_and_is_continuous_at_moho():
    result = evaluate_synthetic_fixture(_fixture("OCEAN_POSITIVE_AGE_ADMITTED"))
    moho = result.crust_depth_m
    assert result.surface_heat_flow_w_m2 == pytest.approx(HWR2().flux(70.0), abs=1e-12)
    assert result.temperature_at(moho - 1e-5) == pytest.approx(result.temperature_at(moho), abs=3e-7)
    assert result.flux_at(moho - 1e-5) == pytest.approx(result.flux_at(moho), abs=1e-7)
    assert result.temperature_at(result.thermal_lab_depth_m) == pytest.approx(
        result.thermal_lab_temperature_k, abs=1e-8
    )
    assert result.effective_column_rate_k_s is None


@pytest.mark.parametrize("property_name,value", [("k", 2.7), ("rho", 2850.0), ("cp", 1100.0), ("radiogenic_w_m3", 9.0e-7)])
def test_material_changes_affect_synthetic_profile_and_discrete_roles_are_not_blended(property_name, value):
    original = _fixture("CONTINENTAL_NORMAL")
    plan = build_initializer_plan(original.binding)
    new_material = replace(original.binding.crust.material, **{property_name: value})
    changed_crust = replace(original.binding.crust, material=new_material,
                            kappa_reference_m2_s=new_material.k / (new_material.rho * new_material.cp))
    changed = SyntheticColumnFixture(
        True, original.fixture_name, replace(original.binding, crust=changed_crust)
    )
    base_result = evaluate_synthetic_fixture(original)
    changed_result = evaluate_synthetic_fixture(changed)
    assert plan.binding.material_role_sequence == (
        "CONTINENTAL_CRUST_REFERENCE", "LITHOSPHERIC_MANTLE_REFERENCE"
    )
    assert base_result.layer_roles == changed_result.layer_roles
    assert base_result.temperature_at(20000.0) != changed_result.temperature_at(20000.0)


def test_registry_does_not_invent_crust_expansivity_and_binds_mantle_expansivity():
    crust = role_binding_from_registry(REGISTRY, "CONTINENTAL_CRUST_REFERENCE")
    mantle = role_binding_from_registry(REGISTRY, "LITHOSPHERIC_MANTLE_REFERENCE")
    assert crust.alpha_k_1 is None
    assert mantle.alpha_k_1 == REGISTRY["roles"]["LITHOSPHERIC_MANTLE_REFERENCE"]["properties"]["alpha"]["nominal"]


@pytest.mark.parametrize("mutator,code", [
    (lambda b: replace(b, crust_depth_m=0.0), FailureCode.INVALID_INPUT),
    (lambda b: replace(b, initializer_family="UNSELECTED_MODEL"), FailureCode.UNSUPPORTED_CONFIGURATION),
    (lambda b: replace(b, support_id="R6G1D-R001-C002"), FailureCode.UNAUTHORIZED_SUPPORT),
    (lambda b: replace(b, uncertainty={}), FailureCode.MISSING_BINDING),
    (lambda b: replace(b, gravity_m_s2=float("nan")), FailureCode.UNSUPPORTED_CONFIGURATION),
    (lambda b: replace(b, crust=replace(b.crust, kappa_reference_m2_s=1e-6)), FailureCode.MISSING_BINDING),
    (lambda b: replace(b, mantle=replace(b.mantle, alpha_k_1=None)), FailureCode.MISSING_BINDING),
])
def test_contract_rejects_invalid_geometry_identity_and_tuple(mutator, code):
    fixture = _fixture("CONTINENTAL_NORMAL")
    invalid = SyntheticColumnFixture(True, fixture.fixture_name, mutator(fixture.binding))
    with pytest.raises(InitializerError, match=code.value):
        evaluate_synthetic_fixture(invalid)


def test_role_binding_rejects_unbound_property_override():
    with pytest.raises(InitializerError, match=FailureCode.UNKNOWN_AUTHORITY.value):
        role_binding_from_registry(REGISTRY, "CONTINENTAL_CRUST_REFERENCE", overrides={"alpha": 3e-5})


def test_explicit_input_validator_does_not_generate_profile():
    binding = _fixture("CONTINENTAL_NORMAL").binding
    validate_column_binding(binding)


@pytest.mark.parametrize("mutator,code", [
    (lambda b: replace(b, physical_lab_depth_m=80000.0), FailureCode.UNSUPPORTED_CONFIGURATION),
    (lambda b: replace(b, t0_world_age_ma=209.0), FailureCode.UNSUPPORTED_CONFIGURATION),
    (lambda b: replace(b, support_class="ZERO_AGE_RIDGE"), FailureCode.UNAUTHORIZED_SUPPORT),
    (lambda b: replace(b, units={**b.units, "temperature": "C"}), FailureCode.INVALID_INPUT),
    (lambda b: replace(b, boundary_scenario_id="UNKNOWN"), FailureCode.UNSUPPORTED_CONFIGURATION),
])
def test_invalid_or_excluded_synthetic_binding_fails_closed(mutator, code):
    fixture = _fixture("CONTINENTAL_NORMAL")
    invalid = SyntheticColumnFixture(True, fixture.fixture_name, mutator(fixture.binding))
    with pytest.raises(InitializerError, match=code.value):
        evaluate_synthetic_fixture(invalid)


def test_production_preflight_validates_support_without_evaluating_profiles(monkeypatch):
    import arcana_worldsim.r6.pre_orbdata_t0_initializer as initializer

    def forbidden(*args, **kwargs):
        raise AssertionError("production profile evaluation is forbidden in preflight")

    monkeypatch.setattr(initializer, "continental_column", forbidden)
    monkeypatch.setattr(initializer, "ocean_column", forbidden)
    result = preflight_admitted_bindings(ROOT)
    assert (result.native_support_count, result.admitted_count) == (64800, 63620)
    assert (result.continental_count, result.positive_age_ocean_count) == (14258, 49362)
    assert (result.unresolved_positive_age_ocean_excluded, result.zero_age_ridge_excluded) == (1072, 108)
    assert (result.candidate_boundary_segments, result.adjacent_oceanic_cells) == (634, 1075)
    assert result.ridge_overlap_cells == 3
    assert result.temperature_profiles_evaluated is False
    assert result.production_execution_authorized is False


def test_module_has_no_world_history_or_publication_dependency():
    path = ROOT / "src/arcana_worldsim/r6/pre_orbdata_t0_initializer.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = {
        alias.name.lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported.update(
        (node.module or "").lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )
    assert not any("world_history" in module for module in imported)
    assert not any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and ("publish" in node.name.lower() or "write" in node.name.lower())
        for node in ast.walk(tree)
    )
