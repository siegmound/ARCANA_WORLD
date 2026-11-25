import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c02_consolidation as a


def test_campaign_member_set():
    assert len(a.expected_members()) == 50
    assert "C02_UCC_BASE_01/NATIVE.toml" in a.expected_members()
    assert "C02_MCC_WET_02/AUDIT.json" in a.expected_members()


@pytest.mark.parametrize("case,family",[
    ("M01_BASE","MANTLE"),("M02_P_PLUS","MANTLE"),("M03_G_P_01","MANTLE"),
    ("C01_LCC_BASE","LCC"),("C01_MORB_WET","MORB"),
    ("C02_UCC_BASE","UCC"),("C02_MCC_WET","MCC")])
def test_family(case,family):
    assert a.family(case)==family


def test_unknown_family_rejected():
    with pytest.raises(ValueError,match="C02_UNKNOWN_FAMILY"):
        a.family("UNSUPPORTED")


def test_coordinate_exact_and_zero_pressure():
    assert a.coordinate(0,6.85)==(float(0).hex(),float(6.85).hex())
    assert a.coordinate(7.69888,778.4081968311126)!=a.coordinate(7.69888,778.4081968311127)
    with pytest.raises(ValueError,match="C02_COVERAGE_PT"):
        a.coordinate(-1,300)


def test_coverage_rejects_empty_library():
    with pytest.raises(ValueError,match="C02_COVERAGE_FAMILIES"):
        a.coverage({"states":{}},[])
