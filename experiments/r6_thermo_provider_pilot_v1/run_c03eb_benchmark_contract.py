"""C03E-B: materialize dataset-specific candidate and pre-register non-exact MORB comparison.
No native process or equilibrium is authorized here. Upstream inputs remain untouched.
"""
from __future__ import annotations
import argparse
from decimal import Decimal
import json
import re
from experiments.r6_thermo_provider_pilot_v1 import run_c03ea_configuration_audit as a

d=a.d
s2=a.s2
need=a.need
hgp=a.hgp
SCOPE=a.SCOPE
PIN="07bd106646263d618dd37bc5bb4b4d74a877457c4a7a9d7ace16b49c88a800b0"
PARENT="27af0a2019d10c440d7746c84b9d5f979d1d3c85"
OUT=s2.BASE/"R6_THERMO_C03EB_BENCHMARK_CONTRACT_NEW01"
STATUS="C03EB_DS5_VARIANT_AND_NONEXACT_BENCHMARK_CONTRACT_CAPTURED__EXECUTION_NOT_AUTHORIZED"
DP="cAmph(DP)"
DS6={"ts_q":10000,"gl":-3000,"parg":-10000,"grun":-3000,"mrb_q":0}
DS5={"ts_q":10000,"gl":3000,"parg":15000,"grun":-5000,"mrb_q":8000,"cumm":-6400}
RX=re.compile(r"^([ \t]*)(\|[ \t]*)?DQF\(([^)]+)\)[ \t]*=[ \t]*(-?\d+)[ \t]*\|[ \t]*(ds5/ds6|ds5|ds6)[ \t]*$",re.I)
EXCLUSIONS={"vesuvianite":"vsv","andradite":"andr","grossular":"gr","Na-phlogopite":"naph",
            "riebeckite":"rieb","zoisite":"zo","anthophyllite":"anth"}
DRY={"SIO2":"50.42","TIO2":"1.53","AL2O3":"15.13","FEO":"9.81",
     "MGO":"7.76","CAO":"11.35","NA2O":"2.83","K2O":"0.14"}


def active_dqf(block):
    result={}
    for line in a.section(d.composition_audit.active_text(block),"dqf_corrections").splitlines():
        if not line:
            continue
        m=re.fullmatch(r"\s*DQF\(([^)]+)\)\s*=\s*(-?\d+)\s*",line,re.I)
        need(m is not None and m[1] not in result,"C03EB_DQF_PARSE:"+line)
        result[m[1]]=int(m[2])
    return result


def switch_block(block):
    need(active_dqf(block)==DS6,"C03EB_ORIGINAL_DQF_DRIFT")
    lines=block.splitlines(keepends=True)
    start=[i for i,x in enumerate(lines) if x.strip()=="begin_dqf_corrections"]
    end=[i for i,x in enumerate(lines) if x.strip()=="end_dqf_corrections"]
    need(len(start)==len(end)==1 and start[0]<end[0],"C03EB_DQF_SECTION")
    changes=[]
    for i in range(start[0]+1,end[0]):
        body=lines[i].rstrip("\r\n")
        newline=lines[i][len(body):]
        m=RX.fullmatch(body)
        if not m:
            continue
        indent,comment,name,value,dataset=m.groups()
        if dataset=="ds6" and comment is None:
            new=indent+"| "+body[len(indent):]+newline
        elif dataset=="ds5" and comment is not None:
            new=indent+body[len(indent)+len(comment):]+newline
        else:
            continue
        changes.append({"block_line":i+1,"before":body,"after":new.rstrip("\r\n")})
        lines[i]=new
    out="".join(lines)
    need(len(changes)==9 and active_dqf(out)==DS5,"C03EB_SWITCH_DRIFT")
    return out,changes


def derive_models(raw):
    blocks=d.c.b.model_blocks(raw,(DP,))
    block=blocks[DP]
    need(block is not None,"C03EB_DP_MISSING")
    lines=raw.decode("utf-8").splitlines(keepends=True)
    lo,hi=block["line"]-1,block["end_line"]
    original="".join(lines[lo:hi])
    need(original.replace("\r\n","\n")==block["text"],"C03EB_MODEL_BLOCK_DRIFT")
    switched,changes=switch_block(original)
    candidate=("".join(lines[:lo])+switched+"".join(lines[hi:])).encode("utf-8")
    need(candidate!=raw and len(candidate.splitlines())==len(raw.splitlines()),"C03EB_LIBRARY_DERIVATION")
    other_before=lines[:lo]+lines[hi:]
    new_lines=candidate.decode().splitlines(keepends=True)
    need(other_before==new_lines[:lo]+new_lines[hi:],"C03EB_OTHER_MODEL_EDIT")
    return candidate,{"model":DP,"source_library_sha256":hgp.sha(raw),
                       "derived_library_sha256":hgp.sha(candidate),
                       "active_before_J_per_mol":DS6,"active_after_J_per_mol":DS5,
                       "changed_lines":changes,"other_models_unchanged":True,
                       "historical_ts_correction_ambiguity":True,
                       "calibration_qualified":False}


def benchmark_moles(masses,ferric):
    f=Decimal(str(ferric))
    need(0<f<1,"C03EB_FERRIC_RATIO")
    mol={k:Decimal(v)/Decimal(str(masses[k])) for k,v in DRY.items()}
    mol["O2"]=mol["FEO"]*f/4
    # H2O is a saturated-phase component, not a fixed dry bulk input.
    return {k:str(v) for k,v in mol.items()}


def benchmark_contract(masses,records):
    need(all(k in records for k in EXCLUSIONS.values()),"C03EB_EXCLUSION_CROSSWALK")
    need(sum(Decimal(v) for v in DRY.values())==Decimal("98.97"),"C03EB_DRY_SOURCE_SUM")
    original=list(d.c.VERTICES)
    base=[x for x in original if x not in ("GlTrTsPg","Act(M)")]
    # Only one amphibole model per comparison arm. Neither is qualified.
    arms={"ACT_ONLY":{"solution_models":base+["Act(M)"],"library":"ORIGINAL"},
          "DP_DS5_ONLY":{"solution_models":base+[DP],"library":"DERIVED_DS5"}}
    points=[
        {"id":"B01","T_C":225,"P_bar":1500,"targets":["chlorite","Ca-rich amphibole","prehnite"],
         "rationale":"interior low-P prehnite range"},
        {"id":"B02","T_C":200,"P_bar":4000,"targets":["chlorite","Ca-rich amphibole","lawsonite"],
         "rationale":"high-P low-T lawsonite range"},
        {"id":"B03","T_C":315,"P_bar":2000,"targets":["chlorite","Ca-rich amphibole","epidote"],
         "expected_absent":["clinopyroxene"],"rationale":"reported low-P Cpx gap"}]
    for x in points:
        x["T_K"]=str(Decimal(x["T_C"])+Decimal("273.15"))
        x["target_authority"]="SECTION_3_1_BROAD_TEXT_EXPECTATION_NOT_DIGITIZED_POINT"
    return {"reference":{"doi":"10.1029/2018JE005869",
                "locator":"Sections 2.1, 3.1, Tables 1/2, Figure 1a",
                "pdf":"https://oro.open.ac.uk/59162/1/Semprich_et_al-2019-Journal_of_Geophysical_Research__Planets.pdf",
                "original_pdf_bytes_sha256":None,"visual_digitization":"UNAVAILABLE_CACHE_MISS",
                "exact_O2_input":None,"supplementary_inputs_recovered":False,
                "classification":"NONEXACT_TEXT_CONSTRAINED_MODEL_COMPARISON"},
            "dry_oxide_wt_as_published":DRY,"dry_oxide_sum":str(sum(Decimal(v) for v in DRY.values())),
            "boundary":{"H2O":"SATURATED_PURE_FLUID_CANDIDATE","O2":"FIXED_COMPONENT_NOT_BUFFER",
                        "fluid_EOS":"CORK_CANDIDATE","native_project_serialization_verified":False},
            "redox":{"initial_Fe3_fraction_primary":0.10,"initial_Fe3_fraction_sensitivity":0.15,
                     "choices_authority":"ARCANA_EXPLICIT_SENSITIVITY_NOT_PAPER_INPUT",
                     "primary_moles":benchmark_moles(masses,"0.10"),
                     "sensitivity_moles":benchmark_moles(masses,"0.15"),
                     "paper_reported_O2_range":[0.12,0.15],"paper_range_units_unresolved":True},
            "literature_exclusion_crosswalk":EXCLUSIONS,
            "exclusion_policy":"CANDIDATE_FOR_REFERENCE_COMPARISON_ONLY_NOT_ARCANA",
            "additional_species_policy":{"O2":"CANDIDATE_EXCLUDE_MOLECULAR_SPECIES_RETAIN_COMPONENT",
                                         "H2":"REVIEW_REQUIRED","Si(s)":"NATIVE_REJECTION_UNQUALIFIED",
                                         "iron":"REVIEW_REQUIRED","h2oL":"REVIEW_REQUIRED"},
            "pure_phase_admission_verified":False,
            "arms":arms,"points":points,
            "first_batch_design":{"processes":2,"points_per_process":3,"total_requested_points":6,
                                  "redox_case":"primary","sequential":True,
                                  "authorization":False,"budget":"PROPOSED_NOT_RATIFIED"},
            "acceptance":{"native_initialization":"all requested models accounted; no invalid-site or fatal warnings",
                          "physical_checks":["finite properties","positive phase amounts subject to printed rounding",
                                             "mass balance of conserved components within documented output precision",
                                             "saturated water boundary verified independently"],
                          "mineralogical_checks":"report target presence/absence by phase identity and composition; do not equate Amph label to Ca-rich amphibole",
                          "reference_modal_targets":None,
                          "quantitative_tolerances":None,
                          "interpretation":"comparison only; no scientific promotion from broad text agreement",
                          "kinetic_applicability":"NOT_ESTABLISHED"},
            "secondary_reference":{"doi":"10.1127/0935-1221/2008/0020-1871",
                                   "evidence":"abstract confirms low-grade MORB phase and dehydration comparison; full input unavailable"},
            "executable":False,"authorized_equilibrium_solver_calls":0}


def parent():
    receipt=json.loads((d.m.HERE/"c03ea_fair_receipt_v1.json").read_text())
    man=d.m.archive_manifest(a.OUT,PIN,"files_sha256")
    need(man["schema"]=="R6_C03EA_CONFIGURATION_AUDIT_MANIFEST_V1"
         and man["source_sha"]==receipt["source_sha"]==PARENT
         and receipt["manifest_sha256"]==PIN and receipt["exit"]==0
         and man["status"]==receipt["status"]==a.STATUS
         and man["C03E_manifest_sha256"]==receipt["C03E_manifest_sha256"]==a.PIN
         and man["additional_engine_runs"]==man["authorized_equilibrium_solver_calls"]==0
         and not man["scientific_promotion"] and set(man["files_sha256"])=={"CONFIGURATION_AUDIT.json"}
         and all(man[k]==v for k,v in SCOPE.items()),"C03EB_PARENT")
    prev=json.loads((a.OUT/"CONFIGURATION_AUDIT.json").read_text())
    report,runtime,hp,models=a.parent()
    masses=d.c.b.components(hp)
    direct=d.composition_audit.inventory(hp,masses,d.ORDER)
    makes=a.equations(a.section(d.composition_audit.active_text(hp.decode()),"makes"))
    blocks=d.c.b.model_blocks(models,tuple(a.VERTICES))
    candidates={k:a.audit_candidate(k,blocks[k],direct,makes) for k in a.VERTICES}
    need(prev["candidate_models"]==candidates and prev["configuration_risks"]==a.risk_inventory(direct,report)
         and prev["provider_runtime"]==runtime and prev["selected_model"] is None
         and prev["additional_engine_runs"]==prev["authorized_equilibrium_solver_calls"]==0
         and all(prev[k]==v for k,v in SCOPE.items()),"C03EB_PARENT_REPLAY")
    return models,masses,direct


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03EB_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C03EB_OUTPUT_EXISTS")
    models,masses,records=parent()
    candidate,change=derive_models(models)
    contract=benchmark_contract(masses,records)
    need(len(candidate)<16*1024**2,"C03EB_FILE_BUDGET")
    OUT.mkdir(parents=False,exist_ok=False)
    with (OUT/"solution_model_DP_DS5_candidate.dat").open("xb") as f:
        f.write(candidate)
    result={"schema":"R6_C03EB_BENCHMARK_CONTRACT_V1","status":STATUS,
            "C03EA_manifest_sha256":PIN,"candidate_derivation":change,
            "upstream_calibration_authority":"https://www.perplex.ethz.ch/perple_x_updates/perple_x_updates.html",
            "historical_correction_authority":"https://www.perplex.ethz.ch/examples/perplex_updates_body.html",
            "boundary_authority":"https://www.perplex.ethz.ch/perplex_66_build_prompts.html",
            "benchmark":contract,"additional_engine_runs":0,"authorized_equilibrium_solver_calls":0,
            "scientific_promotion":False,**SCOPE}
    s2.write_json(OUT/"BENCHMARK_CONTRACT.json",result)
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03EB_BENCHMARK_CONTRACT_MANIFEST_V1",
        "source_sha":head,"status":STATUS,"C03EA_manifest_sha256":PIN,
        "files_sha256":{k:s2.sha(OUT/k) for k in ("BENCHMARK_CONTRACT.json","solution_model_DP_DS5_candidate.dat")},
        "additional_engine_runs":0,"authorized_equilibrium_solver_calls":0,"scientific_promotion":False,**SCOPE})
    print("C03EB_C03EA_PARENT_REPLAY_PASS",PIN)
    print("C03EB_DQF_VARIANT",json.dumps(change,sort_keys=True))
    print("C03EB_BENCHMARK_DESIGN",len(contract["arms"]),len(contract["points"]),contract["first_batch_design"])
    print("C03EB_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
    print(STATUS)
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()
