"""C03EE-R1: bounded cold subsolidus comparison, source-audited PMELT exclusions."""
from __future__ import annotations
import argparse
import json
import re
import shutil
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03ee_diagnostic_benchmark as prior
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_native_preflight as c
from experiments.r6_thermo_provider_pilot_v1 import run_c03ed_scientific_readiness as ed

d=c.d
s2=c.s2
need=c.need
hgp=c.hgp
launcher=prior.launcher
PIN=prior.PIN
POINTS=prior.POINTS
LIMITS=prior.LIMITS
FAILED_PIN="85d9117befcd7dc10590b7ce00a7be794538c7a1fb29d6456a4b704338123a38"
FAILED_SOURCE="622e780030d6917b3286047ebe80a9fee3f2a6b0"
OUT=s2.BASE/"R6_THERMO_C03EE_DIAGNOSTIC_BENCHMARK_NEW02"
STATUS="C03EE_R1_SIX_SUBSOLIDUS_DIAGNOSTICS_CAPTURED__SCIENTIFIC_REVIEW_REQUIRED"
LIQUID_IDS=("qGL","coGL","faGL","foGL","woGL","nasGL","kalGL","tiGL","hemGL")
FAILED_SPECIES=("foGL","woGL","nasGL")


def token_hits(text,name):
    return [i+1 for i,line in enumerate(text.splitlines())
            if re.search(r"(?<![\w])"+re.escape(name)+r"(?![\w])",line)]


def liquid_headers(hp):
    text=hp.decode("utf-8")
    result={}
    for name in LIQUID_IDS:
        rows=re.findall(r"(?m)^\s*"+re.escape(name)+r"\s+EoS\s*=\s*3\s*\|([^\r\n]+)$",text)
        need(len(rows)==1 and "PMELT liquid endmember" in rows[0],
             "C03EE_R1_LIQUID_IDENTITY:"+name)
        result[name]=rows[0].strip()
    return result


def liquid_policy(hp,records,original,derived,contract,source):
    headers=liquid_headers(hp)
    need("H2O" in records and "h2oGL" in records
         and not set(LIQUID_IDS)&set(c.EXCLUDED)
         and not set(LIQUID_IDS)&{"H2O","h2oGL","h2oL","wL_q","O2"},
         "C03EE_R1_WATER_REDox_SCOPE")
    active=d.composition_audit.active_text(hp.decode())
    makes=ed.r2.a.section(active,"makes")
    audits={}
    for arm,lib in (("ACT_ONLY",original),("DP_DS5_ONLY",derived)):
        roster=contract["arms"][arm]["solution_models"]
        blocks=d.c.b.model_blocks(lib,tuple(roster))
        need(set(blocks)==set(roster) and all(blocks.values()),"C03EE_R1_MODEL_BLOCKS")
        for name in LIQUID_IDS:
            need(name in records and records[name]["eos"]==3
                 and not token_hits(makes,name)
                 and all(not token_hits(d.composition_audit.active_text(block["text"]),name)
                         for block in blocks.values()),"C03EE_R1_LIQUID_DEPENDENCY:"+arm+":"+name)
        audits[arm]={"models_checked":len(roster),"literal_dependencies":0}
    raw=(source/"src/rlib.f").read_bytes()
    need(hgp.sha(raw)=="8cd5df49273978b737cc6fd4fc5db9dcd09af4e1219c77717e49c9ecfd68cbd1",
         "C03EE_R1_RLIB_PIN")
    text=raw.decode().lower()
    need("if (kt.lt.0d0.or.vt.lt.0d0) then" in text
         and "call warn (46,t,id,names(id))" in text
         and "call warn (49,t,46,'gcpd_bm3')" in text,
         "C03EE_R1_WARNING_SOURCE")
    return {"scope":"NONEXACT_SUBSOLIDUS_REFERENCE_DIAGNOSTIC_ONLY",
            "added_exclusions":list(LIQUID_IDS),"headers":headers,
            "dependency_audit":audits,"water_records_unchanged":True,
            "rlib_sha256":hgp.sha(raw),"warning_046_allowlisted":False,
            "warning_049_allowlisted":False,"remaining_liquid_records_not_qualified":True,
            "scientific_promotion":False}


def verify_failure(parent):
    rec=c.read(d.m.HERE/"c03ee_failed_triage_fair_receipt_v1.json")
    failed=prior.OUT
    need(failed.is_dir() and not failed.is_symlink()
         and not (failed/"MANIFEST.json").is_symlink()
         and hgp.file_sha(failed/"MANIFEST.json")==FAILED_PIN==rec["manifest_sha256"],
         "C03EE_R1_FAILED_PIN")
    man=c.read(failed/"MANIFEST.json")
    inv=d.launcher.inventory(failed)
    inv.pop("MANIFEST.json")
    need(inv==man["files"] and man["source_sha"]==FAILED_SOURCE==rec["source_sha"]
         and man["schema"]=="R6_C03EE_DIAGNOSTIC_BENCHMARK_MANIFEST_V1"
         and man["status"]=="C03EE_DIAGNOSTIC_FAILED_PRESERVED"
         and man["C03ED_manifest_sha256"]==PIN
         and man["native_initialization_attempts"]==1
         and man["requested_equilibrium_points"]==1 and man["completed_equilibrium_points"]==0
         and man["scientific_promotion"] is False
         and all(man[k]==v for k,v in c.SCOPE.items()),"C03EE_R1_FAILED_MANIFEST")
    work=failed/"ACT_ONLY"
    dia=c.read(work/"DIALOGUE.json")
    launch=c.read(work/"LAUNCH.json")
    cap=c.read(work/"POINT_CAPTURE.json")
    failure=c.read(failed/"FAILURE.json")
    raw=(work/"RUN_STDOUT.log").read_bytes()
    stdin=(work/"DIALOGUE_STDIN.log").read_bytes()
    need(failure["message"]=="C03EE_POINT_NATIVE_DIAGNOSTIC"
         and dia["error"]==launch["error"]=="ValueError: C03EE_POINT_NATIVE_DIAGNOSTIC"
         and launch["exit_code"]==-9 and launch["timeout"] is False
         and dia["state"]=="AWAIT_NEXT" and dia["requested_ids"]==["B01"]
         and dia["completed_ids"]==[] and cap["requested_ids"]==["B01"] and cap["completed"]==[]
         and stdin==b"c03d\ny\ny\ny\ny\nn\n498.15 1500 0\n"
         and not (failed/"DP_DS5_ONLY").exists(),"C03EE_R1_FAILED_DIALOGUE")
    offset=dia["events"][-1]["stdout_byte_offset_after_prompt"]
    suffix=raw[offset:].decode("utf-8")
    hits=re.findall(r"\*\*warning ver046\*\* temperature \(\s*498\.150\s+K\) is out of range for endmember/phase:\s*(\S+)",suffix)
    need(tuple(hits)==FAILED_SPECIES
         and re.findall(r"\*\*(?:warning|error) ver(\d+)\*\*",suffix)==["046"]*3
         and "Stable phases at:" not in suffix and "Phase Compositions (" not in suffix,
         "C03EE_R1_FAILED_WARNING_DRIFT")
    report,runtime,template,hp,original,derived,options,contract,records=parent
    roster=contract["arms"]["ACT_ONLY"]["solution_models"]
    project,norm=c.make_project(template,report,d.c.b.components(hp),contract,"ACT_ONLY")
    inputs={"c03d.dat":project,"hp02ver.dat":hp,"solution_model.dat":original,
            "perplex_option.dat":d.options_candidate(options)}
    need(all((work/k).read_bytes()==v for k,v in inputs.items()),"C03EE_R1_FAILED_INPUT_DRIFT")
    p=prior.DiagnosticDialogue("ACT_ONLY",records,roster)
    prefix=raw[:offset]
    replies=[]
    while True:
        response=p.next_response(prefix)
        if response is None:
            break
        replies.append(response)
    need(b"".join(replies)==stdin and p.events==dia["events"],"C03EE_R1_FAILED_PREFIX_REPLAY")
    try:
        p.next_response(raw)
    except ValueError as exc:
        need(str(exc)=="C03EE_POINT_NATIVE_DIAGNOSTIC","C03EE_R1_FAILED_ERROR_REPLAY")
    else:
        raise ValueError("C03EE_R1_FAILED_ERROR_MISSING")
    return {"manifest_sha256":FAILED_PIN,"requested":1,"completed":0,
            "warning_species":list(FAILED_SPECIES),"old_error_replayed":True}


def make_subsolidus_project(template,report,masses,contract,arm):
    raw,norm=c.make_project(template,report,masses,contract,arm)
    text=raw.decode("ascii")
    revised=d.replace_section(text,"begin excluded phase list","end excluded phase list",
                              list(c.EXCLUDED)+list(LIQUID_IDS))
    need(c.section_rows(revised,"excluded phase list")==list(c.EXCLUDED)+list(LIQUID_IDS),
         "C03EE_R1_EXCLUSION_SERIALIZATION")
    restored=d.replace_section(revised,"begin excluded phase list","end excluded phase list",list(c.EXCLUDED))
    need(restored==text,"C03EE_R1_NONEXCLUSION_DRIFT")
    return revised.encode("ascii"),norm


class DiagnosticDialogue(prior.DiagnosticDialogue):
    policy="C03EE_R1_SUBSOLIDUS_PMELT_EXCLUDED_STRICT_NATIVE_DIAGNOSTICS"

    def next_response(self,raw):
        try:
            return super().next_response(raw)
        except ValueError as exc:
            # Include actual native diagnostic lines in traceback; no warning acceptance.
            tail=raw[self.cursor:].decode("utf-8",errors="replace")
            diagnostic=re.search(r"\*\*(?:warning|error) ver\d+\*\*",tail,re.I)
            if diagnostic:
                raise ValueError(str(exc)+":"+tail[diagnostic.start():][:2000]) from exc
            raise


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    ap.add_argument("--diagnostic-six-only",action="store_true",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03EE_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C03EE_OUTPUT_EXISTS")
    parent=c.parent()
    report,runtime,template,hp,original,derived,options,contract,records=parent
    readiness=prior.verify_readiness(parent)
    failure=verify_failure(parent)
    policy=liquid_policy(hp,records,original,derived,contract,Path(runtime["source"]))
    print("C03EE_R1_FAILURE_REPLAY_PASS",FAILED_PIN,flush=True)
    print("C03EE_R1_LIQUID_POLICY",json.dumps(policy,sort_keys=True),flush=True)
    need(shutil.disk_usage(s2.BASE).free>=LIMITS["retained_bytes_stop_threshold"],"C03EE_DISK")
    OUT.mkdir(parents=False,exist_ok=False)
    attempts=0
    requested=0
    completed=0
    results={}
    state="C03EE_R1_DIAGNOSTIC_FAILED_PRESERVED"
    try:
        s2.write_json(OUT/"PROVENANCE.json",{"source_sha":head,"readiness":readiness,
            "limits":LIMITS,"points":POINTS,"max_native_processes":2,"max_requested_points":6,
            "failed_attempt":failure,"liquid_policy":policy,"historical_requested_points":1,
            "scientific_promotion":False,**c.SCOPE})
        for arm in ed.COUNTS:
            work=OUT/arm
            work.mkdir()
            roster=contract["arms"][arm]["solution_models"]
            project,norm=make_subsolidus_project(template,report,d.c.b.components(hp),contract,arm)
            library=original if arm=="ACT_ONLY" else derived
            inputs={"c03d.dat":project,"hp02ver.dat":hp,"solution_model.dat":library,
                    "perplex_option.dat":d.options_candidate(options)}
            for k,v in inputs.items():
                with (work/k).open("xb") as f:
                    f.write(v)
            s2.write_json(work/"INPUT.json",{"files_sha256":{k:hgp.sha(v) for k,v in inputs.items()},
                "normalized_conserved_moles":norm,"points":POINTS,"solution_models":roster,
                "excluded_phases":list(c.EXCLUDED)+list(LIQUID_IDS)})
            need(d.launcher.retained_bytes(OUT)<LIMITS["retained_bytes_stop_threshold"]
                 and hgp.file_sha(runtime["binary"])==runtime["binary_sha256"],"C03EE_LAUNCH_GUARD")
            protocol=DiagnosticDialogue(arm,records,roster)
            attempts+=1
            try:
                telemetry=launcher.launch_dialogue([Path(runtime["binary"])],work,LIMITS,
                            protocol_factory=lambda:protocol)
            finally:
                requested+=len(protocol.requested)
                completed+=len(protocol.completed)
                s2.write_json(work/"POINT_CAPTURE.json",{"requested_ids":protocol.requested,
                    "completed":protocol.completed,"scientific_acceptance":False})
                if (work/"RUN_STDOUT.log").is_file():
                    raw_tail=(work/"RUN_STDOUT.log").read_bytes()
                    print("C03EE_R1_NATIVE_TAIL",arm,raw_tail[protocol.cursor:][-12000:].decode("utf-8",errors="replace"),flush=True)
                for x in protocol.completed:
                    print("C03EE_POINT",arm,x["id"],x["output_text"],flush=True)
            raw=(work/"RUN_STDOUT.log").read_bytes()
            stdin=(work/"DIALOGUE_STDIN.log").read_bytes()
            replay=DiagnosticDialogue(arm,records,roster)
            responses=[]
            while True:
                response=replay.next_response(raw)
                if response is None:
                    break
                responses.append(response)
            need(b"".join(responses)==stdin and replay.events==protocol.events
                 and replay.completed==protocol.completed and replay.state=="SENTINEL_SENT",
                 "C03EE_FULL_REPLAY:"+arm)
            result={"points":protocol.completed,"launch":telemetry,
                    "scientific_acceptance":False,"requested_equilibrium_points":3}
            s2.write_json(work/"RESULT.json",result)
            results[arm]=result
            print("C03EE_ARM_COMPLETE",arm,telemetry["wall_s"],flush=True)
        need(requested==completed==6 and attempts==2,"C03EE_TOTAL")
        s2.write_json(OUT/"RESULT.json",{"arms":results,"scientific_promotion":False,
                     "requested_equilibrium_points":requested,"completed_equilibrium_points":completed,
                     **c.SCOPE})
        state=STATUS
    except BaseException as exc:
        s2.write_json(OUT/"FAILURE.json",{"error":type(exc).__name__,"message":str(exc),
            "requested_equilibrium_points":requested,"completed_equilibrium_points":completed,
            "native_initialization_attempts":attempts})
        raise
    finally:
        members=d.launcher.inventory(OUT)
        s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03EE_R1_SUBSOLIDUS_DIAGNOSTIC_MANIFEST_V1",
            "status":state,"source_sha":head,"C03ED_manifest_sha256":PIN,"files":members,
            "prior_failed_manifest_sha256":FAILED_PIN,"added_exclusions":list(LIQUID_IDS),
            "native_initialization_attempts":attempts,"authorized_equilibrium_solver_calls":6,
            "requested_equilibrium_points":requested,"completed_equilibrium_points":completed,
            "scientific_promotion":False,**c.SCOPE})
        print("C03EE_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"),flush=True)
    print(state)
    print("REQUESTED_EQUILIBRIUM_POINTS="+str(requested))
    print("COMPLETED_EQUILIBRIUM_POINTS="+str(completed))


if __name__=="__main__":
    main()
