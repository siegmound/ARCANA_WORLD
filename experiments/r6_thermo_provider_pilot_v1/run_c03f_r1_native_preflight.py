"""C03FN-R1: reconcile legacy-only ver059 expectation, replay BASE, initialize WET only."""
from __future__ import annotations
import argparse
import json
import re
import shutil
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03f_native_preflight as old
from experiments.r6_thermo_provider_pilot_v1 import run_c03e_reference_design as reference

c=old.c
d=old.d
s2=old.s2
need=old.need
hgp=old.hgp
design=old.design
PIN="b3bad907125b417bfebde43af91b9829643341f78204f8effda1caa9548a7bf5"
SOURCE="f540775cbe46264e8d321cf4737f9d1624eaa22f"
OUT=s2.BASE/"R6_THERMO_C03F_NATIVE_PREFLIGHT_NEW02"
STATUS="C03F_R1_CLOSED_BULK_NATIVE_PREFLIGHT_CAPTURED__REVIEW_REQUIRED"
BASE="C01_MORB_BASE"
WET="C01_MORB_WET"
LEGACY={"GlTrTsPg":["fparg_i","fts_i","fgl_i"]}
EXPECTED={"013":1,"099":1,"114":6,"966":1,"968":1}


def corrected_counts(raw,counts,roster):
    need("GlTrTsPg" not in roster and counts.get("059")==3,
         "C03FN_R1_LEGACY_SCOPE")
    sites=reference.invalid_sites(raw)
    need(sites==LEGACY and old.warning_codes(raw)[b"059"]==3,
         "C03FN_R1_LEGACY_SITE_ATTRIBUTION")
    corrected={k:v for k,v in counts.items() if k!="059"}
    need(corrected==EXPECTED,"C03FN_R1_UNEXPECTED_WARNING_PROFILE")
    return corrected


def corrected_reference(plans,runtime):
    # old_reference independently verifies immutable historical archive.
    counts=old.old_reference()
    source=Path(runtime["source"])/"src"
    rl=(source/"rlib.f").read_bytes()
    tl=(source/"tlib.f").read_bytes()
    need(hgp.sha(rl)=="8cd5df49273978b737cc6fd4fc5db9dcd09af4e1219c77717e49c9ecfd68cbd1"
         and hgp.sha(tl)=="426090ce28f14b81c3921e44b695c0adc13b0ba05c3dc15ffef117937b9cfa77",
         "C03FN_R1_SOURCE_PIN")
    need(re.search(rb"call warn\s*\(\s*59,",rl,re.I)
         and b"**warning ver059** endmember" in tl
         and b"has invalid site populations." in tl,"C03FN_R1_SOURCE_SEMANTICS")
    result={}
    for name in (BASE,WET):
        raw=(d.OUT/name/"RUN_STDOUT.log").read_bytes()
        result[name]=corrected_counts(raw,counts[name],plans[name]["solution_models"])
    return result


def inspect_work(work,plan,records,expected):
    raw=(work/"RUN_STDOUT.log").read_bytes()
    prn=work/"c03d.prn"
    launch=c.read(work/"LAUNCH.json")
    dia=c.read(work/"DIALOGUE.json")
    need(launch["exit_code"]==0 and launch["error"] is None and not launch["timeout"]
         and dia["error"] is None,"C03FN_R1_NATIVE_EXIT")
    return old.inspect(raw,prn.read_bytes() if prn.is_file() else b"",
             (work/"DIALOGUE_STDIN.log").read_bytes(),dia,
             plan["solution_models"],records,expected)


def replay_base(plans,inputs,records,expected):
    archive=old.OUT
    rec=c.read(d.m.HERE/"c03fn_failed_fair_receipt_v1.json")
    need(archive.is_dir() and not archive.is_symlink()
         and not (archive/"MANIFEST.json").is_symlink()
         and hgp.file_sha(archive/"MANIFEST.json")==PIN==rec["manifest_sha256"],
         "C03FN_R1_ARCHIVE_PIN")
    man=c.read(archive/"MANIFEST.json")
    inv=d.launcher.inventory(archive)
    inv.pop("MANIFEST.json")
    need(inv==man["files"] and man["source_sha"]==SOURCE==rec["source_sha"]
         and man["schema"]=="R6_C03F_NATIVE_PREFLIGHT_MANIFEST_V1"
         and man["status"]=="C03F_NATIVE_PREFLIGHT_FAILED_PRESERVED"
         and man["C03F_design_manifest_sha256"]==old.PIN
         and man["native_initialization_attempts"]==1
         and man["requested_equilibrium_points"]==man["authorized_equilibrium_solver_calls"]==0
         and man["scientific_promotion"] is False
         and all(man[k]==v for k,v in c.SCOPE.items()),"C03FN_R1_ARCHIVE_MANIFEST")
    work=archive/BASE
    need(not (archive/WET).exists() and not (work/"READBACK.json").exists()
         and c.read(work/"INPUT.json")==plans[BASE]
         and all((work/k).read_bytes()==v for k,v in inputs[BASE].items()),
         "C03FN_R1_BASE_INPUT")
    failure=c.read(archive/"FAILURE.json")
    need(failure["error"]=="ValueError"
         and failure["message"]=="C03FN_WARNING_DRIFT:"+repr(EXPECTED)
         and failure["native_initialization_attempts"]==1
         and failure["requested_equilibrium_points"]==0,"C03FN_R1_FAILURE_RECEIPT")
    prior=old.old_reference()[BASE]
    try:
        inspect_work(work,plans[BASE],records,prior)
    except ValueError as exc:
        need(str(exc)==failure["message"],"C03FN_R1_OLD_FAILURE_REPLAY")
    else:
        raise ValueError("C03FN_R1_OLD_FAILURE_MISSING")
    result=inspect_work(work,plans[BASE],records,expected[BASE])
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    ap.add_argument("--native-preflight-only",action="store_true",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03FN_R1_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C03FN_R1_OUTPUT_EXISTS")
    parent=c.parent()
    design.r1.prior.verify_readiness(parent)
    design.r1.verify_failure(parent)
    plans,inputs=old.verify_design(parent)
    report,runtime,template,hp,original,derived,options,contract,records=parent
    expected=corrected_reference(plans,runtime)
    base_result=replay_base(plans,inputs,records,expected)
    print("C03FN_R1_LEGACY_WARNING_ATTRIBUTION_PASS",json.dumps(LEGACY),flush=True)
    print("C03FN_R1_BASE_REPLAY_PASS",PIN,flush=True)
    print("C03FN_R1_READBACK",BASE,json.dumps({k:v for k,v in base_result.items()
        if k not in ("observation","native_model_details")},sort_keys=True),flush=True)
    source=old.r5.verify_sentinel_source((Path(runtime["source"])/"src/meemum.f").read_bytes())
    source["prompt_fields"]=list(old.FIELDS)
    source["sentinel"]="0 0"
    need(shutil.disk_usage(s2.BASE).free>=old.LIMITS["retained_bytes_stop_threshold"],"C03FN_R1_DISK")
    OUT.mkdir(parents=False,exist_ok=False)
    attempts=0
    state="C03FN_R1_NATIVE_PREFLIGHT_FAILED_PRESERVED"
    try:
        s2.write_json(OUT/"PROVENANCE.json",{"source_sha":head,"design_manifest":old.PIN,
            "base_archive_manifest":PIN,"historical_native_initialization_attempts":1,
            "legacy_only_warning_removal":LEGACY,"expected_warning_counts":expected,
            "runtime":runtime,"source_sentinel":source,"limits":old.LIMITS,
            "authorized_equilibrium_solver_calls":0,**c.SCOPE})
        s2.write_json(OUT/"BASE_REPLAY.json",base_result)
        work=OUT/WET
        work.mkdir()
        for k,v in inputs[WET].items():
            with (work/k).open("xb") as f:
                f.write(v)
        s2.write_json(work/"INPUT.json",plans[WET])
        need(d.launcher.retained_bytes(OUT)<old.LIMITS["retained_bytes_stop_threshold"]
             and hgp.file_sha(runtime["binary"])==runtime["binary_sha256"],"C03FN_R1_LAUNCH")
        attempts=1
        try:
            old.dialogue.launch_dialogue([Path(runtime["binary"])],work,old.LIMITS,
                                         protocol_factory=old.ClosedDialogue)
        finally:
            if (work/"RUN_STDOUT.log").is_file():
                print("C03FN_R1_NATIVE_TAIL",WET,(work/"RUN_STDOUT.log").read_bytes()[-10000:].decode("utf-8",errors="replace"),flush=True)
            if (work/"DIALOGUE.json").is_file():
                print("C03FN_R1_DIALOGUE",WET,(work/"DIALOGUE.json").read_text(),flush=True)
        wet=inspect_work(work,plans[WET],records,expected[WET])
        s2.write_json(work/"READBACK.json",wet)
        print("C03FN_R1_READBACK",WET,json.dumps({k:v for k,v in wet.items()
             if k not in ("observation","native_model_details")},sort_keys=True),flush=True)
        s2.write_json(OUT/"RESULT.json",{"observations":{BASE:base_result,WET:wet},
            "base_archive_manifest":PIN,"requested_equilibrium_points":0,
            "scientific_promotion":False,**c.SCOPE})
        state=STATUS
    except BaseException as exc:
        s2.write_json(OUT/"FAILURE.json",{"error":type(exc).__name__,"message":str(exc),
             "native_initialization_attempts":attempts,"requested_equilibrium_points":0})
        raise
    finally:
        s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03FN_R1_NATIVE_PREFLIGHT_MANIFEST_V1",
             "status":state,"source_sha":head,"C03F_design_manifest_sha256":old.PIN,
             "base_archive_manifest":PIN,"files":d.launcher.inventory(OUT),
             "native_initialization_attempts":attempts,
             "historical_native_initialization_attempts":1,
             "requested_equilibrium_points":0,"authorized_equilibrium_solver_calls":0,
             "scientific_promotion":False,**c.SCOPE})
        print("C03FN_R1_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"),flush=True)
    print(state)
    print("ADDITIONAL_NATIVE_INITIALIZATIONS=1")
    print("REQUESTED_EQUILIBRIUM_POINTS=0")


if __name__=="__main__":
    main()
