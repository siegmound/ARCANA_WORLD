"""C01 chemistry conversion only; no initialization or minimization.
Write-once native conversion evidence, no research selection or canonical promotion.
"""
from __future__ import annotations
import argparse
import json
import os
import tomllib
import traceback
from experiments.r6_thermo_provider_pilot_v1 import c01_readiness_audit as c
from experiments.t0_geochemical_reference_v1.compile_references import git_blob_sha

m=c.m
s2=c.s2
need=c.need
OUT=s2.BASE/"R6_THERMO_C01_MB_CONVERSION_PREFLIGHT_NEW01"
DESIGN_BLOB="fc1540d34414776c849263e6b7023f612b63a30a"
WRAPPER="4e4148395fc4d9ff2eed5b0bf18f363ae97de8f8"
INFO="a4e89099410933577ebd182732705ab472d090cb"
REGISTRY="887cba5331efcf8adff81555f8a58dcd07e59c90"
NAMES=tuple(k for k in m.NAMES if k!="Cr2O3")
NATIVE=(set(NAMES)-{"Fe2O3"})|{"O"}
OPTIONS={"database":"mb","dataset":62,"mbCpx":1,"mbIlm":0,"solver":0,"optimizer":0,"final_Newton_step":1,"buffer":"NONE"}
SCOPE={**m.SCOPE,"authorial_selection":None,"additional_engine_runs":0,"minimization_authorized":False}


def recipes(d):
    result={}
    refs=d["references"]
    for label,ox in (("LCC",refs["continental_lower"]["source_major_oxides_wt"]),
        ("MORB",{k:v[0] for k,v in refs["basalt_nmorb"]["rows"].items()})):
        iron_key="FeO*" if label=="LCC" else "FeO"
        total=sum(ox.values())
        omitted={k:ox[k] for k in ("MnO","P2O5")}
        for spec in d["scenarios"]:
            f=spec["ferric_atom_fraction"];water=spec["water_wt_amount"]
            name=f"C01_{label}_{spec['suffix']}"
            iron=ox[iron_key]/m.MASS["FeO"]
            v={k:ox[k] for k in NAMES if k not in ("FeO","Fe2O3","H2O")}
            v.update(FeO=(1-f)*iron*m.MASS["FeO"],
                     Fe2O3=f*iron*m.MASS["Fe2O3"]/2,H2O=water)
            n={k:v[k]/m.MASS[k] for k in NAMES}
            ferric=n.pop("Fe2O3");n["FeO"]+=2*ferric;n["O"]=ferric
            mol=m.normalized(n);wt=m.normalized({k:x*m.MASS[k] for k,x in n.items()})
            delta_o=v["FeO"]+v["Fe2O3"]-ox[iron_key]
            need(set(mol)==NATIVE and m.close(n["FeO"],iron)
                and m.close(sum(v.values()),total-sum(omitted.values())+water+delta_o)
                and m.close(delta_o,(m.MASS["Fe2O3"]-2*m.MASS["FeO"])*ferric,1e-12),"C01_CHEMICAL_LEDGER")
            result[name]={"case":name,"names":list(NAMES),"wt_amounts":[v[k] for k in NAMES],
                "P_kbar":d["experimental_PT"]["P_kbar"],"T_C":d["experimental_PT"]["T_C"],
                "wrapper_git_blob":WRAPPER,"expected_native_mol":mol,"expected_native_wt":wt,
                "source_major_oxide_sum":total,"omitted_source_oxides_wt":omitted,
                "added_H2O_wt_amount":water,"added_oxygen_from_ferric_split_wt_amount":delta_o,
                "native_oxygen_equivalent_wt_amount":m.MASS["O"]*ferric,
                "native_minus_input_mass_rounding_wt_amount":(m.MASS["O"]-(m.MASS["Fe2O3"]-2*m.MASS["FeO"]))*ferric,
                "ferric_atom_fraction_hypothesis":f,"reduced_input_sum":sum(v.values()),
                "unaccounted_source_mass":None,"source_trace_partition":None}
    return result


def check_conversion(out,inp):
    ox=out["oxides"];v=out["mol_fraction"]
    need(len(ox)==len(NATIVE) and set(ox)==NATIVE and m.valid_fraction(v,len(ox))
        and out["wrapper_git_blob"]==WRAPPER and out["info_git_blob"]==INFO
        and out["registry_git_blob"]==REGISTRY and out["minimization_calls"]==0,"C01_NATIVE_CONVERSION_SCHEMA")
    err=max(abs(x-inp["expected_native_mol"][k]) for k,x in zip(ox,v,strict=True))
    need(err<=1e-12,"C01_NATIVE_CONVERSION_CHANGED_INPUT")
    return err


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C01_PREFLIGHT_CHECKOUT")
    need(git_blob_sha((m.HERE/"c01_crust_experimental_design_candidate_v1.json").read_bytes())==DESIGN_BLOB,"C01_DESIGN_BLOB")
    d,_=c.check_design(root);c.verify_pt(d)
    paths,_=m.runtime()
    inputs=recipes(d)
    need(len(inputs)==6 and not OUT.exists(),"C01_PREFLIGHT_SCOPE")
    env=os.environ.copy()
    env.update(JULIA_DEPOT_PATH=str(paths["JULIA_DEPOT_PATH"]),JULIA_LOAD_PATH="@:@stdlib",
        JULIA_PKG_OFFLINE="true",JULIA_PKG_PRECOMPILE_AUTO="0",JULIA_NUM_THREADS="1",
        JULIA_NUM_PRECOMPILE_TASKS="1",OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1")
    OUT.mkdir(parents=False,exist_ok=False)
    try:
        s2.write_json(OUT/"PROVENANCE.json",{"source_sha":head,"design_git_blob":DESIGN_BLOB,
            "inputs":inputs,"future_solver_options_proposed_not_selected":OPTIONS,**SCOPE})
        summary={}
        for name,inp in inputs.items():
            path=OUT/name;path.mkdir()
            m.input_file(path/"INPUT.toml",inp)
            s2.launch(root,[str(paths["JULIA_BIN"]),"--startup-file=no","--threads=1",
                "--project="+str(paths["JULIA_PROJECT"]),str(m.HERE/"c01_conversion_preflight.jl"),
                str(path/"INPUT.toml"),str(path)],path,env,600)
            out=tomllib.loads((path/"CONVERSION.toml").read_text())
            delta=check_conversion(out,inp)
            summary[name]={"native_mol_delta":delta,"source_oxide_sum":inp["source_major_oxide_sum"],
                "omitted_source_oxides_wt":inp["omitted_source_oxides_wt"],
                "reduced_input_sum":inp["reduced_input_sum"]}
            print("C01_CONVERSION",name,json.dumps(summary[name],sort_keys=True),flush=True)
        s2.write_json(OUT/"EVALUATION.json",{"status":"C01_MB_CONVERSION_PREFLIGHT_PASS__SELECTION_PENDING",
            "cases":summary,"thermodynamic_equilibrium_qualified":False,**SCOPE})
        files={str(f.relative_to(OUT)):s2.sha(f) for f in sorted(OUT.rglob("*")) if f.is_file()}
        s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C01_MB_CONVERSION_PREFLIGHT_V1","source_sha":head,
            "files_sha256":files,"conversion_processes":6,**SCOPE})
        print("C01_PREFLIGHT_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
        print("C01_MB_CONVERSION_PREFLIGHT_PASS__SELECTION_PENDING")
        print("ADDITIONAL_ENGINE_RUNS=0")
    except BaseException as e:
        s2.write_json(OUT/"FAILURE.json",{"status":"C01_PREFLIGHT_FAILED_PRESERVE_ALL","error":str(e),
            "traceback":traceback.format_exc(),**SCOPE})
        raise


if __name__=="__main__":
    main()
