from pathlib import Path
from copy import deepcopy
import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_m01_fair as m

ROOT=Path(__file__).resolve().parents[1]


def test_approved_source_inputs():
    x=m.build_inputs(ROOT)
    assert list(x)==[a[0] for a in m.CASES]
    assert x["M01_BASE"]["input_total"]==pytest.approx(99.80429745066961)
    assert x["M01_LOW_H2O"]["wt_amounts"][-1]==.0058
    assert x["M01_HIGH_H2O"]["wt_amounts"][-1]==.0174
    assert x["M01_HIGH_FERRIC"]["expected_native_mol"]["O"]>x["M01_BASE"]["expected_native_mol"]["O"]


def fixture():
    inp=m.build_inputs(ROOT)["M01_BASE"]
    ox=list(inp["expected_native_wt"])
    wt=[inp["expected_native_wt"][k] for k in ox]
    mol=[inp["expected_native_mol"][k] for k in ox]
    c={"case":inp["case"],"status":0,"database":"ig","dataset":"tc_ds636",
       "P_kbar":m.P,"T_C":m.T,"oxides":ox,"bulk_wt":wt,"bulk_mol":mol,
       "phases":["synthetic"],"phase_mass_fractions":[1.],"phase_comp_wt":[wt.copy()],
       "bulk_res_norm":0.,"G_system":-800.,"rho_kg_m3":3300.,"solid_wt":1.,"melt_wt":0.,
       "fluid_wt":0.,"native_diagnostics":{}}
    return c,inp


def test_synthetic_closure_and_repetition():
    c,inp=fixture()
    a=m.validate(c,inp)
    assert a["phase_component_closure"]==0.
    assert all(v==0 for v in m.compare(a,a).values())


@pytest.mark.parametrize("key,value",[
    ("status",5),("P_kbar",16.0),("rho_kg_m3",0.),("bulk_res_norm",1e-5),
    ("melt_wt",.2),("phase_mass_fractions",[.9]),("database","mp")])
def test_invalid_native(key,value):
    c,inp=fixture()
    c[key]=value
    with pytest.raises(ValueError):
        m.validate(c,inp)


def test_silent_water_truncation_rejected():
    c,inp=fixture()
    ox=c["oxides"];i=ox.index("H2O")
    c["bulk_mol"][0]+=c["bulk_mol"][i]
    c["bulk_mol"][i]=0.
    with pytest.raises(ValueError,match="M01_NATIVE_INPUT_DRIFT"):
        m.validate(c,inp)


def test_repeatability_rejects_phase_change():
    c,inp=fixture()
    a=m.validate(c,inp)
    b=deepcopy(a);b["phases"]={"other":1.}
    with pytest.raises(ValueError,match="M01_REPEAT_PHASE_SET"):
        m.compare(a,b)
