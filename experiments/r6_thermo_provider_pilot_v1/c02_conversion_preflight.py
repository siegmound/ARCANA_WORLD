"""C02 fixed source felsic recipe candidate and conversion-only audit.
No equilibrium call; preserve guard changes rather than accepting them.
"""
from __future__ import annotations
import argparse
import json
import os
import tomllib
import traceback
from experiments.r6_thermo_provider_pilot_v1 import run_c02_material_library_and_design as c

m=c.m
s2=c.s2
need=c.need
p=c.p
OUT=s2.BASE/"R6_THERMO_C02_IG_CONVERSION_PREFLIGHT_NEW01"
C02_SHA="866b3af5fc653224b60b12de30f72e14368137cec1ec072d65d0eb02b3b6be4a"
C02_HEAD="acbb1c1c911381cab00dc47ec7d2d387dce99e42"
POINT={"P_kbar_hypothetical":7.69888,"T_C":778.4081968311126,"T_K":1051.5581968311126,"absolute_pressure_pa":None,"depth_m":28000,"parent_node_id":34587}
SCOPE={**m.SCOPE,"authorial_selection":None,"additional_engine_runs":0,"minimization_authorized":False}
CR_AW=51.9961
O_AW=15.999


def audit_library(root):
    man=m.archive_manifest(c.OUT,C02_SHA,"files_sha256")
    need(man["schema"]=="R6_C02_LIBRARY_DESIGN_MANIFEST_V1" and man["source_sha"]==C02_HEAD
        and man["states"]==27 and man["chemistries"]==10 and man["source_solver_processes"]==54
        and man["additional_engine_runs"]==0 and man["M04_manifest_sha256"]==p.c.M04_SHA
        and man["C01_manifest_sha256"]==c.C01_SHA and all(man[k]==v for k,v in m.SCOPE.items())
        and set(man["files_sha256"])=={"LIBRARY.json","C02_FELSIC_DESIGN_CANDIDATE.json"},"C02_PINNED_LIBRARY_SCOPE")
    lib=json.loads((c.OUT/"LIBRARY.json").read_text())
    mantle=p.c.audit_m04(root)
    inputs,crust=c.audit_c01(root)
    rebuilt=c.combine(mantle,inputs,crust);rebuilt["source_sha"]=C02_HEAD
    need(rebuilt==lib,"C02_LIBRARY_REBUILD_DRIFT")
    d=c.felsic_design(root)
    need(d==json.loads((c.OUT/"C02_FELSIC_DESIGN_CANDIDATE.json").read_text()),"C02_DESIGN_REBUILD_DRIFT")
    rec=json.loads((m.HERE/"c02_library_design_fair_receipt_v1.json").read_text())
    need(rec["manifest_sha256"]==C02_SHA and rec["candidate_count"]==d["candidate_count"]==70
        and rec["selected_comparative_source_point"]==d["selected_comparative_source_point"]==POINT
        and rec["source_chemistry_sha256"]==d["source_chemistry_sha256"],"C02_RECEIPT_DRIFT")
    return d


def recipes(d):
    need(d["status"]=="PROPOSED_NOT_EXECUTABLE" and d["authorial_selection"] is None
        and d["authorized_solver_calls"]==0 and d["selected_comparative_source_point"]==POINT
        and d["proposed_scenarios"]==[{"suffix":"BASE","water_wt_amount":.2,"ferric_atom_fraction":.1},
            {"suffix":"WET","water_wt_amount":1.,"ferric_atom_fraction":.1}],"C02_RECIPE_DESIGN")
    result={}
    refs={x["reference_scope"]:x for x in d["references"]}
    for label,scope in (("UCC","Upper continental crust"),("MCC","Middle continental crust")):
        ref=refs[scope];ox=ref["source_major_oxides_wt_percent"]
        cr=ref["selected_source_trace_elements"]["Cr"]
        need(cr=={"unit":"ppm","value":92. if label=="UCC" else 76.},"C02_CHROMIUM_SOURCE")
        cr_amount=cr["value"]/10000*(2*CR_AW+3*O_AW)/(2*CR_AW)
        omitted={k:ox[k] for k in ("MnO","P2O5")}
        for spec in d["proposed_scenarios"]:
            f=spec["ferric_atom_fraction"];water=spec["water_wt_amount"]
            name=f"C02_{label}_{spec['suffix']}"
            n=ox["FeO*"]/m.MASS["FeO"]
            v={k:ox[k] for k in m.NAMES if k not in ("FeO","Fe2O3","H2O","Cr2O3")}
            v.update(FeO=(1-f)*n*m.MASS["FeO"],Fe2O3=f*n*m.MASS["Fe2O3"]/2,H2O=water,Cr2O3=cr_amount)
            mol,wt=m.expected_basis(v)
            delta_o=v["FeO"]+v["Fe2O3"]-ox["FeO*"]
            need(m.close(v["FeO"]/m.MASS["FeO"]+2*v["Fe2O3"]/m.MASS["Fe2O3"],n)
                and m.close(sum(v.values()),sum(ox.values())-sum(omitted.values())+water+delta_o+cr_amount),
                "C02_CHEMICAL_LEDGER")
            result[name]={"case":name,"P_kbar":POINT["P_kbar_hypothetical"],"T_C":POINT["T_C"],
                "names":list(m.NAMES),"wt_amounts":[v[k] for k in m.NAMES],"wrapper_git_blob":p.WRAPPER,
                "expected_native_mol":mol,"expected_native_wt":wt,"source_major_oxide_sum":sum(ox.values()),
                "omitted_source_oxides_wt":omitted,"Cr_source_ppm":cr["value"],"Cr2O3_equivalent_wt_amount":cr_amount,
                "Cr_semantics":"STOICHIOMETRIC_EQUIVALENT_NOT_MEASURED_OXIDATION_STATE",
                "source_trace_elements":ref["selected_source_trace_elements"],
                "added_H2O_wt_amount":water,"ferric_atom_fraction_hypothesis":f,
                "added_oxygen_from_ferric_split_wt_amount":delta_o,
                "native_minus_input_mass_rounding_wt_amount":(m.MASS["O"]-m.MASS["Fe2O3"]+2*m.MASS["FeO"])*f*n/2,
                "reduced_input_sum":sum(v.values()),"unaccounted_source_mass":None,"source_trace_partition":None}
    return result


def review(out,inp):
    ox=out["oxides"];v=out["mol_fraction"]
    need(len(ox)==len(m.NATIVE) and set(ox)==m.NATIVE and m.valid_fraction(v,len(ox))
        and out["wrapper_git_blob"]==p.WRAPPER and out["info_git_blob"]==p.INFO
        and out["registry_git_blob"]==p.REGISTRY and out["minimization_calls"]==0,"C02_CONVERSION_SCHEMA")
    deltas={k:x-inp["expected_native_mol"][k] for k,x in zip(ox,v,strict=True)}
    err=max(map(abs,deltas.values()))
    return {"status":"INPUT_PRESERVED" if err<=1e-12 else "BLOCKED_NATIVE_GUARD_OR_CONVERSION_CHANGED_INPUT",
        "native_mol_delta":err,"component_mole_fraction_delta":deltas,
        "Cr2O3_expected_mole_fraction":inp["expected_native_mol"]["Cr2O3"],
        "Cr2O3_native_mole_fraction":dict(zip(ox,v,strict=True))["Cr2O3"],
        "Cr2O3_equivalent_wt_amount":inp["Cr2O3_equivalent_wt_amount"],"reduced_input_sum":inp["reduced_input_sum"]}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C02_PREFLIGHT_CHECKOUT")
    d=audit_library(root)
    print("C02_INDEPENDENT_LIBRARY_DESIGN_REPLAY_PASS",C02_SHA,flush=True)
    inputs=recipes(d)
    paths,previous=m.runtime()
    prior=json.loads((m.OUT/"PROVENANCE.json").read_text())
    need(s2.sha(paths["JULIA_BIN"])==prior["julia_binary_sha256"]
        and previous["julia_project_sha256"]==prior["julia_project_sha256"]
        and previous["julia_manifest_sha256"]==prior["julia_manifest_sha256"],"C02_RUNTIME_DRIFT")
    need(len(inputs)==4 and not OUT.exists(),"C02_PREFLIGHT_SCOPE")
    env=os.environ.copy()
    env.update(JULIA_DEPOT_PATH=str(paths["JULIA_DEPOT_PATH"]),JULIA_LOAD_PATH="@:@stdlib",
        JULIA_PKG_OFFLINE="true",JULIA_PKG_PRECOMPILE_AUTO="0",JULIA_NUM_THREADS="1",
        JULIA_NUM_PRECOMPILE_TASKS="1",OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1")
    OUT.mkdir(parents=False,exist_ok=False)
    try:
        s2.write_json(OUT/"PROVENANCE.json",{"source_sha":head,"C02_manifest_sha256":C02_SHA,
            "inputs":inputs,"model_candidate":c.IG,"runtime_paths":{k:str(v) for k,v in paths.items()},
            **{k:prior[k] for k in ("julia_binary_sha256","julia_project_sha256","julia_manifest_sha256")},**SCOPE})
        results={}
        for name,inp in inputs.items():
            folder=OUT/name;folder.mkdir()
            m.input_file(folder/"INPUT.toml",inp)
            s2.launch(root,[str(paths["JULIA_BIN"]),"--startup-file=no","--threads=1",
                "--project="+str(paths["JULIA_PROJECT"]),str(m.HERE/"c02_conversion_preflight.jl"),
                str(folder/"INPUT.toml"),str(folder)],folder,env,600)
            a=review(tomllib.loads((folder/"CONVERSION.toml").read_text()),inp)
            results[name]=a
            print("C02_CONVERSION",name,json.dumps(a,sort_keys=True,allow_nan=False),flush=True)
        passed=sum(v["status"]=="INPUT_PRESERVED" for v in results.values())
        status="C02_CONVERSION_PREFLIGHT_PASS__SELECTION_PENDING" if passed==4 else "C02_CONVERSION_PREFLIGHT_COMPLETE__INPUT_DRIFT_BLOCKED"
        s2.write_json(OUT/"EVALUATION.json",{"status":status,"cases":results,"input_preserved_count":passed,
            "thermodynamic_equilibrium_qualified":False,**SCOPE})
        files={str(f.relative_to(OUT)):s2.sha(f) for f in sorted(OUT.rglob("*")) if f.is_file()}
        s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C02_IG_CONVERSION_PREFLIGHT_V1","source_sha":head,
            "C02_manifest_sha256":C02_SHA,"files_sha256":files,"conversion_processes":4,**SCOPE})
        print("C02_PREFLIGHT_INPUT_PRESERVED",passed,4)
        print("C02_PREFLIGHT_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
        print(status)
        print("ADDITIONAL_ENGINE_RUNS=0")
    except BaseException as e:
        s2.write_json(OUT/"FAILURE.json",{"status":"C02_PREFLIGHT_FAILED_PRESERVE_ALL","error":str(e),
            "traceback":traceback.format_exc(),**SCOPE})
        raise


if __name__=="__main__":
    main()
