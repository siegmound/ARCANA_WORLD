"""Prepared C02 felsic research campaign; fail closed until explicit selection exists."""
from __future__ import annotations
import argparse
import json
import os
import tomllib
import traceback
from experiments.r6_thermo_provider_pilot_v1 import c02_conversion_preflight as p
from experiments.r6_thermo_provider_pilot_v1 import run_c01_fair as old

m=p.m
s2=p.s2
need=p.need
OUT=s2.BASE/"R6_THERMO_C02_IG_FELSIC_CAMPAIGN_NEW01"
PRE_SHA="1fddd5ffaacee41387e01ab4312e43fff2468ca3b68ec99744f564253e8ece37"
PRE_HEAD="517b55b5433b37ed2920cef04cab22b67e9745e3"
IDS=["C02_UCC_BASE","C02_UCC_WET","C02_MCC_BASE","C02_MCC_WET"]
SCOPE=m.SCOPE
SELECTION="C02_NONCANONICAL_RESEARCH_APPROVAL_20261125"
SELECTION_PATH=m.HERE/"c02_research_selection_v1.json"


def check_selection(sel):
    need(sel["selection_id"]==SELECTION
        and sel["authorial_statement"]=="Approvo tutte e quattro le ipotesi sperimentali C02 come ricerca non canonica."
        and sel["library_manifest_sha256"]==p.C02_SHA and sel["preflight_manifest_sha256"]==PRE_SHA
        and sel["case_order"]==IDS and sel["model_identity"]==p.c.IG
        and sel["repeats"]==2 and sel["maximum_solver_calls"]==8 and sel["threads"]==1
        and sel["process_timeout_s"]==600 and all(sel[k]==v for k,v in SCOPE.items())
        and sel["scientific_promotion"] is False,"C02_SELECTION_SCOPE")


def load_selection(path):
    need(path.is_file(),"C02_EXPLICIT_AUTHORIAL_SELECTION_REQUIRED")
    sel=json.loads(path.read_text())
    check_selection(sel)
    return sel


def audit_preflight(root):
    d=p.audit_library(root)
    inputs=p.recipes(d)
    need(list(inputs)==IDS,"C02_CASE_ORDER")
    man=m.archive_manifest(p.OUT,PRE_SHA,"files_sha256")
    expected={"PROVENANCE.json","EVALUATION.json"}
    for name in inputs:
        expected.update(f"{name}/{x}" for x in ("INPUT.toml","CONVERSION.toml","LAUNCH.json","LAUNCH_STDOUT.log"))
    need(man["schema"]=="R6_C02_IG_CONVERSION_PREFLIGHT_V1" and man["source_sha"]==PRE_HEAD
        and man["C02_manifest_sha256"]==p.C02_SHA and man["conversion_processes"]==4
        and len(expected)==18 and set(man["files_sha256"])==expected
        and all(man[k]==v for k,v in p.SCOPE.items()),"C02_PREFLIGHT_SCOPE")
    prov=json.loads((p.OUT/"PROVENANCE.json").read_text())
    need(prov["source_sha"]==PRE_HEAD and prov["C02_manifest_sha256"]==p.C02_SHA
        and prov["inputs"]==inputs and prov["model_candidate"]==p.c.IG
        and all(prov[k]==v for k,v in p.SCOPE.items()),"C02_PREFLIGHT_PROVENANCE")
    ev=json.loads((p.OUT/"EVALUATION.json").read_text())
    rec=json.loads((m.HERE/"c02_conversion_fair_receipt_v1.json").read_text())
    need(rec["manifest_sha256"]==PRE_SHA and ev["status"]=="C02_CONVERSION_PREFLIGHT_PASS__SELECTION_PENDING"
        and ev["input_preserved_count"]==4 and ev["thermodynamic_equilibrium_qualified"] is False
        and all(ev[k]==v for k,v in p.SCOPE.items())
        and set(ev["cases"])==set(rec["selected_observations"])==set(inputs),"C02_PREFLIGHT_EVALUATION")
    for name,inp in inputs.items():
        a=read_conversion(p.OUT/name,inp)
        need(a==ev["cases"][name] and all(a[k]==v for k,v in rec["selected_observations"][name].items()),
            "C02_PREFLIGHT_REPLAY_DRIFT")
    return inputs,prov


def read_conversion(folder,inp):
    old.verify_input(folder,inp)
    launch=json.loads((folder/"LAUNCH.json").read_text())
    need(launch["exit_code"]==0 and launch["timeout"] is False,"C02_LAUNCH_FAILED")
    a=p.review(tomllib.loads((folder/"CONVERSION.toml").read_text()),inp)
    need(a["status"]=="INPUT_PRESERVED","C02_NATIVE_CONVERSION_CHANGED_INPUT")
    return a


def basis_delta(ox,v,expected):
    need(isinstance(ox,list) and len(ox)==len(m.NATIVE) and set(ox)==m.NATIVE
        and m.valid_fraction(v,len(ox)),"C02_NATIVE_BASIS")
    return max(abs(x-expected[k]) for k,x in zip(ox,v,strict=True))


def validate(c,inp):
    need(c["case"]==inp["case"] and c["status"]==0 and c["database"]=="ig" and c["dataset"]=="tc_ds636","C02_NATIVE_STATUS")
    need(m.within_float64_roundoff(c["P_kbar"],inp["P_kbar"])
        and m.within_float64_roundoff(c["T_C"],inp["T_C"]),"C02_NATIVE_PT")
    ox=c["oxides"];bulk=c["bulk_wt"];ph=c["phases"];frac=c["phase_mass_fractions"];comp=c["phase_comp_wt"]
    wd=basis_delta(ox,bulk,inp["expected_native_wt"])
    md=basis_delta(ox,c["bulk_mol"],inp["expected_native_mol"])
    need(wd<=1e-12 and md<=1e-12,"C02_NATIVE_INPUT_DRIFT")
    need(isinstance(ph,list) and len(ph)>0 and all(isinstance(k,str) and k for k in ph)
        and m.valid_fraction(frac,len(ph)) and len(comp)==len(ph)
        and all(m.valid_fraction(v,len(ox)) for v in comp),"C02_NATIVE_PHASES")
    types=c["phase_types"]
    need(len(types)==len(ph) and all(k in (0,1) for k in types),"C02_PHASE_TYPES")
    closure=max(abs(sum(frac[i]*comp[i][j] for i in range(len(ph)))-bulk[j]) for j in range(len(ox)))
    need(closure<=1e-10 and m.finite(c["bulk_res_norm"]) and 0<=c["bulk_res_norm"]<=1e-9,"C02_NATIVE_CLOSURE")
    need(m.finite(c["rho_kg_m3"]) and c["rho_kg_m3"]>0 and m.finite(c["G_system"]),"C02_NATIVE_PRIMARY")
    aggregate=[c[k] for k in ("solid_wt","melt_wt","fluid_wt")]
    need(m.valid_fraction(aggregate,3),"C02_NATIVE_AGGREGATES")
    # Preserve repeated solution-phase instances, e.g. solvus branches. Never overwrite a dict key.
    totals={};instances=[]
    for name,f,v,typ in zip(ph,frac,comp,types,strict=True):
        totals[name]=totals.get(name,0.)+f
        instances.append({"phase":name,"type":typ,"mass_fraction":f,"component_mass_fractions":dict(zip(ox,v,strict=True))})
    return {"case":inp["case"],"native_input_weight_delta":wd,"native_input_mole_delta":md,
        "phase_component_closure":closure,"residual":c["bulk_res_norm"],"rho_kg_m3":c["rho_kg_m3"],
        "G_system":c["G_system"],"phases":totals,"phase_instances":instances,
        "aggregate_mass_fractions":aggregate,"native_diagnostics":c["native_diagnostics"]}



def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    ap.add_argument("--audit-only",action="store_true")
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C02_CHECKOUT")
    sel=None if args.audit_only else load_selection(SELECTION_PATH)
    inputs,prior=audit_preflight(root)
    print("C02_INDEPENDENT_PREFLIGHT_REPLAY_PASS",PRE_SHA,flush=True)
    if args.audit_only:
        print("ADDITIONAL_ENGINE_RUNS=0")
        return
    paths,previous=m.runtime()
    need(s2.sha(paths["JULIA_BIN"])==prior["julia_binary_sha256"]
        and previous["julia_project_sha256"]==prior["julia_project_sha256"]
        and previous["julia_manifest_sha256"]==prior["julia_manifest_sha256"],"C02_RUNTIME_DRIFT")
    need(not OUT.exists(),"C02_OUTPUT_EXISTS")
    env=os.environ.copy()
    env.update(JULIA_DEPOT_PATH=str(paths["JULIA_DEPOT_PATH"]),JULIA_LOAD_PATH="@:@stdlib",
        JULIA_PKG_OFFLINE="true",JULIA_PKG_PRECOMPILE_AUTO="0",JULIA_NUM_THREADS="1",
        JULIA_NUM_PRECOMPILE_TASKS="1",OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1")
    OUT.mkdir(parents=False,exist_ok=False)
    launched=0
    try:
        s2.write_json(OUT/"PROVENANCE.json",{"source_sha":head,"selection":sel,"inputs":inputs,
            "preflight_manifest_sha256":PRE_SHA,"library_manifest_sha256":p.C02_SHA,
            "runtime_paths":{k:str(v) for k,v in paths.items()},
            **{k:prior[k] for k in ("julia_binary_sha256","julia_project_sha256","julia_manifest_sha256")},
            "pressure_semantics":"COMMON_HYPOTHETICAL_COMPARATIVE_PT_NOT_SPATIAL_ASSIGNMENT",**SCOPE})
        cases={}
        for name,inp in inputs.items():
            reports=[]
            for rep in (1,2):
                folder=OUT/f"{name}_{rep:02d}";folder.mkdir()
                m.input_file(folder/"INPUT.toml",inp)
                need(launched<8,"C02_PROCESS_BUDGET")
                launched+=1
                s2.launch(root,[str(paths["JULIA_BIN"]),"--startup-file=no","--threads=1",
                    "--project="+str(paths["JULIA_PROJECT"]),str(m.HERE/"run_c02_native.jl"),
                    str(folder/"INPUT.toml"),str(folder)],folder,env,600)
                read_conversion(folder,inp)
                a=validate(tomllib.loads((folder/"NATIVE.toml").read_text()),inp)
                a["diagnostic_review"]=old.diagnostic_review(a,inp["T_C"])
                s2.write_json(folder/"AUDIT.json",a)
                reports.append(a)
                print("C02_RUN",name,rep,json.dumps({k:v for k,v in a.items() if k!="phase_instances"},sort_keys=True,allow_nan=False),flush=True)
            cases[name]={"first":reports[0],"second":reports[1],"repeatability_absolute_deltas":old.compare(*reports)}
        need(launched==8,"C02_PROCESS_BUDGET")
        s2.write_json(OUT/"EVALUATION.json",{"status":"C02_IG_NUMERICAL_RESEARCH_SCREEN_PASS",
            "cases":cases,"fresh_processes_completed":launched,"scientific_promotion":False,**SCOPE})
        files={str(f.relative_to(OUT)):s2.sha(f) for f in sorted(OUT.rglob("*")) if f.is_file()}
        s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C02_IG_CAMPAIGN_MANIFEST_V1","source_sha":head,
            "preflight_manifest_sha256":PRE_SHA,"library_manifest_sha256":p.C02_SHA,
            "files_sha256":files,"fresh_processes_completed":launched,"science":"UNVALIDATED_NONCANONICAL_RESEARCH",**SCOPE})
        print("C02_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
        print("C02_IG_NUMERICAL_RESEARCH_SCREEN_PASS")
    except BaseException as e:
        s2.write_json(OUT/"FAILURE.json",{"status":"C02_FAILED_PRESERVE_ALL","process_launch_attempts":launched,
            "error":str(e),"traceback":traceback.format_exc(),**SCOPE})
        raise


if __name__=="__main__":
    main()
