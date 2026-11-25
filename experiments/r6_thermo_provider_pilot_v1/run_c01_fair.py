"""C01 approved noncanonical crust research; twelve fresh solves maximum."""
from __future__ import annotations
import argparse
from collections import Counter
import json
import os
import tomllib
import traceback
from experiments.r6_thermo_provider_pilot_v1 import c01_conversion_preflight as p

m=p.m
s2=p.s2
need=p.need
OUT=s2.BASE/"R6_THERMO_C01_MB_CRUST_CAMPAIGN_NEW01"
PRE_SHA="f28e4def7b3bb25daa55fdce0fc273fa2276bde60c3602ea94934837e8f38a9e"
PRE_HEAD="84893f9ceed1d0b2b12d6c4e06e179fc9267af96"
SELECTION="C01_NONCANONICAL_RESEARCH_APPROVAL_20261125"
SCOPE=m.SCOPE


def selected(root):
    raw=(m.HERE/"c01_crust_experimental_design_candidate_v1.json").read_bytes()
    need(p.git_blob_sha(raw)==p.DESIGN_BLOB,"C01_DESIGN_DRIFT")
    d,_=p.c.check_design(root)
    inp=p.recipes(d)
    sel=json.loads((m.HERE/"c01_research_selection_v1.json").read_text())
    need(sel["selection_id"]==SELECTION and sel["design_git_blob"]==p.DESIGN_BLOB
        and sel["conversion_manifest_sha256"]==PRE_SHA
        and sel["case_order"]==list(inp) and sel["repeats"]==2
        and sel["maximum_solver_calls"]==12 and sel["threads"]==1 and sel["process_timeout_s"]==600
        and sel["provider_options"]==p.OPTIONS and sel["source_morb_raw_bytes_verified"] is False
        and sel["authorial_statement"]=="Approvo tutte e sei le ipotesi sperimentali C01 come ricerca non canonica."
        and all(sel[k]==v for k,v in SCOPE.items()),"C01_SELECTION_DRIFT")
    return d,inp,sel


def audit_preflight(inputs):
    man=m.archive_manifest(p.OUT,PRE_SHA,"files_sha256")
    need(man["source_sha"]==PRE_HEAD and man["conversion_processes"]==6
        and all(man[k]==v for k,v in p.SCOPE.items()),"C01_PREFLIGHT_SCOPE")
    expected={"PROVENANCE.json","EVALUATION.json"}
    for name in inputs:
        expected.update(f"{name}/{f}" for f in ("INPUT.toml","CONVERSION.toml","LAUNCH.json","LAUNCH_STDOUT.log"))
    need(set(man["files_sha256"])==expected and len(expected)==26,"C01_PREFLIGHT_COVERAGE")
    prov=json.loads((p.OUT/"PROVENANCE.json").read_text())
    need(prov["source_sha"]==PRE_HEAD and prov["design_git_blob"]==p.DESIGN_BLOB
        and prov["inputs"]==inputs and prov["future_solver_options_proposed_not_selected"]==p.OPTIONS
        and all(prov[k]==v for k,v in p.SCOPE.items()),"C01_PREFLIGHT_PROVENANCE")
    rec=json.loads((m.HERE/"c01_conversion_fair_receipt_v1.json").read_text())
    ev=json.loads((p.OUT/"EVALUATION.json").read_text())
    need(rec["manifest_sha256"]==PRE_SHA and ev["status"]=="C01_MB_CONVERSION_PREFLIGHT_PASS__SELECTION_PENDING"
        and ev["thermodynamic_equilibrium_qualified"] is False and all(ev[k]==v for k,v in p.SCOPE.items())
        and set(rec["cases"])==set(ev["cases"])==set(inputs),"C01_PREFLIGHT_EVALUATION")
    for name,inp in inputs.items():
        folder=p.OUT/name
        verify_input(folder,inp)
        launch=json.loads((folder/"LAUNCH.json").read_text())
        need(launch["exit_code"]==0 and launch["timeout"] is False,"C01_PREFLIGHT_LAUNCH")
        a=tomllib.loads((folder/"CONVERSION.toml").read_text())
        delta=p.check_conversion(a,inp)
        summary={"native_mol_delta":delta,"source_oxide_sum":inp["source_major_oxide_sum"],
            "omitted_source_oxides_wt":inp["omitted_source_oxides_wt"],"reduced_input_sum":inp["reduced_input_sum"]}
        need(summary==ev["cases"][name]==rec["cases"][name],"C01_PREFLIGHT_REPLAY_DRIFT")


def verify_input(folder,inp):
    a=tomllib.loads((folder/"INPUT.toml").read_text())
    need(all(a[k]==inp[k] for k in ("case","P_kbar","T_C","names","wt_amounts","wrapper_git_blob","expected_native_mol")),"C01_INPUT_DRIFT")


def basis_delta(ox,v,expected):
    need(isinstance(ox,list) and len(ox)==len(p.NATIVE) and set(ox)==p.NATIVE
        and m.valid_fraction(v,len(ox)),"C01_NATIVE_BASIS")
    return max(abs(x-expected[k]) for k,x in zip(ox,v,strict=True))


def validate(c,inp):
    need(c["case"]==inp["case"] and c["status"]==0 and c["database"]=="mb" and c["dataset"]=="tc_ds62","C01_NATIVE_STATUS")
    need(m.within_float64_roundoff(c["P_kbar"],inp["P_kbar"])
        and m.within_float64_roundoff(c["T_C"],inp["T_C"]),"C01_NATIVE_PT")
    ox=c["oxides"];bulk=c["bulk_wt"];ph=c["phases"];frac=c["phase_mass_fractions"];comp=c["phase_comp_wt"]
    wd=basis_delta(ox,bulk,inp["expected_native_wt"])
    md=basis_delta(ox,c["bulk_mol"],inp["expected_native_mol"])
    need(wd<=1e-12 and md<=1e-12,"C01_NATIVE_INPUT_DRIFT")
    need(isinstance(ph,list) and len(ph)>0 and all(isinstance(k,str) and k for k in ph)
        and m.valid_fraction(frac,len(ph)) and len(comp)==len(ph)
        and all(m.valid_fraction(v,len(ox)) for v in comp),"C01_NATIVE_PHASES")
    types=c["phase_types"]
    need(len(types)==len(ph) and all(k in (0,1) for k in types),"C01_PHASE_TYPES")
    closure=max(abs(sum(frac[i]*comp[i][j] for i in range(len(ph)))-bulk[j]) for j in range(len(ox)))
    need(closure<=1e-10 and m.finite(c["bulk_res_norm"]) and 0<=c["bulk_res_norm"]<=1e-9,"C01_NATIVE_CLOSURE")
    need(m.finite(c["rho_kg_m3"]) and c["rho_kg_m3"]>0 and m.finite(c["G_system"]),"C01_NATIVE_PRIMARY")
    aggregate=[c[k] for k in ("solid_wt","melt_wt","fluid_wt")]
    need(m.valid_fraction(aggregate,3),"C01_NATIVE_AGGREGATES")
    # Preserve repeated solution-phase instances, e.g. solvus branches. Never overwrite a dict key.
    totals={};instances=[]
    for name,f,v,typ in zip(ph,frac,comp,types,strict=True):
        totals[name]=totals.get(name,0.)+f
        instances.append({"phase":name,"type":typ,"mass_fraction":f,"component_mass_fractions":dict(zip(ox,v,strict=True))})
    return {"case":inp["case"],"native_input_weight_delta":wd,"native_input_mole_delta":md,
        "phase_component_closure":closure,"residual":c["bulk_res_norm"],"rho_kg_m3":c["rho_kg_m3"],
        "G_system":c["G_system"],"phases":totals,"phase_instances":instances,
        "aggregate_mass_fractions":aggregate,"native_diagnostics":c["native_diagnostics"]}


def compare(a,b):
    out=m.compare(a,b)
    need(Counter((x["phase"],x["type"]) for x in a["phase_instances"])==
        Counter((x["phase"],x["type"]) for x in b["phase_instances"]),"C01_REPEAT_INSTANCE_COUNT")
    # Pair repeated phase branches deterministically by sorted component vector, then fraction.
    def order(x):
        return (x["phase"],x["type"],tuple(v for _,v in sorted(x["component_mass_fractions"].items())),x["mass_fraction"])
    max_delta=0.
    for x,y in zip(sorted(a["phase_instances"],key=order),sorted(b["phase_instances"],key=order),strict=True):
        need(x["phase"]==y["phase"] and x["type"]==y["type"],"C01_REPEAT_INSTANCE_ID")
        f,g=x["mass_fraction"],y["mass_fraction"]
        need(abs(f-g)<=.0001+.001*max(abs(f),abs(g)),"C01_REPEAT_INSTANCE_FRACTION")
        delta=max(abs(v-y["component_mass_fractions"][k]) for k,v in x["component_mass_fractions"].items())
        need(delta<=1e-5,"C01_REPEAT_PHASE_COMPONENT_DRIFT")
        max_delta=max(max_delta,delta)
    out["max_phase_instance_component_delta"]=max_delta
    return out


def diagnostic_review(a,t):
    # Diagnostics are not qualified primary outputs; explicit UNKNOWN if unavailable.
    d=a["native_diagnostics"]
    def scalar(k,vector=False):
        x=d.get(k)
        if vector:
            x=x[0] if isinstance(x,list) and len(x)==1 else None
        return x if m.finite(x) else None
    h=scalar("enthalpy_kJ_mol_oxide",True);s=scalar("entropy_kJ_mol_oxide_K",True)
    mass=scalar("M_sys_g_mol_oxide");vol=scalar("volume_cm3_mol_oxide")
    h_err=None if h is None or s is None else h-(a["G_system"]+(t+273.15)*s)
    rho_err=None if mass is None or vol is None or vol<=0 else a["rho_kg_m3"]-1000*mass/vol
    return {"H_minus_G_TS_kJ_per_mol":h_err,"rho_minus_mass_over_volume_kg_m3":rho_err,
        "algebraic_identity_status":"PASS" if h_err is not None and rho_err is not None and abs(h_err)<=1e-8 and abs(rho_err)<=1e-7 else "UNQUALIFIED_OR_INCONSISTENT",
        "thermodynamic_derivatives_qualified":False}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C01_CHECKOUT")
    d,inputs,sel=selected(root)
    audit_preflight(inputs)
    p.c.verify_pt(d)
    print("C01_INDEPENDENT_CONVERSION_REPLAY_PASS",PRE_SHA,flush=True)
    paths,previous=m.runtime()
    prior=json.loads((m.OUT/"PROVENANCE.json").read_text())
    need(s2.sha(paths["JULIA_BIN"])==prior["julia_binary_sha256"]
        and previous["julia_project_sha256"]==prior["julia_project_sha256"]
        and previous["julia_manifest_sha256"]==prior["julia_manifest_sha256"],"C01_RUNTIME_DRIFT")
    need(not OUT.exists(),"C01_OUTPUT_EXISTS")
    env=os.environ.copy()
    env.update(JULIA_DEPOT_PATH=str(paths["JULIA_DEPOT_PATH"]),JULIA_LOAD_PATH="@:@stdlib",
        JULIA_PKG_OFFLINE="true",JULIA_PKG_PRECOMPILE_AUTO="0",JULIA_NUM_THREADS="1",
        JULIA_NUM_PRECOMPILE_TASKS="1",OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1")
    OUT.mkdir(parents=False,exist_ok=False)
    launched=0
    try:
        s2.write_json(OUT/"PROVENANCE.json",{"source_sha":head,"selection":sel,"inputs":inputs,
            "preflight_manifest_sha256":PRE_SHA,"runtime_paths":{k:str(v) for k,v in paths.items()},
            **{k:prior[k] for k in ("julia_binary_sha256","julia_project_sha256","julia_manifest_sha256")},
            "pressure_semantics":"COMMON_HYPOTHETICAL_COMPARATIVE_PT_NOT_SPATIAL_ASSIGNMENT",**SCOPE})
        cases={}
        for name,inp in inputs.items():
            reports=[]
            for rep in (1,2):
                folder=OUT/f"{name}_{rep:02d}";folder.mkdir()
                m.input_file(folder/"INPUT.toml",inp)
                launched+=1
                s2.launch(root,[str(paths["JULIA_BIN"]),"--startup-file=no","--threads=1",
                    "--project="+str(paths["JULIA_PROJECT"]),str(m.HERE/"run_c01_native.jl"),
                    str(folder/"INPUT.toml"),str(folder)],folder,env,600)
                verify_input(folder,inp)
                p.check_conversion(tomllib.loads((folder/"CONVERSION.toml").read_text()),inp)
                a=validate(tomllib.loads((folder/"NATIVE.toml").read_text()),inp)
                a["diagnostic_review"]=diagnostic_review(a,inp["T_C"])
                s2.write_json(folder/"AUDIT.json",a)
                reports.append(a)
                print("C01_RUN",name,rep,json.dumps({k:v for k,v in a.items() if k!="phase_instances"},sort_keys=True,allow_nan=False),flush=True)
            cases[name]={"first":reports[0],"second":reports[1],"repeatability_absolute_deltas":compare(*reports)}
        need(launched==12,"C01_PROCESS_BUDGET")
        s2.write_json(OUT/"EVALUATION.json",{"status":"C01_MB_NUMERICAL_RESEARCH_SCREEN_PASS",
            "cases":cases,"fresh_processes_completed":launched,"scientific_promotion":False,**SCOPE})
        files={str(f.relative_to(OUT)):s2.sha(f) for f in sorted(OUT.rglob("*")) if f.is_file()}
        s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C01_MB_CAMPAIGN_MANIFEST_V1","source_sha":head,
            "preflight_manifest_sha256":PRE_SHA,"files_sha256":files,"fresh_processes_completed":launched,
            "science":"UNVALIDATED_NONCANONICAL_RESEARCH",**SCOPE})
        print("C01_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
        print("C01_MB_NUMERICAL_RESEARCH_SCREEN_PASS")
    except BaseException as e:
        s2.write_json(OUT/"FAILURE.json",{"status":"C01_FAILED_PRESERVE_ALL","process_launch_attempts":launched,
            "error":str(e),"traceback":traceback.format_exc(),**SCOPE})
        raise


if __name__=="__main__":
    main()
