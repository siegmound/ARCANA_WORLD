"""G2 engineering two-layer smooth Drucker-Prager-limited dislocation creep.

This is a convex smooth-cap reference continuum, NOT ideal plastic return,
physical fault slip, or ShellSet's Diamnd/Mohr/OneBar implementation.
Pore pressure, Biot, cohesion, friction and creep must all be explicit.
No direct ARCANA material assignments or physical T1 are authorized.
"""
from __future__ import annotations

import math
import numpy as np

from experiments.plate58_deforming_explore_v1.full_column import (
    R_GAS, temperature_k, overburden_pa, bounds,
)
from experiments.plate58_deforming_explore_v1.nonlinear_layered_g3 import (
    Q_3D_PLANE_STRESS_KINEMATIC as Q,
)
from experiments.plate58_deforming_explore_v1.g2_exact_thermal_validity import (
    require_laboratory_temperature_coverage,
)

STATUS = "CANDIDATE_G2_PRESSURE_AWARE_TWO_LAYER_VISCOPLASTIC_CONTINUUM__R6_MATERIAL_OPEN"
# BOTH formulas appear in published ASPECT documentation. Do not silently
# mix their pressure coefficients; they are different constitutive conventions.
# Modern ASPECT Rheology::DruckerPrager describes 6*P*sin(phi); legacy
# MaterialModel::ViscoPlastic documentation describes 2*P*sin(phi).
# https://aspect.geodynamics.org/doc/doxygen/classaspect_1_1MaterialModel_1_1Rheology_1_1DruckerPrager.html
# https://aspect.geodynamics.org/doc/doxygen/classaspect_1_1MaterialModel_1_1ViscoPlastic.html
DRUCKER_PRAGER_PRESSURE_TERMS = {
    "ASPECT_RHEOLOGY_DP_3D_6P": 6.0,
    "ASPECT_LEGACY_VISCOPLASTIC_3D_2P": 2.0,
}


def need(ok, code):
    if not ok:
        raise ValueError(code)


def num(value, name, *, positive=False, minimum=None, maximum=None):
    try:
        x = float(value)
    except (TypeError, ValueError) as ex:
        raise ValueError("G2_VP_"+name+"_MISSING") from ex
    need(math.isfinite(x) and (not positive or x>0)
         and (minimum is None or x>=minimum)
         and (maximum is None or x<=maximum),
         "G2_VP_"+name+"_INVALID")
    return x


def layer_material(law, temperature_k, lith_pressure_pa, rate_s_inv):
    """Full documented creep and 3D Drucker-Prager pressure-aware cap.

    This yields a *continuum* yield stress, not a friction plane strength.
    Reference 3D DP formula follows ASPECT's viscoplastic material model.
    """
    need(isinstance(law,dict) and law.get("authority")==
         "ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
         "G2_VP_LAYER_AUTHORITY_NOT_RATIFIED")
    creep,brittle=law.get("ductile"),law.get("brittle")
    need(isinstance(creep,dict) and isinstance(brittle,dict),
         "G2_VP_TWO_MECHANISMS_REQUIRED")
    for mechanism in (creep,brittle):
        need(isinstance(mechanism.get("source_reference"),str)
             and len(mechanism["source_reference"].strip())>=10,
             "G2_VP_LITERATURE_PROVENANCE_REQUIRED")
    need(creep.get("stress_convention")==
         "ASPECT_2ETA_EPS_INVARIANT_SCALE" and
         brittle.get("criterion")=="DRUCKER_PRAGER_3D_CONTINUUM",
         "G2_VP_INVARIANT_OR_YIELD_CRITERION_UNSUPPORTED")
    A=num(creep.get("A_pa_minus_n_s_inv"),"A",positive=True)
    n=num(creep.get("n"),"N",minimum=1)
    E=num(creep.get("E_j_mol"),"E",minimum=0)
    V=num(creep.get("V_m3_mol"),"V",minimum=0)
    wr=num(creep.get("fugacity_exponent"),"WATER_EXPONENT",minimum=0)
    if wr>0:
        water=num(creep.get("water_fugacity_pa"),"FIELD_WATER",positive=True)
        ref=num(creep.get("reference_fugacity_pa"),"WATER_REFERENCE",positive=True)
        logA=math.log(A)+wr*math.log(water/ref)
    else:
        need(creep.get("water_fugacity_pa") is None and
             creep.get("reference_fugacity_pa") is None,
             "G2_VP_WATER_STATE_AMBIGUOUS")
        logA=math.log(A)
    tmin,tmax=bounds(creep,"valid_temperature_k")
    pmin,pmax=bounds(creep,"valid_pressure_pa")
    rmin,rmax=bounds(creep,"valid_strain_rate_s_inv")
    need(tmin<=np.min(temperature_k) and np.max(temperature_k)<=tmax
         and pmin<=np.min(lith_pressure_pa) and
         np.max(lith_pressure_pa)<=pmax
         and rmin<=rate_s_inv<=rmax,
         "G2_VP_CREEP_LAB_PT_RATE_OUTSIDE_VALIDITY")
    phi=math.radians(num(brittle.get("friction_angle_deg"),"PHI_DEG",
                         minimum=0,maximum=80))
    cohesion=num(brittle.get("cohesion_pa"),"COHESION",minimum=0)
    biot=num(brittle.get("biot_coefficient"),"BIOT",
             minimum=0,maximum=1)
    pore_ratio=num(brittle.get("pore_pressure_over_lithostatic"),
                   "PORE_PRESSURE_RATIO",minimum=0,maximum=1)
    p_eff=lith_pressure_pa*(1-biot*pore_ratio)
    need(np.all(p_eff>=0),"G2_VP_NEGATIVE_EFFECTIVE_PRESSURE")
    variant = brittle.get("drucker_prager_pressure_convention")
    need(variant in DRUCKER_PRAGER_PRESSURE_TERMS,
         "G2_VP_DP_PRESSURE_CONVENTION_UNDECLARED")
    pressure_term = DRUCKER_PRAGER_PRESSURE_TERMS[variant]
    yield_stress=(6*cohesion*math.cos(phi)+
                  pressure_term*p_eff*math.sin(phi))/(
        math.sqrt(3)*(3+math.sin(phi)))
    need(np.all(yield_stress>0),"G2_VP_ZERO_YIELD_STRESS")
    alpha=1.0/n
    logC=(-logA+(E+lith_pressure_pa*V)/(R_GAS*temperature_k))/n
    need(np.all(np.isfinite(logC)) and
         np.all(logC<700) and np.all(logC>-700),
         "G2_VP_CREEP_NUMERIC_RANGE_INVALID")
    return alpha,np.exp(logC),yield_stress


def radial_stress(rate,alpha,C,yield_stress):
    """Saturating monotone cap sigma_v*y/(sigma_v+y). Not exact DP return."""
    visc=C*np.power(rate,alpha)
    return visc*yield_stress/(visc+yield_stress)


def potential_gradient_tangent(pre,scenario,strain):
    """Consistent dPhi/de and d²Phi/de², with depth and log-rate quadrature.

    For epsilonII²=e.T Q e, r=sqrt(epsilonII²+floor²), sigma_v=C(z)r^alpha,
    sigma_eff=(1/sigma_v+1/y)^(-1), N=dPhi/de=2sigma_eff Qe/r.
    The analytic tangent is the derivative of that N and remains SPD.
    Different layer exponents n are supported without modifying SHELLS.
    """
    need(isinstance(scenario,dict) and
         scenario.get("authority")=="ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED"
         and isinstance(scenario.get("source_identifier"),str)
         and len(scenario["source_identifier"])>=10,
         "G2_VP_UNAUTHORIZED_SCENARIO")
    e=np.asarray(strain,dtype=float)
    need(e.shape==(3,) and np.all(np.isfinite(e)),
         "G2_VP_STRAIN_INVALID")
    floor=num(scenario.get("regularization_strain_rate_s_inv"),
              "RATE_FLOOR",positive=True)
    gravity=num(scenario.get("gravity_m_s2"),"GRAVITY",positive=True)
    rate=math.sqrt(max(0.0,float(e@Q@e)))
    r=math.hypot(rate,floor)
    order=scenario.get("gauss_points_per_layer")
    need(isinstance(order,int) and 4<=order<=48,
         "G2_VP_GAUSS_ORDER_MISSING")
    potential=0.0
    stress=np.zeros(3)
    tangent=np.zeros((3,3))
    layer_info=[]
    qe=Q@e
    z_nodes,z_weights=np.polynomial.legendre.leggauss(order)
    rate_nodes,rate_weights=np.polynomial.legendre.leggauss(24)
    # Integrate in log-rate, not linearly: r/floor can exceed 10^4.
    # This avoids an apparent mismatch between Phi and its exact gradient.
    logratio=math.log(r/floor)
    r_samples=floor*np.exp(0.5*logratio*(1+rate_nodes))
    for index,name in ((1,"crust"),(2,"mantle")):
        z0=num(pre.get(f"layer{index}_z0_m"),"LAYER_TOP",minimum=0)
        z1=num(pre.get(f"layer{index}_z1_m"),"LAYER_BOTTOM",positive=True)
        need(z1>z0,"G2_VP_LAYER_DEPTH_INVALID")
        z=z0+0.5*(z1-z0)*(1+z_nodes)
        weights=z_weights*(z1-z0)/2
        T=temperature_k(pre,index,z)
        P=overburden_pa(pre,gravity,z)
        need(np.all(np.isfinite(T)) and np.all(T>0)
             and np.all(np.isfinite(P)) and np.all(P>=0),
             "G2_VP_PRE_TP_INVALID")
        layers=scenario.get("layers")
        need(isinstance(layers,dict) and isinstance(layers.get(name),dict),
             "G2_VP_LAYER_LAW_MISSING")
        # Gauss nodes alone cannot certify the cubic PRE laboratory T domain.
        require_laboratory_temperature_coverage(pre,index,layers[name]["ductile"])
        alpha,C,y=layer_material(layers[name],T,P,r)
        sv=C*r**alpha
        sigma=sv*y/(sv+y)
        sigma_prime=alpha*sv/r*(y/(sv+y))**2
        scale=2*sigma/r
        stress+=(weights@scale)*qe
        tangent+=((weights@scale)*Q+
                  (weights@(2*(sigma_prime*r-sigma)/r**3))*
                  np.outer(qe,qe))
        samples=radial_stress(r_samples[None,:],alpha,
                              C[:,None],y[:,None])
        potential+=float(weights@(logratio*((samples*r_samples)@
                                             rate_weights)))
        layer_info.append({
            "name":name,"n":1/alpha,
            "T_min_max_K":[float(T.min()),float(T.max())],
            "P_min_max_Pa":[float(P.min()),float(P.max())],
            "effective_3D_DP_yield_min_max_Pa":
                [float(y.min()),float(y.max())],
            "creep_only_stress_min_max_Pa":
                [float(sv.min()),float(sv.max())]})
    tangent=0.5*(tangent+tangent.T)
    need(math.isfinite(potential) and potential>=0
         and np.all(np.isfinite(stress))
         and np.all(np.isfinite(tangent))
         and np.min(np.linalg.eigvalsh(tangent))>0,
         "G2_VP_TANGENT_OR_POTENTIAL_INVALID")
    return {
        "status":STATUS,"potential_N_per_m_s":potential,
        "stress_resultant_N_per_m":stress,
        "tangent_N_s_per_m":tangent,"layers":layer_info,
        "rms_3D_deviatoric_rate_s_inv":rate,
        "smooth_cap_not_ideal_Drucker_Prager_plasticity":True,
        "temperature_coverage_authorial_qualified":False,
        "water_pore_pressure_from_source_PRE":False,
        "physical_material_G2_authorized":False,
        "ShellSet_Diamnd_Mohr_OneBar_parity":False,
        "mechanical_solve_authorized":False,"physical_T1":None}
