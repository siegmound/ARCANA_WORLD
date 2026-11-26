"""C03F: four conditional ARCANA closed-bulk research equilibria, no promotion."""
from __future__ import annotations
import argparse
from decimal import Decimal as D
import json
import re
import shutil
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03f_r1_native_preflight as r
from experiments.r6_thermo_provider_pilot_v1 import run_c03ee_r2_dp_solver_sensitivity as audit
from experiments.r6_thermo_provider_pilot_v1 import run_c03ee_diagnostic_benchmark as ref

old=r.old
c=r.c
d=r.d
s2=r.s2
need=r.need
hgp=r.hgp
PIN="ea0782292000ac40a2551aa41d41d7a3d4f45df5e7e7c1ac0fb69ccd065b44d9"
SOURCE="c7a93562867df6877a51f0424b50a84c4af916f7"
OUT=s2.BASE/"R6_THERMO_C03F_CLOSED_BULK_CAMPAIGN_NEW01"
STATUS="C03F_FOUR_CLOSED_BULK_RESEARCH_EQUILIBRIA_AUDITED__SCIENTIFIC_REVIEW_REQUIRED"
LIMITS={**old.LIMITS,"walltime_s":180}
NAMES=(r.BASE,r.WET)
MARK=re.compile(rb"\*\*(?:warning|error) ver\d+\*\*",re.I)


def replay_preflight(parent):
    plans,inputs=old.verify_design(parent)
    report,runtime,template,hp,original,derived,options,contract,records=parent
    expected=r.corrected_reference(plans,runtime)
    base=r.replay_base(plans,inputs,records,expected)
    archive=r.OUT
    rec=c.read(d.m.HERE/"c03fn_r1_fair_receipt_v1.json")
    need(archive.is_dir() and not archive.is_symlink()
         and not (archive/"MANIFEST.json").is_symlink()
         and hgp.file_sha(archive/"MANIFEST.json")==PIN==rec["manifest_sha256"],
         "C03FC_PREFLIGHT_PIN")
    man=c.read(archive/"MANIFEST.json")
    inv=d.launcher.inventory(archive)
    inv.pop("MANIFEST.json")
    need(inv==man["files"] and man["source_sha"]==SOURCE==rec["source_sha"]
         and rec["exit"]==0 and rec["regression_passed"]==185
         and man["schema"]=="R6_C03FN_R1_NATIVE_PREFLIGHT_MANIFEST_V1"
         and man["status"]==r.STATUS and man["C03F_design_manifest_sha256"]==old.PIN
         and man["base_archive_manifest"]==r.PIN
         and man["native_initialization_attempts"]==1
         and man["historical_native_initialization_attempts"]==1
         and man["requested_equilibrium_points"]==man["authorized_equilibrium_solver_calls"]==0
         and man["scientific_promotion"] is False
         and all(man[k]==v for k,v in c.SCOPE.items()),"C03FC_PREFLIGHT_MANIFEST")
    work=archive/r.WET
    need(not (archive/r.BASE).exists()
         and c.read(work/"INPUT.json")==plans[r.WET]
         and all((work/k).read_bytes()==v for k,v in inputs[r.WET].items()),
         "C03FC_WET_INPUT")
    wet=r.inspect_work(work,plans[r.WET],records,expected[r.WET])
    need(base==c.read(archive/"BASE_REPLAY.json")
         and wet==c.read(work/"READBACK.json")
         and c.read(archive/"RESULT.json")=={"observations":{r.BASE:base,r.WET:wet},
            "base_archive_manifest":r.PIN,"requested_equilibrium_points":0,
            "scientific_promotion":False,**c.SCOPE},"C03FC_PREFLIGHT_REPLAY")
    return plans,inputs,expected,{r.BASE:base,r.WET:wet}


def point_spec(plan):
    points=plan["points"]
    need(len(points)==2 and len({p["id"] for p in points})==2
         and {p["source_point"]["parent_node_id"] for p in points}=={35304,36026},
         "C03FC_POINT_SCOPE")
    for p in points:
        t=D(str(p["T_K"]))
        pressure=D(str(p["P_bar_candidate"]))
        need(t.is_finite() and pressure.is_finite() and min(t,pressure)>0
             and p["source_point"]["absolute_pressure_pa"] is None
             and p["source_point"]["pressure_semantics"]=="HYPOTHETICAL_COMPARATIVE_ONLY",
             "C03FC_POINT_AUTHORITY")
    return tuple(points)


def capture(segment,point):
    ident=point["id"]
    txt=segment.decode("utf-8",errors="strict")
    need(MARK.search(segment) is None,"C03FC_POINT_NATIVE_DIAGNOSTIC:"+ident)
    need(txt.count("Stable phases at:")==1 and txt.count("Phase Compositions (")==1,
         "C03FC_POINT_OUTPUT_MISSING:"+ident)
    vals={}
    for field in old.FIELDS:
        m=re.findall(r"(?m)^\s*"+re.escape(field)+r"\s*=\s*("+ref.NUMBER+r")\s*$",txt)
        need(len(m)==1,"C03FC_POINT_FIELD:"+ident+":"+field)
        vals[field]=D(m[0].replace("D","E").replace("d","e"))
    need(abs(vals["T(K)"]-D(str(point["T_K"])))<=D("0.01")
         and abs(vals["P(bar)"]-D(str(point["P_bar_candidate"])))<=D("0.1"),
         "C03FC_POINT_READBACK:"+ident)
    return {"id":ident,"source_point":point["source_point"],
            "native_potential_readback":{k:str(v) for k,v in vals.items()},
            "stdout_sha256":hgp.sha(segment),"stdout_bytes":len(segment),
            "output_text":txt,"scientific_acceptance":False}


def number(s):
    v=D(str(s).replace("D","E").replace("d","e"))
    need(v.is_finite(),"C03FC_NONFINITE")
    return v


def audit_closed(point,norm):
    # Same native tables/printed-precision arithmetic as C03EE-R2, but
    # all ten components are conserved. No terrestrial target phase requirement.
    txt=point["output_text"]
    phase=audit.rows(txt,"Phase Compositions (molar  proportions):","Phase speciation (molar proportions):")
    need(len(phase)>1,"C03FC_PHASE_ROWS")
    cols=phase[0][7:]
    need(len(cols)==10 and set(cols)==set(c.ORDER)|{"H2O"}
         and set(norm)==set(cols),"C03FC_COLUMNS")
    instances=phase[1:]
    need(all(len(x)==5+len(cols) for x in instances),"C03FC_PHASE_ROWS")
    for row in instances:
        for v in row[1:]:
            number(v)
        need(all(number(row[k])>=0 for k in (1,2,3,4)),"C03FC_NEGATIVE_AMOUNT")
    for k in (1,2,3):
        need(audit.overlaps(audit.total([audit.interval(x[k]) for x in instances]),(D(100),D(100))),
             "C03FC_MODAL_CLOSURE:"+str(k))
    bulk=audit.rows(txt,"Bulk Composition:","Other Bulk Properties:")
    need(len(bulk)==11 and bulk[0]==["mol","g","wt","%","mol/kg"]
         and all(len(x)==5 for x in bulk[1:]),"C03FC_BULK_ROWS")
    b={x[0]:x[1:] for x in bulk[1:]}
    need(set(b)==set(cols),"C03FC_BULK_COLUMNS")
    closure={}
    for i,name in enumerate(cols):
        for v in b[name]:
            number(v)
        summed=audit.total([audit.product(audit.interval(x[4]),audit.interval(x[5+i])) for x in instances])
        reported=audit.interval(b[name][0])
        v=number(norm[name])
        need(audit.overlaps(summed,reported),"C03FC_PHASE_BULK_CLOSURE:"+name)
        need(reported[0]<=v<=reported[1],"C03FC_CONSERVED_INPUT_CLOSURE:"+name)
        # Stronger: phase-derived interval must itself admit the pinned input.
        need(summed[0]<=v<=summed[1],"C03FC_PHASE_INPUT_CLOSURE:"+name)
        closure[name]={"input_moles":str(v),"phase_sum_interval":[str(x) for x in summed],
                       "printed_bulk_interval":[str(x) for x in reported]}
    props=audit.rows(txt,"Molar Properties and Density:","Seismic Properties:")
    system=[x for x in props if x[0]=="System"]
    need(len(system)==1 and len(system[0])==10,"C03FC_SYSTEM_ROW")
    x=system[0]
    mass,g,entropy,volume,cp,alpha,beta,ratio,rho=map(number,x[1:])
    need(min(mass,volume,cp,beta,rho)>0,"C03FC_SYSTEM_PROPERTIES")
    m,v=audit.interval(x[1]),audit.interval(x[4])
    need(v[0]>0 and audit.overlaps((100*m[0]/v[1],100*m[1]/v[0]),audit.interval(x[9])),
         "C03FC_DENSITY_CLOSURE")
    phases={}
    for x in instances:
        phases[x[0]]=phases.get(x[0],0)+float(number(x[1]))
    need(not set(phases)&set(r.design.r1.LIQUID_IDS),"C03FC_EXCLUDED_LIQUID_PRESENT")
    return {"id":point["id"],"phase_instances":instances,"phase_wt_percent":phases,
            "bulk_closure_at_print_precision":closure,"native_bulk_readback_verified":True,
            "density_kg_m3":float(rho),"Cp_J_kg_K":float(cp/mass*1000),
            "H2O_wt_percent":float(number(b["H2O"][2])),
            "G_J_per_printed_bulk":float(g),"scientific_promotion":False}


class CampaignDialogue(old.ClosedDialogue):
    policy="C03FC_CLOSED_BULK_TWO_PINNED_PT_THEN_ZERO_SENTINEL"

    def __init__(self,plan,records,expected,preflight):
        super().__init__()
        self.plan=plan
        self.records=records
        self.expected=expected
        self.preflight=preflight
        self.points=point_spec(plan)
        self.requested=[]
        self.completed=[]
        self.audits=[]

    def next_response(self,raw):
        tail=raw[self.cursor:]
        if self.state in ("AWAIT_NEXT","SENTINEL_SENT"):
            marker=MARK.search(tail)
            need(marker is None,"C03FC_POINT_NATIVE_DIAGNOSTIC:"+
                 tail[marker.start():][:2000].decode(errors="replace") if marker else "C03FC_POINT_NATIVE_DIAGNOSTIC")
        hits=[(tail.find(p),p) for p in old.dialogue.PROMPTS if p in tail]
        if hits:
            pos,prompt=min(hits,key=lambda x:x[0])
            if prompt==old.dialogue.PT:
                end=tail.find(b"\n",pos)
                if end<0:
                    return None
                fields=tuple(tail[pos+len(prompt):end].decode("ascii").split())
                need(fields==old.FIELDS and self.state in ("AWAIT_PT","AWAIT_NEXT"),
                     "C03FC_UNEXPECTED_PT")
                if self.state=="AWAIT_PT":
                    # Virtual zero-PT replay of actual initialization prefix only.
                    # No sentinel is transmitted here; this validates the same header.
                    header=raw[:self.cursor+end+1]
                    probe=old.ClosedDialogue()
                    replies=[]
                    while True:
                        reply=probe.next_response(header)
                        if reply is None:
                            break
                        replies.append(reply)
                    need(probe.state=="SENTINEL_SENT" and probe.events[:-1]==self.events
                         and probe.acknowledged==self.acknowledged,
                         "C03FC_INIT_DIALOGUE_DRIFT")
                    virtual={"events":probe.events,"state":probe.state,
                             "acknowledged_warning_codes":probe.acknowledged,
                             "scientific_warning_acceptance":False}
                    observed=old.inspect(header,b"",b"".join(replies),virtual,
                                 self.plan["solution_models"],self.records,self.expected)
                    need(observed["native_model_details"]==self.preflight["native_model_details"]
                         and observed["warning_counts"]==self.preflight["warning_counts"],
                         "C03FC_INITIALIZATION_DRIFT")
                else:
                    need(len(self.requested)==len(self.completed)+1,"C03FC_POINT_SEQUENCE")
                    result=capture(tail[:pos],self.points[len(self.completed)])
                    self.completed.append(result)
                    # Stop before requesting another equilibrium if conservation fails.
                    self.audits.append(audit_closed(result,self.plan["normalized_moles"]))
                self.cursor+=end+1
                if len(self.requested)==len(self.points):
                    need(len(self.completed)==len(self.audits)==len(self.points),"C03FC_INCOMPLETE")
                    self.state="SENTINEL_SENT"
                    response=old.SENTINEL
                    event={"prompt":"ZERO_PT_SENTINEL"}
                else:
                    point=self.points[len(self.requested)]
                    self.requested.append(point["id"])
                    self.state="AWAIT_NEXT"
                    response=(format(D(str(point["T_K"])),"f")+" "+
                              format(D(str(point["P_bar_candidate"])),"f")+"\n").encode("ascii")
                    event={"prompt":"RESEARCH_PT","id":point["id"]}
                self.events.append({**event,"response":response.decode().strip(),
                   "potential_fields":list(fields),"stdout_byte_offset_after_prompt":self.cursor})
                return response
            need(self.state not in ("AWAIT_NEXT","SENTINEL_SENT"),
                 "C03FC_UNEXPECTED_INTERACTIVE_PROMPT:"+repr(prompt))
        if self.state in ("AWAIT_NEXT","SENTINEL_SENT"):
            return None
        return super().next_response(raw)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    ap.add_argument("--research-four-only",action="store_true",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03FC_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C03FC_OUTPUT_EXISTS")
    parent=c.parent()
    r.design.r1.prior.verify_readiness(parent)
    r.design.r1.verify_failure(parent)
    plans,inputs,expected,preflight=replay_preflight(parent)
    runtime=parent[1]
    records=parent[-1]
    for name in NAMES:
        point_spec(plans[name])
    need(len({p["id"] for name in NAMES for p in plans[name]["points"]})==4,"C03FC_UNIQUE_POINTS")
    need(shutil.disk_usage(s2.BASE).free>=LIMITS["retained_bytes_stop_threshold"],"C03FC_DISK")
    print("C03FC_PREFLIGHT_REPLAY_PASS",PIN,flush=True)
    OUT.mkdir(parents=False,exist_ok=False)
    attempts=requested=completed=audited=0
    results={}
    state="C03FC_FAILED_PRESERVED"
    try:
        s2.write_json(OUT/"PROVENANCE.json",{"source_sha":head,"preflight_manifest":PIN,
             "design_manifest":old.PIN,"limits":LIMITS,"runtime":runtime,
             "max_native_processes":2,"max_requested_points":4,
             "pressure_semantics":"HYPOTHETICAL_COMPARATIVE_ONLY",
             "boundary":"CLOSED_BULK_NO_BUFFER_NO_SATURATION",**c.SCOPE})
        s2.write_json(OUT/"PREFLIGHT_REPLAY.json",preflight)
        for name in NAMES:
            work=OUT/name
            work.mkdir()
            for k,v in inputs[name].items():
                with (work/k).open("xb") as f:
                    f.write(v)
            s2.write_json(work/"INPUT.json",plans[name])
            need(d.launcher.retained_bytes(OUT)<LIMITS["retained_bytes_stop_threshold"]
                 and hgp.file_sha(runtime["binary"])==runtime["binary_sha256"],"C03FC_LAUNCH_GUARD")
            protocol=CampaignDialogue(plans[name],records,expected[name],preflight[name])
            attempts+=1
            try:
                telemetry=ref.launcher.launch_dialogue([Path(runtime["binary"])],work,LIMITS,
                            protocol_factory=lambda:protocol)
            finally:
                requested+=len(protocol.requested)
                completed+=len(protocol.completed)
                audited+=len(protocol.audits)
                s2.write_json(work/"POINT_CAPTURE.json",{"requested_ids":protocol.requested,
                    "completed":protocol.completed,"audits":protocol.audits,"scientific_acceptance":False})
                if (work/"RUN_STDOUT.log").is_file():
                    print("C03FC_NATIVE_TAIL",name,
                          (work/"RUN_STDOUT.log").read_bytes()[protocol.cursor:][-12000:].decode(errors="replace"),flush=True)
                for x in protocol.completed:
                    print("C03FC_POINT",name,x["id"],x["output_text"],flush=True)
                for x in protocol.audits:
                    print("C03FC_AUDIT",name,json.dumps(x,sort_keys=True),flush=True)
            raw=(work/"RUN_STDOUT.log").read_bytes()
            replay=CampaignDialogue(plans[name],records,expected[name],preflight[name])
            replies=[]
            while True:
                reply=replay.next_response(raw)
                if reply is None:
                    break
                replies.append(reply)
            dia=c.read(work/"DIALOGUE.json")
            need(b"".join(replies)==(work/"DIALOGUE_STDIN.log").read_bytes()
                 and replay.events==protocol.events==dia["events"]
                 and replay.completed==protocol.completed and replay.audits==protocol.audits
                 and replay.state==dia["state"]=="SENTINEL_SENT"
                 and dia["requested_ids"]==protocol.requested
                 and dia["completed_ids"]==[x["id"] for x in protocol.completed]
                 and dia["scientific_warning_acceptance"] is False
                 and telemetry["exit_code"]==0 and telemetry["error"] is None
                 and not telemetry["timeout"],"C03FC_FULL_REPLAY:"+name)
            result={"points":protocol.completed,"audit":protocol.audits,"launch":telemetry,
                    "scientific_promotion":False}
            s2.write_json(work/"RESULT.json",result)
            results[name]=result
            print("C03FC_RECIPE_COMPLETE",name,flush=True)
        need(requested==completed==audited==4 and attempts==2,"C03FC_TOTAL")
        s2.write_json(OUT/"RESULT.json",{"recipes":results,"requested_equilibrium_points":requested,
             "completed_equilibrium_points":completed,"audited_equilibrium_points":audited,
             "scientific_promotion":False,**c.SCOPE})
        state=STATUS
    except BaseException as exc:
        s2.write_json(OUT/"FAILURE.json",{"error":type(exc).__name__,"message":str(exc),
            "requested_equilibrium_points":requested,"completed_equilibrium_points":completed,
            "audited_equilibrium_points":audited,"native_initialization_attempts":attempts})
        raise
    finally:
        s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03F_CLOSED_BULK_CAMPAIGN_MANIFEST_V1",
             "source_sha":head,"status":state,"preflight_manifest_sha256":PIN,
             "design_manifest_sha256":old.PIN,"files":d.launcher.inventory(OUT),
             "native_initialization_attempts":attempts,"authorized_equilibrium_solver_calls":4,
             "requested_equilibrium_points":requested,"completed_equilibrium_points":completed,
             "audited_equilibrium_points":audited,"scientific_promotion":False,**c.SCOPE})
        print("C03FC_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"),flush=True)
    print(state)
    print("REQUESTED_EQUILIBRIUM_POINTS="+str(requested))
    print("COMPLETED_EQUILIBRIUM_POINTS="+str(completed))
    print("AUDITED_EQUILIBRIUM_POINTS="+str(audited))


if __name__=="__main__":
    main()
