"""R4: exact audited rejection diagnostics with a total operational budget."""
from __future__ import annotations
import argparse
import json
import re
import shutil
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_r3_native_preflight as r3
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_r2_phase_policy_audit as r2
from experiments.r6_thermo_provider_pilot_v1.run_c03ec_native_preflight import (
    d,s2,hgp,need,SCOPE,dialogue,PIN,FAILED_PIN,LIMITS,EXCLUDED,
    read,parent,audit_failed_attempt,make_project,inspect_native,
)

R2_PIN=r3.R2_PIN
R3_PIN="bef7bc3fcfa8b3b5fa2cfca440b5f37640fae7c2dfd9a43455ea4005386bf6c5"
R3_SOURCE="2618672f35ad7c970d56f4090ff17e9766a640a3"
OUT=s2.BASE/"R6_THERMO_C03EC_NATIVE_PREFLIGHT_NEW04"
STATUS="C03EC_R4_NATIVE_PREFLIGHT_CAPTURED__SCIENTIFIC_REVIEW_REQUIRED"
MAX_EXACT_ACKNOWLEDGEMENTS=32
SPECIES={dialogue.SI013:"Si(s)",r2.H2_WARNING:"H2"}


class PreflightDialogue(dialogue.Dialogue):
    policy="C03EC_R4_EXACT_SI_H2_VER013_TOTAL_BUDGET_ZERO_PT_ONLY"

    def __init__(self):
        super().__init__()
        self.species_counts={"Si(s)":0,"H2":0}

    def next_response(self,raw):
        tail=raw[self.cursor:]
        fatal=re.search(rb"\*\*error ver\d+\*\*[^\n]*|\*\*warning ver(?:017|059|966|968|536)\*\*",tail,re.I)
        need(fatal is None,"C03EC_R4_FORBIDDEN_NATIVE_DIAGNOSTIC:"+repr(fatal.group() if fatal else b""))
        hits=[(tail.find(p),p) for p in dialogue.PROMPTS if p in tail]
        if hits:
            pos,prompt=min(hits,key=lambda x:x[0])
            if prompt==dialogue.WARNING:
                marks=list(re.finditer(rb"\*\*warning ver(\d+)\*\*",tail[:pos],re.I))
                flat=b" ".join(tail[marks[-1].start():pos].split()) if marks else b""
                species=SPECIES.get(flat)
                need(self.state=="INITIALIZING" and species is not None,
                     "C03EC_R4_UNAPPROVED_INTERACTIVE_WARNING:"+repr(flat))
                need(len(self.acknowledged)<MAX_EXACT_ACKNOWLEDGEMENTS,
                     "C03EC_R4_TOTAL_DIAGNOSTIC_BUDGET")
                self.species_counts[species]+=1
                self.cursor+=pos+len(prompt)
                self.acknowledged.append("013")
                self.events.append({"prompt":"HP02_NATIVE_PHASE_REJECTION_VER013","species":species,
                                    "response":"y","occurrence":self.species_counts[species],
                                    "global_occurrence":len(self.acknowledged),
                                    "stdout_byte_offset_after_prompt":self.cursor})
                return b"y\n"
        return super().next_response(raw)


def verify_warning_source(tlib):
    text=tlib.decode("utf-8",errors="strict").lower()
    match=re.search(r"(?m)^\s*subroutine wrnstp\s*$",text)
    need(match is not None,"C03EC_R4_WRNSTP_MISSING")
    body=text[match.end():].split("logical function readyn",1)[0]
    need("continue execution despite this warning (y/n)?" in body
         and "if (lopt(56)) then" in body and "if (.not.readyn()) then" in body
         and "warning ver536" in body and "max_warn_limit" not in body,
         "C03EC_R4_WRNSTP_SOURCE_DRIFT")
    return {"tlib_sha256":hgp.sha(tlib),"interactive_stop_requires_response":True,
            "wrnstp_has_no_max_warn_limit_reference":True,
            "diagnostic_budget":MAX_EXACT_ACKNOWLEDGEMENTS,
            "budget_scope":"OPERATIONAL_NOT_NATIVE_OR_SCIENTIFIC_LIMIT"}


def verify_r3_failure():
    rec=read(d.m.HERE/"c03ec_r3_failed_fair_receipt_v1.json")
    failed=r3.OUT
    need(failed.is_dir() and not failed.is_symlink()
         and not (failed/"MANIFEST.json").is_symlink()
         and hgp.file_sha(failed/"MANIFEST.json")==R3_PIN==rec["manifest_sha256"],
         "C03EC_R4_R3_PIN")
    man=read(failed/"MANIFEST.json")
    inv=d.launcher.inventory(failed)
    inv.pop("MANIFEST.json")
    need(inv==man["files"] and man["source_sha"]==R3_SOURCE==rec["source_sha"]
         and man["schema"]=="R6_C03EC_R3_NATIVE_PREFLIGHT_MANIFEST_V1"
         and man["status"]=="NATIVE_PREFLIGHT_FAILED_PRESERVED"
         and man["failed_manifest_sha256"]==FAILED_PIN
         and man["r1_failed_manifest_sha256"]==r2.PIN
         and man["r2_audit_manifest_sha256"]==R2_PIN
         and man["C03EB_manifest_sha256"]==PIN
         and man["native_initialization_attempts"]==1
         and man["requested_equilibrium_points"]==man["authorized_equilibrium_solver_calls"]==0
         and man["scientific_promotion"] is False
         and all(man[k]==v for k,v in SCOPE.items()),"C03EC_R4_R3_MANIFEST")
    work=failed/"ACT_ONLY"
    raw=(work/"RUN_STDOUT.log").read_bytes()
    stdin=(work/"DIALOGUE_STDIN.log").read_bytes()
    failure=read(failed/"FAILURE.json")
    dia=read(work/"DIALOGUE.json")
    launch=read(work/"LAUNCH.json")
    expected="C03EC_R3_REPEAT_LIMIT:Si(s)"
    need(failure["error"]=="ValueError" and failure["message"]==expected
         and failure["native_initialization_attempts"]==1
         and failure["requested_equilibrium_points"]==0
         and dia["error"]==launch["error"]=="ValueError: "+expected
         and dia["state"]=="INITIALIZING" and dia["acknowledged_warning_codes"]==["013"]*3
         and [e["species"] for e in dia["events"] if "species" in e]==["Si(s)","Si(s)","H2"]
         and dia["requested_equilibrium_points"]==0
         and dia["scientific_warning_acceptance"] is False
         and stdin==b"c03d\ny\ny\ny\n" and raw.count(dialogue.WARNING)==4
         and dialogue.PT not in raw and not (failed/"DP_DS5_ONLY").exists(),
         "C03EC_R4_R3_DIALOGUE")
    for name in ("c03d.dat","hp02ver.dat","solution_model.dat","perplex_option.dat","INPUT.json"):
        need((r2.FAILED/"ACT_ONLY"/name).read_bytes()==(work/name).read_bytes(),
             "C03EC_R4_R3_INPUT_DRIFT:"+name)
    p=r3.PreflightDialogue()
    need([p.next_response(raw) for _ in range(4)]==[b"c03d\n",b"y\n",b"y\n",b"y\n"],
         "C03EC_R4_R3_OLD_PREFIX")
    try:
        p.next_response(raw)
    except ValueError as exc:
        need(str(exc)==expected,"C03EC_R4_R3_OLD_FAILURE")
    else:
        raise ValueError("C03EC_R4_R3_OLD_FAILURE_MISSING")
    q=PreflightDialogue()
    need([q.next_response(raw) for _ in range(6)]==[b"c03d\n",b"y\n",b"y\n",b"y\n",b"y\n",None]
         and q.state=="INITIALIZING" and q.species_counts=={"Si(s)":3,"H2":1},
         "C03EC_R4_R3_CANDIDATE_REPLAY")
    return {"manifest_sha256":R3_PIN,"source_sha":R3_SOURCE,"exact_old_failure_replay":True,
            "candidate_replay_species":q.species_counts,"requested_equilibrium_points":0}


def verify_readback(raw,stdin,result):
    dia=result["dialogue"]
    species=result["acknowledged_species"]
    need(all(k in ("Si(s)","H2") for k in species)
         and len(species)<=MAX_EXACT_ACKNOWLEDGEMENTS
         and result["warning_codes"].count("013")==len(species)
         and raw.count(dialogue.WARNING)==len(species)
         and dia["acknowledged_warning_codes"]==["013"]*len(species)
         and dia["state"]=="SENTINEL_SENT"
         and dia["scientific_warning_acceptance"] is False
         and stdin==b"c03d\n"+b"y\n"*len(species)+b"n\n0 0\n",
         "C03EC_R4_DIALOGUE_RECONCILIATION")
    p=PreflightDialogue()
    responses=[]
    while True:
        response=p.next_response(raw)
        if response is None:
            break
        responses.append(response)
    need(b"".join(responses)==stdin and p.events==dia["events"]
         and p.state=="SENTINEL_SENT","C03EC_R4_COMPLETE_DIALOGUE_REPLAY")


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
    print("C03EC_R4_ALL_EVIDENCE_REPLAY_PASS",R2_PIN,R3_PIN,flush=True)
    masses=d.c.b.components(hp)
    need(all(k in records for k in EXCLUDED),"C03EC_EXCLUSION_IDS")
    source=Path(runtime["source"])
    tlib=(source/"src/tlib.f").read_bytes()
    need(b"if (ifct.gt.0) call rfluid (0,jc)" in tlib
         and b"if (name.eq.exname(i)) goto 90" in tlib,"C03EC_NATIVE_SOURCE_CONTRACT")
    warning_source=verify_warning_source(tlib)
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
            "r3_failed_attempt":r3_failure,"warning_source":warning_source,
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
            print("C03EC_R4_ACKNOWLEDGED_SPECIES",arm,json.dumps(result["acknowledged_species"]),flush=True)
            need(result["dialogue"]["requested_equilibrium_points"]==0
                 and (work/"DIALOGUE_STDIN.log").read_bytes().endswith(b"0 0\n"),"C03EC_SENTINEL")
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
        s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03EC_R4_NATIVE_PREFLIGHT_MANIFEST_V1",
            "status":state,"source_sha":head,"C03EB_manifest_sha256":PIN,"files":members,
            "failed_manifest_sha256":FAILED_PIN,"r1_failed_manifest_sha256":r2.PIN,
            "r2_audit_manifest_sha256":R2_PIN,"r3_failed_manifest_sha256":R3_PIN,
            "max_exact_diagnostic_acknowledgements":MAX_EXACT_ACKNOWLEDGEMENTS,
            "native_initialization_attempts":attempts,"requested_equilibrium_points":0,
            "authorized_equilibrium_solver_calls":0,"scientific_promotion":False,**SCOPE})
        print("C03EC_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"),flush=True)
    print(state)
    print("NATIVE_INITIALIZATION_ATTEMPTS="+str(attempts))
    print("REQUESTED_EQUILIBRIUM_POINTS=0")


if __name__=="__main__":
    main()
