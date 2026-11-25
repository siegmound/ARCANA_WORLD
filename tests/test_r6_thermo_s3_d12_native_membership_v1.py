import hashlib
import numpy as np
import pytest
from experiments.r6_thermo_provider_pilot_v1.s3_d12_native_membership import adjacent, classify, encoded, verified_membership


def test_periodic_east():
    assert adjacent({"row":1,"column":2,"axis":"EAST"},(2,3))==((1,2),(1,0))


def test_north():
    assert adjacent({"row":0,"column":1,"axis":"NORTH"},(2,3))==((0,1),(1,1))


def fixture():
    dom=np.array([[1,1,1],[2,3,4]])
    f={"physical_crust_domain_id":dom,
       "continental_thermal_domain_id":np.array([[0,0,0],[1,2,3]]),
       "oceanic_lithosphere_age_ma":np.array([[0.,2.,3.],[np.nan,np.nan,np.nan]])}
    for k in ("crustal_thickness_m","continental_reference_lithosphere_thickness_m","continental_reference_surface_heat_flow_w_m2"):
        f[k]=np.ones(dom.shape)
    s=[{"boundary_id":"a","parent_grid_edge":{"row":0,"column":0,"axis":"EAST"},"relative_normal_velocity_m_per_year":1.}]
    return f,s


def test_exclusion_and_ridge_are_disjoint():
    f,s=fixture()
    masks,a=classify(f,s,set())
    assert masks["ZERO_AGE_RIDGE"].sum()==1
    assert masks["UNRESOLVED_POSITIVE_AGE_OCEAN"].sum()==1
    assert masks["ADMITTED_INITIALIZER_SUPPORT"].sum()==4
    assert a=={"unselected_positive_normal_ocean_ocean_segments":1,"unique_adjacent_ocean_cells":2,"overlap_selected_ridge":1}


def test_selected_boundary_not_excluded():
    f,s=fixture()
    masks,_=classify(f,s,{"a"})
    assert masks["ADMITTED_INITIALIZER_SUPPORT"].sum()==5


def test_exact_encoding():
    assert encoded(np.array([[False,True],[True,False]]))==b"R6G1D-R000-C001\nR6G1D-R001-C000\n"


def test_digest_mismatch_fails():
    f,s=fixture()
    masks,_=classify(f,s,set())
    idx={"membership_sha256":{k:hashlib.sha256(encoded(v)).hexdigest() for k,v in masks.items()},
         "support_classes":[{"class":k,"count":int(v.sum())} for k,v in masks.items() if k!="ADMITTED_INITIALIZER_SUPPORT"],
         "partition_counts":{"admitted":4}}
    assert len(verified_membership(masks,idx))==7
    idx["membership_sha256"]["ZERO_AGE_RIDGE"]="0"*64
    with pytest.raises(ValueError,match="D12_MEMBERSHIP_DRIFT"):
        verified_membership(masks,idx)
