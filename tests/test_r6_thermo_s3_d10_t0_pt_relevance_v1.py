import pytest
from experiments.r6_thermo_provider_pilot_v1.s3_d10_t0_pt_relevance import classify, BOXES


def test_bar_conversion_inclusive():
    assert classify(300_000_000,1000,BOXES["PERPLEX_D7_BOUNDING_RECTANGLE_NOT_COVERAGE"])==(True,True)


def test_axes_independent():
    box=BOXES["PERPLEX_D7_BOUNDING_RECTANGLE_NOT_COVERAGE"]
    assert classify(0,1050,box)==(False,True)
    assert classify(400_000_000,900,box)==(True,False)


def test_magemin_celsius_to_kelvin():
    box=BOXES["MAGEMIN_S3_DESIGN_RECTANGLE_NOT_COVERAGE"]
    assert classify(800_000_000,1273.15,box)==(True,True)
    assert classify(800_000_000,1000,box)==(True,False)


@pytest.mark.parametrize("p,t",[(-1,1000),(1,0),(float("nan"),1000),(1,float("inf"))])
def test_invalid(p,t):
    with pytest.raises(ValueError):
        classify(p,t,BOXES["PERPLEX_D7_BOUNDING_RECTANGLE_NOT_COVERAGE"])
