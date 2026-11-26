"""R3 native preflight: audited bounded Si(s)/H2 rejection; no equilibrium calls."""
from __future__ import annotations
import argparse
import json
import re
import shutil
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_native_preflight as c
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_r2_phase_policy_audit as r2
from experiments.r6_thermo_provider_pilot_v1.run_c03ec_native_preflight import (
    d, s2, hgp, need, SCOPE, dialogue, PIN, FAILED_PIN, LIMITS, ORDER, EXCLUDED,
    MAX_SI013_ACKNOWLEDGEMENTS, read, parent, audit_failed_attempt, make_project, inspect_native,
)

R2_PIN="4ff258a5021fe07c3bd6ebd663f91c925c4c402b214341eab9550deb76bf67bb"
R2_SOURCE="2a57d2282cd6e49b934cdfbde67a2e8e03c2ab17"
OUT=s2.BASE/"R6_THERMO_C03EC_NATIVE_PREFLIGHT_NEW03"
STATUS="C03EC_R3_NATIVE_PREFLIGHT_CAPTURED__SCIENTIFIC_REVIEW_REQUIRED"
MAX_H2_ACKNOWLEDGEMENTS=1


class PreflightDialogue(dialogue.Dialogue):
    policy="C03EC_R3_EXACT_SI013_MAX_TWO_H2_MAX_ONE_ZERO_PT_ONLY"

    def __init__(self):
        super().__init__()
        self.species_counts={"Si(s)":0,"H2":0}

    def next_response(self,raw):
        tail=raw[self.cursor:]
        fatal=re.search(rb"\*\*error ver\d+\*\*[^\n]*|\*\*warning ver(?:017|059|966|968)\*\*",tail,re.I)
        need(fatal is None,"C03EC_R3_FORBIDDEN_NATIVE_DIAGNOSTIC:"+repr(fatal.group() if fatal else b""))
        hits=[(tail.find(p),p) for p in dialogue.PROMPTS if p in tail]
        if hits:
            pos,prompt=min(hits,key=lambda x:x[0])
            if prompt==dialogue.WARNING:
                marks=list(re.finditer(rb"\*\*warning ver(\d+)\*\*",tail[:pos],re.I))
                flat=b" ".join(tail[marks[-1].start():pos].split()) if marks else b""
                species={dialogue.SI013:"Si(s)",r2.H2_WARNING:"H2"}.get(flat)
                need(self.state=="INITIALIZING" and species is not None,
                     "C03EC_R3_UNAPPROVED_INTERACTIVE_WARNING:"+repr(flat))
                limit=MAX_SI013_ACKNOWLEDGEMENTS if species=="Si(s)" else MAX_H2_ACKNOWLEDGEMENTS
                need(self.species_counts[species]<limit,"C03EC_R3_REPEAT_LIMIT:"+species)
                self.species_counts[species]+=1
                self.cursor+=pos+len(prompt)
                self.acknowledged.append("013")
                self.events.append({"prompt":"HP02_NATIVE_PHASE_REJECTION_VER013","species":species,
                                    "response":"y","occurrence":self.species_counts[species],
                                    "stdout_byte_offset_after_prompt":self.cursor})
                return b"y\n"
        return super().next_response(raw)


def verify_r2(runtime,hp,records):
    rec=read(d.m.HERE/"c03ec_r2_fair_receipt_v1.json")
    man=d.m.archive_manifest(r2.OUT,R2_PIN,"files_sha256")
    need(man["schema"]=="R6_C03EC_R2_STATIC_PHASE_POLICY_AUDIT_MANIFEST_V1"
         and man["source_sha"]==rec["source_sha"]==R2_SOURCE
         and rec["manifest_sha256"]==R2_PIN and rec["exit"]==0
         and man["status"]==r2.STATUS==rec["status"]
         and man["R1_failed_manifest_sha256"]==r2.PIN
         and man["C03EB_manifest_sha256"]==PIN
         and man["additional_engine_runs"]==man["authorized_equilibrium_solver_calls"]==0
         and man["scientific_promotion"] is False
         and set(man["files_sha256"])=={"PHASE_POLICY_AUDIT.json"}
         and all(man[k]==v for k,v in SCOPE.items()),"C03EC_R3_R2_MANIFEST")
    payload=read(r2.OUT/"PHASE_POLICY_AUDIT.json")
    active=d.composition_audit.active_text(hp.decode())
    makes=r2.a.equations(r2.a.section(active,"makes"))
    rows,unresolved=r2.inventory_vectors(records,makes)
    candidates=sorted(k for k,v in rows.items() if not v["outside_basis"]
                      and v["nonpositive_conserved_sum"])
    need(len(records)==198 and len(makes)==89 and len(unresolved)==27
         and candidates==["H2","H2O","Si(s)","h2oGL","h2oL","wL_q"]
         and payload["direct_and_make_vectors"]==rows
         and payload["unresolved_make_equations"]==unresolved
         and payload["nonpositive_conserved_sum_candidates"]==candidates
         and payload["provider_runtime"]==runtime
         and payload["conserved"]==list(ORDER) and payload["saturated"]==["H2O"]
         and payload["explicit_exclusions"]==list(EXCLUDED)
         and payload["phase_policy_authorized"] is False
         and payload["scientific_promotion"] is False
         and payload["additional_engine_runs"]==payload["authorized_equilibrium_solver_calls"]==0,
         "C03EC_R3_R2_PAYLOAD")
    need(rows["H2"]["coefficients"]=={"H2O":"1","O2":"-1/2"}
         and rows["H2"]["conserved_sum"]=="-1/2" and rows["H2"]["eos"]==105
         and rows["Si(s)"]["conserved_sum"]=="0"
         and all(not v["model_hits"][k] for v in payload["model_literal_reference_hits"].values()
                 for k in ("Si(s)","H2"))
         and all(not payload["make_literal_reference_hits"][k] for k in ("Si(s)","H2")),
         "C03EC_R3_SPECIES_AUDIT")
    excerpts=r2.source_context(Path(runtime["source"]))
    need(excerpts==payload["native_source_context"],"C03EC_R3_NATIVE_SOURCE_REPLAY")
    tlib=(Path(runtime["source"])/"src/tlib.f").read_bytes()
    need(b"if (tot.lt.0d0.and.ichk.eq.1.and.lopt(60)) then" in tlib
         and b"reject phases such as H2" in tlib,"C03EC_R3_H2_REJECTION_SOURCE")
    raw=(r2.FAILED/"ACT_ONLY"/"RUN_STDOUT.log").read_bytes()
    p=PreflightDialogue()
    need([p.next_response(raw) for _ in range(5)]==[b"c03d\n",b"y\n",b"y\n",b"y\n",None]
         and p.species_counts=={"Si(s)":2,"H2":1}
         and p.state=="INITIALIZING","C03EC_R3_R1_CANDIDATE_REPLAY")
    return {"manifest_sha256":R2_PIN,"projected_candidates":candidates,
            "unresolved_make_count":len(unresolved),"candidate_replay_species":p.species_counts,
            "scientific_phase_policy_authorized":False,
            "scope":"EXACT_OBSERVED_DIAGNOSTICS_ONLY_NO_EQUILIBRIUM"}


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
    audit=verify_r2(runtime,hp,records)
    print("C03EC_R3_R2_EVIDENCE_REPLAY_PASS",R2_PIN,flush=True)
    masses=d.c.b.components(hp)
    need(all(k in records for k in EXCLUDED),"C03EC_EXCLUSION_IDS")
    source=Path(runtime["source"])
    tlib=(source/"src/tlib.f").read_bytes()
    need(b"if (ifct.gt.0) call rfluid (0,jc)" in tlib
         and b"if (name.eq.exname(i)) goto 90" in tlib,"C03EC_NATIVE_SOURCE_CONTRACT")
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
            "max_h2_acknowledgements":MAX_H2_ACKNOWLEDGEMENTS,
            "max_si013_acknowledgements":MAX_SI013_ACKNOWLEDGEMENTS,"requested_equilibrium_points":0,
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
            need(result["warning_codes"].count("013")==len(result["acknowledged_species"]),
                 "C03EC_R3_UNRECONCILED_VER013")
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
        s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03EC_R3_NATIVE_PREFLIGHT_MANIFEST_V1",
            "status":state,"source_sha":head,"C03EB_manifest_sha256":PIN,"files":members,
            "failed_manifest_sha256":FAILED_PIN,"r1_failed_manifest_sha256":r2.PIN,
            "r2_audit_manifest_sha256":R2_PIN,"max_h2_acknowledgements":MAX_H2_ACKNOWLEDGEMENTS,
            "max_si013_acknowledgements":MAX_SI013_ACKNOWLEDGEMENTS,
            "native_initialization_attempts":attempts,"requested_equilibrium_points":0,
            "authorized_equilibrium_solver_calls":0,"scientific_promotion":False,**SCOPE})
        print("C03EC_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"),flush=True)
    print(state)
    print("NATIVE_INITIALIZATION_ATTEMPTS="+str(attempts))
    print("REQUESTED_EQUILIBRIUM_POINTS=0")


if __name__=="__main__":
    main()
