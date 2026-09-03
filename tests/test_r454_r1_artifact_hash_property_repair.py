from pathlib import Path
import hashlib

PRE_SHA = "46251558cc7d373aff56707dc783b4cacc32b2fcbcf8a6a735ee998b88fe1067"
POST_SHA = "9f8e09c2122b41cab224412b478adfd1e1e816122a2b2652a3c8668246feeaf8"


def test_authorized_hashes_are_distinct():
    assert PRE_SHA != POST_SHA
    assert len(PRE_SHA) == 64
    assert len(POST_SHA) == 64


def test_patched_bridge_materializes_property_with_add_member():
    s = Path("capture_v0_6D1_R4_54_dry_runs.ps1").read_text(encoding="utf-8")
    assert "function Set-ArtifactHashes" in s
    assert "Add-Member -NotePropertyName artifact_hashes" in s


def test_no_direct_artifact_hash_assignment_remains():
    s = Path("capture_v0_6D1_R4_54_dry_runs.ps1").read_text(encoding="utf-8")
    assert "$r.artifact_hashes=" not in s


def test_madingley_uses_helper():
    s = Path("capture_v0_6D1_R4_54_dry_runs.ps1").read_text(encoding="utf-8")
    assert '$r=Set-ArtifactHashes $r ([ordered]@{"dry_run_result_json"=' in s


def test_nemo_empty_hash_case_uses_helper():
    s = Path("capture_v0_6D1_R4_54_dry_runs.ps1").read_text(encoding="utf-8")
    assert "$r=Set-ArtifactHashes $r ([ordered]@{})" in s


def test_capture_bridge_hash_is_exact_postpatch():
    p = Path("capture_v0_6D1_R4_54_dry_runs.ps1")
    assert hashlib.sha256(p.read_bytes()).hexdigest() == POST_SHA
