"""Read-only scientific validation for S2 Earth-only native chemistry outputs."""
from __future__ import annotations

from decimal import Decimal
import math
from pathlib import Path
import re
import tomllib

from experiments.r6_thermo_provider_pilot_v1.s2_repro_protocol import (
    S2ProtocolError, check, load, stability_screen
)

EXPECTED_CASES = {"MAGEMIN_PREDEFINED_KLB1": (8.0, 800.0),
                  "MAGEMIN_CUSTOM_IG": (10.0, 1100.0)}
EXPECTED_PHASES = {"MAGEMIN_PREDEFINED_KLB1": {"ol","spl","cpx","opx"},
                   "MAGEMIN_CUSTOM_IG": {"liq","cpx","opx"}}
EXPECTED_OXIDES = {"SiO2","Al2O3","CaO","MgO","FeO","K2O",
                   "Na2O","TiO2","O","Cr2O3","H2O"}
CUSTOM = {"SiO2":48.43,"Al2O3":15.19,"CaO":11.57,"MgO":10.13,
          "FeO":6.65,"Fe2O3":1.64,"K2O":.59,"Na2O":1.87,
          "TiO2":.68,"Cr2O3":0.0,"H2O":3.0}


def finite(v):
    return type(v) in (int,float) and math.isfinite(v)


def input_basis():
    x = dict(CUSTOM)
    n = x.pop("Fe2O3")/159.69
    x["FeO"] += 2*n*71.85
    x["O"] = n*16.0
    total = sum(x.values())
    return {k:v/total for k,v in x.items()}


def within_float64_roundoff(observed, expected):
    """Serialization tolerance only: <=16 ULP of the fixed P/T setpoint.

    This is NOT a repeatability or physical P/T uncertainty threshold.
    Reject nonfinite readings, type coercion and meaningful P/T drift.
    """
    if not finite(observed) or not finite(expected):
        return False
    return abs(observed - expected) <= 16 * math.ulp(float(expected))


def check_magemin_case(c, case_id, policy):
    tol = policy["magemin_tolerances"]
    check(c.get("status") == 0 and c.get("database")=="ig"
          and c.get("dataset")=="tc_ds636",
          "S2_MAGEMIN_STATUS_OR_DATASET_DRIFT")
    p,t = EXPECTED_CASES[case_id]
    check(within_float64_roundoff(c.get("P_kbar"), p)
          and within_float64_roundoff(c.get("T_C"), t),
          "S2_MAGEMIN_PT_DRIFT")
    check(finite(c.get("G_system")) and finite(c.get("rho_kg_m3"))
          and c["rho_kg_m3"]>0 and type(c.get("iterations")) is int
          and c["iterations"]>=0,
          "S2_MAGEMIN_NUMERIC_FIELDS_INVALID")
    ph, frac = c.get("phases"), c.get("phase_mass_fractions")
    ox, bulk, comps = c.get("oxides"), c.get("bulk_wt"), c.get("phase_comp_wt")
    check(isinstance(ph,list) and isinstance(frac,list)
          and len(ph)==len(frac) and set(ph)==EXPECTED_PHASES[case_id]
          and len(set(ph))==len(ph),
          "S2_MAGEMIN_PHASE_IDENTITIES_INVALID")
    check(isinstance(ox,list) and set(ox)==EXPECTED_OXIDES
          and len(ox)==len(EXPECTED_OXIDES) and isinstance(bulk,list)
          and len(bulk)==len(ox) and isinstance(comps,list)
          and len(comps)==len(ph),
          "S2_MAGEMIN_OXIDE_COVERAGE_INVALID")
    check(all(finite(x) and x>=0 for x in frac+bulk)
          and abs(sum(frac)-1)<=tol["phase_fraction_sum_abs"]
          and abs(sum(bulk)-1)<=tol["phase_fraction_sum_abs"],
          "S2_MAGEMIN_FRACTION_SUM_INVALID")
    check(all(isinstance(v,list) and len(v)==len(ox)
              and all(finite(x) and x>=-1e-13 for x in v)
              and abs(sum(v)-1)<1e-8 for v in comps),
          "S2_MAGEMIN_PHASE_COMP_INVALID")
    predicted = [sum(frac[i]*comps[i][j] for i in range(len(ph)))
                 for j in range(len(ox))]
    delta = max(abs(a-b) for a,b in zip(predicted,bulk))
    check(delta<=tol["native_oxide_component_closure_abs"]
          and finite(c.get("bulk_res_norm"))
          and 0<=c["bulk_res_norm"]<=tol["bulk_res_norm_max"]
          and finite(c.get("native_component_weight_closure_abs"))
          and abs(delta-c["native_component_weight_closure_abs"])<1e-12,
          "S2_MAGEMIN_NATIVE_BULK_CHEMISTRY_FAIL")
    source_delta=None
    if case_id=="MAGEMIN_CUSTOM_IG":
        basis=input_basis()
        source_delta=max(abs(bulk[ox.index(k)]-v) for k,v in basis.items())
        check(source_delta<=tol["source_to_native_component_closure_abs"]
              and finite(c.get("source_native_basis_closure_custom"))
              and abs(source_delta-c["source_native_basis_closure_custom"])<1e-12,
              "S2_MAGEMIN_INPUT_BASIS_CHEMISTRY_FAIL")
    return {"max_native_component_delta":delta,
            "max_source_input_basis_delta":source_delta,
            "bulk_res_norm":c["bulk_res_norm"],
            "G_system":c["G_system"],
            "rho_kg_m3":c["rho_kg_m3"],
            "phases":dict(zip(ph,frac))}


def check_magemin_report(report,policy=None):
    policy=load() if policy is None else policy
    check(report.get("schema")=="ARCANA_R6_THERMO_S2_MAGEMIN_NATIVE_RUN_V1"
          and report.get("scope")=="EARTH_FIXTURES_ONLY"
          and report.get("provider")=="MAGEMin_C.jl"
          and report.get("provider_version")=="2.4.5"
          and report.get("D_024")=="ACTIVE"
          and report.get("physical_T1_is_null") is True
          and report.get("cross_provider_equivalence") is False
          and report.get("WORLD_HISTORY_PRODUCTION_AUTHORIZED") is False,
          "S2_MAGEMIN_REPORT_PROVENANCE_INVALID")
    cases=report.get("cases",{})
    check(isinstance(cases,dict) and set(cases)==set(EXPECTED_CASES),
          "S2_MAGEMIN_CASE_SET_DRIFT")
    return {k:check_magemin_case(cases[k],k,policy)
            for k in sorted(EXPECTED_CASES)}


def read_magemin(path,policy=None):
    with Path(path).open("rb") as f:
        return check_magemin_report(tomllib.load(f),policy)


def interval(token):
    v=Decimal(token)
    check(v.is_finite() and v>=0, "S2_PERPLEX_NONFINITE_MOLE_NUMBER")
    r=Decimal("0.5").scaleb(v.as_tuple().exponent)
    return max(Decimal(0),v-r),v+r


def check_perplex_native_prn(prn_text,policy=None):
    policy=load() if policy is None else policy
    check(prn_text.count("Phase Compositions (molar  proportions):")==1
          and prn_text.count("Phase speciation")>=1
          and prn_text.count("Bulk Composition:")==1,
          "S2_PERPLEX_PRN_SECTIONS_MISSING")
    phase=prn_text.split("Phase Compositions (molar  proportions):",1)[1].split("Phase speciation",1)[0]
    rows=[x for x in phase.splitlines() if x.strip()]
    header=re.split(r"\s{2,}",rows[0].strip())
    check(header[:4]==["wt %","vol %","mol %","mol"],
          "S2_PERPLEX_PHASE_COLUMN_HEADER_INVALID")
    oxides=header[4:]
    check(set(oxides)=={"Na2O","MgO","Al2O3","K2O","CaO",
                         "TiO2","FeO","O2","H2O","SiO2"}
          and len(oxides)==10,"S2_PERPLEX_OXIDE_SET_INVALID")
    phases={}
    for line in rows[1:]:
        fields=line.split()
        check(len(fields)==5+len(oxides),"S2_PERPLEX_PHASE_ROW_WIDTH_INVALID")
        name=fields[0]
        check(name not in phases,"S2_PERPLEX_PHASE_DUPLICATE")
        phases[name]={"wt":float(fields[1]),"mol":fields[4],
                      "comp":dict(zip(oxides,fields[5:]))}
    check(set(phases)=={"cAmph(G)","Augite(G)","melt(G)",
                       "Ilm(WPH)","Fsp(C1)","q"},
          "S2_PERPLEX_PHASE_IDENTITIES_INVALID")
    bulk=prn_text.split("Bulk Composition:",1)[1].split("Other Bulk Properties:",1)[0]
    mol={}
    for line in bulk.splitlines():
        f=line.split()
        if f and f[0] in oxides:
            check(f[0] not in mol and len(f)==9,
                  "S2_PERPLEX_BULK_ROW_INVALID")
            mol[f[0]]=f[1]
    check(set(mol)==set(oxides),"S2_PERPLEX_BULK_OXIDE_COVERAGE_INVALID")
    obs={}
    for oxide in oxides:
        reconstructed=Decimal(0)
        lower=Decimal(0)
        upper=Decimal(0)
        for ph in phases.values():
            n,c=Decimal(ph["mol"]),Decimal(ph["comp"][oxide])
            nlo,nhi=interval(ph["mol"])
            clo,chi=interval(ph["comp"][oxide])
            reconstructed+=n*c
            lower+=nlo*clo
            upper+=nhi*chi
        observed=Decimal(mol[oxide])
        olo,ohi=interval(mol[oxide])
        check(lower<=ohi and upper>=olo,
              "S2_PERPLEX_PRINTED_MOLAR_COMPONENT_MISMATCH_"+oxide)
        obs[oxide]={"reported_mol":str(observed),
                    "reconstructed_mol":str(reconstructed),
                    "delta_mol":str(reconstructed-observed),
                    "rounding_compatible":True}
    check(abs(sum(x["wt"] for x in phases.values())-100.0)<=0.05,
          "S2_PERPLEX_PHASE_WEIGHTS_NOT_CLOSED")
    return {"phase_wt_percent":{k:v["wt"] for k,v in phases.items()},
            "printed_oxide_molar_rounding_audit":obs,
            "component_count":len(obs)}


def compare_magemin_runs(runs,policy=None):
    policy=load() if policy is None else policy
    check(len(runs)==policy["runs_per_case"],"S2_MAGEMIN_RUN_COUNT_INVALID")
    tol=policy["magemin_tolerances"]
    results={}
    for case in EXPECTED_CASES:
        values=[x[case] for x in runs]
        ids=[set(v["phases"]) for v in values]
        check(all(s==ids[0] for s in ids),"S2_PHASE_SET_CHANGED")
        bounds={}
        checks=[("G_system",tol["g_system_abs_kj_per_mol"],tol["g_system_rel"]),
                ("rho_kg_m3",tol["rho_abs_kg_per_m3"],tol["rho_rel"])]
        for phase in sorted(ids[0]):
            checks.append(("phase:"+phase,tol["phase_fraction_abs"],
                            tol["phase_fraction_rel"]))
        for name,abs_tol,rel_tol in checks:
            data=[v["phases"][name[6:]] if name.startswith("phase:")
                  else v[name] for v in values]
            for a in data:
                for b in data:
                    check(stability_screen(a,b,abs_tol,rel_tol),
                          "S2_MAGEMIN_REPEATABILITY_SCREEN_FAIL_"+name)
            delta=max(data)-min(data)
            rel=delta/max(1e-30,max(abs(x) for x in data))
            bounds[name]={"max_absolute_delta":delta,
                          "max_relative_delta":rel}
        results[case]=bounds
    return results


def compare_perplex_runs(runs,policy=None):
    policy=load() if policy is None else policy
    check(len(runs)==policy["runs_per_case"],"S2_PERPLEX_RUN_COUNT_INVALID")
    tol=policy["perplex_tolerances"]
    phases=set(runs[0]["phase_wt_percent"])
    check(all(set(r["phase_wt_percent"])==phases for r in runs),
          "S2_PERPLEX_PHASE_SET_CHANGED")
    result={}
    for ph in sorted(phases):
        data=[v["phase_wt_percent"][ph] for v in runs]
        for a in data:
            for b in data:
                check(stability_screen(a,b,tol["phase_percent_abs_pp"],
                                       tol["phase_percent_rel"]),
                      "S2_PERPLEX_REPEATABILITY_SCREEN_FAIL_"+ph)
        result[ph]={"max_absolute_percentage_point_delta":max(data)-min(data),
                    "max_relative_delta":(max(data)-min(data))/max(1e-30,max(data))}
    return result
