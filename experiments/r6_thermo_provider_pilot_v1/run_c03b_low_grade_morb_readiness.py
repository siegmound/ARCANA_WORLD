"""C03B: source-pinned low-grade MORB model/basis readiness; no engine execution."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03_cold_crust_design as d

m=d.m
s2=d.s2
need=d.need
SCOPE=d.SCOPE
PIN="0b05bfc715352d960cae08f0049e494c38d69796f38f622916fbcd2ea8c69f18"
PARENT="0d1ed77353952018f7908f6d9a1855d4a66852fd"
OUT=s2.BASE/"R6_THERMO_C03B_LOW_GRADE_MORB_READINESS_NEW01"
HP02_BLOB="2515636a49b91cbee796d7b1ddee4fbdf94fa940"
MODEL_BLOB="564742a569998a768c2d8e15d2b9599ee90438d1"
CORE={"Pu(M)":("pump","fpum","ffpu"),"Stlp(M)":("stlp","mstl","mnsp"),
      "Act(M)":("tr","acti","gl","mrie"),"Mica(M)":("ma","mu","pa")}
NAMES=("Chl(HP)","Chl(W)","Ep(HP11)","Mica(W)","Fsp(HGP)","lAb(HGP)",
       "Pu(M)","Stlp(M)","Act(M)","Mica(M)","Cpx(HP)","Opx(HP)","Kf","Pl(h)","Bio(TCC)")
MORB=("C01_MORB_BASE","C01_MORB_WET")


def model_blocks(raw,names=NAMES):
    # The previous C03 regex missed bare headers (no trailing whitespace).
    # Strip inline comments, require an actual following abbreviation field and end marker.
    lines=raw.decode("utf-8",errors="strict").splitlines()
    result={}
    for name in names:
        hits=[i for i,line in enumerate(lines[:-1])
              if line.split("|",1)[0].strip()==name
              and lines[i+1].strip().startswith("abbreviation ")]
        need(len(hits)<=1,"C03B_AMBIGUOUS_MODEL:"+name)
        if not hits:
            result[name]=None
            continue
        i=hits[0]
        stop=next((j for j in range(i+1,len(lines))
                   if lines[j].strip().split("|",1)[0].strip()=="end_of_model"),None)
        need(stop is not None,"C03B_UNTERMINATED_MODEL:"+name)
        block="\n".join(lines[i:stop+1])+"\n"
        result[name]={"line":i+1,"end_line":stop+1,"normalized_text_sha256":d.hgp.sha(block.encode()),"text":block}
    return result


def endmember_names(raw):
    # Match uncommented native EoS record headers, not glossary/comments.
    text=raw.decode("utf-8",errors="strict")
    return set(re.findall(r"(?m)^([A-Za-z0-9_+.-]+)[ \t]+EoS[ \t]*=",text))


def components(raw):
    lines=raw.decode("utf-8",errors="strict").splitlines()
    starts=[i for i,x in enumerate(lines) if x.split("|",1)[0].strip()=="begin_components"]
    need(len(starts)==1,"C03B_COMPONENT_START")
    ends=[i for i,x in enumerate(lines) if x.split("|",1)[0].strip()=="end_components"]
    need(len(ends)==1 and ends[0]>starts[0],"C03B_COMPONENT_END")
    out={}
    for line in lines[starts[0]+1:ends[0]]:
        fields=line.split("|",1)[0].split()
        if not fields:
            continue
        need(len(fields)>=2 and fields[0] not in out,"C03B_COMPONENT_ROW")
        mass=float(fields[1]);need(m.finite(mass) and mass>0,"C03B_COMPONENT_MASS")
        out[fields[0]]=mass
    return out


def native_morb_basis(inp,masses):
    # Preserve the previous recipe's mole ledger. Re-express ferric oxygen as O2,
    # not as O or Fe2O3 in the native Perple_X component list.
    vals=dict(zip(inp["names"],inp["wt_amounts"],strict=True))
    need(len(vals)==len(inp["names"])==len(inp["wt_amounts"])
        and set(vals)==set(d.a.p.p.NAMES) and all(m.finite(v) and v>=0 for v in vals.values()),
        "C03B_MORB_INPUT")
    old={k:v/m.MASS[k] for k,v in vals.items()}
    ferric=old.pop("Fe2O3")
    old["FeO"]+=2*ferric
    native={k.upper():v for k,v in old.items()}
    native["O2"]=ferric/2
    need(set(native)<=set(masses) and m.close(native["FEO"],vals["FeO"]/m.MASS["FeO"]+2*ferric)
        and m.close(native["O2"]*2,ferric),"C03B_NATIVE_STOICHIOMETRY")
    amounts={k:v*masses[k] for k,v in native.items()}
    total=sum(amounts.values())
    need(total>0,"C03B_NATIVE_MASS")
    return {"native_moles_per_source_recipe":native,"native_mass_g_per_source_recipe":amounts,
        "normalized_native_wt_percent":{k:100*v/total for k,v in amounts.items()},
        "native_total_mass_g":total,"original_reduced_recipe_mass_g":sum(vals.values()),
        "mass_difference_from_molar_mass_convention_g":total-sum(vals.values()),
        "oxygen_semantics":"O2_COMPONENT_MOLES_HALF_FERRIC_OXIDE_MOLES",
        "fluid_boundary":"CLOSED_BULK_WATER_CANDIDATE_NOT_WATER_SATURATION",
        "omitted_source_oxides_wt":inp["omitted_source_oxides_wt"],
        "native_engine_conversion_verified":False}


def audit_design():
    rec=json.loads((m.HERE/"c03_design_fair_receipt_v1.json").read_text())
    man=m.archive_manifest(d.OUT,PIN,"files_sha256")
    need(man["schema"]=="R6_C03_COLD_CRUST_DESIGN_MANIFEST_V1"
        and man["source_sha"]==rec["source_sha"]==PARENT and rec["manifest_sha256"]==PIN
        and rec["exit"]==0 and man["consolidation_manifest_sha256"]==d.PIN
        and man["additional_engine_runs"]==man["authorized_solver_calls"]==0
        and set(man["files_sha256"])=={"DESIGN.json"} and all(man[k]==v for k,v in SCOPE.items()),"C03B_DESIGN_MANIFEST")
    lib,cov=d.load_consolidated()
    old=json.loads((d.OUT/"DESIGN.json").read_text())
    inputs,_,runtime=d.hgp.verify_runtime_and_inputs()
    need(runtime==man["perplex_runtime"] and old==d.proposed_design(lib,cov,inputs)
        and old["candidate_source_points"]==rec["source_points"]
        and old["perplex_pinned_solution_file_header_sightings"]==rec["original_header_sightings"]
        and all(all(old["cohort"][e][k]==v for k,v in z.items()) for e,z in rec["cohort"].items()),"C03B_DESIGN_REPLAY")
    return old,inputs,runtime


def build(old,inputs,runtime):
    source=Path(runtime["source"])
    hp02=(source/"datafiles/hp02ver.dat").read_bytes()
    sol=inputs["solution_model.dat"]
    need(d.hgp.blob(hp02)==HP02_BLOB and d.hgp.blob(sol)==MODEL_BLOB,"C03B_PINNED_NATIVE_SOURCE")
    blocks=model_blocks(sol)
    oldset=endmember_names(inputs["hp62ver.dat"]);newset=endmember_names(hp02)
    needs={}
    for name,required in CORE.items():
        block=blocks[name]
        need(block is not None and all(re.search(r"(?<![\w])"+re.escape(k)+r"(?![\w])",block["text"]) for k in required),"C03B_MODEL_SOURCE:"+name)
        needs[name]={"required_named_endmembers":list(required),"hp62_missing":sorted(set(required)-oldset),
            "hp02_missing":sorted(set(required)-newset)}
    need(not any(v["hp02_missing"] for v in needs.values())
        and set(needs["Pu(M)"]["hp62_missing"])=={"pump","fpum","ffpu"},"C03B_EXPECTED_ENDMEMBER_MEMBERSHIP")
    masses=components(hp02)
    cases=[]
    for name in MORB:
        source=old["reference_recipes"][name]
        inp=source["source_input"]
        need(d.a.c.l.chemistry_id(inp)==source["chemistry_sha256"],"C03B_RECIPE_ID")
        basis=native_morb_basis(inp,masses)
        for point in old["candidate_source_points"]:
            need(150<=point["T_C"]<=450 and 1<=point["conditional_delta_P_kbar"]<=25
                and point["absolute_pressure_pa"] is None,"C03B_PT_CONTEXT")
            cases.append({"id":name+"_P"+str(point["parent_node_id"]),"source_recipe":name,
                "source_chemistry_sha256":source["chemistry_sha256"],"source_point":point,"candidate_basis":basis})
    return {"schema":"R6_C03B_LOW_GRADE_MORB_READINESS_V1",
        "status":"HP02_MORB_CANDIDATE__PHASE_ROSTER_AND_NATIVE_PREFLIGHT_PENDING",
        "C03_manifest_sha256":PIN,"hp02_git_blob":HP02_BLOB,"hp02_sha256":d.hgp.sha(hp02),
        "solution_model_git_blob":MODEL_BLOB,"model_blocks":blocks,"core_endmember_inventory":needs,
        "candidate_native_components_g_mol":masses,"candidate_cases":cases,
        "candidate_scope":"NONCANONICAL_LOW_GRADE_MORB_ONLY",
        "source_domain_context":{"reference":"10.1127/0935-1221/2008/0020-1871","T_C":[150,450],"P_kbar":[1,25],
            "not_a_calibration_certificate_for_our_recipes":True},
        "not_yet_resolved":["complete compatible phase roster and dependent endmembers",
            "feldspar structural model applicability","fluid and redox options",
            "native MEEMUM input and component readback","independent Earth benchmark and source PDF pin"],
        "UCC_status":"DEFERRED_NO_GENERIC_FELSIC_SUBSOLIDUS_MODEL_SELECTED",
        "scientific_promotion":False,"authorial_selection":None,"authorized_solver_calls":0,
        "additional_engine_runs":0,**SCOPE}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03B_CHECKOUT")
    need(not OUT.exists(),"C03B_OUTPUT_EXISTS")
    old,inputs,runtime=audit_design()
    print("C03B_INDEPENDENT_DESIGN_REPLAY_PASS",PIN,flush=True)
    report=build(old,inputs,runtime)
    OUT.mkdir(parents=False,exist_ok=False)
    s2.write_json(OUT/"READINESS.json",report)
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03B_LOW_GRADE_MORB_READINESS_MANIFEST_V1",
        "source_sha":head,"C03_manifest_sha256":PIN,"additional_engine_runs":0,"authorized_solver_calls":0,
        "files_sha256":{"READINESS.json":s2.sha(OUT/"READINESS.json")},**SCOPE})
    print("C03B_MODEL_HEADERS",json.dumps({k:v["line"] if v else None for k,v in report["model_blocks"].items()},sort_keys=True))
    print("C03B_ENDMEMBER_INVENTORY",json.dumps(report["core_endmember_inventory"],sort_keys=True))
    print("C03B_MORB_CANDIDATE_CASES",len(report["candidate_cases"]))
    print("C03B_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
    print("C03B_LOW_GRADE_MORB_READINESS_COMPLETE__PHASE_ROSTER_PENDING")
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()
