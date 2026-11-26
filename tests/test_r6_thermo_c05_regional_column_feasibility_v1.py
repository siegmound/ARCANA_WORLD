import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c05_regional_column_feasibility as r


def fixture(pattern):
    rows=[]
    states={}
    for i,names in enumerate(pattern):
        keys=[]
        for name in names:
            k=f"{name}:{i}"
            keys.append(k)
            states[k]={"model_identity":"provider","native_chemistry_sha256":name,
                       "source_chemistry_sha256":name,"family":"MORB","P_kbar":float(i+1),"T_C":float(i)}
        rows.append({"fraction_of_layer":i/4,"source_temperature_K":273.15+i,
                     "conditional_delta_P_kbar":float(i+1),
                     "cold_MORB_conditional_candidate_keys":keys,"comparative_coordinate_matches":{}})
    return rows,states


def test_same_recipe_full_profile():
    rows,states=fixture([["a"]]*5)
    result=r.column_profile(rows,states)
    assert result["same_model_native_chemistry_full_profiles"]==1
    assert result["actual_material"] is None
    assert result["continuous_EOS_qualified"] is False


def test_combined_coverage_not_single_material_profile():
    rows,states=fixture([["a"],["a"],["b"],["b"],["b"]])
    result=r.column_profile(rows,states)
    assert result["any_coordinate_hits"]==5
    assert result["same_model_native_chemistry_full_profiles"]==0
    assert result["max_same_model_native_chemistry_depth_hits"]==3


def test_missing_depths_are_explicit():
    rows,states=fixture([["a"],[],["a"],[],[]])
    result=r.column_profile(rows,states)
    assert result["candidate_profiles"][0]["missing_depth_indices"]==[1,3,4]


def test_unknown_key_fails_closed():
    rows,states=fixture([["a"],[],[],[],[]])
    with pytest.raises(ValueError,match="UNKNOWN_STATE_KEY"):
        r.column_profile(rows,{})


def test_mismatched_coordinate_fails_closed():
    rows,states=fixture([["a"],[],[],[],[]])
    states["a:0"]["P_kbar"]=99.
    with pytest.raises(ValueError,match="STATE_COORDINATE"):
        r.column_profile(rows,states)


def test_provider_switch_not_one_profile():
    rows,states=fixture([["a"]]*5)
    states["a:4"]["model_identity"]="different_provider"
    assert r.column_profile(rows,states)["same_model_native_chemistry_full_profiles"]==0
