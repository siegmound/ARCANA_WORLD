"""C03E-C native saturated-water comparison preflight, zero PT only.
Two sequential fresh native processes at most. No equilibrium authority.
"""
from __future__ import annotations
import argparse
import json
import re
import shutil
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03eb_benchmark_contract as b

d=b.d
s2=b.s2
hgp=b.hgp
need=b.need
SCOPE=b.SCOPE
dialogue=d.dialogue
PIN="8d48410dbcd2c2057016d07198aa0c369ccbe4dbf10da387ecca0f09428673cb"
PARENT="67e2a73a9f5e1232a0e07cd225fd1fdef774b9d1"
OUT=s2.BASE/"R6_THERMO_C03EC_NATIVE_PREFLIGHT_NEW01"
LIMITS=d.LIMITS
ORDER=tuple(k for k in d.ORDER if k!="H2O")
EXCLUDED=tuple(b.EXCLUSIONS.values())+("O2",)
STATUS="C03EC_NATIVE_PREFLIGHT_CAPTURED__SCIENTIFIC_REVIEW_REQUIRED"


class PreflightDialogue(dialogue.Dialogue):
    policy="C03EC_SATURATED_WATER_O2_SPECIES_EXCLUDED_ZERO_PT_ONLY"

    def __init__(self):
        super().__init__()

    def next_response(self,raw):
        tail=raw[self.cursor:]
        # Inspect newly observed text before responding to any prompt.
        fatal=re.search(rb"\*\*error ver\d+\*\*[^\n]*|\*\*warning ver(?:017|059|966|968)\*\*",tail,re.I)
        need(fatal is None,"C03EC_FORBIDDEN_NATIVE_DIAGNOSTIC:"+repr(fatal.group() if fatal else b""))
        hits=[(tail.find(p),p) for p in dialogue.PROMPTS if p in tail]
        if hits:
            pos,prompt=min(hits,key=lambda x:x[0])
            if prompt==dialogue.WARNING:
                marks=list(re.finditer(rb"\*\*warning ver(\d+)\*\*",tail[:pos],re.I))
                flat=b" ".join(tail[marks[-1].start():pos].split()) if marks else b""
                need(self.state=="INITIALIZING" and not self.acknowledged and flat==dialogue.SI013,
                     "C03EC_UNAPPROVED_INTERACTIVE_WARNING:"+repr(flat))
                self.cursor+=pos+len(prompt)
                self.acknowledged.append("013")
                self.events.append({"prompt":"HP02_SI_REJECTION_VER013","response":"y",
                                    "stdout_byte_offset_after_prompt":self.cursor})
                return b"y\n"
        return super().next_response(raw)


def read(path):
    return json.loads(path.read_text())


def parent():
    rec=read(d.m.HERE/"c03eb_fair_receipt_v1.json")
    man=d.m.archive_manifest(b.OUT,PIN,"files_sha256")
    need(man["schema"]=="R6_C03EB_BENCHMARK_CONTRACT_MANIFEST_V1"
         and man["source_sha"]==rec["source_sha"]==PARENT
         and rec["manifest_sha256"]==PIN and rec["exit"]==0
         and man["status"]==b.STATUS and man["C03EA_manifest_sha256"]==b.PIN
         and man["additional_engine_runs"]==man["authorized_equilibrium_solver_calls"]==0
         and man["scientific_promotion"] is False
         and set(man["files_sha256"])=={"BENCHMARK_CONTRACT.json","solution_model_DP_DS5_candidate.dat"}
         and all(man[k]==v for k,v in SCOPE.items()),"C03EC_PARENT_MANIFEST")
    prev=read(b.OUT/"BENCHMARK_CONTRACT.json")
    original,masses,records=b.parent()
    derived,change=b.derive_models(original)
    contract=b.benchmark_contract(masses,records)
    need(prev["benchmark"]==contract and prev["candidate_derivation"]==change
         and prev["status"]==b.STATUS and prev["C03EA_manifest_sha256"]==b.PIN
         and prev["scientific_promotion"] is False
         and prev["additional_engine_runs"]==prev["authorized_equilibrium_solver_calls"]==0
         and all(prev[k]==v for k,v in SCOPE.items())
         and derived==(b.OUT/"solution_model_DP_DS5_candidate.dat").read_bytes()
         and hgp.sha(derived)==rec["derived_library_sha256"]
         and hgp.sha(original)==rec["original_library_sha256"],"C03EC_PARENT_REPLAY")
    report,runtime,template,hp,models,options=d.audit_parent()
    need(models==original,"C03EC_SOURCE_LIBRARY_DRIFT")
    return report,runtime,template,hp,original,derived,options,contract,records


def section_rows(text,name,end=None):
    start="begin "+name
    stop="end "+(end or name)
    need(text.count(start+"\n")==text.count("\n"+stop+"\n")==1,"C03EC_SECTION:"+name)
    return [x for x in text.split(start+"\n",1)[1].split("\n"+stop+"\n",1)[0].splitlines() if x.strip()]


def make_project(template,report,masses,contract,arm):
    # Reuse the already FAIR-verified C03D project serializer as template.
    basis,_=d.recipe_basis(report["candidate_cases"],"C01_MORB_BASE")
    raw,_=d.project_input(template,basis,masses,list(d.c.VERTICES))
    text=raw.decode("ascii").replace("C03D noncanonical closed-bulk MORB initialization only",
                                    "C03EC nonexact saturated water MORB preflight "+arm)
    mol={k:float(v) for k,v in contract["redox"]["primary_moles"].items()}
    need(set(mol)==set(ORDER) and all(d.m.finite(v) and v>0 for v in mol.values()),"C03EC_DRY_MOLES")
    total=sum(mol.values())
    norm={k:100*mol[k]/total for k in ORDER}
    roster=contract["arms"][arm]["solution_models"]
    need(len(roster)==len(set(roster))==17 and "GlTrTsPg" not in roster
         and (("Act(M)" in roster) != (b.DP in roster)),"C03EC_ROSTER")
    for name,end,rows in (
        ("thermodynamic component list",None,[d.component_row(k,norm[k]) for k in ORDER]),
        ("saturated component list",None,[]),
        ("saturated phase component list",None,["H2O"]),
        ("independent potential/fugacity/activity list","independent potential list",[]),
        ("excluded phase list",None,list(EXCLUDED)),
        ("solution phase list",None,roster)):
        text=d.replace_section(text,"begin "+name,"end "+(end or name),rows)
    raw=text.encode("ascii")
    check_project(raw,norm,roster)
    return raw,norm


def check_project(raw,norm,roster):
    text=raw.decode("ascii")
    rows=section_rows(text,"thermodynamic component list")
    actual={}
    for row in rows:
        name=row[:5].strip()
        fields=row[5:].split()
        need(name in norm and name not in actual and len(fields)==4 and fields[0]=="1"
             and fields[2:]==["0.0","0.0"],"C03EC_COMPONENT_ROW")
        actual[name]=float(fields[1])
    need(tuple(actual)==ORDER and actual==norm and "O2" in actual and "H2O" not in actual,
         "C03EC_CONSERVED_COMPONENTS")
    need(section_rows(text,"saturated component list")==[]
         and section_rows(text,"saturated phase component list")==["H2O"]
         and section_rows(text,"independent potential/fugacity/activity list","independent potential list")==[]
         and section_rows(text,"excluded phase list")==list(EXCLUDED)
         and section_rows(text,"solution phase list")==roster,"C03EC_PROJECT_SECTIONS")
    need(re.search(r"(?m)^\s*5 ifug EoS for saturated phase$",text) is not None,
         "C03EC_CORK_FLAG")
    return actual


def heading_tokens(text,heading):
    matches=list(re.finditer(r"(?m)^\s*"+re.escape(heading)+r"[ \t]*\r?$",text))
    if len(matches)!=1:
        return None
    lines=text[matches[0].end():].splitlines()
    for line in lines:
        if line.strip():
            return line.split()
    return None


def inspect_native(raw,prn,roster,records):
    obs=d.observe(raw,prn,roster)
    text=raw.decode("utf-8",errors="replace")
    printed=prn.decode("utf-8",errors="replace")
    details=d.model_audit.native_model_details(raw,roster,records)
    headings={key:heading_tokens(printed,label) for key,label in {
        "saturated_phase_components":"Saturated phase components:",
        "conserved_components":"Components with unconstrained potentials:",
        "saturated_or_buffered_components":"Saturated or buffered components:",
        "excluded_phases_first_row":"Excluded phases:"}.items()}
    counts=details["pseudocompound_reports"]
    count_total=sum(x["count"] for x in counts)
    warnings=re.findall(r"\*\*warning ver(\d+)\*\*",text,re.I)
    need(not set(warnings)&{"017","059","966","968"},"C03EC_FORBIDDEN_WARNING_FINAL")
    dispositions=obs["native_model_dispositions"]
    checks={"all_requested_included":set(dispositions["included"])==set(roster)
                and not dispositions["rejected"] and not dispositions["not_found"]
                and not obs["unaccounted_requested_models"],
            "pseudocompound_reconciliation":len(counts)==len(roster)
                and set(x["model"] for x in counts)==set(roster)
                and all(x["count"]>0 for x in counts)
                and details["native_total_pseudocompounds_reports"]==[count_total],
            "native_water_saturation_header":headings["saturated_phase_components"]==["H2O"],
            "native_conserved_components_header":headings["conserved_components"] is not None
                and set(headings["conserved_components"])==set(ORDER),
            "no_buffer_header":headings["saturated_or_buffered_components"] is None}
    return {"observation":obs,"native_model_details":details,"pseudocompound_sum":count_total,
            "warning_codes":warnings,"native_print_headers":headings,"checks":checks,
            "scientific_promotion":False,"requested_equilibrium_points":0,
            "full_native_phase_admission_verified":False}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    ap.add_argument("--native-preflight-only",action="store_true",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03EC_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C03EC_OUTPUT_EXISTS")
    report,runtime,template,hp,original,derived,options,contract,records=parent()
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
            "native_policy":PreflightDialogue.policy,"requested_equilibrium_points":0,
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
        s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03EC_NATIVE_PREFLIGHT_MANIFEST_V1",
            "status":state,"source_sha":head,"C03EB_manifest_sha256":PIN,"files":members,
            "native_initialization_attempts":attempts,"requested_equilibrium_points":0,
            "authorized_equilibrium_solver_calls":0,"scientific_promotion":False,**SCOPE})
        print("C03EC_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"),flush=True)
    print(state)
    print("NATIVE_INITIALIZATION_ATTEMPTS="+str(attempts))
    print("REQUESTED_EQUILIBRIUM_POINTS=0")


if __name__=="__main__":
    main()
