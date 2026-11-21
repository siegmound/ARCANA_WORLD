"""Real P1 load-quadrature regression on an explicit SYNTHETIC core+exterior fan.

No source mesh, ARCANA mantle forces or physical T1 are fabricated. The
synthetic input exercises the SAME G3 code path as a future source scenario.
"""
from copy import deepcopy
import math

import numpy as np
import pytest

from experiments.plate58_deforming_explore_v1.g2_g3_full_external_candidate import (
    assemble_full_candidate_external, STATUS,
)
from experiments.plate58_deforming_explore_v1.g2_g3_source_core_exterior_stitch import (
    StitchedCandidateError,
)
from experiments.plate58_deforming_explore_v1.g3_force_budget import (
    assemble_explicit_g3_loads, edge_key, SYNTHETIC_GPE_OWNER,
    ENGINEERING_AUTHORITY,
)
from experiments.plate58_deforming_explore_v1.g3_gpe_force_accounting import (
    GPE_OWNER,
)
from experiments.plate58_deforming_explore_v1.spherical_exterior import (
    frames_and_cartesian,
)
from experiments.plate58_deforming_explore_v1.g2_g3_core_exterior_source_runner import (
    validate_full_scenario, INPUT_FULL,
)


def synthetic_full_candidate():
    # 8 core ring nodes, the source core-only center 9, and two ext-only.
    ids=list(range(1,12))
    ext_order=list(range(1,9))+[10,11]
    ring={
        n:(0.25*math.sin((n-1)*math.pi/4),
           0.25*math.cos((n-1)*math.pi/4))
        for n in range(1,9)}
    coords={**ring,9:(0.,0.),10:(0.55,0.45),11:(0.56,-0.46)}
    xyz,radial,east,north=frames_and_cartesian(
        np.asarray([coords[n] for n in ids]))
    unit_east={n:east[i] for i,n in enumerate(ids)}
    core={100+i:(9,1+i,1+((i+1)%8)) for i in range(8)}
    exterior={200:(1,2,10),201:(3,4,11),202:(5,6,10),203:(7,8,11)}
    cuts=[
        {"source_parent_node_ids":[1,10],"side":"north","adjacent_plate_id":5},
        {"source_parent_node_ids":[2,10],"side":"east","adjacent_plate_id":5},
        {"source_parent_node_ids":[3,11],"side":"south","adjacent_plate_id":8},
        {"source_parent_node_ids":[4,11],"side":"west","adjacent_plate_id":8},
    ]
    line={}
    for row in cuts:
        key=edge_key(row["source_parent_node_ids"])
        line[key]={
            **row,
            "force_channel":"EXTERIOR_BOUNDARY",
            "authority":ENGINEERING_AUTHORITY,
            "source_reference":"SYNTHETIC_CUT_TRACTION_NOT_ARCANA_20261121",
            "nodal_xyz_N_per_m":[
                (120.*unit_east[n]).tolist()
                for n in row["source_parent_node_ids"]],
        }
    def basal(triangles):
        return {tid:{
            "parent_triangle_id":tid,
            "parent_node_ids":list(nodes),
            "force_channel":"BASAL_TANGENTIAL",
            "authority":ENGINEERING_AUTHORITY,
            "source_reference":"SYNTHETIC_BASAL_TRACTION_NOT_ARCANA_20261121",
            "nodal_xyz_N_per_m2":[
                (20.*unit_east[n]).tolist() for n in nodes],
        } for tid,nodes in triangles.items()}
    ext_basal=basal(exterior)
    core_basal=basal(core)
    gpe=np.asarray([[2.5*n,-3.7*n] for n in ext_order])
    exterior_gpe={
        "GPE_force_owner":GPE_OWNER,
        "source_interface_node_order":ext_order,
        "candidate_GPE_force_vector_N":gpe.ravel().tolist(),
        "mechanical_solve_authorized":False,
        "physical_T1":None,
    }
    core_gpe={str(n):{
        "force_en_N":[4.0*n,-0.5*n],
        "force_channel":"CORE_TRIANGLE_GPE_INCREMENT_ONLY",
        "GPE_force_owner":GPE_OWNER,
        "authority":ENGINEERING_AUTHORITY,
        "source_reference":"SYNTHETIC_EXPLICIT_CORE_GPE_INCREMENT_20261121",
    } for n in range(1,10)}
    old=assemble_explicit_g3_loads(
        ext_order,{n:coords[n] for n in ext_order},cuts,line,
        exterior,ext_basal,gpe_ownership=SYNTHETIC_GPE_OWNER)
    known_ext=np.asarray(old["candidate_total_nodal_force_N"]).reshape(-1,2)+gpe
    pos={n:i for i,n in enumerate(ids)}
    known=np.zeros((11,2))
    for j,n in enumerate(ext_order):
        known[pos[n]]=known_ext[j]
    internal=np.arange(22,dtype=float).reshape(11,2)*6.0
    stitched={
        "fixture_only":True,
        "original_parent_node_order":ids,
        "source_interface_node_ids":list(range(1,9)),
        "source_core_only_node_id":9,
        "source_G2_core_triangle_count":8,
        "source_G3_exterior_triangle_count":4,
        "source_original_full_domain_triangle_count":12,
        "candidate_whole_domain_internal_force_N":internal.ravel().tolist(),
        "known_exterior_external_and_GPE_force_N":known.ravel().tolist(),
        "known_PARTIAL_residual_N_NOT_EQUILIBRIUM":
            (internal-known).ravel().tolist(),
        "full_domain_physical_residual_AVAILABLE":False,
        "physical_solver_runs":0,
        "physical_T1":None,
    }
    ext_result={
        "source_node_order":ext_order,
        "candidate_external_plus_GPE_force_N":known_ext.ravel().tolist(),
        "physical_solver_runs":0,
        "physical_T1":None,
    }
    kwargs={
        "stitched":stitched,
        "exterior":ext_result,
        "original_parent_node_order":ids,
        "source_core_triangles":core,
        "source_exterior_triangles":exterior,
        "source_cut_edges":cuts,
        "node_lat_lon_deg":coords,
        "line_tractions_by_edge":line,
        "exterior_basal_tractions_by_triangle":ext_basal,
        "core_basal_tractions_by_triangle":core_basal,
        "exterior_gpe":exterior_gpe,
        "core_gpe_increment_by_parent_node":core_gpe,
        "velocity_en_by_parent_node":{n:[1e-10*n,-2e-10*n] for n in ids},
        "fixture_only":True,
    }
    return kwargs


def test_full_core_and_exterior_have_no_unowned_loads_and_partition():
    a=synthetic_full_candidate()
    r=assemble_full_candidate_external(**a)
    assert r["status"]==STATUS
    assert r["source_original_core_triangles"]==8
    assert r["source_original_exterior_triangles"]==4
    assert r["source_original_basal_triangles"]==12
    assert r["source_external_cut_edges"]==4
    assert len(r["candidate_full_channel_external_N"])==22
    old=np.asarray(r["original_external_known_N"])
    core_b=np.asarray(r["new_core_basal_increment_N"])
    core_g=np.asarray(r["new_core_GPE_increment_N"])
    full=np.asarray(r["candidate_full_channel_external_N"])
    internal=np.asarray(a["stitched"]["candidate_whole_domain_internal_force_N"])
    residual=np.asarray(r["candidate_FULL_CHANNEL_residual_N_NOT_EQUILIBRIUM"])
    assert np.allclose(full,old+core_b+core_g,rtol=1e-12,atol=1e-6)
    assert np.allclose(residual,internal-full,rtol=1e-12,atol=1e-6)
    assert np.allclose(np.asarray(r["candidate_partial_to_full_residual_change_N"]),
                       -core_b-core_g,rtol=1e-12,atol=1e-6)
    assert abs(core_b[2*8])+abs(core_b[2*8+1])>0
    assert abs(core_g[2*8])+abs(core_g[2*8+1])>0
    assert r["full_domain_physical_residual_AVAILABLE"] is False
    assert r["mechanical_solve_authorized"] is False
    assert r["physical_T1"] is None
    assert r["HistoryStore_modified"] is False
    for channel in ("known_exterior_cut_basal_GPE","new_core_basal",
                    "new_core_GPE","candidate_all_external"):
        assert len(r["global_force_xyz_N"][channel])==3
        assert len(r["global_torque_xyz_N_m"][channel])==3
        assert math.isfinite(r["virtual_power_W"][channel])
    # Explicit source channel partitions conserve resultant, torque and work.
    for name in ("global_force_xyz_N","global_torque_xyz_N_m"):
        data=r[name]
        assert np.allclose(data["candidate_all_external"],
            np.asarray(data["known_exterior_cut_basal_GPE"])+
            np.asarray(data["new_core_basal"])+
            np.asarray(data["new_core_GPE"]),
            rtol=1e-12,atol=1e-3)
    p=r["virtual_power_W"]
    assert p["candidate_all_external"]==pytest.approx(
        p["known_exterior_cut_basal_GPE"]+
        p["new_core_basal"]+p["new_core_GPE"],rel=1e-12,abs=1e-8)


@pytest.mark.parametrize("mutation",[
    "missing_core_triangle","missing_core_gpe_node","duplicate_core_exterior",
    "non_source_gpe_owner","missing_source_reference","wrong_core_owner",
    "infinite_core_gpe","old_external_tampered","partial_residual_tampered",
    "unauthorized_physical_promotion","hidden_core_node",
])
def test_fail_closed_bad_core_channels_and_source_provenance(mutation):
    a=synthetic_full_candidate()
    if mutation=="missing_core_triangle":
        del a["core_basal_tractions_by_triangle"][100]
    elif mutation=="missing_core_gpe_node":
        del a["core_gpe_increment_by_parent_node"]["9"]
    elif mutation=="duplicate_core_exterior":
        a["source_exterior_triangles"][100]=(1,2,10)
    elif mutation=="non_source_gpe_owner":
        a["exterior_gpe"]["GPE_force_owner"]="DOUBLE_COUNT_SHELLS_GPE"
    elif mutation=="missing_source_reference":
        a["core_gpe_increment_by_parent_node"]["1"]["source_reference"]=""
    elif mutation=="wrong_core_owner":
        a["core_gpe_increment_by_parent_node"]["3"]["force_channel"]="EXTERIOR_GPE"
    elif mutation=="infinite_core_gpe":
        a["core_gpe_increment_by_parent_node"]["4"]["force_en_N"]=[math.inf,0.]
    elif mutation=="old_external_tampered":
        a["exterior"]["candidate_external_plus_GPE_force_N"][0]+=1e10
    elif mutation=="partial_residual_tampered":
        a["stitched"]["known_PARTIAL_residual_N_NOT_EQUILIBRIUM"][0]+=1e10
    elif mutation=="unauthorized_physical_promotion":
        a["stitched"]["physical_T1"]=1
    else:
        a["source_core_triangles"][100]=(9,1,11)
    with pytest.raises((StitchedCandidateError,ValueError)):
        assemble_full_candidate_external(**a)


def test_runner_does_not_accept_core_basal_without_core_gpe():
    ids=list(range(1,82))
    s={
        "schema":INPUT_FULL,
        "scope_extent_cells":8,
        "authority":ENGINEERING_AUTHORITY,
        "physical_source_authority_ratified":False,
        "mechanical_solve_authorized":False,
        "core_external_force_provider_qualified":False,
        "fault_interface_physics_authorized":False,
        "candidate_material_by_parent_node":{str(n):{"test":True} for n in ids},
        "velocity_en_by_parent_node":{str(n):[0.,0.] for n in ids},
        "line_tractions_by_edge":{"1:2":{"test":True}},
        "basal_tractions_by_triangle":{"100":{"test":True}},
        "external_gpe":{"test":True},
        "core_basal_tractions_by_triangle":{"100":{"test":True}},
        "core_gpe_increment_by_parent_node":None,
    }
    with pytest.raises(StitchedCandidateError,
                       match="CORE_SOURCE_CORE_G3_BASAL_AND_GPE_MUST_BE_PAIRED"):
        validate_full_scenario(s,ids,8)
    s["core_gpe_increment_by_parent_node"]={"9":{"test":True}}
    validate_full_scenario(s,ids,8)
    s["core_basal_tractions_by_triangle"]=None
    with pytest.raises(StitchedCandidateError):
        validate_full_scenario(s,ids,8)


def test_fixture_outer_facet_node_coverage_is_exact():
    a=synthetic_full_candidate()
    ext_nodes={node for tri in a["source_exterior_triangles"].values()
               for node in tri}
    assert ext_nodes==set(a["exterior"]["source_node_order"])
    core_nodes={node for tri in a["source_core_triangles"].values()
                for node in tri}
    assert len(core_nodes)==9
    assert core_nodes & ext_nodes == set(range(1,9))
    assert core_nodes - ext_nodes == {9}
    assert len(a["source_exterior_triangles"])==4
    assert len(a["source_core_triangles"])==8
