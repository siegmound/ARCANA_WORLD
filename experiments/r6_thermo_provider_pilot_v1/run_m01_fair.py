"""M01 bounded approved research campaign. No execution on import."""
from __future__ import annotations
import argparse
import csv
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tomllib
import traceback

from experiments.r6_thermo_provider_pilot_v1 import run_s2_fair as s2
from experiments.r6_thermo_provider_pilot_v1 import s3_d10_t0_pt_relevance as d10
from experiments.r6_thermo_provider_pilot_v1.validate_s2_native import within_float64_roundoff
from experiments.t0_geochemical_reference_v1.compile_references import git_blob_sha

HERE=Path(__file__).resolve().parent
OUT=s2.BASE/"R6_THERMO_M01_MANTLE_CAMPAIGN_NEW01"
S2=s2.BASE/"R6_THERMO_S2_REPEATABILITY_NEW01"
S2_SHA="74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604"
D12=s2.BASE/"R6_T0_B6N8N_EXACT_MEMBERSHIP_NEW01"
D12_SHA="c7a9382755c65392702c05f2c02f1793e56cb54b9a3d927b2bca6b2ed01ad234"
NAMES=("SiO2","Al2O3","CaO","MgO","FeO","Fe2O3","K2O","Na2O","TiO2","Cr2O3","H2O")
MASS=dict(zip(NAMES,(60.08,101.96,56.08,40.30,71.85,159.69,94.2,61.98,79.88,151.99,18.015)))
MASS["O"]=16.0
NATIVE=set(NAMES)-{"Fe2O3"}|{"O"}
CASES=(("M01_BASE",.03,116),("M01_LOW_H2O",.03,58),("M01_HIGH_H2O",.03,174),("M01_HIGH_FERRIC",.053,116))
SCOPE={"material_assignments":0,"physical_T1":None,"mechanical_solve_authorized":False,"WORLD_HISTORY_PRODUCTION_AUTHORIZED":False}
P=16.12444
T=1141.375818001164


def require(ok,code):
    if not ok:
        raise ValueError(code)


def finite(x):
    return type(x) in (int,float) and math.isfinite(x)


def close(a,b,tol=1e-12):
    return finite(a) and finite(b) and abs(a-b)<=tol


def normalized(x):
    require(all(finite(v) and v>=0 for v in x.values()) and sum(x.values())>0,"M01_BAD_COMPOSITION")
    total=sum(x.values())
    return {k:v/total for k,v in x.items()}


def expected_basis(values):
    require(set(values)==set(NAMES),"M01_INPUT_OXIDES")
    n={k:v/MASS[k] for k,v in values.items()}
    f=n.pop("Fe2O3")
    n["FeO"]+=2*f
    n["O"]=f
    return normalized(n),normalized({k:v*MASS[k] for k,v in n.items()})


def build_inputs(root):
    plan=HERE/"m01_mantle_experimental_design_candidate_v1.json"
    raw=plan.read_bytes()
    require(git_blob_sha(raw)=="63dba6466b22bfa79bb3d69f002b20ed72959d71","M01_APPROVED_PROPOSAL_DRIFT")
    design=json.loads(raw)
    selected=json.loads((HERE/"m01_research_selection_v1.json").read_text())
    require(selected["selection_id"]=="M01_NONCANONICAL_RESEARCH_APPROVAL_20261125"
            and selected["proposal_git_blob"]==git_blob_sha(raw)
            and selected["case_order"]==[x[0] for x in CASES]
            and selected["repeats"]==2 and selected["maximum_solver_calls"]==8
            and selected["threads"]==1 and selected["process_timeout_s"]==600
            and all(selected[k]==v for k,v in SCOPE.items()),"M01_SELECTION_SCOPE")
    source=design["source_reference"]
    raw=(root/source["path"]).read_bytes()
    require(git_blob_sha(raw)==source["git_blob"]=="262447b687f5cae36fde836ffd12c7d439a9f16b","M01_SOURCE_DRIFT")
    rows={x["Element"]:x for x in csv.DictReader(io.StringIO("\n".join(l for l in raw.decode().splitlines() if l and not l.startswith("#"))))}
    for k,v in source["records"].items():
        require(float(rows[k]["Model"])==v["value"] and rows[k]["Unit"]==v["unit"]
            and rows[k]["Constraint"]==v["constraint"]
            and float(rows[k]["Uncertainty in %"])==v["reported_uncertainty_percent"],"M01_SOURCE_RECORD_DRIFT:"+k)
    record=source["records"]
    aw=design["conventions"]["element_oxide_equivalent_atomic_weights"]
    minor={}
    for el,name,a,b in (("K","K2O",2,1),("Ti","TiO2",1,2),("Cr","Cr2O3",2,3)):
        minor[name]=record[el]["value"]/10000*(a*aw[el]+b*aw["O"])/(a*aw[el])
    require(design["experimental_PT_choice"]["P_kbar"]==P and design["experimental_PT_choice"]["T_C"]==T,"M01_PT_DESIGN_DRIFT")
    result={}
    for spec,(name,f,h) in zip(design["proposed_cases"],CASES,strict=True):
        require((spec["id"],spec["ferric_atom_fraction"],spec["water_source_ppm"])==(name,f,h),"M01_CASE_DRIFT")
        values={k:record[k]["value"] for k in ("SiO2","Al2O3","CaO","MgO","FeO","Na2O")}
        n=values["FeO"]/MASS["FeO"]
        values["FeO"]=(1-f)*n*MASS["FeO"]
        values["Fe2O3"]=f*n*MASS["Fe2O3"]/2
        values.update(minor,H2O=h/10000)
        require(all(close(values[k],spec["input_wt_amounts_unscaled"][k]) for k in NAMES)
                and close(sum(values.values()),spec["input_sum"])
                and close(values["FeO"]/MASS["FeO"]+2*values["Fe2O3"]/MASS["Fe2O3"],n),"M01_STOICHIOMETRY_DRIFT")
        mol,wt=expected_basis(values)
        result[name]={"case":name,"P_kbar":P,"T_C":T,"names":list(NAMES),
            "wt_amounts":[values[k] for k in NAMES],"expected_native_mol":mol,
            "expected_native_wt":wt,"input_total":sum(values.values()),
            "wrapper_git_blob":selected["wrapper_git_blob"]}
    return result


def archive_manifest(folder,digest,key):
    path=folder/"MANIFEST.json"
    require(s2.sha(path)==digest,"M01_UPSTREAM_MANIFEST_DRIFT")
    m=json.loads(path.read_text())
    for rel,expected in m[key].items():
        f=(folder/rel).resolve()
        require(f.is_relative_to(folder.resolve()) and f.is_file() and s2.sha(f)==expected,"M01_UPSTREAM_FILE_DRIFT:"+rel)
    return m


def runtime():
    m=archive_manifest(S2,S2_SHA,"files_sha256")
    require(len(m["files_sha256"])==68 and m["source_sha"]=="632c4a570f876e3963b1dcd8a1f411a143fc8a59","M01_S2_SCOPE")
    archive_manifest(D12,D12_SHA,"files")
    folder=d10.BASE/"R6_G2G3_T0_LITHOSTATIC_PT_REFERENCE_NEW01"
    require(s2.sha(folder/"MANIFEST.json")=="515eb9f3fd523035d1ddba2ff2252380dc95bac7dec6d99033f37051fcef0a6f","M01_PT_MANIFEST_DRIFT")
    _,reports,_=d10.cold._load_original_pt(folder)
    samples=reports[0]["original_T0_source_nodes"]["36025"]["source_depth_pt_samples"]
    matching=[x for x in samples if x["layer"]=="mantle_lithosphere" and x["source_depth_m"]==54000]
    require(len(matching)==1 and close(matching[0]["source_PRE_temperature_k"],T+273.15,1e-9)
        and close(matching[0]["conditional_delta_vertical_overburden_pa"],P*1e8,1e-5),"M01_SOURCE_PT_DRIFT")
    p=json.loads((S2/"RUN_PROVENANCE.json").read_text())
    paths={k:Path(p["runtime_paths"][k]).resolve() for k in ("JULIA_BIN","JULIA_PROJECT","JULIA_DEPOT_PATH")}
    jb,jp,jd=(paths[k] for k in ("JULIA_BIN","JULIA_PROJECT","JULIA_DEPOT_PATH"))
    require(jb.is_file() and os.access(jb,os.X_OK) and jd.is_dir()
        and s2.sha(jp/"Project.toml")==p["julia_project_sha256"]
        and s2.sha(jp/"Manifest.toml")==p["julia_manifest_sha256"],"M01_RUNTIME_HASH_DRIFT")
    require(subprocess.check_output([str(jb),"--version"],text=True,timeout=30).strip()=="julia version 1.10.4","M01_JULIA_DRIFT")
    manifest=tomllib.loads((jp/"Manifest.toml").read_text())
    dep=manifest["deps"]
    require(dep["MAGEMin_C"][0]["version"]=="2.4.5" and dep["MAGEMin_jll"][0]["version"]=="2.1.0+0","M01_PACKAGE_VERSION_DRIFT")
    return paths,p


def input_file(path,inp):
    with path.open("x") as f:
        for k in ("case","P_kbar","T_C","names","wt_amounts","wrapper_git_blob"):
            f.write(k+" = "+json.dumps(inp[k],allow_nan=False)+"\n")
        f.write("[expected_native_mol]\n")
        for k,v in inp["expected_native_mol"].items():
            f.write(k+" = "+repr(v)+"\n")


def valid_fraction(x,n):
    return isinstance(x,list) and len(x)==n and all(finite(v) and -1e-13<=v<=1+1e-13 for v in x) and abs(sum(x)-1)<=1e-8


def basis_delta(names,values,expected):
    require(isinstance(names,list) and len(names)==len(NATIVE) and set(names)==NATIVE
        and valid_fraction(values,len(names)),"M01_NATIVE_BASIS")
    return max(abs(v-expected[k]) for k,v in zip(names,values))


def validate(c,inp):
    require(c["case"]==inp["case"] and c["status"]==0 and c["database"]=="ig" and c["dataset"]=="tc_ds636","M01_NATIVE_STATUS")
    require(within_float64_roundoff(c["P_kbar"],inp["P_kbar"]) and within_float64_roundoff(c["T_C"],inp["T_C"]),"M01_NATIVE_PT")
    ox=c["oxides"];bulk=c["bulk_wt"];ph=c["phases"];frac=c["phase_mass_fractions"];comp=c["phase_comp_wt"]
    wd=basis_delta(ox,bulk,inp["expected_native_wt"])
    md=basis_delta(ox,c["bulk_mol"],inp["expected_native_mol"])
    require(wd<=1e-12 and md<=1e-12,"M01_NATIVE_INPUT_DRIFT")
    require(isinstance(ph,list) and len(ph)>0 and len(set(ph))==len(ph)
        and valid_fraction(frac,len(ph)) and len(comp)==len(ph)
        and all(valid_fraction(v,len(ox)) for v in comp),"M01_NATIVE_PHASES")
    closure=max(abs(sum(frac[i]*comp[i][j] for i in range(len(ph)))-bulk[j]) for j in range(len(ox)))
    require(closure<=1e-10 and finite(c["bulk_res_norm"]) and 0<=c["bulk_res_norm"]<=1e-9,"M01_NATIVE_CLOSURE")
    require(finite(c["rho_kg_m3"]) and c["rho_kg_m3"]>0 and finite(c["G_system"]),"M01_NATIVE_PRIMARY")
    aggregate=[c[k] for k in ("solid_wt","melt_wt","fluid_wt")]
    require(valid_fraction(aggregate,3),"M01_NATIVE_AGGREGATES")
    return {"case":inp["case"],"native_input_weight_delta":wd,"native_input_mole_delta":md,
        "phase_component_closure":closure,"residual":c["bulk_res_norm"],
        "rho_kg_m3":c["rho_kg_m3"],"G_system":c["G_system"],
        "phases":dict(zip(ph,frac)),"aggregate_mass_fractions":aggregate,
        "native_diagnostics":c["native_diagnostics"]}


def compare(a,b):
    require(a["case"]==b["case"] and set(a["phases"])==set(b["phases"]),"M01_REPEAT_PHASE_SET")
    out={}
    for k,x,y,abs_tol,rel_tol in [
        ("rho",a["rho_kg_m3"],b["rho_kg_m3"],.01,1e-6),
        ("G",a["G_system"],b["G_system"],.001,1e-6),
        *[(k,a["phases"][k],b["phases"][k],.0001,.001) for k in sorted(a["phases"])],
        *[(k,x,y,.0001,.001) for k,x,y in zip(("solid","melt","fluid"),a["aggregate_mass_fractions"],b["aggregate_mass_fractions"])]
    ]:
        delta=abs(x-y)
        require(delta<=abs_tol+rel_tol*max(abs(x),abs(y)),"M01_REPEAT_DRIFT:"+k)
        out[k]=delta
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha",required=True)
    args=parser.parse_args()
    root,head=s2.verify_checkout()
    require(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"M01_SOURCE_CHECKOUT")
    inputs=build_inputs(root)
    paths,previous=runtime()
    require(not OUT.exists(),"M01_OUTPUT_WRITE_ONCE")
    env=os.environ.copy()
    env.update(JULIA_DEPOT_PATH=str(paths["JULIA_DEPOT_PATH"]),JULIA_LOAD_PATH="@:@stdlib",
        JULIA_PKG_OFFLINE="true",JULIA_PKG_PRECOMPILE_AUTO="0",JULIA_NUM_THREADS="1",
        JULIA_NUM_PRECOMPILE_TASKS="1",OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1")
    OUT.mkdir(parents=False,exist_ok=False)
    launched=0
    try:
        s2.write_json(OUT/"PROVENANCE.json",{"source_sha":head,"selection_id":"M01_NONCANONICAL_RESEARCH_APPROVAL_20261125",
            "s2_manifest_sha256":S2_SHA,"membership_manifest_sha256":D12_SHA,
            "runtime_paths":{k:str(v) for k,v in paths.items()},"julia_project_sha256":previous["julia_project_sha256"],
            "julia_manifest_sha256":previous["julia_manifest_sha256"],"julia_binary_sha256":s2.sha(paths["JULIA_BIN"]),
            "inputs":inputs,**SCOPE})
        result={}
        for name,inp in inputs.items():
            reports=[]
            for repeat in (1,2):
                run=OUT/f"{name}_{repeat:02d}"
                run.mkdir()
                input_file(run/"INPUT.toml",inp)
                launched+=1
                s2.launch(root,[str(paths["JULIA_BIN"]),"--startup-file=no","--threads=1",
                    "--project="+str(paths["JULIA_PROJECT"]),str(HERE/"run_m01_native.jl"),
                    str(run/"INPUT.toml"),str(run)],run,env,600)
                conversion=tomllib.loads((run/"CONVERSION.toml").read_text())
                require(basis_delta(conversion["oxides"],conversion["mol_fraction"],inp["expected_native_mol"])<=1e-12,"M01_CONVERSION_DRIFT")
                c=tomllib.loads((run/"NATIVE.toml").read_text())
                checked=validate(c,inp)
                s2.write_json(run/"AUDIT.json",checked)
                reports.append(checked)
                print("M01_RUN",name,repeat,json.dumps(checked,sort_keys=True,allow_nan=False),flush=True)
            result[name]={"repeatability_absolute_deltas":compare(*reports),"first":reports[0],"second":reports[1]}
        s2.write_json(OUT/"EVALUATION.json",{"status":"M01_NUMERICAL_RESEARCH_SCREEN_PASS","cases":result,
            "fresh_processes_completed":launched,"scientific_promotion":False,**SCOPE})
        files={str(f.relative_to(OUT)):s2.sha(f) for f in sorted(OUT.rglob("*")) if f.is_file()}
        s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_M01_CAMPAIGN_MANIFEST_V1","source_sha":head,
            "files_sha256":files,"fresh_processes_completed":launched,"science":"UNVALIDATED_NONCANONICAL_RESEARCH",**SCOPE})
        print("M01_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
        print("M01_NUMERICAL_RESEARCH_SCREEN_PASS")
    except BaseException as e:
        s2.write_json(OUT/"FAILURE.json",{"status":"M01_FAILED_PRESERVE_ALL","process_launch_attempts":launched,
            "error":str(e),"traceback":traceback.format_exc(),**SCOPE})
        raise


if __name__=="__main__":
    main()
