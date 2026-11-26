"""C03F-N: qualify exact closed-bulk native inputs with zero equilibrium requests."""
from __future__ import annotations
import argparse
from collections import Counter
import json
import re
import shutil
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03f_closed_bulk_design as design
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_r5_native_preflight as r5

c=design.c
d=c.d
s2=c.s2
need=c.need
hgp=c.hgp
dialogue=d.dialogue
PIN="f6df798d5d818f599703ce979f0a3c36d772ef0d9b84d6fdeb299dd4496d68ca"
SOURCE="13e354d0e1a94b812ef8d98cf5b06c8bba21c4e8"
OLD_PIN="5a64f2e9ba0d753a3183bef295ce6771529b3ba178928012909d378e8a1891af"
OUT=s2.BASE/"R6_THERMO_C03F_NATIVE_PREFLIGHT_NEW01"
STATUS="C03F_CLOSED_BULK_NATIVE_PREFLIGHT_CAPTURED__REVIEW_REQUIRED"
LIMITS=d.LIMITS
FIELDS=("T(K)","P(bar)")
SENTINEL=b"0 0\n"


def warning_codes(raw):
    return Counter(re.findall(rb"\*\*warning ver(\d+)\*\*",raw,re.I))


class ClosedDialogue(dialogue.Dialogue):
    policy="C03F_CLOSED_BULK_PINNED_O2_SI_ACK_FULL_TWO_FIELD_ZERO_SENTINEL"

    def __init__(self):
        super().__init__(allow_si013=True,allow_gl017=False)

    def next_response(self,raw):
        tail=raw[self.cursor:]
        bad=re.search(rb"\*\*error ver\d+\*\*|\*\*warning ver(?!966\*\*|968\*\*|013\*\*|099\*\*|114\*\*)\d+\*\*",tail,re.I)
        need(bad is None,"C03F_NATIVE_UNAPPROVED_DIAGNOSTIC:"+repr(bad.group() if bad else b""))
        hits=[(tail.find(p),p) for p in dialogue.PROMPTS if p in tail]
        if hits:
            pos,prompt=min(hits,key=lambda x:x[0])
            if prompt==dialogue.PT:
                end=tail.find(b"\n",pos)
                if end<0:
                    return None
                fields=tuple(tail[pos+len(prompt):end].decode("ascii").split())
                need(self.state=="AWAIT_PT" and fields==FIELDS,
                     "C03F_NATIVE_PT_FIELDS:"+repr(fields))
                need(self.acknowledged==["966","968","013"],"C03F_NATIVE_ACK_SEQUENCE")
                self.cursor+=end+1
                self.state="SENTINEL_SENT"
                self.events.append({"prompt":"ZERO_PT_SENTINEL","response":"0 0",
                    "potential_fields":list(fields),"stdout_byte_offset_after_prompt":self.cursor})
                return SENTINEL
        return super().next_response(raw)


def verify_design(parent):
    archive=design.OUT
    rec=c.read(d.m.HERE/"c03f_design_fair_receipt_v1.json")
    need(archive.is_dir() and not archive.is_symlink()
         and not (archive/"MANIFEST.json").is_symlink()
         and hgp.file_sha(archive/"MANIFEST.json")==PIN==rec["manifest_sha256"],"C03FN_DESIGN_PIN")
    man=c.read(archive/"MANIFEST.json")
    inv=d.launcher.inventory(archive)
    inv.pop("MANIFEST.json")
    need(inv==man["files"] and man["source_sha"]==SOURCE==rec["source_sha"]
         and man["schema"]=="R6_C03F_CLOSED_BULK_DESIGN_MANIFEST_V1"
         and man["status"]==design.STATUS and man["C03EE_R2_manifest_sha256"]==design.PIN
         and man["candidate_recipes"]==2 and man["candidate_points"]==4
         and man["authorized_equilibrium_solver_calls"]==man["additional_engine_runs"]==0
         and man["scientific_promotion"] is False
         and all(man[k]==v for k,v in c.SCOPE.items()),"C03FN_DESIGN_MANIFEST")
    report,runtime,template,hp,original,derived,options,contract,records=parent
    review=design.replay_reference(parent)
    plans,inputs=design.build_plans(parent)
    policy=design.r1.liquid_policy(hp,records,original,derived,contract,Path(runtime["source"]))
    archived=c.read(archive/"DESIGN.json")
    need(review==c.read(archive/"REFERENCE_REVIEW.json")
         and archived["plans"]==plans and archived["liquid_policy"]==policy
         and archived["boundary"]=="CLOSED_BULK_NO_BUFFER_NO_SATURATION"
         and archived["authorized_equilibrium_solver_calls"]==archived["additional_engine_runs"]==0,
         "C03FN_DESIGN_REPLAY")
    for name in plans:
        need(c.read(archive/name/"INPUT.json")==plans[name]
             and all((archive/name/k).read_bytes()==v for k,v in inputs[name].items()),
             "C03FN_INPUT_DRIFT:"+name)
    return plans,inputs


def old_reference():
    archive=d.OUT
    need(hgp.file_sha(archive/"MANIFEST.json")==OLD_PIN,"C03FN_OLD_PIN")
    man=c.read(archive/"MANIFEST.json")
    inv=d.launcher.inventory(archive)
    inv.pop("MANIFEST.json")
    need(inv==man["files"] and man["requested_equilibrium_points"]==0
         and man["native_initialization_attempts"]==2
         and man["scientific_promotion"] is False,"C03FN_OLD_MANIFEST")
    result={}
    for name in ("C01_MORB_BASE","C01_MORB_WET"):
        work=archive/name
        raw=(work/"RUN_STDOUT.log").read_bytes()
        dia=c.read(work/"DIALOGUE.json")
        need(dia["acknowledged_warning_codes"]==["966","968","013","017"]
             and dia["state"]=="SENTINEL_SENT","C03FN_OLD_ACK")
        start=raw.index(dialogue.PT)
        end=raw.index(b"\n",start)
        fields=tuple(raw[start+len(dialogue.PT):end].decode("ascii").split())
        need(fields==FIELDS,"C03FN_OLD_FIELDS")
        counts=warning_codes(raw)
        need(counts.pop(b"017")==1,"C03FN_OLD_LEGACY_WARNING")
        result[name]={k.decode():v for k,v in sorted(counts.items())}
    return result


def inspect(raw,prn,stdin,dia,roster,records,expected):
    obs=d.observe(raw,prn,roster)
    details=d.model_audit.native_model_details(raw,roster,records)
    included=obs["native_model_dispositions"]
    need(set(included["included"])==set(roster) and not included["rejected"]
         and not included["not_found"] and not obs["unaccounted_requested_models"],
         "C03FN_NATIVE_ROSTER")
    rows=details["pseudocompound_reports"]
    need(len(rows)==17 and {x["model"] for x in rows}==set(roster)
         and all(x["count"]>0 for x in rows)
         and sum(x["count"] for x in rows)==1123
         and details["native_total_pseudocompounds_reports"]==[1123],"C03FN_PSEUDOCOMPOUNDS")
    missing={x["model"]:[v["endmember"] for v in x["endmembers"]]
             for x in details["missing_endmember_reports"]}
    need(missing==design.r1.ed.MISSING,"C03FN_MISSING_DRIFT")
    actual={k.decode():v for k,v in sorted(warning_codes(raw).items())}
    need(actual==expected,"C03FN_WARNING_DRIFT:"+repr(actual))
    p=ClosedDialogue()
    replies=[]
    while True:
        reply=p.next_response(raw)
        if reply is None:
            break
        replies.append(reply)
    need(b"".join(replies)==stdin==b"c03d\ny\ny\ny\nn\n0 0\n"
         and p.events==dia["events"] and p.state==dia["state"]=="SENTINEL_SENT"
         and p.acknowledged==dia["acknowledged_warning_codes"]
         and raw.count(dialogue.PT)==1 and dia["scientific_warning_acceptance"] is False,
         "C03FN_DIALOGUE_REPLAY")
    return {"observation":obs,"native_model_details":details,"warning_counts":actual,
            "potential_fields":list(FIELDS),"included_models":17,"pseudocompounds":1123,
            "printed_bytes":len(prn),"requested_equilibrium_points":0,
            "native_bulk_readback_verified":False,"scientific_promotion":False}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    ap.add_argument("--native-preflight-only",action="store_true",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03FN_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C03FN_OUTPUT_EXISTS")
    parent=c.parent()
    design.r1.prior.verify_readiness(parent)
    design.r1.verify_failure(parent)
    plans,inputs=verify_design(parent)
    report,runtime,template,hp,original,derived,options,contract,records=parent
    sentinel_source=r5.verify_sentinel_source((Path(runtime["source"])/"src/meemum.f").read_bytes())
    # Only the source read-before-exit ordering is reused, not its saturated field metadata.
    sentinel_source["prompt_fields"]=list(FIELDS)
    sentinel_source["sentinel"]="0 0"
    expected=old_reference()
    print("C03FN_DESIGN_REPLAY_PASS",PIN,flush=True)
    print("C03FN_CLOSED_REFERENCE_WARNING_COUNTS",json.dumps(expected,sort_keys=True),flush=True)
    need(shutil.disk_usage(s2.BASE).free>=LIMITS["retained_bytes_stop_threshold"],"C03FN_DISK")
    OUT.mkdir(parents=False,exist_ok=False)
    attempts=0
    state="C03F_NATIVE_PREFLIGHT_FAILED_PRESERVED"
    results={}
    try:
        s2.write_json(OUT/"PROVENANCE.json",{"source_sha":head,"design_manifest":PIN,
            "old_closed_manifest":OLD_PIN,"source_sentinel":sentinel_source,
            "expected_warning_counts":expected,"runtime":runtime,"limits":LIMITS,
            "authorized_equilibrium_solver_calls":0,**c.SCOPE})
        for name,files in inputs.items():
            work=OUT/name
            work.mkdir()
            for k,v in files.items():
                with (work/k).open("xb") as f:
                    f.write(v)
            s2.write_json(work/"INPUT.json",plans[name])
            need(d.launcher.retained_bytes(OUT)<LIMITS["retained_bytes_stop_threshold"]
                 and hgp.file_sha(runtime["binary"])==runtime["binary_sha256"],"C03FN_LAUNCH_GUARD")
            attempts+=1
            try:
                dialogue.launch_dialogue([Path(runtime["binary"])],work,LIMITS,
                                         protocol_factory=ClosedDialogue)
            finally:
                if (work/"RUN_STDOUT.log").is_file():
                    raw=(work/"RUN_STDOUT.log").read_bytes()
                    print("C03FN_NATIVE_TAIL",name,raw[-10000:].decode("utf-8",errors="replace"),flush=True)
                if (work/"DIALOGUE.json").is_file():
                    print("C03FN_DIALOGUE",name,(work/"DIALOGUE.json").read_text(),flush=True)
            prn=work/"c03d.prn"
            result=inspect(raw,prn.read_bytes() if prn.is_file() else b"",
                    (work/"DIALOGUE_STDIN.log").read_bytes(),c.read(work/"DIALOGUE.json"),
                    plans[name]["solution_models"],records,expected[name])
            s2.write_json(work/"READBACK.json",result)
            results[name]=result
            print("C03FN_READBACK",name,json.dumps({k:v for k,v in result.items()
                if k not in ("observation","native_model_details")},sort_keys=True),flush=True)
        need(attempts==2 and len(results)==2,"C03FN_TOTAL")
        s2.write_json(OUT/"RESULT.json",{"observations":results,"requested_equilibrium_points":0,
                     "scientific_promotion":False,**c.SCOPE})
        state=STATUS
    except BaseException as exc:
        s2.write_json(OUT/"FAILURE.json",{"error":type(exc).__name__,"message":str(exc),
            "native_initialization_attempts":attempts,"requested_equilibrium_points":0})
        raise
    finally:
        s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03F_NATIVE_PREFLIGHT_MANIFEST_V1",
            "status":state,"source_sha":head,"C03F_design_manifest_sha256":PIN,
            "files":d.launcher.inventory(OUT),"native_initialization_attempts":attempts,
            "requested_equilibrium_points":0,"authorized_equilibrium_solver_calls":0,
            "scientific_promotion":False,**c.SCOPE})
        print("C03FN_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"),flush=True)
    print(state)
    print("REQUESTED_EQUILIBRIUM_POINTS=0")


if __name__=="__main__":
    main()
