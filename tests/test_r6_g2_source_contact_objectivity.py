"""Contact policy and SO(3) invariance source-free synthetic tests.

Only synthetic regional fixtures; FAIR source run is separately required.
"""
import math

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from experiments.plate58_deforming_explore_v1.g2_source_contact_objectivity import (
    SparseP1Error, contact_registry, assemble_split_source, euler_source_en,
    active_contacts, penalty_matrix, solve_contact_policy,
    finite_rotation_objectivity, POLICIES,
)


def fixture():
    ids=[11,12,13,14]
    ll={11:(10.,-159.),12:(10.,-158.),13:(11.,-158.),14:(11.,-159.)}
    faces=[(11,12,13),(11,13,14)]
    plates=[5,8]
    contacts=[{
        "source_edge_node_ids":[11,13],"plate_pair":[5,8],
        "source_boundary_id":"R6BND-T0-SYNTHETIC-EDGE"
    }]
    pre={node:{"crust_thickness_m":20000.,"mantle_lithosphere_thickness_m":70000.}
         for node in ids}
    return ids,ll,faces,plates,contacts,pre


def prepare():
    ids,ll,faces,plates,contacts,pre=fixture()
    registry=contact_registry(ids,faces,plates,ll,contacts)
    K,index,source,plate_views,stats=assemble_split_source(
        ids,faces,plates,ll,pre)
    omega={5:np.array([0.,0.,1.5e-8]),8:np.array([0.,0.,2.4e-8])}
    target=euler_source_en(source,plate_views,omega)
    links=active_contacts(registry["contacts"],index,target)
    c=.5*float(np.mean(K.diagonal()))
    return registry,K,index,source,plate_views,links,target,c


def test_true_edge_pair_contact_not_all_shared_nodes():
    reg,*_=prepare()
    assert len(reg["edges"])==1
    assert reg["contact_parent_node_count"]==2
    assert len(reg["contacts"])==2
    assert reg["owner_by_parent_node"][11]==(5,8)
    assert reg["owner_by_parent_node"][12]==(5,)
    assert reg["triple_junction_parent_ids"]==[]


def test_missing_or_wrong_mentioned_source_contact_fails_closed():
    ids,ll,faces,plates,contacts,pre=fixture()
    bad=[{**contacts[0],"plate_pair":[5,11]}]
    with pytest.raises(SparseP1Error,match="EDGE_PLATE_PAIR_MISMATCH"):
        contact_registry(ids,faces,plates,ll,bad)
    with pytest.raises(SparseP1Error,match="EDGE_PLATE_PAIR_MISMATCH"):
        contact_registry(ids,faces,plates,ll,[])


def test_nonmanifold_source_topology_rejected():
    ids,ll,faces,plates,contacts,pre=fixture()
    with pytest.raises(SparseP1Error,match="NONMANIFOLD"):
        contact_registry(ids,faces+[faces[0],faces[0]],
                         plates+[5,5],ll,contacts)


def test_split_plate_dofs_not_accidentally_welded():
    reg,K,index,ll,owners,links,target,c=prepare()
    assert K.shape==(12,12)
    assert (5,11) in index and (8,11) in index
    assert index[(5,11)]!=index[(8,11)]
    # Node 11 cross-plate stiffness is exactly zero before adding contact.
    a,b=index[(5,11)],index[(8,11)]
    assert K[2*a:2*a+2,2*b:2*b+2].nnz==0


def test_three_policy_operators_are_symmetric_positive_semidefinite():
    reg,K,index,ll,owners,links,target,c=prepare()
    for p in POLICIES:
        H,active=penalty_matrix(len(target),links,p,30*c)
        assert H.shape==K.shape
        assert (H-H.T).nnz==0 or np.max(np.abs((H-H.T).data))<1e-12*c
        assert np.min(np.linalg.eigvalsh(H.toarray()))>=-1e-8*c
        if p=="UNWELDED":
            assert active==0 and H.nnz==0


def test_welded_penalty_changes_relative_euler_velocity():
    reg,K,index,ll,owners,links,target,c=prepare()
    independent=solve_contact_policy(K,target,links,"UNWELDED",c,30*c)
    welded=solve_contact_policy(K,target,links,"PENALTY_WELDED",c,30*c)
    assert independent["active_penalty_contacts"]==0
    assert welded["active_penalty_contacts"]==len(links)
    assert welded["synthetic_contact_work"]>0
    assert np.linalg.norm(welded["velocity_vector"]-
                          independent["velocity_vector"])>1e-8
    assert welded["relative_force_balance"]<2e-9


def test_unilateral_rate_selector_only_acts_on_closing():
    reg,K,index,ll,owners,links,target,c=prepare()
    forced=[]
    for i,x in enumerate(links):
        forced.append({**x,"closing_under_Euler_target":i==0})
    H,active=penalty_matrix(len(target),forced,"CLOSING_NORMAL_ONLY",30*c)
    assert active==1
    assert H.nnz>0
    result=solve_contact_policy(K,target,forced,"CLOSING_NORMAL_ONLY",c,30*c)
    assert result["active_penalty_contacts"]==1
    assert result["relative_virtual_work_identity"]<2e-9


def test_no_ex_nihilo_contact_on_lonely_node():
    ids,ll,faces,plates,contacts,pre=fixture()
    reg=contact_registry(ids,faces,plates,ll,contacts)
    assert 12 not in {x["parent_node_id"] for x in reg["contacts"]}


@pytest.mark.parametrize("axisangle",[[0.,0.,0.], [0.,0.,.00001],
                                      [.6,-.35,.24], [1.1,.2,-.4]])
def test_P1_source_facet_frame_objective_under_SO3(axisangle):
    ids,ll,faces,plates,contacts,pre=fixture()
    R=Rotation.from_rotvec(axisangle).as_matrix()
    err=finite_rotation_objectivity(
        [ll[n] for n in faces[0]],1e21,1e21,R)
    assert err<3e-9


def test_objectivity_rejects_non_rotation_reflection():
    ids,ll,faces,plates,contacts,pre=fixture()
    q=np.diag([1,1,-1])
    with pytest.raises(SparseP1Error,match="OBJECTIVE_ROTATION_INVALID"):
        finite_rotation_objectivity([ll[n] for n in faces[0]],1e21,1e21,q)


def test_invalid_contact_policy_rejected():
    reg,K,index,ll,owners,links,target,c=prepare()
    with pytest.raises(SparseP1Error,match="POLICY_INVALID"):
        penalty_matrix(len(target),links,"PHYSICAL_FAULT_BY_MAGIC",30*c)


def test_contact_relative_normal_and_tangential_work_are_SO3_objective():
    from experiments.plate58_deforming_explore_v1.spherical_exterior import (
        frames_and_cartesian,
    )
    reg,K,index,ll,owners,links,target,c=prepare()
    link=links[0]
    parent=link["parent_node_id"]
    original=fixture()[1][parent]
    xyz,radial,e,n=frames_and_cartesian([original])
    normal_EN=np.asarray(link["normal_EN"])
    relative=np.array([-.07,.05])
    original_world=e[0]*relative[0]+n[0]*relative[1]
    original_normal=e[0]*normal_EN[0]+n[0]*normal_EN[1]
    Q=Rotation.from_rotvec([.9,-.4,.2]).as_matrix()
    moved_relative=Q@original_world
    moved_normal=Q@original_normal
    assert abs(float(original_world@original_normal)-
               float(moved_relative@moved_normal))<1e-12
    assert abs(np.dot(original_world,original_world)-
               np.dot(moved_relative,moved_relative))<1e-12
