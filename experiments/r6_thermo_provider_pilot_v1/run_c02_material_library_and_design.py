"""C02 design: audited multi-model exact research library + original hot crust PT selection.
Zero new solver calls, no interpolation or spatial/material promotion.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import json
import tomllib
from experiments.r6_thermo_provider_pilot_v1 import run_c01_fair as c

p=c.p
m=c.m
s2=c.s2
need=c.need
l=p.c.l
geo=p.c.geo
SCOPE=m.SCOPE
C01_SHA="5e710dd1d7144a280f68d721a701066eb7b90ab4b240686282d13a6591269289"
C01_HEAD="8031c39bc29ce52ca3baf3035bca7dc55ce0096a"
OUT=s2.BASE/"R6_THERMO_C02_MULTIMODEL_LIBRARY_DESIGN_NEW01"
IG="MAGEMin_C_2.4.5:ig:tc_ds636:public_defaults_M01"
MB="MAGEMin_C_2.4.5:mb:tc_ds62:mbCpx1_mbIlm0_solver0_optimizer0_Newton1_bufferNONE"
MODELS={IG:{"database":"ig","dataset":"tc_ds636","configuration":"M01 pinned public defaults"},
        MB:{"database":"mb","dataset":"tc_ds62","configuration":p.OPTIONS}}


def key(model,x,p_kbar,t_c):
    need(isinstance(model,str) and model in MODELS,"C02_UNKNOWN_MODEL")
    return model+":"+l.state_key(x,p_kbar,t_c)


def lookup(lib,model,x,p_kbar,t_c):
    v=lib["states"].get(key(model,x,p_kbar,t_c))
    return {"status":"EXACT_RESEARCH_SAMPLE" if v is not None else "UNKNOWN_UNSAMPLED_MODEL_PT_X",
        "state":deepcopy(v),"interpolated":False}


def audit_c01(root):
    d,inputs,sel=c.selected(root)
    c.audit_preflight(inputs)
    p.c.verify_pt(d)
    man=m.archive_manifest(c.OUT,C01_SHA,"files_sha256")
    need(man["source_sha"]==C01_HEAD and man["schema"]=="R6_C01_MB_CAMPAIGN_MANIFEST_V1"
        and man["fresh_processes_completed"]==12 and man["preflight_manifest_sha256"]==c.PRE_SHA
        and all(man[k]==v for k,v in SCOPE.items()),"C02_C01_SCOPE")
    expected={"PROVENANCE.json","EVALUATION.json"}
    for name in inputs:
        for rep in (1,2):
            expected.update(f"{name}_{rep:02d}/{x}" for x in
                ("INPUT.toml","CONVERSION.toml","NATIVE.toml","LAUNCH.json","LAUNCH_STDOUT.log","AUDIT.json"))
    need(len(expected)==74 and set(man["files_sha256"])==expected,"C02_C01_COVERAGE")
    prov=json.loads((c.OUT/"PROVENANCE.json").read_text())
    prior=json.loads((m.OUT/"PROVENANCE.json").read_text())
    need(prov["source_sha"]==C01_HEAD and prov["selection"]==sel and prov["inputs"]==inputs
        and prov["preflight_manifest_sha256"]==c.PRE_SHA and all(prov[k]==v for k,v in SCOPE.items())
        and all(prov[k]==prior[k] for k in ("julia_binary_sha256","julia_project_sha256","julia_manifest_sha256")),"C02_C01_PROVENANCE")
    ev=json.loads((c.OUT/"EVALUATION.json").read_text())
    rec=json.loads((m.HERE/"c01_campaign_fair_receipt_v1.json").read_text())
    need(rec["manifest_sha256"]==C01_SHA and rec["source_sha"]==C01_HEAD
        and ev["status"]=="C01_MB_NUMERICAL_RESEARCH_SCREEN_PASS" and ev["fresh_processes_completed"]==12
        and ev["scientific_promotion"] is False and set(ev["cases"])==set(inputs)
        and set(rec["selected_observations"])==set(inputs),"C02_C01_EVALUATION")
    first={}
    for name,inp in inputs.items():
        reports=[]
        for rep in (1,2):
            folder=c.OUT/f"{name}_{rep:02d}"
            c.verify_input(folder,inp)
            launch=json.loads((folder/"LAUNCH.json").read_text())
            need(launch["exit_code"]==0 and launch["timeout"] is False,"C02_C01_LAUNCH")
            p.check_conversion(tomllib.loads((folder/"CONVERSION.toml").read_text()),inp)
            a=c.validate(tomllib.loads((folder/"NATIVE.toml").read_text()),inp)
            a["diagnostic_review"]=c.diagnostic_review(a,inp["T_C"])
            need(a==json.loads((folder/"AUDIT.json").read_text()),"C02_C01_AUDIT_DRIFT")
            z=rec["selected_observations"][name]
            need(all(a[k]==z[k] for k in ("rho_kg_m3","G_system","residual","phase_component_closure","phases","aggregate_mass_fractions"))
                and a["native_diagnostics"]["Cp_fixed_phase_J_kg_K"]==z["Cp_fixed_phase_J_kg_K"]
                and a["diagnostic_review"]["algebraic_identity_status"]==z["algebraic_identity_status"],"C02_C01_RECEIPT_DRIFT")
            reports.append(a)
        need({"first":reports[0],"second":reports[1],"repeatability_absolute_deltas":c.compare(*reports)}==ev["cases"][name],"C02_C01_REPEAT_REPLAY")
        first[name]=reports[0]
    return inputs,first


def combine(mantle,inputs,crust):
    lib={"schema":"R6_C02_MULTIMODEL_EXACT_RESEARCH_LIBRARY_V1","scope":"NONCANONICAL_EXACT_ONLY",
        "models":MODELS,"interpolation_authorized":False,"state_key_semantics":"model_identity:recipe_sha256:float64_hex_P_kbar:float64_hex_T_C",
        "mantle_phase_brackets":mantle["phase_brackets"],"mantle_local_PT_response":mantle["local_PT_response"],
        "states":{},**SCOPE}
    for v in mantle["states"].values():
        a=deepcopy(v);a["model_identity"]=IG
        k=key(IG,a["chemistry_sha256"],a["P_kbar"],a["T_C"])
        need(k not in lib["states"],"C02_DUPLICATE_STATE")
        lib["states"][k]=a
    for name,inp in inputs.items():
        a=crust[name]
        x=l.chemistry_id(inp);k=key(MB,x,inp["P_kbar"],inp["T_C"])
        need(k not in lib["states"],"C02_DUPLICATE_STATE")
        raw=tomllib.loads((c.OUT/f"{name}_01"/"NATIVE.toml").read_text())
        sources=[]
        for rep in (1,2):
            rel=f"{name}_{rep:02d}/NATIVE.toml"
            sources.append({"relative_path":rel,"sha256":s2.sha(c.OUT/rel)})
        lib["states"][k]={"case":name,"model_identity":MB,"chemistry_sha256":x,"P_kbar":inp["P_kbar"],
            "T_C":inp["T_C"],"input":inp,"audit":a,"phase_instances":deepcopy(a["phase_instances"]),
            "native_bulk_mass_fractions":dict(zip(raw["oxides"],raw["bulk_wt"],strict=True)),
            "source_archive":c.OUT.name,"source_manifest_sha256":C01_SHA,"native_sources":sources,
            "pressure_semantics":"HYPOTHETICAL_SOLVER_PRESSURE","authority":"RESEARCH_SAMPLE_ONLY","spatial_assignment":None}
    return lib


def hot_candidates(record):
    # Design window, NOT validated range of the model. Choose shallower sampled depth first.
    result=[]
    for node_id in record["original_parent_node_order"]:
        node=record["original_T0_source_nodes"][str(node_id)]
        need(node["absolute_surface_pressure_pa"] is None,"C02_PRESSURE_AUTHORITY")
        for v in node["source_depth_pt_samples"]:
            if v["layer"]!="crust":
                continue
            z=v["source_depth_m"];t=v["source_PRE_temperature_k"];pk=v["conditional_delta_vertical_overburden_pa"]/1e8
            need(all(m.finite(x) for x in (z,t,pk)) and z>=0 and t>0 and pk>=0,"C02_PT_SOURCE_INVALID")
            if 650<=t-273.15<=850 and 2<=pk<=15:
                result.append({"parent_node_id":node_id,"depth_m":z,"T_K":t,"T_C":t-273.15,
                    "P_kbar_hypothetical":pk,"absolute_pressure_pa":None})
    return sorted(result,key=lambda x:(x["depth_m"],x["T_K"],x["parent_node_id"]))


def felsic_design(root):
    raw,digest=geo.source_bytes(root/"experiments/t0_geochemical_reference_v1/data/CC__Rudnick_Gao__2014.csv",
        geo.SOURCES["CC__Rudnick_Gao__2014.csv"])
    records=geo.continental_reference(raw)
    refs=[x for x in records if x["reference_scope"] in ("Upper continental crust","Middle continental crust")]
    need(len(refs)==2,"C02_REFERENCE_COUNT")
    folder=m.d10.BASE/"R6_G2G3_T0_LITHOSTATIC_PT_REFERENCE_NEW01"
    need(s2.sha(folder/"MANIFEST.json")=="515eb9f3fd523035d1ddba2ff2252380dc95bac7dec6d99033f37051fcef0a6f","C02_PT_MANIFEST")
    _,reports,_=m.d10.cold._load_original_pt(folder)
    need(len(reports[0]["original_parent_node_order"])==81,"C02_EXTENT")
    pts=hot_candidates(reports[0])
    return {"status":"PROPOSED_NOT_EXECUTABLE" if pts else "UNRESOLVED_NO_SOURCE_PT_IN_DESIGN_WINDOW",
        "source_extent":8,"source_chemistry_sha256":digest,"references":refs,
        "model_candidate":IG,"model_reference":"10.1093/petrology/egy048",
        "model_correction":"https://hpxeosandthermocalc.org/2025/01/06/correction-to-the-holland-et-al-2018-and-tomlinson-holland-2021-models/",
        "model_scope":"PERIDOTITE_THROUGH_GRANITE_IGNEOUS_MODEL_NOT_QUALIFIED_FOR_ALL_CRUST",
        "design_window":{"T_C":[650,850],"P_kbar":[2,15],"is_certified_calibration":False},
        "candidate_count":len(pts),"selected_comparative_source_point":pts[0] if pts else None,
        "first_five_ranked_samples":pts[:5],"pt_semantics":"COMMON_HYPOTHETICAL_PT_NOT_UPPER_MIDDLE_STRATIGRAPHIC_PLACEMENT",
        "proposed_scenarios":[{"suffix":"BASE","water_wt_amount":.2,"ferric_atom_fraction":.1},
            {"suffix":"WET","water_wt_amount":1.,"ferric_atom_fraction":.1}],
        "Cr_policy":"SOURCE_TRACE_Cr_TO_OXIDE_EQUIVALENT_CANDIDATE_REQUIRES_NATIVE_GUARD_CHECK_NO_FLOOR_OVERRIDE",
        "cold_crust_coverage":"UNRESOLVED_REQUIRES_SUITABLE_SUBSOLIDUS_MODELS",
        "authorial_selection":None,"max_proposed_cases":4,"max_proposed_solver_calls":8,
        "authorized_solver_calls":0,**SCOPE}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C02_CHECKOUT")
    mantle=p.c.audit_m04(root)
    inputs,crust=audit_c01(root)
    print("C01_INDEPENDENT_READONLY_REPLAY_PASS",C01_SHA,flush=True)
    lib=combine(mantle,inputs,crust)
    lib["source_sha"]=head
    need(len(lib["states"])==27 and len({v["chemistry_sha256"] for v in lib["states"].values()})==10,"C02_LIBRARY_COUNT")
    a=inputs["C01_LCC_BASE"];x=l.chemistry_id(a)
    need(lookup(lib,MB,x,a["P_kbar"],a["T_C"])["state"]["case"]==a["case"]
        and lookup(lib,IG,x,a["P_kbar"],a["T_C"])["state"] is None
        and lookup(lib,MB,x,a["P_kbar"],a["T_C"]+.123)["state"] is None,"C02_LOOKUP_SMOKE")
    design=felsic_design(root)
    need(not OUT.exists(),"C02_OUTPUT_EXISTS")
    OUT.mkdir(parents=False,exist_ok=False)
    s2.write_json(OUT/"LIBRARY.json",lib)
    s2.write_json(OUT/"C02_FELSIC_DESIGN_CANDIDATE.json",design)
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C02_LIBRARY_DESIGN_MANIFEST_V1","source_sha":head,
        "M04_manifest_sha256":p.c.M04_SHA,"C01_manifest_sha256":C01_SHA,"states":27,"chemistries":10,
        "source_solver_processes":54,"additional_engine_runs":0,
        "files_sha256":{x:s2.sha(OUT/x) for x in ("LIBRARY.json","C02_FELSIC_DESIGN_CANDIDATE.json")},**SCOPE})
    print("C02_LIBRARY_STATES",len(lib["states"]))
    print("C02_MODEL_AWARE_EXACT_AND_UNKNOWN_QUERY_PASS")
    print("C02_FELSIC_DESIGN",json.dumps({k:v for k,v in design.items() if k!="references"},sort_keys=True,allow_nan=False))
    print("C02_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
    print("C02_LIBRARY_DESIGN_COMPLETE")
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()
