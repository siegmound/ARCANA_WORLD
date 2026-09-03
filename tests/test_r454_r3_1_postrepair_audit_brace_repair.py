from pathlib import Path
import hashlib

POST_SHA = "1b359cc4616e7960a9b4d240eb12d00a05f4947af6f267cfc8f03a35673915a7"

def test_postrepair_audit_hash_exact():
    p=Path("scripts/audit_v0_6D1_R4_54_R3_postrepair.py")
    assert hashlib.sha256(p.read_bytes()).hexdigest()==POST_SHA

def test_out_is_dict_not_set_literal():
    s=Path("scripts/audit_v0_6D1_R4_54_R3_postrepair.py").read_text()
    assert "out={{" not in s
    assert "out={" in s

def test_closing_double_brace_removed():
    s=Path("scripts/audit_v0_6D1_R4_54_R3_postrepair.py").read_text()
    assert "\n}}\np=root/" not in s
    assert "\n}\np=root/" in s

def test_audit_still_targets_r455():
    s=Path("scripts/audit_v0_6D1_R4_54_R3_postrepair.py").read_text()
    assert "BUILD_R455_NON_GEONOMICS_80_STREAM_SCIENTIFIC_EXECUTION_AND_EVIDENCE_CAPTURE" in s
