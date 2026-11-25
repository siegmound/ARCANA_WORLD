"""Consolidate C02 and audit regional T0 material support, without solver calls.
Exact P/T-coordinate coincidence is NOT a physical material assignment or EOS coverage.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import json
import tomllib
from experiments.r6_thermo_provider_pilot_v1 import run_c02_fair as q

p=q.p
c=p.c
m=q.m
s2=q.s2
need=q.need
SCOPE=m.SCOPE
CAMPAIGN_HEAD="4dd92dcc8b449c548402c7e4d82c107e09f51cc9"
CAMPAIGN_SHA="60fe095a91a7fc2c4a2900512380b40a2e9f5ea8b7accec03c6e2a2df4306558"
PT_SHA="515eb9f3fd523035d1ddba2ff2252380dc95bac7dec6d99033f37051fcef0a6f"
OUT=s2.BASE/"R6_THERMO_C02_CONSOLIDATED_REGIONAL_COVERAGE_NEW01"
FILES=("INPUT.toml","CONVERSION.toml","NATIVE.toml","LAUNCH.json","LAUNCH_STDOUT.log","AUDIT.json")
FAMILIES={"crust":("LCC","MORB","UCC","MCC"),"mantle_lithosphere":("MANTLE",)}


def expected_members():
    return {"PROVENANCE.json","EVALUATION.json"} | {
        f"{name}_{rep:02d}/{file}" for name in q.IDS for rep in (1,2) for file in FILES}


def audit_c02(root):
    inputs,prior=q.audit_preflight(root)
    sel=q.load_selection(q.SELECTION_PATH)
    man=m.archive_manifest(q.OUT,CAMPAIGN_SHA,"files_sha256")
    need(man["schema"]=="R6_C02_IG_CAMPAIGN_MANIFEST_V1"
        and man["source_sha"]==CAMPAIGN_HEAD
        and man["preflight_manifest_sha256"]==q.PRE_SHA
        and man["library_manifest_sha256"]==p.C02_SHA
        and man["fresh_processes_completed"]==8
        and man["science"]=="UNVALIDATED_NONCANONICAL_RESEARCH"
        and all(man[k]==v for k,v in SCOPE.items())
        and len(expected_members())==50 and set(man["files_sha256"])==expected_members(),
        "C02_CONSOLIDATE_MANIFEST_SCOPE")
    prov=json.loads((q.OUT/"PROVENANCE.json").read_text())
    need(prov["source_sha"]==CAMPAIGN_HEAD and prov["selection"]==sel
        and prov["inputs"]==inputs and prov["preflight_manifest_sha256"]==q.PRE_SHA
        and prov["library_manifest_sha256"]==p.C02_SHA
        and prov["pressure_semantics"]=="COMMON_HYPOTHETICAL_COMPARATIVE_PT_NOT_SPATIAL_ASSIGNMENT"
        and all(prov[k]==v for k,v in SCOPE.items())
        and all(prov[k]==prior[k] for k in ("julia_binary_sha256","julia_project_sha256","julia_manifest_sha256")),
        "C02_CONSOLIDATE_PROVENANCE")
    ev=json.loads((q.OUT/"EVALUATION.json").read_text())
    rec=json.loads((m.HERE/"c02_campaign_fair_receipt_v1.json").read_text())
    need(rec["source_sha"]==CAMPAIGN_HEAD and rec["manifest_sha256"]==CAMPAIGN_SHA
        and rec["preflight_manifest_sha256"]==q.PRE_SHA and rec["exit"]==0
        and rec["marker"]==ev["status"]=="C02_IG_NUMERICAL_RESEARCH_SCREEN_PASS"
        and ev["fresh_processes_completed"]==rec["fresh_processes_completed"]==8
        and ev["scientific_promotion"] is False and all(ev[k]==v for k,v in SCOPE.items())
        and set(ev["cases"])==set(inputs)==set(rec["selected_observations"]),
        "C02_CONSOLIDATE_EVALUATION")
    first={}
    for name,inp in inputs.items():
        reports=[]
        for rep in (1,2):
            folder=q.OUT/f"{name}_{rep:02d}"
            q.read_conversion(folder,inp)
            a=q.validate(tomllib.loads((folder/"NATIVE.toml").read_text()),inp)
            a["diagnostic_review"]=q.old.diagnostic_review(a,inp["T_C"])
            need(a==json.loads((folder/"AUDIT.json").read_text()),"C02_CONSOLIDATE_NATIVE_REPLAY")
            z=rec["selected_observations"][name]
            need(all(a[k]==z[k] for k in ("rho_kg_m3","G_system","residual","phase_component_closure"))
                and a["aggregate_mass_fractions"][1]==z["melt_mass_fraction"]
                and a["native_diagnostics"]["Cp_fixed_phase_J_kg_K"]==z["Cp_fixed_phase_J_kg_K"]
                and a["diagnostic_review"]["algebraic_identity_status"]==z["algebraic_identity_status"],
                "C02_CONSOLIDATE_RECEIPT_DRIFT")
            reports.append(a)
        need({"first":reports[0],"second":reports[1],"repeatability_absolute_deltas":q.old.compare(*reports)}
            ==ev["cases"][name],"C02_CONSOLIDATE_REPEAT_REPLAY")
        first[name]=reports[0]
    return inputs,first


def consolidate(lib,inputs,first,head):
    result=deepcopy(lib)
    result.update(schema="R6_C02_CONSOLIDATED_EXACT_RESEARCH_LIBRARY_V1",source_sha=head,
        upstream_library_manifest_sha256=p.C02_SHA,C02_campaign_manifest_sha256=CAMPAIGN_SHA,
        source_solver_processes=62,additional_engine_runs=0)
    for name,inp in inputs.items():
        x=c.l.chemistry_id(inp)
        k=c.key(c.IG,x,inp["P_kbar"],inp["T_C"])
        need(k not in result["states"],"C02_CONSOLIDATE_DUPLICATE")
        raw=tomllib.loads((q.OUT/f"{name}_01"/"NATIVE.toml").read_text())
        a=first[name]
        result["states"][k]={"case":name,"model_identity":c.IG,"chemistry_sha256":x,
            "P_kbar":inp["P_kbar"],"T_C":inp["T_C"],"input":inp,"audit":a,
            "phase_instances":deepcopy(a["phase_instances"]),
            "native_bulk_mass_fractions":dict(zip(raw["oxides"],raw["bulk_wt"],strict=True)),
            "source_archive":q.OUT.name,"source_manifest_sha256":CAMPAIGN_SHA,
            "native_sources":[{"relative_path":f"{name}_{rep:02d}/NATIVE.toml",
                "sha256":s2.sha(q.OUT/f"{name}_{rep:02d}/NATIVE.toml")} for rep in (1,2)],
            "pressure_semantics":"HYPOTHETICAL_SOLVER_PRESSURE","authority":"RESEARCH_SAMPLE_ONLY","spatial_assignment":None}
    need(len(result["states"])==31 and len({v["chemistry_sha256"] for v in result["states"].values()})==14,
        "C02_CONSOLIDATE_COUNTS")
    for k,v in result["states"].items():
        need(k==c.key(v["model_identity"],v["chemistry_sha256"],v["P_kbar"],v["T_C"])
            and c.lookup(result,v["model_identity"],v["chemistry_sha256"],v["P_kbar"],v["T_C"])["state"]==v
            and c.lookup(result,v["model_identity"],v["chemistry_sha256"],v["P_kbar"],v["T_C"]+.123456789)["state"] is None
            and v["spatial_assignment"] is None,"C02_CONSOLIDATE_LOOKUP")
    return result


def family(case):
    if case.startswith(("M01_","M02_","M03_")):
        return "MANTLE"
    for prefix,f in (("C01_LCC_","LCC"),("C01_MORB_","MORB"),("C02_UCC_","UCC"),("C02_MCC_","MCC")):
        if case.startswith(prefix):
            return f
    raise ValueError("C02_UNKNOWN_FAMILY:"+case)


def coordinate(p_kbar,t_c):
    need(m.finite(p_kbar) and p_kbar>=0 and m.finite(t_c) and t_c>-273.15,"C02_COVERAGE_PT")
    return float(p_kbar).hex(),float(t_c).hex()


def coverage(lib,reports):
    # Families are candidate comparison sets, not inferred rock identities.
    index=defaultdict(list)
    counts=Counter()
    for key,v in sorted(lib["states"].items()):
        f=family(v["case"]);counts[f]+=1
        index[f,coordinate(v["P_kbar"],v["T_C"])].append(key)
    need(dict(counts)=={"MANTLE":21,"LCC":3,"MORB":3,"UCC":2,"MCC":2},"C02_COVERAGE_FAMILIES")
    need(len(reports)==2,"C02_COVERAGE_REGIONS")
    rows=[];summary={}
    for extent,record in zip((8,16),reports,strict=True):
        m.d10.summarize(record,extent)  # reuses nodal identity/pressure/five-sample guards
        local=Counter()
        for node in record["original_parent_node_order"]:
            for x in record["original_T0_source_nodes"][str(node)]["source_depth_pt_samples"]:
                layer=x["layer"]
                need(layer in FAMILIES,"C02_COVERAGE_LAYER")
                pk=x["conditional_delta_vertical_overburden_pa"]/1e8
                tc=x["source_PRE_temperature_k"]-273.15
                matches={f:index.get((f,coordinate(pk,tc)),[]) for f in FAMILIES[layer]}
                hit=any(matches.values())
                local[layer,"samples"]+=1
                local[layer,"comparative_coordinate_hits"]+=int(hit)
                local[layer,"unsampled_coordinates"]+=int(not hit)
                if layer=="crust":
                    local[layer,"below_felsic_design_T_min"]+=int(tc<650)
                rows.append({"extent":extent,"parent_node_id":node,"layer":layer,
                    "fraction_of_layer":x["fraction_of_layer"],"source_depth_m":x["source_depth_m"],
                    "source_temperature_K":x["source_PRE_temperature_k"],"conditional_delta_P_kbar":pk,
                    "absolute_pressure_pa":None,"material_recipe":None,"spatial_assignment":None,
                    "candidate_families":list(FAMILIES[layer]),"comparative_coordinate_matches":matches,
                    "coordinate_status":"EXACT_COMPARATIVE_PT_COORDINATE" if hit else "UNSAMPLED_COMPARATIVE_PT",
                    "physical_coverage_status":"UNKNOWN","continuous_EOS_qualified":False,
                    "thermodynamic_derivatives_qualified":False,"rheology_binding":None})
        summary[str(extent)]={layer:{k:v for (l,k),v in sorted(local.items()) if l==layer} for layer in FAMILIES}
    need(len(rows)==3700,"C02_COVERAGE_SAMPLE_COUNT")
    return {"schema":"R6_C02_REGIONAL_MATERIAL_COVERAGE_V1","scope":"COMPARATIVE_PT_ONLY",
        "PT_manifest_sha256":PT_SHA,"family_state_counts":dict(counts),"regions":summary,
        "samples":rows,"physical_material_coverage_count":0,
        "cold_crust_screen_semantics":"BELOW_650C_FELSIC_DESIGN_FILTER_ONLY_NOT_CALIBRATION_BOUND",
        "unresolved_requirements":["absolute_pressure_and_boundary_authority","spatial_chemistry_water_redox",
            "cold_crust_subsolidus_provider_domain","ocean_intrusive_alteration_and_source_promotion",
            "continuous_EOS_and_derivative_qualification","rheology_and_mechanical_binding"],
        "additional_engine_runs":0,**SCOPE}


def original_pt(root):
    d=m.d10
    folder=d.BASE/"R6_G2G3_T0_LITHOSTATIC_PT_REFERENCE_NEW01"
    need(s2.sha(folder/"MANIFEST.json")==PT_SHA,"C02_COVERAGE_PT_MANIFEST")
    _,archived,audit=d.cold._load_original_pt(folder)
    a,b,expected=d.pt.build(root,d.BASE/"R6_G2G3_PHYSICAL_SOURCE_PACKET_8X8_NEW02",
        d.BASE/"R6_G2G3_PHYSICAL_SOURCE_PACKET_16X16_NEW02",
        d.BASE/"R6_G2G3_SOURCE_TO_COUPLED_AUTHORING_NEW01")
    need(archived==[a,b] and audit==expected,"C02_COVERAGE_PT_REPLAY")
    return archived


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C02_CONSOLIDATE_CHECKOUT")
    need(not OUT.exists(),"C02_CONSOLIDATE_OUTPUT_EXISTS")
    inputs,first=audit_c02(root)
    print("C02_INDEPENDENT_CAMPAIGN_REPLAY_PASS",CAMPAIGN_SHA,50,flush=True)
    lib=consolidate(json.loads((c.OUT/"LIBRARY.json").read_text()),inputs,first,head)
    report=coverage(lib,original_pt(root))
    OUT.mkdir(parents=False,exist_ok=False)
    s2.write_json(OUT/"LIBRARY.json",lib)
    s2.write_json(OUT/"REGIONAL_COVERAGE.json",report)
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C02_CONSOLIDATED_REGIONAL_COVERAGE_MANIFEST_V1",
        "source_sha":head,"C02_campaign_manifest_sha256":CAMPAIGN_SHA,"previous_library_manifest_sha256":p.C02_SHA,
        "PT_manifest_sha256":PT_SHA,"states":31,"chemistries":14,"source_solver_processes":62,
        "samples":3700,"additional_engine_runs":0,
        "files_sha256":{x:s2.sha(OUT/x) for x in ("LIBRARY.json","REGIONAL_COVERAGE.json")},**SCOPE})
    print("C02_CONSOLIDATED_LIBRARY",31,14,62)
    print("C02_REGIONAL_COVERAGE",json.dumps(report["regions"],sort_keys=True))
    print("C02_CONSOLIDATION_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
    print("C02_CONSOLIDATION_AND_REGIONAL_COVERAGE_COMPLETE")
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()
