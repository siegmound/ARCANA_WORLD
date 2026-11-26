"""C05: source-keyed column material feasibility and G2/G3 physical closure handoff.

No new equilibrium, no rock placement, no force or mechanical solve.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
from experiments.r6_thermo_provider_pilot_v1 import run_c04_integrated_research_library as q
from experiments.plate58_deforming_explore_v1 import g2_t0_material_trial as trial

c=q.c
s2=q.s2
need=q.need
hgp=q.hgp
PIN="c29e3db62085b79428d86cc3428588c0d7e152c27ef9dc8a039ac32593946a17"
SOURCE="1d5738c11e1f7ef6d175581a964baf0113ad1100"
OUT=s2.BASE/"R6_THERMO_C05_REGIONAL_COLUMN_FEASIBILITY_NEW01"
STATUS="C05_SOURCE_KEYED_COLUMN_FEASIBILITY_AND_PHYSICAL_GAP_HANDOFF_COMPLETE__NO_MATERIAL_SELECTION"
LAYERS=("crust","mantle_lithosphere")
EXPECTED={
    "8":{"crust":(405,68,136,204,201),"mantle_lithosphere":(405,68,0,68,337)},
    "16":{"crust":(1445,160,320,480,965),"mantle_lithosphere":(1445,160,0,160,1285)}}
METRICS=("samples","prior_coordinate_hits","cold_MORB_coordinate_hits","integrated_coordinate_hits","unsampled_coordinates")


def replay_c04():
    parent=c.parent()
    plans,records,limits=q.replay_closure(parent)
    legacy,old=q.cold.load_consolidated()
    lib=q.integrate(legacy,plans,records,limits,SOURCE)
    report=q.coverage(lib,old)
    archive=q.OUT
    rec=c.read(q.z.d.m.HERE/"c04_fair_receipt_v1.json")
    need(archive.is_dir() and not archive.is_symlink()
         and not (archive/"MANIFEST.json").is_symlink()
         and hgp.file_sha(archive/"MANIFEST.json")==PIN==rec["manifest_sha256"],
         "C05_C04_PIN")
    man=c.read(archive/"MANIFEST.json")
    inv=q.z.d.launcher.inventory(archive)
    inv.pop("MANIFEST.json")
    need(inv==man["files"] and set(inv)=={"LIBRARY.json","REGIONAL_COVERAGE.json","PHYSICAL_CLOSURE_REQUIREMENTS.json"}
         and man["source_sha"]==SOURCE==rec["source_sha"] and rec["exit"]==0
         and rec["regression_passed"]==214
         and man["schema"]=="R6_C04_INTEGRATED_RESEARCH_LIBRARY_MANIFEST_V1"
         and man["status"]==q.STATUS and man["C03FA_manifest_sha256"]==q.PIN
         and man["C02_manifest_sha256"]==q.cold.PIN and man["states"]==35
         and man["source_chemistries"]==14 and man["cold_MORB_native_chemistries"]==2
         and man["regional_samples"]==3700 and man["physical_material_coverage_count"]==0
         and man["additional_engine_runs"]==0 and man["scientific_promotion"] is False
         and all(man[k]==v for k,v in c.SCOPE.items()),"C05_C04_MANIFEST")
    need(c.read(archive/"LIBRARY.json")==lib and c.read(archive/"REGIONAL_COVERAGE.json")==report
         and report["regions"]==rec["regions"],"C05_C04_CONTENT_REPLAY")
    need(all(tuple(report["regions"][e][l][k] for k in METRICS)==expected
             for e,region in EXPECTED.items() for l,expected in region.items()),"C05_C04_RECEIPT")
    return lib,report


def replay_source(root):
    base=s2.BASE
    folder=base/"R6_G2_T0_MATERIAL_FLUID_TRIAL_NEW01"
    manifest=trial.manifest(folder,"ARCANA_R6_G2_T0_MATERIAL_TRIAL_SOURCE_MANIFEST_V1",trial.FILES)
    need(manifest["no_solver_run"] is True and manifest["physical_T1"] is None
         and manifest["HistoryStore_modified"] is False,"C05_SOURCE_MANIFEST_SCOPE")
    paths={"packet8":base/"R6_G2G3_PHYSICAL_SOURCE_PACKET_8X8_NEW02",
           "packet16":base/"R6_G2G3_PHYSICAL_SOURCE_PACKET_16X16_NEW02",
           "handoff":base/"R6_G2G3_SOURCE_TO_COUPLED_AUTHORING_NEW01",
           "pt_folder":base/"R6_G2G3_T0_LITHOSTATIC_PT_REFERENCE_NEW01",
           "cold_folder":base/"R6_G2G3_T0_COLD_CRUST_REGIME_NEW01"}
    templates=trial.build(repo_root=root,**paths)
    need(tuple(c.read(folder/name) for name in trial.FILES)==templates,"C05_SOURCE_TEMPLATE_REPLAY")
    pt=q.cold.a.original_pt(root)
    for extent,template,original in zip((8,16),templates[:2],pt,strict=True):
        trial.validate_unselected_report(template,extent)
        need(template["source_parent_ids"]==original["original_parent_node_order"],
             "C05_PARENT_ID_REPLAY")
    # Read only the already verified authoring handoff, never modify or execute it.
    handoff={str(e):c.read(paths["handoff"]/f"SCENARIO_{e}X{e}_UNSELECTED.json") for e in (8,16)}
    for e,sc in handoff.items():
        need(sc["authoring_template_unselected"] is True
             and sc["mechanical_solve_authorized"] is False and sc["physical_T1"] is None,
             "C05_HANDOFF_SCOPE")
        need(all(v is None for v in sc["candidate_material_by_parent_node"].values())
             and all(v is None for v in sc["velocity_en_by_parent_node"].values())
             and all(v is None for v in sc["line_tractions_by_edge"].values())
             and all(v is None for v in sc["basal_tractions_by_triangle"].values()),
             "C05_HANDOFF_UNSELECTED")
    return templates[:2],pt,handoff,{"material_trial_manifest_sha256":s2.sha(folder/"MANIFEST.json"),
          **{k+"_manifest_sha256":s2.sha(v/"MANIFEST.json") for k,v in paths.items()}}


def signature(row):
    return (row["model_identity"],row["native_chemistry_sha256"])


def sample_keys(row):
    return sorted(set(row["cold_MORB_conditional_candidate_keys"]) |
                  {k for keys in row["comparative_coordinate_matches"].values() for k in keys})


def column_profile(rows,states):
    need(len(rows)==5 and len({r["fraction_of_layer"] for r in rows})==5,"C05_FIVE_DEPTHS")
    ordered=sorted(rows,key=lambda r:r["fraction_of_layer"])
    support=defaultdict(list)
    for i,row in enumerate(ordered):
        keys=sample_keys(row)
        for key in keys:
            need(key in states,"C05_UNKNOWN_STATE_KEY")
            state=states[key]
            need(q.cold.a.coordinate(state["P_kbar"],state["T_C"])==
                 q.cold.a.coordinate(row["conditional_delta_P_kbar"],row["source_temperature_K"]-273.15),
                 "C05_STATE_COORDINATE")
            support[signature(state)].append((i,key))
    candidates=[]
    for (model,chem),hits in sorted(support.items()):
        indices=sorted({i for i,k in hits})
        candidates.append({"model_identity":model,"native_chemistry_sha256":chem,
            "family":states[hits[0][1]]["family"],
            "source_chemistry_sha256":states[hits[0][1]]["source_chemistry_sha256"],
            "matched_depth_indices":indices,
            "missing_depth_indices":[i for i in range(5) if i not in indices],
            "exact_state_keys":sorted({k for i,k in hits}),
            "all_five_depths_exact":len(indices)==5,
            "physical_assignment_authorized":False})
    return {"samples":ordered,"candidate_profiles":candidates,
        "any_coordinate_hits":sum(bool(sample_keys(row)) for row in ordered),
        "same_model_native_chemistry_full_profiles":sum(x["all_five_depths_exact"] for x in candidates),
        "max_same_model_native_chemistry_depth_hits":max((len(x["matched_depth_indices"]) for x in candidates),default=0),
        "actual_material":None,"continuous_EOS_qualified":False,"rheology_binding":None}


def compile_region(extent,template,pt,report,states):
    ids=template["source_parent_ids"]
    groups=defaultdict(list)
    for row in report["samples"]:
        if row["extent"]==extent:
            groups[row["parent_node_id"],row["layer"]].append(row)
    need(set(groups)=={(node,l) for node in ids for l in LAYERS},"C05_REGION_GROUPS")
    columns={}
    summary={l:Counter() for l in LAYERS}
    gaps=defaultdict(list)
    for node in ids:
        node_source=pt["original_T0_source_nodes"][str(node)]
        original=node_source["source_depth_pt_samples"]
        layers={}
        for layer in LAYERS:
            rows=groups[node,layer]
            originals=[x for x in original if x["layer"]==layer]
            def source_tuple(x):
                return (x["fraction_of_layer"],x["source_depth_m"],x["source_PRE_temperature_k"],
                        x["conditional_delta_vertical_overburden_pa"]/1e8)
            need(sorted(source_tuple(x) for x in originals)==sorted(
                (x["fraction_of_layer"],x["source_depth_m"],x["source_temperature_K"],x["conditional_delta_P_kbar"])
                for x in rows),"C05_ORIGINAL_DEPTH_PT")
            profile=column_profile(rows,states)
            layers[layer]=profile
            a=summary[layer]
            a["columns"]+=1
            a["any_exact_comparative_depth"]+=int(profile["any_coordinate_hits"]>0)
            a["all_five_any_candidate"]+=int(profile["any_coordinate_hits"]==5)
            a["all_five_same_model_native_chemistry"]+=int(profile["same_model_native_chemistry_full_profiles"]>0)
            a["no_exact_comparative_depth"]+=int(profile["any_coordinate_hits"]==0)
            a["comparative_depth_hits"]+=profile["any_coordinate_hits"]
            for row in profile["samples"]:
                if not sample_keys(row):
                    p=row["conditional_delta_P_kbar"]
                    t=row["source_temperature_K"]
                    gaps[layer,p,t].append({"parent_node_id":node,"depth_m":row["source_depth_m"]})
        columns[str(node)]={"parent_node_id":node,"source_crust_temperature_k":
            template["nodewise_conditional_PT_reference"][str(node)]["source_crust_temperature_k"],
            "layers":layers,"selected_material":None,"pore_pressure_pa":None,"constitutive_law":None}
    for layer,a in summary.items():
        need(a["comparative_depth_hits"]==report["regions"][str(extent)][layer]["integrated_coordinate_hits"],
             "C05_COLUMN_COVERAGE_DRIFT")
    ranked=[{"layer":l,"conditional_delta_P_kbar":p,"source_T_K":t,"occurrences":len(v),
             "parent_depth_support":v,"absolute_pressure_pa":None,
             "new_solver_authorized":False}
             for (l,p,t),v in sorted(gaps.items(),key=lambda x:(-len(x[1]),x[0]))]
    return {"schema":"R6_C05_SOURCE_COLUMN_FEASIBILITY_V1","extent":extent,
        "source_parent_ids":ids,"source_original_FEG_sha256":template["source_original_FEG_sha256"],
        "source_original_PRE_sha256":template["source_original_PRE_sha256"],
        "local_triple_junctions":template["source_actual_local_triple_plate_junctions"],
        "columns":columns,"summary":{l:dict(v) for l,v in summary.items()},
        "ranked_unsampled_comparative_coordinates":ranked,"physical_material_assignments":0,
        "full_profile_is_not_continuous_EOS_or_placement":True,**c.SCOPE}


def physical_handoff(root,regions,handoff,source):
    path=root/"experiments/plate58_deforming_explore_v1/R6_G2_G3_INTEGRATED_PHYSICAL_PROVIDER_MATRIX_20261121.json"
    matrix=c.read(path)
    groups=matrix["groups"]
    need(len(groups)==8 and len({x["id"] for x in groups})==8,"C05_PHYSICAL_GROUPS")
    counts={}
    for e,sc in handoff.items():
        counts[e]={"parent_nodes":len(sc["candidate_material_by_parent_node"]),
                   "outer_cut_edges":len(sc["line_tractions_by_edge"]),
                   "exterior_basal_facets":len(sc["basal_tractions_by_triangle"])}
    need(counts=={"8":{"parent_nodes":81,"outer_cut_edges":32,"exterior_basal_facets":120},
                  "16":{"parent_nodes":289,"outer_cut_edges":64,"exterior_basal_facets":504}},
         "C05_FORCE_SUPPORT_COUNTS")
    return {"schema":"R6_C05_PHYSICAL_CLOSURE_HANDOFF_V1","source":source,
        "C04_manifest_sha256":PIN,"provider_matrix_sha256":s2.sha(path),
        "prior_G2G3_required_groups":groups,"regional_support_counts":counts,
        "preferred_first_domain":"8x8; 16x16 domain sensitivity, not mesh convergence",
        "material_selection":"UNSELECTED_EXPLICIT_SOURCE_KEYED_HYPOTHESIS_REQUIRED",
        "thermodynamic_scope":"exact comparison candidates, not continuous column properties",
        "pressure_policy":"conditional overburden only; no pore pressure or fault effective stress inferred",
        "mechanical_routes":[{"route":"G2_G3_FULL_COUPLED","status":"PHYSICAL_INPUTS_UNSELECTED",
             "minimum_next":"source-qualified material scenario and mechanism validity; independent cut/basal/GPE/fault closure"},
            {"route":"SHELLSET_MINIMUM","status":"REFERENCE_PARAMETERS_AND_NATIVE_INPUT_AUTHORITY_UNQUALIFIED",
             "contract":"R6_SHELLSET_MINIMUM_THERMOMECHANICAL_STATE_CONTRACT.md",
             "external_absolute_pressure_required":False}],
        "next_decision":"AUTHORIAL_REGIONAL_BULK_HYPOTHESIS_WITH_SPATIAL_SUPPORT_AND_FLUID_ASSUMPTIONS; THEN_CONSTITUTIVE_PROVIDER_DOMAIN",
        "automatic_new_equilibrium_campaign_authorized":False,"additional_engine_runs":0,**c.SCOPE}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    ap.add_argument("--offline-regional-feasibility-only",required=True,action="store_true")
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C05_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C05_OUTPUT_EXISTS")
    lib,report=replay_c04()
    print("C05_C04_REPLAY_PASS",PIN,flush=True)
    templates,pt,handoff,source=replay_source(root)
    print("C05_G2_G3_SOURCE_REPLAY_PASS",json.dumps(source,sort_keys=True),flush=True)
    regions={str(e):compile_region(e,t,p,report,lib["states"])
             for e,t,p in zip((8,16),templates,pt,strict=True)}
    decision=physical_handoff(root,regions,handoff,source)
    OUT.mkdir(parents=False,exist_ok=False)
    for e,record in regions.items():
        s2.write_json(OUT/f"REGION_{e}X{e}_COLUMN_FEASIBILITY.json",record)
        print("C05_COLUMN_SUMMARY",e,json.dumps(record["summary"],sort_keys=True),flush=True)
        for layer in LAYERS:
            ranked=[{k:v for k,v in row.items() if k!="parent_depth_support"}
                    for row in record["ranked_unsampled_comparative_coordinates"] if row["layer"]==layer][:5]
            print("C05_TOP_UNSAMPLED",e,layer,json.dumps(ranked,sort_keys=True),flush=True)
    s2.write_json(OUT/"PHYSICAL_CLOSURE_HANDOFF.json",decision)
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C05_COLUMN_FEASIBILITY_MANIFEST_V1",
        "source_sha":head,"status":STATUS,"C04_manifest_sha256":PIN,"source":source,
        "files":q.z.d.launcher.inventory(OUT),"regional_column_records":370,"regional_samples":3700,
        "physical_material_assignments":0,"additional_engine_runs":0,
        "scientific_promotion":False,**c.SCOPE})
    print("C05_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"),flush=True)
    print(STATUS)
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()
