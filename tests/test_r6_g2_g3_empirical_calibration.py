"""Mathematical synthetic recoverability; never ARCANA physical calibration."""
import math
import numpy as np
import pytest
from experiments.plate58_deforming_explore_v1.g2_g3_empirical_calibration import (
 fit_g2_dislocation_laboratory,fit_g3_linear_basal_drag,assess_current_t0_constraints,
 CalibrationError,R_GAS,
)


def laboratory_rows(water=False):
    # Deterministic constructed data, not measured laboratory results.
    rng=np.random.default_rng(71)
    entries=[]
    logA=math.log(1.1e-22); n=3.5; E=300000.; V=6e-6; r=1.1
    for i in range(28):
        T=float(rng.uniform(800,1400)); P=float(rng.uniform(1e8,2e9))
        stress=float(rng.uniform(80e6,400e6))
        fugacity=float(rng.uniform(2e7,5e8))
        log_rate=logA+n*math.log(stress)-(E+P*V)/(R_GAS*T)
        if water:log_rate+=r*math.log(fugacity/1e8)
        entries.append({"source_kind":"LAB_MEASURED_TRIAXIAL",
            "source_reference":"SYNTHETIC_MANUFACTURED_TEST_NOT_LAB",
            "experiment_group":"holdout" if i>=23 else "training",
            "measurement_id":str(i),"differential_stress_pa":stress,
            "measured_strain_rate_s_inv":math.exp(log_rate),
            "temperature_k":T,"confining_pressure_pa":P,
            "water_fugacity_pa":fugacity})
    return entries[:23],entries[23:]


@pytest.mark.parametrize("water",[False,True])
def test_recover_manufactured_creep_parameters_without_world_claim(water):
    a,b=laboratory_rows(water)
    fit=fit_g2_dislocation_laboratory(a,b,water_reference_pa=1e8 if water else None)
    assert fit["n"]==pytest.approx(3.5,rel=1e-8)
    assert fit["E_j_mol"]==pytest.approx(300000,rel=1e-8)
    assert fit["V_m3_mol"]==pytest.approx(6e-6,rel=1e-7)
    assert fit["A_pa_minus_n_s_inv"]==pytest.approx(1.1e-22,rel=1e-8)
    assert fit["water_fugacity_exponent"]==(pytest.approx(1.1,rel=1e-8) if water else None)
    assert fit["holdout_log_rate_rmse"]<1e-9
    assert not fit["mineralogy_author_ratified"]


def test_pressure_temperature_collinearity_blocks_V():
    a,b=laboratory_rows()
    for row in a+b:row["confining_pressure_pa"]=1e9
    with pytest.raises(CalibrationError,match="NOT_IDENTIFIABLE"):
        fit_g2_dislocation_laboratory(a,b)


def test_missing_fugacity_does_not_default_to_dry():
    a,b=laboratory_rows(water=True)
    del a[0]["water_fugacity_pa"]
    with pytest.raises(CalibrationError,match="WATER_FUGACITY"):
        fit_g2_dislocation_laboratory(a,b,water_reference_pa=1e8)


def test_holdout_group_leakage_rejected():
    a,b=laboratory_rows()
    b[0]["experiment_group"]="training"
    with pytest.raises(CalibrationError,match="HOLDOUT_GROUP_LEAKAGE"):
        fit_g2_dislocation_laboratory(a,b)


def test_no_stress_observations_no_fit():
    with pytest.raises(CalibrationError,match="INDEPENDENT_MEASUREMENTS"):
        fit_g2_dislocation_laboratory([],[])


def basal_rows():
    a=[]
    beta=2.5e9 # synthetic Pa s/m, NOT a mantle parameter
    for i in range(6):
        lith=np.array([1e-9*i,-2e-9])
        deep=np.array([3e-9+i*3e-10,1e-9])
        a.append({"source_kind":"OBSERVED_TANGENTIAL_TRACTION_AND_DEEP_FLOW",
                  "source_reference":"SYNTHETIC_MANUFACTURED_NOT_ARCANA",
                  "experiment_group":"holdout" if i>=4 else "train",
                  "measurement_id":f"B{i}",
                  "lithosphere_velocity_en_m_s":lith.tolist(),
                  "deep_mantle_velocity_en_m_s":deep.tolist(),
                  "measured_basal_traction_en_pa":(beta*(deep-lith)).tolist()})
    return a[:4],a[4:]


def test_basal_beta_recovers_manufactured_vector_traction():
    a,b=basal_rows()
    r=fit_g3_linear_basal_drag(a,b)
    assert r["basal_drag_beta_pa_s_per_m"]==pytest.approx(2.5e9)
    assert r["holdout_traction_rmse_pa"]<1e-11
    assert r["ARCANA_basal_traction_authorized"] is False


def test_basal_missing_deep_mantle_flow_rejected():
    a,b=basal_rows();del a[0]["deep_mantle_velocity_en_m_s"]
    with pytest.raises(CalibrationError,match="G3_VECTOR_MISSING"):
        fit_g3_linear_basal_drag(a,b)


def test_basal_motion_without_reference_speed_not_identifiable():
    a,b=basal_rows()
    for row in a:
        row["deep_mantle_velocity_en_m_s"]=row["lithosphere_velocity_en_m_s"]
    with pytest.raises(CalibrationError,match="DRAG_NOT_IDENTIFIABLE"):
        fit_g3_linear_basal_drag(a,b)


def test_current_t0_evidence_reports_nonidentifiability_not_fitted_values():
    r=assess_current_t0_constraints()
    assert r["g2_laboratory_fit"] is None and r["g3_basal_drag_fit"] is None
    assert r["mechanical_solve_authorized"] is False
    assert r["physical_T1"] is None
    assert r["kinematic_rate_proxy_s_inv_by_assumed_width_km"]["100"]==pytest.approx(4.99087e-14)
