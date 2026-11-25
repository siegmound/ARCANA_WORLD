"""C03 source-driven cold crust design; no thermodynamic solver or new assignments."""
from __future__ import annotations
import argparse
from collections import Counter
import json
import re
from experiments.r6_thermo_provider_pilot_v1 import run_c02_consolidation as a
from experiments.r6_thermo_provider_pilot_v1 import s3_d5_hgp_prepare as hgp

m=a.m
s2=a.s2
need=a.need
SCOPE=a.SCOPE
PARENT="868adc6ec5a1c58491d9656051fc7a0001949149"
PIN="7d0db630d22320f86a928915426aa81b3ce98e3462542a830101e3ec1bae87db"
OUT=s2.BASE/"R6_THERMO_C03_COLD_CRUST_DESIGN_NEW01"
# Exact D11 original samples, not inferred pressure or selected rock strata.
POINTS=((35304,7000),(36026,14000))
PROVIDER_REFERENCES={
    "metapelite":{"source":"https://doi.org/10.1111/jmg.12071",
        "candidate":"MAGEMin mp / White et al. 2014","scope":"metapelitic compositions only; not generic UCC/MCC"},
    "low_grade_metabasite":{"source":"https://doi.org/10.1111/j.1525-1314.1991.tb00542.x",
        "candidate":"Perple_X with independently justified low-grade models",
        "scope":"simplified NCMASH petrogenetic grid; not full MORB validation"},
    "low_grade_application":{"source":"https://doi.org/10.1029/2018JE005869",
        "candidate":"Perple_X low-grade basalt assemblages","scope":"published application, not installed-model parity"},
    "fixed_assemblage":{"source":"https://doi.org/10.1111/j.1525-1314.2010.00923.x",
        "candidate":"mineral EOS for inherited assemblages","scope":"requires independent phase identity/modal fractions and kinetic authority"},
}


def load_consolidated():
    rec=json.loads((m.HERE/"c02_consolidation_fair_receipt_v1.json").read_text())
    man=m.archive_manifest(a.OUT,PIN,"files_sha256")
    need(man["schema"]=="R6_C02_CONSOLIDATED_REGIONAL_COVERAGE_MANIFEST_V1"
        and man["source_sha"]==rec["source_sha"]==PARENT
        and rec["manifest_sha256"]==PIN and rec["exit"]==0
        and man["C02_campaign_manifest_sha256"]==a.CAMPAIGN_SHA
        and man["PT_manifest_sha256"]==a.PT_SHA
        and man["previous_library_manifest_sha256"]==a.p.C02_SHA
        and man["states"]==31 and man["chemistries"]==14 and man["source_solver_processes"]==62
        and man["samples"]==3700 and man["additional_engine_runs"]==0
        and set(man["files_sha256"])=={"LIBRARY.json","REGIONAL_COVERAGE.json"}
        and all(man[k]==v for k,v in SCOPE.items()),"C03_PARENT_MANIFEST")
    lib=json.loads((a.OUT/"LIBRARY.json").read_text())
    cov=json.loads((a.OUT/"REGIONAL_COVERAGE.json").read_text())
    need(lib["source_sha"]==PARENT and len(lib["states"])==31
        and len({v["chemistry_sha256"] for v in lib["states"].values()})==14
        and cov["regions"]==rec["regions"] and cov["physical_material_coverage_count"]==0
        and len(cov["samples"])==3700 and all(cov[k]==v for k,v in SCOPE.items()),"C03_PARENT_CONTENT")
    return lib,cov


def sample_points(cov):
    out=[]
    for node,depth in POINTS:
        rows=[r for r in cov["samples"] if r["extent"]==8 and r["layer"]=="crust"
              and r["parent_node_id"]==node and r["source_depth_m"]==depth]
        need(len(rows)==1,"C03_SOURCE_POINT_MISSING")
        r=rows[0]
        need(r["absolute_pressure_pa"] is None and r["material_recipe"] is None
            and r["spatial_assignment"] is None,"C03_SOURCE_AUTHORITY")
        out.append({"parent_node_id":node,"depth_m":depth,"T_K":r["source_temperature_K"],
            "T_C":r["source_temperature_K"]-273.15,"conditional_delta_P_kbar":r["conditional_delta_P_kbar"],
            "absolute_pressure_pa":None,"pressure_semantics":"HYPOTHETICAL_COMPARATIVE_ONLY"})
    return out


def cold_cohort(cov):
    # Group only by exact P/T to avoid confusing repeated coordinates with independent experiments.
    groups={}
    for extent in (8,16):
        rows=[r for r in cov["samples"] if r["extent"]==extent and r["layer"]=="crust"]
        need(len(rows)==5*(extent+1)**2,"C03_COHORT_COUNT")
        cold=[r for r in rows if r["source_temperature_K"]-273.15<650]
        counts=Counter(a.coordinate(r["conditional_delta_P_kbar"],r["source_temperature_K"]-273.15) for r in cold)
        groups[str(extent)]={"samples":len(rows),"below_prior_design_filter":len(cold),
            "unique_exact_cold_PT_coordinates":len(counts),
            "zero_conditional_overburden":sum(r["conditional_delta_P_kbar"]==0 for r in cold),
            "most_common_cold_PT":[{"P_kbar":float.fromhex(k[0]),"T_C":float.fromhex(k[1]),"count":n}
                for k,n in sorted(counts.items(),key=lambda kv:(-kv[1],kv[0]))[:8]]}
        need(len(cold)==cov["regions"][str(extent)]["crust"]["below_felsic_design_T_min"],"C03_COLD_COUNT_DRIFT")
    return groups


def candidate_tokens(raw):
    # Header-like sightings only, NOT parsed or calibrated solution models.
    names=("Chl(W)","Chl(HP)","Mica(W)","Ep(HP11)","Pu(M)","Fsp(HGP)","lAb(HGP)")
    return {name:len(re.findall(rb"(?m)^"+re.escape(name.encode())+rb"[ \t]+[^\r\n]*",raw)) for name in names}


def proposed_design(lib,cov,perplex_inputs):
    points=sample_points(cov)
    # Retain existing recipe identifiers; never silently recast a composition between models.
    cases={}
    for v in lib["states"].values():
        if v["case"] in ("C01_MORB_BASE","C01_MORB_WET","C02_UCC_BASE","C02_UCC_WET"):
            cases[v["case"]]={"chemistry_sha256":v["chemistry_sha256"],"model_identity":v["model_identity"],
                "source_input":v["input"],"target_model":None,"target_basis_conversion":None}
    need(len(cases)==4,"C03_RECIPE_SOURCE")
    return {"schema":"R6_C03_COLD_CRUST_RESEARCH_DESIGN_V1","status":"PROVIDER_SELECTION_PENDING",
        "consolidation_manifest_sha256":PIN,"original_PT_manifest_sha256":a.PT_SHA,
        "cohort":cold_cohort(cov),"candidate_source_points":points,
        "reference_recipes":cases,"provider_references":PROVIDER_REFERENCES,
        "perplex_pinned_solution_file_header_sightings":candidate_tokens(perplex_inputs["solution_model.dat"]),
        "perplex_sightings_are_not_model_qualification":True,
        "comparative_matrix_candidate":[{"source_recipe":name,"source_point":point["parent_node_id"]}
            for name in sorted(cases) for point in points],
        "proposed_points":8,"authorized_solver_calls":0,"authorial_selection":None,
        "pressure_boundary_required_for_physical_initialization":True,
        "near_surface_policy":"UNKNOWN_ABSOLUTE_PRESSURE_NO_ZERO_PRESSURE_EQUILIBRIUM",
        "cold_kinetic_policy":"EQUILIBRIUM_CANDIDATE_AND_INHERITED_ASSEMBLAGE_DISTINCT",
        "MORB_source_promotion_pending":True,
        "required_before_campaign":["exact provider version and phase/basis selection",
            "primary-source model-domain and chemistry review","source-preserving native conversion",
            "bounded research authorization"],"additional_engine_runs":0,**SCOPE}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03_CHECKOUT")
    need(not OUT.exists(),"C03_OUTPUT_EXISTS")
    lib,cov=load_consolidated()
    # The original reports were independently replayed in the pinned parent.
    print("C03_PARENT_CONSOLIDATION_HASH_AUDIT_PASS",PIN,flush=True)
    inputs,_,runtime=hgp.verify_runtime_and_inputs()
    design=proposed_design(lib,cov,inputs)
    OUT.mkdir(parents=False,exist_ok=False)
    s2.write_json(OUT/"DESIGN.json",design)
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03_COLD_CRUST_DESIGN_MANIFEST_V1",
        "source_sha":head,"consolidation_manifest_sha256":PIN,
        "perplex_runtime":runtime,"additional_engine_runs":0,"authorized_solver_calls":0,
        "files_sha256":{"DESIGN.json":s2.sha(OUT/"DESIGN.json")},**SCOPE})
    print("C03_COLD_COHORT",json.dumps(design["cohort"],sort_keys=True))
    print("C03_SOURCE_POINTS",json.dumps(design["candidate_source_points"],sort_keys=True))
    print("C03_PERPLEX_HEADER_SIGHTINGS",json.dumps(design["perplex_pinned_solution_file_header_sightings"],sort_keys=True))
    print("C03_DESIGN_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
    print("C03_COLD_CRUST_DESIGN_COMPLETE__PROVIDER_SELECTION_PENDING")
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()
