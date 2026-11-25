"""M02: fixed M01_BASE X, local PT response and two original regional states.
Audit M01 first; preserve evidence; no canonical promotion.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import json
import math
import os
import tomllib
import traceback

from experiments.r6_thermo_provider_pilot_v1 import run_m01_fair as m

s2=m.s2
OUT=s2.BASE/"R6_THERMO_M02_MANTLE_PT_RESPONSE_NEW01"
M01_SHA="0da41455541a05413b347ea4519185e4332d78b4509de43daef9192177f38581"
M01_HEAD="6bc36c6b1edfefdd86ba31261163a31f68105311"
SCOPE=m.SCOPE
DT=10.0
DP=.25 # kbar
REGIONAL=(("M02_REGIONAL_41KM",35303,41000,1246.2572600999367,11911.66),
          ("M02_REGIONAL_67KM",36747,67000,1556.3638705347944,20337.22))


def need(ok,code):
    m.require(ok,code)


def design(base):
    out={}
    for name,p,t in (("M02_T_MINUS",m.P,m.T-DT),("M02_T_PLUS",m.P,m.T+DT),
                     ("M02_P_MINUS",m.P-DP,m.T),("M02_P_PLUS",m.P+DP,m.T),
                     *((name,bar/1000,tk-273.15) for name,_,_,tk,bar in REGIONAL)):
        inp=deepcopy(base)
        inp.update(case=name,P_kbar=p,T_C=t)
        out[name]=inp
    need(len(out)==6,"M02_DESIGN_CASE_COUNT")
    return out


def audit_m01(root):
    man=m.archive_manifest(m.OUT,M01_SHA,"files_sha256")
    need(man["source_sha"]==M01_HEAD and man["fresh_processes_completed"]==8
         and all(man[k]==v for k,v in SCOPE.items()),"M02_M01_SCOPE")
    inputs=m.build_inputs(root)
    expected={"PROVENANCE.json","EVALUATION.json"}
    for name in inputs:
        for rep in (1,2):
            expected.update(f"{name}_{rep:02d}/{x}" for x in
                ("INPUT.toml","CONVERSION.toml","NATIVE.toml","LAUNCH.json","LAUNCH_STDOUT.log","AUDIT.json"))
    need(set(man["files_sha256"])==expected,"M02_M01_MANIFEST_COVERAGE")
    provenance=json.loads((m.OUT/"PROVENANCE.json").read_text())
    need(provenance["source_sha"]==M01_HEAD and provenance["inputs"]==inputs
         and provenance["selection_id"]=="M01_NONCANONICAL_RESEARCH_APPROVAL_20261125"
         and all(provenance[k]==v for k,v in SCOPE.items()),"M02_M01_PROVENANCE")
    ev=json.loads((m.OUT/"EVALUATION.json").read_text())
    receipt=json.loads((m.HERE/"m01_fair_campaign_receipt_v1.json").read_text())
    need(ev["status"]=="M01_NUMERICAL_RESEARCH_SCREEN_PASS"
         and ev["fresh_processes_completed"]==8 and ev["scientific_promotion"] is False
         and set(ev["cases"])==set(inputs) and receipt["manifest_sha256"]==M01_SHA,"M02_M01_EVALUATION")
    rechecked={}
    for name,inp in inputs.items():
        reports=[]
        for rep in (1,2):
            path=m.OUT/f"{name}_{rep:02d}"
            checked=read_run(path,inp)
            need(checked==json.loads((path/"AUDIT.json").read_text()),"M02_M01_AUDIT_DRIFT")
            need(checked==receipt["cases"][name],"M02_M01_OPERATOR_RECEIPT_DRIFT")
            reports.append(checked)
        rebuilt={"repeatability_absolute_deltas":m.compare(*reports),"first":reports[0],"second":reports[1]}
        need(rebuilt==ev["cases"][name],"M02_M01_REPLAY_DRIFT")
        rechecked[name]=reports[0]
    return rechecked,provenance


def read_run(path,inp):
    raw=tomllib.loads((path/"INPUT.toml").read_text())
    need(all(raw[k]==inp[k] for k in ("case","P_kbar","T_C","names","wt_amounts","wrapper_git_blob","expected_native_mol")),
         "M02_INPUT_DRIFT")
    launch=json.loads((path/"LAUNCH.json").read_text())
    need(launch["exit_code"]==0 and launch["timeout"] is False,"M02_LAUNCH_FAILED")
    conversion=tomllib.loads((path/"CONVERSION.toml").read_text())
    need(conversion["wrapper_git_blob"]==inp["wrapper_git_blob"]
         and m.basis_delta(conversion["oxides"],conversion["mol_fraction"],inp["expected_native_mol"])<=1e-12,
         "M02_CONVERSION_DRIFT")
    c=tomllib.loads((path/"NATIVE.toml").read_text())
    return m.validate(c,inp)


def scalar(diag,key,vector=False):
    x=diag[key]
    if vector:
        need(isinstance(x,list) and len(x)==1,"M02_DIAGNOSTIC_SHAPE:"+key)
        x=x[0]
    need(m.finite(x),"M02_DIAGNOSTIC_NONFINITE:"+key)
    return x


def thermo(a,t_kelvin):
    d=a["native_diagnostics"]
    ms=scalar(d,"M_sys_g_mol_oxide")
    v=scalar(d,"volume_cm3_mol_oxide")
    h=scalar(d,"enthalpy_kJ_mol_oxide",True)
    s=scalar(d,"entropy_kJ_mol_oxide_K",True)
    need(ms>0 and v>0,"M02_MOLAR_MASS_VOLUME")
    rho=a["rho_kg_m3"];g=a["G_system"]
    # Algebraic consistency, not validation of independent physical derivatives.
    hr=h-(g+t_kelvin*s)
    rr=rho-1000*ms/v
    need(abs(hr)<=1e-8 and abs(rr)<=1e-7,"M02_NATIVE_ALGEBRAIC_IDENTITY")
    return {"mass_g_per_mol":ms,"H_J_per_kg":h*1e6/ms,"S_J_per_kg_K":s*1e6/ms,
        "G_kJ_per_mol":g,"V_cm3_per_mol":v,"rho":rho,
        "Cp_native_fixed_phase":scalar(d,"Cp_fixed_phase_J_kg_K",True),
        "alpha_native_fixed_phase":scalar(d,"alpha_fixed_phase_per_K",True),
        "beta_native_per_GPa":scalar(d,"beta_per_GPa"),
        "H_minus_G_TS_kJ_per_mol":hr,"rho_minus_mass_over_volume_kg_m3":rr}


def response(base,points):
    a=thermo(base,m.T+273.15)
    tslo=thermo(points["M02_T_MINUS"],m.T-DT+273.15)
    tshi=thermo(points["M02_T_PLUS"],m.T+DT+273.15)
    plo=thermo(points["M02_P_MINUS"],m.T+273.15)
    phi=thermo(points["M02_P_PLUS"],m.T+273.15)
    need(all(abs(x["mass_g_per_mol"]-a["mass_g_per_mol"])<=1e-8 for x in (tslo,tshi,plo,phi)),
         "M02_FIXED_X_MOLAR_MASS_DRIFT")
    cp=(tshi["H_J_per_kg"]-tslo["H_J_per_kg"])/(2*DT)
    alpha=-(math.log(tshi["rho"])-math.log(tslo["rho"]))/(2*DT)
    beta=(math.log(phi["rho"])-math.log(plo["rho"]))/(2*DP/10)
    sg=-(tshi["G_kJ_per_mol"]-tslo["G_kJ_per_mol"])/(2*DT)
    vg=(phi["G_kJ_per_mol"]-plo["G_kJ_per_mol"])/(2*DP)*10
    def split(x,y,z,h):
        return [(y-x)/h,(z-y)/h]
    return {"step_K":DT,"step_kbar":DP,"native_anchor":a,
        "central_equilibrium_path_Cp_secant_J_kg_K":cp,
        "left_right_Cp_secants_J_kg_K":split(tslo["H_J_per_kg"],a["H_J_per_kg"],tshi["H_J_per_kg"],DT),
        "central_alpha_secant_per_K":alpha,
        "left_right_alpha_secants_per_K":split(-math.log(tslo["rho"]),-math.log(a["rho"]),-math.log(tshi["rho"]),DT),
        "central_beta_secant_per_GPa":beta,
        "left_right_beta_secants_per_GPa":split(math.log(plo["rho"]),math.log(a["rho"]),math.log(phi["rho"]),DP/10),
        "minus_dG_dT_kJ_mol_K_secant":sg,
        "dG_dP_volume_equivalent_cm3_per_mol_secant":vg,
        "anchor_S_kJ_per_mol_K":a["S_J_per_kg_K"]*a["mass_g_per_mol"]/1e6,
        "anchor_V_cm3_per_mol":a["V_cm3_per_mol"],
        "phase_set_change_vs_anchor":{k:set(v["phases"])!=set(base["phases"]) for k,v in points.items()},
        "secants_not_certified_derivatives":True,"equilibrium_path_vs_fixed_phase_not_equivalent":True}


def source_states():
    folder=m.d10.BASE/"R6_G2G3_T0_LITHOSTATIC_PT_REFERENCE_NEW01"
    _,reports,_=m.d10.cold._load_original_pt(folder)
    for name,node,depth,tk,bar in REGIONAL:
        samples=reports[0]["original_T0_source_nodes"][str(node)]["source_depth_pt_samples"]
        found=[x for x in samples if x["layer"]=="mantle_lithosphere" and x["source_depth_m"]==depth]
        need(len(found)==1 and m.close(found[0]["source_PRE_temperature_k"],tk,1e-9)
            and m.close(found[0]["conditional_delta_vertical_overburden_pa"],bar*1e5,1e-5),
             "M02_REGIONAL_SOURCE_DRIFT:"+name)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    ap.add_argument("--audit-only",action="store_true")
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"M02_CHECKOUT")
    anchors,prior=audit_m01(root)
    print("M01_INDEPENDENT_READONLY_REPLAY_PASS",M01_SHA,flush=True)
    for name,a in anchors.items():
        print("M01_IDENTITIES",name,json.dumps(thermo(a,m.T+273.15),sort_keys=True,allow_nan=False),flush=True)
    if args.audit_only:
        return
    paths,previous=m.runtime()
    need(prior["julia_binary_sha256"]==s2.sha(paths["JULIA_BIN"])
         and prior["julia_project_sha256"]==previous["julia_project_sha256"]
         and prior["julia_manifest_sha256"]==previous["julia_manifest_sha256"],"M02_M01_RUNTIME_DRIFT")
    source_states()
    inputs=design(m.build_inputs(root)["M01_BASE"])
    need(not OUT.exists(),"M02_OUTPUT_EXISTS")
    env=os.environ.copy()
    env.update(JULIA_DEPOT_PATH=str(paths["JULIA_DEPOT_PATH"]),JULIA_LOAD_PATH="@:@stdlib",
        JULIA_PKG_OFFLINE="true",JULIA_PKG_PRECOMPILE_AUTO="0",JULIA_NUM_THREADS="1",
        JULIA_NUM_PRECOMPILE_TASKS="1",OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1")
    OUT.mkdir(parents=False,exist_ok=False)
    launched=0
    try:
        s2.write_json(OUT/"PROVENANCE.json",{"source_sha":head,"M01_manifest_sha256":M01_SHA,
            "runtime_paths":{k:str(v) for k,v in paths.items()},"julia_binary_sha256":prior["julia_binary_sha256"],
            "julia_project_sha256":prior["julia_project_sha256"],"julia_manifest_sha256":prior["julia_manifest_sha256"],
            "inputs":inputs,"regional_source_states":REGIONAL,"pressure_semantics":"HYPOTHETICAL_SOLVER_P_NUMERICALLY_FROM_SOURCE_DELTA",
            "research_scope":"FIXED_APPROVED_M01_BASE_CHEMISTRY_NONCANONICAL",**SCOPE})
        results={};first={}
        for name,inp in inputs.items():
            reports=[]
            for rep in (1,2):
                path=OUT/f"{name}_{rep:02d}"
                path.mkdir()
                m.input_file(path/"INPUT.toml",inp)
                launched+=1
                s2.launch(root,[str(paths["JULIA_BIN"]),"--startup-file=no","--threads=1",
                    "--project="+str(paths["JULIA_PROJECT"]),str(m.HERE/"run_m01_native.jl"),
                    str(path/"INPUT.toml"),str(path)],path,env,600)
                a=read_run(path,inp)
                derived=thermo(a,inp["T_C"]+273.15)
                s2.write_json(path/"AUDIT.json",a)
                s2.write_json(path/"THERMO_IDENTITIES.json",derived)
                reports.append(a)
                print("M02_RUN",name,rep,json.dumps(a,sort_keys=True,allow_nan=False),flush=True)
            first[name]=reports[0]
            results[name]={"repeatability_absolute_deltas":m.compare(*reports),"first":reports[0],"second":reports[1]}
        derivative=response(anchors["M01_BASE"],first)
        s2.write_json(OUT/"EVALUATION.json",{"status":"M02_NUMERICAL_RESEARCH_SCREEN_PASS",
            "cases":results,"local_PT_response":derivative,"fresh_processes_completed":launched,
            "scientific_promotion":False,**SCOPE})
        files={str(f.relative_to(OUT)):s2.sha(f) for f in sorted(OUT.rglob("*")) if f.is_file()}
        s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_M02_CAMPAIGN_MANIFEST_V1","source_sha":head,
            "M01_manifest_sha256":M01_SHA,"files_sha256":files,"fresh_processes_completed":launched,
            "science":"UNVALIDATED_NONCANONICAL_RESEARCH",**SCOPE})
        print("M02_RESPONSE",json.dumps(derivative,sort_keys=True,allow_nan=False))
        print("M02_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
        print("M02_NUMERICAL_RESEARCH_SCREEN_PASS")
    except BaseException as e:
        s2.write_json(OUT/"FAILURE.json",{"status":"M02_FAILED_PRESERVE_ALL","process_launch_attempts":launched,
            "error":str(e),"traceback":traceback.format_exc(),**SCOPE})
        raise


if __name__=="__main__":
    main()
