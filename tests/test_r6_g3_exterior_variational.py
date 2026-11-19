"""Synthetic G3 A viscous membrane FEM checks; not actual ARCANA G2."""
import numpy as np
import pytest
from experiments.plate58_deforming_explore_v1.exterior_variational import (
    MechanicalInputError,triangle_viscous_tangent,
    integrated_viscosity_tensor,assemble_explicit_exterior,tangent_log_map,
    affine_patch_energy)


def model():
    coords={1:(0.,0.),2:(1000.,0.),3:(1000.,1000.),4:(0.,1000.)}
    faces={11:(1,2,3),12:(1,3,4)}
    law={"source_reference":"SYNTHETIC_HOMOGENEOUS_VISCOSITY_NOT_ARCANA",
       "authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
       "eta_h_pa_s_m":8e19,"lambda_h_pa_s_m":3e19}
    return list(coords),faces,coords,{11:law.copy(),12:law.copy()}


def test_patch_affine_work_and_symmetry():
    coords=np.array([[0.,0.],[1000.,0.],[0.,1000.]])
    a=np.array([[0.,0.5e-14,0.25e-14],[0.,-0.2e-14,0.3e-14]])
    patch=affine_patch_energy(coords,8e19,3e19,a)
    assert patch["relative_error"]<1e-14
    k,_,area=triangle_viscous_tangent(coords,8e19,3e19)
    assert area==pytest.approx(500000.)
    assert np.allclose(k,k.T)
    eig=np.linalg.eigvalsh(k)
    assert eig[-1]>0
    assert eig[-4]<1e-5*eig[-1]


def test_rigid_modes_gauge_and_force_balance():
    ids,faces,coords,mats=model()
    out=assemble_explicit_exterior(ids,faces,coords,mats)
    k=out["tangent"]
    assert out["area_m2"]==pytest.approx(1e6)
    assert k.shape==(8,8)
    for v in ([1.,0.]*4,[0.,1.]*4):
        assert np.linalg.norm(k@np.array(v))/np.linalg.norm(k)<1e-10
    omega=[]
    for i in ids:
        x,y=coords[i]
        omega.extend([-y,x])
    assert np.linalg.norm(k@omega)/(np.linalg.norm(k)*np.linalg.norm(omega))<1e-12
    eig=np.linalg.eigvalsh(k)
    assert np.count_nonzero(eig>1e-7*np.max(eig))==5
    assert out["G3_A_real_boundary_tractions"] is None
    assert out["mechanical_solve_authorized"] is False


def test_shear_tensor_is_dimensioned_and_positive():
    d=integrated_viscosity_tensor(8e19,3e19)
    assert np.min(np.linalg.eigvalsh(d))>0
    assert d[2,2]==8e19


def test_material_coverage_guard():
    ids,faces,coords,mats=model()
    del mats[12]
    with pytest.raises(MechanicalInputError,match="COVERAGE_INCOMPLETE"):
        assemble_explicit_exterior(ids,faces,coords,mats)


def test_missing_material_provenance_guard():
    ids,faces,coords,mats=model()
    mats[11]["authority"]="AUTHOR_RATIFIED"
    with pytest.raises(MechanicalInputError,match="PROVENANCE_OR_AUTHORITY_MISSING"):
        assemble_explicit_exterior(ids,faces,coords,mats)


def test_degenerate_element_fails():
    with pytest.raises(MechanicalInputError,match="SINGULAR"):
        triangle_viscous_tangent([(0,0),(1,1),(2,2)],8e19,3e19)


def test_tangent_map_origin_and_cardinal_orientation():
    p=tangent_log_map([[10.,20.],[10.,21.],[11.,20.]],[10.,20.])
    assert np.linalg.norm(p[0])<1e-8
    assert p[1,0]>0 and abs(p[1,1])<200
    assert p[2,1]>0 and abs(p[2,0])<200


def test_no_material_default():
    ids,faces,coords,mats=model()
    mats[11].pop("eta_h_pa_s_m")
    with pytest.raises(MechanicalInputError,match="MATERIAL_TANGENT_MISSING"):
        assemble_explicit_exterior(ids,faces,coords,mats)
