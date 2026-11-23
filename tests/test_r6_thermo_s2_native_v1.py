"""S2 native output/chemistry and stability tests. No Julia/MEEMUM invoked."""
from __future__ import annotations

import copy
from pathlib import Path
import pytest

from experiments.r6_thermo_provider_pilot_v1.s2_repro_protocol import S2ProtocolError
from experiments.r6_thermo_provider_pilot_v1.validate_s2_native import (
    check_magemin_report, check_perplex_native_prn,
    compare_magemin_runs, compare_perplex_runs, input_basis
)


@pytest.fixture
def native_report():
    bulk = {"SiO2":.5,"Al2O3":.2,"CaO":0.0,"MgO":0.0,
            "FeO":.3,"K2O":0.0,"Na2O":0.0,"TiO2":0.0,
            "O":0.0,"Cr2O3":0.0,"H2O":0.0}
    native_order = list(bulk)
    def case(phases,frac,wt,p,t,g,rho,custom=False):
        return {
            "status":0, "P_kbar":p,"T_C":t,"G_system":g,
            "rho_kg_m3":rho,"phases":phases,
            "phase_mass_fractions":frac, "oxides":native_order,
            "bulk_wt":[wt[x] for x in native_order],
            "phase_comp_wt":[[wt[x] for x in native_order]
                             for _ in phases],
            "bulk_res_norm":1e-13, "iterations":25,
            "source_native_basis_closure_custom":0.0 if custom else -1.0,
            "native_component_weight_closure_abs":0.0,
            "database":"ig","dataset":"tc_ds636"
        }
    return {
        "schema":"ARCANA_R6_THERMO_S2_MAGEMIN_NATIVE_RUN_V1",
        "scope":"EARTH_FIXTURES_ONLY", "provider":"MAGEMin_C.jl",
        "provider_version":"2.4.5",
        "cross_provider_equivalence":False,"physical_T1_is_null":True,
        "D_024":"ACTIVE","WORLD_HISTORY_PRODUCTION_AUTHORIZED":False,
        "cases":{
            "MAGEMIN_PREDEFINED_KLB1":case(
                ["ol","spl","cpx","opx"],[.58,.03,.15,.24],
                bulk,8.0,800.0,-797.787387,3281.233),
            "MAGEMIN_CUSTOM_IG":case(
                ["liq","cpx","opx"],[.73,.25,.02],
                input_basis(),10.0,1100.0,-916.834776,2796.559,True)
        }
    }


def test_native_report_chemistry_pass(native_report):
    obs=check_magemin_report(native_report)
    assert set(obs)=={"MAGEMIN_PREDEFINED_KLB1","MAGEMIN_CUSTOM_IG"}
    assert obs["MAGEMIN_CUSTOM_IG"]["max_source_input_basis_delta"]==0


@pytest.mark.parametrize(("case","field","value"),[
    ("MAGEMIN_CUSTOM_IG","status",1),
    ("MAGEMIN_CUSTOM_IG","dataset","wrong"),
    ("MAGEMIN_CUSTOM_IG","bulk_res_norm",.1),
    ("MAGEMIN_CUSTOM_IG","iterations",-1),
    ("MAGEMIN_CUSTOM_IG","phases",["liq","opx","opx"]),
    ("MAGEMIN_PREDEFINED_KLB1","P_kbar",8.1),
    ("MAGEMIN_CUSTOM_IG","source_native_basis_closure_custom",0.1),
])
def test_s2_native_failure_cases(native_report,case,field,value):
    c=copy.deepcopy(native_report)
    c["cases"][case][field]=value
    with pytest.raises(S2ProtocolError):
        check_magemin_report(c)


def test_mutated_oxide_balance_is_rejected(native_report):
    c=copy.deepcopy(native_report)
    c["cases"]["MAGEMIN_CUSTOM_IG"]["phase_comp_wt"][0][0]+=.01
    with pytest.raises(S2ProtocolError):
        check_magemin_report(c)


def test_source_input_basis_crosswalk_rejected(native_report):
    c=copy.deepcopy(native_report)
    c["cases"]["MAGEMIN_CUSTOM_IG"]["bulk_wt"][0]+=.00001
    c["cases"]["MAGEMIN_CUSTOM_IG"]["bulk_wt"][1]-=.00001
    c["cases"]["MAGEMIN_CUSTOM_IG"]["phase_comp_wt"]=[
        list(c["cases"]["MAGEMIN_CUSTOM_IG"]["bulk_wt"])
        for _ in range(3)
    ]
    with pytest.raises(S2ProtocolError):
        check_magemin_report(c)


def test_all_five_equal_fresh_reports_compare(native_report):
    obs=check_magemin_report(native_report)
    result=compare_magemin_runs([obs]*5)
    assert result["MAGEMIN_CUSTOM_IG"]["G_system"]["max_absolute_delta"]==0.0


def test_five_fresh_processes_are_mandatory(native_report):
    obs=check_magemin_report(native_report)
    with pytest.raises(S2ProtocolError):
        compare_magemin_runs([obs]*4)


def test_stability_fail_closed_on_one_large_numeric_drift(native_report):
    obs=check_magemin_report(native_report)
    runs=[copy.deepcopy(obs) for _ in range(5)]
    runs[-1]["MAGEMIN_CUSTOM_IG"]["G_system"]+=1
    with pytest.raises(S2ProtocolError):
        compare_magemin_runs(runs)


def synthetic_perplex():
    oxides=["Na2O","MgO","Al2O3","K2O","CaO","TiO2",
            "FeO","O2","H2O","SiO2"]
    names=["cAmph(G)","Augite(G)","melt(G)",
           "Ilm(WPH)","Fsp(C1)","q"]
    rows=[]
    for name,wt in zip(names,[50,10,10,10,10,10]):
        vals=["0.00000"]*9+["1.00000"]
        rows.append("  "+" ".join(
            [name,f"{wt:.2f}","10.00","10.00","1.000",*vals]
        ))
    bulk=[]
    for name in oxides:
        value="6.000" if name=="SiO2" else "0.000"
        bulk.append("   "+" ".join([name,value,*["0.000"]*7]))
    return "\n".join([
        "Phase Compositions (molar  proportions):",
        "   wt %      vol %     mol %     mol        "+"     ".join(oxides),
        *rows,"",
        "Phase speciation (molar proportions):","",
        "Bulk Composition:",
        "       Complete Assemblage                         Solid Only",
        "   mol        g         wt %      mol/kg",
        *bulk,"","Other Bulk Properties:"
    ])


def test_perplex_native_print_rounding_valid():
    r=check_perplex_native_prn(synthetic_perplex())
    assert r["component_count"]==10


def test_perplex_printed_wrong_bulk_rejected():
    r=synthetic_perplex().replace("SiO2 6.000","SiO2 7.000")
    with pytest.raises(S2ProtocolError):
        check_perplex_native_prn(r)


def test_perplex_missing_component_rejected():
    r=synthetic_perplex().replace("SiO2 6.000","ZnO 6.000")
    with pytest.raises(S2ProtocolError):
        check_perplex_native_prn(r)


def test_perplex_five_run_phase_stability():
    r=check_perplex_native_prn(synthetic_perplex())
    cmp=compare_perplex_runs([r]*5)
    assert len(cmp)==6
    x=[copy.deepcopy(r) for _ in range(5)]
    x[-1]["phase_wt_percent"]["q"]=20.0
    with pytest.raises(S2ProtocolError):
        compare_perplex_runs(x)


def test_runner_stage_requires_explicit_invocation():
    source=(Path(__file__).resolve().parents[1]/
            "experiments/r6_thermo_provider_pilot_v1/run_s2_fair.py").read_text()
    assert 'if __name__=="__main__":' in source
    assert "S2_REAL_OUTPUT_WRITE_ONCE_ALREADY_EXISTS" in source
    assert "S2_SOURCE_PREFLIGHT_PASS" in source
    assert "S2_REAL_ENGINE_REPEATABILITY_SCREEN_PASS" in source
