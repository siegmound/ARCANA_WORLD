"""C03D native initialization only. Two fresh MEEMUM processes, no nonzero PT.
Read-only parent replay; no phase pruning, no equilibrium request or promotion.
"""
from __future__ import annotations
import argparse
import json
import re
import shutil
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03c_morb_roster_audit as c
from experiments.r6_thermo_provider_pilot_v1 import run_s3_d5_hgp_fair as launcher
from experiments.r6_thermo_provider_pilot_v1 import c03d_native_dialogue as dialogue
from experiments.r6_thermo_provider_pilot_v1 import c03d_r3_composition_audit as composition_audit
from experiments.r6_thermo_provider_pilot_v1 import c03d_r4_model_audit as model_audit

m=c.m
s2=c.s2
need=c.need
SCOPE=c.SCOPE
hgp=c.b.d.hgp
PIN="a040ef1577d2122822f695a584b205fcdfa254b6fc7e1e177afc88c3983d02a8"
PARENT="88b698ce98460bdc75ed989b02c7844e829cee60"
FAILED_OUT=s2.BASE/"R6_THERMO_C03D_NATIVE_INITIALIZATION_NEW01"
FAILED_PIN="eb882ecaf4fc85271b3c057a3b966ad8a8074ff96ceedf2e3327fdfc8e217161"
FAILED_SOURCE="724c60dcdc14f02a12dd875b7c5777c49701a768"
R1_FAILED_OUT=s2.BASE/"R6_THERMO_C03D_NATIVE_INITIALIZATION_NEW02"
R1_FAILED_PIN="99f64a5056c881f721d7b72e4ff795e2b6a330fac62e4929a131bc53111797a1"
R1_FAILED_SOURCE="5e393e3f1abcdd86460d4054f45adc0255a8c308"
R2_FAILED_OUT=s2.BASE/"R6_THERMO_C03D_NATIVE_INITIALIZATION_NEW03"
R2_FAILED_PIN="2ec231196c4f738993a982842905af1ab40fba066931c68b9e763b8878f4e2e1"
R2_FAILED_SOURCE="37167a279f33be6c8ba3d5dba87a5ed33cc5e116"
R3_FAILED_OUT=s2.BASE/"R6_THERMO_C03D_NATIVE_INITIALIZATION_NEW04"
R3_FAILED_PIN="d863620fad202747ef5cd46570c7b4670b757c06c3539d627bd310f186a4618d"
R3_FAILED_SOURCE="793a1e9e83e323da22bebe6a876131076dd4d107"
OUT=s2.BASE/"R6_THERMO_C03D_NATIVE_INITIALIZATION_NEW05"
RLIB_BLOB="d9cf25af82bba61f60d7c9b29c510ca9fe9eedaa"
TLIB_BLOB="a825163285c7a524c1ebc2980394b030fe9c7e04"
BUILD_BLOB="23f0a59ed5d1773e6e7e6d45c35462502f164579"
OPTION_BLOB="fba52ca4471749b84a930c6126cade7ed8d0efa0"
MEEMUM_SOURCE_BLOB="f2809f9b6e89a16f24ac89660650848150ac2334"
LIMITS={"address_space_limit_bytes":4*1024**3,"file_size_limit_bytes":16*1024**2,
        "retained_bytes_stop_threshold":64*1024**2,"walltime_s":60}
ORDER=("NA2O","MGO","AL2O3","K2O","CAO","TIO2","FEO","O2","H2O","SIO2")
STDIN=b"c03d\nn\n0 0\n"
HEADINGS={"included":"Summary of included solution models:",
          "rejected":"Summary of rejected solution models (see warnings above for reasons):",
          "not_found":"Requested solution models that were not found:"}


def audit_parent():
    rec=json.loads((m.HERE/"c03c_r1_fair_receipt_v1.json").read_text())
    man=m.archive_manifest(c.OUT,PIN,"files_sha256")
    need(man["schema"]=="R6_C03C_MORB_ROSTER_AUDIT_MANIFEST_V1"
        and man["source_sha"]==rec["source_sha"]==PARENT and rec["manifest_sha256"]==PIN
        and rec["exit"]==0 and man["C03B_manifest_sha256"]==c.PIN
        and man["additional_engine_runs"]==man["authorized_solver_calls"]==0
        and set(man["files_sha256"])=={"ROSTER_AUDIT.json"} and all(man[k]==v for k,v in SCOPE.items()),"C03D_PARENT_MANIFEST")
    ready,runtime=c.audit_parent()
    source=Path(runtime["source"])
    hp=(source/"datafiles/hp02ver.dat").read_bytes()
    models=(source/"datafiles/solution_model.dat").read_bytes()
    audit=c.audit_sources(hp,models,(source/c.LEGACY).read_bytes())
    report=json.loads((c.OUT/"ROSTER_AUDIT.json").read_text())
    need(report["candidate_roster"]==audit and report["candidate_cases"]==ready["candidate_cases"]
        and report["benchmark_candidate"]==c.benchmark_candidate()
        and report["additional_engine_runs"]==report["authorized_solver_calls"]==0
        and all(report[k]==v for k,v in SCOPE.items())
        and len(audit["main_models"])==rec["models"]==18
        and len(audit["pure_phase_records"])==rec["pure_and_water"]==11
        and audit["missing_by_model"]==rec["missing_by_model"]
        and audit["pure_phase_records"]["magnetite"]["composition"]==rec["magnetite_composition"]
        and report["benchmark_candidate"]["benchmark_status"]==rec["benchmark_status"],"C03D_PARENT_REPLAY")
    inputs,_,runtime2=hgp.verify_runtime_and_inputs()
    need(runtime==runtime2,"C03D_RUNTIME_DRIFT")
    options=(source/"optionfiles/perplex_option.dat").read_bytes()
    meemum=(source/"src/meemum.f").read_bytes()
    need(hgp.blob(options)==OPTION_BLOB and hgp.blob(meemum)==MEEMUM_SOURCE_BLOB,
         "C03D_NATIVE_SOURCE_DRIFT")
    need(b"if (v(1).eq.0d0) exit" in meemum and meemum.index(b"if (v(1).eq.0d0) exit")<meemum.index(b"call meemum (bad)"),
         "C03D_ZERO_PRESSURE_EXIT_SOURCE_DRIFT")
    tlib=(source/"src/tlib.f").read_bytes()
    build=(source/"src/build.f").read_bytes()
    need(hgp.blob(tlib)==TLIB_BLOB and hgp.blob(build)==BUILD_BLOB,"C03D_FIXED_WIDTH_SOURCE_DRIFT")
    need(b"rname*5" in tlib and b"read (n1,'(a,a)') rname,strg" in tlib
        and b"3000  format (a,1x,i1," in build,"C03D_FIXED_WIDTH_SOURCE_CONTRACT")
    rlib=(source/"src/rlib.f").read_bytes()
    need(hgp.blob(rlib)==RLIB_BLOB and b"**warning ver966**" in rlib and b"**warning ver968**" in rlib
        and b"Continue execution despite this warning (Y/N)?" in tlib,"C03D_DIALOGUE_SOURCE_DRIFT")
    need(b"key.eq.'site_check_override'" in rlib and b"stck = .false." in rlib
         and b"if (.not.stck.and..not.refine.and.iam.lt.3) then" in rlib
         and b"call warn (17,r,i,tname)" in rlib,"C03D_R4_LEGACY_MODEL_SOURCE_DRIFT")
    return report,runtime,inputs["bl691_MEEMUM.dat"],hp,models,options


def set_option(raw,key,value):
    pattern=rb"(?m)^("+re.escape(key.encode())+rb"[ \t]+)default(?=[ \t]+\|)"
    changed,n=re.subn(pattern,lambda z:z[1]+value.encode(),raw)
    need(n==1,"C03D_OPTION_DRIFT:"+key)
    return changed


def options_candidate(raw):
    for key,value in (("hybrid_EoS_H2O","2"),("hybrid_EoS_CO2","2"),
                      ("console_messages","on"),("solution_names","mod")):
        raw=set_option(raw,key,value)
    # Other options, including interactive warnings, remain pinned defaults.
    return raw


def replace_section(text,start,end,rows):
    pattern=r"(?m)^"+re.escape(start)+r"[ \t]*\n[\s\S]*?^"+re.escape(end)+r"[ \t]*$"
    value=start+"\n"+"\n".join(rows)+"\n"+end
    text,n=re.subn(pattern,lambda _:value,text)
    need(n==1,"C03D_SECTION_DRIFT:"+start)
    return text


def recipe_basis(cases,name):
    group=[x for x in cases if x["source_recipe"]==name]
    need(len(group)==2 and group[0]["candidate_basis"]==group[1]["candidate_basis"]
        and group[0]["source_chemistry_sha256"]==group[1]["source_chemistry_sha256"],"C03D_CHEMISTRY_REPLAY")
    return group[0]["candidate_basis"],group[0]["source_chemistry_sha256"]



def component_row(name,amount):
    # INPUT1 reads CHARACTER*5 rname then strg; BUILD writes a,1x,i1.
    need(name in ORDER and 1<=len(name)<=5 and m.finite(amount) and amount>0,
         "C03D_COMPONENT_ROW")
    return f"{name:<5} 1 {amount:.17g} 0.0 0.0"


def fixed_width_readback(project,expected):
    """Mirror the relevant native record boundary, not the full Fortran parser."""
    text=project.decode("ascii")
    rows=text.split("begin thermodynamic component list\n",1)[1].split("\nend thermodynamic component list",1)[0].splitlines()
    actual={}
    for row in rows:
        name=row[:5].strip()
        fields=row[5:].split()
        need(name in expected and name not in actual and len(fields)==4 and fields[0]=="1",
             "C03D_FIXED_WIDTH_COMPONENT:"+name)
        value=float(fields[1])
        need(m.finite(value) and value==expected[name] and fields[2:]==["0.0","0.0"],
             "C03D_COMPONENT_READBACK:"+name)
        actual[name]=value
    need(tuple(actual)==ORDER and actual==expected,"C03D_COMPONENT_ROUNDTRIP")
    return actual


def audit_failed_attempt():
    receipt=json.loads((m.HERE/"c03d_failed_fair_receipt_v1.json").read_text())
    need(hgp.file_sha(FAILED_OUT/"MANIFEST.json")==FAILED_PIN==receipt["manifest_sha256"],
         "C03D_FAILED_MANIFEST_DRIFT")
    man=json.loads((FAILED_OUT/"MANIFEST.json").read_text())
    members=launcher.inventory(FAILED_OUT)
    members.pop("MANIFEST.json")
    need(members==man["files"] and man["source_sha"]==receipt["source_sha"]==FAILED_SOURCE
        and man["status"]=="NATIVE_INITIALIZATION_FAILED_PRESERVED"
        and man["C03C_manifest_sha256"]==PIN and man["native_initialization_attempts"]==1
        and man["requested_equilibrium_points"]==man["authorized_equilibrium_solver_calls"]==0
        and all(man[k]==v for k,v in SCOPE.items()),"C03D_FAILED_ARCHIVE_DRIFT")
    failure=json.loads((FAILED_OUT/"FAILURE.json").read_text())
    work=FAILED_OUT/"C01_MORB_BASE"
    launch=json.loads((work/"LAUNCH.json").read_text())
    log=(work/"RUN_STDOUT.log").read_bytes()
    need(failure["message"]==receipt["failure"]=="C03D_NATIVE_PT_PROMPT_MISSING"
        and failure["native_initialization_attempts"]==1 and failure["requested_equilibrium_points"]==0
        and launch["exit_code"]==0 and launch["timeout"] is False
        and len(log)==receipt["stdout_bytes"] and receipt["native_error"].encode() in log,
        "C03D_FAILED_DIAGNOSTIC_DRIFT")
    bad=(work/"c03d.dat").read_text()
    row=next(x for x in bad.splitlines() if x.startswith("MGO "))
    need(row[:5]=="MGO 1" and "." in row[5:].split()[0],"C03D_FAILED_FIXED_WIDTH_EVIDENCE")
    return {"failed_manifest_sha256":FAILED_PIN,"native_error":"ver027",
            "observed_bad_name_field":row[:5],"observed_bad_flag_token":row[5:].split()[0]}



def audit_r1_failed_attempt():
    receipt=json.loads((m.HERE/"c03d_r1_failed_fair_receipt_v1.json").read_text())
    need(hgp.file_sha(R1_FAILED_OUT/"MANIFEST.json")==R1_FAILED_PIN==receipt["manifest_sha256"],
         "C03D_R1_FAILED_MANIFEST_DRIFT")
    man=json.loads((R1_FAILED_OUT/"MANIFEST.json").read_text())
    members=launcher.inventory(R1_FAILED_OUT)
    members.pop("MANIFEST.json")
    need(members==man["files"] and man["source_sha"]==receipt["source_sha"]==R1_FAILED_SOURCE
        and man["status"]=="NATIVE_INITIALIZATION_FAILED_PRESERVED"
        and man["C03C_manifest_sha256"]==PIN and man["native_initialization_attempts"]==1
        and man["requested_equilibrium_points"]==man["authorized_equilibrium_solver_calls"]==0
        and all(man[k]==v for k,v in SCOPE.items()),"C03D_R1_FAILED_ARCHIVE_DRIFT")
    failure=json.loads((R1_FAILED_OUT/"FAILURE.json").read_text())
    work=R1_FAILED_OUT/"C01_MORB_BASE"
    log=(work/"RUN_STDOUT.log").read_bytes()
    need(failure["message"]==receipt["failure"] and failure["native_initialization_attempts"]==1
        and failure["requested_equilibrium_points"]==0 and receipt["warning"].encode() in log
        and receipt["prompt"].encode() in log and dialogue.PT not in log
        and (work/"bl691_MEEMUM_input.txt").read_bytes()==STDIN,"C03D_R1_FAILED_DIAGNOSTIC_DRIFT")
    return {"manifest_sha256":R1_FAILED_PIN,"warning":"ver966","fixed_width_input_reached_database":True}


def audit_r2_failed_attempt():
    receipt=json.loads((m.HERE/"c03d_r2_failed_fair_receipt_v1.json").read_text())
    need(hgp.file_sha(R2_FAILED_OUT/"MANIFEST.json")==R2_FAILED_PIN==receipt["manifest_sha256"],
         "C03D_R2_FAILED_MANIFEST_DRIFT")
    man=json.loads((R2_FAILED_OUT/"MANIFEST.json").read_text())
    members=launcher.inventory(R2_FAILED_OUT)
    members.pop("MANIFEST.json")
    need(members==man["files"] and man["source_sha"]==receipt["source_sha"]==R2_FAILED_SOURCE
        and man["status"]=="NATIVE_INITIALIZATION_FAILED_PRESERVED"
        and man["C03C_manifest_sha256"]==PIN and man["native_initialization_attempts"]==1
        and man["requested_equilibrium_points"]==man["authorized_equilibrium_solver_calls"]==0
        and man["scientific_promotion"] is False and all(man[k]==v for k,v in SCOPE.items()),
        "C03D_R2_FAILED_ARCHIVE_DRIFT")
    failure=json.loads((R2_FAILED_OUT/"FAILURE.json").read_text())
    work=R2_FAILED_OUT/"C01_MORB_BASE"
    log=(work/"RUN_STDOUT.log").read_bytes()
    dia=json.loads((work/"DIALOGUE.json").read_text())
    need(failure["message"]==receipt["failure"] and failure["native_initialization_attempts"]==1
        and failure["requested_equilibrium_points"]==0 and dialogue.SI013 in b" ".join(log.split())
        and dialogue.PT not in log and dialogue.BULK not in log
        and (work/"DIALOGUE_STDIN.log").read_bytes()==b"c03d\ny\ny\n"
        and dia["policy"]==dialogue.POLICY and dia["state"]=="INITIALIZING"
        and dia["acknowledged_warning_codes"]==["966","968"]
        and [e["prompt"] for e in dia["events"]]==["PROJECT","HP02_O2_VER966","HP02_O2_VER968"]
        and dia["requested_equilibrium_points"]==0 and dia["scientific_warning_acceptance"] is False
        and dia["error"]=="ValueError: "+receipt["failure"],"C03D_R2_FAILED_DIAGNOSTIC_DRIFT")
    return {"manifest_sha256":R2_FAILED_PIN,"warning":"ver013","species":"Si(s)",
            "unknown_warning_fail_closed":True}


def audit_r3_failed_attempt(composition,roster):
    receipt=json.loads((m.HERE/"c03d_r3_failed_fair_receipt_v1.json").read_text())
    need(hgp.file_sha(R3_FAILED_OUT/"MANIFEST.json")==R3_FAILED_PIN==receipt["manifest_sha256"],
         "C03D_R3_FAILED_MANIFEST_DRIFT")
    man=json.loads((R3_FAILED_OUT/"MANIFEST.json").read_text())
    members=launcher.inventory(R3_FAILED_OUT)
    members.pop("MANIFEST.json")
    need(members==man["files"] and man["source_sha"]==receipt["source_sha"]==R3_FAILED_SOURCE
        and man["status"]=="NATIVE_INITIALIZATION_FAILED_PRESERVED"
        and man["C03C_manifest_sha256"]==PIN and man["native_initialization_attempts"]==1
        and man["requested_equilibrium_points"]==man["authorized_equilibrium_solver_calls"]==0
        and man["scientific_promotion"] is False and all(man[k]==v for k,v in SCOPE.items())
        and json.loads((R3_FAILED_OUT/"DIRECT_EOS_AUDIT.json").read_text())==composition,
        "C03D_R3_FAILED_ARCHIVE_DRIFT")
    failure=json.loads((R3_FAILED_OUT/"FAILURE.json").read_text())
    work=R3_FAILED_OUT/"C01_MORB_BASE"
    log=(work/"RUN_STDOUT.log").read_bytes()
    dia=json.loads((work/"DIALOGUE.json").read_text())
    need(failure["message"]==receipt["failure"] and failure["native_initialization_attempts"]==1
        and failure["requested_equilibrium_points"]==0 and dialogue.GL017 in b" ".join(log.split())
        and dialogue.PT not in log and dialogue.BULK not in log
        and (work/"DIALOGUE_STDIN.log").read_bytes()==b"c03d\ny\ny\ny\n"
        and dia["policy"]==dialogue.R3_POLICY and dia["state"]=="INITIALIZING"
        and dia["acknowledged_warning_codes"]==["966","968","013"]
        and [e["prompt"] for e in dia["events"]]==["PROJECT","HP02_O2_VER966","HP02_O2_VER968","HP02_SI_REJECTION_VER013"]
        and dia["requested_equilibrium_points"]==0 and dia["scientific_warning_acceptance"] is False
        and dia["error"]=="ValueError: "+receipt["failure"],"C03D_R3_FAILED_DIAGNOSTIC_DRIFT")
    details=model_audit.native_model_details(log,roster,composition["records"])
    observed={(x["model"],v["endmember"]) for x in details["missing_endmember_reports"] for v in x["endmembers"]}
    need({("O(HP)","teph"),("O(HP)","fran"),("IlGkPy","pnt"),("Cpx(HP)","esn"),
          ("Cpx(HP)","ccrts"),("Stlp(M)","mnsp")}<=observed,"C03D_R3_MISSING_READBACK_DRIFT")
    return {"manifest_sha256":R3_FAILED_PIN,"warning":"ver017","model":"GlTrTsPg",
            "partial_native_model_details":details}


def project_input(template,basis,masses,roster):
    text=template.decode("ascii").replace("\r\n","\n")
    lines=text.splitlines()
    need(lines[0].startswith("hp62ver.dat") and lines[3].startswith("solution_model.dat")
        and lines[5].startswith("bl691_MEEMUM_perplex_option.dat"),"C03D_TEMPLATE_HEADER")
    lines[0]="hp02ver.dat"
    lines[1]="print"
    lines[2]="no_plot"
    lines[3]="solution_model.dat"
    lines[4]="C03D noncanonical closed-bulk MORB initialization only"
    lines[5]="perplex_option.dat"
    text="\n".join(lines)+"\n"
    text,n=re.subn(r"(?m)^\s*19 number of components in the data base$",
        f"   {len(masses)} number of components in the data base",text)
    need(n==1 and len(masses)==15,"C03D_DATASET_COMPONENT_COUNT")
    text,n=re.subn(r"(?m)^\s*14 ifug EoS for saturated phase$","    5 ifug EoS for saturated phase",text)
    need(n==1 and re.search(r"(?m)^\s*0 component amounts, 0 - molar, 1 weight$",text),"C03D_MOLAR_OR_EOS")
    vals=basis["native_moles_per_source_recipe"]
    need(set(vals)==set(ORDER) and all(m.finite(v) and v>0 for v in vals.values()),"C03D_BULK_COMPONENTS")
    total=sum(vals.values())
    normalized={k:100*vals[k]/total for k in ORDER}
    rows=[component_row(k,normalized[k]) for k in ORDER]
    text=replace_section(text,"begin thermodynamic component list","end thermodynamic component list",rows)
    for start,end in (("begin saturated component list","end saturated component list"),
                      ("begin saturated phase component list","end saturated phase component list"),
                      ("begin independent potential/fugacity/activity list","end independent potential list"),
                      ("begin excluded phase list","end excluded phase list")):
        text=replace_section(text,start,end,[])
    need(len(roster)==18 and set(roster)==set(c.VERTICES),"C03D_ROSTER")
    text=replace_section(text,"begin solution phase list","end solution phase list",roster)
    # Remove upstream fixture's appended diagnostic output. Retain only native project input.
    idx=list(re.finditer(r"(?m)^\s*2\s+1\s+4\s+5\s+3\s+indices[^\n]*$",text))
    need(len(idx)==1,"C03D_PT_INDEX_TEMPLATE")
    text=text[:idx[0].end()]+"\n"
    text,n=re.subn(r"(?m)^\s*10000\.\s+1323\.0[^\n]*max p, t, xco2, u1, u2$",
        " 5000.0 723.15 0.0 0.0 0.0 max p, t, xco2, u1, u2",text)
    need(n==1,"C03D_PT_MAX")
    text,n=re.subn(r"(?m)^\s*500\.0\s+873\.00[^\n]*min p, t, xco2, u1, u2$",
        " 1000.0 423.15 0.0 0.0 0.0 min p, t, xco2, u1, u2",text)
    need(n==1,"C03D_PT_MIN")
    raw=text.encode("ascii")
    fixed_width_readback(raw,normalized)
    return raw,normalized


def summary_section(text,heading,roster):
    matches=list(re.finditer(r"(?m)^\s*"+re.escape(heading)+r"[ \t]*\r?$",text))
    need(len(matches)<=1,"C03D_DUPLICATE_NATIVE_SUMMARY:"+heading)
    if not matches:
        return []
    result=[]
    for line in text[matches[0].end():].splitlines():
        tokens=line.split()
        if not tokens:
            if result: break
            continue
        if all(k in roster for k in tokens):
            result.extend(tokens)
        else:
            break
    need(len(set(result))==len(result),"C03D_DUPLICATE_NATIVE_MODEL")
    return result


def observe(stdout,prn,roster):
    text=stdout.decode("utf-8",errors="replace")
    fatal=re.search(r"\*\*error ver\d+\*\*[^\n]*",text,re.I)
    need(fatal is None,"C03D_NATIVE_FATAL:"+ (fatal.group(0) if fatal else ""))
    # The zero-P sentinel is not a physical pressure sample.
    need("Enter (T = 0 to quit)" in text,"C03D_NATIVE_PT_PROMPT_MISSING")
    need("Interactively enter bulk compositions (y/n)?" in text,"C03D_NATIVE_BULK_PROMPT_MISSING")
    need("Phase Compositions (" not in text and b"Phase Compositions (" not in prn,
        "C03D_UNEXPECTED_EQUILIBRIUM_OUTPUT")
    sections={k:summary_section(text,v,roster) for k,v in HEADINGS.items()}
    flat=[k for z in sections.values() for k in z]
    need(len(flat)==len(set(flat)),"C03D_OVERLAPPING_NATIVE_DISPOSITIONS")
    unknown=sorted(set(roster)-set(flat))
    warnings=[l.strip() for l in text.splitlines() if re.search(r"warning|error|endmember|end-member",l,re.I)]
    return {"native_model_dispositions":sections,"unaccounted_requested_models":unknown,
        "native_warnings_and_endmember_lines":warnings,"native_bulk_readback_verified":False,
        "native_endmember_pruning_verified":False,"native_pure_phase_admission_verified":False,
        "requested_equilibrium_points":0,"equilibrium_output_detected":False,
        "initialization_only":True,"stdout_sha256":hgp.sha(stdout),
        "prn_sha256":hgp.sha(prn) if prn else None,
        "scientific_applicability":"UNKNOWN",
        "status":"NATIVE_ROSTER_CAPTURED" if not unknown else "NATIVE_ROSTER_REVIEW_REQUIRED"}


def seal(state,head,attempts,report):
    members=launcher.inventory(OUT)
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03D_NATIVE_INITIALIZATION_MANIFEST_V1",
        "status":state,"source_sha":head,"C03C_manifest_sha256":PIN,
        "native_initialization_attempts":attempts,"requested_equilibrium_points":0,
        "authorized_equilibrium_solver_calls":0,"files":members,
        "scientific_promotion":False,**SCOPE})
    print("C03D_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"),flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    ap.add_argument("--native-initialization-only",action="store_true",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03D_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C03D_OUTPUT_EXISTS")
    report,runtime,template,hp,models,options=audit_parent()
    print("C03D_INDEPENDENT_C03C_REPLAY_PASS",PIN,flush=True)
    failed=audit_failed_attempt()
    print("C03D_R1_FAILED_ARCHIVE_VERIFIED",FAILED_PIN,flush=True)
    failed_r1=audit_r1_failed_attempt()
    print("C03D_R2_FAILED_ARCHIVE_VERIFIED",R1_FAILED_PIN,flush=True)
    failed_r2=audit_r2_failed_attempt()
    print("C03D_R3_FAILED_ARCHIVE_VERIFIED",R2_FAILED_PIN,flush=True)
    roster=list(c.VERTICES)
    masses=c.b.components(hp)
    composition=composition_audit.audit(hp,masses,ORDER,c.b.model_blocks(models,tuple(roster)),c.PURE.values())
    print("C03D_R3_DIRECT_EOS_AUDIT",composition["direct_eos_count"],composition["active_basis_compatible_count"],composition["nonpositive_compatible"],flush=True)
    failed_r3=audit_r3_failed_attempt(composition,roster)
    print("C03D_R4_FAILED_ARCHIVE_VERIFIED",R3_FAILED_PIN,flush=True)
    legacy=model_audit.model_audit(c.b.model_blocks(models,tuple(roster)))
    print("C03D_R4_MODEL_AUDIT",legacy["allowed_diagnostic_warning_models"],flush=True)
    opts=options_candidate(options)
    plans={}
    for name in c.b.MORB:
        basis,chem=recipe_basis(report["candidate_cases"],name)
        project,normalized=project_input(template,basis,masses,roster)
        plans[name]=(project,normalized,chem)
    print("C03D_R1_FIXED_WIDTH_ROUNDTRIP_PASS",len(plans),len(ORDER),flush=True)
    need(shutil.disk_usage(s2.BASE).free>=LIMITS["retained_bytes_stop_threshold"],"C03D_DISK")
    OUT.mkdir(parents=False,exist_ok=False)
    attempts=0
    try:
        s2.write_json(OUT/"DIRECT_EOS_AUDIT.json",composition)
        s2.write_json(OUT/"MODEL_AUDIT.json",legacy)
        s2.write_json(OUT/"PROVENANCE.json",{"source_sha":head,"runtime":runtime,"limits":LIMITS,
            "C03C_manifest_sha256":PIN,"meemum_source_git_blob":MEEMUM_SOURCE_BLOB,
            "failed_attempt":failed,"failed_r1_attempt":failed_r1,"failed_r2_attempt":failed_r2,
            "failed_r3_attempt":failed_r3,"model_audit_sha256":s2.sha(OUT/"MODEL_AUDIT.json"),
            "direct_eos_audit_sha256":s2.sha(OUT/"DIRECT_EOS_AUDIT.json"),"dialogue_policy":dialogue.R4_POLICY,
            "rlib_git_blob":RLIB_BLOB,"fixed_width_parser_git_blob":TLIB_BLOB,"build_writer_git_blob":BUILD_BLOB,
            "input_option_git_blob":OPTION_BLOB,"fluid_eos_ifug":5,"hybrid_water_eos":2,
            "fluid_boundary":"CLOSED_BULK_NO_BUFFER_NO_SATURATION",
            "pure_phase_selection":"NATIVE_DEFAULT_COMPONENT_FILTERING_NO_EXCLUSIONS",
            "requested_solution_models":roster,"requested_equilibrium_points":0,
            "allocation_independently_verified":False,**SCOPE})
        results={}
        for name,(project,normalized,chem) in plans.items():
            work=OUT/name
            work.mkdir()
            files={"c03d.dat":project,"hp02ver.dat":hp,"solution_model.dat":models,
                   "perplex_option.dat":opts}
            for k,raw in files.items():
                with (work/k).open("xb") as f: f.write(raw)
            s2.write_json(work/"INPUT.json",{"source_chemistry_sha256":chem,
                "normalized_native_molar_amounts":normalized,"fixed_width_input_roundtrip":fixed_width_readback(project,normalized),"files_sha256":{k:hgp.sha(v) for k,v in files.items()},
                "requested_equilibrium_points":0})
            need(launcher.retained_bytes(OUT)<LIMITS["retained_bytes_stop_threshold"]
                and hgp.file_sha(runtime["binary"])==runtime["binary_sha256"],"C03D_LAUNCH_GUARD")
            attempts+=1
            try:
                dialogue.launch_dialogue([Path(runtime["binary"])],work,LIMITS,
                    allow_si013=composition["allowed_diagnostic_warning_species"]==["Si(s)"],
                    allow_gl017=legacy["allowed_diagnostic_warning_models"]==["GlTrTsPg"])
            finally:
                if (work/"RUN_STDOUT.log").is_file():
                    rawlog=(work/"RUN_STDOUT.log").read_bytes()
                    print("C03D_NATIVE_LOG_TAIL",name,rawlog[-6000:].decode("utf-8",errors="replace"),flush=True)
                    details=model_audit.native_model_details(rawlog,roster,composition["records"])
                    s2.write_json(work/"NATIVE_MODEL_DETAILS.json",details)
                    print("C03D_NATIVE_MODEL_DETAILS",name,json.dumps(details,sort_keys=True),flush=True)
                if (work/"DIALOGUE.json").is_file():
                    print("C03D_NATIVE_DIALOGUE",name,(work/"DIALOGUE.json").read_text(),flush=True)
            prn=work/"c03d.prn"
            obs=observe(rawlog,prn.read_bytes() if prn.is_file() else b"",roster)
            obs["dialogue"]=json.loads((work/"DIALOGUE.json").read_text())
            obs["native_model_details"]=details
            s2.write_json(work/"READBACK.json",obs)
            results[name]=obs
            print("C03D_NATIVE_MODEL_DISPOSITIONS",name,json.dumps(obs["native_model_dispositions"],sort_keys=True),flush=True)
            print("C03D_UNACCOUNTED_MODELS",name,json.dumps(obs["unaccounted_requested_models"]),flush=True)
            need(launcher.retained_bytes(OUT)<LIMITS["retained_bytes_stop_threshold"],"C03D_RETAINED_STOP")
        s2.write_json(OUT/"RESULT.json",{"observations":results,"requested_equilibrium_points":0,
            "native_initialization_attempts":attempts,"campaign_authorized":False,**SCOPE})
        seal("NATIVE_INITIALIZATION_CAPTURED__REVIEW_REQUIRED",head,attempts,report)
        print("C03D_NATIVE_INITIALIZATION_CAPTURED__REVIEW_REQUIRED")
        print("NATIVE_INITIALIZATION_ATTEMPTS="+str(attempts))
        print("REQUESTED_EQUILIBRIUM_POINTS=0")
    except BaseException as exc:
        if not (OUT/"MANIFEST.json").exists():
            s2.write_json(OUT/"FAILURE.json",{"error":type(exc).__name__,"message":str(exc),
                "native_initialization_attempts":attempts,"requested_equilibrium_points":0})
            seal("NATIVE_INITIALIZATION_FAILED_PRESERVED",head,attempts,report)
        raise


if __name__=="__main__":
    main()
