"""Whole-column diagnostic envelopes for explicit synthetic hypotheses."""
import math

import numpy as np

from experiments.plate58_deforming_explore_v1 import full_column
from experiments.r6_thermo_provider_pilot_v1 import c08_constitutive as c08

COMMON_E = 15/56
# Geometric pivot of the retained opening/width rate interval.
DEPTH_INTERVALS = 256
FAMILY = "PROPOSED_SYNTHETIC_INITIAL_HYPOTHESIS"
EARTH_REFERENCE = "external/ShellSet-v1.1.0/INPUT/iEarth5-049.in"
EARTH_SHA = "c07834e17d9c6e21bad0d7cd81af20e8a670e0ae9ed481f999c881129ee4a89e"


def legacy_lr(path):
    lines = [x.split()[0] for x in path.read_text().splitlines()[1:10]]
    f, c, biot, byerly, *creep = lines
    pairs = [list(map(float, x.split(","))) for x in creep[:4]]
    return {"A_Pa_s_to_e":pairs[0],"B_K":pairs[1],"C_K_per_m":pairs[2],
            "dCreep_Pa":pairs[3],"eCreep":float(creep[4]),
            "cFric":float(c),"Biot_hydrostatic":float(biot),
            "unused_fFric_source":float(f),"unused_Byerly_source":float(byerly)}


def model_catalog(root, sha):
    p = root/EARTH_REFERENCE
    full_column.need(sha(p)==EARTH_SHA,"C09_LEGACY_LR_SHA")
    old = legacy_lr(p)
    modern = {"A_Pa_s_to_e":[1.38e6,2.23e4],"B_K":[10524.,16494.],
              "C_K_per_m":[.0079,.0104],"dCreep_Pa":[5e8,5e8],
              "eCreep":.267,"cFric":.85,"Biot_hydrostatic":1.}
    modern["cap_authority"] = "Section 2, Eq. 1 uses 500 MPa per layer; Sec. 5.1 gives B/C/e and Table 1 Diorite2 changes the two prefactors."
    yu = {"dislocation_by_role":{
            "wet_quartzite":[8.57e-28,4.,223e3,0.],
            "wet_anorthite":[7.13e-18,3.,345e3,0.],
            "dry_olivine":[6.52e-16,3.5,530e3,18e-6]},
          "mantle_diffusion_A_Pa_inv_s_inv_before_grain_factor":2.37e-15,
          "mantle_diffusion_E_J_mol":375e3,"mantle_diffusion_V_m3_mol":10e-6,
          "mantle_grain_size_m":.005,"mantle_grain_exponent":3,
          "initial_cohesion_Pa":20e6,"initial_friction_angle_deg":30.,
          "published_weakened_cohesion_Pa":10e6,"published_weakened_friction_angle_deg":15.,
          "activity":"Intact initial strengths; no inherited fault seed or strain weakening transferred.",
          "crust_assignment_options":["homogeneous quartzite analogue","upper half quartzite analogue and lower half anorthite analogue"],
          "layer_geometry_authority":"Half the PRE crust is an explicit synthetic choice adapting published 20+20 km. Mantle and thermal geometry stay PRE.",
          "water":"Wet calibration for crustal material constants, dry calibration for mantle. No regional dissolved water, fugacity, or pore pressure inferred.",
          "diffusion_units_note":"Table 1 labels A_diff Pa^-1 s^-1; Eq.14 uses d numerically in metres with implicit grain-size units in its prefactor.",
          "reference_rate_s_inv":1e-15}
    return {"native_legacy":old,"native_diorite2":modern,"layered_yu_initial":yu,
            "retained_C08_eCreep":COMMON_E,
            "source_records":[
                {"doi":"10.5194/gmd-17-6153-2024","use":"ShellSet v1.1.0 and Earth5-049; published CC BY 4.0",
                 "local_example_sha256":EARTH_SHA,"local_user_guide_sha256":sha(root/"external/ShellSet-v1.1.0/DOCS/User Guide.pdf")},
                {"doi":"10.5281/zenodo.7986808","use":"Reproducibility link from GMD. Remote returned HTTP 429; pinned local LR used."},
                {"doi":"10.1029/2001JB001544","use":"Section 2 A/B/C, n=3, cFric=.85 and hydrostatic condition; older 3-mechanism regional study. Legacy cap from local LR."},
                {"doi":"10.1029/2025JB032949","use":"Sections 5.1/5.2, Table 1 and Eq.1; adjusted CRM then Diorite2 prefactors. No tectonic fields transferred."},
                {"doi":"10.1029/2018TC005346","use":"Table 1 and Figure S2; lower crust quartzite/anorthite/granulite endmembers.",
                 "log10_A_dis_Pa_minus_n_s_inv":[-28.,-15.40,-21.05,-15.96,-15.81],
                 "n":[4.,3.,4.2,3.5,3.5],"E_kJ_mol":[223,356,445,530,480],
                 "V_cm3_mol":[0,0,0,13,10]},
                {"doi":"10.1029/2022TC007659","use":"Published fault-network scope consulted. Used to assess plausibility of fault-network growth as a later benchmark. The available study text supplies no authorized ARCANA fault geometry."},
                {"doi":"10.1029/2024JB030041","use":"Table 1 and Eq.12–18; parameters only for initial diagnostic.",
                 "reproducibility_doi":"10.5281/zenodo.14847235"}],
            "uncertainty_scope":"Compare published structural analogues and named atmosphere/pore sensitivities. No probability or parameter covariance inferred.",
            "full_column_authority":FAMILY,"experimental_validation":False}


def pressure(pre, depth, gravity, alpha):
    """Integrate source reference density with one 1-alpha*T correction."""
    z = np.asarray(depth)
    p = np.zeros_like(z,dtype=float)
    for layer,name in ((1,"crust"),(2,"mantle")):
        prefix = f"layer{layer}_"
        d = np.clip(z-pre[prefix+"z0_m"],0,pre[prefix+"z1_m"]-pre[prefix+"z0_m"])
        integral_t = sum(pre[prefix+key]*d**(i+1)/(i+1) for i,key in
                         enumerate(("c0_k","c1_k_m","c2_k_m2","c3_k_m3")))
        p += gravity*pre[name+"_density_kg_m3"]*(d-alpha[name]*integral_t)
    return p


def native_components(model, layer, z, t, p_eff, rate, e, pivot):
    # sqrt(J2) is the input rate. Diamnd uses twice that value in viscosity.
    e_original = model["eCreep"]
    a = model["A_Pa_s_to_e"][layer]*(2*pivot)**(e_original-e)
    stress = .5*a*(2*rate)**e*np.exp((model["B_K"][layer]+model["C_K_per_m"][layer]*z)/t)
    plastic = math.sin(math.atan(model["cFric"]))*p_eff
    return stress, plastic, model["dCreep_Pa"][layer]


def composite_stress(dislocation, diffusion, exponent):
    """Invert summed rates at one stress, in normalized units."""
    if diffusion is None:
        return dislocation
    upper = np.minimum(dislocation,diffusion)
    disl_weight = (upper/dislocation)**exponent
    diff_weight = upper/diffusion
    lo, hi = np.zeros_like(upper), np.ones_like(upper)
    for _ in range(40):
        middle = (lo+hi)*.5
        left = disl_weight*middle**exponent + diff_weight*middle <= 1.
        lo = np.where(left,middle,lo)
        hi = np.where(left,hi,middle)
    return upper*(lo+hi)*.5


def layered_components(model, role, t, p, p_eff, rate, common, pivot):
    A,n,E,V = model["dislocation_by_role"][role]
    e = 1/n
    R = full_column.R_GAS
    dislocation = np.exp((math.log(rate/A)+(E+V*p)/(R*t))/n)
    if common:
        dislocation *= (rate/pivot)**(COMMON_E-e)
        n = 1/COMMON_E
    diffusion = None
    if role=="dry_olivine":
        diffusion = (rate/model["mantle_diffusion_A_Pa_inv_s_inv_before_grain_factor"]
                     *model["mantle_grain_size_m"]**model["mantle_grain_exponent"]
                     *np.exp((model["mantle_diffusion_E_J_mol"]+
                              p*model["mantle_diffusion_V_m3_mol"])/(R*t)))
    creep = composite_stress(dislocation,diffusion,n)
    angle = math.radians(model["initial_friction_angle_deg"])
    plastic = model["initial_cohesion_Pa"]*math.cos(angle) + p_eff*math.sin(angle)
    activity = np.full(t.shape, "dislocation", dtype="<U16")
    if diffusion is not None:
        activity[creep/diffusion>.5] = "diffusion"
    return creep, plastic, activity


def summarize_curve(z, creep, brittle, cap, activity):
    stress = np.minimum(np.minimum(creep,cap),brittle)
    labels = np.where(brittle<=np.minimum(creep,cap),"brittle",
                      np.where(cap<=creep,"physical_cap",activity))
    signed = np.minimum(creep,cap)-brittle
    flips = np.flatnonzero((signed[:-1]>0)!=(signed[1:]>0))
    crossings = [float(z[i]+(z[i+1]-z[i])*signed[i]/(signed[i]-signed[i+1])) for i in flips]
    return stress, labels, crossings


def column_runs(pre, models, rate, pivot, gravity, rho_water, alpha, mode, detail, *, surface_delta=0.):
    moho, bottom = pre["layer1_z1_m"],pre["layer2_z1_m"]
    cases = ["native_legacy","native_diorite2",
             "layered_homogeneous","layered_two_crust"]
    rows = {}
    for case in cases:
        layered = case.startswith("layered")
        segments = [(0.,moho,1,"wet_quartzite"),(moho,bottom,2,"dry_olivine")]
        if case=="layered_two_crust":
            segments[:1] = [(0.,moho/2,1,"wet_quartzite"),(moho/2,moho,1,"wet_anorthite")]
        base_strength, approx_strength, coarse_strength = (np.zeros(2) for _ in range(3))
        curves = []
        max_local, max_log = 0.,0.
        for a,b,layer,role in segments:
            z = np.linspace(a,b,DEPTH_INTERVALS+1)
            t = full_column.temperature_k(pre,layer,z) + surface_delta*(1-z/bottom)
            p = pressure(pre,z,gravity,alpha)
            if surface_delta:
                # Integral of the prescribed taper, not a thermal evolution.
                for which,name in ((1,"crust"),(2,"mantle")):
                    start = pre[f"layer{which}_z0_m"]
                    end = np.clip(z,start,pre[f"layer{which}_z1_m"])
                    delta_int = surface_delta*(end-start)*(1-(end+start)/(2*bottom))
                    p -= gravity*pre[name+"_density_kg_m3"]*alpha[name]*delta_int
            full_column.need(np.all(t>0) and np.all(p>=0),"C09_SENSITIVITY_THERMAL_STATE")
            eff = p - (rho_water*gravity*z if mode=="hydrostatic" else 0.)
            full_column.need(np.all(eff>=0),"C09_EFFECTIVE_PRESSURE_NEGATIVE")
            if layered:
                model = models["layered_yu_initial"]
                creep, brittle, activity = layered_components(model,role,t,p,eff,rate,False,pivot)
                approx, _, common_activity = layered_components(model,role,t,p,eff,rate,True,pivot)
                cap = math.inf
            else:
                model = models[case]
                creep,brittle,cap = native_components(model,layer-1,z,t,eff,rate,model["eCreep"],pivot)
                approx,_,_ = native_components(model,layer-1,z,t,eff,rate,COMMON_E,pivot)
                activity = common_activity = "dislocation"
            stress, tags, crossings = summarize_curve(z,creep,brittle,cap,activity)
            common, _, _ = summarize_curve(z,approx,brittle,cap,common_activity)
            differences = np.log(common[stress>0]/stress[stress>0])
            max_local = max(max_local,float(np.max(np.abs(np.expm1(differences)))))
            max_log = max(max_log,float(np.max(np.abs(differences))))
            base_strength[layer-1] += c08.integrate(z,stress)
            approx_strength[layer-1] += c08.integrate(z,common)
            coarse_strength[layer-1] += c08.integrate(z[::2],stress[::2])
            curve = {"support_m":[a,b],"material_role":role if layered else ("effective_crust" if layer==1 else "effective_mantle"),
                     "min_max_invariant_Pa":[float(np.min(stress)),float(np.max(stress))],
                     "transition_depths_m":crossings,
                     "mechanism_samples":{k:int(np.count_nonzero(tags==k)) for k in sorted(set(tags))}}
            if detail:
                curve |= {"depth_m":z.tolist(),"temperature_K":t.tolist(),
                          "lithostatic_proxy_Pa":p.tolist(),"effective_pressure_proxy_Pa":eff.tolist(),
                          "invariant_stress_Pa":stress.tolist(),"common_e_stress_Pa":common.tolist(),
                          "effective_viscosity_Pa_s":(stress/(2*rate)).tolist(),"mechanism":tags.tolist()}
            curves.append(curve)
        total = float(base_strength.sum())
        rows[case] = {"layers_N_m":base_strength.tolist(),"total_N_m":total,"curves":curves,
                      "relative_128_vs_256":float(abs(coarse_strength.sum()-total)/total),
                      "common_e_layers_N_m":approx_strength.tolist(),
                      "common_e_relative_layer_errors":(approx_strength/base_strength-1).tolist(),
                      "common_e_relative_total_error":float(approx_strength.sum()/total-1),
                      "max_local_stress_and_viscosity_relative_error":max_local,"max_local_log_error":max_log}
    return rows


def assess(pre_rows, models, rates, gravity, rho_water, surface_range, alpha_ranges):
    pivot = math.sqrt(min(rates.values())*max(rates.values()))
    detail = {}
    bins = {}
    for name,rate in rates.items():
        for water in ("dry","hydrostatic"):
            key = f"{name}km_{water}"
            records = {parent:column_runs(pre,models,rate,pivot,gravity,rho_water,
                        {"crust":pre["crust_expansivity_k_1"],"mantle":pre["mantle_expansivity_k_1"]},
                        water, name=="100") for parent,pre in pre_rows.items()}
            detail[key] = records
            bins[key] = {}
            for case in next(iter(records.values())):
                values = [r[case] for r in records.values()]
                bins[key][case] = {
                    "total_N_m":c08.summary([r["total_N_m"] for r in values]),
                    "crust_N_m":c08.summary([r["layers_N_m"][0] for r in values]),
                    "mantle_N_m":c08.summary([r["layers_N_m"][1] for r in values]),
                    "max_128_vs_256":max(r["relative_128_vs_256"] for r in values),
                    "common_e_total_relative_error":c08.summary([r["common_e_relative_total_error"] for r in values]),
                    "common_e_max_depth_relative_error":max(r["max_local_stress_and_viscosity_relative_error"] for r in values),
                }
    sensitivities = {}
    reference = detail["100km_hydrostatic"]
    for label in ("cool_surface","warm_surface","low_expansivity","high_expansivity"):
        sample = {case:[] for case in next(iter(reference.values()))}
        for parent,pre in pre_rows.items():
            alpha = {name:pre[name+"_expansivity_k_1"] for name in ("crust","mantle")}
            delta = 0.
            if label.endswith("surface"):
                delta = surface_range[label=="warm_surface"]-pre["layer1_c0_k"]
            else:
                alpha = {name:bounds[label=="high_expansivity"] for name,bounds in alpha_ranges.items()}
            rows = column_runs(pre,models,rates["100"],pivot,gravity,rho_water,alpha,
                               "hydrostatic",False,surface_delta=delta)
            for case,value in rows.items():
                sample[case].append(value["total_N_m"]/reference[parent][case]["total_N_m"]-1)
        sensitivities[label] = {case:c08.summary(v) for case,v in sample.items()}
    return detail,bins,pivot,{
        "fractional_change_total_column_strength":sensitivities,
        "scope":"Paired 100 km hydrostatic sensitivity. Surface endpoints use a prescribed linear taper to unchanged thermal LAB, not a regenerated PRE thermal history. Alpha endpoints change only reference-density overburden.",
        "surface_endpoints_K":surface_range,"expansivity_endpoints_K_inv":alpha_ranges}
