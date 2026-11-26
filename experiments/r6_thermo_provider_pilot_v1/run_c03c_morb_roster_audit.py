"""C03C: literature roster crosswalk and pinned native endmember dependency audit.
No solver, automatic phase pruning, canonical assignment or benchmark promotion.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03b_low_grade_morb_readiness as b

m=b.m
s2=b.s2
need=b.need
SCOPE=b.SCOPE
PIN="5a887ca1fa9405d7d97d4b09aee6d02517fb82ad40a9704d81e22d1d07be1c38"
PARENT="49fe02bcd5eff9829e9a6d1359c1e95d60245b28"
OUT=s2.BASE/"R6_THERMO_C03C_MORB_ROSTER_AUDIT_NEW01"
MAIN_BLOB="90a69e26a7e3553a183aee49bf00adda4a065e0c"
LEGACY_BLOB="88de95ee57acf527bd99954835d801be45714533"
LEGACY="datafiles/old_or_less_used_data_files/solution_model_681.dat"
# Transcription of the main-file vertex/endmember rosters reviewed at the pinned upstream.
# This is intentionally explicit; it does not claim to parse the full Perple_X model grammar.
VERTICES={
    "Act(M)":"tr acti gl mrie","GlTrTsPg":"tr ftr parg fparg_i ts_q fts_i gl fgl_i",
    "Cpx(HP)":"esn ccrts cats jd acm hed di","Opx(HP)":"mgts fets_d en fs ots_q feots",
    "Kf":"mic ab","Pl(h)":"abh an","Chl(W)":"mnchl fames fafchl ff3cli daph ames afchl f3cl_q clin",
    "Bio(TCC)":"mnbi ffbit f3b_q sdph east ftbit tbi_q ann phl",
    "Mica(M)":"ma mu pa","Stlp(M)":"stlp mstl mnsp","Atg(PN)":"atg fatg_q atgts_q",
    "T(F)":"ta fta tats","Pu(M)":"pump fpum ffpu","Ep(HP11)":"cz fep ep",
    "O(HP)":"teph fran fo fa","Sp(WPC)":"sp herc usp mt","IlGkPy":"pnt geik ilm",
    "B(F)":"br fbr_q"}
LOCAL={
    "GlTrTsPg":{"fparg_i":"parg ftr tr","fts_i":"ts_q ftr tr","fgl_i":"gl ftr tr"},
    "Opx(HP)":{"opx":"en fs","fets_d":"mgts opx en","feots":"ots_q opx en"},
    "Chl(W)":{"och1":"afchl clin daph","och2":"afchl clin daph","fames":"ames daph och2 afchl clin",
              "fafchl":"och1 och2 afchl","ff3cli":"f3cl_q daph clin"},
    "Bio(TCC)":{"obi":"phl ann","sdph":"east ann obi","ffbit":"f3b_q ann obi","ftbit":"tbi_q ann obi phl"}}
MAKES={"ts_q":"ts","ots_q":"mgts cor hem","f3cl_q":"clin gr andr","f3b_q":"east cor hem",
       "tbi_q":"phl br ru","fatg_q":"atg ta fta","atgts_q":"clin atg br","fbr_q":"br ta fta"}
# Source Table 1 labels vs native identifiers; alternatives do not imply exact historical reproduction.
CROSSWALK={"GTrTsPg":"GlTrTsPg","Stp(M)":"Stlp(M)","T":"T(F)","IlGy":"IlGkPy","B":"B(F)"}
PURE={"analcime":"anl","laumontite":"lmt","stilbite":"stlb","wairakite":"wrk","prehnite":"pre",
      "titanite":"sph","quartz":"q","lawsonite":"law","nepheline":"ne","magnetite":"mt","water":"H2O"}


def require_tokens(body,tokens):
    for k in tokens:
        need(re.search(r"(?<![\w])"+re.escape(k)+r"(?![\w])",body) is not None,"C03C_SOURCE_TOKEN:"+k)


def equation_rows(body):
    """Only simple named equation headers; source RHS retained, no numeric interpretation."""
    result={}
    for line in body.splitlines():
        active=line.split("|",1)[0].strip()
        hit=re.match(r"^([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.+)$",active)
        if hit:
            result.setdefault(hit[1],[]).append(hit[2])
    return result


def check_equation(rows,name,deps):
    hits=rows.get(name,[])
    need(any(all(re.search(r"(?<![\w])"+re.escape(k)+r"(?![\w])",x) for k in deps.split()) for x in hits),
        "C03C_DEPENDENCY_EQUATION_DRIFT:"+name)


def resolve(name,direct,makes,local,stack=()):
    if name in stack:
        raise ValueError("C03C_DEPENDENCY_CYCLE:"+name)
    # Model-local definitions take precedence over dataset definitions.
    if name in local or name in makes:
        deps=local[name] if name in local else makes[name]
        children=[resolve(k,direct,makes,local,stack+(name,)) for k in deps.split()]
        return {"status":"DEFINED_DEPENDENCY" if not any(x["missing"] for x in children) else "UNRESOLVED_DEPENDENCY",
                "missing":sorted({k for x in children for k in x["missing"]})}
    return {"status":"DIRECT_EOS" if name in direct else "ABSENT_NAMED_EOS_OR_DECLARED_MAKE",
            "missing":[] if name in direct else [name]}


def pure_record(raw,name):
    lines=raw.decode("utf-8").splitlines()
    hits=[i for i,l in enumerate(lines) if re.match(r"^"+re.escape(name)+r"[ \t]+EoS[ \t]*=",l)]
    need(len(hits)==1,"C03C_PURE_RECORD:"+name)
    return {"header":lines[hits[0]],"composition":lines[hits[0]+1]}


def audit_parent():
    rec=json.loads((m.HERE/"c03b_fair_receipt_v1.json").read_text())
    man=m.archive_manifest(b.OUT,PIN,"files_sha256")
    need(man["schema"]=="R6_C03B_LOW_GRADE_MORB_READINESS_MANIFEST_V1"
        and man["source_sha"]==rec["source_sha"]==PARENT and rec["manifest_sha256"]==PIN
        and man["C03_manifest_sha256"]==b.PIN and rec["exit"]==0
        and man["additional_engine_runs"]==man["authorized_solver_calls"]==0
        and set(man["files_sha256"])=={"READINESS.json"} and all(man[k]==v for k,v in SCOPE.items()),"C03C_PARENT_MANIFEST")
    old,inputs,runtime=b.audit_design()
    ready=json.loads((b.OUT/"READINESS.json").read_text())
    need(ready==b.build(old,inputs,runtime)
        and ready["core_endmember_inventory"]==rec["core_endmember_inventory"]
        and {k:v["line"] if v else None for k,v in ready["model_blocks"].items()}==rec["model_headers"]
        and len(ready["candidate_cases"])==rec["candidate_cases"]==4,"C03C_PARENT_REPLAY")
    return ready,runtime


def audit_sources(hp,main,legacy):
    need(b.d.hgp.blob(hp)==b.HP02_BLOB and b.d.hgp.blob(main)==MAIN_BLOB
        and b.d.hgp.blob(legacy)==LEGACY_BLOB,"C03C_PINNED_SOURCES")
    direct=b.endmember_names(hp)
    text=hp.decode("utf-8")
    make_body=text.split("\nbegin_makes",1)[1].split("\nend_makes",1)[0]
    equations=equation_rows(make_body)
    for name,deps in MAKES.items():
        check_equation(equations,name,deps)
    blocks=b.model_blocks(main,tuple(VERTICES))
    legacy_blocks=b.model_blocks(legacy,("GlTrTsPg","Stlp(M)","T","IlGkPy","B"))
    need(all(v is not None for v in blocks.values()) and all(v is not None for v in legacy_blocks.values()),
        "C03C_ROSTER_BLOCK_MISSING")
    result={}
    for name,vertices in VERTICES.items():
        block=blocks[name]
        require_tokens(block["text"],vertices.split())
        local=LOCAL.get(name,{})
        rows=equation_rows(block["text"])
        for k,deps in local.items():
            check_equation(rows,k,deps)
        states={k:resolve(k,direct,MAKES,local) for k in vertices.split()}
        result[name]={"line":block["line"],"normalized_text_sha256":block["normalized_text_sha256"],
            "vertices":states,"missing":sorted({v for x in states.values() for v in x["missing"]})}
    pure={k:pure_record(hp,v) for k,v in PURE.items()}
    need(pure["magnetite"]["composition"].strip()=="FEO(3)O2(.5)"
        and pure_record(hp,"mag")["composition"].strip()=="MGO(1)CO2(1)","C03C_MAGNETITE_IDENTITY")
    need(pure["water"]["composition"].strip()=="H2O(1)","C03C_WATER_IDENTITY")
    return {"main_model_git_blob":MAIN_BLOB,"legacy_model_git_blob":LEGACY_BLOB,
        "hp02_git_blob":b.HP02_BLOB,"main_models":result,"legacy_alias_blocks":legacy_blocks,
        "pure_phase_records":pure,"mag_is_magnesite_not_magnetite":True,
        "missing_by_model":{k:v["missing"] for k,v in result.items() if v["missing"]},
        "roster_crosswalk":CROSSWALK,"full_native_parser_or_phase_pruning_verified":False}


def benchmark_candidate():
    # Table 2 dry oxide values; NOT a complete numerical reference case.
    return {"reference_doi":"10.1029/2018JE005869","reference_engine":"Perple_X 6.8.1",
        "source_locator":"Table 1, Table 2, section 2.1, Figure 1a",
        "source_pdf":"https://oro.open.ac.uk/59162/1/Semprich_et_al-2019-Journal_of_Geophysical_Research__Planets.pdf",
        "source_text_checked":True,"source_pdf_raw_sha256":None,"source_table_visual_verified":False,
        "N_MORB_dry_oxide_wt":{"SiO2":50.42,"TiO2":1.53,"Al2O3":15.13,"FeO_total":9.81,
            "MgO":7.76,"CaO":11.35,"Na2O":2.83,"K2O":0.14},
        "water_boundary":"WATER_SATURATED_FIGURE_1A_NOT_ARCANA_CLOSED_BULK",
        "water_EOS_reference":"COMPENSATED_REDLICH_KWONG",
        "O2_exact_MORB_input":None,"exact_benchmark_PT":None,
        "benchmark_expected_phases_and_modal_fractions":None,
        "benchmark_executable":False,"benchmark_status":"REFERENCE_INPUT_AND_FIGURE_DIGITIZATION_PENDING"}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03C_CHECKOUT")
    need(not OUT.exists(),"C03C_OUTPUT_EXISTS")
    ready,runtime=audit_parent()
    print("C03C_INDEPENDENT_C03B_REPLAY_PASS",PIN,flush=True)
    source=Path(runtime["source"])
    audit=audit_sources((source/"datafiles/hp02ver.dat").read_bytes(),
        (source/"datafiles/solution_model.dat").read_bytes(),(source/LEGACY).read_bytes())
    report={"schema":"R6_C03C_MORB_ROSTER_AUDIT_V1",
        "status":"ROSTER_SOURCE_AUDITED__NATIVE_AND_SCIENCE_GATES_PENDING",
        "candidate_roster":audit,"benchmark_candidate":benchmark_candidate(),
        "candidate_cases":ready["candidate_cases"],"candidate_recipe_count":4,
        "additional_engine_runs":0,"authorized_solver_calls":0,"authorial_selection":None,
        "scientific_promotion":False,**SCOPE}
    OUT.mkdir(parents=False,exist_ok=False)
    s2.write_json(OUT/"ROSTER_AUDIT.json",report)
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03C_MORB_ROSTER_AUDIT_MANIFEST_V1",
        "source_sha":head,"C03B_manifest_sha256":PIN,"additional_engine_runs":0,"authorized_solver_calls":0,
        "files_sha256":{"ROSTER_AUDIT.json":s2.sha(OUT/"ROSTER_AUDIT.json")},**SCOPE})
    print("C03C_ROSTER_MODELS",len(audit["main_models"]),"PURE_AND_WATER",len(audit["pure_phase_records"]))
    print("C03C_MISSING_NAMED_DEPENDENCIES",json.dumps(audit["missing_by_model"],sort_keys=True))
    print("C03C_MAGNETITE_NATIVE_IDENTITY",audit["pure_phase_records"]["magnetite"]["composition"])
    print("C03C_BENCHMARK_STATUS",report["benchmark_candidate"]["benchmark_status"])
    print("C03C_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
    print("C03C_ROSTER_SOURCE_AUDIT_COMPLETE__NATIVE_AND_SCIENCE_GATES_PENDING")
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()
