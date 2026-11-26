"""C03EC R2: consolidate phase-admission evidence, no native processes."""
from __future__ import annotations
import argparse
from fractions import Fraction
import json
import re
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_native_preflight as c

d=c.d
s2=c.s2
need=c.need
a=c.b.a
PIN="86e039ce7884b846b0deeaa0700e05a26f18d426f0396daf4d74bbf5c9ef7bb5"
SOURCE="579c840b73ab730a5bad78d6bde72bd7f8f35b83"
FAILED=c.OUT
OUT=s2.BASE/"R6_THERMO_C03EC_R2_PHASE_POLICY_AUDIT_NEW01"
STATUS="C03EC_R2_STATIC_PHASE_POLICY_EVIDENCE_CAPTURED__REVIEW_REQUIRED"
H2_WARNING=c.dialogue.SI013.replace(b"Si(s)",b"H2")


def verify_r1_failure():
    rec=c.read(d.m.HERE/"c03ec_r1_failed_fair_receipt_v1.json")
    need(FAILED.is_dir() and not FAILED.is_symlink()
         and not (FAILED/"MANIFEST.json").is_symlink()
         and c.hgp.file_sha(FAILED/"MANIFEST.json")==PIN==rec["manifest_sha256"],
         "C03EC_R2_R1_PIN")
    man=c.read(FAILED/"MANIFEST.json")
    inv=d.launcher.inventory(FAILED)
    inv.pop("MANIFEST.json")
    need(inv==man["files"] and man["source_sha"]==SOURCE==rec["source_sha"]
         and man["schema"]=="R6_C03EC_NATIVE_PREFLIGHT_MANIFEST_V1"
         and man["status"]=="NATIVE_PREFLIGHT_FAILED_PRESERVED"
         and man["failed_manifest_sha256"]==c.FAILED_PIN
         and man["C03EB_manifest_sha256"]==c.PIN
         and man["native_initialization_attempts"]==1
         and man["requested_equilibrium_points"]==man["authorized_equilibrium_solver_calls"]==0
         and man["scientific_promotion"] is False
         and all(man[k]==v for k,v in c.SCOPE.items()),"C03EC_R2_R1_MANIFEST")
    work=FAILED/"ACT_ONLY"
    raw=(work/"RUN_STDOUT.log").read_bytes()
    stdin=(work/"DIALOGUE_STDIN.log").read_bytes()
    failure=c.read(FAILED/"FAILURE.json")
    dia=c.read(work/"DIALOGUE.json")
    launch=c.read(work/"LAUNCH.json")
    expected="C03EC_UNAPPROVED_INTERACTIVE_WARNING:"+repr(H2_WARNING)
    need(failure["error"]=="ValueError" and failure["message"]==expected
         and failure["native_initialization_attempts"]==1
         and failure["requested_equilibrium_points"]==0
         and dia["error"]==launch["error"]=="ValueError: "+expected
         and dia["state"]=="INITIALIZING" and dia["acknowledged_warning_codes"]==["013","013"]
         and dia["requested_equilibrium_points"]==0
         and dia["scientific_warning_acceptance"] is False
         and stdin==b"c03d\ny\ny\n" and raw.count(c.dialogue.WARNING)==3
         and c.dialogue.PT not in raw and not (FAILED/"DP_DS5_ONLY").exists(),
         "C03EC_R2_R1_DIALOGUE")
    p=c.PreflightDialogue()
    need([p.next_response(raw) for _ in range(3)]==[b"c03d\n",b"y\n",b"y\n"],
         "C03EC_R2_R1_REPLAY_PREFIX")
    try:
        p.next_response(raw)
    except ValueError as exc:
        need(str(exc)==expected,"C03EC_R2_R1_REPLAY_ERROR")
    else:
        raise ValueError("C03EC_R2_R1_REPLAY_MISSING_FAILURE")
    old=c.FAILED_OUT/"ACT_ONLY"
    for name in ("c03d.dat","hp02ver.dat","solution_model.dat","perplex_option.dat","INPUT.json"):
        need((old/name).read_bytes()==(work/name).read_bytes(),"C03EC_R2_INPUT_DRIFT:"+name)
    return {"manifest_sha256":PIN,"source_sha":SOURCE,"exact_replay":True,
            "acknowledged_species":["Si(s)","Si(s)"],"blocked_species":"H2",
            "requested_equilibrium_points":0}


def project_vector(vector, conserved, saturated):
    vec={k:Fraction(v) for k,v in vector.items() if Fraction(v)}
    cons=set(conserved)
    sat=set(saturated)
    need(not cons & sat,"C03EC_R2_OVERLAPPING_BASIS")
    outside=sorted(set(vec)-cons-sat)
    full=sum(vec.values(),Fraction(0))
    projected=sum((v for k,v in vec.items() if k in cons),Fraction(0))
    return {"coefficients":{k:str(v) for k,v in sorted(vec.items())},
            "outside_basis":outside,"full_sum":str(full),"conserved_sum":str(projected),
            "saturated_coefficients":{k:str(vec[k]) for k in sorted(sat & set(vec))},
            "nonpositive_conserved_sum":projected<=0,
            "interpretation":"STATIC_LITERAL_PROJECTION_NOT_NATIVE_ADMISSION"}


def inventory_vectors(records,makes):
    rows={}
    for name,r in sorted(records.items()):
        rows[name]={"kind":"DIRECT","eos":r["eos"],
                    **project_vector(r["coefficients"],c.ORDER,("H2O",))}
    unresolved={}
    for name in sorted(makes):
        try:
            roots=set()
            used=set()
            vector=a.resolve(name,records,{},makes,roots,used)
            rows[name]={"kind":"MAKE","roots":sorted(roots),"makes":sorted(used),
                        **project_vector(vector,c.ORDER,("H2O",))}
        except (ValueError,ZeroDivisionError) as exc:
            unresolved[name]=str(exc)
    return rows,unresolved


def reference_hits(text,name):
    # Literal token matches; not a complete native dependency parser.
    pat=re.compile(r"(?<![A-Za-z0-9_])"+re.escape(name)+r"(?![A-Za-z0-9_])")
    return [{"line":i,"text":line.strip()} for i,line in enumerate(text.splitlines(),1)
            if pat.search(line)]


def source_context(source):
    excerpts={}
    pattern=re.compile(r"\bcall\s+warn\s*\(\s*13\s*,|\bif\s*\(\s*name\.eq\.exname\(i\)|"
                       r"\bsubroutine\s+(?:rfluid|chkphi|input1)\b|"
                       r"\bcall\s+rfluid\s*\(|total amount of the commponents|"
                       r"\bhybrid_eos_h2o\b",re.I)
    for name in ("tlib.f","rlib.f","meemum.f","build.f"):
        raw=(source/"src"/name).read_bytes()
        lines=raw.decode("utf-8",errors="replace").splitlines()
        hits=[i for i,line in enumerate(lines) if pattern.search(line)]
        spans=set()
        for i in hits:
            spans.update(range(max(0,i-12),min(len(lines),i+13)))
        excerpts[name]={"sha256":c.hgp.sha(raw),"match_lines":[i+1 for i in hits],
                        "lines":[[i+1,lines[i]] for i in sorted(spans)]}
    return excerpts


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03EC_R2_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C03EC_R2_OUTPUT_EXISTS")
    old=c.audit_failed_attempt()
    failed=verify_r1_failure()
    print("C03EC_R2_BOTH_FAILED_REPLAYS_PASS",c.FAILED_PIN,PIN,flush=True)
    report,runtime,template,hp,original,derived,options,contract,records=c.parent()
    active=d.composition_audit.active_text(hp.decode())
    makes=a.equations(a.section(active,"makes"))
    rows,unresolved=inventory_vectors(records,makes)
    need(all(k in rows for k in ("Si(s)","H2","O2","H2O","iron","h2oL")),
         "C03EC_R2_FOCUS_RECORDS")
    candidates=sorted(k for k,v in rows.items() if not v["outside_basis"]
                      and v["nonpositive_conserved_sum"])
    focus=sorted(set(candidates)|{"Si(s)","H2","O2","H2O","iron","h2oL"}|set(c.EXCLUDED))
    by_arm={}
    for arm,arm_spec in contract["arms"].items():
        library=original if arm_spec["library"]=="ORIGINAL" else derived
        roster=arm_spec["solution_models"]
        blocks=d.c.b.model_blocks(library,tuple(roster))
        need(set(blocks)==set(roster) and all(blocks.values()),"C03EC_R2_MODEL_BLOCKS")
        model_hits={}
        for name in focus:
            hits={m:reference_hits(d.composition_audit.active_text(blocks[m]["text"]),name)
                  for m in roster}
            model_hits[name]={k:v for k,v in hits.items() if v}
        by_arm[arm]={"model_hits":model_hits,"roster":roster}
    make_hits={k:reference_hits(a.section(active,"makes"),k) for k in focus}
    excerpts=source_context(Path(runtime["source"]))
    payload={"schema":"R6_C03EC_R2_STATIC_PHASE_POLICY_AUDIT_V1","status":STATUS,
             "source_sha":head,"prior_failures":[old,failed],"provider_runtime":runtime,
             "conserved":list(c.ORDER),"saturated":["H2O"],"explicit_exclusions":list(c.EXCLUDED),
             "direct_and_make_vectors":rows,"unresolved_make_equations":unresolved,
             "nonpositive_conserved_sum_candidates":candidates,
             "focus_records":{k:rows[k] for k in focus if k in rows},
             "model_literal_reference_hits":by_arm,"make_literal_reference_hits":make_hits,
             "native_source_context":excerpts,"native_admission_verified":False,
             "phase_policy_authorized":False,"scientific_promotion":False,
             "additional_engine_runs":0,"authorized_equilibrium_solver_calls":0,**c.SCOPE}
    OUT.mkdir(parents=False,exist_ok=False)
    s2.write_json(OUT/"PHASE_POLICY_AUDIT.json",payload)
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03EC_R2_STATIC_PHASE_POLICY_AUDIT_MANIFEST_V1",
        "source_sha":head,"status":STATUS,"R1_failed_manifest_sha256":PIN,
        "C03EB_manifest_sha256":c.PIN,
        "files_sha256":{"PHASE_POLICY_AUDIT.json":s2.sha(OUT/"PHASE_POLICY_AUDIT.json")},
        "additional_engine_runs":0,"authorized_equilibrium_solver_calls":0,
        "scientific_promotion":False,**c.SCOPE})
    print("C03EC_R2_INVENTORY",json.dumps({"records":len(records),"makes":len(makes),
          "resolved_makes":len(makes)-len(unresolved),"unresolved_makes":unresolved},sort_keys=True))
    print("C03EC_R2_NONPOSITIVE",json.dumps(candidates))
    print("C03EC_R2_FOCUS",json.dumps(payload["focus_records"],sort_keys=True))
    print("C03EC_R2_MODEL_HITS",json.dumps({arm:{k:sorted(v) for k,v in spec["model_hits"].items() if v}
          for arm,spec in by_arm.items()},sort_keys=True))
    print("C03EC_R2_MAKE_HITS",json.dumps({k:v for k,v in make_hits.items() if v},sort_keys=True))
    for fname,context in excerpts.items():
        print("C03EC_R2_SOURCE_MATCHES",fname,context["match_lines"])
        # Print nearby warn(13) call context; full source context retained.
        for i,line in context["lines"]:
            if re.search(r"\bcall\s+warn\s*\(\s*13\s*,|total amount of the commponents",line,re.I):
                print("C03EC_R2_VER013_CONTEXT",fname,i,json.dumps(
                    [[n,l] for n,l in context["lines"] if abs(n-i)<=12]))
    print("C03EC_R2_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
    print(STATUS)
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()
