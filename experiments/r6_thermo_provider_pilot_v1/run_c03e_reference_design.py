"""C03D technical closure and C03E reference design; read-only replay, no engine."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03d_native_initialization as d

s2=d.s2
need=d.need
hgp=d.hgp
SCOPE=d.SCOPE
PIN="5a64f2e9ba0d753a3183bef295ce6771529b3ba178928012909d378e8a1891af"
PARENT="deb7f4e919e53157662dc32bdf1bc6c2737817ab"
OUT=s2.BASE/"R6_THERMO_C03E_REFERENCE_DESIGN_NEW01"
STATUS="C03D_TECHNICAL_REPLAY_PASS__C03E_REFERENCE_DESIGN_BLOCKED_PENDING_SCIENTIFIC_INPUTS"


def read(path):
    return json.loads(path.read_text())


def invalid_sites(raw):
    text=raw.decode("utf-8",errors="replace")
    result={}
    for member,model in re.findall(r"(?m)^\s*\*\*warning ver059\*\* endmember\s+(\S+)\s+in solution model\s+(\S+)\s+has invalid site populations\.\s*$",text):
        result.setdefault(model,[]).append(member)
    return result


def validate_details(z,receipt,roster):
    counts=z["pseudocompound_reports"]
    countmap={x["model"]:x["count"] for x in counts}
    need(len(counts)==len(countmap)==len(roster)==18 and set(countmap)==set(roster)
        and all(x["requested_model"] and type(x["count"]) is int and x["count"]>0 for x in counts)
        and countmap==receipt["model_counts"] and sum(countmap.values())==receipt["total_pseudocompounds_per_recipe"]
        and z["native_total_pseudocompounds_reports"]==[receipt["total_pseudocompounds_per_recipe"]],
        "C03E_PSEUDOCOMPOUND_REPLAY")
    reports=z["missing_endmember_reports"]
    missing={x["model"]:[v["endmember"] for v in x["endmembers"]] for x in reports}
    need(len(reports)==len(missing) and all(x["requested_model"] and x["parsed_nonempty"] for x in reports)
         and missing==receipt["missing_by_model"] and sum(map(len,missing.values()))==8
         and not z["full_native_pruning_verified"] and not z["scientific_acceptance"],
         "C03E_MISSING_ENDMEMBER_REPLAY")
    return {"counts":countmap,"missing":missing}


def validate_dialogue(dia,stdin,raw,receipt):
    prompts=[d.dialogue.PROJECT]+[d.dialogue.WARNING]*4+[d.dialogue.BULK,d.dialogue.PT]
    kinds=["PROJECT","HP02_O2_VER966","HP02_O2_VER968","HP02_SI_REJECTION_VER013",
           "GLTRTSPG_LEGACY_VER017","FIXED_BULK","ZERO_PT_SENTINEL"]
    responses=["c03d","y","y","y","y","n","0 0"]
    events=dia["events"]
    need(dia["policy"]==d.dialogue.R4_POLICY and dia["state"]=="SENTINEL_SENT"
         and dia["error"] is None and dia["scientific_warning_acceptance"] is False
         and dia["requested_equilibrium_points"]==0
         and dia["acknowledged_warning_codes"]==receipt["acknowledged_warning_codes"]
         and [x["prompt"] for x in events]==kinds and [x["response"] for x in events]==responses
         and stdin==("\n".join(responses)+"\n").encode(),"C03E_DIALOGUE_REPLAY")
    cursor=0
    for event,prompt in zip(events,prompts,strict=True):
        end=event["stdout_byte_offset_after_prompt"]
        need(type(end) is int and cursor+len(prompt)<=end<=len(raw)
             and raw[end-len(prompt):end]==prompt,"C03E_DIALOGUE_OFFSET")
        cursor=end
    protocol=d.dialogue.Dialogue(allow_si013=True,allow_gl017=True)
    replay=[]
    while (response:=protocol.next_response(raw)) is not None:
        replay.append(response)
    need(b"".join(replay)==stdin and protocol.events==events
         and protocol.acknowledged==dia["acknowledged_warning_codes"]
         and protocol.state==dia["state"],"C03E_CONTROLLER_REPLAY")


def replay():
    rec=read(d.m.HERE/"c03d_r4_fair_receipt_v1.json")
    need(hgp.file_sha(d.OUT/"MANIFEST.json")==PIN==rec["manifest_sha256"],
         "C03E_PARENT_MANIFEST_HASH")
    man=read(d.OUT/"MANIFEST.json")
    members=d.launcher.inventory(d.OUT)
    members.pop("MANIFEST.json")
    need(members==man["files"] and man["schema"]=="R6_C03D_NATIVE_INITIALIZATION_MANIFEST_V1"
         and man["source_sha"]==rec["source_sha"]==PARENT
         and man["status"]=="NATIVE_INITIALIZATION_CAPTURED__REVIEW_REQUIRED"
         and man["C03C_manifest_sha256"]==d.PIN and man["native_initialization_attempts"]==2
         and man["requested_equilibrium_points"]==man["authorized_equilibrium_solver_calls"]==0
         and not man["scientific_promotion"] and rec["exit"]==0
         and all(man[k]==v for k,v in SCOPE.items()),"C03E_PARENT_MANIFEST")
    report,runtime,template,hp,models,options=d.audit_parent()
    d.audit_failed_attempt()
    d.audit_r1_failed_attempt()
    d.audit_r2_failed_attempt()
    roster=list(d.c.VERTICES)
    masses=d.c.b.components(hp)
    blocks=d.c.b.model_blocks(models,tuple(roster))
    composition=d.composition_audit.audit(hp,masses,d.ORDER,blocks,d.c.PURE.values())
    d.audit_r3_failed_attempt(composition,roster)
    legacy=d.model_audit.model_audit(blocks)
    need(read(d.OUT/"DIRECT_EOS_AUDIT.json")==composition and read(d.OUT/"MODEL_AUDIT.json")==legacy,
         "C03E_SOURCE_AUDITS_DRIFT")
    prov=read(d.OUT/"PROVENANCE.json")
    need(prov["source_sha"]==PARENT and prov["runtime"]==runtime
         and prov["dialogue_policy"]==d.dialogue.R4_POLICY
         and prov["requested_solution_models"]==roster
         and prov["direct_eos_audit_sha256"]==hgp.file_sha(d.OUT/"DIRECT_EOS_AUDIT.json")
         and prov["model_audit_sha256"]==hgp.file_sha(d.OUT/"MODEL_AUDIT.json")
         and all(prov[k]==v for k,v in SCOPE.items()),"C03E_PROVENANCE")
    results={}
    summary={}
    for name in d.c.b.MORB:
        work=d.OUT/name
        basis,chem=d.recipe_basis(report["candidate_cases"],name)
        project,normalized=d.project_input(template,basis,masses,roster)
        files={"c03d.dat":project,"hp02ver.dat":hp,"solution_model.dat":models,
               "perplex_option.dat":d.options_candidate(options)}
        need(all((work/k).read_bytes()==v for k,v in files.items()),"C03E_NATIVE_INPUT_DRIFT:"+name)
        expected={"source_chemistry_sha256":chem,"normalized_native_molar_amounts":normalized,
                  "fixed_width_input_roundtrip":d.fixed_width_readback(project,normalized),
                  "files_sha256":{k:hgp.sha(v) for k,v in files.items()},"requested_equilibrium_points":0}
        need(read(work/"INPUT.json")==expected,"C03E_INPUT_RECEIPT_DRIFT:"+name)
        raw=(work/"RUN_STDOUT.log").read_bytes()
        prn=work/"c03d.prn"
        obs=d.observe(raw,prn.read_bytes() if prn.is_file() else b"",roster)
        dia=read(work/"DIALOGUE.json")
        validate_dialogue(dia,(work/"DIALOGUE_STDIN.log").read_bytes(),raw,rec)
        launch=read(work/"LAUNCH.json")
        need(launch["exit_code"]==0 and launch["timeout"] is False and launch["error"] is None,
             "C03E_LAUNCH_DRIFT:"+name)
        details=d.model_audit.native_model_details(raw,roster,composition["records"])
        summary[name]=validate_details(details,rec,roster)
        need(details==read(work/"NATIVE_MODEL_DETAILS.json"),"C03E_DETAILS_DRIFT:"+name)
        need(invalid_sites(raw)==rec["invalid_site_populations"],"C03E_INVALID_SITE_DRIFT:"+name)
        need(set(obs["native_model_dispositions"]["included"])==set(roster)
             and not obs["native_model_dispositions"]["rejected"]
             and not obs["native_model_dispositions"]["not_found"]
             and not obs["unaccounted_requested_models"],"C03E_NATIVE_ROSTER_DRIFT:"+name)
        obs["dialogue"]=dia
        obs["native_model_details"]=details
        need(obs==read(work/"READBACK.json"),"C03E_READBACK_DRIFT:"+name)
        results[name]=obs
        summary[name]["invalid_site_populations"]=invalid_sites(raw)
        summary[name]["all_warning_headers"]=re.findall(r"(?m)^\s*\*\*warning ver\d+\*\*[^\n]*",raw.decode("utf-8",errors="replace"))
    result=read(d.OUT/"RESULT.json")
    need(result=={"observations":results,"requested_equilibrium_points":0,
                  "native_initialization_attempts":2,"campaign_authorized":False,**SCOPE},
         "C03E_RESULT_REPLAY")
    need(results["C01_MORB_BASE"]["native_model_details"]==results["C01_MORB_WET"]["native_model_details"],
         "C03E_RECIPE_ROSTER_DIFFERENCE")
    return summary,report["benchmark_candidate"]


def reference_design(benchmark):
    return {"reference":benchmark,
            "reference_scope":"PUBLISHED_EARTH_MORB_MODEL_COMPARISON_NOT_LAB_VALIDATION",
            "reference_pt":{"temperature_C":[150,450],"pressure_GPa":[0,0.5]},
            "reference_boundary":"PURE_WATER_SATURATION_NOT_FIXED_BULK",
            "reference_O2":{"reported_range":[0.12,0.15],"exact_MORB_value":None,
                            "unit_and_normalization_verified":False,"buffer_imposed":False},
            "reference_reported_exclusions":["vesuvianite","andradite","grossular","Na-phlogopite",
                                            "riebeckite","zoisite","anthophyllite"],
            "reference_pdf_visual_check":"FAILED_CACHE_MISS",
            "exact_figure_targets":None,"quantitative_acceptance_thresholds":None,
            "scientific_blockers":{
                "amphibole":"GlTrTsPg ver017 and three ver059 invalid site populations; no scientific use approved",
                "amphibole_candidates":["cAmph(DP)","cAmph_I(DP)","cAmph(G)"],
                "oxygen":"Separate O2 component inventory from O2 phase EOS; redox and species admission unresolved",
                "silicon":"Native zero-sum rejection observed; applicability not qualified",
                "pruning":"8 native missing endmembers; retained topology and pure phase admission unverified",
                "benchmark":"Exact O2 units/value, reference phase restrictions, source figure targets and tolerances unresolved",
                "water":"Reference saturated boundary is not the ARCANA closed bulk boundary"},
            "required_next":["pin reference PDF and supporting data; obtain exact input or declare non-exact comparison",
                             "audit alternative amphibole model dependencies and applicability against HP02",
                             "adjudicate O2 phase EOS and reduced phase admission without changing ferric oxygen ledger",
                             "resolve pure-phase selection and missing endmember scientific implications",
                             "define benchmark points and acceptance metrics before requesting any engine calls"],
            "benchmark_executable":False,"authorized_equilibrium_solver_calls":0}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03E_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C03E_OUTPUT_EXISTS")
    summary,benchmark=replay()
    report={"schema":"R6_C03E_REFERENCE_DESIGN_V1","status":STATUS,
            "C03D_manifest_sha256":PIN,"native_replay":summary,
            "design":reference_design(benchmark),"additional_engine_runs":0,
            "authorized_equilibrium_solver_calls":0,"scientific_promotion":False,**SCOPE}
    OUT.mkdir(parents=False,exist_ok=False)
    s2.write_json(OUT/"REFERENCE_DESIGN.json",report)
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03E_REFERENCE_DESIGN_MANIFEST_V1",
        "source_sha":head,"status":STATUS,"C03D_manifest_sha256":PIN,
        "files_sha256":{"REFERENCE_DESIGN.json":s2.sha(OUT/"REFERENCE_DESIGN.json")},
        "additional_engine_runs":0,"authorized_equilibrium_solver_calls":0,
        "scientific_promotion":False,**SCOPE})
    print("C03E_INDEPENDENT_C03D_REPLAY_PASS",PIN)
    print("C03E_NATIVE_ROSTER",18,"PSEUDOCOMPOUNDS_PER_RECIPE",1454,"MISSING_PER_RECIPE",8)
    print("C03E_INVALID_SITE_POPULATIONS",json.dumps(summary["C01_MORB_BASE"]["invalid_site_populations"]))
    print("C03E_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
    print(STATUS)
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()
