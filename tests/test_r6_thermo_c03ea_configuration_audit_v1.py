from fractions import Fraction
import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03ea_configuration_audit as a


def test_exact_fraction_equation():
    assert a.terms("1 gl - 2 jd +2 acm")==[("gl",Fraction(1)),("jd",Fraction(-2)),("acm",Fraction(2))]
    assert a.terms("3/7 cumm + 4/7 grun")[0][1]==Fraction(3,7)


def test_unparsed_tail_rejected():
    with pytest.raises(ValueError,match="UNPARSED_EQUATION"):
        a.terms("1 gl - nonsense")


def test_missing_sign_rejected():
    with pytest.raises(ValueError,match="MISSING_SIGN"):
        a.terms("1 gl 2 jd")


def test_resolve_signed_composition():
    direct={"gl":{"coefficients":{"O2":"0","H2O":"1","AL2O3":"1"}},
            "jd":{"coefficients":{"AL2O3":"0.5"}},
            "acm":{"coefficients":{"O2":"0.25"}}}
    roots=set()
    used=set()
    v=a.resolve("mrb_q",direct,{},{"mrb_q":"1 gl - 2 jd +2 acm"},roots,used)
    assert v=={"H2O":Fraction(1),"O2":Fraction(1,2)}
    assert roots==set(direct) and used=={"mrb_q"}


def test_missing_dependency_rejected():
    with pytest.raises(ValueError,match="MISSING_DIRECT_EOS"):
        a.resolve("unknown",{}, {},{},set(),set())


def test_cycle_rejected():
    with pytest.raises(ValueError,match="DEPENDENCY_CYCLE"):
        a.resolve("a",{},{"a":"1 b","b":"1 a"},{},set(),set())


def test_duplicate_equation_rejected():
    with pytest.raises(ValueError,match="DUPLICATE_EQUATION"):
        a.equations("a = 1 b\na = 1 c")


def test_ordered_energy_not_composition():
    assert a.equations("cammo1 = 3/7 cumm + 4/7 grun   delta_g_of_ordering  = -9.5d3\nDQF = 0\nDQF = 1")=={"cammo1":"3/7 cumm + 4/7 grun"}
