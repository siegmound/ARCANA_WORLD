"""S2 candidate software tests, not real-engine evidence."""
import copy
import pytest
from experiments.r6_thermo_provider_pilot_v1.s2_repro_protocol import (
    S2ProtocolError, load, validate, stability_screen
)

def test_policy_contract():
    assert load()["runs_per_case"] == 5

@pytest.mark.parametrize(("keys","bad"),[
    (("status",),"S2_FINAL_PASS"),
    (("runs_per_case",),4),
    (("threads",),4),
    (("new_process_each_run",),False),
    (("s1_source_sha",),"invalid"),
    (("rules","physical_T1"),1),
    (("rules","D_024"),"INACTIVE"),
    (("rules","WORLD_HISTORY_PRODUCTION_AUTHORIZED"),True),
    (("rules","no_same_database_or_chemistry_cross_provider_equivalence"),False),
    (("magemin_tolerances","native_oxide_component_closure_abs"),0.1),
    (("magemin_tolerances","phase_fraction_abs"),0.1),
    (("perplex_tolerances","phase_percent_abs_pp"),2.0),
    (("pins","magemin_c_version"),"1.0"),
    (("per_run_fields_magemin",),[]),
    (("per_run_fields_perplex",),[]),
])
def test_mutations_fail_closed(keys,bad):
    obj = copy.deepcopy(load())
    dest = obj
    for k in keys[:-1]:
        dest = dest[k]
    dest[keys[-1]]=bad
    with pytest.raises(S2ProtocolError):
        validate(obj)

def test_stability_screen_logic():
    assert stability_screen(1000.0,1000.0001,.001,1e-6)
    assert not stability_screen(1000.0,1000.1,.001,1e-6)

def test_nonfinite_fail_closed():
    with pytest.raises(S2ProtocolError):
        stability_screen(float("nan"),1.0,.001,1e-6)
