from pathlib import Path
from copy import deepcopy
import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c01_fair as c

ROOT=Path(__file__).resolve().parents[1]


def fixture():
    _,cases,_=c.selected(ROOT)
    inp=cases["C01_LCC_BASE"]
    ox=list(inp["expected_native_wt"]);wt=[inp["expected_native_wt"][k] for k in ox]
    raw={"case":inp["case"],"status":0,"database":"mb","dataset":"tc_ds62",
        "P_kbar":inp["P_kbar"],"T_C":inp["T_C"],"oxides":ox,"bulk_wt":wt,
        "bulk_mol":[inp["expected_native_mol"][k] for k in ox],
        "phases":["test","test"],"phase_types":[1,1],"phase_mass_fractions":[.4,.6],
        "phase_comp_wt":[wt,wt],"bulk_res_norm":0.,"G_system":-800.,"rho_kg_m3":3000.,
        "solid_wt":1.,"melt_wt":0.,"fluid_wt":0.,"native_diagnostics":{}}
    return inp,raw


def test_approved_scope():
    _,cases,s=c.selected(ROOT)
    assert len(cases)==6 and s["maximum_solver_calls"]==12
    assert not s["mechanical_solve_authorized"] and s["physical_T1"] is None


def test_preserve_duplicate_phase_instances():
    inp,raw=fixture();a=c.validate(raw,inp)
    assert a["phases"]=={"test":1.}
    assert len(a["phase_instances"])==2
    assert c.compare(a,a)["max_phase_instance_component_delta"]==0.


@pytest.mark.parametrize("key,value,err",[
    ("database","ig","C01_NATIVE_STATUS"),("dataset","tc_ds636","C01_NATIVE_STATUS"),
    ("P_kbar",5.8,"C01_NATIVE_PT"),("bulk_res_norm",1e-6,"C01_NATIVE_CLOSURE")])
def test_invalid_primary(key,value,err):
    inp,raw=fixture();raw[key]=value
    with pytest.raises(ValueError,match=err):
        c.validate(raw,inp)


def test_repeat_instances_not_lost():
    inp,raw=fixture();a=c.validate(raw,inp);b=deepcopy(a)
    b["phase_instances"].pop()
    with pytest.raises(ValueError,match="C01_REPEAT_INSTANCE_COUNT"):
        c.compare(a,b)


def test_unqualified_secondary_diagnostics_explicit():
    inp,raw=fixture()
    assert c.diagnostic_review(c.validate(raw,inp),inp["T_C"])["algebraic_identity_status"]=="UNQUALIFIED_OR_INCONSISTENT"
