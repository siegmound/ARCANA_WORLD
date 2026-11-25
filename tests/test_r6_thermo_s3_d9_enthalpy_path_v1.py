from decimal import Decimal as D
import pytest
from experiments.r6_thermo_provider_pilot_v1.s3_d9_enthalpy_path import specific_h, secant


def sys(g="-1000", s="2", m="1000"):
    return {k:{"native_token":v} for k,v in zip(("g_J","s_J_K","mass_g"),(g,s,m))}


def test_specific_enthalpy_total_units():
    h,lo,hi=specific_h(sys(),1000)
    assert h==D(1000) and lo<h<hi


def test_negative_g_and_enthalpy_valid():
    h,lo,hi=specific_h(sys("-3000"),1000)
    assert h==D(-1000) and lo<h<hi


@pytest.mark.parametrize("mass",["0","-1","NaN"])
def test_bad_mass(mass):
    with pytest.raises(ValueError):
        specific_h(sys(m=mass),1000)


def test_secant_bounds():
    assert secant((D(100),D(99),D(101)),(D(200),D(198),D(202)),1000,1050)==(D(2),D("1.94"),D("2.06"))


def test_bad_temperature_order():
    with pytest.raises(ValueError):
        secant((D(1),)*3,(D(2),)*3,1050,1050)
