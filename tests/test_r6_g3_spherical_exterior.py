"""Manufactured spherical G3 A finite elements; synthetic materials only."""
from types import SimpleNamespace
import numpy as np
import pytest

from experiments.plate58_deforming_explore_v1.spherical_exterior import (
    SphericalExteriorInputError, frames_and_cartesian,
    spherical_element_tangent, spherical_triangle_geometry,
    assemble_spherical_exterior, source_geometry_audit,
)


def nodal_rotation(coords, omega):
    x, _, e, n = frames_and_cartesian(coords)
    v = np.cross(omega, x)
    return np.stack((np.einsum("ij,ij->i", v, e),
                     np.einsum("ij,ij->i", v, n)),axis=1).ravel()


def test_exact_three_rigid_rotation_modes_on_facet():
    coords = np.array([[11.,20.],[11.,21.],[12.,20.]])
    k,g = spherical_element_tangent(coords,1e21,3e20)
    for omega in np.eye(3)*1e-15:
        u=nodal_rotation(coords,omega)
        assert np.linalg.norm(g["strain_operator"]@u)<2e-29
        assert abs(u@k@u)/(np.linalg.norm(k)*np.linalg.norm(u)**2)<1e-12
    assert 0<g["facet_sphere_relative_area_deficit"]<0.002


def test_global_two_triangle_three_rigid_modes():
    ids=[11,12,13,14]
    ll=np.array([[11.,20.],[11.,21.],[12.,21.],[12.,20.]])
    law={"authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
         "source_reference":"SYNTHETIC_SURFACE_VISCOSITY_NOT_ARCANA",
         "eta_h_pa_s_m":1e21,"lambda_h_pa_s_m":1e20}
    obj=assemble_spherical_exterior(
        ids,{3:(11,12,13),4:(11,13,14)},dict(zip(ids,ll)),
        {3:law,4:law})
    k=obj["tangent"]
    assert k.shape==(8,8) and np.allclose(k,k.T)
    for omega in np.eye(3)*1e-15:
        u=nodal_rotation(ll,omega)
        assert np.linalg.norm(k@u)/(np.linalg.norm(k)*np.linalg.norm(u))<1e-12
    assert np.count_nonzero(np.linalg.eigvalsh(k)>1e-8*np.max(np.linalg.eigvalsh(k)))==5
    assert obj["shellset_covariant_and_nonlinear_parity"] is False
    assert obj["physical_load"] is None


def test_nonrigid_nodal_velocity_positive_energy():
    coords=np.array([[11.,20.],[11.,21.],[12.,20.]])
    k,_=spherical_element_tangent(coords,1e21,3e20)
    u=np.array([0.,0.,10.,0.,0.,0.])
    assert u@k@u>0


def test_facet_winding_preserves_area():
    coords=np.array([[11.,20.],[11.,21.],[12.,20.]])
    a=spherical_triangle_geometry(coords)
    b=spherical_triangle_geometry(coords[::-1])
    assert a["facet_area_m2"]==pytest.approx(b["facet_area_m2"])
    assert a["spherical_area_m2"]==pytest.approx(b["spherical_area_m2"])


def test_antimeridian_and_high_lat():
    for points in ([[2.,179.8],[2.,-179.8],[3.,179.8]],
                   [[80.,30.],[80.,31.],[81.,30.]]):
        k,_=spherical_element_tangent(points,1e21,3e20)
        assert np.all(np.isfinite(k))


def test_missing_physical_material_is_not_imputed():
    with pytest.raises((SphericalExteriorInputError,ValueError,TypeError)):
        spherical_element_tangent([[11,20],[11,21],[12,20]],None,1e20)


def test_missing_source_node_fails_closed():
    law={"authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
         "source_reference":"SYNTHETIC_SURFACE_VISCOSITY_NOT_ARCANA",
         "eta_h_pa_s_m":1e21,"lambda_h_pa_s_m":1e20}
    with pytest.raises(SphericalExteriorInputError,match="COVERAGE"):
        assemble_spherical_exterior(
            [1,2,3,4],{10:(1,2,3)},
            {1:(10,20),2:(10,21),3:(11,20)},{10:law})


def test_source_style_eight_cell_geometry_audit_no_mechanics():
    size=8
    coords=[(5+i,20+j) for i in range(9) for j in range(9)]
    def node(i,j):return 1+i*9+j
    elements=[]
    for i in range(size):
        for j in range(size):
            for tri in ((node(i,j),node(i,j+1),node(i+1,j+1)),
                        (node(i,j),node(i+1,j+1),node(i+1,j))):
                elements.append(SimpleNamespace(node_ids=tri))
    tids=list(range(1,len(elements)+1))
    core=[]
    for i in (3,4):
        for j in (3,4):
            core.extend([2*(i*size+j)+1,2*(i*size+j)+2])
    interface=sorted([node(i,j) for i in range(3,6)
                      for j in range(3,6) if (i,j)!=(4,4)])
    center=node(4,4)
    order=interface+[n for n in range(1,82) if n not in interface+[center]]
    region={"cell_extent_per_side":8,"parent_node_ids":list(range(1,82)),
            "parent_triangle_ids":tids}
    scale={"source_exterior_triangles":[n for n in tids if n not in core],
           "mechanical_node_order_interface_first":order,
           "source_interface_node_ids":interface,
           "actual_3plus_plate_junctions":[]}
    feg=SimpleNamespace(
        nodes=[SimpleNamespace(latitude_deg=la,longitude_deg=lo)
               for la,lo in coords],
        elements=elements)
    audit=source_geometry_audit(region,scale,feg)
    assert audit["exterior_triangles"]==120
    assert audit["mechanical_dofs"]==160
    assert audit["max_unit_test_rigid_rotation_strain_s_inv"]<1e-23
    assert audit["physical_operator"] is None
