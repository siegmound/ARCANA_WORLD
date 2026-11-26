"""Close reference diagnostic review and materialize four ARCANA closed-bulk candidate inputs.
No native process or world material assignment in this stage.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03ee_r2_dp_solver_sensitivity as r2

r1=r2.r1
c=r2.c
d=c.d
s2=c.s2
need=c.need
hgp=c.hgp
PIN="70696a75b5bc4bb8b73fbcb950eba0e5ed73adabad89d2079f75740836611b3b"
SOURCE="62f3d1555b820a34f800342194ae2c5d9d25d9e9"
OUT=s2.BASE/"R6_THERMO_C03F_CLOSED_BULK_DESIGN_NEW01"
STATUS="C03F_ACT_CLOSED_BULK_INPUTS_CAPTURED__NATIVE_QUALIFICATION_REQUIRED"


def review_pair(act,dp):
    need(act["id"]==dp["id"] and act["target"]==dp["target"]
         and act["target_present"] and dp["target_present"],"C03F_REFERENCE_TARGET")
    a=act["phase_wt_percent"]
    b=dp["phase_wt_percent"]
    need(a.get("Act(M)",0)>0 and b.get("acti",0)>0 and "cAmph(DP)" not in b,
         "C03F_AMPHIBOLE_OBSERVATION_DRIFT")
    names=set(a)|set(b)
    # Compare amphibole as a family without erasing native model identity.
    names-= {"Act(M)","acti"}
    delta={k:b.get(k,0)-a.get(k,0) for k in sorted(names)}
    delta["amphibole_family"]=b["acti"]-a["Act(M)"]
    return {"id":act["id"],"target":act["target"],
            "target_wt_percent":{"ACT":a[act["target"]],"DP":b[dp["target"]]},
            "phase_delta_DP_minus_ACT_percentage_points":delta,
            "density_relative_delta":dp["density_kg_m3"]/act["density_kg_m3"]-1,
            "Cp_relative_delta":dp["Cp_J_kg_K"]/act["Cp_J_kg_K"]-1,
            "H2O_delta_percentage_points":dp["H2O_wt_percent"]-act["H2O_wt_percent"],
            "ACT_amphibole_native_identity":"Act(M)","DP_amphibole_native_identity":"acti",
            "DP_solution_observed":False,"solver_confounding":True}


def replay_reference(parent):
    act=r2.verify_archive(parent)
    archive=r2.OUT
    rec=c.read(d.m.HERE/"c03ee_r2_fair_receipt_v1.json")
    need(archive.is_dir() and not archive.is_symlink()
         and not (archive/"MANIFEST.json").is_symlink()
         and hgp.file_sha(archive/"MANIFEST.json")==PIN==rec["manifest_sha256"],
         "C03F_REFERENCE_PIN")
    man=c.read(archive/"MANIFEST.json")
    inv=d.launcher.inventory(archive)
    inv.pop("MANIFEST.json")
    need(inv==man["files"] and man["source_sha"]==SOURCE==rec["source_sha"]
         and man["schema"]=="R6_C03EE_R2_DP_SOLVER_SENSITIVITY_MANIFEST_V1"
         and man["status"]==r2.STATUS and man["R1_manifest_sha256"]==r2.PIN
         and man["native_initialization_attempts"]==1
         and man["requested_equilibrium_points"]==man["completed_equilibrium_points"]==3
         and man["scientific_promotion"] is False
         and all(man[k]==v for k,v in c.SCOPE.items()),"C03F_REFERENCE_MANIFEST")
    need(c.read(archive/"ACT_ARCHIVE_AUDIT.json")=={"source_manifest":r2.PIN,"points":act,
            "scientific_promotion":False},"C03F_ACT_ARCHIVE_AUDIT")
    report,runtime,template,hp,original,derived,options,contract,records=parent
    source=r2.verify_source(runtime)
    work=archive/"DP_DS5_ONLY_MINFXC"
    old=r1.OUT/"DP_DS5_ONLY"
    expected={k:(old/k).read_bytes() for k in ("c03d.dat","hp02ver.dat","solution_model.dat","perplex_option.dat")}
    expected["perplex_option.dat"]=r2.solver_option(expected["perplex_option.dat"])
    need(all((work/k).read_bytes()==v for k,v in expected.items()),"C03F_DP_INPUT")
    inp=c.read(work/"INPUT.json")
    roster=contract["arms"]["DP_DS5_ONLY"]["solution_models"]
    norm=c.read(old/"INPUT.json")["normalized_conserved_moles"]
    need(inp["normalized_conserved_moles"]==norm and inp["solution_models"]==roster
         and inp["files_sha256"]=={k:hgp.sha(v) for k,v in expected.items()},"C03F_DP_METADATA")
    p=r1.DiagnosticDialogue("DP_DS5_ONLY",records,roster)
    raw=(work/"RUN_STDOUT.log").read_bytes()
    replies=[]
    while True:
        reply=p.next_response(raw)
        if reply is None:
            break
        replies.append(reply)
    dia=c.read(work/"DIALOGUE.json")
    launch=c.read(work/"LAUNCH.json")
    result=c.read(work/"RESULT.json")
    dp=[r2.audit_point(x,norm,act=False) for x in p.completed]
    need(b"".join(replies)==(work/"DIALOGUE_STDIN.log").read_bytes()
         and p.events==dia["events"] and p.state=="SENTINEL_SENT"
         and p.requested==["B01","B02","B03"]
         and launch["exit_code"]==0 and launch["error"] is None
         and result["points"]==p.completed and result["audit"]==dp
         and result["launch"]==launch
         and c.read(work/"POINT_CAPTURE.json")=={"requested_ids":p.requested,
            "completed":p.completed,"scientific_acceptance":False},"C03F_DP_REPLAY")
    return {"ACT":act,"DP_MINFXC":dp,"DP_launch":launch,"solver_source":source,
            "comparison":[review_pair(a,b) for a,b in zip(act,dp,strict=True)],
            "decision":"ACT_CANDIDATE_FOR_CLOSED_BULK_MORB_RESEARCH",
            "DP_status":"RESEARCH_ONLY_NO_STABLE_COMPLEX_AMPHIBOLE_OBSERVED",
            "scientific_promotion":False}


def build_plans(parent):
    report,runtime,template,hp,original,derived,options,contract,records=parent
    roster=contract["arms"]["ACT_ONLY"]["solution_models"]
    masses=d.c.b.components(hp)
    plans={}
    inputs={}
    for name in ("C01_MORB_BASE","C01_MORB_WET"):
        basis,chem=d.recipe_basis(report["candidate_cases"],name)
        raw,norm=d.project_input(template,basis,masses,list(d.c.VERTICES))
        text=raw.decode("ascii").replace("C03D noncanonical closed-bulk MORB initialization only",
              "C03F noncanonical closed-bulk MORB candidate "+name)
        text=d.replace_section(text,"begin solution phase list","end solution phase list",roster)
        # Only the audited nonwater PMELT family, NOT reference-paper solid exclusions.
        text=d.replace_section(text,"begin excluded phase list","end excluded phase list",list(r1.LIQUID_IDS))
        raw=text.encode("ascii")
        need(d.fixed_width_readback(raw,norm)==norm and "H2O" in norm and "O2" in norm
             and c.section_rows(text,"saturated component list")==[]
             and c.section_rows(text,"saturated phase component list")==[]
             and c.section_rows(text,"independent potential/fugacity/activity list","independent potential list")==[]
             and c.section_rows(text,"solution phase list")==roster
             and c.section_rows(text,"excluded phase list")==list(r1.LIQUID_IDS),
             "C03F_CLOSED_BULK_SERIALIZATION")
        points=[]
        for case in report["candidate_cases"]:
            if case["source_recipe"]!=name:
                continue
            pt=case["source_point"]
            need(pt["absolute_pressure_pa"] is None
                 and pt["pressure_semantics"]=="HYPOTHETICAL_COMPARATIVE_ONLY"
                 and case["source_chemistry_sha256"]==chem,"C03F_PT_AUTHORITY")
            points.append({"id":case["id"],"T_K":pt["T_K"],
                "P_bar_candidate":pt["conditional_delta_P_kbar"]*1000,
                "source_point":pt})
        need(len(points)==2 and {p["source_point"]["parent_node_id"] for p in points}=={35304,36026},
             "C03F_POINTS")
        inputs[name]={"c03d.dat":raw,"hp02ver.dat":hp,"solution_model.dat":original,
                      "perplex_option.dat":d.options_candidate(options)}
        plans[name]={"source_chemistry_sha256":chem,"basis":basis,"normalized_moles":norm,
                     "points":points,"solution_models":roster,"excluded_phases":list(r1.LIQUID_IDS),
                     "reference_solid_exclusions_reused":False,"H2O_conserved":True,
                     "files_sha256":{k:hgp.sha(v) for k,v in inputs[name].items()}}
    need(plans["C01_MORB_BASE"]["basis"]["native_moles_per_source_recipe"]["H2O"]
         <plans["C01_MORB_WET"]["basis"]["native_moles_per_source_recipe"]["H2O"],"C03F_WATER_ORDER")
    return plans,inputs


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03F_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C03F_OUTPUT_EXISTS")
    parent=c.parent()
    r1.prior.verify_readiness(parent)
    r1.verify_failure(parent)
    report,runtime,template,hp,original,derived,options,contract,records=parent
    policy=r1.liquid_policy(hp,records,original,derived,contract,Path(runtime["source"]))
    review=replay_reference(parent)
    print("C03F_REFERENCE_REPLAY_PASS",PIN,flush=True)
    for row in review["comparison"]:
        print("C03F_REFERENCE_COMPARISON",json.dumps(row,sort_keys=True))
    plans,inputs=build_plans(parent)
    OUT.mkdir(parents=False,exist_ok=False)
    s2.write_json(OUT/"REFERENCE_REVIEW.json",review)
    for name,files in inputs.items():
        work=OUT/name
        work.mkdir()
        for k,v in files.items():
            with (work/k).open("xb") as f:
                f.write(v)
        s2.write_json(work/"INPUT.json",plans[name])
    s2.write_json(OUT/"DESIGN.json",{"plans":plans,"liquid_policy":policy,
         "provider_candidate":review["decision"],"boundary":"CLOSED_BULK_NO_BUFFER_NO_SATURATION",
         "required_next":["native initialization and exact PT prompt audit for changed boundary/roster",
                           "closed H2O and O2 conservation, phase and property readback",
                           "four conditional research points, not absolute regional pressure"],
         "authorized_equilibrium_solver_calls":0,"additional_engine_runs":0,**c.SCOPE})
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03F_CLOSED_BULK_DESIGN_MANIFEST_V1",
         "source_sha":head,"status":STATUS,"C03EE_R2_manifest_sha256":PIN,
         "files":d.launcher.inventory(OUT),"candidate_recipes":2,"candidate_points":4,
         "authorized_equilibrium_solver_calls":0,"additional_engine_runs":0,
         "scientific_promotion":False,**c.SCOPE})
    for name,plan in plans.items():
        print("C03F_PLAN",name,json.dumps(plan,sort_keys=True))
    print("C03F_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
    print(STATUS)
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()
