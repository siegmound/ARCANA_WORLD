"""R5: bind the full saturated-water potential prompt and zero sentinel."""
from __future__ import annotations
import argparse
import json
import re
import shutil
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_r4_native_preflight as r4
from experiments.r6_thermo_provider_pilot_v1.run_c03ec_r4_native_preflight import (
    r2,r3,d,s2,hgp,need,SCOPE,dialogue,PIN,FAILED_PIN,LIMITS,ORDER,EXCLUDED,
    R2_PIN,R3_PIN,MAX_EXACT_ACKNOWLEDGEMENTS,read,parent,audit_failed_attempt,
    make_project,inspect_native,verify_r3_failure,verify_warning_source,
)

R4_PIN="a4c3ba1456ce785082540d6fe7a82d3567f10b9262e493335fa508d2313258c1"
R4_SOURCE="73ec27266e75744f55b8f8b870a46a7a0d39e0f0"
OUT=s2.BASE/"R6_THERMO_C03EC_NATIVE_PREFLIGHT_NEW05"
STATUS="C03EC_R5_NATIVE_PREFLIGHT_CAPTURED__SCIENTIFIC_REVIEW_REQUIRED"
PT_FIELDS=("T(K)","P(bar)","Y(CO2)")
SENTINEL=b"0 0 0\n"


class PreflightDialogue(r4.PreflightDialogue):
    policy="C03EC_R5_EXACT_REJECTION_BUDGET_FULL_THREE_FIELD_ZERO_SENTINEL"

    def next_response(self,raw):
        tail=raw[self.cursor:]
        fatal=re.search(rb"\*\*error ver\d+\*\*[^\n]*|\*\*warning ver(?:017|059|966|968|536)\*\*",tail,re.I)
        need(fatal is None,"C03EC_R5_FORBIDDEN_NATIVE_DIAGNOSTIC:"+repr(fatal.group() if fatal else b""))
        hits=[(tail.find(p),p) for p in dialogue.PROMPTS if p in tail]
        if hits:
            pos,prompt=min(hits,key=lambda x:x[0])
            if prompt==dialogue.PT:
                end=tail.find(b"\n",pos)
                if end<0:
                    return None
                fields=tuple(tail[pos+len(prompt):end].decode("ascii").split())
                need(self.state=="AWAIT_PT","C03EC_R5_UNEXPECTED_PT_STATE:"+self.state)
                need(fields==PT_FIELDS,"C03EC_R5_UNEXPECTED_POTENTIAL_FIELDS:"+repr(fields))
                self.cursor+=end+1
                self.state="SENTINEL_SENT"
                self.events.append({"prompt":"ZERO_PT_SENTINEL","response":SENTINEL.decode().strip(),
                                    "potential_fields":list(fields),
                                    "stdout_byte_offset_after_prompt":self.cursor})
                return SENTINEL
        return super().next_response(raw)


def verify_sentinel_source(raw):
    text=raw.decode("utf-8").lower()
    terms=("write (*,1070) (vname(jv(i)), i = 1, ipot)",
           "read (*,*,iostat=ier) (v(jv(i)), i = 1, ipot)",
           "if (ier.ne.0) cycle","if (v(1).eq.0d0) exit","call meemum (bad)")
    positions=[text.find(term) for term in terms]
    need(all(i>=0 for i in positions) and positions==sorted(set(positions))
         and "enter (t = 0 to quit)" in text,"C03EC_R5_SENTINEL_SOURCE_DRIFT")
    return {"meemum_sha256":hgp.sha(raw),"prompt_fields":list(PT_FIELDS),
            "sentinel":SENTINEL.decode().strip(),"read_all_potentials_before_zero_pressure_exit":True,
            "equilibrium_call_after_exit_guard":True,"fluid_semantics_qualified":False}


def verify_r4_failure():
    rec=read(d.m.HERE/"c03ec_r4_failed_fair_receipt_v1.json")
    failed=r4.OUT
    need(failed.is_dir() and not failed.is_symlink()
         and not (failed/"MANIFEST.json").is_symlink()
         and hgp.file_sha(failed/"MANIFEST.json")==R4_PIN==rec["manifest_sha256"],
         "C03EC_R5_R4_PIN")
    man=read(failed/"MANIFEST.json")
    inv=d.launcher.inventory(failed)
    inv.pop("MANIFEST.json")
    need(inv==man["files"] and man["source_sha"]==R4_SOURCE==rec["source_sha"]
         and man["schema"]=="R6_C03EC_R4_NATIVE_PREFLIGHT_MANIFEST_V1"
         and man["status"]=="NATIVE_PREFLIGHT_FAILED_PRESERVED"
         and man["failed_manifest_sha256"]==FAILED_PIN
         and man["r1_failed_manifest_sha256"]==r2.PIN
         and man["r2_audit_manifest_sha256"]==R2_PIN
         and man["r3_failed_manifest_sha256"]==R3_PIN
         and man["C03EB_manifest_sha256"]==PIN
         and man["native_initialization_attempts"]==1
         and man["requested_equilibrium_points"]==man["authorized_equilibrium_solver_calls"]==0
         and man["scientific_promotion"] is False
         and all(man[k]==v for k,v in SCOPE.items()),"C03EC_R5_R4_MANIFEST")
    work=failed/"ACT_ONLY"
    raw=(work/"RUN_STDOUT.log").read_bytes()
    stdin=(work/"DIALOGUE_STDIN.log").read_bytes()
    failure=read(failed/"FAILURE.json")
    dia=read(work/"DIALOGUE.json")
    launch=read(work/"LAUNCH.json")
    expected="C03D_UNEXPECTED_PROMPT:SENTINEL_SENT:"+dialogue.PT.decode()
    species=[e["species"] for e in dia["events"] if "species" in e]
    need(failure["error"]=="ValueError" and failure["message"]==expected
         and failure["native_initialization_attempts"]==1
         and failure["requested_equilibrium_points"]==0
         and dia["error"]==launch["error"]=="ValueError: "+expected
         and dia["state"]=="SENTINEL_SENT" and dia["requested_equilibrium_points"]==0
         and dia["scientific_warning_acceptance"] is False
         and dia["acknowledged_warning_codes"]==["013"]*len(species)
         and stdin==b"c03d\n"+b"y\n"*len(species)+b"n\n0 0\n"
         and raw.count(dialogue.PT)>=2 and not (failed/"DP_DS5_ONLY").exists(),
         "C03EC_R5_R4_DIALOGUE")
    for name in ("c03d.dat","hp02ver.dat","solution_model.dat","perplex_option.dat","INPUT.json"):
        need((r3.OUT/"ACT_ONLY"/name).read_bytes()==(work/name).read_bytes(),
             "C03EC_R5_R4_INPUT_DRIFT:"+name)
    first=raw.index(dialogue.PT)
    end=raw.index(b"\n",first)+1
    prefix=raw[:end]
    p=r4.PreflightDialogue()
    old_responses=[]
    while True:
        response=p.next_response(prefix)
        if response is None:
            break
        old_responses.append(response)
    # R4 captured its event cursor at the prompt prefix, not the entire line.
    need(b"".join(old_responses)==stdin and p.events==dia["events"],
         "C03EC_R5_R4_OLD_PREFIX")
    try:
        p.next_response(raw)
    except ValueError as exc:
        need(str(exc)==expected,"C03EC_R5_R4_OLD_FAILURE")
    else:
        raise ValueError("C03EC_R5_R4_OLD_FAILURE_MISSING")
    q=PreflightDialogue()
    new_responses=[]
    while True:
        response=q.next_response(prefix)
        if response is None:
            break
        new_responses.append(response)
    need(b"".join(new_responses)==stdin[:-len(b"0 0\n")]+SENTINEL
         and q.state=="SENTINEL_SENT" and q.events[-1]["potential_fields"]==list(PT_FIELDS),
         "C03EC_R5_R4_CANDIDATE_REPLAY")
    roster=read(work/"INPUT.json")["solution_models"]
    prn=work/"c03d.prn"
    observed=d.observe(raw,prn.read_bytes() if prn.is_file() else b"",roster)
    need(set(observed["native_model_dispositions"]["included"])==set(roster)
         and len(roster)==17 and not observed["unaccounted_requested_models"]
         and re.search(rb"Total number of pseudocompounds:\s+1123\b",raw) is not None,
         "C03EC_R5_R4_ROSTER_EVIDENCE")
    return {"manifest_sha256":R4_PIN,"source_sha":R4_SOURCE,
            "old_failure_replay":True,"candidate_prefix_replay":True,
            "archived_species":species,"included_models":17,"pseudocompounds":1123,
            "potential_fields":list(PT_FIELDS),"requested_equilibrium_points":0}


def verify_readback(raw,stdin,result):
    dia=result["dialogue"]
    species=result["acknowledged_species"]
    need(all(k in ("Si(s)","H2") for k in species)
         and len(species)<=MAX_EXACT_ACKNOWLEDGEMENTS
         and result["warning_codes"].count("013")==len(species)
         and raw.count(dialogue.WARNING)==len(species) and raw.count(dialogue.PT)==1
         and dia["acknowledged_warning_codes"]==["013"]*len(species)
         and dia["state"]=="SENTINEL_SENT" and dia["scientific_warning_acceptance"] is False
         and stdin==b"c03d\n"+b"y\n"*len(species)+b"n\n"+SENTINEL,
         "C03EC_R5_DIALOGUE_RECONCILIATION")
    p=PreflightDialogue()
    responses=[]
    while True:
        response=p.next_response(raw)
        if response is None:
            break
        responses.append(response)
    need(b"".join(responses)==stdin and p.events==dia["events"]
         and p.state=="SENTINEL_SENT","C03EC_R5_COMPLETE_DIALOGUE_REPLAY")
    result["native_potential_fields"]=list(PT_FIELDS)
    result["fluid_semantics_qualified"]=False


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    ap.add_argument("--native-preflight-only",action="store_true",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03EC_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C03EC_OUTPUT_EXISTS")
    failed_attempt=audit_failed_attempt()
    r1_attempt=r2.verify_r1_failure()
    report,runtime,template,hp,original,derived,options,contract,records=parent()
    audit=r3.verify_r2(runtime,hp,records)
    r3_failure=verify_r3_failure()
    r4_failure=verify_r4_failure()
    print("C03EC_R5_ALL_EVIDENCE_REPLAY_PASS",R2_PIN,R3_PIN,R4_PIN,flush=True)
    masses=d.c.b.components(hp)
    need(all(k in records for k in EXCLUDED),"C03EC_EXCLUSION_IDS")
    source=Path(runtime["source"])
    tlib=(source/"src/tlib.f").read_bytes()
    need(b"if (ifct.gt.0) call rfluid (0,jc)" in tlib
         and b"if (name.eq.exname(i)) goto 90" in tlib,"C03EC_NATIVE_SOURCE_CONTRACT")
    warning_source=verify_warning_source(tlib)
    sentinel_source=verify_sentinel_source((source/"src/meemum.f").read_bytes())
    plans={arm:make_project(template,report,masses,contract,arm) for arm in contract["arms"]}
    print("C03EC_PARENT_REPLAY_PASS",PIN,flush=True)
    need(shutil.disk_usage(s2.BASE).free>=LIMITS["retained_bytes_stop_threshold"],"C03EC_DISK")
    OUT.mkdir(parents=False,exist_ok=False)
    attempts=0
    state="NATIVE_PREFLIGHT_FAILED_PRESERVED"
    results={}
    try:
        s2.write_json(OUT/"PROVENANCE.json",{"source_sha":head,"C03EB_manifest_sha256":PIN,
            "runtime":runtime,"limits":LIMITS,"excluded_species_candidate":list(EXCLUDED),
            "water_boundary":"PURE_WATER_SATURATED_PHASE","O2_component_retained":True,
            "native_policy":PreflightDialogue.policy,"failed_attempt":failed_attempt,
            "r1_failed_attempt":r1_attempt,"phase_policy_audit":audit,
            "r3_failed_attempt":r3_failure,"r4_failed_attempt":r4_failure,
            "warning_source":warning_source,"sentinel_source":sentinel_source,
            "max_exact_diagnostic_acknowledgements":MAX_EXACT_ACKNOWLEDGEMENTS,"requested_equilibrium_points":0,
            "scientific_warning_acceptance":False,**SCOPE})
        for arm,(project,norm) in plans.items():
            work=OUT/arm
            work.mkdir()
            lib=original if contract["arms"][arm]["library"]=="ORIGINAL" else derived
            files={"c03d.dat":project,"hp02ver.dat":hp,"solution_model.dat":lib,
                   "perplex_option.dat":d.options_candidate(options)}
            for k,v in files.items():
                with (work/k).open("xb") as f:
                    f.write(v)
            roster=contract["arms"][arm]["solution_models"]
            s2.write_json(work/"INPUT.json",{"normalized_conserved_moles":norm,
                "saturated_phase_components":["H2O"],"excluded_phases":list(EXCLUDED),
                "solution_models":roster,"files_sha256":{k:hgp.sha(v) for k,v in files.items()},
                "requested_equilibrium_points":0})
            need(d.launcher.retained_bytes(OUT)<LIMITS["retained_bytes_stop_threshold"]
                and hgp.file_sha(runtime["binary"])==runtime["binary_sha256"],"C03EC_LAUNCH_GUARD")
            attempts+=1
            try:
                dialogue.launch_dialogue([Path(runtime["binary"])],work,LIMITS,
                                        protocol_factory=PreflightDialogue)
            finally:
                if (work/"RUN_STDOUT.log").is_file():
                    print("C03EC_NATIVE_LOG_TAIL",arm,(work/"RUN_STDOUT.log").read_bytes()[-8000:].decode("utf-8",errors="replace"),flush=True)
            raw=(work/"RUN_STDOUT.log").read_bytes()
            prn=work/"c03d.prn"
            result=inspect_native(raw,prn.read_bytes() if prn.is_file() else b"",roster,records)
            result["dialogue"]=read(work/"DIALOGUE.json")
            result["acknowledged_species"]=[e["species"] for e in result["dialogue"]["events"] if "species" in e]
            verify_readback(raw,(work/"DIALOGUE_STDIN.log").read_bytes(),result)
            print("C03EC_R5_ACKNOWLEDGED_SPECIES",arm,json.dumps(result["acknowledged_species"]),flush=True)
            need(result["dialogue"]["requested_equilibrium_points"]==0
                 and (work/"DIALOGUE_STDIN.log").read_bytes().endswith(SENTINEL),"C03EC_SENTINEL")
            s2.write_json(work/"READBACK.json",result)
            results[arm]=result
            print("C03EC_NATIVE_READBACK",arm,json.dumps({"checks":result["checks"],
                  "warnings":result["warning_codes"],"pseudocompounds":result["pseudocompound_sum"],
                  "headers":result["native_print_headers"],"missing":result["native_model_details"]["missing_endmember_reports"]},sort_keys=True),flush=True)
            need(d.launcher.retained_bytes(OUT)<LIMITS["retained_bytes_stop_threshold"],"C03EC_RETAINED_STOP")
        s2.write_json(OUT/"RESULT.json",{"observations":results,"requested_equilibrium_points":0,
            "native_initialization_attempts":attempts,"campaign_authorized":False,**SCOPE})
        state=STATUS
    except BaseException as exc:
        s2.write_json(OUT/"FAILURE.json",{"error":type(exc).__name__,"message":str(exc),
            "native_initialization_attempts":attempts,"requested_equilibrium_points":0})
        raise
    finally:
        members=d.launcher.inventory(OUT)
        s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03EC_R5_NATIVE_PREFLIGHT_MANIFEST_V1",
            "status":state,"source_sha":head,"C03EB_manifest_sha256":PIN,"files":members,
            "failed_manifest_sha256":FAILED_PIN,"r1_failed_manifest_sha256":r2.PIN,
            "r2_audit_manifest_sha256":R2_PIN,"r3_failed_manifest_sha256":R3_PIN,
            "r4_failed_manifest_sha256":R4_PIN,"sentinel_fields":list(PT_FIELDS),
            "max_exact_diagnostic_acknowledgements":MAX_EXACT_ACKNOWLEDGEMENTS,
            "native_initialization_attempts":attempts,"requested_equilibrium_points":0,
            "authorized_equilibrium_solver_calls":0,"scientific_promotion":False,**SCOPE})
        print("C03EC_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"),flush=True)
    print(state)
    print("NATIVE_INITIALIZATION_ATTEMPTS="+str(attempts))
    print("REQUESTED_EQUILIBRIUM_POINTS=0")


if __name__=="__main__":
    main()
