from pathlib import Path
import pytest
from experiments.r6_thermo_provider_pilot_v1 import c02_conversion_preflight as q
ROOT=Path(__file__).resolve().parents[1]

def inputs():
    raw,_=q.c.geo.source_bytes(ROOT/"experiments/t0_geochemical_reference_v1/data/CC__Rudnick_Gao__2014.csv",q.c.geo.SOURCES["CC__Rudnick_Gao__2014.csv"])
    refs=q.c.geo.continental_reference(raw)[:2]
    return q.recipes({"status":"PROPOSED_NOT_EXECUTABLE","authorial_selection":None,"authorized_solver_calls":0,
        "selected_comparative_source_point":q.POINT,"references":refs,
        "proposed_scenarios":[{"suffix":"BASE","water_wt_amount":.2,"ferric_atom_fraction":.1},
            {"suffix":"WET","water_wt_amount":1.,"ferric_atom_fraction":.1}]})

def test_chemistry_source_and_ledger():
    cases=inputs()
    assert len(cases)==4
    assert cases["C02_UCC_BASE"]["Cr_source_ppm"]==92
    assert cases["C02_MCC_BASE"]["Cr_source_ppm"]==76
    assert cases["C02_UCC_BASE"]["Cr2O3_equivalent_wt_amount"]==pytest.approx(0.0134462069271,rel=1e-4)
    for label in ("UCC","MCC"):
        a,b=(cases[f"C02_{label}_{s}"] for s in ("BASE","WET"))
        assert b["reduced_input_sum"]-a["reduced_input_sum"]==pytest.approx(.8)
        assert set(a["expected_native_mol"])==q.m.NATIVE
        assert set(a["omitted_source_oxides_wt"])=={"MnO","P2O5"}

def fake(inp):
    ox=list(inp["expected_native_mol"])
    return {"oxides":ox,"mol_fraction":[inp["expected_native_mol"][k] for k in ox],
        "wrapper_git_blob":q.p.WRAPPER,"info_git_blob":q.p.INFO,"registry_git_blob":q.p.REGISTRY,"minimization_calls":0}

def test_exact_conversion():
    inp=inputs()["C02_UCC_BASE"]
    assert q.review(fake(inp),inp)["status"]=="INPUT_PRESERVED"

def test_guard_drift_is_blocked_and_preserved():
    inp=inputs()["C02_UCC_BASE"];out=fake(inp)
    i=out["oxides"].index("Cr2O3");j=out["oxides"].index("SiO2")
    out["mol_fraction"][i]+=1e-5;out["mol_fraction"][j]-=1e-5
    a=q.review(out,inp)
    assert a["status"]=="BLOCKED_NATIVE_GUARD_OR_CONVERSION_CHANGED_INPUT"
    assert a["component_mole_fraction_delta"]["Cr2O3"]==pytest.approx(1e-5)

def test_no_authority():
    assert q.SCOPE["authorial_selection"] is None
    assert not q.SCOPE["minimization_authorized"]
    assert q.SCOPE["additional_engine_runs"]==0
