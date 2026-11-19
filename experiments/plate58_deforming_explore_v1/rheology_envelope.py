"""Source-bound laboratory proxy vs T0 PRE G2 envelope — no constitutive authorization.

Evaluates two explicitly *noncanonical* laboratory benchmarks against the
actual nine T0 PRE columns and the three *kinematic-only* opening/width scales.
Nothing here assigns pore water, friction, shellset LR data, traction, or T1.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from experiments.plate58_deforming_explore_v1.check import verify as verify_stage
from experiments.plate58_deforming_explore_v1.prepare import (
    PRE, ROOT, SECONDS_YEAR, _json, require, sha,
)
from arcana_worldsim.r6.material_rheology_provider import (DEFAULT_BENCHMARK, evaluate_dislocation_creep)

STATUS = "PASS_G2_SOURCE_PT_PROXY_SENSITIVITY__NO_CONSTITUTIVE_CLOSURE"
SCHEMA = "ARCANA_R6_PLATE58_G2_PT_PROXY_ENVELOPE_V1"
R_GAS = 8.31446261815324
G = 9.82  # local FAIR analytical diagnostic gravity, NOT new source physics
GT_A_MPA = 1.1e-4
GT_N = 4.0
GT_Q_J_MOL = 223_000.0
GT_LAB_TEMP_K = (1173.15, 1373.15)  # 900–1100 deg Celsius
GT_LAB_P_PA = 1.5e9  # reference center, NOT an acceptance interval
# GT was a no-melt Black Hills quartzite experiment with ~0.15 wt% water.
# No pressure activation V has been identified; do not silently set V=0.
GT_PROVENANCE = "Gleason and Tullis (1995), doi:10.1016/0040-1951(95)00011-B; A from published tabulation (MPa^-4 s^-1)"
HTD_PROVENANCE = "Hirth, Teyssier and Dunlap (2001), doi:10.1007/s005310000152; water fugacity required"


def require_positive_finite(value, name):
    value = float(value)
    require(math.isfinite(value) and value > 0.0, "INVALID_" + name)
    return value


def polynomial_temperature(profile, layer, depth_m):
    """Polynomial already materialized by the governed PRE package."""
    z0 = float(profile["layer" + str(layer) + "_z0_m"])
    z1 = float(profile["layer" + str(layer) + "_z1_m"])
    z = float(depth_m)
    require(math.isfinite(z) and z0 <= z <= z1 and z1 > z0,
            "PRE_TEMPERATURE_DEPTH_OUTSIDE_LAYER")
    x = z - z0
    # Explicit field spellings preserve the source units (K/m^p).
    t = (float(profile[f"layer{layer}_c0_k"])
         + x * (float(profile[f"layer{layer}_c1_k_m"])
         + x * (float(profile[f"layer{layer}_c2_k_m2"])
         + x * float(profile[f"layer{layer}_c3_k_m3"]))))
    return require_positive_finite(t, "PRE_TEMPERATURE")


def lithostatic_proxy_pa(profile, depth_m):
    """Overburden from PRE layer densities; excludes pore pressure."""
    d = float(depth_m)
    moho = float(profile["crust_thickness_m"])
    lab = float(profile["lab_depth_m"])
    require(math.isfinite(d) and 0 <= d <= lab and 0 < moho < lab,
            "PRE_PRESSURE_DEPTH_INVALID")
    rho_c = require_positive_finite(profile["crust_density_kg_m3"], "RHO_CRUST")
    rho_m = require_positive_finite(profile["mantle_density_kg_m3"], "RHO_MANTLE")
    return G * (rho_c * min(d, moho) + rho_m * max(0.0, d-moho))


def log_triaxial_differential_stress_pa(*, eps_s, temperature_k, a_pa_n_s,
                                       exponent_n, q_j_mol, p_pa=0.0,
                                       activation_volume_m3_mol=0.0):
    """log(Delta sigma / 1 Pa), triaxial lab convention; no SHELLS LR assignment."""
    eps = require_positive_finite(eps_s, "STRAIN_RATE")
    t = require_positive_finite(temperature_k, "TEMPERATURE")
    a = require_positive_finite(a_pa_n_s, "A_PREFACTOR")
    n = require_positive_finite(exponent_n, "STRESS_EXPONENT")
    require(math.isfinite(p_pa) and p_pa >= 0.0 and
            math.isfinite(q_j_mol) and q_j_mol >= 0.0 and
            math.isfinite(activation_volume_m3_mol) and
            activation_volume_m3_mol >= 0.0, "FLOW_LAW_INPUT_INVALID")
    return ((math.log(eps) - math.log(a) +
             (q_j_mol + p_pa * activation_volume_m3_mol) / (R_GAS * t)) / n)


def nominal_flow_stress_pa(log_value):
    require(math.isfinite(log_value) and log_value < 700,
            "FLOW_STRESS_OVERFLOW")
    return math.exp(log_value)


def slope_only_fit_check(width_rates, common_e):
    """Compare slopes AFTER exact stress matching at 100-km pivot.

    This is an exponent-only stress ratio, NOT a constitutive fit validation.
    """
    rate_by_width = {int(row["width_km"]): require_positive_finite(
        row["nominal_extension_rate_s_inv"], "WIDTH_STRAIN_RATE")
        for row in width_rates}
    require(set(rate_by_width) == {10,100,300}, "WIDTH_INVENTORY_CHANGED")
    e = require_positive_finite(common_e, "ECREEP")
    pivot = rate_by_width[100]
    errors = {}
    for label, n in (("GT_QUARTZITE", GT_N),
                     ("DRY_OLIVINE", DEFAULT_BENCHMARK.stress_exponent)):
        exponent = 1.0 / n
        errors[label] = {str(width): {
            "stress_fit_over_lab_ratio": math.exp((e-exponent)*math.log(rate/pivot)),
            "absolute_pct_from_unit_ratio": 100*abs(math.exp(
                (e-exponent)*math.log(rate/pivot))-1),
        } for width,rate in sorted(rate_by_width.items())}
    return {"pivot_width_km": 100, "chosen_eCreep_explore_only":e,
            "errors_by_law_and_width":errors,
            "max_slope_only_absolute_pct":max(
                row["absolute_pct_from_unit_ratio"]
                for values in errors.values() for row in values.values()),
            "does_not_check_prefactor_or_full_depth_integral":True}


def evaluate_column(pre, rates):
    """Keep all nine owner-bound node columns and source depth samples distinct."""
    required = ("layer1_z0_m","layer1_z1_m","layer2_z0_m","layer2_z1_m",
                "crust_thickness_m","lab_depth_m","mantle_lithosphere_thickness_m",
                "surface_temperature_k","moho_temperature_k","lab_temperature_k")
    require(all(name in pre for name in required), "PRE_FIELD_MISSING")
    zc = float(pre["crust_thickness_m"])
    zl = float(pre["lab_depth_m"])
    require(0 < zc < zl and math.isclose(float(pre["layer1_z0_m"]),0,abs_tol=1e-6)
            and math.isclose(float(pre["layer1_z1_m"]),zc,abs_tol=1e-6)
            and math.isclose(float(pre["layer2_z0_m"]),zc,abs_tol=1e-6)
            and math.isclose(float(pre["layer2_z1_m"]),zl,abs_tol=1e-6)
            and math.isclose(float(pre["mantle_lithosphere_thickness_m"]),zl-zc,
                             rel_tol=0,abs_tol=1e-5), "PRE_DEPTH_TOPOLOGY_CHANGED")
    t0=polynomial_temperature(pre,1,0)
    tmoho1=polynomial_temperature(pre,1,zc)
    tmoho2=polynomial_temperature(pre,2,zc)
    tlab=polynomial_temperature(pre,2,zl)
    require(all(math.isclose(a,b,rel_tol=0,abs_tol=2e-7) for a,b in (
        (t0,pre["surface_temperature_k"]),
        (tmoho1,pre["moho_temperature_k"]),
        (tmoho2,pre["moho_temperature_k"]),
        (tlab,pre["lab_temperature_k"]))), "PRE_POLYNOMIAL_ANCHOR_MISMATCH")
    crust_z=[zc*i/8 for i in range(9)]
    mantle_z=[zc+(zl-zc)*i/8 for i in range(9)]
    crust_t=[polynomial_temperature(pre,1,z) for z in crust_z]
    mantle_t=[polynomial_temperature(pre,2,z) for z in mantle_z]
    valid=sum(GT_LAB_TEMP_K[0] <= t <= GT_LAB_TEMP_K[1] for t in crust_t)
    curves={}
    a_gt=GT_A_MPA * (1e6**(-GT_N))  # MPa^-n s^-1 to Pa^-n s^-1
    b=DEFAULT_BENCHMARK
    for w,eps in rates.items():
        crust=[nominal_flow_stress_pa(log_triaxial_differential_stress_pa(
            eps_s=eps,temperature_k=t,a_pa_n_s=a_gt,
            exponent_n=GT_N,q_j_mol=GT_Q_J_MOL))
            for t in crust_t]
        # Preserve the ASPECT shear-viscosity convention of the existing
        # R6 olivine benchmark; DO NOT relabel as laboratory axial Delta sigma.
        mantle=[2.0*eps*evaluate_dislocation_creep(
            temperature_k=t, strain_rate_s=eps,
            pressure_pa=lithostatic_proxy_pa(pre,z)
        )["effective_shear_viscosity_pa_s"]
            for z,t in zip(mantle_z,mantle_t,strict=True)]
        curves[str(w)]={
            "kinematic_only_epsilon_s_inv":eps,
            "GT_crust_uncapped_triaxial_differential_stress_pa":crust,
            "dry_olivine_mantle_uncapped_ASPECT_invariant_stress_scale_pa":mantle,
        }
    return {
        "crust_thickness_m":zc,"lab_depth_m":zl,
        "pressure_proxy_pa_at_moho":lithostatic_proxy_pa(pre,zc),
        "pressure_proxy_pa_at_lab":lithostatic_proxy_pa(pre,zl),
        "crust_sample_depths_m":crust_z,
        "crust_sample_temperature_k":crust_t,
        "mantle_sample_depths_m":mantle_z,
        "mantle_sample_temperature_k":mantle_t,
        "GT_crust_samples_in_reported_lab_T_window":valid,
        "GT_crust_samples_total":len(crust_t),
        "curves_by_nominal_width_km":curves,
    }


def analyze(stage_dir:Path, output:Path):
    require(not output.exists(), "OUTPUT_ALREADY_EXISTS")
    verify_stage(stage_dir)
    case=json.loads((stage_dir/"CASE.json").read_text())
    require(not case["readiness"]["mechanical_solve_authorized"]
            and case["physical_deforming_t1"] is None,
            "PRIOR_STAGE_AUTHORITY_CHANGED")
    require(sha(ROOT/(PRE+".json")) ==
            case["source_sha256"][PRE+".json"], "PRE_METADATA_SHA_CHANGED")
    rates={int(r["width_km"]):float(r["nominal_extension_rate_s_inv"])
           for r in case["diagnostic_width_rates"]}
    slope=slope_only_fit_check(case["diagnostic_width_rates"],
                               case["decisions"]["G2_material"]["common_eCreep_FAIR_candidate"])
    require(len(case["parent_node_PRE"])==9 and set(rates)=={10,100,300},
            "SOURCE_NODE_OR_WIDTH_INVENTORY_INVALID")
    nodes=[]
    for row in case["parent_node_PRE"]:
        nodes.append({"parent_node_id":row["parent_id"],
                      "local_node_id":row["local_id"],
                      **evaluate_column(row["PRE"],rates)})
    report={
        "schema":SCHEMA,"status":STATUS,
        "authority":"SOURCE_PT_PLUS_LITERATURE_BENCHMARK__EXPERIMENT_ONLY",
        "stage_case_sha256":sha(stage_dir/"CASE.json"),
        "source_pre_metadata_sha256":sha(ROOT/(PRE+".json")),
        "reported_lab_quartzite":{
            "identity":"BLACK_HILLS_QUARTZITE_NO_MELT_NOT_ASSUMED_DRY",
            "reference":GT_PROVENANCE,
            "A_mpa_to_minus_n_s_inv":GT_A_MPA,"n":GT_N,"Q_j_mol":GT_Q_J_MOL,
            "reported_lab_temperature_window_k":GT_LAB_TEMP_K,
            "approx_lab_confining_pressure_pa":GT_LAB_P_PA,
            "water_content_note":"~0.15 wt percent in experimental quartzite; ARCANA field water UNKNOWN",
            "pressure_activation_term":"NOT_PROVIDED_BY_LAW; NO PRESSURE TERM APPLIED IN LAB-CURVE EVALUATION",
            "physical_validity":"UNVALIDATED_OUTSIDE_EXPERIMENTAL_PT_RATE_DOMAIN",
        },
        "mantle_literature_benchmark":{
            "identity":b_id() ,"provenance":"repository dry-olivine benchmark; NOT R6 mineralogy",
            "A_pa_to_minus_n_s_inv":DEFAULT_BENCHMARK.prefactor_pa_n_s,
            "n":DEFAULT_BENCHMARK.stress_exponent,
            "E_j_mol":DEFAULT_BENCHMARK.activation_energy_j_mol,
            "V_m3_mol":DEFAULT_BENCHMARK.activation_volume_m3_mol,
            "valid_PT_window":"UNKNOWN; NOT CLAIMED",
            "stress_convention":"2 * eta_ASPECT * nominal_strain_rate; not triaxial axial stress",
        },
        "alternative_water_sensitive_quartzite":{
            "reference":HTD_PROVENANCE,
            "state":"UNCOMPUTED__FUGACITY_P_T_FIELD_AND_LAW_NORMALIZATION_MISSING",
            "fugacity_mpa":None,
        },
        "source_rate_basis":"mean plate5:8 Euler opening divided by nominal 10/100/300 km widths; not a strain observation",
        "nominal_widths_km":sorted(rates),
        "slope_only_common_eCreep_check":slope,
        "source_pre_nodes":nodes,
        "total_node_crust_lab_T_window_samples":sum(x["GT_crust_samples_in_reported_lab_T_window"] for x in nodes),
        "total_node_crust_T_samples":sum(x["GT_crust_samples_total"] for x in nodes),
        "brittle_cap":None,"pore_pressure":None,"biot":None,"water_model":None,
        "integrated_strength":None,"shellset_lr_records":None,
        "G2_effective_constitutive_closure":None,
        "north_south_mechanical_boundary_condition":None,
        "basal_normal_support":None,
        "mechanical_solve_authorized":False,
        "solver_runs":0,"first_deforming_T1":None,
        "limitations":[
            "lab curves are not authorial ARCANA materials",
            "GT crust stresses are uncapped triaxial laboratory benchmarks, NOT SHELLS stresses",
            "mantle stress scale uses the original ASPECT shear-invariant viscosity convention, not triaxial Delta sigma",
            "source width/rate scales are kinematic only; actual strain is unknown",
            "no pressure activation for GT source law; cannot infer V=0 physically",
            "no water/fugacity/fragile law or integrated column strength",
            "mantle benchmark laboratory validity not established",
            "no FE mesh refinement, solver, G4, or HistoryStore writes",
        ],
    }
    require(report["total_node_crust_T_samples"]==81 and
            not report["mechanical_solve_authorized"], "INCOMPLETE_G2_ENVELOPE")
    output.mkdir(parents=True)
    (output/"G2_ENVELOPE.json").write_bytes(_json(report))
    manifest={"schema":"ARCANA_R6_PLATE58_G2_ENVELOPE_MANIFEST_V1",
              "status":STATUS,"files":{"G2_ENVELOPE.json":sha(output/"G2_ENVELOPE.json")},
              "prior_stage_case_sha256":report["stage_case_sha256"],
              "no_solver_run":True,"no_T1":True,"no_canonical_promotion":True}
    (output/"MANIFEST.json").write_bytes(_json(manifest))
    return report


def b_id():
    return DEFAULT_BENCHMARK.benchmark_id


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage_dir",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    d=analyze(a.stage_dir,a.output)
    print(json.dumps({
        "status":d["status"],
        "source_pre_nodes":len(d["source_pre_nodes"]),
        "crust_lab_temperature_compatible_samples":d["total_node_crust_lab_T_window_samples"],
        "total_crust_samples":d["total_node_crust_T_samples"],
        "common_eCreep_slope_only_max_absolute_pct":
            d["slope_only_common_eCreep_check"]["max_slope_only_absolute_pct"],
        "G2_effective_constitutive_closure":None,
        "mechanical_solve_authorized":False,
        "solver_runs":0,
    },indent=2))
