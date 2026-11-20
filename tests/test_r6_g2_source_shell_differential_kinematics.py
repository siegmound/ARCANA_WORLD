"""Synthetic differential original material shell gap, signs, and triple kinematics."""
import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from experiments.plate58_deforming_explore_v1.g2_source_shell_differential_kinematics import (
    directional_rate_audit, detect_sampled_sign_events, triple_material_view_audit,
    sign_class, SAMPLE_YEARS,
)
from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import SparseP1Error


def source_faces(yq=-10., zq=0.):
    r=6_371_000.
    p=np.array([[0.,0.,r],[2000.,0.,r],[1000.,1000.,r]])
    q=np.array([[2000.,yq,r+zq],[0.,yq,r+zq],[1000.,yq-1000.,r+zq]])
    return p,q,p[[0,1]],q[[1,0]]


def all_velocity(yq=-.1):
    vp=np.zeros((3,3))
    vq=np.zeros((3,3))
    vq[:,1]=yq
    return vp,vq,vp[[0,1]],vq[[1,0]]


@pytest.mark.parametrize("vq_y,expected",[
    (-.1,.1),(.25,-.25),(0.,0.)
])
def test_source_matched_shell_instantaneous_rate(vq_y,expected):
    args=source_faces()
    vel=all_velocity(vq_y)
    result=directional_rate_audit(*args,*vel)
    assert result["classification"]=="ENGINEERING_ONLY_MATCHED_SHELL_EDGE_GAP"
    assert result["gdot_m_per_model_year"]==pytest.approx(expected,abs=1e-6)
    assert abs(result["normal_rotation_contribution_m_per_model_year"])<1e-6
    assert result["SO3_rate_absolute_error_m_per_model_year"]<1e-5
    assert result["physical_contact_force_derived"] is False


def test_pure_global_translation_is_zero_gap_rate():
    p,q,ep,eq=source_faces()
    translation=np.array([1.,-.3,.2])
    vp=np.tile(translation,(3,1))
    vq=np.tile(translation,(3,1))
    x=directional_rate_audit(p,q,ep,eq,vp,vq,vp[[0,1]],vq[[1,0]])
    assert abs(x["gdot_m_per_model_year"])<1e-6
    assert abs(x["frozen_normal_contribution_m_per_model_year"])<1e-9


def test_sourced_conormal_rotation_contributes_to_kinematic_gap_rate():
    p,q,ep,eq=source_faces(zq=2.)
    vp=np.zeros((3,3));vq=np.zeros((3,3))
    vq[2,2]=.1
    result=directional_rate_audit(p,q,ep,eq,vp,vq,vp[[0,1]],vq[[1,0]])
    assert result["classification"]=="ENGINEERING_ONLY_MATCHED_SHELL_EDGE_GAP"
    assert abs(result["frozen_normal_contribution_m_per_model_year"])<1e-12
    assert abs(result["normal_rotation_contribution_m_per_model_year"])>1e-7
    assert result["rate_decomposition_residual_m_per_model_year"]<1e-4


@pytest.mark.parametrize("theta",[.1,.7,1.3])
def test_Rigid_SO3_rotating_source_rates_remain_objective(theta):
    p,q,ep,eq=source_faces()
    vel=all_velocity(-.17)
    Q=Rotation.from_rotvec(theta*np.array([.4,-.7,.2])).as_matrix()
    original=directional_rate_audit(p,q,ep,eq,*vel)
    rotated=directional_rate_audit(
        *(a@Q.T for a in (p,q,ep,eq)),
        *(v@Q.T for v in vel))
    assert abs(original["gdot_m_per_model_year"]-
               rotated["gdot_m_per_model_year"])<1e-5


def test_ineligible_shell_sidedness_rejects_rate_without_force():
    p,q,ep,eq=source_faces()
    q[2]=[1000.,1000.,6_371_000.]
    v=all_velocity()
    result=directional_rate_audit(p,q,ep,eq,*v)
    assert result["classification"]=="NOT_QUALIFIED"
    assert result["gdot_m_per_model_year"] is None


def test_sampled_sign_event_brackets_not_exact_times():
    def row(g):
        return {"signed_shell_midpoint_gap_m":g}
    snapshots={
        0:{"id1":row(0.)},
        25:{"id1":row(-1.)},
        50:{"id1":row(-2.)},
        75:{"id1":row(1.)},
        100:{"id1":row(3.)},
    }
    r=detect_sampled_sign_events(snapshots,["id1"])
    assert len(r["initial_T0_zero_departures"])==1
    assert r["initial_T0_zero_departures"][0]["initial_departure_direction"]=="NEGATIVE"
    assert len(r["opposite_nonzero_sign_brackets"])==1
    assert r["opposite_nonzero_sign_brackets"][0]["from_year"]==50
    assert r["opposite_nonzero_sign_brackets"][0]["to_year"]==75
    assert not r["exact_zero_crossing_time_claimed"]


def test_sampled_same_negative_count_may_hide_switch():
    def row(g):
        return {"signed_shell_midpoint_gap_m":g}
    sample={
        0:{"a":row(0.),"b":row(0.)},
        25:{"a":row(-1.),"b":row(+1.)},
        50:{"a":row(+1.),"b":row(-1.)},
    }
    events=detect_sampled_sign_events(sample,["a","b"])
    assert len(events["opposite_nonzero_sign_brackets"])==2


def test_true_original_material_triple_vector_closure_not_scalar_signorini():
    index={(5,34587):0,(8,34587):1,(11,34587):2}
    x=np.array([[6_371_000.,0.,0.],[6_371_000.,5.,0.],
                [6_371_000.,2.,10.]])
    v=np.array([[0.,1.,0.],[0.,-.2,.1],[.1,.3,0.]])
    r=triple_material_view_audit(34587,[5,8,11],index,x,v)
    assert r["material_displacement_vector_closure_error_m"]<1e-7
    assert r["material_velocity_vector_closure_error_m_per_model_year"]<1e-8
    assert r["three_body_contact_or_force_balance_solved"] is False


def test_missing_triple_source_plate_copy_fails_closed():
    with pytest.raises(SparseP1Error,match="SHELL_TRIPLE_PARENT_VIEW_PROVENANCE_INVALID"):
        triple_material_view_audit(
            34587,[5,8,11],{(5,34587):0,(8,34587):1},
            np.zeros((2,3)),np.zeros((2,3)))


def test_sample_schedule_preserves_original_checkpoint_years():
    assert len(SAMPLE_YEARS)==41
    assert SAMPLE_YEARS[:3]==(0,25,50)
    assert SAMPLE_YEARS[-1]==1000
    assert {0,100,500,1000}.issubset(SAMPLE_YEARS)


@pytest.mark.parametrize("value,sign",[
    (-.01,"NEGATIVE"),(.01,"POSITIVE"),
    (-1e-9,"NEAR_ZERO"),(0.,"NEAR_ZERO"),(None,"NOT_QUALIFIED")
])
def test_explicit_engineering_gap_sign_deadband(value,sign):
    assert sign_class(value)==sign
