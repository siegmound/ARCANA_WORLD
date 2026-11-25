from pathlib import Path
import pytest
from experiments.r6_thermo_provider_pilot_v1 import c01_conversion_preflight as p

ROOT=Path(__file__).resolve().parents[1]

def inputs():
    return p.recipes(p.c.check_design(ROOT)[0])

def test_six_recipes_and_explicit_omissions():
    x=inputs()
    assert len(x)==6
    for v in x.values():
        assert set(v["expected_native_mol"])==p.NATIVE
        assert len(v["names"])==10
        assert set(v["omitted_source_oxides_wt"])=={"MnO","P2O5"}
        assert v["unaccounted_source_mass"] is None
        assert sum(v["expected_native_mol"].values())==pytest.approx(1.)
        assert sum(v["expected_native_wt"].values())==pytest.approx(1.)

def test_water_and_redox_independent():
    x=inputs()
    for label in ("LCC","MORB"):
        a,b,c=(x[f"C01_{label}_{s}"] for s in ("BASE","WET","OXIDIZED"))
        assert b["reduced_input_sum"]-a["reduced_input_sum"]==pytest.approx(.8)
        assert c["added_H2O_wt_amount"]==a["added_H2O_wt_amount"]
        assert c["added_oxygen_from_ferric_split_wt_amount"]==pytest.approx(2*a["added_oxygen_from_ferric_split_wt_amount"])

def test_conversion_guard():
    a=inputs()["C01_LCC_BASE"]
    ox=list(a["expected_native_mol"])
    out={"oxides":ox,"mol_fraction":[a["expected_native_mol"][k] for k in ox],
         "wrapper_git_blob":p.WRAPPER,"info_git_blob":p.INFO,"registry_git_blob":p.REGISTRY,"minimization_calls":0}
    assert p.check_conversion(out,a)==0
    out["mol_fraction"][0]+=.001
    out["mol_fraction"][1]-=.001
    with pytest.raises(ValueError,match="C01_NATIVE_CONVERSION_CHANGED_INPUT"):
        p.check_conversion(out,a)

def test_no_thermodynamic_authority():
    assert p.SCOPE["authorial_selection"] is None
    assert p.SCOPE["minimization_authorized"] is False
    assert p.SCOPE["additional_engine_runs"]==0
