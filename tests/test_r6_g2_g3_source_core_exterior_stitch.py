"""R6 single-parent source G2 8-core + G3 exterior internal weak form tests.

These are SYNTHETIC fixtures, NOT true ARCANA source materials, rock faults
or a valid assembled global physical load. Core external forces remain unknown.
"""
from copy import deepcopy
import math

import numpy as np
import pytest

from experiments.plate58_deforming_explore_v1.g2_g3_source_core_exterior_stitch import (
    source_core_contribution,stitch_source_core_exterior,StitchedCandidateError,
    SCHEMA,
)
from experiments.plate58_deforming_explore_v1.g2_g3_coupled_weak_form import (
    SCHEMA as EXT_SCHEMA,
)


def _pre(n):
    return {
        "node_id":float(n),"material_configuration_code":1.,
        "crust_thickness_m":30000.,"mantle_lithosphere_thickness_m":50000.,
        "crust_density_kg_m3":2800.,"mantle_density_kg_m3":3250.,
        "layer1_z0_m":0.,"layer1_z1_m":30000.,
        "layer2_z0_m":30000.,"layer2_z1_m":80000.,
        "layer1_c0_k":850.,"layer1_c1_k_m":0.,
        "layer1_c2_k_m2":0.,"layer1_c3_k_m3":0.,
        "layer2_c0_k":1450.,"layer2_c1_k_m":0.,
        "layer2_c2_k_m2":0.,"layer2_c3_k_m3":0.,
    }


def _law():
    def layer(n):
        return {
            "authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
            "ductile":{
                "source_reference":"SYNTHETIC_FAN_CREEP_NOT_ARCANA",
                "stress_convention":"ASPECT_2ETA_EPS_INVARIANT_SCALE",
                "A_pa_minus_n_s_inv":1e-28,
                "n":n,"E_j_mol":200000.,"V_m3_mol":0.,
                "fugacity_exponent":0.,"water_fugacity_pa":None,
                "reference_fugacity_pa":None,
                "valid_temperature_k":[250.,1900.],
                "valid_pressure_pa":[0.,4e9],
                "valid_strain_rate_s_inv":[1e-19,1e-10],
            },
            "brittle":{
                "source_reference":"SYNTHETIC_FAN_DP_NOT_ARCANA",
                "criterion":"DRUCKER_PRAGER_3D_CONTINUUM",
                "drucker_prager_pressure_convention":"ASPECT_RHEOLOGY_DP_3D_6P",
                "cohesion_pa":5e6,"friction_angle_deg":30.,
                "biot_coefficient":1.,
                "pore_pressure_over_lithostatic":.3,
            },
        }
    return {
        "authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
        "source_identifier":"SYNTHETIC_CORE_RING_VP_001",
        "regularization_strain_rate_s_inv":1e-18,
        "gravity_m_s2":9.82,"gauss_points_per_layer":4,
        "layers":{"crust":layer(4.),"mantle":layer(3.5)}
    }


def core_ring():
    interface=list(range(1,9))
    core_only=9
    ids=interface+[core_only]
    # Small geodesic fan around the test-only center, not ARCANA lat/lon.
    ll={n:(.30*math.sin((n-1)*math.pi/4),
           .30*math.cos((n-1)*math.pi/4)) for n in interface}
    ll[core_only]=(0.,0.)
    faces={100+i:(core_only,interface[i],interface[(i+1)%8])
           for i in range(8)}
    bindings={
        tid:{
            "parent_triangle_id":tid,
            "parent_node_ids":list(tri),
            "vertex_quadrature_weights":[1./3]*3,
            "material_law_by_node":None,
            "material_configuration_codes":[1.]*3,
            "PRE_source_only_not_constitutive_projection":True,
        }
        for tid,tri in faces.items()
    }
    v={n:(1.e-10*n,-1.e-10*n) for n in ids}
    return {
        "core_node_order":ids,"core_triangles":faces,
        "source_core_triangle_bindings":bindings,
        "source_pre_by_parent_node":{n:_pre(n) for n in ids},
        "candidate_material_by_parent_node":{n:_law() for n in ids},
        "node_lat_lon_deg":ll,
        "velocity_en_by_parent_node":v,
    }


def synthetic_stitch():
    # 8 shared parent nodes, 1 core center, 2 exterior-only.
    ids=list(range(1,12))
    core_ids=list(range(1,10))
    ext_ids=list(range(1,9))+[10,11]
    v={n:np.array([.01*n,-.02*n]) for n in ids}
    f_core=np.arange(1.,19.)
    f_ext=np.arange(1.,21.)*.1
    f_known=np.arange(1.,21.)*.01
    kc=3.*np.eye(18)
    ke=5.*np.eye(20)
    kc[0,16]=kc[16,0]=.4 # core interface ↔ center coupling
    core={
        "source_node_order":core_ids,
        "source_triangle_count":8,
        "candidate_internal_force_N":f_core.tolist(),
        "candidate_tangent_N_s_per_m":kc.tolist(),
        "candidate_dissipation_potential_N_m_per_s":12.,
        "candidate_internal_virtual_power_W":
            float(f_core@np.stack([v[n] for n in core_ids]).ravel()),
        "mechanical_solve_authorized":False,
        "physical_T1":None,
    }
    exterior={
        "schema":EXT_SCHEMA,
        "source_scope":"SYNTHETIC_UNIT_TEST_NOT_ARCANA",
        "source_node_order":ext_ids,
        "source_parent_triangle_count":2,
        "candidate_internal_force_N":f_ext.tolist(),
        "candidate_external_plus_GPE_force_N":f_known.tolist(),
        "candidate_weak_form_residual_N":(f_ext-f_known).tolist(),
        "candidate_tangent_N_s_per_m":ke.tolist(),
        "candidate_dissipation_potential_N_m_per_s":7.,
        "candidate_virtual_power_W":{
            "internal":float(f_ext@np.stack([v[n] for n in ext_ids]).ravel()),
            "external_plus_GPE":float(
                f_known@np.stack([v[n] for n in ext_ids]).ravel())
        },
        "physical_solver_runs":0,"physical_T1":None,
        "source_solid_contact_gap_available":False,
    }
    args={
        "original_parent_node_order":ids,
        "original_core_interface_node_ids":list(range(1,9)),
        "original_core_only_node_id":9,
        "velocity_en_by_original_parent_node":v,
        "fixture_only":True,
    }
    return core,exterior,args


def test_real_engineering_g2_core_8_source_triangles_with_vertex_quadrature():
    s=core_ring()
    r=source_core_contribution(**s)
    assert r["source_triangle_count"]==8
    assert r["source_node_order"]==list(range(1,10))
    assert r["source_area_m2"]>0.
    assert r["candidate_dissipation_potential_N_m_per_s"]>=0.
    f=np.asarray(r["candidate_internal_force_N"])
    k=np.asarray(r["candidate_tangent_N_s_per_m"])
    assert f.shape==(18,) and np.all(np.isfinite(f))
    assert k.shape==(18,18) and np.all(np.isfinite(k))
    assert np.allclose(k,k.T,rtol=1e-12,atol=1e-8)
    assert r["mechanical_solve_authorized"] is False
    assert r["physical_T1"] is None


def test_core_source_parent_node_id_not_fabricated():
    s=core_ring()
    s["source_pre_by_parent_node"][9]["node_id"]=8.
    with pytest.raises(StitchedCandidateError,
                       match="CORE_STITCH_G2_SOURCE_PRE_OR_MATERIAL_AUTHORITY_INVALID"):
        source_core_contribution(**s)


def test_core_source_triangle_config_metadata_cannot_drift():
    s=core_ring()
    s["source_core_triangle_bindings"][100]["material_configuration_codes"]=[1.,7.,1.]
    with pytest.raises(StitchedCandidateError,
                       match="CORE_STITCH_SOURCE_MATERIAL_CONFIGURATION_CHANGED"):
        source_core_contribution(**s)


def test_full_domain_11_nodes_source_interface_shared_once_and_cross_tangent():
    core,ext,args=synthetic_stitch()
    r=stitch_source_core_exterior(core,ext,**args)
    assert r["schema"]==SCHEMA
    assert r["original_source_parent_node_count"]==11
    assert r["source_G2_core_triangle_count"]==8
    assert r["source_G3_exterior_triangle_count"]==2
    assert r["source_original_full_domain_triangle_count"]==10
    assert r["source_original_shared_interface_en_dof_count"]==16
    fi=np.asarray(r["candidate_whole_domain_internal_force_N"])
    K=np.asarray(r["candidate_whole_domain_internal_tangent_N_s_per_m"])
    # Shared node 1: source force sum; center 9: core only; node 10 ext only.
    assert fi[0]==pytest.approx(1.+.1)
    assert fi[16]==pytest.approx(17.)
    assert fi[18]==pytest.approx(1.7)
    assert K[0,0]==pytest.approx(8.)
    assert K[16,16]==pytest.approx(3.)
    assert K[18,18]==pytest.approx(5.)
    assert K[0,16]==pytest.approx(.4)
    assert K[16,0]==pytest.approx(.4)
    assert K.shape==(22,22)
    assert r["candidate_whole_domain_dissipation_potential_N_m_per_s"]==19.
    assert r["full_domain_physical_residual_AVAILABLE"] is False
    assert r["physical_T1"] is None
    assert r["D_024"]=="ACTIVE"


def test_virtual_power_stitches_same_node_velocities_in_shared_dofs():
    core,ext,args=synthetic_stitch()
    r=stitch_source_core_exterior(core,ext,**args)
    u=np.stack([args["velocity_en_by_original_parent_node"][i]
                for i in args["original_parent_node_order"]]).ravel()
    f=np.asarray(r["candidate_whole_domain_internal_force_N"])
    known=np.asarray(r["known_exterior_external_and_GPE_force_N"])
    assert r["candidate_virtual_power_W"]["whole_internal"]==pytest.approx(
        float(f@u))
    assert r["candidate_virtual_power_W"]["known_exterior_external"]==pytest.approx(
        float(known@u))
    assert r["candidate_virtual_power_W"]["PARTIAL_residual"]==pytest.approx(
        float((f-known)@u))
    assert r["core_external_and_basal_GPE_physics_qualified"] is False


@pytest.mark.parametrize("mutate",[
    "interface","center","ext_order","hidden_residual",
    "core_power","ext_power","duplicate_node",
])
def test_source_stitch_fails_closed_on_ownership_or_virtual_work(mutate):
    core,ext,args=synthetic_stitch()
    if mutate=="interface":
        args["original_core_interface_node_ids"][0]=10
    elif mutate=="center":
        args["original_core_only_node_id"]=10
    elif mutate=="ext_order":
        ext["source_node_order"][0],ext["source_node_order"][1]=(
            ext["source_node_order"][1],ext["source_node_order"][0])
    elif mutate=="hidden_residual":
        ext["candidate_weak_form_residual_N"][0]+=2.
    elif mutate=="core_power":
        core["candidate_internal_virtual_power_W"]+=8.
    elif mutate=="ext_power":
        ext["candidate_virtual_power_W"]["internal"]+=8.
    else:
        args["original_parent_node_order"][0]=2
    with pytest.raises(StitchedCandidateError):
        stitch_source_core_exterior(core,ext,**args)


def test_not_qualified_full_source_scope_cannot_be_asserted_from_small_fixture():
    core,ext,args=synthetic_stitch()
    args["fixture_only"]=False
    ext["source_scope"]="SOURCE_ORIGINAL_8x8_5_8"
    with pytest.raises(StitchedCandidateError):
        stitch_source_core_exterior(core,ext,**args)


def test_missing_core_external_load_never_converted_to_zero_physical_support():
    core,ext,args=synthetic_stitch()
    r=stitch_source_core_exterior(core,ext,**args)
    assert "physical_total_residual_N" not in r
    assert r["core_external_and_basal_GPE_physics_qualified"] is False
    assert r["full_domain_mechanical_equilibrium_qualified"] is False
    assert r["physical_solver_runs"]==0
