"""Source-identity reconciliation of C05, and bounded regional hypothesis design input.

Retain every native float64 key. No tolerant nearest-neighbour lookup, no solver,
no automatic lithology/pressure/fluid assignment, no modification of C04/C05.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
import math
from experiments.r6_thermo_provider_pilot_v1 import run_c05_regional_column_feasibility as v
from experiments.plate58_deforming_explore_v1.g2_g3_source_to_coupled_handoff import load_packet

q=v.q
c=v.c
s2=v.s2
need=v.need
hgp=v.hgp
PIN="7224fb290672ba483f7dee69e34129e9e48029f4acf43a20de910be83d1d41a2"
SOURCE="0b1f96c6b8de1d44c621433291eafd6e66915509"
OUT=s2.BASE/"R6_THERMO_C05_SOURCE_IDENTITY_AND_HYPOTHESIS_DESIGN_NEW01"
STATUS="C05_SOURCE_IDENTITY_RECONCILED__REGIONAL_HYPOTHESIS_REVIEW_REQUIRED"
DESIGNS=(
    ("M01","m01_mantle_experimental_design_candidate_v1.json",
     "63dba6466b22bfa79bb3d69f002b20ed72959d71","mantle_lithosphere",
     "experimental_PT_choice",("M01_BASE","M01_LOW_H2O","M01_HIGH_H2O","M01_HIGH_FERRIC")),
    ("C01","c01_crust_experimental_design_candidate_v1.json",
     "fc1540d34414776c849263e6b7023f612b63a30a","crust",
     "experimental_PT",tuple("C01_"+f+"_"+s for f in ("LCC","MORB") for s in ("BASE","WET","OXIDIZED"))),
)


def pinned_archive(folder,pin,files,source,schema):
    need(folder.is_dir() and not folder.is_symlink() and not (folder/"MANIFEST.json").is_symlink()
         and hgp.file_sha(folder/"MANIFEST.json")==pin,"C05R_MANIFEST_PIN")
    man=c.read(folder/"MANIFEST.json")
    inventory=q.z.d.launcher.inventory(folder)
    inventory.pop("MANIFEST.json")
    need(inventory==man["files"] and set(inventory)==set(files) and man["source_sha"]==source
         and man["schema"]==schema and man["additional_engine_runs"]==0
         and man["scientific_promotion"] is False and all(man[k]==x for k,x in c.SCOPE.items()),
         "C05R_ARCHIVE_SCOPE")
    return man


def load_inputs():
    rec=c.read(q.z.d.m.HERE/"c05_fair_receipt_v1.json")
    need(rec["source_sha"]==SOURCE and rec["manifest_sha256"]==PIN
         and rec["exit"]==0 and rec["regression_passed"]==220,"C05R_RECEIPT")
    names=[f"REGION_{e}X{e}_COLUMN_FEASIBILITY.json" for e in (8,16)]
    man=pinned_archive(v.OUT,PIN,names+["PHYSICAL_CLOSURE_HANDOFF.json"],SOURCE,
                      "R6_C05_COLUMN_FEASIBILITY_MANIFEST_V1")
    need(man["status"]==v.STATUS and man["C04_manifest_sha256"]==v.PIN
         and man["source"]==rec["source"] and man["regional_column_records"]==370
         and man["regional_samples"]==3700 and man["physical_material_assignments"]==0,
         "C05R_C05_SCOPE")
    regions={e:c.read(v.OUT/name) for e,name in zip((8,16),names,strict=True)}
    for e,record in regions.items():
        need(record["extent"]==e and record["summary"]==rec["column_summary"][str(e)]
             and len(record["columns"])==(e+1)**2 and record["physical_material_assignments"]==0,
             "C05R_COLUMN_RECEIPT")
    prev=pinned_archive(q.OUT,v.PIN,["LIBRARY.json","REGIONAL_COVERAGE.json","PHYSICAL_CLOSURE_REQUIREMENTS.json"],
                        v.SOURCE,"R6_C04_INTEGRATED_RESEARCH_LIBRARY_MANIFEST_V1")
    need(prev["status"]==q.STATUS and prev["states"]==35 and prev["physical_material_coverage_count"]==0,
         "C05R_C04_SCOPE")
    lib=c.read(q.OUT/"LIBRARY.json")
    need(len(lib["states"])==35 and lib["assignment_authorized"] is False
         and lib["interpolation_authorized"] is False,"C05R_LIBRARY_SCOPE")
    packets={}
    for e in (8,16):
        folder=s2.BASE/f"R6_G2G3_PHYSICAL_SOURCE_PACKET_{e}X{e}_NEW02"
        ix,_,receipt=load_packet(folder,e)
        region=regions[e]
        need(receipt["evidence_manifest_sha256"]==rec["source"][f"packet{e}_manifest_sha256"]
             and region["source_parent_ids"]==ix["original_parent_node_order"]
             and region["source_original_FEG_sha256"]==ix["source_hashes"]["original_FEG_sha256"]
             and region["source_original_PRE_sha256"]==ix["source_hashes"]["original_PRE_sha256"],
             "C05R_PACKET_SOURCE")
        packets[e]=ix
    return lib,regions,packets


def coord(row):
    # Original regional T in kelvin, not solver T converted back to kelvin.
    return (row["layer"],row["conditional_delta_P_kbar"],row["source_temperature_K"])


def design_links(lib,regions):
    links={}
    for name,filename,blob,layer,pt_key,cases in DESIGNS:
        raw=(q.z.d.m.HERE/filename).read_bytes()
        need(q.cold.a.m.git_blob_sha(raw)==blob,"C05R_DESIGN_PIN:"+name)
        design=json.loads(raw)
        src=design["source_state"]
        ex=design[pt_key]
        col=regions[src["extent"]]["columns"][str(src["parent_node_id"])]
        rows=col["layers"][layer]["samples"]
        hits=[r for r in rows if r["source_depth_m"]==src["depth_m"]]
        need(len(hits)==1 and src["absolute_pressure_pa"] is None,"C05R_ANCHOR")
        anchor=hits[0]
        need(anchor["source_temperature_K"]==src["T_K"]
             and anchor["conditional_delta_P_kbar"]==src["conditional_delta_P_bar"]/1000==ex["P_kbar"]
             and anchor["absolute_pressure_pa"] is None,"C05R_ANCHOR_PT")
        recomputed=src["T_K"]-273.15
        native=ex["T_C"]
        # Strict reproduction of this documented one-ULP discrepancy, NOT a general tolerance.
        need(math.nextafter(native,math.inf)==recomputed,"C05R_DOCUMENTED_ROUNDOFF")
        keys={}
        for k,state in lib["states"].items():
            case=state["provider_record"].get("case")
            if case not in cases:
                continue
            need(case not in keys and state["P_kbar"]==ex["P_kbar"] and state["T_C"]==native
                 and state["spatial_assignment"] is None,"C05R_NATIVE_DESIGN_BINDING")
            keys[case]=k
        need(set(keys)==set(cases),"C05R_DESIGN_CASES")
        identity=coord(anchor)
        need(identity not in links,"C05R_DUPLICATE_DESIGN_COORDINATE")
        links[identity]={"design":name,"design_git_blob":blob,
            "source_anchor":src,"native_T_C":native,"converted_source_T_C":recomputed,
            "temperature_delta_C":recomputed-native,"delta_ULP":1,
            "state_keys_by_case":keys,
            "classification":"SOURCE_ANCHORED_DESIGN_COORDINATE_LINK_NOT_NATIVE_EXACT_LOOKUP"}
    return links


def linked_keys(row,links):
    link=links.get(coord(row))
    return sorted(link["state_keys_by_case"].values()) if link else []


def classify_profile(rows,states,links):
    support=defaultdict(set)
    depth_rows=[]
    for i,row in enumerate(sorted(rows,key=lambda x:x["fraction_of_layer"])):
        exact=v.sample_keys(row)
        bound=linked_keys(row,links)
        all_keys=set(exact)|set(bound)
        need(all(k in states for k in all_keys),"C05R_STATE_KEY")
        for k in all_keys:
            support[v.signature(states[k])].add(i)
        depth_rows.append({"fraction_of_layer":row["fraction_of_layer"],
           "depth_m":row["source_depth_m"],"source_T_K":row["source_temperature_K"],
           "conditional_delta_P_kbar":row["conditional_delta_P_kbar"],
           "native_exact_keys":exact,"source_design_link_keys":bound,
           "physical_assignment":None,"absolute_pressure_pa":None})
    need(len(depth_rows)==5,"C05R_DEPTH_COUNT")
    return {"depths":depth_rows,"any_linked_depths":sum(bool(x["native_exact_keys"] or x["source_design_link_keys"]) for x in depth_rows),
       "additional_source_link_depths":sum(bool(x["source_design_link_keys"]) and not x["native_exact_keys"] for x in depth_rows),
       "candidate_profiles":[{"model_identity":m,"native_chemistry_sha256":x,
          "matched_depths":sorted(ds),"missing_depths":[i for i in range(5) if i not in ds]}
          for (m,x),ds in sorted(support.items())],
       "same_recipe_full_profile_count":sum(len(ds)==5 for ds in support.values()),
       "actual_material":None}


def group_region(region,packet,states,links):
    groups={}
    totals={l:Counter() for l in v.LAYERS}
    for node in region["source_parent_ids"]:
        k=str(node)
        column=region["columns"][k]
        pre=packet["source_original_PRE_model_T0_thermal_profiles_by_parent_node"][k]
        config=packet["source_material_configuration_code_by_parent_node"][k]
        layers={l:classify_profile(column["layers"][l]["samples"],states,links) for l in v.LAYERS}
        # Group only by exact original thermal state/configuration and geometry.
        # Do not assign a geological meaning to numerical configuration codes.
        identity={"configuration_code":config,
            "source_crust_density_kg_m3":pre["crust_density_kg_m3"],
            "source_mantle_density_kg_m3":pre["mantle_density_kg_m3"],
            "crust_thickness_m":pre["crust_thickness_m"],
            "mantle_thickness_m":pre["mantle_lithosphere_thickness_m"],
            "profile_coordinates":{l:[(x["fraction_of_layer"],x["depth_m"],x["source_T_K"],x["conditional_delta_P_kbar"])
                                       for x in layers[l]["depths"]] for l in v.LAYERS}}
        key=q.digest(identity)
        if key not in groups:
            groups[key]={"source_thermal_group":identity,"source_parent_ids":[],"layers":layers,
                         "selected_bulk_recipe":None,"selected_hydration":None,"selected_redox":None}
        else:
            need(groups[key]["layers"]==layers,"C05R_GROUP_PROFILE_DRIFT")
        groups[key]["source_parent_ids"].append(node)
        for l,p in layers.items():
            a=totals[l]
            a["columns"]+=1
            a["native_exact_depth_hits"]+=sum(bool(x["native_exact_keys"]) for x in p["depths"])
            a["additional_source_link_depth_hits"]+=p["additional_source_link_depths"]
            a["combined_depth_hits"]+=p["any_linked_depths"]
            a["same_recipe_complete_columns"]+=int(p["same_recipe_full_profile_count"]>0)
            a["all_five_any_candidate_columns"]+=int(p["any_linked_depths"]==5)
    for l,a in totals.items():
        need(a["native_exact_depth_hits"]==region["summary"][l]["comparative_depth_hits"]
             and a["combined_depth_hits"]==a["native_exact_depth_hits"]+a["additional_source_link_depth_hits"],
             "C05R_COVERAGE_ACCOUNTING")
    return {"extent":region["extent"],"groups":groups,"summary":{l:dict(x) for l,x in totals.items()},
            "grouping_semantics":"EXACT_SOURCE_THERMAL_CONFIG_AND_PT_NOT_NATURAL_LITHOLOGY",
            "physical_material_assignments":0,**c.SCOPE}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    ap.add_argument("--offline-design-only",action="store_true",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C05R_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C05R_OUTPUT_EXISTS")
    lib,regions,packets=load_inputs()
    links=design_links(lib,regions)
    results={e:group_region(r,packets[e],lib["states"],links) for e,r in regions.items()}
    # Preserve prior coverage as-is; the new category is source identity, not a rewritten exact key.
    for link in links.values():
        print("C05R_DESIGN_LINK",json.dumps(link,sort_keys=True),flush=True)
    OUT.mkdir(parents=False,exist_ok=False)
    for e,r in results.items():
        s2.write_json(OUT/f"REGION_{e}X{e}_HYPOTHESIS_DESIGN.json",r)
        print("C05R_SUMMARY",e,json.dumps(r["summary"],sort_keys=True),flush=True)
        for key,g in sorted(r["groups"].items(),key=lambda kv:(-len(kv[1]["source_parent_ids"]),kv[0])):
            compact={"group_id":key,"nodes":len(g["source_parent_ids"]),
                "first_parent_ids":g["source_parent_ids"][:5],
                "configuration_code":g["source_thermal_group"]["configuration_code"],
                "crust_thickness_m":g["source_thermal_group"]["crust_thickness_m"],
                "crust_density_reference":g["source_thermal_group"]["source_crust_density_kg_m3"],
                "mantle_thickness_m":g["source_thermal_group"]["mantle_thickness_m"],
                "depth_hits":{l:g["layers"][l]["any_linked_depths"] for l in v.LAYERS}}
            print("C05R_SOURCE_GROUP",e,json.dumps(compact,sort_keys=True),flush=True)
    s2.write_json(OUT/"SOURCE_DESIGN_LINKS.json",list(links.values()))
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C05_SOURCE_IDENTITY_AND_HYPOTHESIS_DESIGN_MANIFEST_V1",
        "source_sha":head,"status":STATUS,"C05_manifest_sha256":PIN,"C04_manifest_sha256":v.PIN,
        "files":q.z.d.launcher.inventory(OUT),"source_design_links":2,"additional_engine_runs":0,
        "scientific_promotion":False,**c.SCOPE})
    print("C05R_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"),flush=True)
    print(STATUS)
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()
