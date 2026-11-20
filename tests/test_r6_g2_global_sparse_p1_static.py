"""Numerical P1 sparse/dense parity without accessing T0 source on unit tests."""
from __future__ import annotations

import numpy as np
import pytest

from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import (
    SparseP1Error, sparse_p1_tangent, static_global_spd_probe,
    local_law_from_pre,
)
from experiments.plate58_deforming_explore_v1.spherical_exterior import (
    assemble_spherical_exterior, frames_and_cartesian,
)


def fixture():
    ids=[1,2,3,4]
    ll=np.array([[10.,-160.],[10.,-159.],[11.,-159.],[11.,-160.]])
    faces=np.array([[0,1,2],[0,2,3]],dtype=np.int32)
    eta=np.array([1.e21,2.e21])
    bulk=np.array([.4e21,.7e21])
    materials={i+1:{
        "authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
        "source_reference":"MANUFACTURED_SPHERICAL_P1_SYNTHETIC",
        "eta_h_pa_s_m":float(eta[i]),
        "lambda_h_pa_s_m":float(bulk[i])}
        for i in range(2)}
    return ids,ll,faces,eta,bulk,materials


def compare():
    ids,ll,faces,eta,bulk,materials=fixture()
    triangle={i+1:tuple(ids[int(x)] for x in faces[i]) for i in range(2)}
    dense=assemble_spherical_exterior(
        ids,triangle,dict(zip(ids,ll)),materials)["tangent"]
    K,stat=sparse_p1_tangent(ll,faces,eta,bulk)
    return dense,K,stat


def test_exact_local_facet_assembly_parity():
    dense,K,stat=compare()
    assert K.shape==(8,8) and stat["source_triangles"]==2
    assert np.allclose(K.toarray(),dense,rtol=1e-13,atol=0)
    assert stat["one_csr_bytes"]>0


def test_matrix_action_and_virtual_work_reciprocity():
    dense,K,_=compare()
    rng=np.random.default_rng(42)
    a,b=rng.normal(size=(2,8))
    assert np.linalg.norm(K@a-dense@a)/np.linalg.norm(dense@a)<1e-12
    assert abs(a@(K@b)-b@(K@a))<1e-12*max(abs(a@(K@b)),abs(b@(K@a)))
    assert a@(K@a)>=0


def test_rigid_plate_rotation_has_null_action():
    ids,ll,faces,eta,bulk,_=fixture()
    K,_=sparse_p1_tangent(ll,faces,eta,bulk)
    xyz,unit,e,n=frames_and_cartesian(ll)
    for ax in np.eye(3)*1e-15:
        xyzv=np.cross(ax,xyz)
        v=np.stack((np.einsum("ij,ij->i",xyzv,e),
                    np.einsum("ij,ij->i",xyzv,n)),axis=1).reshape(-1)
        assert np.linalg.norm(K@v)/(np.max(K.diagonal())*np.linalg.norm(v))<1e-10


def test_distinct_plate_local_views_not_automatically_welded():
    ids,ll,faces,eta,bulk,_=fixture()
    coords=np.concatenate([ll[:3],ll[:3]])
    duplicate_faces=np.array([[0,1,2],[3,4,5]],dtype=np.int32)
    K,stats=sparse_p1_tangent(coords,duplicate_faces,[1e21,1e21],[1e21,1e21])
    assert K.shape==(12,12)
    assert K[:6,6:].nnz==0 and K[6:,:6].nnz==0
    assert stats["source_nodes"]==6


def test_nonfinite_viscosity_rejected():
    ids,ll,faces,eta,bulk,_=fixture()
    with pytest.raises(SparseP1Error,match="INVALID_MATERIAL"):
        sparse_p1_tangent(ll,faces,[float("nan"),1.],bulk)


def test_malformed_topology_rejected():
    ids,ll,faces,eta,bulk,_=fixture()
    bad=faces.copy();bad[0]=[0,0,2]
    with pytest.raises(SparseP1Error,match="INVALID_MATERIAL"):
        sparse_p1_tangent(ll,bad,eta,bulk)


def test_pre_true_thickness_geometry_is_required():
    parent=[100,101,102,103]
    ids,ll,faces,eta,bulk,_=fixture()
    pre={p:{"crust_thickness_m":1e4+i*100,
            "mantle_lithosphere_thickness_m":8e4+i*500}
         for i,p in enumerate(parent)}
    e,l=local_law_from_pre(parent,faces,pre)
    assert np.all(e>0) and np.array_equal(e,l)
    pre[parent[0]]["mantle_lithosphere_thickness_m"]=-1
    with pytest.raises(SparseP1Error,match="THICKNESS_INVALID"):
        local_law_from_pre(parent,faces,pre)


def test_independent_static_sparse_spd_work_and_feedback():
    _,K,stats=compare()
    ll=fixture()[1]
    xyz,unit,e,n=frames_and_cartesian(ll)
    rotation=np.cross([0,0,1e-15],xyz)
    rigid=np.stack((np.einsum("ij,ij->i",rotation,e),
                    np.einsum("ij,ij->i",rotation,n)),axis=1).ravel()
    g=rigid+np.array([0.,0.,.003,0.,0.,-.002,0.,.001])
    out=static_global_spd_probe(K,stats,{
        "manufactured_target":g,
        "euler":rigid,
        "synthetic_nonrigid_part":g-rigid,
    })
    assert out["cg_info"]==0
    assert out["cg_final_relative_residual"]<1e-8
    assert out["synthetic_static_work_balance_relative"]<1e-8
    assert out["relative_velocity_correction"]>0


def test_no_canonical_inputs_or_global_history_in_source_free_unit_tests():
    ids,ll,faces,eta,bulk,_=fixture()
    K,out=sparse_p1_tangent(ll,faces,eta,bulk)
    assert "physical_T1" not in out
    assert out["EN_dofs"]==8
