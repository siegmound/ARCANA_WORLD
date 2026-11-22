"""Contract tests for the revised S1 real-engine gate; NO simulated PASS claim."""
from __future__ import annotations

import copy
from pathlib import Path

import pytest

from experiments.r6_thermo_provider_pilot_v1.validate_magemin_s1_v2 import (
    S1ValidationError, check_document,
)


@pytest.fixture
def report():
    return {
        "provider": "MAGEMin_C.jl",
        "version": "2.4.5",
        "scope": "EARTH_OFFICIAL_FIXTURE_ONLY_NOT_ARCANA",
        "cross_provider_comparable": False,
        "physical_T1_is_null": True,
        "reference_test_scope": "S1_STANDALONE_NUMERICAL",
        "fixtures": {
            "MAGEMIN_PREDEFINED_KLB1": {
                "status": 0,
                "P_kbar": 8.0,
                "T_C": 800.0,
                "rho_kg_m3": 3281.233784839709,
                "database_label": "ig",
                "G_system": -797.7873870835227,
                "phases": ["ol", "spl", "cpx", "opx"],
                "phase_mass_fractions": [
                    0.5828145981179869, 0.032941095355754346,
                    0.14893343831259942, 0.2353108682136594,
                ],
                "phase_molar_fractions": [
                    0.6118258952547502, 0.022535895841090246,
                    0.13758493601173902, 0.22805327289242058,
                ],
                "KLB1_G_reference_abs_delta": 5.614328983938321e-7,
                "KLB1_cp_reference_abs_delta": 0.6511044569438127,
            },
            "MAGEMIN_CUSTOM_IG": {
                "status": 0,
                "P_kbar": 10.0,
                "T_C": 1100.0,
                "rho_kg_m3": 2796.5590641303947,
                "database_label": "ig",
                "G_system": -916.8347763924897,
                "phases": ["liq", "cpx", "opx"],
                "phase_mass_fractions": [
                    0.7313343478373275, 0.2489167968690463,
                    0.019748855293626123,
                ],
                "phase_molar_fractions": [
                    0.7285174688188991, 0.25103686662063857,
                    0.020445664560462214,
                ],
                "frac_M_wt": 0.7313343478373275,
                "frac_S_wt": 0.2686656521626724,
                # Synthetic density-consistent numbers: contract test only.
                "rho_M": 2796.5590641303947,
                "rho_S": 2796.5590641303947,
                "density_closure_abs": 0.0,
                "input_sum_as_reported_wt_percent": 99.75,
                "readme_quantitative_reconciliation": "PENDING",
            },
        },
    }


def test_nominal_report_structure(report):
    assert check_document(report)["status"] == "MAGEMIN_S1_NUMERICAL_REPORT_CHECK_PASS"


@pytest.mark.parametrize("path,value", [
    (("cross_provider_comparable",), True),
    (("physical_T1_is_null",), False),
    (("fixtures", "MAGEMIN_PREDEFINED_KLB1", "G_system"), -750.0),
    (("fixtures", "MAGEMIN_PREDEFINED_KLB1", "KLB1_cp_reference_abs_delta"), 2.2),
    (("fixtures", "MAGEMIN_PREDEFINED_KLB1", "phase_mass_fractions"), [0.2, 0.2, 0.2, 0.2]),
    (("fixtures", "MAGEMIN_PREDEFINED_KLB1", "phase_molar_fractions"), [0.2, 0.2, 0.2, 0.2]),
    (("fixtures", "MAGEMIN_CUSTOM_IG", "input_sum_as_reported_wt_percent"), 100.0),
    (("fixtures", "MAGEMIN_CUSTOM_IG", "readme_quantitative_reconciliation"), "PASS"),
    (("fixtures", "MAGEMIN_CUSTOM_IG", "density_closure_abs"), 1.0),
    (("fixtures", "MAGEMIN_CUSTOM_IG", "frac_S_wt"), 0.5),
    (("fixtures", "MAGEMIN_CUSTOM_IG", "phases"), ["liq", "ol", "opx"]),
])
def test_fail_closed(report, path, value):
    case = copy.deepcopy(report)
    item = case
    for key in path[:-1]:
        item = item[key]
    item[path[-1]] = value
    with pytest.raises(S1ValidationError):
        check_document(case)


def test_julia_source_uses_functions_not_global_soft_scope():
    root = Path(__file__).resolve().parents[1]
    text = (root / "experiments/r6_thermo_provider_pilot_v1"
            / "run_magemin_official.jl").read_text()
    assert "function run_predefined_case()" in text
    assert "function run_custom_case()" in text
    assert "function main()" in text
    assert "global data =" not in text
    assert "MAGEMIN_KLB1_G_REFERENCE_MISMATCH" in text
    assert "MAGEMIN_CUSTOM_DENSITY_CLOSURE_INVALID" in text
