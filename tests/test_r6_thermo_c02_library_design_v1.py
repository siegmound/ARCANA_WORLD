import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c02_material_library_and_design as c

def test_model_is_part_of_state_identity():
    x="a"*64
    k=c.key(c.MB,x,5.,600.)
    assert k!=c.key(c.IG,x,5.,600.)
    lib={"states":{k:{"case":"synthetic"}}}
    assert c.lookup(lib,c.MB,x,5.,600.)["state"]["case"]=="synthetic"
    assert c.lookup(lib,c.IG,x,5.,600.)["state"] is None
    assert c.lookup(lib,c.MB,x,5.,600.001)["state"] is None
    with pytest.raises(ValueError,match="C02_UNKNOWN_MODEL"):
        c.key("unknown",x,5.,600.)

def sample(z,t,p,layer="crust"):
    return {"layer":layer,"source_depth_m":z,"source_PRE_temperature_k":t,
        "conditional_delta_vertical_overburden_pa":p*1e8}

def record(samples):
    return {"original_parent_node_order":[1],"original_T0_source_nodes":{"1":{
        "absolute_surface_pressure_pa":None,"source_depth_pt_samples":samples}}}

def test_hot_source_ranking_not_spatial_assignment():
    r=record([sample(50000,1098.,13.7),sample(30000,950.,8.),sample(10000,700.,3.),sample(20000,950.,8.,"mantle_lithosphere")])
    a=c.hot_candidates(r)
    assert len(a)==2 and a[0]["depth_m"]==30000
    assert a[0]["absolute_pressure_pa"] is None

def test_no_candidate_is_empty():
    assert c.hot_candidates(record([sample(10000,700.,3.)]))==[]

def test_pressure_authority_rejected():
    r=record([sample(30000,950.,8.)])
    r["original_T0_source_nodes"]["1"]["absolute_surface_pressure_pa"]=1.
    with pytest.raises(ValueError,match="C02_PRESSURE_AUTHORITY"):
        c.hot_candidates(r)
