"""C03E-A: static chemical closure of amphibole candidates and configuration risks.
No model modification, phase selection, engine invocation or scientific qualification.
"""
from __future__ import annotations
import argparse
from fractions import Fraction
import json
import re
from experiments.r6_thermo_provider_pilot_v1 import run_c03e_reference_design as e

d=e.d
s2=e.s2
need=e.need
hgp=e.hgp
SCOPE=e.SCOPE
PIN="921a1f7eccdbdda36f70c832b4209c71ad8d654262382aa42ed5eb5e7ac23350"
PARENT="30c94dbf12207e6af1e25df4b1ac8989e7d54837"
OUT=s2.BASE/"R6_THERMO_C03EA_CONFIGURATION_AUDIT_NEW01"
STATUS="C03EA_STATIC_CHEMICAL_CLOSURE__CALIBRATION_AND_PHASE_POLICY_UNRESOLVED"
# Reviewed active vertex rows, in source order; comment-only vertices excluded.
VERTICES={
    "cAmph(DP)":"mrb_q frb_d gl fgl_d ts_q fcts_d mts_d fts_d parg fcparg_d mparg_d fparg_d mcgrk_d fcgrk_d mgrk_d fgrk_d cumm grun tr ftr_d",
    "cAmph_I(DP)":"mrb_q frb_d gl fgl_d mgrk_d fgrk_d mts_d fts_d mcgrk_d fcgrk_d ts_q fcts_d mparg_d fparg_d parg fcparg_d ompg_d ofpg_d ocmpg_d ocfpg_d nmfn_d nffn_d nmfmn_d nfffn_d nmfcn_d nffcn_d nman_d nfan_d nmamn_d nfafn_d nmacn_d nfacn_d cumm grun tr ftr_d",
    "cAmph(G)":"mrb1_q frb_d gl fgl_d mts_d fts_d ts_q fcts_d mparg_d fparg_d parg fcparg_d kmparg_d kfparg_d kprg_q kfcprg_d mtts_d ftts_d tts_q fctts_d mgrk_d fgrk_d mcgrk_d fcgrk_d cumm grun tr ftr_d"}
ROOTS={"cAmph(DP)":"acm cumm gl grun jd parg tr ts",
       "cAmph_I(DP)":"acm cumm gl grun jd parg tr ts",
       "cAmph(G)":"andr cumm dsp gl gr grun mu pa parg ru tr ts"}
MAKE_NAMES={"cAmph(DP)":["mrb_q","ts_q"],"cAmph_I(DP)":["mrb_q","ts_q"],
            "cAmph(G)":["mrb1_q","ts_q","kprg_q","tts_q"]}
TERM=re.compile(r"\s*([+-]?)\s*(\d+(?:/\d+|\.\d+)?|\.\d+)\s+([A-Za-z][A-Za-z0-9_]*)")


def section(text,name):
    lines=text.splitlines()
    starts=[i for i,x in enumerate(lines) if x.strip()=="begin_"+name]
    ends=[i for i,x in enumerate(lines) if x.strip()=="end_"+name]
    need(len(starts)==len(ends)==1 and starts[0]<ends[0],"C03EA_SECTION:"+name)
    return "\n".join(lines[starts[0]+1:ends[0]])


def equations(text):
    result={}
    for line in text.splitlines():
        m=re.fullmatch(r"\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.+)",line)
        if m and m[1].upper()!="DQF":
            need(m[1] not in result,"C03EA_DUPLICATE_EQUATION:"+m[1])
            result[m[1]]=m[2].split("delta_g_of_ordering",1)[0].strip()
    return result


def terms(rhs):
    cursor=0
    out=[]
    while cursor<len(rhs):
        m=TERM.match(rhs,cursor)
        need(m is not None,"C03EA_UNPARSED_EQUATION:"+rhs)
        sign,value,name=m.groups()
        need(cursor==0 or sign in ("+","-"),"C03EA_MISSING_SIGN:"+rhs)
        out.append((name,Fraction(value)*(-1 if sign=="-" else 1)))
        cursor=m.end()
    need(bool(out),"C03EA_EMPTY_EQUATION")
    return out


def resolve(name,direct,local,makes,roots,used,stack=()):
    need(name not in stack,"C03EA_DEPENDENCY_CYCLE:"+name)
    if name in local or name in makes:
        if name not in local:
            used.add(name)
        rhs=local[name] if name in local else makes[name]
        out={}
        for child,factor in terms(rhs):
            for k,v in resolve(child,direct,local,makes,roots,used,stack+(name,)).items():
                out[k]=out.get(k,Fraction(0))+factor*v
        return {k:v for k,v in out.items() if v}
    need(name in direct,"C03EA_MISSING_DIRECT_EOS:"+name)
    roots.add(name)
    return {k:Fraction(v) for k,v in direct[name]["coefficients"].items() if Fraction(v)}


def audit_candidate(name,block,direct,makes):
    raw=block["text"]
    active=d.composition_audit.active_text(raw)
    need("688" in active.splitlines()[:8] and "site_check_override" not in active.splitlines(),
         "C03EA_MODEL_FORMAT:"+name)
    verts=VERTICES[name].split()
    header=active.split("begin_ordered_endmembers",1)[0]
    # Transcribed source vertex rows must occur in order, without duplicates.
    seen=[token for line in header.splitlines() if line.split() and all(x in verts for x in line.split())
          for token in line.split()]
    need(seen==verts and len(set(verts))==len(verts),"C03EA_VERTEX_ROWS:"+name)
    ordered=equations(section(active,"ordered_endmembers"))
    dependent=equations(section(active,"dependent_endmembers"))
    need(not set(ordered)&set(dependent),"C03EA_DUPLICATE_LOCAL")
    local={**ordered,**dependent}
    roots=set()
    used=set()
    vectors={}
    for k in verts:
        v=resolve(k,direct,local,makes,roots,used)
        need(set(v)<=set(d.ORDER) and sum(v.values())>0,"C03EA_VERTEX_BASIS:"+k)
        # Green Ti-tschermak vertices are deprotonated (zero H2O in this basis).
        expected_water=0 if name=="cAmph(G)" and k in {"tts_q","mtts_d","ftts_d","fctts_d"} else 1
        need(v.get("H2O",Fraction(0))==expected_water,"C03EA_VERTEX_WATER:"+k)
        vectors[k]={c:str(a) for c,a in sorted(v.items())}
    need(roots==set(ROOTS[name].split()) and used==set(MAKE_NAMES[name]),"C03EA_ROOT_DRIFT:"+name)
    dqf=section(active,"dqf_corrections")
    for k in used:
        need(re.search(r"(?im)^\s*dqf\("+re.escape(k)+r"\)\s*=",dqf) is not None,
             "C03EA_MAKE_NOT_ACTIVATED:"+k)
    # Retain comments as evidence of dataset-specific calibrations, not active input.
    ds_lines=[line.strip() for line in section(raw,"dqf_corrections").splitlines()
              if re.search(r"\bds[56]\b",line,re.I)]
    if name in ("cAmph(DP)","cAmph_I(DP)"):
        need(any("ds6" in x and not x.startswith("|") for x in ds_lines)
             and any("ds5" in x and x.startswith("|") for x in ds_lines),
             "C03EA_DATASET_ANNOTATION_DRIFT:"+name)
    return {"vertex_count":len(verts),"vertices":vectors,"direct_roots":sorted(roots),
            "used_global_makes":sorted(used),"ordered_definitions":ordered,
            "dependent_definitions":dependent,"source_block_sha256":block["normalized_text_sha256"],
            "active_dqf":dqf,"dataset_comment_lines":ds_lines,"site_check_override":False,
            "static_chemical_closure":True,"native_admission_verified":False,
            "site_population_validity_verified":False,"calibration_qualified":False}


def risk_inventory(direct,report):
    pure={}
    for label,name in d.c.PURE.items():
        need(name in direct,"C03EA_PURE_RECORD_MISSING:"+name)
        pure[label]={"name":name,"record":direct[name],"native_admission_verified":False}
    focus={k:direct[k] for k in ("O2","Si(s)","iron","H2","H2O")}
    need(focus["O2"]["eos"]==1 and focus["O2"]["coefficients"]=={"O2":"1"}
         and focus["H2O"]["eos"]==101 and focus["Si(s)"]["nonpositive"],
         "C03EA_REDOX_SOURCE_DRIFT")
    recipes={}
    for name in d.c.b.MORB:
        basis,chem=d.recipe_basis(report["candidate_cases"],name)
        mol=basis["native_moles_per_source_recipe"]
        need(mol["O2"]>0 and mol["FEO"]>0 and mol["H2O"]>0,"C03EA_RECIPE_LEDGER")
        recipes[name]={"chemistry_sha256":chem,"native_moles_per_source_recipe":mol,
            "initial_ferric_iron_fraction_of_total_iron":4*mol["O2"]/mol["FEO"],
            "initial_ferric_ratio_not_equilibrium_fugacity":True,
            "omitted_source_oxides_wt":basis["omitted_source_oxides_wt"]}
    return {"audited_pure_reference_records":pure,"redox_and_fluid_direct_records":focus,
            "recipes":recipes,"O2_component_policy":"RETAIN_FIXED_BULK_OXYGEN_LEDGER",
            "O2_species_policy_candidate":"TEST_EXCLUSION_OF_MOLECULAR_O2_SPECIES_ONLY_IF_JUSTIFIED",
            "O2_species_exclusion_authorized":False,"H2_iron_Si_reduced_phase_policy":"UNRESOLVED",
            "pure_phase_roster_policy":"NO_WHITELIST_OR_EXCLUSIONS_AUTHORIZED",
            "amphibole_overlap":"Act(M) and broader cAmph alternatives overlap; joint admission requires explicit scientific justification",
            "MnO_policy":"PRESERVE_REDUCED_RECIPES_AND_RECORD_OMISSION_NOT_ZERO_NATURAL_MNO"}


def parent():
    receipt=e.read(d.m.HERE/"c03e_reference_design_fair_receipt_v1.json")
    man=d.m.archive_manifest(e.OUT,PIN,"files_sha256")
    need(man["schema"]=="R6_C03E_REFERENCE_DESIGN_MANIFEST_V1"
         and man["source_sha"]==receipt["source_sha"]==PARENT
         and receipt["manifest_sha256"]==PIN and man["status"]==receipt["status"]==e.STATUS
         and man["C03D_manifest_sha256"]==receipt["C03D_manifest_sha256"]==e.PIN
         and man["additional_engine_runs"]==man["authorized_equilibrium_solver_calls"]==0
         and receipt["exit"]==0 and man["scientific_promotion"] is False
         and set(man["files_sha256"])=={"REFERENCE_DESIGN.json"}
         and all(man[k]==v for k,v in SCOPE.items()),"C03EA_PARENT_MANIFEST")
    prev=e.read(e.OUT/"REFERENCE_DESIGN.json")
    need(prev["status"]==e.STATUS and prev["C03D_manifest_sha256"]==e.PIN
         and prev["additional_engine_runs"]==prev["authorized_equilibrium_solver_calls"]==0
         and prev["design"]["benchmark_executable"] is False
         and all(prev[k]==v for k,v in SCOPE.items()),"C03EA_PARENT_REPORT")
    # Recheck pinned sources/chemistry from C03C, do not launch or repeat C03D.
    report,runtime,_,hp,models,_=d.audit_parent()
    need(prev["design"]==e.reference_design(report["benchmark_candidate"]),"C03EA_REFERENCE_DESIGN_DRIFT")
    return report,runtime,hp,models


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03EA_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C03EA_OUTPUT_EXISTS")
    report,runtime,hp,models=parent()
    masses=d.c.b.components(hp)
    direct=d.composition_audit.inventory(hp,masses,d.ORDER)
    makes=equations(section(d.composition_audit.active_text(hp.decode()),"makes"))
    blocks=d.c.b.model_blocks(models,tuple(VERTICES))
    candidates={k:audit_candidate(k,blocks[k],direct,makes) for k in VERTICES}
    risks=risk_inventory(direct,report)
    result={"schema":"R6_C03EA_CONFIGURATION_AUDIT_V1","status":STATUS,
            "C03E_manifest_sha256":PIN,"provider_runtime":runtime,
            "candidate_models":candidates,"configuration_risks":risks,
            "literature_scope":{"DP":"10.1111/j.1525-1314.2007.00720.x; 10.1111/j.1525-1314.2011.00959.x",
                "G":"10.1111/jmg.12211; DS6 partial melting calibration, not low-grade HP02 authority",
                "upstream_updates":"https://www.perplex.ethz.ch/perple_x_updates/perple_x_updates.html",
                "subsolidus_sensitivity":"https://hpxeosandthermocalc.org/the-hpx-eos/the-hpx-eos-families/metabasite-set/"},
            "decision":"DP_CANDIDATE_PRIORITY_FOR_CALIBRATION_REVIEW_NOT_SELECTED",
            "next":["resolve dataset-specific DQF provenance and compare complete amphibole roster alternatives",
                    "retrieve benchmark source and exact input or adopt explicitly non-exact comparison",
                    "bind redox and pure-phase admission policy before any equilibrium execution"],
            "selected_model":None,"additional_engine_runs":0,"authorized_equilibrium_solver_calls":0,
            "scientific_promotion":False,**SCOPE}
    OUT.mkdir(parents=False,exist_ok=False)
    s2.write_json(OUT/"CONFIGURATION_AUDIT.json",result)
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03EA_CONFIGURATION_AUDIT_MANIFEST_V1",
        "source_sha":head,"status":STATUS,"C03E_manifest_sha256":PIN,
        "files_sha256":{"CONFIGURATION_AUDIT.json":s2.sha(OUT/"CONFIGURATION_AUDIT.json")},
        "additional_engine_runs":0,"authorized_equilibrium_solver_calls":0,"scientific_promotion":False,**SCOPE})
    print("C03EA_PARENT_REFERENCE_DESIGN_VERIFIED",PIN)
    for k,v in candidates.items():
        print("C03EA_STATIC_CANDIDATE",k,v["vertex_count"],len(v["direct_roots"]),v["used_global_makes"])
    print("C03EA_RECIPE_REDOX_LEDGER",json.dumps(risks["recipes"],sort_keys=True))
    print("C03EA_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
    print(STATUS)
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()
