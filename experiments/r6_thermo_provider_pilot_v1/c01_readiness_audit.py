"""C01 readiness: pinned M04 readback and crust reference / P-T source audit.
No engine calls, no authorial selection, no placement, no output mutation.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_m04_material_library as l
from experiments.t0_geochemical_reference_v1 import compile_references as geo

m=l.m
s2=l.s2
need=l.need
M04_SHA="9a4cba29ed0535b8f25b2608329aaa40ab11344bc22b2460c50d2694c4c8ba57"
M04_HEAD="ed64baae5fe2ee44ca79a107d14fbabc1c8c47fa"
BASE_X="f8ebf058efa8a9a5eb9bdd66ea64ed4636c7210b75d0180946b2049c2e3cddff"


def audit_m04(root):
    man=m.archive_manifest(l.OUT,M04_SHA,"files_sha256")
    need(man["source_sha"]==M04_HEAD and man["schema"]=="R6_M04_EXACT_LIBRARY_MANIFEST_V1"
        and man["states"]==21 and man["chemistries"]==4 and man["source_processes"]==42
        and man["additional_engine_runs"]==0 and set(man["files_sha256"])=={"LIBRARY.json"}
        and man["M01_manifest_sha256"]==l.r.M01_SHA and man["M02_manifest_sha256"]==l.q.M02_SHA
        and man["M03_manifest_sha256"]==l.M03_SHA and all(man[k]==v for k,v in m.SCOPE.items()),"C01_M04_SCOPE")
    archived=json.loads((l.OUT/"LIBRARY.json").read_text())
    anchors,_=l.r.audit_m01(root)
    pts,_=l.q.audit_m02(root,anchors)
    ins3,pts3,brackets=l.audit_m03(root,anchors,pts)
    ins1=m.build_inputs(root);ins2=l.r.design(ins1["M01_BASE"])
    rebuilt={"schema":"R6_M04_EXACT_MATERIAL_LIBRARY_V1","source_sha":M04_HEAD,
        "scope":"NONCANONICAL_RESEARCH_EXACT_ONLY","interpolation_authorized":False,
        "state_key_semantics":"unscaled_recipe_sha256:float64_hex_P_kbar:float64_hex_T_C",
        "phase_brackets":brackets,"local_PT_response":l.r.response(anchors["M01_BASE"],pts),
        "states":{},**m.SCOPE}
    for folder,digest,ins,values in ((m.OUT,l.r.M01_SHA,ins1,anchors),
        (l.r.OUT,l.q.M02_SHA,ins2,pts),(l.q.OUT,l.M03_SHA,ins3,pts3)):
        for name,inp in ins.items():
            l.add_state(rebuilt,folder,digest,inp,values[name])
    need(rebuilt==archived and len(rebuilt["states"])==21,"C01_M04_FULL_REBUILD_DRIFT")
    need(l.chemistry_id(ins1["M01_BASE"])==BASE_X
        and l.exact_lookup(archived,BASE_X,m.P,m.T)["state"]["case"]=="M01_BASE"
        and l.exact_lookup(archived,BASE_X,m.P,m.T+.123)["status"]=="UNKNOWN_UNSAMPLED_PT_X","C01_M04_QUERY")
    return archived


def check_design(root):
    d=json.loads((m.HERE/"c01_crust_experimental_design_candidate_v1.json").read_text())
    need(d["status"]=="PROPOSED_NOT_EXECUTABLE" and d["authorial_selection"] is None
        and d["engine_executions_authorized"]==0 and d["max_distinct_cases"]==6
        and d["max_fresh_processes_if_approved"]==12 and d["m04_manifest_sha256"]==M04_SHA
        and all(d[k]==v for k,v in m.SCOPE.items()),"C01_AUTHORITY")
    c=d["references"]["continental_lower"]
    raw,digest=geo.source_bytes(root/c["path"],c["git_blob"])
    records=geo.continental_reference(raw)
    lower=next(x for x in records if x["reference_scope"]=="Lower continental crust")
    need(lower["source_major_oxides_wt_percent"]==c["source_major_oxides_wt"],"C01_RG2014_DRIFT")
    b=d["references"]["basalt_nmorb"]
    need(b["doi"]=="10.1029/2012GC004334" and b["table"]==3 and b["source_column"]=="N-MORB"
        and set(b["rows"])=={"MgO","SiO2","FeO","CaO","Na2O","Al2O3","TiO2","K2O","P2O5","MnO"}
        and all(len(v)==3 and all(m.finite(x) and x>0 for x in v) and type(v[2]) is int for v in b["rows"].values()),
        "C01_MORB_TRANSCRIPTION_SCHEMA")
    p=d["source_state"];pt=d["experimental_PT"]
    need(p["extent"]==8 and p["parent_node_id"]==36748 and p["layer"]=="crust" and p["depth_m"]==21000
        and p["absolute_pressure_pa"] is None and m.close(pt["P_kbar"],p["conditional_delta_P_bar"]/1000)
        and m.close(pt["T_C"],p["T_K"]-273.15),"C01_PT_SEMANTICS")
    need(2<=pt["P_kbar"]<=12 and 600<=pt["T_C"]<=1050,"C01_COMPANION_PT_RECTANGLE")
    need(d["provider"]["database"]=="mb" and d["provider"]["dataset_candidate"]=="tc_ds62"
        and d["provider"]["mbCpx"] is None and d["provider"]["mbIlm"] is None,"C01_MB_OPTIONS_UNSELECTED")
    need(d["scenarios"]==[{"suffix":"BASE","water_wt_amount":.2,"ferric_atom_fraction":.1},
        {"suffix":"WET","water_wt_amount":1.,"ferric_atom_fraction":.1},
        {"suffix":"OXIDIZED","water_wt_amount":.2,"ferric_atom_fraction":.2}],"C01_SCENARIO_DRIFT")
    return d,{"continental_source_sha256":digest,"continental_lower_oxide_sum":sum(c["source_major_oxides_wt"].values()),
        "nmorb_transcribed_oxide_sum":sum(v[0] for v in b["rows"].values()),"nmorb_raw_source_bytes_verified":False,
        "source_record_count":len(records),"provider_native_input_qualified":False}


def verify_pt(d):
    folder=m.d10.BASE/"R6_G2G3_T0_LITHOSTATIC_PT_REFERENCE_NEW01"
    need(s2.sha(folder/"MANIFEST.json")=="515eb9f3fd523035d1ddba2ff2252380dc95bac7dec6d99033f37051fcef0a6f","C01_PT_MANIFEST_DRIFT")
    _,reports,_=m.d10.cold._load_original_pt(folder)
    p=d["source_state"]
    node=reports[0]["original_T0_source_nodes"][str(p["parent_node_id"])]
    samples=[a for a in node["source_depth_pt_samples"] if a["layer"]==p["layer"] and a["source_depth_m"]==p["depth_m"]]
    need(len(samples)==1 and m.close(samples[0]["source_PRE_temperature_k"],p["T_K"],1e-9)
        and m.close(samples[0]["conditional_delta_vertical_overburden_pa"],p["conditional_delta_P_bar"]*1e5,1e-5),"C01_SOURCE_PT_DRIFT")
    need(all(node[k] is None for k in ("absolute_surface_pressure_pa","pore_pressure_pa","effective_pressure_pa","fault_normal_pressure_pa")),
        "C01_PRESSURE_AUTHORITY")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C01_CHECKOUT")
    lib=audit_m04(root)
    print("M04_INDEPENDENT_EXACT_LIBRARY_REBUILD_PASS",M04_SHA,len(lib["states"]),flush=True)
    d,summary=check_design(root)
    verify_pt(d)
    print("C01_SOURCE_REVIEW",json.dumps(summary,sort_keys=True,allow_nan=False))
    print("C01_SOURCE_PT_REPLAY_PASS")
    print("C01_READINESS_AUDIT_COMPLETE__SELECTION_PENDING")
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()
