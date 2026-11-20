"""Source-free R6 original fixed-T0 shell dt convergence diagnostic contracts."""
import pytest

from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import SparseP1Error
from experiments.plate58_deforming_explore_v1.g2_source_shell_dt_convergence import (
    STEP_SIZES,SOURCE_BOUNDARY_REPLAY_MAX_ABS_M,
    analyze_subyear_samples,assess_timestep_differences,
    compare_original_source_samples,original_1y_events,
)
from experiments.plate58_deforming_explore_v1.g2_source_shell_event_1y_refinement import (
    EXPECTED_BRACKETS,
)
from experiments.plate58_deforming_explore_v1.g2_source_shell_differential_kinematics import (
    SAMPLE_YEARS,
)


def samples(year,gaps,dt):
    return [
        {"model_year":float(year+i*dt),
         "signed_shell_midpoint_gap_m":float(g)}
        for i,g in enumerate(gaps)
    ]


def test_refine_half_year_definite_bracket():
    s=samples(197,[-1.,-.1,+1.],.5)
    x=analyze_subyear_samples("r",(197,198,"NEGATIVE","POSITIVE"),s,.5)
    assert x["observed_status"]=="SAMPLED_DEFINITE_BRACKETS"
    assert x["definite_sampled_sign_brackets"]==[{
        "from_model_year":197.5,"to_model_year":198.,
        "from_sign":"NEGATIVE","to_sign":"POSITIVE",
        "exact_zero_year_known":False
    }]
    assert x["no_exact_continuous_time_root_claim"] is True


def test_refine_quarter_year_preserves_two_event_brackets():
    s=samples(477,[1.,-1.,1.,-1.,-2.],.25)
    x=analyze_subyear_samples("r",(477,478,"POSITIVE","NEGATIVE"),s,.25)
    assert len(x["definite_sampled_sign_brackets"])==3
    assert x["prior_endpoint_signs_reproduced"]
    assert x["no_guarantee_absence_of_substep_crossings"]


def test_near_zero_is_not_invented_exact_root():
    s=samples(197,[-1.,0.,.1],.5)
    x=analyze_subyear_samples("r",(197,198,"NEGATIVE","POSITIVE"),s,.5)
    assert x["observed_status"]=="SAMPLED_NEAR_ZERO_NO_DEFINITE_PAIR"
    assert x["near_zero_samples"]==[197.5]
    assert x["no_exact_continuous_time_root_claim"] is True


def test_dt_drift_can_leave_verified_one_year_bracket():
    s=samples(197,[+.1,+.2,+.3],.5)
    x=analyze_subyear_samples("r",(197,198,"NEGATIVE","POSITIVE"),s,.5)
    assert x["observed_status"]=="OUTSIDE_PRIOR_1Y_BRACKET_OR_SIGN_DRIFT"
    assert not x["prior_endpoint_signs_reproduced"]


def test_source_clock_mismatch_fails_closed():
    s=samples(197,[-1.,0.,1.],.5)
    s[1]["model_year"]=197.7
    with pytest.raises(SparseP1Error,match="DTC_SOURCE_SUBYEAR_CLOCK_OR_GAP_INVALID"):
        analyze_subyear_samples("r",(197,198,"NEGATIVE","POSITIVE"),s,.5)


def test_source_subyear_sample_missing_fails_closed():
    s=samples(197,[-1.,1.],.5)
    with pytest.raises(SparseP1Error,match="DTC_SOURCE_SUBYEAR_SAMPLE_COUNT_CHANGED"):
        analyze_subyear_samples("r",(197,198,"NEGATIVE","POSITIVE"),s,.5)


def reference_one_year():
    rows=[]
    source_dates={
        "R6BND-T0-f679f4c97f1e7445d8d9":(197,198),
        "R6BND-T0-4d168aac7492e7c418de":(477,478),
        "R6BND-T0-1569360d5844c75db0d3":(642,643),
        "R6BND-T0-16d7dc72630ecb414c04":(892,893),
    }
    for bid,(lo,hi) in source_dates.items():
        coarse=EXPECTED_BRACKETS[bid]
        rows.append({
            "source_boundary_id":bid,
            "definite_1y_opposite_nonzero_sign_brackets":[{
                "from_year":lo,"to_year":hi,
                "from_sign":coarse[2],"to_sign":coarse[3],
            }],
            "sampled_near_zero_years":[],
        })
    return {"result_16":{
        "original_source_boundary_count":36,
        "original_source_contact_link_count":39,
        "original_source_triple_parent_node_id":34587,
        "one_model_year_source_bracket_refinements":rows,
    }}


def test_all_four_exact_source_bracket_ids_preserved():
    r=original_1y_events(reference_one_year())
    assert len(r)==4
    assert r["R6BND-T0-4d168aac7492e7c418de"]==(
        477,478,"POSITIVE","NEGATIVE")


def test_forged_original_one_year_id_or_sign_rejected():
    r=reference_one_year()
    r["result_16"]["one_model_year_source_bracket_refinements"][0][
        "definite_1y_opposite_nonzero_sign_brackets"][0]["from_year"]=150
    with pytest.raises(SparseP1Error,match="DTC_PRIOR_ONE_YEAR_EVENT_DIRECTION_CHANGED"):
        original_1y_events(r)


def make_matrix(scale):
    return {t:{f"source-{i}":float(i+.01*t)*scale
               for i in range(36)} for t in SAMPLE_YEARS}


def test_same_source_checkpoint_dt_difference_contraction():
    a=make_matrix(1.)
    b=make_matrix(1.0001)
    c=make_matrix(1.00015)
    r=assess_timestep_differences(a,b,c)
    assert r["identical_original_source_pairs_common_checkpoint_count"]==41*36
    assert r["observed_difference_contraction"] is True
    assert r["successive_difference_ratio"]==pytest.approx(.5)
    assert r["physical_time_step_convergence_certified"] is False


def test_same_source_checkpoint_dt_divergence_remains_observable():
    a=make_matrix(1.)
    b=make_matrix(1.0001)
    c=make_matrix(1.0003)
    r=assess_timestep_differences(a,b,c)
    assert r["observed_difference_contraction"] is False
    assert r["numerical_order_of_accuracy_claimed"] is False


def test_silent_missing_original_material_id_is_disallowed():
    a,b,c=make_matrix(1.),make_matrix(1.0001),make_matrix(1.00015)
    del c[100]["source-1"]
    with pytest.raises(SparseP1Error,match="DTC_SOURCE_COMMON_IDS_CHANGED"):
        assess_timestep_differences(a,b,c)


def test_prior_source_gap_and_count_rigidity():
    old=[{
        "source_boundary_id":f"source-{i}",
        "classification":"ENGINEERING_ONLY_MATCHED_SHELL_EDGE_GAP",
        "signed_shell_midpoint_gap_m":float(i)
    } for i in range(36)]
    current={f"source-{i}":float(i)+.01 for i in range(36)}
    r=compare_original_source_samples(old,current,.5,100)
    assert r["source_matched_edge_count"]==36
    assert r["max_abs_change_from_verified_dt1_m"]==pytest.approx(.01)
    assert r["numerical_dt_convergence_proven"] is False


def test_nonqualified_prior_source_gap_rejected():
    old=[{
        "source_boundary_id":f"source-{i}",
        "classification":"ENGINEERING_ONLY_MATCHED_SHELL_EDGE_GAP",
        "signed_shell_midpoint_gap_m":float(i)
    } for i in range(36)]
    old[0]["classification"]="NOT_QUALIFIED"
    current={f"source-{i}":float(i) for i in range(36)}
    with pytest.raises(SparseP1Error,match="DTC_PRIOR_ORIGINAL_SHELL_GAP_NOT_QUALIFIED"):
        compare_original_source_samples(old,current,.5,100)


def test_timestep_ordinal_contract_is_frozen():
    assert STEP_SIZES==(.5,.25)
    assert SOURCE_BOUNDARY_REPLAY_MAX_ABS_M==1e-7
    assert len(SAMPLE_YEARS)==41


@pytest.mark.parametrize("dt",[.5,.25])
def test_fractional_local_restart_uses_returned_state_without_int_checkpoint(dt,monkeypatch):
    """Regression: original integrate rounds checkpoint years to int.

    A fractional restart cannot require an integer-keyed snapshot.
    """
    import numpy as np
    import experiments.plate58_deforming_explore_v1.g2_source_shell_dt_convergence as mod
    calls=[]
    def fake_integrate(K,J,drive,step,steps,*,initial=None,checkpoints=None):
        calls.append((step,steps,checkpoints))
        assert step==dt and steps==1 and checkpoints==()
        assert initial is not None
        next_u=np.asarray(initial["displacement"])+dt*np.array([2.,-3.,4.])
        return {
            "state":{
                "displacement":next_u,
                "gap":np.asarray(initial["gap"]).copy(),
            },
            "snapshots":{},
            "steps":1,
            "max_scaled_complementarity":0.,
        }
    monkeypatch.setattr(mod,"integrate",fake_integrate)
    initial={"displacement":np.array([1.,2.,3.]),
             "gap":np.array([.5,-0.0])}
    snap,state=mod.advance_source_restart_state(
        np.eye(3),np.zeros((2,3)),np.zeros(3),dt,initial)
    assert len(calls)==1
    assert np.allclose(snap["velocity"],[2.,-3.,4.])
    assert np.allclose(snap["displacement"],
                       initial["displacement"]+dt*np.array([2.,-3.,4.]))
    assert np.allclose(snap["gap"],initial["gap"])
    assert state is not initial


def test_fractional_local_restart_does_not_hide_complementarity_failure(monkeypatch):
    import numpy as np
    import experiments.plate58_deforming_explore_v1.g2_source_shell_dt_convergence as mod
    def fake_integrate(K,J,drive,dt,steps,*,initial=None,checkpoints=None):
        return {
            "state":initial,
            "snapshots":{},
            "steps":1,
            "max_scaled_complementarity":2e-8,
        }
    monkeypatch.setattr(mod,"integrate",fake_integrate)
    initial={"displacement":np.zeros(3),"gap":np.zeros(2)}
    with pytest.raises(SparseP1Error,match="DTC_SOURCE_LOCAL_RESTART_FAILED"):
        mod.advance_source_restart_state(
            np.eye(3),np.zeros((2,3)),np.zeros(3),.5,initial)
