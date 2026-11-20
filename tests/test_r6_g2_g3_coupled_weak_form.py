"""Integrated R6 G2/G3 membrane residual and force accounting: synthetic only."""
from copy import deepcopy

import numpy as np
import pytest

from experiments.plate58_deforming_explore_v1.g2_g3_coupled_weak_form import (
    MODEL_FAMILY, CoupledAssemblyError, integrate_coupled_candidate,
)
from experiments.plate58_deforming_explore_v1.g3_force_budget import (
    ENGINEERING_AUTHORITY, edge_key,
)
from experiments.plate58_deforming_explore_v1.g3_gpe_force_accounting import (
    GPE_OWNER,
)


def pre(node):
    return {
        "node_id":float(node),"material_configuration_code":1.,
        "crust_thickness_m":30000.,
        "mantle_lithosphere_thickness_m":50000.,
        "crust_density_kg_m3":2800.,"mantle_density_kg_m3":3250.,
        "layer1_z0_m":0.,"layer1_z1_m":30000.,
        "layer2_z0_m":30000.,"layer2_z1_m":80000.,
        "layer1_c0_k":850.,"layer1_c1_k_m":0.,
        "layer1_c2_k_m2":0.,"layer1_c3_k_m3":0.,
        "layer2_c0_k":1450.,"layer2_c1_k_m":0.,
        "layer2_c2_k_m2":0.,"layer2_c3_k_m3":0.,
    }


def candidate():
    def material(n):
        return {
          "authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
          "ductile":{
              "source_reference":"SYNTHETIC_DISLOCATION_NOT_ARCANA",
              "stress_convention":"ASPECT_2ETA_EPS_INVARIANT_SCALE",
              "A_pa_minus_n_s_inv":1e-28,"n":n,
              "E_j_mol":200000.,"V_m3_mol":0.,
              "fugacity_exponent":0.,
              "water_fugacity_pa":None,"reference_fugacity_pa":None,
              "valid_temperature_k":[250.,1900.],
              "valid_pressure_pa":[0.,4e9],
              "valid_strain_rate_s_inv":[1e-19,1e-10]},
          "brittle":{
              "source_reference":"SYNTHETIC_DRUCKER_PRAGER_NO_ARCANA",
              "criterion":"DRUCKER_PRAGER_3D_CONTINUUM",
              "drucker_prager_pressure_convention":"ASPECT_RHEOLOGY_DP_3D_6P",
              "cohesion_pa":5e6,"friction_angle_deg":30.,
              "biot_coefficient":1.,
              "pore_pressure_over_lithostatic":0.3,
          }}
    return {
       "authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
       "source_identifier":"SYNTHETIC_COUPLED_SCENARIO_TEST_001",
       "regularization_strain_rate_s_inv":1e-18,
       "gravity_m_s2":9.82,
       "gauss_points_per_layer":4,
       "layers":{"crust":material(4.),"mantle":material(3.5)},
    }


def scenario():
    ids=[100,101,102,103]
    triangles={55:(100,101,102),56:(100,102,103)}
    latlon={100:(0.,0.),101:(0.,.7),102:(.7,.7),103:(.7,0.)}
    source_edges=[
       {"source_parent_node_ids":[100,101],"side":"south","adjacent_plate_id":5},
       {"source_parent_node_ids":[101,102],"side":"east","adjacent_plate_id":5},
       {"source_parent_node_ids":[102,103],"side":"north","adjacent_plate_id":8},
       {"source_parent_node_ids":[103,100],"side":"west","adjacent_plate_id":8},
    ]
    line={}
    for r in source_edges:
        v=r["source_parent_node_ids"]
        line[edge_key(v)]={
            "authority":ENGINEERING_AUTHORITY,
            "source_reference":"SYNTHETIC_COUPLED_NO_PHYSICAL_TRACTION",
            "source_parent_node_ids":v,
            "side":r["side"],"adjacent_plate_id":r["adjacent_plate_id"],
            "force_channel":"EXTERIOR_BOUNDARY",
            "nodal_xyz_N_per_m":[[0.,0.,0.],[0.,0.,0.]],
        }
    basal={
        tid:{
          "authority":ENGINEERING_AUTHORITY,
          "source_reference":"SYNTHETIC_COUPLED_ZERO_BASAL_NOT_NATURAL",
          "parent_triangle_id":tid,"parent_node_ids":list(nodes),
          "force_channel":"BASAL_TANGENTIAL",
          "nodal_xyz_N_per_m2":[[0.,0.,0.]]*3,
        } for tid,nodes in triangles.items()
    }
    binds={
        tid:{
            "parent_triangle_id":tid,"parent_node_ids":list(nodes),
            "vertex_quadrature_weights":[1./3]*3,
            "material_configuration_codes":[1.,1.,1.],
            "material_law_by_node":None,
            "PRE_source_only_not_constitutive_projection":True,
        } for tid,nodes in triangles.items()
    }
    velocity={100:[0.,0.],101:[1e-9,0.],
              102:[1e-9,-2e-9],103:[0.,-2e-9]}
    return dict(
        scope={
            "model_family":MODEL_FAMILY,
            "physical_source_authority_ratified":False,
            "mechanical_solve_authorized":False,
            "source_scope":"SYNTHETIC_UNIT_TEST_NOT_ARCANA",
            "fixture_only":True,
            "interface_contact_authority":"UNQUALIFIED",
            "basal_normal_support_authority":"UNQUALIFIED",
            "constitutive_full_fault_law_authority":"UNQUALIFIED",
        },
        node_order=ids,parent_triangle_nodes=triangles,
        source_triangle_bindings=binds,node_lat_lon_deg=latlon,
        source_pre_by_parent_node={n:pre(n) for n in ids},
        candidate_material_by_parent_node={n:candidate() for n in ids},
        velocity_en_by_parent_node=velocity,
        source_cut_edges=source_edges,
        line_tractions_by_edge=line,
        basal_tractions_by_triangle=basal,
        gpe={
          "source_interface_node_order":ids,
          "candidate_GPE_force_vector_N":[0.,1., 2.,0., 0.,-2., 1.,0.],
          "GPE_force_owner":GPE_OWNER,
          "mechanical_solve_authorized":False,
          "physical_T1":None,
        },
    )


def test_coupled_real_g2_vp_and_g3_two_channel_plus_external_gpe():
    s=scenario()
    r=integrate_coupled_candidate(**s)
    assert r["source_node_order"]==[100,101,102,103]
    assert r["source_parent_triangle_count"]==2
    assert r["external_cut_count"]==4
    assert r["source_basal_triangle_count"]==2
    assert r["candidate_dissipation_potential_N_m_per_s"]>=0
    internal=np.asarray(r["candidate_internal_force_N"])
    external=np.asarray(r["candidate_external_plus_GPE_force_N"])
    residual=np.asarray(r["candidate_weak_form_residual_N"])
    tangent=np.asarray(r["candidate_tangent_N_s_per_m"])
    v=np.array([x for n in s["node_order"]
                for x in s["velocity_en_by_parent_node"][n]])
    assert internal.shape==(8,)
    assert np.array_equal(external,[0.,1.,2.,0.,0.,-2.,1.,0.])
    assert np.allclose(residual,internal-external,rtol=1e-13)
    assert tangent.shape==(8,8)
    assert np.allclose(tangent,tangent.T,rtol=1e-12,atol=0)
    p=r["candidate_virtual_power_W"]
    assert p["residual"]==pytest.approx(float(residual@v),rel=1e-12,abs=1e-6)
    assert p["external_plus_GPE"]==pytest.approx(
        p["outer_cut"]+p["basal_tangential"]+p["gpe_external"],
        abs=1e-6)
    assert r["nonlinear_solver_iterations"]==0
    assert r["physical_solver_runs"]==0
    assert r["physical_T1"] is None
    assert r["source_solid_contact_gap_available"] is False
    assert r["D_024"]=="ACTIVE"


@pytest.mark.parametrize("channel",["material","traction","gpe","pre","source_node"])
def test_explicit_source_coverage_refuses_missing_channels(channel):
    s=scenario()
    if channel=="material":
        s["candidate_material_by_parent_node"].pop(100)
    elif channel=="traction":
        s["line_tractions_by_edge"].pop(edge_key([100,101]))
    elif channel=="gpe":
        s["gpe"]["source_interface_node_order"]=[101,100,102,103]
    elif channel=="pre":
        s["source_pre_by_parent_node"].pop(100)
    else:
        s["source_triangle_bindings"][55]["parent_node_ids"]=[100,102,101]
    with pytest.raises(ValueError):
        integrate_coupled_candidate(**s)


def test_cannot_hide_gpe_in_two_channels():
    s=scenario()
    s["gpe"]["GPE_force_owner"]="EXTERNAL_PLUS_INTERNAL_DOUBLE_COUNT"
    with pytest.raises(ValueError,match="GPE_DOUBLE_COUNT_OR_OWNER_UNKNOWN"):
        integrate_coupled_candidate(**s)


@pytest.mark.parametrize("flag",[
    "physical_source_authority_ratified","mechanical_solve_authorized",
])
def test_cannot_promote_undocumented_physics(flag):
    s=scenario()
    s["scope"][flag]=True
    with pytest.raises(CoupledAssemblyError,
                       match="SCOPE_OR_PHYSICAL_AUTHORITY_UNDECLARED"):
        integrate_coupled_candidate(**s)


def test_cannot_assign_material_from_source_configuration_code():
    s=scenario()
    s["candidate_material_by_parent_node"][100]["authority"]="SOURCE_AUTHENTIC"
    with pytest.raises(CoupledAssemblyError,
                       match="SOURCE_PRE_OR_MATERIAL_PROVENANCE_INVALID"):
        integrate_coupled_candidate(**s)


def test_cannot_pretend_true_source_original_node_count_with_synthetic_data():
    s=scenario()
    s["scope"]["source_scope"]="SOURCE_ORIGINAL_16x16_5_8_11"
    with pytest.raises(CoupledAssemblyError,
                       match="ORIGINAL_SOURCE_COUNTS_CHANGED"):
        integrate_coupled_candidate(**s)


def test_cannot_silently_promote_thermal_LAB_to_basement_contact():
    s=scenario()
    s["scope"]["basal_normal_support_authority"]="THERMAL_LAB_ASSUMED_MECHANICAL"
    with pytest.raises(CoupledAssemblyError,
                       match="UNAUTHORIZED_CONTACT_OR_NORMAL_SUPPORT"):
        integrate_coupled_candidate(**s)


def test_original_pre_node_id_cannot_silently_switch_parent():
    s=scenario()
    s["source_pre_by_parent_node"][100]["node_id"]=101.
    with pytest.raises(CoupledAssemblyError,
                       match="SOURCE_PRE_OR_MATERIAL_PROVENANCE_INVALID"):
        integrate_coupled_candidate(**s)


def test_original_material_configuration_metadata_must_match_pre_but_not_be_lithology():
    s=scenario()
    s["source_triangle_bindings"][55]["material_configuration_codes"]=[1.,9.,1.]
    with pytest.raises(CoupledAssemblyError,
                       match="SOURCE_CONFIGURATION_CODE_DRIFT"):
        integrate_coupled_candidate(**s)
