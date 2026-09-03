from pathlib import Path
P=Path("tools/r4_39_r1_dynamic_representability_failure_diagnostic.py")

def test_compiles():
    compile(P.read_text(encoding="utf-8"),str(P),"exec")

def test_read_only_r439_and_writes_only_r1():
    s=P.read_text(encoding="utf-8")
    assert 'outputs/v0_6D1_R4_39"' in s
    assert 'outputs/v0_6D1_R4_39_R1' in s
    assert "r439_outputs_modified" in s
    assert "False" in s

def test_no_geonomics_or_model_execution():
    s=P.read_text(encoding="utf-8")
    assert "import geonomics" not in s
    assert "make_model" not in s
    assert ".run(" not in s
    assert ".walk(" not in s
    assert "_make_change(" not in s

def test_captures_dynamic_range_failures():
    s=P.read_text(encoding="utf-8")
    for token in ["bad_state_count","bad_field_count","bad_age_ka","global_min_across_bad_states","global_max_across_bad_states"]:
        assert token in s
