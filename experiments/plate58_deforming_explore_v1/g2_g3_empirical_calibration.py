"""Lab-only G2 flow-law and observed-traction G3 drag calibration.

Never calibrate geological constitutive laws from Euler motion alone.
All data must be independent empirical observations with explicit provenance.
Passing a regression does not authorize ARCANA mineralogy, G3 forcing or T1.
"""
from __future__ import annotations

import math
import numpy as np

R_GAS = 8.31446261815324
STATUS = "EMPIRICAL_FIT_CANDIDATE__ARCANA_PHYSICAL_AUTHORITY_UNRESOLVED"


class CalibrationError(ValueError):
    pass


def require(ok, code):
    if not ok:
        raise CalibrationError(code)


def number(value, label, *, strictly_positive=False):
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise CalibrationError("CALIBRATION_" + label + "_MISSING") from exc
    require(math.isfinite(result) and (not strictly_positive or result > 0),
            "CALIBRATION_" + label + "_INVALID")
    return result


def validated_observations(rows, required_kind, min_count):
    require(isinstance(rows, list) and len(rows) >= min_count,
            "CALIBRATION_INDEPENDENT_MEASUREMENTS_MISSING")
    keys = set()
    for row in rows:
        require(isinstance(row, dict) and
                row.get("source_kind") == required_kind and
                isinstance(row.get("source_reference"), str) and
                len(row["source_reference"].strip()) >= 10 and
                isinstance(row.get("experiment_group"), str) and
                bool(row["experiment_group"].strip()) and
                isinstance(row.get("measurement_id"), str) and
                bool(row["measurement_id"].strip()),
                "CALIBRATION_OBSERVATION_PROVENANCE_INCOMPLETE")
        key = row["measurement_id"]
        require(key not in keys,"CALIBRATION_DUPLICATED_MEASUREMENT")
        keys.add(key)
    return rows


def validate_split(train, holdout):
    train_groups = {r["experiment_group"] for r in train}
    test_groups = {r["experiment_group"] for r in holdout}
    require(train_groups.isdisjoint(test_groups),
            "CALIBRATION_HOLDOUT_GROUP_LEAKAGE")


def _creep_features(rows, water_reference_pa):
    X, y = [], []
    for r in rows:
        stress = number(r.get("differential_stress_pa"),"STRESS",strictly_positive=True)
        rate = number(r.get("measured_strain_rate_s_inv"),"RATE",strictly_positive=True)
        temp = number(r.get("temperature_k"),"TEMPERATURE",strictly_positive=True)
        p = number(r.get("confining_pressure_pa"),"PRESSURE")
        require(p >= 0,"CALIBRATION_PRESSURE_NEGATIVE")
        features = [1., math.log(stress), -1./(R_GAS*temp),
                    -p/(R_GAS*temp)]
        if water_reference_pa is not None:
            f = number(r.get("water_fugacity_pa"),"WATER_FUGACITY",strictly_positive=True)
            features.append(math.log(f/water_reference_pa))
        X.append(features)
        y.append(math.log(rate))
    return np.array(X, dtype=float), np.array(y, dtype=float)


def _fit_linear(X, y, condition_max):
    scale = np.maximum(np.max(np.abs(X),axis=0),1e-300)
    scaled = X / scale
    singular = np.linalg.svd(scaled, full_matrices=False, compute_uv=False)
    require(singular[-1] > 0 and
            singular[0]/singular[-1] <= condition_max,
            "CALIBRATION_NOT_IDENTIFIABLE_OR_ILL_CONDITIONED")
    coefficients, _, rank, _ = np.linalg.lstsq(scaled,y,rcond=1e-12)
    require(rank == X.shape[1],"CALIBRATION_DESIGN_RANK_DEFICIENT")
    return coefficients/scale, float(singular[0]/singular[-1])


def fit_g2_dislocation_laboratory(train, holdout, *, water_reference_pa=None,
                                 condition_max=1e8):
    """Fit log(eps)=log(A)+n*log(sigma)-E/(RT)-PV/(RT)+r*log(f/fref).

    Sigma is *triaxial differential stress*, never silently ASPECT J2 stress.
    Requires independent measured training/holdout groups, not synthetic PRE
    temperatures paired with invented stresses and rates.
    """
    if water_reference_pa is not None:
        water_reference_pa=number(water_reference_pa,"WATER_REFERENCE",strictly_positive=True)
    max_condition=number(condition_max,"CONDITION_LIMIT",strictly_positive=True)
    count=5 if water_reference_pa is not None else 4
    validated_observations(train,"LAB_MEASURED_TRIAXIAL",count+2)
    validated_observations(holdout,"LAB_MEASURED_TRIAXIAL",2)
    validate_split(train,holdout)
    X,y = _creep_features(train,water_reference_pa)
    Xt,yt = _creep_features(holdout,water_reference_pa)
    beta,condition=_fit_linear(X,y,max_condition)
    log_A,n,E,V=map(float,beta[:4])
    r = float(beta[4]) if water_reference_pa is not None else 0.
    require(1. <= n <= 10. and E>=0 and r>=0 and -700<log_A<700,
            "CALIBRATION_PHYSICAL_PARAMETER_CONSTRAINT_FAILED")
    train_error=y-X@beta
    holdout_error=yt-Xt@beta
    require(np.all(np.isfinite(holdout_error)),"CALIBRATION_NONFINITE_PREDICTION")
    temps=[number(i["temperature_k"],"TEMPERATURE") for i in train]
    pressures=[number(i["confining_pressure_pa"],"PRESSURE") for i in train]
    stresses=[number(i["differential_stress_pa"],"STRESS") for i in train]
    rate=[number(i["measured_strain_rate_s_inv"],"RATE") for i in train]
    def band(values):return [min(values),max(values)]
    return {
        "status":STATUS,
        "stress_convention":"LAB_TRIAXIAL_DIFFERENTIAL_STRESS_PA_NOT_ASPECT_J2",
        "A_pa_minus_n_s_inv":math.exp(log_A),"n":n,
        "E_j_mol":E,"V_m3_mol":V,
        "activation_volume_sign_requires_source_review":V<0,
        "water_fugacity_exponent":r if water_reference_pa is not None else None,
        "water_reference_pa":water_reference_pa,
        "train_log_rate_rmse":float(np.sqrt(np.mean(train_error**2))),
        "holdout_log_rate_rmse":float(np.sqrt(np.mean(holdout_error**2))),
        "design_condition_number":condition,
        "training_observations":len(train),"holdout_observations":len(holdout),
        "train_temperature_k_range":band(temps),
        "train_pressure_pa_range":band(pressures),
        "train_differential_stress_pa_range":band(stresses),
        "train_measured_strain_rate_s_inv_range":band(rate),
        "full_T0_crust_law_validated":False,
        "mineralogy_author_ratified":False,
        "measurements_independently_verified":False,
        "SHELLS_stress_convention_equivalence":False,
        "physical_T1":None,
    }


def _vector(row, key):
    try:
        v=np.asarray(row[key],dtype=float)
    except (KeyError,TypeError,ValueError) as exc:
        raise CalibrationError("CALIBRATION_G3_VECTOR_MISSING") from exc
    require(v.shape==(2,) and bool(np.all(np.isfinite(v))),
            "CALIBRATION_G3_VECTOR_INVALID")
    return v


def fit_g3_linear_basal_drag(train, holdout):
    """Tau_b=beta*(v_deep-v_lith) using independent observed shear+flow.

    Beta has units Pa*s/m, never inferred from plate Euler rates alone.
    A real physical basal NORMAL condition and mechanical LAB are separate.
    """
    validated_observations(train,"OBSERVED_TANGENTIAL_TRACTION_AND_DEEP_FLOW",3)
    validated_observations(holdout,"OBSERVED_TANGENTIAL_TRACTION_AND_DEEP_FLOW",1)
    validate_split(train,holdout)
    def pairs(rows):
        dv=[]; traction=[]
        for row in rows:
            dv.append(_vector(row,"deep_mantle_velocity_en_m_s")-
                      _vector(row,"lithosphere_velocity_en_m_s"))
            traction.append(_vector(row,"measured_basal_traction_en_pa"))
        return np.array(dv),np.array(traction)
    v,t=pairs(train)
    vh,th=pairs(holdout)
    denom=float(np.sum(v*v))
    require(denom>1e-40,"CALIBRATION_G3_DRAG_NOT_IDENTIFIABLE")
    beta=float(np.sum(v*t)/denom)
    require(beta>0 and math.isfinite(beta),
            "CALIBRATION_G3_DRAG_NONPOSITIVE")
    return {
        "status":STATUS,"basal_drag_beta_pa_s_per_m":beta,
        "train_traction_rmse_pa":float(np.sqrt(np.mean((t-beta*v)**2))),
        "holdout_traction_rmse_pa":float(np.sqrt(np.mean((th-beta*vh)**2))),
        "training_observations":len(train),"holdout_observations":len(holdout),
        "deep_mantle_reference_frame_verified":False,
        "basal_normal_support_qualified":False,
        "mechanical_LAB_depth_qualified":False,
        "ARCANA_basal_traction_authorized":False,
        "physical_T1":None,
    }


def assess_current_t0_constraints():
    """Source-reported facts: no physical measured stresses/tractions provided."""
    opening_m_per_year=0.1575  # R6 5:8 source terminal diagnostic rounded.
    seconds_per_year=31557600.
    widths_km=(10.,100.,300.)  # EXPLORE widths, not observed fault zones.
    return {
      "status":"CALIBRATION_INPUTS_INSUFFICIENT__NO_PHYSICAL_FIT_EXECUTED",
      "basis":"R6_FIRST_DEFORMATION_MODEL_DECISION_FAIR_20261118 + 20261119 FAIR docs",
      "opening_rate_reference_m_per_year":opening_m_per_year,
      "kinematic_rate_proxy_s_inv_by_assumed_width_km":{
          str(int(w)):opening_m_per_year/(w*1000*seconds_per_year)
          for w in widths_km},
      "T0_crust_reported_temperature_k":[280.,1051.5581968311126],
      "GT95_lab_temperature_k":[1173.15,1373.15],
      "GT95_full_column_coverage":False,
      "source_measured_lab_stress_rate_records":None,
      "source_observed_basal_traction_and_deep_flow_records":None,
      "arcana_mineralogy":None,"water_fugacity":None,"pore_pressure":None,
      "physical_basal_normal_pressure":None,
      "g2_laboratory_fit":None,"g3_basal_drag_fit":None,
      "source_motion_is_not_stress_observation":True,
      "mechanical_solve_authorized":False,"solver_runs":0,"physical_T1":None,
    }
