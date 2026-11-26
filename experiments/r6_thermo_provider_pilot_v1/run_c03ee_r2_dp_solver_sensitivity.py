"""C03EE-R2: replay ACT and try one bounded DP-only alternate solver diagnostic."""
from __future__ import annotations
import argparse
from decimal import Decimal
import json
import re
import shutil
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03ee_r1_subsolidus_diagnostic as r1

c=r1.c
d=c.d
s2=c.s2
need=c.need
hgp=c.hgp
prior=r1.prior
PIN="127e9799c4ecf9e050170d4f2e4b1fafcde92451c7302bdecea4815fb837c4c7"
SOURCE="96efb63330f4b99ed168c840b0ecf3eb3be0de65"
OUT=s2.BASE/"R6_THERMO_C03EE_DIAGNOSTIC_BENCHMARK_NEW03"
STATUS="C03EE_R2_DP_SOLVER_SENSITIVITY_CAPTURED__SCIENTIFIC_REVIEW_REQUIRED"
D=Decimal
TARGETS={"B01":"pre","B02":"law","B03":"Ep(HP11)"}


def interval(s):
    x=D(s.replace("D","E").replace("d","e"))
    need(x.is_finite(),"C03EE_R2_NONFINITE")
    u=D(1).scaleb(x.as_tuple().exponent)/2
    return x-u,x+u


def overlaps(a,b):
    return a[0]<=b[1] and b[0]<=a[1]


def product(a,b):
    v=[x*y for x in a for y in b]
    return min(v),max(v)


def total(items):
    return tuple(sum(x[i] for x in items) for i in (0,1))


def rows(text,start,stop):
    need(text.count(start)==1 and text.count(stop)==1,"C03EE_R2_SECTION:"+start)
    return [line.split() for line in text.split(start,1)[1].split(stop,1)[0].splitlines() if line.strip()]


def audit_point(point,norm,*,act):
    txt=point["output_text"]
    phase=rows(txt,"Phase Compositions (molar  proportions):","Phase speciation (molar proportions):")
    cols=phase[0][7:]
    need(set(cols)==set(c.ORDER)|{"H2O"} and len(cols)==10,"C03EE_R2_COLUMNS")
    instances=phase[1:]
    need(instances and all(len(x)==5+len(cols) for x in instances),"C03EE_R2_PHASE_ROWS")
    for k in (1,2,3):
        need(overlaps(total([interval(x[k]) for x in instances]),(D(100),D(100))),
             "C03EE_R2_MODAL_CLOSURE:"+str(k))
    need(all(D(x[k])>=0 for x in instances for k in (1,2,3,4)),"C03EE_R2_NEGATIVE_AMOUNT")
    bulk=rows(txt,"Bulk Composition:","Other Bulk Properties:")
    need(bulk[0]==["mol","g","wt","%","mol/kg"],"C03EE_R2_BULK_HEADER")
    b={x[0]:x[1:] for x in bulk[1:]}
    need(set(b)==set(cols) and len(bulk)==11 and all(len(x)==4 for x in b.values()),
         "C03EE_R2_BULK_ROWS")
    closure={}
    for i,name in enumerate(cols):
        summed=total([product(interval(x[4]),interval(x[5+i])) for x in instances])
        reported=interval(b[name][0])
        need(overlaps(summed,reported),"C03EE_R2_PHASE_BULK_CLOSURE:"+name)
        if name!="H2O":
            v=D(str(norm[name]))
            need(reported[0]<=v<=reported[1],"C03EE_R2_CONSERVED_INPUT_CLOSURE:"+name)
        closure[name]={"phase_sum_interval":[str(x) for x in summed],
                       "printed_bulk_interval":[str(x) for x in reported]}
    props=rows(txt,"Molar Properties and Density:","Seismic Properties:")
    system=[x for x in props if x[0]=="System"]
    need(len(system)==1 and len(system[0])==10,"C03EE_R2_SYSTEM_ROW")
    x=system[0]
    mass,g,entropy,volume,cp,alpha,beta,ratio,rho=map(D,x[1:])
    need(all(v.is_finite() for v in (mass,g,entropy,volume,cp,alpha,beta,ratio,rho))
         and min(mass,volume,cp,beta,rho)>0,"C03EE_R2_SYSTEM_PROPERTIES")
    # J/bar = 10 cm^3. Decimal intervals respect printed significant figures.
    m,v=interval(x[1]),interval(x[4])
    need(overlaps((100*m[0]/v[1],100*m[1]/v[0]),interval(x[9])),
         "C03EE_R2_DENSITY_CLOSURE")
    phases={}
    for x in instances:
        phases[x[0]]=phases.get(x[0],0)+float(x[1])
    target=TARGETS[point["id"]]
    if act:
        need(phases.get(target,0)>0,"C03EE_R2_ACT_TARGET")
        if point["id"]=="B03":
            need("Cpx(HP)" not in phases,"C03EE_R2_ACT_B03_CPX")
    return {"id":point["id"],"phase_instances":instances,"phase_wt_percent":phases,
            "target":target,"target_present":phases.get(target,0)>0,
            "bulk_closure_at_print_precision":closure,"density_kg_m3":float(rho),
            "Cp_J_kg_K":float(cp/mass*1000),"H2O_wt_percent":float(b["H2O"][2]),
            "G_J_per_printed_bulk":float(g),"scientific_promotion":False}


def verify_archive(parent):
    rec=c.read(d.m.HERE/"c03ee_r1_partial_fair_receipt_v1.json")
    archive=r1.OUT
    need(archive.is_dir() and not archive.is_symlink()
         and hgp.file_sha(archive/"MANIFEST.json")==PIN==rec["manifest_sha256"],"C03EE_R2_PIN")
    man=c.read(archive/"MANIFEST.json")
    inv=d.launcher.inventory(archive)
    inv.pop("MANIFEST.json")
    need(inv==man["files"] and man["source_sha"]==SOURCE==rec["source_sha"]
         and man["schema"]=="R6_C03EE_R1_SUBSOLIDUS_DIAGNOSTIC_MANIFEST_V1"
         and man["status"]=="C03EE_R1_DIAGNOSTIC_FAILED_PRESERVED"
         and man["C03ED_manifest_sha256"]==prior.PIN
         and man["prior_failed_manifest_sha256"]==r1.FAILED_PIN
         and man["added_exclusions"]==list(r1.LIQUID_IDS)
         and man["native_initialization_attempts"]==2
         and man["requested_equilibrium_points"]==4 and man["completed_equilibrium_points"]==3
         and all(man[k]==v for k,v in c.SCOPE.items()) and man["scientific_promotion"] is False,
         "C03EE_R2_MANIFEST")
    report,runtime,template,hp,original,derived,options,contract,records=parent
    act=[]
    for arm,lib in (("ACT_ONLY",original),("DP_DS5_ONLY",derived)):
        work=archive/arm
        roster=contract["arms"][arm]["solution_models"]
        project,norm=r1.make_subsolidus_project(template,report,d.c.b.components(hp),contract,arm)
        expected={"c03d.dat":project,"hp02ver.dat":hp,"solution_model.dat":lib,
                  "perplex_option.dat":d.options_candidate(options)}
        need(all((work/k).read_bytes()==v for k,v in expected.items()),"C03EE_R2_INPUT:"+arm)
        raw=(work/"RUN_STDOUT.log").read_bytes()
        sent=(work/"DIALOGUE_STDIN.log").read_bytes()
        dia=c.read(work/"DIALOGUE.json")
        launch=c.read(work/"LAUNCH.json")
        cap=c.read(work/"POINT_CAPTURE.json")
        p=r1.DiagnosticDialogue(arm,records,roster)
        end=len(raw) if arm=="ACT_ONLY" else dia["events"][-1]["stdout_byte_offset_after_prompt"]
        replies=[]
        while True:
            reply=p.next_response(raw[:end])
            if reply is None:
                break
            replies.append(reply)
        need(b"".join(replies)==sent and p.events==dia["events"]
             and p.completed==cap["completed"] and p.requested==cap["requested_ids"],
             "C03EE_R2_ARCHIVE_REPLAY:"+arm)
        if arm=="ACT_ONLY":
            result=c.read(work/"RESULT.json")
            need(p.requested==["B01","B02","B03"] and p.state=="SENTINEL_SENT"
                 and launch["exit_code"]==0 and launch["error"] is None
                 and result["points"]==p.completed,"C03EE_R2_ACT_COMPLETE")
            act=[audit_point(x,norm,act=True) for x in p.completed]
        else:
            tail=raw[end:].decode("utf-8",errors="replace")
            need(p.requested==["B01"] and not p.completed and p.state=="AWAIT_NEXT"
                 and launch["exit_code"]==-9 and not launch["timeout"]
                 and "SPECI2/cAmph(DP)" in tail and "Oscillating, result will be rejected." in tail
                 and "Stable phases at:" not in tail
                 and set(re.findall(r"\*\*(?:warning|error) ver(\d+)\*\*",tail))=={"093"},
                 "C03EE_R2_DP_FAILURE")
            try:
                p.next_response(raw)
            except ValueError as exc:
                need("C03EE_POINT_NATIVE_DIAGNOSTIC" in str(exc) and "ver093" in str(exc),
                     "C03EE_R2_DP_FAILURE_REPLAY")
            else:
                raise ValueError("C03EE_R2_DP_FAILURE_MISSING")
    return act


def solver_option(raw):
    text=raw.decode("utf-8")
    # Preserve every byte except one explicit solver value (or append one if default implicit).
    pat=re.compile(r"(?im)^([ \t]*minfxc_solver[ \t]+)([-+]?\d+)([ \t]*(?:\|[^\r\n]*)?)(\r?)$")
    matches=list(pat.finditer(text))
    active=[line for line in text.splitlines() if re.match(r"^\s*minfxc_solver\b",line,re.I)]
    need(len(matches)==len(active)<=1,"C03EE_R2_SOLVER_OPTION_FORMAT")
    if matches:
        m=matches[0]
        need(m[2]=="0","C03EE_R2_SOLVER_BASE_NOT_ZERO")
        out=text[:m.start(2)]+"-1"+text[m.end(2):]
    else:
        out=text+("" if text.endswith("\n") else "\n")+"MINFXC_solver -1\n"
    return out.encode("utf-8")


def verify_source(runtime):
    source=Path(runtime["source"])/"src"
    r=(source/"rlib.f").read_bytes()
    t=(source/"tlib.f").read_bytes()
    need(hgp.sha(r)=="8cd5df49273978b737cc6fd4fc5db9dcd09af4e1219c77717e49c9ecfd68cbd1"
         and hgp.sha(t)=="426090ce28f14b81c3921e44b695c0adc13b0ba05c3dc15ffef117937b9cfa77",
         "C03EE_R2_SOURCE_PIN")
    rr=r.decode().lower()
    tt=t.decode().lower()
    need(re.search(r"if \(iopt\(37\)\.lt\.0\) then\s*(?:c[^\n]*\n\s*)*call minfxc \(g,id,minfx\)",rr)
         and "call spewrn (id,102,itic,iwarn,.true.,'speci2')" in rr
         and "key.eq.'minfxc_solver'" in tt and "read (strg,*) iopt(37)" in tt,
         "C03EE_R2_SOLVER_SOURCE")
    return {"rlib_sha256":hgp.sha(r),"tlib_sha256":hgp.sha(t),
            "option":"MINFXC_solver","candidate":-1,"classification":"ALTERNATE_NUMERICAL_SOLVER_SENSITIVITY"}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    ap.add_argument("--dp-only",action="store_true",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03EE_R2_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C03EE_R2_OUTPUT_EXISTS")
    parent=c.parent()
    report,runtime,template,hp,original,derived,options,contract,records=parent
    prior.verify_readiness(parent)
    r1.verify_failure(parent)
    r1.liquid_policy(hp,records,original,derived,contract,Path(runtime["source"]))
    act=verify_archive(parent)
    print("C03EE_R2_ACT_ARCHIVE_REPLAY_PASS",PIN,flush=True)
    for x in act:
        print("C03EE_R2_ACT_AUDIT",json.dumps(x,sort_keys=True),flush=True)
    source=verify_source(runtime)
    print("C03EE_R2_SOLVER_SOURCE",json.dumps(source),flush=True)
    work_old=r1.OUT/"DP_DS5_ONLY"
    inputs={k:(work_old/k).read_bytes() for k in ("c03d.dat","hp02ver.dat","solution_model.dat","perplex_option.dat")}
    original_opt=inputs["perplex_option.dat"]
    inputs["perplex_option.dat"]=solver_option(original_opt)
    roster=contract["arms"]["DP_DS5_ONLY"]["solution_models"]
    norm=c.read(work_old/"INPUT.json")["normalized_conserved_moles"]
    need(shutil.disk_usage(s2.BASE).free>=r1.LIMITS["retained_bytes_stop_threshold"],"C03EE_R2_DISK")
    OUT.mkdir(parents=False,exist_ok=False)
    work=OUT/"DP_DS5_ONLY_MINFXC"
    work.mkdir()
    protocol=r1.DiagnosticDialogue("DP_DS5_ONLY",records,roster)
    state="C03EE_R2_DP_SENSITIVITY_FAILED_PRESERVED"
    attempts=0
    try:
        s2.write_json(OUT/"ACT_ARCHIVE_AUDIT.json",{"source_manifest":PIN,"points":act,
            "scientific_promotion":False})
        s2.write_json(OUT/"PROVENANCE.json",{"source_sha":head,"source":source,"limits":r1.LIMITS,
            "old_options_sha256":hgp.sha(original_opt),"new_options_sha256":hgp.sha(inputs["perplex_option.dat"]),
            "historical_requested_points":5,"historical_completed_points":3,
            "max_additional_requests":3,"max_additional_processes":1,**c.SCOPE})
        for k,v in inputs.items():
            with (work/k).open("xb") as f:
                f.write(v)
        s2.write_json(work/"INPUT.json",{"normalized_conserved_moles":norm,"solution_models":roster,
            "points":prior.POINTS,"files_sha256":{k:hgp.sha(v) for k,v in inputs.items()}})
        need(hgp.file_sha(runtime["binary"])==runtime["binary_sha256"]
             and d.launcher.retained_bytes(OUT)<r1.LIMITS["retained_bytes_stop_threshold"],
             "C03EE_R2_LAUNCH_GUARD")
        attempts=1
        telemetry=r1.launcher.launch_dialogue([Path(runtime["binary"])],work,r1.LIMITS,
                    protocol_factory=lambda:protocol)
        raw=(work/"RUN_STDOUT.log").read_bytes()
        replay=r1.DiagnosticDialogue("DP_DS5_ONLY",records,roster)
        replies=[]
        while True:
            reply=replay.next_response(raw)
            if reply is None:
                break
            replies.append(reply)
        need(b"".join(replies)==(work/"DIALOGUE_STDIN.log").read_bytes()
             and replay.events==protocol.events and replay.completed==protocol.completed
             and replay.state=="SENTINEL_SENT" and len(replay.completed)==3,
             "C03EE_R2_DP_REPLAY")
        audit=[audit_point(x,norm,act=False) for x in protocol.completed]
        s2.write_json(work/"RESULT.json",{"points":protocol.completed,"audit":audit,"launch":telemetry,
                     "scientific_promotion":False})
        for x in audit:
            print("C03EE_R2_DP_AUDIT",json.dumps(x,sort_keys=True),flush=True)
        state=STATUS
    except BaseException as exc:
        s2.write_json(OUT/"FAILURE.json",{"error":type(exc).__name__,"message":str(exc),
            "requested_ids":protocol.requested,"completed_ids":[x["id"] for x in protocol.completed]})
        raise
    finally:
        s2.write_json(work/"POINT_CAPTURE.json",{"requested_ids":protocol.requested,
            "completed":protocol.completed,"scientific_acceptance":False})
        if (work/"RUN_STDOUT.log").is_file():
            print("C03EE_R2_NATIVE_TAIL",(work/"RUN_STDOUT.log").read_bytes()[protocol.cursor:][-12000:].decode("utf-8",errors="replace"),flush=True)
        for x in protocol.completed:
            print("C03EE_R2_DP_POINT",x["id"],x["output_text"],flush=True)
        members=d.launcher.inventory(OUT)
        s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03EE_R2_DP_SOLVER_SENSITIVITY_MANIFEST_V1",
            "status":state,"source_sha":head,"R1_manifest_sha256":PIN,"files":members,
            "native_initialization_attempts":attempts,"authorized_equilibrium_solver_calls":3,
            "requested_equilibrium_points":len(protocol.requested),
            "completed_equilibrium_points":len(protocol.completed),"scientific_promotion":False,**c.SCOPE})
        print("C03EE_R2_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"),flush=True)
    print(state)
    print("ADDITIONAL_REQUESTED_POINTS="+str(len(protocol.requested)))
    print("ADDITIONAL_COMPLETED_POINTS="+str(len(protocol.completed)))


if __name__=="__main__":
    main()
