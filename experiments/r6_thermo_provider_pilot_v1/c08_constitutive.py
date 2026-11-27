"""Depth-resolved, offline comparison of partial T0 analogue envelopes."""
import math

import numpy as np

from arcana_worldsim.r6.material_rheology_provider import DEFAULT_BENCHMARK
from experiments.plate58_deforming_explore_v1 import full_column as column
from experiments.plate58_deforming_explore_v1 import rheology_envelope as sources
from experiments.plate58_deforming_explore_v1 import shells_lr_bridge as lr
from experiments.plate58_deforming_explore_v1.wet_quartz_screen import WET_EXP_TEMPERATURE_WINDOW_K

# Predeclared sensitivity band. 1373 K and 1.8 GPa are anchored to the
# Dixon--Durham pressure series. Extending across T and geological rates
# is a conditional high-temperature mechanism screen, not joint lab support.
WARM_T = (1373., 1673.15)
WARM_P = (1.8e9, 8.8e9)
V_CASES = (10e-6, 14e-6, 20e-6)
PRESSURE_MAX = 1.7e9
FINE = 256
QUARTZ_E = 1 / sources.GT_N
OLIVINE_E = 1 / DEFAULT_BENCHMARK.stress_exponent


def law_mantle(rates, volume):
    b = DEFAULT_BENCHMARK
    return {
        "A_pa_minus_n_s_inv": b.prefactor_pa_n_s, "n": b.stress_exponent,
        "E_j_mol": b.activation_energy_j_mol, "V_m3_mol": volume,
        "stress_convention": "ASPECT_2ETA_EPS_INVARIANT_SCALE",
        "source_reference": "HK03 ASPECT dry benchmark; Dixon-Durham V alternative",
        "fugacity_exponent": 0, "water_fugacity_pa": None, "reference_fugacity_pa": None,
        "invariant_to_friction_shear_factor": 1.,
        "shear_conversion_reference": "Report raw sigma_II; equals |tau| in pure simple shear",
        "valid_temperature_k": list(WARM_T), "valid_pressure_pa": list(WARM_P),
        "valid_strain_rate_s_inv": [min(rates), max(rates)],
    }


def friction_policy(pore_ratio):
    return {"source_reference": "BYERLEE_1978_REFERENCE__NOT_R6_MATERIAL",
            "normal_stress_over_lithostatic": 1., "biot_coefficient": 1.,
            "pore_pressure_over_lithostatic": pore_ratio,
            "valid_effective_normal_pressure_pa": [0., PRESSURE_MAX]}


def summary(values):
    if not len(values):
        return None
    return dict(zip(("min", "p05", "median", "p95", "max"),
                    np.quantile(values, [0., .05, .5, .95, 1.]).tolist(), strict=True))


def integrate(depth, stress):
    """Integrate one contiguous eligible interval in Pa m."""
    column.need(len(depth) == len(stress) and len(depth) >= 2
                and np.all(np.diff(depth) > 0) and np.all(np.isfinite(stress))
                and np.all(stress >= 0), "C08_INTEGRAL_INPUT")
    return float(np.trapezoid(stress, depth))


def thermal_segments(pre, layer, t_bounds, p_bounds, gravity):
    """Clip at original material interfaces and all T/P crossings."""
    tag = f"layer{layer}_"
    start, stop = (pre[tag + key] for key in ("z0_m", "z1_m"))
    thick = stop - start
    coeff = [pre[tag + f"c{k}_" + ("k" if k == 0 else "k_m" if k == 1 else f"k_m{k}")]
             * thick**k for k in range(4)]
    knots = {0., 1.}
    for bound in t_bounds:
        roots = np.polynomial.polynomial.polyroots([coeff[0] - bound, *coeff[1:]])
        knots.update(float(q.real) for q in roots if abs(q.imag) < 1e-10 and 0 < q.real < 1)
    p0, p1 = column.overburden_pa(pre, gravity, np.asarray([start, stop]))
    knots.update((p-p0)/(p1-p0) for p in p_bounds if p0 < p < p1)
    intervals = []
    for a, b in zip(sorted(knots)[:-1], sorted(knots)[1:], strict=True):
        mid = (a+b)/2
        t = np.polynomial.polynomial.polyval(mid, coeff)
        p = p0 + (p1-p0)*mid
        ok = t_bounds[0] <= t <= t_bounds[1] and p_bounds[0] <= p <= p_bounds[1]
        if intervals and intervals[-1][2] == bool(ok):
            intervals[-1][1] = start + b*thick
        else:
            intervals.append([start + a*thick, start + b*thick, bool(ok)])
    return intervals


def grid(start, stop, extras=()):
    return np.unique(np.r_[np.linspace(start, stop, FINE+1),
                           [z for z in extras if start < z < stop]])


def common_coefficient(lr_row, common_e, pivot):
    return lr_row["aCreep_candidate_pa_s_to_e"] * pivot**(lr_row["eCreep_candidate"] - common_e)


def invariant_prefactor(axial_A_mpa_minus_n, n):
    """Incompressible uniaxial experiment: epsII=sqrt(3)/2*eps_axial,
    sigmaII=delta_sigma/sqrt(3). Convert MPa to Pa before refitting units.
    """
    return math.sqrt(3)/2 * axial_A_mpa_minus_n * (math.sqrt(3)/1e6)**n


def diamnd_a(lr_row, common_e, pivot):
    # Diamnd uses 2*sqrt(J2), while the reference rate is sqrt(J2).
    return 2**(1-common_e) * common_coefficient(lr_row, common_e, pivot)


def raw_native_stress(lr_row, common_e, pivot, rate, t, z):
    a = diamnd_a(lr_row, common_e, pivot)
    b = lr_row["bCreep_candidate_kelvin"]
    c = lr_row["cCreep_candidate_kelvin_per_m"]
    vis = .5*a*(2*rate)**(common_e-1)*np.exp((b+c*z)/t)
    return 2*rate*vis


def clipped_values(values, bounds):
    # Only snap computed crossing endpoints within ordinary roundoff.
    lo, hi = bounds
    slack = 64*np.finfo(float).eps*max(1., abs(lo), abs(hi))
    column.need(np.all((values >= lo-slack)&(values <= hi+slack)), "C08_CLIPPING_DOMAIN")
    return np.clip(values, lo, hi)


def mantle_segment(pre, gravity, a, b, rates, holdout_rates, variants, pivot):
    z = grid(a, b)
    t = clipped_values(column.temperature_k(pre, 2, z), WARM_T)
    p = clipped_values(column.overburden_pa(pre, gravity, z), WARM_P)
    laws = {v: law_mantle(rates.values(), v) for v in V_CASES}
    coeff = lr._coefficients(pre, {"layers": {"mantle": {"ductile": laws[14e-6]}}},
                             "mantle", gravity)
    runs = {}
    tested_rates = {**rates, **holdout_rates}
    for key, rate in tested_rates.items():
        stresses = {str(v): column.flow_stress_pa(law, t, p, rate)
                    for v, law in laws.items()}
        reference = stresses[str(14e-6)]
        recovered = raw_native_stress(coeff, OLIVINE_E, pivot, rate, t, z)
        column.need(np.allclose(recovered, reference, rtol=2e-13, atol=0.),
                    "C08_NATIVE_FORM_BRIDGE_DRIFT")
        integrated = integrate(z, reference)
        runs[key] = {
            "stress_pa_by_activation_volume_m3_mol": {v: s.tolist() for v,s in stresses.items()},
            "integrated_pa_m_by_activation_volume_m3_mol": {
                v: integrate(z,s) for v,s in stresses.items()},
            "fine_vs_half_grid_fraction": abs(integrated-integrate(z[::2], reference[::2])) / integrated,
            "native_form_comparison": {},
            "pure_shear_cap_threshold_dCreep_Pa": summary(reference),
            "pure_shear_uncapped_viscosity_Pa_s": summary(reference/(2*rate)),
            "eligible_band_mean_viscosity_Pa_s": integrated/((b-a)*2*rate),
        }
        for name, e in variants.items():
            native = raw_native_stress(coeff, e, pivot, rate, t, z)
            runs[key]["native_form_comparison"][name] = {
                "native_stress_pa": native.tolist(),
                "signed_stress_difference_pa": (native-reference).tolist(),
                "relative_depth_error": summary(native/reference - 1),
                "log_stress_error": summary(np.log(native/reference)),
                "native_integral_pa_m": integrate(z,native),
                "separate_integral_pa_m": integrated,
                "relative_integrated_error": integrate(z,native)/integrated-1,
            }
    return {"depth_m": z.tolist(), "temperature_K": t.tolist(), "overburden_proxy_Pa": p.tolist(),
            "raw_reference_LR": coeff,
            "Diamnd_aCreep_Pa_s_to_e": {k:diamnd_a(coeff, e, pivot) for k,e in variants.items()},
            "rate_cases": runs}


def assess_columns(profiles, kinematic_rates, gravity, rho_water, scope):
    """Build actual source profiles, plus explicitly bounded analogue branches."""
    rates = {k: float(v) for k,v in kinematic_rates.items()}
    lo, hi = min(rates.values()), max(rates.values())
    pivot = math.sqrt(lo*hi)
    holdout = {f"log_holdout_{i}": math.exp((1-i/4)*math.log(lo)+(i/4)*math.log(hi))
               for i in (1,3)}
    variants = {"crust_slope": QUARTZ_E, "joint_slope_minimax": (QUARTZ_E+OLIVINE_E)/2,
                "mantle_slope": OLIVINE_E}
    nodes, curves = {}, {}
    for parent, pre in profiles.items():
        moho = pre["layer1_z1_m"]
        base = pre["layer2_z1_m"]
        thick = pre["mantle_lithosphere_thickness_m"]
        column.need(pre["layer1_z0_m"] == 0. and pre["layer2_z0_m"] == moho
                    and pre["crust_thickness_m"] == moho and base == moho+thick,
                    "C08_PRE_LAYER_IDENTITY")
        pt = {}
        for layer, label in ((1,"crust"),(2,"mantle")):
            z = grid(pre[f"layer{layer}_z0_m"], pre[f"layer{layer}_z1_m"])
            pt[label] = {"depth_m": z.tolist(),
                         "temperature_K": column.temperature_k(pre,layer,z).tolist(),
                         "overburden_proxy_Pa": column.overburden_pa(pre,gravity,z).tolist()}
        bhq = thermal_segments(pre, 1, sources.GT_LAB_TEMP_K, (0., math.inf), gravity)
        wet = thermal_segments(pre, 1, WET_EXP_TEMPERATURE_WINDOW_K, (0., math.inf), gravity)
        mantle = thermal_segments(pre, 2, WARM_T, WARM_P, gravity)
        brittle = {}
        for label, pore_ratio in (("dry_sliding", 0.), ("hydrostatic_sliding", rho_water/pre["crust_density_kg_m3"])):
            policy = friction_policy(pore_ratio)
            crossover = column.BYERLEE_TRANSITION_PA/(1-pore_ratio)/(gravity*pre["crust_density_kg_m3"])
            z = grid(0, moho, [crossover])
            p = column.overburden_pa(pre,gravity,z)
            tau = column.brittle_shear_pa(p, policy)
            brittle[label] = {"depth_m": z.tolist(), "shear_Pa":tau.tolist(), "policy":policy,
                              "integrated_crust_sliding_envelope_N_m": integrate(z,tau),
                              "transition_200MPa_depth_m": crossover if crossover < moho else None}
        nodes[parent] = {"layers": pt, "BHQ_temperature_window_intervals":bhq,
                         "wet_quartz_temperature_window_intervals":wet,
                         "dry_olivine_analogue_TP_intervals":mantle,
                         "complete_mechanism_columns_supported":False}
        curves[parent] = {"brittle_crust_conditional":brittle, "crust_ductile_integral_N_m":None,
                         "mantle_partial": [mantle_segment(pre, gravity, a,b,rates,holdout,variants,pivot)
                                            for a,b,eligible in mantle if eligible],
                         "mantle_whole_layer_integral_N_m":None, "total_lithosphere_integral_N_m":None}

    # The eligible products do not fill the unsupported layer intervals.
    results = [piece for node in curves.values() for piece in node["mantle_partial"]]
    summaries = {}
    for key in {**rates, **holdout}:
        samples = [r["rate_cases"][key] for r in results]
        summaries[key] = {
            "integrated_analogue_mantle_N_m": {
                str(v): summary([r["integrated_pa_m_by_activation_volume_m3_mol"][str(v)] for r in samples])
                for v in V_CASES},
            "relative_integral_error": {name:summary([
                r["native_form_comparison"][name]["relative_integrated_error"] for r in samples
            ]) for name in variants},
            "max_abs_depth_fractional_error": {name:max((
                abs(r["native_form_comparison"][name]["relative_depth_error"][q])
                for r in samples for q in ("min","max")), default=None) for name in variants},
            "pointwise_log_error_distribution": {name: summary(np.concatenate([
                np.log(np.asarray(r["native_form_comparison"][name]["native_stress_pa"]) /
                       np.asarray(r["stress_pa_by_activation_volume_m3_mol"][str(14e-6)]))
                for r in samples]) if samples else []) for name in variants},
            "max_half_grid_delta": max((r["fine_vs_half_grid_fraction"] for r in samples), default=None),
            "dCreep_binding_threshold_Pa_for_pure_shear": summary([
                val for r in samples for val in r["pure_shear_cap_threshold_dCreep_Pa"].values()]),
            "visMax_analogue_band_mean_viscosity_Pa_s": summary([
                r["eligible_band_mean_viscosity_Pa_s"] for r in samples]),
            "actual_full_creeping_interval_cap_activation":None,
        }
    return (
        {"nodes":nodes, "gravity_m_s2":gravity,
         "P_meaning":"Piecewise reference-density overburden sensitivity; absolute and effective P unassigned",
         "rates_s_inv":rates, "rates_meaning":"T0 opening divided by alternative widths; kinematic priors",
         "BHQ_eligible_depth_interval_count":sum(sum(w for _,_,w in n["BHQ_temperature_window_intervals"]) for n in nodes.values()),
         "wet_quartz_nodes_with_temperature_eligible_interval":sum(any(w for _,_,w in n["wet_quartz_temperature_window_intervals"]) for n in nodes.values()),
         "mantle_nodes_with_analogue_interval":sum(bool(n["mantle_partial"]) for n in curves.values()),
         "mantle_analogue_eligible_thickness_m": summary([
             sum(b-a for a,b,w in n["dry_olivine_analogue_TP_intervals"] if w) for n in nodes.values()]), **scope},
        {"nodes":curves, "finite_conditional_crust_sliding_integrals_N_m":{
            mode:summary([n["brittle_crust_conditional"][mode]["integrated_crust_sliding_envelope_N_m"]
                          for n in curves.values()]) for mode in ("dry_sliding","hydrostatic_sliding")},
         "friction_and_creep_overlap_applicable":False,
         "branch_policy":"A candidate lower envelope needs a common shear convention, shared mechanism support, and a transition model. Present branches are separate. Cold crust mechanism and transition unbound.",
         "normal_model":"sigma_n = reference overburden, Biot = 1 for the sensitivity only",
         "hydrostatic_water_reference_kg_m3":rho_water,
         "pressure_and_fugacity":{"field_pore_pressure":None, "water_fugacity_Pa":None, "bulk_water":None},
         "selected":{"cFric":None,"fFric":None,"Byerly":None,"Biot":None,"dCreep":None,"visMax":None}, **scope},
        {"fit_objective":"Minimax absolute log error of two nominal slopes on log-rate interval with exact pivot match; coefficients scaled via LR. Mantle-only evaluated in regional band.",
         "common_e_candidates":variants, "pivot_rate_s_inv":pivot,
         "midpoint_log_minimax_error_over_both_nominal_laws":
             (OLIVINE_E-QUARTZ_E)/2 * math.log(hi/pivot),
         "empirical_fit":None,"empirical_holdout":None,
         "numerical_held_out_rate_samples_s_inv":holdout,
         "identifiability":"At fixed T/P support, each power-law integral factors into rate^e times depth integral. Pivot alone cannot identify e. Supported mantle values cannot identify crust coefficients or a regional joint physical loss.",
         "rates":summaries,"accepted_error_threshold":None,
         "acceptance_requires":"Tie permitted integrated stress error to reaction, work and strain tolerances in a later physically closed problem.",
         "native_Diamnd_full_tensor_evaluated":False, **scope},
    )


def integration_point_thermal(root, index, profiles, provenance):
    """Report native barycentric temperature at projected interfaces within PRE support."""
    import re

    src = root/"external/ShellSet-v1.1.0/src/MOD_SharedVars.f90"
    constants = src.read_text().split("data points /",1)[1].split("/",1)[0]
    points = np.asarray([float(x) for x in re.findall(r"([\d.]+)D0",constants)]).reshape(7,3)
    column.need(np.all(points>=0) and np.allclose(points.sum(axis=1),1,rtol=0,atol=3e-15),
                "C08_NATIVE_POINTS_INVALID")
    results = {}
    for key, ids in index["source_original_full_basal_triangle_nodes"].items():
        local = [profiles[str(parent)] for parent in ids]
        rows = []
        for weights in points:
            moho = float(weights @ [row["crust_thickness_m"] for row in local])
            thermal_lab = float(weights @ [row["layer2_z1_m"] for row in local])
            temp = []
            phases = []
            for pre in local:
                layer = 1 if moho < pre["layer1_z1_m"] else 2
                t = column.temperature_k(pre, layer, np.asarray([moho]))[0]
                phases.append("PRE_CRUST" if layer==1 else "PRE_MANTLE")
                temp.append(float(t))
            rows.append({"weighted_Moho_m":moho,"weighted_thermal_LAB_m":thermal_lab,
                         "PRE_phases_at_weighted_Moho":phases,
                         "projected_temperature_at_weighted_Moho_K":float(weights @ temp)})
        results[key] = {"parents":ids, "integration_points_in_native_order":rows}
    return {"native_points":points.tolist(),"triangle_count":len(results),
            "projected_moho_points":7*len(results),"weights_source":provenance(src),
            "phase_mixed_at_projected_moho_count":sum(
                len(set(row["PRE_phases_at_weighted_Moho"]))>1 for rec in results.values()
                for row in rec["integration_points_in_native_order"]),
            "meaning":"Evaluate each source PRE polynomial at common geometric depth, then weight. No lithology or density assignment at integration points.",
            "triangles":results}
