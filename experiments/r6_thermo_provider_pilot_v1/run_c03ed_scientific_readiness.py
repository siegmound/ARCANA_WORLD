"""C03E-D: offline native evidence replay and scientific readiness review."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_r5_native_preflight as r5
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_native_preflight as c
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_r2_phase_policy_audit as r2

d=c.d
s2=c.s2
need=c.need
hgp=c.hgp
PIN="d0da7aa70e93a5996d4a7922045f41ff644192592df76388958fbddacb8ae7a8"
SOURCE="38dc5258020fcdd4a25bf1f4f037334e87d02b01"
OUT=s2.BASE/"R6_THERMO_C03ED_SCIENTIFIC_READINESS_NEW01"
STATUS="C03ED_NATIVE_EVIDENCE_REPLAYED__SCIENTIFIC_REVIEW_REQUIRED"
COUNTS={"ACT_ONLY":1123,"DP_DS5_ONLY":10957}
AMPH={"ACT_ONLY":("Act(M)",52),"DP_DS5_ONLY":("cAmph(DP)",9886)}
SPECIES=["Si(s)","Si(s)","H2","Si(s)"]
WARNINGS=["013"]*4+["099"]+["114"]*6
MISSING={"Chl(W)":["mnchl"],"Bio(TCC)":["mnbi"],"O(HP)":["teph","fran"],
         "IlGkPy":["pnt"],"Cpx(HP)":["esn","ccrts"],"Stlp(M)":["mnsp"]}
UNKNOWN=("fran","esn","ccrts")


def warning_context(raw,code):
    lines=raw.decode("utf-8",errors="replace").splitlines()
    pat=re.compile(r"\*\*warning ver"+re.escape(code)+r"\*\*",re.I)
    return [{"line":i+1,"lines":lines[max(0,i-3):i+12]}
            for i,line in enumerate(lines) if pat.search(line)]


def summarize_counts(result,arm):
    rows=result["native_model_details"]["pseudocompound_reports"]
    counts={x["model"]:x["count"] for x in rows}
    need(len(rows)==len(counts)==17 and sum(counts.values())==COUNTS[arm],
         "C03ED_COUNT_DRIFT:"+arm)
    name,count=AMPH[arm]
    need(counts.pop(name)==count,"C03ED_AMPHIBOLE_COUNT:"+arm)
    return counts


def classify_missing(records,models,hp):
    active=d.composition_audit.active_text(hp.decode())
    makes=r2.a.equations(r2.a.section(active,"makes"))
    result={}
    for model,names in MISSING.items():
        block=models[model]["text"]
        for name in names:
            direct=records.get(name)
            result[name]={"model":model,"direct_record":direct,
                          "global_make":makes.get(name),
                          "active_model_references":r2.reference_hits(
                              d.composition_audit.active_text(block),name),
                          "raw_model_references":r2.reference_hits(block,name),
                          "hp02_active_references":r2.reference_hits(active,name),
                          "classification":("MNO_OUTSIDE_REDUCED_BASIS" if direct and
                              direct["outside_active_components"]==["MNO"] else
                              "SOURCE_REVIEW_REQUIRED")}
            if name in UNKNOWN:
                need(result[name]["classification"]=="SOURCE_REVIEW_REQUIRED",
                     "C03ED_UNEXPECTED_CLASSIFICATION:"+name)
    return result


def source_context(source):
    # Excerpts from actual installed provider, not floating upstream main.
    patterns={
        "flib.f":r"subroutine\s+rfluid\b|subroutine\s+.*cork\b|ifug\.eq\.5|cork holland|eoscmp\(|vname\(3\)|\bcall\s+(?:cork|hcork|corkh2o)\b",
        "fluids.f":r"ifug\.eq\.5|ifug\.le\.2|vname\(3\)|\bifct\b|\bcall\s+.*cork",
        "tlib.f":r"subroutine\s+(?:input1|chkphi|outtit)\b|call\s+rfluid\s*\(|saturated phase components|components with unconstrained potentials|saturated or buffered components|if\s*\(name\.eq\.exname\(i\)|call\s+warn\s*\(\s*99\s*,",
        "meemum.f":r"\bcall\s+(?:outtit|meemum|calpr0)\b|read\s*\(\*,\*,iostat=ier\)|v\(1\)\.eq\.0d0",
        "rlib.f":r"\bcall\s+warn\s*\(\s*(?:99|114)\s*,",
        "build.f":r"ifug|saturated phase component",
    }
    result={}
    for name,pattern in patterns.items():
        raw=(source/"src"/name).read_bytes()
        lines=raw.decode("utf-8",errors="replace").splitlines()
        hits=[i for i,line in enumerate(lines) if re.search(pattern,line,re.I)]
        span={j for i in hits for j in range(max(0,i-8),min(len(lines),i+9))}
        result[name]={"sha256":hgp.sha(raw),"matches":[i+1 for i in hits],
                      "lines":[[i+1,lines[i]] for i in sorted(span)]}
    return result


def replay_archive(report,runtime,template,hp,original,derived,options,contract,records):
    rec=c.read(d.m.HERE/"c03ec_r5_fair_receipt_v1.json")
    archive=r5.OUT
    need(archive.is_dir() and not archive.is_symlink()
         and not (archive/"MANIFEST.json").is_symlink()
         and hgp.file_sha(archive/"MANIFEST.json")==PIN==rec["manifest_sha256"],
         "C03ED_MANIFEST_PIN")
    man=c.read(archive/"MANIFEST.json")
    inv=d.launcher.inventory(archive)
    inv.pop("MANIFEST.json")
    need(inv==man["files"] and man["source_sha"]==SOURCE==rec["source_sha"]
         and man["schema"]=="R6_C03EC_R5_NATIVE_PREFLIGHT_MANIFEST_V1"
         and man["status"]==r5.STATUS==rec["status"] and rec["exit"]==0
         and man["C03EB_manifest_sha256"]==c.PIN
         and man["failed_manifest_sha256"]==c.FAILED_PIN
         and man["r1_failed_manifest_sha256"]==r2.PIN
         and man["r2_audit_manifest_sha256"]==r5.R2_PIN
         and man["r3_failed_manifest_sha256"]==r5.R3_PIN
         and man["r4_failed_manifest_sha256"]==r5.R4_PIN
         and man["sentinel_fields"]==list(r5.PT_FIELDS)
         and man["native_initialization_attempts"]==2
         and man["requested_equilibrium_points"]==man["authorized_equilibrium_solver_calls"]==0
         and man["scientific_promotion"] is False
         and all(man[k]==v for k,v in c.SCOPE.items()),"C03ED_MANIFEST")
    archived=c.read(archive/"RESULT.json")
    need(archived["native_initialization_attempts"]==2
         and archived["requested_equilibrium_points"]==0
         and archived["campaign_authorized"] is False
         and set(archived["observations"])==set(COUNTS),"C03ED_RESULT")
    masses=d.c.b.components(hp)
    observations={}
    common={}
    for arm in COUNTS:
        work=archive/arm
        roster=contract["arms"][arm]["solution_models"]
        project,norm=c.make_project(template,report,masses,contract,arm)
        library=original if arm=="ACT_ONLY" else derived
        expected={"c03d.dat":project,"hp02ver.dat":hp,"solution_model.dat":library,
                  "perplex_option.dat":d.options_candidate(options)}
        need(all((work/k).read_bytes()==v for k,v in expected.items()),"C03ED_INPUT_DRIFT:"+arm)
        inp=c.read(work/"INPUT.json")
        need(inp["files_sha256"]=={k:hgp.sha(v) for k,v in expected.items()}
             and inp["normalized_conserved_moles"]==norm and inp["solution_models"]==roster
             and inp["saturated_phase_components"]==["H2O"]
             and inp["excluded_phases"]==list(c.EXCLUDED)
             and inp["requested_equilibrium_points"]==0,"C03ED_INPUT_METADATA:"+arm)
        raw=(work/"RUN_STDOUT.log").read_bytes()
        prn=work/"c03d.prn"
        printed=prn.read_bytes() if prn.is_file() else b""
        result=c.inspect_native(raw,printed,roster,records)
        result["dialogue"]=c.read(work/"DIALOGUE.json")
        result["acknowledged_species"]=[e["species"] for e in result["dialogue"]["events"] if "species" in e]
        r5.verify_readback(raw,(work/"DIALOGUE_STDIN.log").read_bytes(),result)
        need(result==c.read(work/"READBACK.json")==archived["observations"][arm]
             and result["acknowledged_species"]==SPECIES
             and result["warning_codes"]==WARNINGS
             and result["checks"]["all_requested_included"]
             and result["checks"]["pseudocompound_reconciliation"]
             and result["pseudocompound_sum"]==COUNTS[arm]
             and result["requested_equilibrium_points"]==0,"C03ED_READBACK_DRIFT:"+arm)
        missing={x["model"]:[v["endmember"] for v in x["endmembers"]]
                 for x in result["native_model_details"]["missing_endmember_reports"]}
        need(missing==MISSING,"C03ED_MISSING_DRIFT:"+arm)
        common[arm]=summarize_counts(result,arm)
        context=warning_context(raw,"099")
        need(len(context)==1,"C03ED_VER099_COUNT:"+arm)
        observations[arm]={"readback":result,"warning099":context,
                          "prn_bytes":len(printed),"prn_text":printed.decode("utf-8",errors="replace"),
                          "project_sha256":hgp.sha(project)}
    need(common["ACT_ONLY"]==common["DP_DS5_ONLY"]
         and sum(common["ACT_ONLY"].values())==1071,"C03ED_COMMON_MODEL_COUNT_DRIFT")
    return observations,common["ACT_ONLY"]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03ED_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C03ED_OUTPUT_EXISTS")
    report,runtime,template,hp,original,derived,options,contract,records=c.parent()
    observations,common=replay_archive(report,runtime,template,hp,original,derived,options,contract,records)
    print("C03ED_R5_ARCHIVE_REPLAY_PASS",PIN,flush=True)
    blocks=d.c.b.model_blocks(original,tuple(MISSING))
    need(set(blocks)==set(MISSING) and all(blocks.values()),"C03ED_MODEL_BLOCKS")
    missing=classify_missing(records,blocks,hp)
    sources=source_context(Path(runtime["source"]))
    payload={"schema":"R6_C03ED_SCIENTIFIC_READINESS_V1","status":STATUS,
             "source_sha":head,"R5_manifest_sha256":PIN,"provider_runtime":runtime,
             "observations":observations,"common_model_counts":common,
             "missing_endmember_evidence":missing,"native_source_context":sources,
             "boundary":{"conserved":list(c.ORDER),"saturated":["H2O"],
                         "potential_fields":list(r5.PT_FIELDS),"candidate_Y_CO2":0,
                         "pure_water_semantics_qualified":False,"positive_no_buffer_evidence":False},
             "full_native_phase_admission_verified":False,"scientific_promotion":False,
             "additional_engine_runs":0,"authorized_equilibrium_solver_calls":0,**c.SCOPE}
    OUT.mkdir(parents=False,exist_ok=False)
    s2.write_json(OUT/"SCIENTIFIC_READINESS.json",payload)
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03ED_SCIENTIFIC_READINESS_MANIFEST_V1",
        "status":STATUS,"source_sha":head,"R5_manifest_sha256":PIN,
        "files_sha256":{"SCIENTIFIC_READINESS.json":s2.sha(OUT/"SCIENTIFIC_READINESS.json")},
        "additional_engine_runs":0,"authorized_equilibrium_solver_calls":0,
        "scientific_promotion":False,**c.SCOPE})
    print("C03ED_COMMON_COUNTS",json.dumps(common,sort_keys=True))
    for arm,obs in observations.items():
        print("C03ED_VER099",arm,json.dumps(obs["warning099"]))
        print("C03ED_PRN",arm,obs["prn_bytes"],json.dumps(obs["prn_text"][:10000]))
    print("C03ED_MISSING",json.dumps(missing,sort_keys=True))
    # Emit compact source excerpts around the most relevant branch/call sites.
    for fname,ctx in sources.items():
        print("C03ED_SOURCE",fname,ctx["sha256"],ctx["matches"])
        for i,line in ctx["lines"]:
            if re.search(r"subroutine rfluid\b|ifug\.eq\.5|cork holland|call\s+rfluid\s*\(|call\s+outtit\b|saturated phase components|components with unconstrained potentials",line,re.I):
                print("C03ED_SOURCE_CONTEXT",fname,i,json.dumps(
                    [[n,l] for n,l in ctx["lines"] if abs(n-i)<=8]))
    print("C03ED_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
    print(STATUS)
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()
