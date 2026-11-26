"""C03E-E: six bounded nonexact reference diagnostic equilibria, no promotion."""
from __future__ import annotations
import argparse
from decimal import Decimal
import json
import re
import shutil
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03ed_scientific_readiness as ed
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_r5_native_preflight as r5
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_native_preflight as c
from experiments.r6_thermo_provider_pilot_v1 import c03ee_diagnostic_launcher as launcher

d=c.d
s2=c.s2
need=c.need
hgp=c.hgp
PIN="940a0b24a77781a6547cd04f51b2cc95937dee36dac686192cbdd7361ef47cc0"
SOURCE="2dca534e48081dda90c27073a2b2f17fba73c505"
OUT=s2.BASE/"R6_THERMO_C03EE_DIAGNOSTIC_BENCHMARK_NEW01"
STATUS="C03EE_SIX_DIAGNOSTIC_EQUILIBRIA_CAPTURED__SCIENTIFIC_REVIEW_REQUIRED"
LIMITS={**c.LIMITS,"walltime_s":180}
POINTS=(("B01","498.15",1500),("B02","473.15",4000),("B03","588.15",2000))
EXPECTED_099=b"**warning ver099** no data for aqueous species, aq_output and aq_lagged_speciation disabled."
NUMBER=r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][-+]?\d+)?"


def verify_fluid_source(raw):
    need(hgp.sha(raw)=="c5fffef05a1926059f31b0685e23a0f79f7e34e51d7a25d8173b10d5b49f33dc",
         "C03EE_FLIB_PIN")
    text=raw.decode("utf-8").lower()
    cfluid=text.split("subroutine cfluid (fo2,fs2)",1)[1].split("subroutine rfluid",1)[0]
    hprk=text.split("subroutine hprk",1)[1].split("subroutine mrk",1)[0]
    need(re.search(r"else if \(ifug\.eq\.5\) then\s+call hprk",cfluid) is not None
         and re.search(r"else if \(xco2\.eq\.0d0\) then\s+call crkh2o \(pbars,t,vol,fh2o\)",hprk) is not None
         and "xco2 = mole fraction of co2 in fluid phase" in hprk,
         "C03EE_PURE_WATER_SOURCE")
    return {"flag":5,"Y_CO2":0,"branch":"CFLUID_HPRK_CRKH2O",
            "source_sha256":hgp.sha(raw),"scope":"STATIC_SOURCE_ENDPOINT_NOT_NUMERICAL_VALIDATION"}


def verify_readiness(parent):
    rec=c.read(d.m.HERE/"c03ed_fair_receipt_v1.json")
    man=d.m.archive_manifest(ed.OUT,PIN,"files_sha256")
    need(man["schema"]=="R6_C03ED_SCIENTIFIC_READINESS_MANIFEST_V1"
         and man["source_sha"]==SOURCE==rec["source_sha"]
         and rec["exit"]==0 and rec["manifest_sha256"]==PIN
         and man["status"]==ed.STATUS and man["R5_manifest_sha256"]==ed.PIN
         and man["additional_engine_runs"]==man["authorized_equilibrium_solver_calls"]==0
         and man["scientific_promotion"] is False
         and set(man["files_sha256"])=={"SCIENTIFIC_READINESS.json"}
         and all(man[k]==v for k,v in c.SCOPE.items()),"C03EE_ED_MANIFEST")
    payload=c.read(ed.OUT/"SCIENTIFIC_READINESS.json")
    report,runtime,template,hp,original,derived,options,contract,records=parent
    obs,common=ed.replay_archive(*parent)
    blocks=d.c.b.model_blocks(original,tuple(ed.MISSING))
    missing=ed.classify_missing(records,blocks,hp)
    need(payload["observations"]==obs and payload["common_model_counts"]==common
         and payload["missing_endmember_evidence"]==missing
         and payload["native_source_context"]==ed.source_context(Path(runtime["source"]))
         and payload["provider_runtime"]==runtime and payload["scientific_promotion"] is False
         and payload["additional_engine_runs"]==payload["authorized_equilibrium_solver_calls"]==0,
         "C03EE_ED_REPLAY")
    for arm,ob in obs.items():
        need(ob["prn_bytes"]==0 and any(EXPECTED_099.decode() in x["lines"]
             for x in ob["warning099"]),"C03EE_VER099_DRIFT:"+arm)
    need(all(missing[k]["classification"]=="MNO_OUTSIDE_REDUCED_BASIS"
             for k in ("mnchl","mnbi","teph","pnt","mnsp"))
         and all(missing[k]["direct_record"] is None and missing[k]["global_make"] is None
                 and missing[k]["active_model_references"] for k in ed.UNKNOWN),
         "C03EE_MISSING_EVIDENCE")
    # These are diagnostic limitations, not acceptance of full redox or pruning.
    need(tuple((x["id"],x["T_K"],x["P_bar"]) for x in contract["points"])==POINTS
         and contract["first_batch_design"]["total_requested_points"]==6
         and contract["first_batch_design"]["authorization"] is False,
         "C03EE_POINT_CONTRACT")
    for name in ("pre","law","q","mt"):
        need(name in records and not records[name]["outside_active_components"]
             and name not in c.EXCLUDED,"C03EE_TARGET_PURE_RECORD:"+name)
    return {"manifest_sha256":PIN,"fluid_source":verify_fluid_source(
                (Path(runtime["source"])/"src/flib.f").read_bytes()),
            "missing_endmember_limits":list(ed.UNKNOWN),"aqueous_speciation":False,
            "positive_phase_admission":"TO_BE_OBSERVED_IN_DIAGNOSTIC_OUTPUT",
            "classification":"NONEXACT_TEXT_CONSTRAINED_MODEL_COMPARISON",
            "scientific_promotion":False}


def capture_point(segment,point):
    ident,t,p=point
    txt=segment.decode("utf-8",errors="replace")
    need(txt.count("Stable phases at:")==1 and txt.count("Phase Compositions (")==1,
         "C03EE_POINT_OUTPUT_MISSING:"+ident)
    vals={}
    for field in r5.PT_FIELDS:
        m=re.findall(r"(?m)^\s*"+re.escape(field)+r"\s*=\s*("+NUMBER+r")\s*$",txt)
        need(len(m)==1,"C03EE_POINT_FIELD:"+ident+":"+field)
        vals[field]=Decimal(m[0].replace("D","E").replace("d","e"))
    need(abs(vals["T(K)"]-Decimal(t))<=Decimal("0.01")
         and abs(vals["P(bar)"]-Decimal(p))<=Decimal("0.1")
         and vals["Y(CO2)"]==0,"C03EE_POINT_READBACK:"+ident)
    need(not re.search(r"\*\*(?:warning|error) ver\d+\*\*",txt,re.I),
         "C03EE_POINT_DIAGNOSTIC:"+ident)
    # Raw output is preserved; no inference of mineral chemistry from model label.
    return {"id":ident,"T_K":t,"P_bar":p,"Y_CO2":0,
            "native_potential_readback":{k:str(v) for k,v in vals.items()},
            "stdout_sha256":hgp.sha(segment),"stdout_bytes":len(segment),
            "output_text":txt,"scientific_acceptance":False}


class DiagnosticDialogue(r5.PreflightDialogue):
    policy="C03EE_EXACT_THREE_PINNED_PT_POINTS_THEN_ZERO_SENTINEL"

    def __init__(self,arm,records,roster):
        super().__init__()
        self.arm=arm
        self.records=records
        self.roster=roster
        self.points=POINTS
        self.requested=[]
        self.completed=[]

    def next_response(self,raw):
        tail=raw[self.cursor:]
        hits=[(tail.find(p),p) for p in c.dialogue.PROMPTS if p in tail]
        if hits:
            pos,prompt=min(hits,key=lambda x:x[0])
            if prompt==c.dialogue.PT:
                end=tail.find(b"\n",pos)
                if end<0:
                    return None
                fields=tuple(tail[pos+len(prompt):end].decode("ascii").split())
                need(fields==r5.PT_FIELDS and self.state in ("AWAIT_PT","AWAIT_NEXT"),
                     "C03EE_UNEXPECTED_PT")
                if self.state=="AWAIT_PT":
                    # Validate actual native initialization before sending any nonzero PT.
                    header=raw[:self.cursor+end+1]
                    init=c.inspect_native(header,b"",self.roster,self.records)
                    need(init["checks"]["all_requested_included"]
                         and init["checks"]["pseudocompound_reconciliation"]
                         and init["pseudocompound_sum"]==ed.COUNTS[self.arm]
                         and init["warning_codes"]==ed.WARNINGS
                         and [e["species"] for e in self.events if "species" in e]==ed.SPECIES
                         and EXPECTED_099 in b" ".join(header.split()),
                         "C03EE_INITIALIZATION_DRIFT")
                else:
                    self.completed.append(capture_point(tail[:pos],self.points[len(self.completed)]))
                self.cursor+=end+1
                if len(self.requested)==len(self.points):
                    need(len(self.completed)==len(self.points),"C03EE_INCOMPLETE_POINTS")
                    self.state="SENTINEL_SENT"
                    response=r5.SENTINEL
                    event={"prompt":"ZERO_PT_SENTINEL"}
                else:
                    ident,t,p=self.points[len(self.requested)]
                    self.requested.append(ident)
                    self.state="AWAIT_NEXT"
                    response=f"{t} {p} 0\n".encode("ascii")
                    event={"prompt":"DIAGNOSTIC_PT","id":ident}
                self.events.append({**event,"response":response.decode().strip(),
                                    "potential_fields":list(fields),
                                    "stdout_byte_offset_after_prompt":self.cursor})
                return response
            if self.state=="AWAIT_NEXT":
                raise ValueError("C03EE_UNEXPECTED_INTERACTIVE_PROMPT:"+repr(prompt))
        if self.state=="AWAIT_NEXT":
            # Fail on a complete diagnostic marker without waiting for a new PT prompt.
            if re.search(rb"\*\*(?:warning|error) ver\d+\*\*",tail,re.I):
                raise ValueError("C03EE_POINT_NATIVE_DIAGNOSTIC")
            return None
        return super().next_response(raw)


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
    readiness=verify_readiness(parent)
    print("C03EE_READINESS_REPLAY_PASS",PIN,json.dumps(readiness,sort_keys=True),flush=True)
    need(shutil.disk_usage(s2.BASE).free>=LIMITS["retained_bytes_stop_threshold"],"C03EE_DISK")
    OUT.mkdir(parents=False,exist_ok=False)
    attempts=0
    requested=0
    completed=0
    results={}
    state="C03EE_DIAGNOSTIC_FAILED_PRESERVED"
    try:
        s2.write_json(OUT/"PROVENANCE.json",{"source_sha":head,"readiness":readiness,
            "limits":LIMITS,"points":POINTS,"max_native_processes":2,"max_requested_points":6,
            "scientific_promotion":False,**c.SCOPE})
        for arm in ed.COUNTS:
            work=OUT/arm
            work.mkdir()
            roster=contract["arms"][arm]["solution_models"]
            project,norm=c.make_project(template,report,d.c.b.components(hp),contract,arm)
            library=original if arm=="ACT_ONLY" else derived
            inputs={"c03d.dat":project,"hp02ver.dat":hp,"solution_model.dat":library,
                    "perplex_option.dat":d.options_candidate(options)}
            for k,v in inputs.items():
                with (work/k).open("xb") as f:
                    f.write(v)
            s2.write_json(work/"INPUT.json",{"files_sha256":{k:hgp.sha(v) for k,v in inputs.items()},
                "normalized_conserved_moles":norm,"points":POINTS,"solution_models":roster})
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
        s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03EE_DIAGNOSTIC_BENCHMARK_MANIFEST_V1",
            "status":state,"source_sha":head,"C03ED_manifest_sha256":PIN,"files":members,
            "native_initialization_attempts":attempts,"authorized_equilibrium_solver_calls":6,
            "requested_equilibrium_points":requested,"completed_equilibrium_points":completed,
            "scientific_promotion":False,**c.SCOPE})
        print("C03EE_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"),flush=True)
    print(state)
    print("REQUESTED_EQUILIBRIUM_POINTS="+str(requested))
    print("COMPLETED_EQUILIBRIUM_POINTS="+str(completed))


if __name__=="__main__":
    main()
