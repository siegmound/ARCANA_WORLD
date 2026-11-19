"""G3 A external/basal traction virtual work and provenance tests (synthetic)."""
import numpy as np
import pytest

from experiments.plate58_deforming_explore_v1.g3_force_budget import (
    ForceInputError,assemble_explicit_g3_loads,source_force_requirements,
    SYNTHETIC_GPE_OWNER)
from experiments.plate58_deforming_explore_v1.spherical_exterior import (
    frames_and_cartesian,spherical_triangle_geometry)


def fixture():
    ids=[1,2,3,4]
    ll={1:(0.,0.),2:(0.,1.),3:(1.,1.),4:(1.,0.)}
    edges=[
        {"source_parent_node_ids":[1,2],"side":"south","adjacent_plate_id":5},
        {"source_parent_node_ids":[2,3],"side":"east","adjacent_plate_id":5},
        {"source_parent_node_ids":[3,4],"side":"north","adjacent_plate_id":8},
        {"source_parent_node_ids":[4,1],"side":"west","adjacent_plate_id":8},
    ]
    xyz,unit,e,n=frames_and_cartesian([ll[i] for i in ids])
    refs={k:i for i,k in enumerate(ids)}
    traction={}
    for row in edges:
        nodes=row["source_parent_node_ids"]
        key=":".join(map(str,sorted(nodes)))
        t=[(0.001*e[refs[n]]).tolist() if key=="1:2"
           else [0.,0.,0.] for n in nodes]
        traction[key]={
            "authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
            "source_reference":"SYNTHETIC_EXPLICIT_LINE_LOAD_ONLY",
            "source_parent_node_ids":nodes,"side":row["side"],
            "adjacent_plate_id":row["adjacent_plate_id"],
            "force_channel":"EXTERIOR_BOUNDARY",
            "nodal_xyz_N_per_m":t}
    faces={101:(1,2,3),102:(1,3,4)}
    basal={}
    for tid,tri in faces.items():
        basal[tid]={
            "authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
            "source_reference":"SYNTHETIC_EXPLICIT_ZERO_BASAL_NOT_GEOPHYSICS",
            "force_channel":"BASAL_TANGENTIAL",
            "parent_triangle_id":tid,"parent_node_ids":list(tri),
            "nodal_xyz_N_per_m2":[[0.,0.,0.]]*3}
    return ids,ll,edges,traction,faces,basal


def assemble(args,**kwargs):
    return assemble_explicit_g3_loads(*args,gpe_ownership=SYNTHETIC_GPE_OWNER,
                                     **kwargs)


def test_one_line_edge_exact_consistent_nodal_virtual_forces():
    args=fixture()
    r=assemble(args)
    assert r["external_cut_edges_count"]==4
    assert r["basal_triangles_count"]==2
    xyz,unit,e,n=frames_and_cartesian([args[1][i] for i in args[0]])
    chord=np.linalg.norm(xyz[1]-xyz[0])
    f=r["candidate_external_line_force_N"].reshape(4,2)
    assert f[0,0]==pytest.approx(0.001*chord,rel=1e-4)
    assert f[1,0]==pytest.approx(0.001*chord,rel=1e-4)
    assert np.allclose(f[2:],0)
    assert np.allclose(r["candidate_basal_tangential_force_N"],0)
    assert r["physical_traction_laws_source_qualified"] is False
    assert r["mechanical_solve_authorized"] is False


def test_rigid_rotation_virtual_power_equals_nodal_torque_work():
    args=fixture()
    ids,ll,edges,traction,faces,basal=args
    xyz,unit,e,n=frames_and_cartesian([ll[i] for i in ids])
    omega=np.array([2e-15,-1e-15,1e-15])
    v=np.cross(omega,xyz)
    vel={node:(float(v[i]@e[i]),float(v[i]@n[i]))
         for i,node in enumerate(ids)}
    result=assemble(args,velocity_en_by_node=vel)
    power=result["virtual_power_W_if_velocity_supplied"]
    assert power==pytest.approx(float(omega@result["global_torque_xyz_N_m"]),
                               rel=1e-12,abs=1e-12)


def test_explicit_area_basal_traction_positive_load_without_implict_gpe():
    args=list(fixture())
    ids,ll,edges,traction,faces,basal=args
    xyz,unit,e,n=frames_and_cartesian([ll[i] for i in ids])
    for tid,tri in faces.items():
        basal[tid]["nodal_xyz_N_per_m2"]=[
            (1e-7*e[ids.index(node)]).tolist() for node in tri]
    result=assemble(args)
    assert result["facet_basal_area_m2"]>0
    assert result["candidate_basal_tangential_force_N"].size==8
    assert np.linalg.norm(result["candidate_basal_tangential_force_N"])>0
    assert result["gpe_accounting"]=="NOT_MODELED_IN_SYNTHETIC_KERNEL"
    assert result["resultant_or_torque_balanced"] is False


def test_basal_triangle_missing_cannot_default_to_zero():
    args=list(fixture());args[5].pop(102)
    with pytest.raises(ForceInputError,match="ALL_BASAL"):
        assemble(args)


def test_external_cut_missing_cannot_default_to_zero():
    args=list(fixture());args[3].pop("1:2")
    with pytest.raises(ForceInputError,match="ALL_EXTERNAL"):
        assemble(args)


def test_out_of_plane_normal_as_basal_shear_rejected():
    args=list(fixture())
    ids,ll,edges,traction,faces,basal=args
    xyz,unit,e,n=frames_and_cartesian([ll[i] for i in ids])
    basal[101]["nodal_xyz_N_per_m2"]=[(1e-7*unit[ids.index(x)]).tolist()
                                     for x in faces[101]]
    with pytest.raises(ForceInputError,match="NON_TANGENTIAL"):
        assemble(args)


def test_wrong_source_plate_owner_rejected():
    args=list(fixture())
    args[3]["1:2"]["adjacent_plate_id"]=11
    with pytest.raises(ForceInputError,match="OWNER_OR_ORIENTATION"):
        assemble(args)


def test_gpe_accounting_absence_rejected():
    args=fixture()
    with pytest.raises(ForceInputError,match="GPE_OWNERSHIP"):
        assemble_explicit_g3_loads(*args,gpe_ownership=None)


def test_nodal_triple_junction_has_single_resultant_two_dof():
    ids=[34587,34588,34589]
    ll={34587:(0.,0.),34588:(0.,1.),34589:(1.,0.)}
    edges=[
        {"source_parent_node_ids":[34587,34588],"side":"north","adjacent_plate_id":5},
        {"source_parent_node_ids":[34587,34589],"side":"west","adjacent_plate_id":11},
    ]
    xyz,unit,e,n=frames_and_cartesian([ll[i] for i in ids])
    traction={}
    for row in edges:
        key=":".join(map(str,sorted(row["source_parent_node_ids"])))
        traction[key]={
            "authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
            "source_reference":"SYNTHETIC_TRIPLE_JUNCTION_FORCE",
            "source_parent_node_ids":row["source_parent_node_ids"],
            "side":row["side"],"adjacent_plate_id":row["adjacent_plate_id"],
            "force_channel":"EXTERIOR_BOUNDARY",
            "nodal_xyz_N_per_m":[(1e-4*e[ids.index(v)]).tolist()
                for v in row["source_parent_node_ids"]]}
    tri={123:(34587,34588,34589)}
    basal={123:{"authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
        "source_reference":"SYNTHETIC_ZERO_BASAL_TRIPLE",
        "parent_triangle_id":123,"parent_node_ids":list(tri[123]),
        "force_channel":"BASAL_TANGENTIAL",
        "nodal_xyz_N_per_m2":[[0.,0.,0.]]*3}}
    r=assemble_explicit_g3_loads(ids,ll,edges,traction,tri,basal,
                                 gpe_ownership=SYNTHETIC_GPE_OWNER)
    assert r["candidate_total_nodal_force_N"].shape==(6,)
    assert r["source_node_order"]==ids
    assert np.linalg.norm(r["candidate_total_nodal_force_N"][:2])>0
