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


def test_legacy_non_utf8_preserves_block_bytes_and_lines():
    import hashlib
    block=b"T | old \x96 comment\r\nabbreviation Tlc\r\nend_of_model\r\n"
    raw=b"header \x91 text\r\n"+block+b"trailer\r\n"
    with pytest.raises(UnicodeDecodeError):
        raw.decode("utf-8")
    z=c.legacy_model_blocks(raw,("T","missing"))
    assert z["T"]["line"]==2 and z["T"]["end_line"]==4
    assert z["T"]["raw_block_sha256"]==hashlib.sha256(block).hexdigest()
    assert "\x96" in z["T"]["text"]
    assert z["T"]["text_encoding_policy"]=="LATIN1_REVERSIBLE_BYTE_PROJECTION"
    assert z["missing"] is None


def test_legacy_duplicate_header_rejected():
    raw=b"T\nabbreviation Tlc\nend_of_model\n"*2
    with pytest.raises(ValueError,match="C03C_LEGACY_AMBIGUOUS_MODEL"):
        c.legacy_model_blocks(raw,("T",))


def test_legacy_missing_end_rejected():
    with pytest.raises(ValueError,match="C03C_LEGACY_UNTERMINATED_MODEL"):
        c.legacy_model_blocks(b"T\nabbreviation Tlc\n",("T",))
