"""No physics values are inferred; only source-keyed accounting identities."""
import numpy as np
import pytest
from experiments.plate58_deforming_explore_v1.g3_gpe_force_accounting import (
    compose_candidate_nodal_loads, G3AccountingError, GPE_OWNER, NO_INTERNAL_GPE,
)


def fixture():
    ids=[100,101,102,103]
    f={"source_node_order": ids,
       "candidate_external_line_force_N": [1,2, 2,1, -1,0, 0,1],
       "candidate_basal_tangential_force_N": [1,0, 0,1, 1,-1, 0,0],
       "candidate_total_nodal_force_N": [2,2, 2,2, 0,-1, 0,1],
       "gpe_accounting":NO_INTERNAL_GPE,
       "physical_traction_laws_source_qualified":False,
       "mechanical_solve_authorized":False,"physical_T1":None}
    g={"source_interface_node_order":ids,
       "candidate_GPE_force_vector_N": [0,1, 2,0, 0,-2, 1,0],
       "GPE_force_owner":GPE_OWNER,
       "mechanical_solve_authorized":False,"physical_T1":None}
    coords={100:(0.,0.),101:(0.,1.),102:(1.,1.),103:(1.,0.)}
    return f,g,coords


def check(f=None,g=None,coords=None,vel=None):
    a,b,c=fixture()
    return compose_candidate_nodal_loads(f or a,g or b,
                 node_lat_lon_deg=coords or c,numerical_radius_m=6371000,
                 velocity_en_by_node=vel)


def test_partition_exact_and_source_order_preserved():
    r=check()
    assert r["source_node_order"]==[100,101,102,103]
    assert np.array_equal(np.asarray(r["candidate_total_nodal_force_N"]),
                          [2,3,4,2,0,-3,1,1])
    assert r["physical_model_complete"] is False
    assert r["mechanical_solve_authorized"] is False
    assert r["physical_T1"] is None


def test_velocity_virtual_work_partition_and_rigid_rotation_torque():
    omega=np.array([0.,0.,2e-15]);rad=6371000.
    vel={}
    for node,(lat,lon) in fixture()[2].items():
        a,b=np.deg2rad([lat,lon]);xyz=rad*np.array([np.cos(a)*np.cos(b),
                   np.cos(a)*np.sin(b),np.sin(a)])
        en=np.array([-np.sin(b),np.cos(b),0])
        nn=np.array([-np.sin(a)*np.cos(b),-np.sin(a)*np.sin(b),np.cos(a)])
        v=np.cross(omega,xyz)
        vel[node]=[float(v@en),float(v@nn)]
    r=check(vel=vel)
    p=r["virtual_power_W_by_channel"]
    assert p["total"]==pytest.approx(sum(p[k] for k in (
        "outer_cut","basal_tangential","gpe_external")))
    assert p["total"]==pytest.approx(float(omega@np.asarray(
        r["torque_xyz_N_m_by_channel"]["total"])),rel=1e-12)


def test_permutation_mismatch_cannot_silently_corrupt_gpe_dofs():
    f,g,c=fixture();g["source_interface_node_order"]=[101,100,102,103]
    with pytest.raises(G3AccountingError,match="DOF_ORDER_MISMATCH"):
        check(f=f,g=g)


def test_internal_gpe_double_count_rejected():
    f,g,c=fixture();f["gpe_accounting"]="GPE_ALREADY_INCLUDED"
    with pytest.raises(G3AccountingError,match="DOUBLE_COUNT"):
        check(f=f)


def test_unauthorized_physical_promotion_rejected():
    f,g,c=fixture();g["mechanical_solve_authorized"]=True
    with pytest.raises(G3AccountingError,match="PHYSICAL_PROMOTION"):
        check(g=g)


def test_hidden_additional_force_channel_rejected():
    f,g,c=fixture();f["candidate_total_nodal_force_N"][0]+=1
    with pytest.raises(G3AccountingError,match="HIDDEN_CHANNEL"):
        check(f=f)


def test_missing_gpe_nodal_force_rejected():
    f,g,c=fixture();del g["candidate_GPE_force_vector_N"]
    with pytest.raises(G3AccountingError,match="FORCE_CHANNEL_MISSING"):
        check(g=g)


def test_missing_source_coordinates_rejected():
    f,g,c=fixture();c.pop(103)
    with pytest.raises(G3AccountingError,match="COORDINATES_MISMATCH"):
        check(coords=c)
