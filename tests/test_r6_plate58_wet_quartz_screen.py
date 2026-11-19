"""Scope-limited T–P eligibility screening with no constitutive authorization."""
import math
import pytest

from experiments.plate58_deforming_explore_v1.wet_quartz_screen import screen_pt


@pytest.mark.parametrize("temp,p,window,group,overlap",[
    (1000.,500e6,True,"LOW_LT_560MPA",True),
    (1000.,560e6,True,"BETWEEN_REPORTED_PRESSURE_GROUPS",False),
    (1000.,699e6,True,"BETWEEN_REPORTED_PRESSURE_GROUPS",False),
    (1000.,700e6,True,"HIGH_700_TO_1600MPA",True),
    (1000.,1600e6,True,"HIGH_700_TO_1600MPA",True),
    (1000.,1600e6+1,True,"ABOVE_REPORTED_PRESSURE_GROUPS",False),
    (900.,700e6,False,"HIGH_700_TO_1600MPA",False),
    (973.15,100e6,True,"LOW_LT_560MPA",True),
    (1473.15,100e6,True,"LOW_LT_560MPA",True),
])
def test_pt_screen_has_explicit_cross_study_limit(temp,p,window,group,overlap):
    d=screen_pt(temp,p)
    assert d["temperature_in_Tokle2019_wet_experiment_window"]==window
    assert d["pressure_group_in_2021_calibration"]==group
    assert d["cross_study_PT_window_overlap_for_screen_only"]==overlap
    assert not d["constitutive_law_validated"]
    assert not d["field_water_fugacity_known"]


@pytest.mark.parametrize("t,p",[
    (math.nan,0.), (300.,math.nan), (300.,-1.), (0.,10.)
])
def test_nonphysical_input_refused(t,p):
    with pytest.raises(ValueError,match="NONFINITE_OR_NONPHYSICAL"):
        screen_pt(t,p)


def test_water_not_inferred_from_overlap():
    d=screen_pt(1000.,1e9)
    assert d["cross_study_PT_window_overlap_for_screen_only"]
    assert d["field_water_fugacity_known"] is False
