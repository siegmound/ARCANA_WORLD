from __future__ import annotations

from pathlib import Path

import pytest

from arcana_worldsim.r6.functional_development import (
    NodeMaterial,
    T0_TO_T1_SECONDS,
    _explicit_thermal_update,
    evolve_fixed_geometry_thermal_profile,
    initial_reduced_state,
    materialize_admitted_continental_t0,
    pure_shear_thermal_step,
    select_pair_13_interior_segment,
    state_from_payload,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def t0_profile():
    return materialize_admitted_continental_t0(ROOT)[0]


def test_real_support_binding_materializes_finite_t0_profile(t0_profile):
    assert t0_profile.support_id.startswith("R6G1D-R")
    assert t0_profile.support_class.startswith("CONTINENTAL_")
    assert len(t0_profile.z_m) == len(t0_profile.temperature_k) == len(t0_profile.materials)
    assert all(value > 0 for value in t0_profile.temperature_k)
    assert t0_profile.z_m[0] == 0.0
    assert t0_profile.z_m[-1] == t0_profile.model_base_m
    assert t0_profile.provenance["canonical_state"] is False
    assert "NOT_B6N8R_EXECUTION_ROSTER" in t0_profile.provenance["scenario_roster_status"]


def test_t0_profile_retains_moho_phase_boundary_without_discrete_interpolation(t0_profile):
    idx = t0_profile.z_m.index(t0_profile.crust_m)
    crust, mantle = t0_profile.provenance["piecewise_profile_coefficients"]
    z0, h, c2c, c1c, c0c = crust
    zm, _, c2m, c1m, c0m = mantle
    crust_limit = (c2c * (h-z0) + c1c) * (h-z0) + c0c
    mantle_limit = c0m
    q_crust = t0_profile.materials[idx].k_w_m_k * (2*c2c*(h-z0)+c1c)
    q_mantle = t0_profile.materials[idx+1].k_w_m_k * c1m
    assert t0_profile.materials[idx].role_id == "CONTINENTAL_CRUST_REFERENCE"
    assert t0_profile.materials[idx + 1].role_id == "LITHOSPHERIC_MANTLE_REFERENCE"
    assert crust_limit == pytest.approx(mantle_limit, abs=1e-9)
    assert crust_limit == pytest.approx(t0_profile.provenance["moho_temperature_k"], abs=1e-9)
    assert q_crust == pytest.approx(q_mantle, abs=1e-9)
    assert q_crust == pytest.approx(t0_profile.provenance["moho_heat_flux_w_m2"], abs=1e-9)
    assert len({m.role_id for m in t0_profile.materials}) == 2


def test_t0_to_t1_reference_thermal_evolution_integrates_finite_duration(t0_profile):
    temperatures, diagnostic = evolve_fixed_geometry_thermal_profile(
        t0_profile, duration_s=T0_TO_T1_SECONDS,
    )
    assert diagnostic.duration_s == T0_TO_T1_SECONDS
    assert diagnostic.substeps >= 1
    assert diagnostic.max_stability_ratio <= 0.8
    assert temperatures[0] == t0_profile.surface_temperature_k
    assert temperatures[-1] == t0_profile.base_temperature_k
    assert temperatures != t0_profile.temperature_k
    assert all(value > 0 for value in temperatures)


def test_fixed_geometry_thermal_integrator_dt_refinement_is_deterministic(t0_profile):
    coarse = evolve_fixed_geometry_thermal_profile(
        t0_profile, duration_s=T0_TO_T1_SECONDS,
        maximum_substep_s=T0_TO_T1_SECONDS,
    )[0]
    medium = evolve_fixed_geometry_thermal_profile(
        t0_profile, duration_s=T0_TO_T1_SECONDS,
        maximum_substep_s=T0_TO_T1_SECONDS / 2,
    )[0]
    fine = evolve_fixed_geometry_thermal_profile(
        t0_profile, duration_s=T0_TO_T1_SECONDS,
        maximum_substep_s=T0_TO_T1_SECONDS / 4,
    )[0]
    repeat = evolve_fixed_geometry_thermal_profile(
        t0_profile, duration_s=T0_TO_T1_SECONDS,
        maximum_substep_s=T0_TO_T1_SECONDS / 4,
    )[0]
    err_coarse = max(abs(a-b) for a, b in zip(coarse, fine))
    err_medium = max(abs(a-b) for a, b in zip(medium, fine))
    assert err_medium <= err_coarse + 1e-10
    assert repeat == fine


def test_manufactured_linear_temperature_profile_is_steady_without_source():
    z = (0.0, 1.0, 2.5, 4.0, 7.0, 10.0)
    material = NodeMaterial("TEST_NUMERICAL_HOMOGENEOUS", 3.0, 3300.0, 1200.0, 0.0)
    materials = (material,) * len(z)
    initial = tuple(300.0 + 0.25 * value for value in z)
    evolved = _explicit_thermal_update(
        initial, z, materials, 1.0e5, initial[0], initial[-1],
    )
    assert evolved == pytest.approx(initial, abs=1e-12)


def test_pure_shear_extension_thins_layers_and_conserves_area(t0_profile):
    state = initial_reduced_state(t0_profile, initial_width_m=100_000.0)
    evolved, diagnostics = pure_shear_thermal_step(
        state, duration_s=1.0e10, extension_velocity_m_s=1.0e-9,
    )
    assert evolved.beta > 1.0
    assert evolved.crust_m < state.crust_m
    assert evolved.lithosphere_m < state.lithosphere_m
    assert evolved.accumulated_strain > 0
    assert diagnostics.area_relative_error < 2e-14
    assert diagnostics.max_stability_ratio <= 0.8


def test_zero_forcing_keeps_geometry_and_thermal_term_advances(t0_profile):
    state = initial_reduced_state(t0_profile, initial_width_m=100_000.0)
    evolved, _ = pure_shear_thermal_step(
        state, duration_s=1.0e9, extension_velocity_m_s=0.0,
    )
    assert evolved.beta == 1.0
    assert evolved.width_m == state.width_m
    assert evolved.crust_m == state.crust_m
    assert evolved.lithosphere_m == state.lithosphere_m
    assert evolved.temperature_k != state.temperature_k


def test_compression_is_explicitly_rejected_by_extension_only_v0(t0_profile):
    state = initial_reduced_state(t0_profile, initial_width_m=100_000.0)
    with pytest.raises(ValueError, match="COMPRESSION_NOT_ADMISSIBLE"):
        pure_shear_thermal_step(state, duration_s=1.0e6, extension_velocity_m_s=-1e-9)


def test_checkpoint_roundtrip_and_repeat_step_are_byte_stable(t0_profile):
    initial = initial_reduced_state(t0_profile, initial_width_m=100_000.0)
    checkpoint = state_from_payload(initial.payload())
    assert checkpoint.payload() == initial.payload()
    first, _ = pure_shear_thermal_step(initial, duration_s=1.0e9, extension_velocity_m_s=0)
    second, _ = pure_shear_thermal_step(checkpoint, duration_s=1.0e9, extension_velocity_m_s=0)
    assert first.payload() == second.payload()


def test_pair_13_section_fails_closed_when_admitted_two_sided_mapping_is_absent():
    report = select_pair_13_interior_segment(ROOT)
    assert report["plate_pair"] == [1, 3]
    assert report["physical_section_selected"] is False
    assert report["endpoint_degrees"] == [2, 2]
    assert len(report["adjacent_supports"]) == 2
    assert all(not side["B6N8N_admitted"] for side in report["adjacent_supports"])
    assert all(side["plate_membership"] == "UNKNOWN_NOT_IN_T0_FIELD_PACKAGE"
               for side in report["adjacent_supports"])
    assert report["rift_step_executed"] is False
