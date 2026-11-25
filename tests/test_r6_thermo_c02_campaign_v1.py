from pathlib import Path
import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c02_fair as c

ROOT=Path(__file__).resolve().parents[1]


def fixture():
    geo=c.p.c.geo
    raw,_=geo.source_bytes(ROOT/"experiments/t0_geochemical_reference_v1/data/CC__Rudnick_Gao__2014.csv",geo.SOURCES["CC__Rudnick_Gao__2014.csv"])
    inp=c.p.recipes({"status":"PROPOSED_NOT_EXECUTABLE","authorial_selection":None,"authorized_solver_calls":0,
        "selected_comparative_source_point":c.p.POINT,"references":geo.continental_reference(raw)[:2],
        "proposed_scenarios":[{"suffix":"BASE","water_wt_amount":.2,"ferric_atom_fraction":.1},
            {"suffix":"WET","water_wt_amount":1.,"ferric_atom_fraction":.1}]})["C02_UCC_BASE"]
    ox=list(inp["expected_native_wt"]);wt=[inp["expected_native_wt"][k] for k in ox]
    return inp,{"case":inp["case"],"status":0,"database":"ig","dataset":"tc_ds636",
        "P_kbar":inp["P_kbar"],"T_C":inp["T_C"],"oxides":ox,"bulk_wt":wt,
        "bulk_mol":[inp["expected_native_mol"][k] for k in ox],"phases":["test","test"],
        "phase_types":[1,1],"phase_mass_fractions":[.4,.6],"phase_comp_wt":[wt.copy(),wt.copy()],
        "bulk_res_norm":0.,"rho_kg_m3":2700.,"G_system":-800.,
        "solid_wt":1.,"melt_wt":0.,"fluid_wt":0.,"native_diagnostics":{}}


def test_missing_selection_blocks(tmp_path):
    with pytest.raises(ValueError,match="C02_EXPLICIT_AUTHORIAL_SELECTION_REQUIRED"):
        c.load_selection(tmp_path/"missing.json")


def test_selection_scope():
    sel={"selection_id":c.SELECTION,"authorial_statement":"Approvo tutte e quattro le ipotesi sperimentali C02 come ricerca non canonica.",
        "library_manifest_sha256":c.p.C02_SHA,"preflight_manifest_sha256":c.PRE_SHA,"case_order":c.IDS,
        "model_identity":c.p.c.IG,"repeats":2,"maximum_solver_calls":8,"threads":1,
        "process_timeout_s":600,"scientific_promotion":False,**c.SCOPE}
    c.check_selection(sel)
    sel["maximum_solver_calls"]=9
    with pytest.raises(ValueError,match="C02_SELECTION_SCOPE"):
        c.check_selection(sel)


def test_ig_preserves_repeated_instances():
    inp,raw=fixture()
    a=c.validate(raw,inp)
    assert a["phases"]=={"test":1.}
    assert len(a["phase_instances"])==2
    assert c.old.compare(a,a)["max_phase_instance_component_delta"]==0


@pytest.mark.parametrize("k,v",[("database","mb"),("dataset","tc_ds62"),("status",1),("P_kbar",5.),("bulk_res_norm",1e-6)])
def test_invalid_native(k,v):
    inp,raw=fixture();raw[k]=v
    with pytest.raises(ValueError):
        c.validate(raw,inp)
