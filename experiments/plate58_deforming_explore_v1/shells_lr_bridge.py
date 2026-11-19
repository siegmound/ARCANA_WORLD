"""SHELLS LR creep *parameterization* bridge for candidate ARCANA R6 G2.

Grounded in external/ShellSet-v1.1.0/src/MOD_Shells.f90 (Diamnd and Mohr)
and MOD_ShellSet.f90 (a,b,c,d,e LR descriptions). Not an external K, a
calibrated whole-strength law, or an authorization for physical T1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from experiments.plate58_deforming_explore_v1.full_column import (
    G2InputError, R_GAS, bounds, need, overburden_pa, scalar, temperature_k,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHELLS = "external/ShellSet-v1.1.0/src/MOD_Shells.f90"
SOURCE_PARAMS = "external/ShellSet-v1.1.0/src/MOD_ShellSet.f90"
STATUS = "PASS_G2_SHELLS_CREEP_FORM_MAPPING__FULL_LR_UNRESOLVED"


def _sha(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def _coefficients(pre: dict, spec: dict, layer_name: str, gravity: float) -> dict:
    """Identify the analytical coefficients matching the SHELLS creep scale.

    For an ASPECT-style power law:
      epsilon_II = Aeff * sigma_II**n * exp(-(E + P V)/(R T))
      sigma_II = (Aeff**(-1/n)) epsilon_II**(1/n)
                 * exp((E+PV)/(nRT)).
    If pressure is lithostatic and piecewise linear (PRE rho constant by layer)
    P(z_abs) = P_intercept + rho_layer*g*z_abs, then
      sigma = aCreep * epsilon_II**eCreep
              * exp((bCreep + cCreep*z_abs)/T),
    where e=1/n, a=Aeff**(-1/n),
          b=(E+P_intercept*V)/(n*R), c=rho_layer*g*V/(n*R).

    This matches the creep FORM used by SHELLS for the same invariant, but
    not the entire Diamnd tensor/friction/truncation integrals.
    """
    name = "crust" if layer_name == "crust" else "mantle"
    law = spec["layers"][name]["ductile"]
    need(law.get("stress_convention") == "ASPECT_2ETA_EPS_INVARIANT_SCALE",
         "G2_SHELLS_SOURCE_STRESS_INVARIANT_CONVENTION_MISSING")
    need(isinstance(law.get("source_reference"), str) and
         len(law["source_reference"].strip()) >= 10,
         "G2_SHELLS_LAW_SOURCE_REQUIRED")
    A = scalar(law.get("A_pa_minus_n_s_inv"), "A", positive=True)
    n = scalar(law.get("n"), "N", positive=True)
    E = scalar(law.get("E_j_mol"), "E", nonnegative=True)
    V = scalar(law.get("V_m3_mol"), "V", nonnegative=True)
    r = scalar(law.get("fugacity_exponent"), "WATER_EXPONENT", nonnegative=True)
    if r > 0:
        fugacity = scalar(law.get("water_fugacity_pa"), "FIELD_FUGACITY", positive=True)
        reference = scalar(law.get("reference_fugacity_pa"), "WATER_REFERENCE", positive=True)
        log_Aeff = math.log(A) + r * math.log(fugacity/reference)
    else:
        need(law.get("water_fugacity_pa") is None and
             law.get("reference_fugacity_pa") is None,
             "G2_SHELLS_WATER_STATE_AMBIGUOUS")
        log_Aeff = math.log(A)
    # NB: the envelope's invariant_to_friction_shear_factor is NOT a multiplier
    # for SHELLS aCreep; its friction/plastic law is distinct.
    crust = scalar(pre["crust_thickness_m"], "MOHO", positive=True)
    rho_c = scalar(pre["crust_density_kg_m3"], "CRUST_RHO", positive=True)
    rho_m = scalar(pre["mantle_density_kg_m3"], "MANTLE_RHO", positive=True)
    if name == "crust":
        ztop, zbot, rho = 0.0, crust, rho_c
        intercept = 0.0
        layer = 1
    else:
        m = scalar(pre["mantle_lithosphere_thickness_m"], "MANTLE_THICKNESS",
                   positive=True)
        ztop, zbot, rho = crust, crust + m, rho_m
        intercept = gravity * crust * (rho_c - rho_m)
        layer = 2
    e = 1.0/n
    log_a = -log_Aeff/n
    b = (E + intercept*V)/(n*R_GAS)
    c = rho*gravity*V/(n*R_GAS)
    need(all(math.isfinite(x) for x in (e,log_a,b,c)) and b>=0 and c>=0,
         "G2_SHELLS_B_OR_C_OUTSIDE_PARAMETER_DOMAIN")
    need(log_a < 700 and log_a > -700,
         "G2_SHELLS_A_CREEP_OUTSIDE_NUMERIC_RANGE")
    a = math.exp(log_a)
    need(a>0, "G2_SHELLS_A_CREEP_INVALID")
    return {"layer":name, "n":n,
            "aCreep_candidate_pa_s_to_e":a,
            "bCreep_candidate_kelvin":b,
            "cCreep_candidate_kelvin_per_m":c,
            "eCreep_candidate":e,
            "A_effective_source_log":log_Aeff,
            "source_pressure_intercept_pa":intercept,
            "source_density_kg_m3":rho,
            "depth_interval_m":[ztop,zbot],
            "layer_number":layer,
            "reference_law":law["source_reference"],
            "raw_creep_parameterization_only":True}


def _validate_parameterization(pre: dict, spec: dict, c: dict,
                               sample_count: int) -> dict:
    """Compare independent log stress equations throughout an actual PRE layer."""
    layer = c["layer"]
    law = spec["layers"][layer]["ductile"]
    zlo,zhi = c["depth_interval_m"]
    need(isinstance(sample_count,int) and sample_count>=5,
         "G2_SHELLS_SAMPLE_GRID_UNDEFINED")
    z = np.linspace(zlo,zhi,sample_count)
    t = temperature_k(pre,c["layer_number"],z)
    gravity = scalar(spec.get("gravity_m_s2"), "GRAVITY", positive=True)
    pressure = overburden_pa(pre,gravity,z)
    t_min,t_max = bounds(law,"valid_temperature_k")
    p_min,p_max = bounds(law,"valid_pressure_pa")
    rate_min,rate_max=bounds(law,"valid_strain_rate_s_inv")
    rate=scalar(spec.get("strain_rate_s_inv"),"STRAIN_RATE",positive=True)
    need(rate_min<=rate<=rate_max and
         np.all((t>=t_min)&(t<=t_max)) and
         np.all((pressure>=p_min)&(pressure<=p_max)),
         "G2_SHELLS_CREeP_CALIBRATED_PT_RATE_RANGE_NOT_COVERED")
    e=c["eCreep_candidate"]
    log_a=math.log(c["aCreep_candidate_pa_s_to_e"])
    b,c_gradient=c["bCreep_candidate_kelvin"],c["cCreep_candidate_kelvin_per_m"]
    E=scalar(law.get("E_j_mol"),"E",nonnegative=True)
    V=scalar(law.get("V_m3_mol"),"V",nonnegative=True)
    scales=[]
    for rate_test in (rate_min,rate,rate_max):
        # Independently evaluate the lab/ASPECT-style source equation and
        # the SHELLS-invariant stress FORM at the same T/P/strain.
        source_log = (math.log(rate_test)-c["A_effective_source_log"]
                      +(E+pressure*V)/(R_GAS*t))*e
        shells_log=log_a+e*math.log(rate_test)+(b+c_gradient*z)/t
        delta=np.abs(shells_log-source_log)
        need(bool(np.all(np.isfinite(delta))),"G2_SHELLS_FORM_PARITY_NONFINITE")
        scales.append(float(np.max(np.abs(np.expm1(shells_log-source_log)))))
    return {
        "layer":layer,"PRE_temperature_k_range":[float(np.min(t)),float(np.max(t))],
        "lithostatic_pressure_pa_range":[float(np.min(pressure)),float(np.max(pressure))],
        "tested_strain_rate_s_inv":[rate_min,rate,rate_max],
        "evaluated_depth_samples":int(sample_count),
        "relative_creep_scale_max_error":max(scales)}


def candidate_to_shells_form(pre: dict, spec: dict, *,
                             sample_count: int=33, tol: float=1e-11) -> dict:
    """Return candidate creep-form coefficients or an incompatibility decision.

    No complete SHELLS LR is ever returned. dCreep, cFric, Biot, Byerly,
    GPE/basal forcing, stress-tensor normalization, actual creep+friction
    integration are not inferred.
    """
    need(spec.get("authority")=="ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
         "G2_SHELLS_RATIFICATION_NOT_GRANTED")
    require_id=spec.get("source_identifier")
    need(isinstance(require_id,str) and len(require_id.strip())>=10,
         "G2_SHELLS_SCENARIO_PROVENANCE_REQUIRED")
    gravity=scalar(spec.get("gravity_m_s2"),"GRAVITY",positive=True)
    tolerance=scalar(tol,"PARITY_TOLERANCE",positive=True)
    need(tolerance<0.01,"G2_SHELLS_PARITY_TOLERANCE_TOO_PERMISSIVE")
    crust=_coefficients(pre,spec,"crust",gravity)
    mantle=_coefficients(pre,spec,"mantle",gravity)
    trial=[_validate_parameterization(pre,spec,row,sample_count)
           for row in (crust,mantle)]
    need(max(x["relative_creep_scale_max_error"] for x in trial)<=tolerance,
         "G2_SHELLS_CREEP_FORM_ALGEBRA_PARITY_FAILED")
    e1,e2=crust["eCreep_candidate"],mantle["eCreep_candidate"]
    shared_e=bool(math.isclose(e1,e2,rel_tol=0,abs_tol=1e-14))
    # The global per-LR eCreep is COMMON for crust and mantle in this version.
    # No fake mean can make n=4 and n=3.5 exact.
    return {
        "status": STATUS,
        "authority":"ENGINEERING_PARAMETERIZATION_NOT_PHYSICAL_LR",
        "source_identifier":require_id,
        "candidate_layer_coefficients":{"crust":crust,"mantle":mantle},
        "layer_form_parity":trial,
        "SHELLS_eCreep_shared_exactly_compatible":shared_e,
        "proposed_single_eCreep_if_compatible":e1 if shared_e else None,
        "SHELLS_full_LR_coefficients":None,
        "SHELLS_cFric":None,"SHELLS_Biot":None,
        "SHELLS_Byerly_fault_reduction":None,"SHELLS_dCreep_caps":None,
        "SHELLS_assembled_tangent":None,"G3_A_external_forcing":None,
        "G3_A_basal_reaction":None,
        "SHELLS_full_tensor_and_vertical_stress_parity_validated":False,
        "physical_rheology_authorized":False,
        "mechanical_solve_authorized":False,
        "solver_runs":0,"physical_T1":None,
        "note":"Byerly in SHELLS LR = fault friction reduction, NOT the Byerlee bilinear sliding-friction law. Full LR not assembled."}


def validate_source_fortran(root: Path=ROOT) -> dict:
    """Fail on unexpected solver sources instead of silently using conventions."""
    p1,p2=root/SOURCE_SHELLS,root/SOURCE_PARAMS
    a,b=p1.read_text(),p2.read_text()
    need("visInf = 0.5D0 * aCreep" in a and
         "cCreep * (zOfTop + z)" in a and
         "DIMENSION aCreep(2)" in b and
         "'nent for creep (1/n).  (Same for crust and mantle!)'" in b and
         "Byerlee coefficient (0. to 0.999)" in b,
         "G2_SHELLS_SOURCE_CONVENTIONS_CHANGED")
    return {SOURCE_SHELLS:_sha(p1),SOURCE_PARAMS:_sha(p2)}


def run(coupling_dir: Path, candidate_file: Path, output: Path):
    """Optional source-bound 25-column audit; NOT run until a hypothesis exists."""
    from experiments.plate58_deforming_explore_v1.g2_candidate_runner import (
        sha as hash_file, COUPLING_STATUS,
    )
    need(not output.exists(),"G2_SHELLS_OUTPUT_ALREADY_EXISTS")
    source=validate_source_fortran()
    manifest=json.loads((coupling_dir/"MANIFEST.json").read_text())
    need(manifest["status"]==COUPLING_STATUS and
         manifest["no_solver_run"] and manifest["no_T1"] and
         manifest["no_canonical_promotion"],
         "G2_SHELLS_PRIOR_COUPLING_AUTHORITY_INVALID")
    for name,digest in manifest["files"].items():
        need(hash_file(coupling_dir/name)==digest,
             "G2_SHELLS_COUPLING_MEMBER_SHA_DRIFT")
    pre=json.loads((coupling_dir/"G2_PRE_BINDING.json").read_text())
    geometry=json.loads((coupling_dir/"GEOMETRY.json").read_text())
    transfer=json.loads((coupling_dir/"G3_A_TRANSFER_CONTRACT.json").read_text())
    require_nodes=set(geometry["geometry"]["source_halo_parent_node_ids"])
    need(len(pre["source_columns"])==len(require_nodes)==25 and
         {x["parent_id"] for x in pre["source_columns"]}==require_nodes and
         transfer["actual_interface_tangent"] is None and
         transfer["mechanical_solve_authorized"] is False,
         "G2_SHELLS_INVALID_PRE_OR_EXTERNAL_STATE")
    spec=json.loads(candidate_file.read_text())
    cols=[{"parent_id":x["parent_id"],
           "result":candidate_to_shells_form(x["source_PRE"],spec)}
          for x in pre["source_columns"]]
    all_compatible=all(x["result"]["SHELLS_eCreep_shared_exactly_compatible"]
                       for x in cols)
    report={
        "schema":"ARCANA_R6_G2_25_COLUMN_SHELLS_CREEP_FORM_AUDIT_V1",
        "status":STATUS,
        "scenario_sha256":hash_file(candidate_file),
        "coupling_manifest_sha256":hash_file(coupling_dir/"MANIFEST.json"),
        "fortran_source_sha256":source,
        "all_columns_common_e_compatible":all_compatible,
        "source_bound_columns":cols,
        "global_shells_LR_parameters":None,
        "G3_A_physical_tangent":None,"G3_A_NS_forcing":None,
        "basal_support":None,"mechanical_solve_authorized":False,
        "solver_runs":0,"physical_T1":None}
    output.mkdir(parents=True,exist_ok=False)
    p=output/"SHELLS_CREEP_FORM.json"
    p.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+"\n")
    (output/"MANIFEST.json").write_text(json.dumps({
        "schema":"ARCANA_R6_G2_25_COLUMN_SHELLS_FORM_MANIFEST_V1",
        "status":STATUS,
        "files":{"SHELLS_CREEP_FORM.json":_sha(p)},
        "no_solver_run":True,"no_T1":True,"no_canonical_promotion":True,
    },sort_keys=True,indent=2)+"\n")
    return {"status":STATUS,"columns":len(cols),
            "all_columns_common_e_compatible":all_compatible,
            "mechanical_solve_authorized":False,"solver_runs":0}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("coupling_dir",type=Path)
    p.add_argument("candidate_json",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    print(json.dumps(run(args.coupling_dir,args.candidate_json,args.output),
                     sort_keys=True,indent=2))
