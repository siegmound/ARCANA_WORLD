"""R6 source-free one-model-year shell sign bracket refinement tests."""
import numpy as np
import pytest

from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import SparseP1Error
from experiments.plate58_deforming_explore_v1.g2_source_shell_event_1y_refinement import (
    summarize_integer_bracket, assert_prior_brackets,
    EXPECTED_BRACKETS,REPLAY_EPS_M,
)


def trajectory(values,base_year=10,rates=None):
    if rates is None:
        rates=[-1.0]*len(values)
    return {
        base_year+i:{
            "model_year":base_year+i,
            "signed_shell_midpoint_gap_m":float(g),
            "instantaneous_gdot_m_per_model_year":float(v),
        } for i,(g,v) in enumerate(zip(values,rates,strict=True))
    }


def test_one_year_definite_sign_switch_bracket():
    rows=trajectory([-2.,-1.,1.,3.],10,[-2.,1.5,1.9,2.])
    result=summarize_integer_bracket(rows,10,13,"NEGATIVE","POSITIVE")
    assert result["definite_1y_opposite_nonzero_sign_brackets"]==[{
        "from_year":11,"to_year":12,"from_sign":"NEGATIVE",
        "to_sign":"POSITIVE","exact_crossing_year_known":False,
    }]
    assert not result["continuous_zero_crossing_time_exactly_known"]
    assert len(result["temporal_rate_comparisons"])==2


def test_one_year_zero_sample_marks_uncertainty_not_exact_collision():
    rows=trajectory([-1.,-0.5,0.,.5,1.],10)
    result=summarize_integer_bracket(rows,10,14,"NEGATIVE","POSITIVE")
    assert result["definite_1y_opposite_nonzero_sign_brackets"]==[]
    assert result["sampled_near_zero_years"]==[12]
    assert not result["continuous_zero_crossing_time_exactly_known"]


def test_nonmonotone_interval_may_have_multiple_sign_switches():
    rows=trajectory([-1.,1.,-2.,3.],10)
    result=summarize_integer_bracket(rows,10,13,"NEGATIVE","POSITIVE")
    assert len(result["definite_1y_opposite_nonzero_sign_brackets"])==3


def test_one_year_time_rate_discrepancy_measured_not_auto_faked_pass():
    rows=trajectory([-1.,0.,1.,2.],10,rates=[100.]*4)
    result=summarize_integer_bracket(rows,10,13,"NEGATIVE","POSITIVE")
    assert result["max_absolute_instantaneous_vs_1y_centered_trajectory_rate_difference"]==pytest.approx(99.)
    assert result["temporal_rate_discrepancy_pass_asserted"] is False


def test_one_year_source_history_missing_fails_closed():
    rows=trajectory([-1.,1.,2.,3.],10)
    del rows[12]
    with pytest.raises(SparseP1Error,match="EVENT_ONE_YEAR_SAMPLES_INCOMPLETE"):
        summarize_integer_bracket(rows,10,13,"NEGATIVE","POSITIVE")


def test_original_endpoint_sign_drift_fails_closed():
    rows=trajectory([1.,1.,1.,1.],10)
    with pytest.raises(SparseP1Error,match="EVENT_COARSE_BRACKET_ENDPOINT_SIGN_CHANGED"):
        summarize_integer_bracket(rows,10,13,"NEGATIVE","POSITIVE")


def test_nonfinite_rate_fails_closed():
    rows=trajectory([-1.,-0.1,.1,1.],10)
    rows[12]["instantaneous_gdot_m_per_model_year"]=float("nan")
    with pytest.raises(SparseP1Error,match="EVENT_NONFINITE_GAP_OR_RATE"):
        summarize_integer_bracket(rows,10,13,"NEGATIVE","POSITIVE")


def valid_prior():
    entry=[
        {"source_boundary_id":bid,"from_year":a,"to_year":b,
         "from_sign":s,"to_sign":t}
        for bid,(a,b,s,t) in EXPECTED_BRACKETS.items()
    ]
    return {
        8:{
            "extent":8,"source_edges":12,"source_contact_links":13,
            "source_triple_parent_nodes":[],
            "sampled_sign_event_brackets":{
                "opposite_nonzero_sign_brackets":[]},
        },
        16:{
            "extent":16,"source_edges":36,"source_contact_links":39,
            "source_triple_parent_nodes":[34587],
            "sampled_sign_event_brackets":{
                "opposite_nonzero_sign_brackets":entry},
        },
    }


def test_source_bracket_ids_from_verified_receipt_match():
    assert assert_prior_brackets(valid_prior())==EXPECTED_BRACKETS


def test_source_bracket_forgery_rejected():
    data=valid_prior()
    data[16]["sampled_sign_event_brackets"]["opposite_nonzero_sign_brackets"][0]["from_year"]=174
    with pytest.raises(SparseP1Error,match="EVENT_ORIGINAL_25Y_BRACKET_ID_OR_DIRECTION_CHANGED"):
        assert_prior_brackets(data)


def test_original_triple_parent_source_required():
    data=valid_prior()
    data[16]["source_triple_parent_nodes"]=[]
    with pytest.raises(SparseP1Error,match="EVENT_ORIGINAL_SOURCE_SCOPE_INVALID"):
        assert_prior_brackets(data)


def test_prior_source_scope_preserves_two_regions_and_tolerance():
    assert REPLAY_EPS_M==1e-7
    data=valid_prior()
    del data[8]
    with pytest.raises(SparseP1Error,match="EVENT_ORIGINAL_REGION_SET_INVALID"):
        assert_prior_brackets(data)
