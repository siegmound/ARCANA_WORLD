"""Source/GPE hydrostatic and spherical-force identities; noncanonical."""
import numpy as np
import pytest

from experiments.plate58_deforming_explore_v1.g3_gpe_hydrostatic import (
    column_hydrostatics, triangle_gpe_gradient_load, assemble_candidate_gpe,
)


def pre(rho=3300.):
    return {"crust_thickness_m":30000.,"mantle_lithosphere_thickness_m":50000.,
            "crust_density_kg_m3":rho,"mantle_density_kg_m3":rho,
            "rho_asthenosphere_kg_m3":rho,"rho_water_kg_m3":1027.}


def test_uniform_reference_column_partition_independence():
    x=column_hydrostatics(pre(),0.,gravity_m_s2=10.,
                          reference_elevation_m=-200000.)
    assert x["hydrostatic_normal_pressure_Pa"]==pytest.approx(
        3300*10*200000)
    assert x["gpe_J_m2"]==pytest.approx(0.5*3300*10*200000**2)
    assert not x["physical_isostasy_qualified"]


def test_submerged_column_includes_water_load():
    x=column_hydrostatics(pre(),-2000.,gravity_m_s2=9.81,
                          reference_elevation_m=-200000.)
    assert x["surface_water_depth_m"]==2000.
    assert x["lithosphere_base_elevation_m"]==-82000.
    assert x["hydrostatic_normal_pressure_Pa"]>0


def test_reference_plane_through_lithosphere_fails_closed():
    with pytest.raises(ValueError,match="REFERENCE_LEVEL_INTERSECTS"):
        column_hydrostatics(pre(),0.,gravity_m_s2=9.81,
                            reference_elevation_m=-20000.)


def test_constant_large_gpe_must_produce_exact_zero_nodal_force():
    f,area,grad=triangle_gpe_gradient_load(
        [[10.,20.],[10.,21.],[11.,20.]],[5e14,5e14,5e14])
    assert np.all(f==0.)
    assert np.all(grad==0.)
    assert area>0


def test_nonuniform_gpe_produces_finite_force_and_tangent_orientation():
    f,area,grad=triangle_gpe_gradient_load(
        [[10.,20.],[10.,20.5],[10.5,20.]],
        [5e14,5e14+1e8,5e14+3e8])
    assert np.all(np.isfinite(f)) and np.linalg.norm(f)>0
    assert np.all(np.isfinite(grad)) and np.linalg.norm(grad)>0


def test_two_original_parent_triangles_keep_one_set_of_nodal_dofs():
    ids=[100,101,102,103]
    coords={100:(10.,20.),101:(10.,20.2),
            102:(10.2,20.2),103:(10.2,20.)}
    tris={700:(100,101,102),701:(100,102,103)}
    gpe={n:5e14 for n in ids}
    out=assemble_candidate_gpe(ids,tris,coords,gpe)
    assert out["candidate_gpe_nodal_force_N"].shape==(8,)
    assert np.all(out["candidate_gpe_nodal_force_N"]==0.)
    assert out["mechanical_solve_authorized"] is False


def test_missing_source_triangle_or_node_not_silently_imputed():
    with pytest.raises(ValueError,match="GPE_SOURCE_TRIANGLE_NODE_MISSING"):
        assemble_candidate_gpe(
            [1,2,3,4],{10:(1,2,3)},
            {1:(10,20),2:(10,21),3:(11,20),4:(11,21)},
            {1:1e15,2:1e15,3:1e15})
