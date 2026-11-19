"""SHELLS candidate creep form identity and incompatibility tests.

Synthetic rheology only, no physical model, no authorial material promotion.
"""
import copy

import numpy as np
import pytest

from experiments.plate58_deforming_explore_v1.shells_lr_bridge import (
    candidate_to_shells_form, validate_source_fortran,
)
from experiments.plate58_deforming_explore_v1.full_column import G2InputError


def pre():
    return {
        "crust_thickness_m":28000.,
        "mantle_lithosphere_thickness_m":52000.,
        "crust_density_kg_m3":2750.,
        "mantle_density_kg_m3":3200.,
        "layer1_z0_m":0.,"layer1_z1_m":28000.,
        "layer2_z0_m":28000.,"layer2_z1_m":80000.,
        "layer1_c0_k":850.,"layer1_c1_k_m":0.,
        "layer1_c2_k_m2":0.,"layer1_c3_k_m3":0.,
        "layer2_c0_k":1400.,"layer2_c1_k_m":0.,
        "layer2_c2_k_m2":0.,"layer2_c3_k_m3":0.,
    }


def law(n=3.5):
    return {
        "source_reference":"SYNTHETIC_LAW_TEST_NOT_SOURCE_ROCK",
        "stress_convention":"ASPECT_2ETA_EPS_INVARIANT_SCALE",
        "A_pa_minus_n_s_inv":1e-32,"n":n,"E_j_mol":400000.,
        "V_m3_mol":1.4e-5,
        "fugacity_exponent":0.,"water_fugacity_pa":None,
        "reference_fugacity_pa":None,
        "invariant_to_friction_shear_factor":1.,
        "shear_conversion_reference":"SYNTHETIC_ONLY_NEVER_GEOLOGY",
        "valid_temperature_k":[200.,1900.],
        "valid_pressure_pa":[0.,4e9],
        "valid_strain_rate_s_inv":[1e-17,1e-12],
    }


def spec():
    return {
        "authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
        "source_identifier":"SYNTHETIC_TWO_LAYER_001",
        "gravity_m_s2":9.81,"strain_rate_s_inv":1e-14,
        "layers":{
            "crust":{"ductile":law(),"brittle":{"mode":"UNBOUND"}},
            "mantle":{"ductile":law(),"brittle":{"mode":"UNBOUND"}},
        },
    }


def test_common_n_exact_creep_form_and_layer_pressure_offset():
    r=candidate_to_shells_form(pre(),spec())
    assert r["SHELLS_eCreep_shared_exactly_compatible"]
    assert r["proposed_single_eCreep_if_compatible"]==pytest.approx(1/3.5)
    assert r["SHELLS_full_LR_coefficients"] is None
    assert all(x["relative_creep_scale_max_error"]<1e-12
               for x in r["layer_form_parity"])
    m=r["candidate_layer_coefficients"]["mantle"]
    p=9.81*28000*(2750-3200)
    assert m["source_pressure_intercept_pa"]==pytest.approx(p)
    assert m["cCreep_candidate_kelvin_per_m"]>0
    assert r["mechanical_solve_authorized"] is False


def test_n_crust4_mantle3point5_cannot_share_single_ecreep():
    s=spec()
    s["layers"]["crust"]["ductile"]["n"]=4.
    r=candidate_to_shells_form(pre(),s)
    assert not r["SHELLS_eCreep_shared_exactly_compatible"]
    assert r["proposed_single_eCreep_if_compatible"] is None
    assert r["SHELLS_full_LR_coefficients"] is None


def test_explicit_fugacity_changes_creep_prefactor_without_silent_default():
    s=spec()
    l=s["layers"]["mantle"]["ductile"]
    l["fugacity_exponent"]=1.
    l["water_fugacity_pa"]=2e8
    l["reference_fugacity_pa"]=1e8
    r=candidate_to_shells_form(pre(),s)
    a_new=r["candidate_layer_coefficients"]["mantle"]["aCreep_candidate_pa_s_to_e"]
    a_old=candidate_to_shells_form(pre(),spec())[
        "candidate_layer_coefficients"]["mantle"]["aCreep_candidate_pa_s_to_e"]
    assert a_new/a_old==pytest.approx(2**(-1/3.5))


def test_missing_fugacity_rejected():
    s=spec()
    s["layers"]["crust"]["ductile"]["fugacity_exponent"]=1.
    with pytest.raises(G2InputError):
        candidate_to_shells_form(pre(),s)


def test_temperature_outside_source_window_rejected():
    s=spec()
    s["layers"]["crust"]["ductile"]["valid_temperature_k"]=[973.15,1473.15]
    with pytest.raises(G2InputError,match="CALIBRATED_PT_RATE_RANGE_NOT_COVERED"):
        candidate_to_shells_form(pre(),s)


def test_rho_gradient_does_not_fabricate_lithostatic_pressure():
    s=spec()
    r=candidate_to_shells_form(pre(),s)
    cc=r["candidate_layer_coefficients"]["crust"]
    mm=r["candidate_layer_coefficients"]["mantle"]
    assert cc["source_pressure_intercept_pa"]==0
    assert mm["source_pressure_intercept_pa"]<0
    assert cc["cCreep_candidate_kelvin_per_m"]<mm["cCreep_candidate_kelvin_per_m"]


def test_byrly_is_not_bilinear_byerlee_strength():
    r=candidate_to_shells_form(pre(),spec())
    assert "NOT the Byerlee" in r["note"]
    assert r["SHELLS_Byerly_fault_reduction"] is None
    assert r["SHELLS_cFric"] is None


def test_cannot_promote_authority():
    s=spec()
    s["authority"]="AUTHOR_RATIFIED"
    with pytest.raises(G2InputError,match="RATIFICATION_NOT_GRANTED"):
        candidate_to_shells_form(pre(),s)


def test_exact_implementation_source_conventions_present():
    pins=validate_source_fortran()
    assert len(pins)==2 and all(len(p)==64 for p in pins.values())
