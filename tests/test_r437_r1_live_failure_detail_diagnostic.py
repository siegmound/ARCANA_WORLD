from pathlib import Path
P=Path("tools/r4_37_r1_live_failure_detail_diagnostic.py")

def test_script_compiles():
    compile(P.read_text(encoding="utf-8"),str(P),"exec")

def test_diagnostic_is_read_only_on_r437():
    s=P.read_text(encoding="utf-8")
    assert 'outputs/v0_6D1_R4_37_R1' in s
    assert 'R4_37_J21_CANONICAL_NATIVE_LAYER_BINDING_AUDIT.json' in s
    assert 'R4_37_J14_EXACT_STATE_PUBLIC_API_DRY_RUN_AUDIT.json' in s
    assert 'R4_37_J18_EXACT_STATE_PUBLIC_API_DRY_RUN_AUDIT.json' in s
    assert "payload_values_modified" in s
    assert "canonical_state_changed" in s

def test_no_geonomics_import_or_execution():
    s=P.read_text(encoding="utf-8")
    assert "import geonomics" not in s
    assert "make_model" not in s
    assert ".run(" not in s
    assert ".walk(" not in s
    assert "run_default_model" not in s

def test_captures_j21_ranges_and_native_failures():
    s=P.read_text(encoding="utf-8")
    for token in ["min","max","range_0_1","error","failed_branch_count"]:
        assert token in s
