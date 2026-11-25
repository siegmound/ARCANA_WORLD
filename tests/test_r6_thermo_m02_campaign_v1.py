from pathlib import Path
from copy import deepcopy
import math
import pytest

from experiments.r6_thermo_provider_pilot_v1 import run_m02_fair as r
from experiments.r6_thermo_provider_pilot_v1 import run_m01_fair as m

ROOT=Path(__file__).resolve().parents[1]


def test_fixed_x_design_and_setpoints():
    a=m.build_inputs(ROOT)["M01_BASE"]
    points=r.design(a)
    assert len(points)==6
    for p in points.values():
        assert p["wt_amounts"]==a["wt_amounts"]
        assert p["expected_native_mol"]==a["expected_native_mol"]
    assert points["M02_T_PLUS"]["T_C"]==m.T+10
    assert points["M02_P_MINUS"]["P_kbar"]==m.P-.25
    assert points["M02_REGIONAL_41KM"]["P_kbar"]==pytest.approx(11.91166)


def fake(p,t):
    # synthetic constant Cp, alpha, beta; exact algebraic identities.
    ms=50.;tk=t+273.15;anchor=m.T+273.15
    h=50*(tk-anchor)/1000
    entropy=.1
    rho=3300*math.exp(-3e-5*(t-m.T)+.01*(p-m.P)/10)
    g=h-tk*entropy
    return {"rho_kg_m3":rho,"G_system":g,"phases":{"synthetic":1.},
        "native_diagnostics":{"M_sys_g_mol_oxide":ms,"volume_cm3_mol_oxide":1000*ms/rho,
        "enthalpy_kJ_mol_oxide":[h],"entropy_kJ_mol_oxide_K":[entropy],
        "Cp_fixed_phase_J_kg_K":[1000.],"alpha_fixed_phase_per_K":[3e-5],"beta_per_GPa":.01}}


def test_response_units_and_secants():
    points={k:fake(v["P_kbar"],v["T_C"]) for k,v in r.design(m.build_inputs(ROOT)["M01_BASE"]).items()}
    out=r.response(fake(m.P,m.T),points)
    assert out["central_equilibrium_path_Cp_secant_J_kg_K"]==pytest.approx(1000.)
    assert out["central_alpha_secant_per_K"]==pytest.approx(3e-5)
    assert out["central_beta_secant_per_GPa"]==pytest.approx(.01)
    assert out["left_right_Cp_secants_J_kg_K"]==pytest.approx([1000.,1000.])
    assert not any(out["phase_set_change_vs_anchor"].values())


@pytest.mark.parametrize("key,val",[
    ("enthalpy_kJ_mol_oxide",[1.]),("volume_cm3_mol_oxide",1.),
    ("M_sys_g_mol_oxide",0.),("entropy_kJ_mol_oxide_K",["NaN"])])
def test_bad_identities_or_nonfinite(key,val):
    a=fake(m.P,m.T)
    a["native_diagnostics"][key]=val
    with pytest.raises(ValueError):
        r.thermo(a,m.T+273.15)


def test_pt_validation_uses_case_not_old_anchor():
    inp=r.design(m.build_inputs(ROOT)["M01_BASE"])["M02_T_PLUS"]
    ox=list(inp["expected_native_wt"]);wt=[inp["expected_native_wt"][k] for k in ox]
    c={"case":inp["case"],"status":0,"database":"ig","dataset":"tc_ds636",
       "P_kbar":inp["P_kbar"],"T_C":inp["T_C"],"oxides":ox,"bulk_wt":wt,
       "bulk_mol":[inp["expected_native_mol"][k] for k in ox],"phases":["test"],
       "phase_mass_fractions":[1.],"phase_comp_wt":[wt],"bulk_res_norm":0.,
       "G_system":-800.,"rho_kg_m3":3300.,"solid_wt":1.,"melt_wt":0.,"fluid_wt":0.,"native_diagnostics":{}}
    assert m.validate(c,inp)["case"]==inp["case"]
    c["T_C"]=m.T
    with pytest.raises(ValueError,match="M01_NATIVE_PT"):
        m.validate(c,inp)


def test_phase_transition_reported_not_rejected():
    pts={k:fake(v["P_kbar"],v["T_C"]) for k,v in r.design(m.build_inputs(ROOT)["M01_BASE"]).items()}
    pts["M02_T_PLUS"]["phases"]={"different":1.}
    assert r.response(fake(m.P,m.T),pts)["phase_set_change_vs_anchor"]["M02_T_PLUS"]
