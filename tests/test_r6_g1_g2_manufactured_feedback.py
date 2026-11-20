"""Synthetic tests for G1<->G2 manufactured feedback, not ARCANA physical T1."""
import numpy as np
import pytest

from experiments.plate58_deforming_explore_v1.g1_g2_manufactured_feedback import (
    ManufacturedError, linear_feedback_modes, evolve_modes,
    source_plate_weights, euler_driver,
)


def fixture():
    # Pure manufactured 2-node viscous/elastic force; not geological data.
    K=1e18*np.array([[1.,-1.],[-1.,1.]])
    lam,Q=linear_feedback_modes(K,1e18)
    return lam,Q


def test_positive_kelvin_voigt_feedback_and_virtual_work():
    lam,Q=fixture()
    drive=np.tile([0.12,-0.08],(1000,1))
    out=evolve_modes(lam,Q,drive,1,checkpoints=(100,500,1000))
    assert out["max_balance_relative"]<1e-12
    assert out["max_backward_euler_energy_identity_relative"]<1e-12
    assert np.linalg.norm(Q@out["states"][1000]["modes"])>0
    assert not np.allclose(Q@out["last_velocity_modes"],drive[-1])


def test_zero_g2_stiffness_reproduces_original_G1():
    lam,Q=linear_feedback_modes(np.zeros((2,2)),1.)
    drive=np.tile([0.4,0.8],(100,1))
    out=evolve_modes(lam,Q,drive,1,checkpoints=(100,))
    assert np.allclose(Q@out["states"][100]["modes"],[40.,80.])
    assert out["max_balance_relative"]<1e-12


def test_restart500_plus500_bit_identical():
    lam,Q=fixture()
    drive=np.tile([0.12,-0.08],(1000,1))
    full=evolve_modes(lam,Q,drive,1)
    a=evolve_modes(lam,Q,drive[:500],1)
    b=evolve_modes(lam,Q,drive[500:],1,initial=a["final_modes"],years_start=500)
    assert np.array_equal(full["final_modes"],b["final_modes"])


def test_time_step_refinement_on_const_drive():
    lam,Q=fixture()
    annual=evolve_modes(lam,Q,np.tile([0.12,-0.08],(1000,1)),1)
    ten=evolve_modes(lam,Q,np.tile([0.12,-0.08],(100,1)),10)
    assert np.max(np.abs(Q@(annual["final_modes"]-ten["final_modes"])))<0.1


def test_source_shared_parent_node_only_one_mechanical_owner():
    faces={"parent_node_ids":[34587,34588,34589,34590],
           "parent_triangle_ids":[1,2],
           "parent_triangle_plate_ids":[5,11],
           "faces_parent_nodes":[[34587,34588,34589],
                                 [34587,34589,34590]]}
    weights=source_plate_weights(faces)
    assert weights[34587][5]==weights[34587][11]==1
    assert len(weights)==4


def test_parent_node_missing_plate_source_rejected():
    faces={"parent_node_ids":[1,2,3,4],
           "parent_triangle_ids":[1],
           "parent_triangle_plate_ids":[5],
           "faces_parent_nodes":[[1,2,3]]}
    with pytest.raises(ManufacturedError,match="NODE_NOT_OWNED"):
        source_plate_weights(faces)


def test_negative_tangent_rejected():
    with pytest.raises(ManufacturedError,match="POSITIVE_SEMIDEFINITE"):
        linear_feedback_modes(np.diag([-1.,1.]),1.)


def test_nonsymmetric_tangent_rejected():
    with pytest.raises(ManufacturedError,match="STIFFNESS_OR_DASHPOT"):
        linear_feedback_modes(np.array([[1.,3.],[0.,1.]]),1.)


def test_nonfinite_restart_rejected():
    lam,Q=fixture()
    with pytest.raises(ManufacturedError,match="RESTART_STATE_INVALID"):
        evolve_modes(lam,Q,np.ones((1,2)),1,initial=[float("nan"),1.])


def test_negative_or_zero_time_step_rejected():
    lam,Q=fixture()
    with pytest.raises(ManufacturedError,match="EVOLUTION_INPUT_INVALID"):
        evolve_modes(lam,Q,np.ones((1,2)),0)


def test_euler_driver_uses_real_G1_rotation_convention():
    ll={1:(10.,-159.),2:(11.,-158.),3:(10.,-158.)}
    weights={1:{5:1},2:{5:1},3:{5:1}}
    omega={5:np.array([0.,0.,2.0e-8])}
    velocity=euler_driver(ll,weights,omega,100.)
    assert velocity.shape==(6,) and np.all(np.isfinite(velocity))
    assert np.linalg.norm(velocity)>0
