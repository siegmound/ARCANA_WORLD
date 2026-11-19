"""Source-driven candidate G2 whole-column strength evaluator, NOT a solved material law.

All environmental and constitutive parameters must be explicitly supplied in a
candidate specification with provenance. The PRE T0 polynomial and densities
are source fields; the strain-rate, pore model, Byerlee reference and creep laws
are hypotheses, not inferences from PRE or the author-ratified G3 architecture.
"""
from __future__ import annotations

import math
from typing import Any
import numpy as np

R_GAS = 8.31446261815324
BYERLEE_TRANSITION_PA = 2.0e8


class G2InputError(ValueError):
    pass


def need(ok: bool, message: str):
    if not ok:
        raise G2InputError(message)


def scalar(value: Any, name: str, *, positive=False, nonnegative=False) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise G2InputError(f"G2_REQUIRED_NUMERIC_{name}") from exc
    need(math.isfinite(x), f"G2_NONFINITE_{name}")
    if positive:
        need(x > 0, f"G2_NOT_POSITIVE_{name}")
    if nonnegative:
        need(x >= 0, f"G2_NEGATIVE_{name}")
    return x


def bounds(spec: dict, key: str) -> tuple[float, float]:
    row = spec.get(key)
    need(isinstance(row, list) and len(row) == 2, "G2_DOMAIN_MISSING_" + key)
    lower = scalar(row[0], key+"_MIN", nonnegative=True)
    upper = scalar(row[1], key+"_MAX", positive=True)
    need(lower < upper, "G2_DOMAIN_INVALID_" + key)
    return lower, upper


def temperature_k(pre: dict, layer: int, z_m: np.ndarray) -> np.ndarray:
    prefix = f"layer{layer}_"
    z0 = scalar(pre[prefix+"z0_m"], "Z0", nonnegative=True)
    z1 = scalar(pre[prefix+"z1_m"], "Z1", positive=True)
    need(z1 > z0 and np.all((z_m >= z0-1e-8)&(z_m <= z1+1e-8)),
         "G2_PRE_LAYER_DEPTH_INVALID")
    x = z_m-z0
    result = (float(pre[prefix+"c0_k"])+x*(float(pre[prefix+"c1_k_m"])
              +x*(float(pre[prefix+"c2_k_m2"])+x*float(pre[prefix+"c3_k_m3"]))))
    need(np.all(np.isfinite(result)) and np.all(result > 0),
         "G2_PRE_TEMPERATURE_INVALID")
    return result


def overburden_pa(pre: dict, gravity: float, z_m: np.ndarray) -> np.ndarray:
    c = scalar(pre["crust_thickness_m"], "CRUST_THICKNESS", positive=True)
    m = scalar(pre["mantle_lithosphere_thickness_m"], "MANTLE_THICKNESS", positive=True)
    need(np.all((z_m >= 0) & (z_m <= c+m+1e-8)), "G2_DEPTH_OUTSIDE_LITHOSPHERE")
    rho_c=scalar(pre["crust_density_kg_m3"], "CRUST_DENSITY", positive=True)
    rho_m=scalar(pre["mantle_density_kg_m3"], "MANTLE_DENSITY", positive=True)
    return gravity*(rho_c*np.minimum(z_m,c)+rho_m*np.maximum(0,z_m-c))


def flow_stress_pa(law: dict, temperature: np.ndarray, pressure: np.ndarray,
                   strain_rate_s_inv: float) -> np.ndarray:
    """Power-law stress *scale* in the explicit ASPECT dislocation convention.

    epsilon_dot = A_eff * sigma**n * exp(-(E+P*V)/(R*T)).
    This is not automatically a frictional shear stress; the candidate must
    state an explicit convention-conversion factor for comparison.
    """
    need(law.get("stress_convention") == "ASPECT_2ETA_EPS_INVARIANT_SCALE",
         "G2_STRESS_CONVENTION_UNSUPPORTED")
    need(isinstance(law.get("source_reference"), str) and
         len(law["source_reference"].strip()) >= 10,
         "G2_FLOW_LAW_SOURCE_MISSING")
    a=scalar(law.get("A_pa_minus_n_s_inv"), "FLOW_A", positive=True)
    n=scalar(law.get("n"), "FLOW_N", positive=True)
    e=scalar(law.get("E_j_mol"), "FLOW_E", nonnegative=True)
    v=scalar(law.get("V_m3_mol"), "FLOW_V", nonnegative=True)
    water_exponent=scalar(law.get("fugacity_exponent"), "WATER_EXPONENT", nonnegative=True)
    if water_exponent > 0:
        f=scalar(law.get("water_fugacity_pa"), "WATER_FUGACITY", positive=True)
        ref=scalar(law.get("reference_fugacity_pa"), "REFERENCE_FUGACITY", positive=True)
        a *= (f/ref)**water_exponent
    else:
        need(law.get("water_fugacity_pa") is None and
             law.get("reference_fugacity_pa") is None,
             "G2_UNSUPPORTED_IMPLICIT_WATER_PARAMETER")
    conv=scalar(law.get("invariant_to_friction_shear_factor"),
                "SHEAR_CONVERSION",positive=True)
    need(isinstance(law.get("shear_conversion_reference"), str) and
         len(law["shear_conversion_reference"].strip()) >= 10,
         "G2_SHEAR_CONVERSION_SOURCE_MISSING")
    tlo,thi=bounds(law,"valid_temperature_k")
    plo,phi=bounds(law,"valid_pressure_pa")
    elo,ehi=bounds(law,"valid_strain_rate_s_inv")
    need(elo <= strain_rate_s_inv <= ehi and
         bool(np.all((temperature >= tlo)&(temperature <= thi))) and
         bool(np.all((pressure >= plo)&(pressure <= phi))),
         "G2_CREEP_SOURCE_VALIDITY_OUTSIDE_CALIBRATED_DOMAIN")
    log_stress=(math.log(strain_rate_s_inv)-math.log(a)+
                (e+pressure*v)/(R_GAS*temperature))/n
    need(bool(np.all(np.isfinite(log_stress))) and bool(np.all(log_stress < 700)),
         "G2_FLOW_STRESS_OVERFLOW")
    return np.exp(log_stress)*conv


def brittle_shear_pa(pressure_lith: np.ndarray, spec: dict) -> np.ndarray:
    need(spec.get("source_reference") == "BYERLEE_1978_REFERENCE__NOT_R6_MATERIAL",
         "G2_FRICTION_LAW_NOT_EXPLICIT")
    effective_ratio=scalar(spec.get("normal_stress_over_lithostatic"),
                           "NORMAL_STRESS_RATIO",positive=True)
    biot=scalar(spec.get("biot_coefficient"), "BIOT",nonnegative=True)
    pore_ratio=scalar(spec.get("pore_pressure_over_lithostatic"),
                      "PORE_PRESSURE_RATIO",nonnegative=True)
    need(biot<=1 and pore_ratio<=1, "G2_PRESSURE_MODEL_OUTSIDE_DOMAIN")
    p_eff=(effective_ratio-biot*pore_ratio)*pressure_lith
    need(bool(np.all(p_eff >= 0)),"G2_NEGATIVE_EFFECTIVE_NORMAL_PRESSURE")
    pmin,pmax=bounds(spec,"valid_effective_normal_pressure_pa")
    need(bool(np.all((p_eff >= pmin)&(p_eff <= pmax))),
         "G2_BYERLEE_SOURCE_VALIDITY_OUTSIDE_CALIBRATED_DOMAIN")
    return np.where(p_eff<=BYERLEE_TRANSITION_PA,
                    0.85*p_eff,50.0e6+0.6*p_eff)


def evaluate_layer(pre: dict, layer: int, spec: dict, n_subintervals: int) -> dict:
    need(isinstance(n_subintervals,int) and n_subintervals>=8 and
         n_subintervals%2==0,"G2_QUADRATURE_SAMPLES_INVALID")
    z0=scalar(pre[f"layer{layer}_z0_m"],"Z0",nonnegative=True)
    z1=scalar(pre[f"layer{layer}_z1_m"],"Z1",positive=True)
    need(z1>z0,"G2_INVALID_LAYER_DEPTH")
    z=np.linspace(z0,z1,n_subintervals+1)
    gravity=scalar(spec.get("gravity_m_s2"),"GRAVITY",positive=True)
    strain=scalar(spec.get("strain_rate_s_inv"),"STRAIN_RATE",positive=True)
    t=temperature_k(pre,layer,z)
    lith=overburden_pa(pre,gravity,z)
    which="crust" if layer==1 else "mantle"
    material=spec["layers"][which]
    law=material["ductile"]
    duct=flow_stress_pa(law,t,lith,strain)
    friction=material["brittle"]
    if friction["mode"]=="BYERLEE_1978_REFERENCE":
        yield_b=brittle_shear_pa(lith,friction)
        values=np.minimum(yield_b,duct)
        brittle_governs=int(np.count_nonzero(yield_b<=duct))
    elif friction["mode"]=="DUCTILE_ONLY_EXPLICIT_HYPOTHESIS":
        need(isinstance(friction.get("rationale"),str) and
             len(friction["rationale"].strip())>=10,
             "G2_DUCTILE_ONLY_HYPOTHESIS_WITHOUT_RATIONALE")
        values=duct
        brittle_governs=0
    else:
        raise G2InputError("G2_BRITTLE_BRANCH_UNRESOLVED")
    need(bool(np.all(np.isfinite(values))) and bool(np.all(values>=0)),
         "G2_INTEGRATED_STRENGTH_INVALID")
    integral=float(np.trapezoid(values,z))
    return {"layer":which,"z0_m":z0,"z1_m":z1,
            "effective_strength_integrated_pa_m":integral,
            "min_effective_shear_strength_pa":float(np.min(values)),
            "max_effective_shear_strength_pa":float(np.max(values)),
            "brittle_preferred_sample_count":brittle_governs,
            "ductile_or_unconstrained_sample_count":len(z)-brittle_governs,
            "sample_count":len(z),
            "temperature_k_range":[float(np.min(t)),float(np.max(t))],
            "lithostatic_pressure_pa_range":[float(np.min(lith)),float(np.max(lith))]}


def evaluate_full_column(pre: dict, spec: dict) -> dict:
    """Evaluate only an explicit noncanonical candidate on one genuine PRE column.

    No default G2 material, fluid pressure, gravity, friction or conversion.
    A successful numerical calculation is NOT approval for SHELLS or T1.
    """
    need(spec.get("authority") == "ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
         "G2_ATTEMPTED_PHYSICAL_AUTHORITY_PROMOTION")
    need(isinstance(spec.get("source_identifier"),str) and
         len(spec["source_identifier"].strip())>=10,
         "G2_MATERIAL_SCENARIO_SOURCE_MISSING")
    n=spec["integration"].get("subintervals_per_layer")
    tol=scalar(spec["integration"].get("max_relative_discretization_error"),
               "INTEGRATION_ERROR_TOLERANCE",positive=True)
    need(0<tol<0.5,"G2_INTEGRATION_TOLERANCE_INVALID")
    require_fractions = ("crust_thickness_m","mantle_lithosphere_thickness_m",
                         "crust_density_kg_m3","mantle_density_kg_m3")
    for key in require_fractions:
        scalar(pre[key],key,positive=True)
    c=scalar(pre["crust_thickness_m"],"CRUST_THICKNESS",positive=True)
    m=scalar(pre["mantle_lithosphere_thickness_m"],"MANTLE_THICKNESS",positive=True)
    need(abs(float(pre["layer1_z0_m"]))<1e-6 and
         abs(float(pre["layer1_z1_m"])-c)<1e-6 and
         abs(float(pre["layer2_z0_m"])-c)<1e-6 and
         abs(float(pre["layer2_z1_m"])-(c+m))<1e-6,
         "G2_PRE_LAYER_GEOMETRY_CHANGED")
    layer_results=[]
    fine_results=[]
    for i in (1,2):
        layer_results.append(evaluate_layer(pre,i,spec,n))
        fine_results.append(evaluate_layer(pre,i,spec,2*n))
    integrated=sum(x["effective_strength_integrated_pa_m"] for x in fine_results)
    coarse=sum(x["effective_strength_integrated_pa_m"] for x in layer_results)
    rel=abs(integrated-coarse)/max(abs(integrated),np.finfo(float).tiny)
    need(rel<=tol,"G2_INTEGRATION_DISCRETIZATION_NOT_CONVERGED")
    return {
        "scope":"SOURCE_T0_PRE_INPUT_AND_EXPLICIT_ENGINEERING_CONSTITUTIVE_CANDIDATE",
        "candidate_source_identifier":spec["source_identifier"],
        "full_lithosphere_integrated_effective_shear_strength_pa_m":integrated,
        "layers":fine_results,
        "relative_two_resolution_difference":rel,
        "numerical_tolerance":tol,
        "shear_integral_to_SHELLS_LR_equivalence":None,
        "actual_G3_A_exterior_stiffness":None,
        "mechanical_solve_authorized":False,
        "physical_T1":None,
    }
