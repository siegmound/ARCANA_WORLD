import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03c_morb_roster_audit as c


def test_recursive_dependency_closure():
    z=c.resolve("x",{"a"},{"y":"a"},{"x":"y"})
    assert z=={"status":"DEFINED_DEPENDENCY","missing":[]}


def test_missing_dependency_retained():
    z=c.resolve("x",{"a"},{"y":"a b"},{"x":"y"})
    assert z["missing"]==["b"]


def test_cycle_rejected():
    with pytest.raises(ValueError,match="C03C_DEPENDENCY_CYCLE"):
        c.resolve("a",set(),{"a":"b","b":"a"},{})


def test_comments_not_equations():
    rows=c.equation_rows(" | fake = 1 a\nx = 1 a - 1 b | note\n")
    assert set(rows)=={"x"}
    c.check_equation(rows,"x","a b")
    with pytest.raises(ValueError,match="C03C_DEPENDENCY_EQUATION_DRIFT"):
        c.check_equation(rows,"x","c")


def test_native_pure_record_distinct_names():
    raw=b"mt EoS = 2\nFEO(3)O2(.5)\nmag EoS = 2\nMGO(1)CO2(1)\n"
    assert c.pure_record(raw,"mt")["composition"]=="FEO(3)O2(.5)"
    assert c.pure_record(raw,"mag")["composition"]=="MGO(1)CO2(1)"


def test_reference_is_not_executable():
    z=c.benchmark_candidate()
    assert z["benchmark_executable"] is False
    assert z["O2_exact_MORB_input"] is None
    assert z["source_pdf_raw_sha256"] is None
    assert z["water_boundary"]=="WATER_SATURATED_FIGURE_1A_NOT_ARCANA_CLOSED_BULK"
