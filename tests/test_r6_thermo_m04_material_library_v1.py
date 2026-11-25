from pathlib import Path
from copy import deepcopy
import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_m04_material_library as lib

ROOT=Path(__file__).resolve().parents[1]


def test_chemistry_identity_independent_of_pt():
    cases=lib.m.build_inputs(ROOT)
    a=cases["M01_BASE"];b=deepcopy(a);b["T_C"]+=1
    assert lib.chemistry_id(a)==lib.chemistry_id(b)
    assert len({lib.chemistry_id(v) for v in cases.values()})==4


def test_key_exact_no_rounding():
    x="a"*64
    assert lib.state_key(x,16.,1000.)!=lib.state_key(x,16.,1000.000001)
    assert lib.state_key(x,16.,1000.)!=lib.state_key("b"*64,16.,1000.)


def test_exact_lookup_copy_and_no_interpolation():
    x="a"*64
    key=lib.state_key(x,16.,1000.)
    data={"states":{key:{"case":"synthetic","rho":3300}}}
    result=lib.exact_lookup(data,x,16.,1000.)
    assert result["status"]=="EXACT_RESEARCH_SAMPLE"
    result["state"]["rho"]=0
    assert data["states"][key]["rho"]==3300
    assert lib.exact_lookup(data,x,16.,1000.1)=={"status":"UNKNOWN_UNSAMPLED_PT_X","state":None,"interpolated":False}
    assert lib.exact_lookup(data,"b"*64,16.,1000.)["state"] is None


@pytest.mark.parametrize("x,p,t",[("a",16.,1000.),("g"*64,16.,1000.),("a"*64,0.,1000.),
    ("a"*64,16.,float("nan")),("a"*64,16.,-273.15)])
def test_invalid_queries(x,p,t):
    with pytest.raises(ValueError,match="M04_INVALID_QUERY"):
        lib.state_key(x,p,t)
