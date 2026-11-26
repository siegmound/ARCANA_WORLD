"""C04: exact provider-aware candidate library and original regional coverage, offline."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import json
from experiments.r6_thermo_provider_pilot_v1 import run_c03f_restricted_research_closure as z
from experiments.r6_thermo_provider_pilot_v1 import run_c03_cold_crust_design as cold

c=z.c
s2=z.s2
need=z.need
hgp=z.hgp
PIN="acd0ec42b69411c3fe709076a2a88054eda7691a31084cced1ef1f802cf650fb"
SOURCE="9a02b5574ad738bd9d9eb9544077f94b9620f77c"
OUT=s2.BASE/"R6_THERMO_C04_INTEGRATED_RESEARCH_LIBRARY_NEW01"
STATUS="C04_EXACT_MULTIPROVIDER_RESEARCH_LIBRARY_AND_COVERAGE_COMPLETE__REGIONAL_PHYSICAL_CLOSURE_PENDING"


def digest(value):
    return hgp.sha(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode())


def replay_closure(parent):
    replay=z.replay_review(parent)
    decisions,records=z.close(*replay)
    archive=z.OUT
    rec=c.read(z.d.m.HERE/"c03fa_fair_receipt_v1.json")
    need(archive.is_dir() and not archive.is_symlink()
         and not (archive/"MANIFEST.json").is_symlink()
         and hgp.file_sha(archive/"MANIFEST.json")==PIN==rec["manifest_sha256"],
         "C04_CLOSURE_PIN")
    man=c.read(archive/"MANIFEST.json")
    inv=z.d.launcher.inventory(archive)
    inv.pop("MANIFEST.json")
    need(inv==man["files"] and set(inv)=={"SIGNED_COORDINATE_ADJUDICATION.json","C04_RESEARCH_CANDIDATES.json"}
         and man["source_sha"]==SOURCE==rec["source_sha"]
         and rec["exit"]==0 and rec["regression_passed"]==209
         and man["schema"]=="R6_C03F_RESTRICTED_RESEARCH_CLOSURE_MANIFEST_V1"
         and man["status"]==z.STATUS and man["review_manifest_sha256"]==z.PIN
         and man["campaign_manifest_sha256"]==z.r.PIN
         and man["reviewed_points"]==man["conditional_research_candidates"]==4
         and man["signed_coordinates_adjudicated"]==2
         and man["additional_engine_runs"]==man["authorized_equilibrium_solver_calls"]==0
         and man["scientific_promotion"] is False and all(man[k]==v for k,v in c.SCOPE.items()),
         "C04_CLOSURE_MANIFEST")
    need(c.read(archive/"SIGNED_COORDINATE_ADJUDICATION.json")=={"observations":decisions,
         "scope":"PRINTED_SITE_AND_CHEMICAL_DOMAIN_COMPATIBILITY_NOT_FULL_MODEL_CALIBRATION",
         "scientific_promotion":False},"C04_ADJUDICATION_REPLAY")
    handoff=c.read(archive/"C04_RESEARCH_CANDIDATES.json")
    need(handoff["records"]==records and handoff["assignment_authorized"] is False
         and handoff["cold_felsic"]=="DEFERRED" and all(handoff[k]==v for k,v in c.SCOPE.items()),
         "C04_HANDOFF_REPLAY")
    return replay[0],records,handoff["limitations"]


def identity(model,chem,pk,tc):
    need(isinstance(model,str) and bool(model) and isinstance(chem,str) and bool(chem),"C04_IDENTITY")
    p,t=cold.a.coordinate(pk,tc)
    return model+":"+chem+":"+p+":"+t


def lookup(lib,model,chem,pk,tc):
    row=lib["states"].get(identity(model,chem,pk,tc))
    return {"status":"EXACT_RESEARCH_SAMPLE" if row is not None else "UNKNOWN_UNSAMPLED_MODEL_PT_X",
            "state":deepcopy(row),"interpolated":False,"assignment_authorized":False}


def native_configuration(plan):
    return {"provider":"MEEMUM","dataset":"hp02ver.dat","phase_policy":"ACT_RESTRICTED_SUBSOLIDUS",
        "solution_models":plan["solution_models"],"excluded_phases":plan["excluded_phases"],
        "data_files_sha256":{k:v for k,v in plan["files_sha256"].items() if k!="c03d.dat"},
        "boundary":"CLOSED_BULK_NO_BUFFER_NO_SATURATION","solver":"PINNED_NATIVE_DEFAULTS",
        "campaign_manifest_sha256":z.r.PIN}


def integrate(legacy,plans,records,limitations,head):
    need(len(legacy["states"])==31,"C04_LEGACY_STATE_COUNT")
    states={}
    for oldkey,row in legacy["states"].items():
        k=identity(row["model_identity"],row["chemistry_sha256"],row["P_kbar"],row["T_C"])
        need(k==oldkey and k not in states and row["spatial_assignment"] is None,"C04_LEGACY_KEY")
        states[k]={"provider_record":deepcopy(row),"model_identity":row["model_identity"],
            "native_chemistry_sha256":row["chemistry_sha256"],"source_chemistry_sha256":row["chemistry_sha256"],
            "P_kbar":row["P_kbar"],"T_C":row["T_C"],"family":cold.a.family(row["case"]),
            "authority":"LEGACY_EXACT_RESEARCH_SAMPLE","spatial_assignment":None,
            "absolute_pressure_pa":None,"property_semantics":"PRESERVED_NATIVE_MAGEMIN_RECORD_NO_CROSS_PROVIDER_EQUIVALENCE"}
    legacy_count=len(states)
    configs=[native_configuration(plans[n]) for n in z.f.NAMES]
    need(configs[0]==configs[1],"C04_CONFIGURATION_DRIFT")
    config=configs[0]
    model="MEEMUM_HP02_ACT_RESTRICTED:"+digest(config)
    native_chemistries={}
    for row in records:
        name=row["recipe"]
        plan=plans[name]
        source=row["source_point"]
        need(row["authority"]=="CONDITIONAL_RESEARCH_CANDIDATE_ONLY"
             and row["absolute_pressure_pa"] is None and row["world_material_assignment"] is False
             and row["interpolation_authorized"] is False and row["scientific_promotion"] is False
             and row["source_chemistry_sha256"]==plan["source_chemistry_sha256"]
             and row["normalized_moles"]==plan["normalized_moles"]
             and source["pressure_semantics"]=="HYPOTHETICAL_COMPARATIVE_ONLY","C04_CANDIDATE_SCOPE")
        original=[v for v in legacy["states"].values() if v["case"]==name]
        need(len(original)==1 and original[0]["chemistry_sha256"]==row["source_chemistry_sha256"],
             "C04_SOURCE_RECIPE_BINDING")
        native={"source_chemistry_sha256":row["source_chemistry_sha256"],
            "native_moles":row["normalized_moles"],"basis":plan["basis"],
            "configuration_sha256":digest(config)}
        chem=digest(native)
        native_chemistries[chem]=native
        pk=source["conditional_delta_P_kbar"]
        tc=source["T_C"]
        k=identity(model,chem,pk,tc)
        need(k not in states,"C04_DUPLICATE_NATIVE_STATE")
        states[k]={"provider_record":deepcopy(row),"model_identity":model,"native_chemistry_sha256":chem,
            "source_chemistry_sha256":row["source_chemistry_sha256"],"P_kbar":pk,"T_C":tc,"family":"MORB",
            "authority":"CONDITIONAL_RESEARCH_CANDIDATE_ONLY","spatial_assignment":None,
            "absolute_pressure_pa":None,"property_semantics":"NATIVE_MEEMUM_AGGREGATE_NOT_HARMONIZED_WITH_MAGEMIN",
            "source_coordinate_semantics":"EXACT_DESIGN_PT_NATIVE_READBACK_ROUNDED",
            "closure_manifest_sha256":PIN}
    need(legacy_count==31 and len(states)==35 and len(native_chemistries)==2
         and len({v["source_chemistry_sha256"] for v in states.values()})==14,
         "C04_LIBRARY_COUNTS")
    result={"schema":"R6_C04_INTEGRATED_EXACT_RESEARCH_LIBRARY_V1","source_sha":head,
        "legacy_library":deepcopy(legacy),"native_configuration":config,"native_model_identity":model,
        "native_chemistries":native_chemistries,"states":states,
        "key_semantics":"model_identity:native_chemistry_sha256:float64_hex_design_P_kbar:float64_hex_design_T_C",
        "legacy_state_count":31,"conditional_cold_MORB_state_count":4,"source_chemistry_count":14,
        "interpolation_authorized":False,"assignment_authorized":False,
        "source_solver_processes_legacy":62,"reference_diagnostic_equilibria_excluded":6,
        "cold_MORB_equilibria":4,"cold_MORB_processes":2,"additional_engine_runs":0,
        "limitations":limitations,**c.SCOPE}
    for k,row in states.items():
        args=(row["model_identity"],row["native_chemistry_sha256"],row["P_kbar"],row["T_C"])
        need(k==identity(*args) and lookup(result,*args)["state"]==row
             and lookup(result,*args[:3],args[3]+.123456789)["state"] is None,"C04_EXACT_LOOKUP")
    return result


def coverage(lib,old):
    index=defaultdict(list)
    for key,row in sorted(lib["states"].items()):
        if row["authority"]=="CONDITIONAL_RESEARCH_CANDIDATE_ONLY":
            index[cold.a.coordinate(row["P_kbar"],row["T_C"])].append(key)
    samples=[]
    counts=Counter()
    for original in old["samples"]:
        row=deepcopy(original)
        need(row["absolute_pressure_pa"] is None and row["spatial_assignment"] is None
             and row["material_recipe"] is None and row["physical_coverage_status"]=="UNKNOWN",
             "C04_REGIONAL_AUTHORITY")
        key=cold.a.coordinate(row["conditional_delta_P_kbar"],row["source_temperature_K"]-273.15)
        new=index.get(key,[]) if row["layer"]=="crust" else []
        before=any(row["comparative_coordinate_matches"].values())
        after=before or bool(new)
        region=(str(row["extent"]),row["layer"])
        for field,delta in (("samples",1),("prior_coordinate_hits",int(before)),
             ("cold_MORB_coordinate_hits",int(bool(new))),("new_coordinate_hits",int(after and not before)),
             ("integrated_coordinate_hits",int(after)),("unsampled_coordinates",int(not after))):
            counts[region+(field,)]+=delta
        row["cold_MORB_conditional_candidate_keys"]=new
        row["integrated_coordinate_status"]="EXACT_COMPARATIVE_PT_COORDINATE" if after else "UNSAMPLED_COMPARATIVE_PT"
        samples.append(row)
    need(len(samples)==3700,"C04_COVERAGE_COUNT")
    summary={extent:{layer:{k:v for (e,l,k),v in sorted(counts.items()) if (e,l)==(extent,layer)}
              for layer in cold.a.FAMILIES} for extent in ("8","16")}
    return {"schema":"R6_C04_REGIONAL_EXACT_COMPARATIVE_COVERAGE_V1","regions":summary,
        "samples":samples,"physical_material_coverage_count":0,"material_assignment_authorized":False,
        "limitations":old["unresolved_requirements"],"additional_engine_runs":0,**c.SCOPE}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    ap.add_argument("--offline-integration-only",action="store_true",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C04_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C04_OUTPUT_EXISTS")
    parent=c.parent()
    plans,records,limits=replay_closure(parent)
    print("C04_C03FA_REPLAY_PASS",PIN,flush=True)
    legacy,old=cold.load_consolidated()
    lib=integrate(legacy,plans,records,limits,head)
    report=coverage(lib,old)
    OUT.mkdir(parents=False,exist_ok=False)
    s2.write_json(OUT/"LIBRARY.json",lib)
    s2.write_json(OUT/"REGIONAL_COVERAGE.json",report)
    s2.write_json(OUT/"PHYSICAL_CLOSURE_REQUIREMENTS.json",{
        "pressure":"CONDITIONAL_ONLY_EXTERNAL_ABSOLUTE_PRESSURE_NOT_REQUIRED_FOR_MINIMUM_SHELLSET_PATH",
        "spatial_recipe_authority":"UNKNOWN","cold_felsic":"DEFERRED",
        "continuous_EOS":"UNQUALIFIED","rheology":"UNBOUND",
        "minimum_shellset_contract":"R6_SHELLSET_MINIMUM_THERMOMECHANICAL_STATE_CONTRACT.md",
        "next":"SELECT_PHYSICAL_PATH_AND_BIND_ACTUAL_REQUIRED_INPUTS_WITH_SOURCE_PROVENANCE",
        "additional_engine_runs":0,**c.SCOPE})
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C04_INTEGRATED_RESEARCH_LIBRARY_MANIFEST_V1",
        "source_sha":head,"status":STATUS,"C03FA_manifest_sha256":PIN,"C02_manifest_sha256":cold.PIN,
        "files":z.d.launcher.inventory(OUT),"states":35,"source_chemistries":14,
        "cold_MORB_native_chemistries":2,"regional_samples":3700,"physical_material_coverage_count":0,
        "additional_engine_runs":0,"scientific_promotion":False,**c.SCOPE})
    print("C04_LIBRARY",35,14,2,flush=True)
    print("C04_REGIONAL_COVERAGE",json.dumps(report["regions"],sort_keys=True),flush=True)
    print("C04_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"),flush=True)
    print(STATUS)
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()
