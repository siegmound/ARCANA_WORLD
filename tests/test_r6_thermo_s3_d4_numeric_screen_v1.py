"""S3-D4 fail-closed source, chemistry, repeatability diagnostic tests.

All observations are synthetic. NO engine or S3 numerical-science PASS.
"""
import copy

import pytest

from experiments.r6_thermo_provider_pilot_v1.s3_d4_numeric_screen import (
    S3D4GateError, compare_readbacks, inspect_readback, load,
    validate_contract,
)


@pytest.fixture
def policy():
    return load()


@pytest.fixture
def mag():
    return {
        "provider": "MAGEMin_C.jl", "P": 10, "T": 1100,
        "phases": {"liq": 0.25, "opx": 0.75},
        "G_system": -100000.0, "rho_kg_m3": 2900.0,
        "max_native_component_delta": 1e-15,
        "max_source_component_delta": 1e-16,
        "bulk_res_norm": 1e-12,
        "status": "SOURCE_NATIVE_READBACK_ONLY__S3_SCIENCE_UNQUALIFIED",
    }


@pytest.fixture
def per():
    return {
        "provider": "Perple_X", "P": 4000, "T": 1050,
        "phases": {"Fsp(C1)": 70.0, "Augite(G)": 30.0},
        "printed_component_coverage": 10,
        "printed_oxide_molar_rounding_audit": {
            name: {"reconstructed_mol": "0", "reported_mol": "0"}
            for name in (
                "Na2O", "MgO", "Al2O3", "K2O", "CaO",
                "TiO2", "FeO", "O2", "H2O", "SiO2"
            )
        },
        "status": "PRINTED_RESOLUTION_READBACK_ONLY__S3_SCIENCE_UNQUALIFIED",
    }


def test_contract_pinned_and_not_authorized(policy):
    assert not policy["executable"]
    assert policy["engine_executions_authorized"] == 0
    assert policy["same_point_repeatability"]["numeric_phase_mass_fraction_abs_max"] is None
    assert policy["same_point_repeatability"]["numeric_gibbs_absolute_max"] is None
    assert policy["future_run_evidence"]["peak_rss_memory_bytes_budget"] is None
    assert policy["status_outcome"]["S3_executable_promotion"] == "BLOCKED"
    assert validate_contract(policy) == policy


@pytest.mark.parametrize(("path", "bad"), [
    (("schema",), "wrong"),
    (("state",), "SCIENTIFICALLY_RATIFIED"),
    (("executable",), True),
    (("run_allowed",), True),
    (("engine_executions_authorized",), 1),
    (("engine_executions_authorized",), True),
    (("authority", "D_024"), "INACTIVE"),
    (("authority", "physical_T1"), 210000000),
    (("authority", "mechanical_solve_authorized"), True),
    (("authority", "WORLD_HISTORY_PRODUCTION_AUTHORIZED"), True),
    (("authority", "arcana_original_materials_assigned"), 1),
    (("immutable_inputs", "candidate_git_blob"), "0" * 40),
    (("immutable_inputs", "source_risk_git_blob"), "0" * 40),
    (("immutable_inputs", "source_original_S2_manifest_sha256"), "unknown"),
    (("engineering_screen_only", "magemin_native_component_closure_abs_max"), 1e-3),
    (("engineering_screen_only", "mag_P_T_serialization_max_ulp"), 200),
    (("science_context", "not_numerical_threshold"), False),
    (("science_context", "Fsp_C1_structural_state"), "VALIDATED"),
    (("science_context", "full_50_cell_P_T_X_calibration"), "APPROVED"),
    (("same_point_repeatability", "numeric_phase_mass_fraction_abs_max"), 1e-6),
    (("same_point_repeatability", "numeric_gibbs_absolute_max"), 0.001),
    (("same_point_repeatability", "fresh_independent_processes_required"), False),
    (("same_point_repeatability", "no_missing_as_zero"), False),
    (("cross_point", "no_shared_cross_provider_comparison"), False),
    (("future_run_evidence", "pilot_authorized"), True),
    (("future_run_evidence", "full_grid_authorized"), True),
    (("future_run_evidence", "peak_rss_memory_bytes_budget"), 4096),
    (("future_run_evidence", "per_run_walltime_budget_s"), 500),
    (("future_run_evidence", "write_once_S3_evidence_id_required"), False),
    (("status_outcome", "S3_numeric_repetition_acceptance"), "PASS"),
])
def test_config_mutation_rejected(policy, path, bad):
    changed = copy.deepcopy(policy)
    child = changed
    for item in path[:-1]:
        child = child[item]
    child[path[-1]] = bad
    with pytest.raises(S3D4GateError):
        validate_contract(changed)


def test_duplicate_risk_cell_rejected(policy):
    from experiments.r6_thermo_provider_pilot_v1.s3_d4_numeric_screen import (
        RISK_FILE, load_json,
    )
    risk = load_json(RISK_FILE)
    risk["grids"][0]["cells"][1] = copy.deepcopy(risk["grids"][0]["cells"][0])
    with pytest.raises(S3D4GateError):
        validate_contract(policy, risk=risk)


@pytest.mark.parametrize(("key", "bad"), [
    ("PT_X_scientific_domain", "SUPPORTED"),
    ("authority", "APPROVED"),
    ("S3_engine_runs", 1),
    ("engine_origin_anchor", True),
])
def test_science_risk_cell_promotion_rejected(policy, key, bad):
    from experiments.r6_thermo_provider_pilot_v1.s3_d4_numeric_screen import (
        RISK_FILE, load_json,
    )
    risk = load_json(RISK_FILE)
    risk["grids"][0]["cells"][0][key] = bad
    with pytest.raises(S3D4GateError):
        validate_contract(policy, risk=risk)


def test_same_pt_identical_mag_still_not_numerically_ratified(mag):
    result = compare_readbacks(mag, copy.deepcopy(mag))
    assert result["same_pt"]
    assert result["same_as_printed"]
    assert result["max_abs_phase_fraction_delta"] == 0
    assert result["gibbs_abs_delta"] == 0
    assert result["density_rel_delta"] == 0
    assert result["numeric_acceptance"] == "NOT_RATIFIED"
    assert result["repeatability_pass"] is None
    assert result["engine_executions_authorized"] == 0


def test_same_pt_magemin_delta_recorded_no_pass(mag):
    other = copy.deepcopy(mag)
    other["phases"] = {"liq": 0.26, "opx": 0.74}
    other["G_system"] += 2.0
    other["rho_kg_m3"] = 2910.0
    result = compare_readbacks(mag, other)
    assert result["max_abs_phase_fraction_delta"] == pytest.approx(0.01)
    assert result["gibbs_abs_delta"] == 2
    assert result["density_rel_delta"] == pytest.approx(10 / 2910)
    assert result["repeatability_pass"] is None
    assert result["decision"] == "SAME_PT_DELTAS_RECORDED__NUMERIC_GATE_NOT_RATIFIED"


def test_same_pt_phase_membership_change_review(mag):
    other = copy.deepcopy(mag)
    other["phases"] = {"liq": 0.25, "cpx": 0.75}
    result = compare_readbacks(mag, other)
    assert result["decision"] == "SAME_PT_PHASE_DISAGREEMENT_REQUIRES_ADJUDICATION"
    assert result["repeatability_pass"] is False
    assert result["added_phases"] == ["cpx"]
    assert result["removed_phases"] == ["opx"]


def test_across_pt_phase_change_observation_only(mag):
    other = copy.deepcopy(mag)
    other["P"] = 11
    other["phases"] = {"liq": 0.30, "cpx": 0.70}
    result = compare_readbacks(mag, other)
    assert not result["same_pt"]
    assert result["decision"] == "CROSS_PT_OBSERVATION_ONLY__NOT_PHASE_BOUNDARY_PROOF"
    assert result["max_abs_phase_fraction_delta"] is None
    assert result["physical_model_validation"] == "UNKNOWN"


def test_perplex_same_pt_no_gibbs_invented(per):
    other = copy.deepcopy(per)
    other["phases"] = {"Fsp(C1)": 69.95, "Augite(G)": 30.05}
    result = compare_readbacks(per, other)
    assert result["gibbs_abs_delta"] is None
    assert result["density_rel_delta"] is None
    assert result["max_abs_phase_fraction_delta"] == pytest.approx(.05)
    assert "Fsp_C1_I1_C1_STRUCTURAL_STATE_UNADJUDICATED" in result["science_caveats"]
    assert result["numeric_acceptance"] == "NOT_RATIFIED"


def test_cross_provider_comparison_rejected(mag, per):
    with pytest.raises(S3D4GateError, match="D4_CROSS_PROVIDER_COMPARISON_FORBIDDEN"):
        compare_readbacks(mag, per)


@pytest.mark.parametrize(("field", "bad"), [
    ("status", "SCIENTIFICALLY_VALIDATED"),
    ("provider", "Earth"),
    ("P", 7),
    ("T", float("nan")),
    ("rho_kg_m3", 0),
    ("rho_kg_m3", float("nan")),
    ("G_system", float("inf")),
    ("bulk_res_norm", 1e-2),
    ("max_source_component_delta", 1e-1),
    ("phases", {}),
    ("phases", {"liq": 1.1, "opx": -0.1}),
    ("phases", {"liq": .8, "opx": .1}),
])
def test_bad_mag_summary_rejected(mag, field, bad):
    changed = copy.deepcopy(mag)
    changed[field] = bad
    from experiments.r6_thermo_provider_pilot_v1.s3_design_contract import load as design
    with pytest.raises((S3D4GateError, ValueError)):
        inspect_readback(changed, design=design())


@pytest.mark.parametrize(("field", "bad"), [
    ("status", "SCIENTIFICALLY_VALIDATED"),
    ("printed_component_coverage", 9),
    ("printed_oxide_molar_rounding_audit", {}),
    ("phases", {"Fsp(C1)": 50, "Augite(G)": 40}),
    ("phases", {"Fsp(C1)": float("nan")}),
])
def test_bad_perplex_summary_rejected(per, field, bad):
    changed = copy.deepcopy(per)
    changed[field] = bad
    from experiments.r6_thermo_provider_pilot_v1.s3_design_contract import load as design
    with pytest.raises(S3D4GateError):
        inspect_readback(changed, design=design())


def test_perplex_wrong_component_names_rejected(per):
    changed = copy.deepcopy(per)
    changed["printed_oxide_molar_rounding_audit"].pop("Na2O")
    changed["printed_oxide_molar_rounding_audit"]["INVALID"] = {
        "reconstructed_mol": "0", "reported_mol": "0"
    }
    from experiments.r6_thermo_provider_pilot_v1.s3_design_contract import load as design
    with pytest.raises(S3D4GateError):
        inspect_readback(changed, design=design())


def test_perplex_malformed_printed_molar_row_rejected(per):
    changed = copy.deepcopy(per)
    changed["printed_oxide_molar_rounding_audit"]["O2"] = {
        "reported_mol": "0"
    }
    from experiments.r6_thermo_provider_pilot_v1.s3_design_contract import load as design
    with pytest.raises(S3D4GateError):
        inspect_readback(changed, design=design())


def test_perplex_invented_observable_rejected(per):
    changed = copy.deepcopy(per)
    changed["G_system"] = -200
    from experiments.r6_thermo_provider_pilot_v1.s3_design_contract import load as design
    with pytest.raises(S3D4GateError):
        inspect_readback(changed, design=design())
