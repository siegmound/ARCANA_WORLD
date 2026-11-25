import pytest
from experiments.r6_thermo_provider_pilot_v1.s3_d11_t0_pt_material_design import clipped_joint


def test_pressure_disjoint():
    assert clipped_joint(0,100,(300,500,0,0),(120,150,400,500)) is None


def test_hidden_joint_between_samples():
    x=clipped_joint(0,100,(300,1000,0,0),(40,42,700,720))
    assert x["joint_overlap"] and x["T_bounds_K"]==pytest.approx([700,720])


def test_independent_axis_overlap_not_joint():
    x=clipped_joint(0,100,(300,1000,0,0),(10,20,800,900))
    assert not x["joint_overlap"]


def test_interior_nonmonotonic_extremum():
    x=clipped_joint(0,100,(300,400,-400,0),(0,100,399,401))
    assert x["joint_overlap"] and x["T_bounds_K"]==pytest.approx([300,400])


def test_closed_boundary_contact():
    x=clipped_joint(0,100,(300,500,0,0),(100,120,800,810))
    assert x["joint_overlap"] and x["fraction_interval"]==[1.,1.]


def test_constant_temperature():
    x=clipped_joint(0,100,(500,0,0,0),(20,30,490,510))
    assert x["joint_overlap"] and x["T_bounds_K"]==[500,500]


@pytest.mark.parametrize("p0,p1",[(1,1),(-1,100),(0,float("nan"))])
def test_invalid_pressure(p0,p1):
    with pytest.raises(ValueError):
        clipped_joint(p0,p1,(300,500,0,0),(0,100,300,800))
