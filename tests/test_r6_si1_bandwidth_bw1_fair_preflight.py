from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "r6_si1_bandwidth_bw1_fair_preflight.py"
SPEC = importlib.util.spec_from_file_location("bw1_fair_preflight", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


def _source() -> str:
    return """PROGRAM probe
       INTEGER nRank, nKRows, nCodiagonals
       CALL KSize (brief, iUnitP, iUnitLog, mxEl, mxFEl, mxNode, & ! input
     &             nFl, nodeF, nodes, numEl, numNod, &
     &             nDOF, nLB, nUB, &
     &             jCol1, jCol2)                                 ! work
       ALLOCATE ( stiff(nKRows, nRank) )
       END PROGRAM probe
"""


def _log(*, marker: str = preflight.PREFLIGHT_MARKER, bytes_text: str = "2249799104") -> str:
    return (
        " SI1_KSIZE  nRank=128884  nKRows=2182  nCodiagonals=727  matrix_bytes= "
        + bytes_text
        + "\n"
        + marker
        + "\n"
    )


def test_instrumentation_is_after_unique_ksize_and_before_stiffness_allocation() -> None:
    original = _source()
    transformed, proof = preflight.instrument_source_text(original)
    assert original == _source()
    assert transformed.index("CALL KSize") < transformed.index("SI1_KSIZE nRank=")
    assert transformed.index("FLUSH(6)") < transformed.index("ERROR STOP 73")
    assert transformed.index("ERROR STOP 73") < transformed.index("ALLOCATE ( stiff")
    assert proof["unconditional_error_stop_count"] == 1
    assert proof["environment_or_cli_guard_used"] is False
    assert "--solve" not in preflight.build_parser().format_help()


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("PROGRAM p\nEND PROGRAM p\n", "exactly one KSize"),
        (_source().replace("CALL KSize", "CALL KSize", 1).replace("       ALLOCATE", "       CALL KSize (brief, iUnitP, iUnitLog, mxEl, mxFEl, mxNode, & ! input\n     &             nFl, nodeF, nodes, numEl, numNod, &\n     &             nDOF, nLB, nUB, &\n     &             jCol1, jCol2) ! work\n       ALLOCATE"), "exactly one KSize"),
        (_source().replace("       ALLOCATE ( stiff(nKRows, nRank) )\n", ""), "stiffness allocation"),
    ],
)
def test_bad_source_anchors_fail_closed(source: str, message: str) -> None:
    with pytest.raises(preflight.BW1PreflightError, match=message):
        preflight.instrument_source_text(source)


def test_instrumentation_guard_rejects_missing_or_conditional_stop() -> None:
    transformed, _ = preflight.instrument_source_text(_source())
    with pytest.raises(preflight.BW1PreflightError, match="marker, FLUSH, or unconditional"):
        preflight.inspect_instrumentation(transformed.replace("ERROR STOP 73\n", ""))
    conditional = transformed.replace("       ERROR STOP 73", "       IF (nRank .GT. 0) ERROR STOP 73")
    with pytest.raises(preflight.BW1PreflightError):
        preflight.inspect_instrumentation(conditional)


def test_ksize_parser_accepts_fortran_exponent_and_rejects_bad_diagnostics() -> None:
    text = _log(bytes_text="2.249799104D+09")
    result = preflight.validate_preflight_log(text)
    assert result["ksize"] == preflight.EXPECTED_KSIZE
    for invalid in (
        "nRank=128884 nKRows=2182 nCodiagonals=727 matrix_bytes=2249799104\n" + preflight.PREFLIGHT_MARKER,
        _log().replace("nCodiagonals=727", "nCodiagonals=728"),
        _log().replace(preflight.PREFLIGHT_MARKER, ""),
        "ERROR STOP 1\n" + _log(),
        _log() + "SHELLS MECHANICAL SOLVE\n",
    ):
        with pytest.raises(preflight.BW1PreflightError):
            preflight.validate_preflight_log(invalid)


def test_cli_has_no_solve_or_executable_override() -> None:
    parser = preflight.build_parser()
    options = {option for action in parser._actions for option in action.option_strings}
    assert "--solve" not in options
    assert "--executable" not in options
    with pytest.raises(SystemExit):
        parser.parse_args(["--output-dir", "new-evidence", "--solve"])


def test_input_verification_failure_occurs_before_any_tool_probe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(preflight.sys, "platform", "linux")
    monkeypatch.setattr(preflight, "validate_bw1_inputs", lambda *_: (_ for _ in ()).throw(preflight.BW1PreflightError("fixture tampering")))
    monkeypatch.setattr(preflight, "_probe_tool", lambda *_: pytest.fail("compiler/tool probe ran before input gate"))
    result = preflight.run_preflight(tmp_path / "shellset", tmp_path / "bw1", tmp_path / "partition.npz", tmp_path / "evidence")
    assert result["decision"] == "BLOCKED_BW1_FAIR_PREFLIGHT"
    assert "fixture tampering" in result["failure"]
    assert (tmp_path / "evidence" / "BW1_FAIR_PREFLIGHT_RESULT.json").is_file()
    assert (tmp_path / "evidence" / "BW1_FAIR_PREFLIGHT_ARTIFACT_MANIFEST.json").is_file()


def test_windows_invocation_is_reported_blocked_without_validation_or_tool_execution(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(preflight.sys, "platform", "win32")
    monkeypatch.setattr(preflight, "validate_bw1_inputs", lambda *_: pytest.fail("Windows must not enter Fair input/build path"))
    monkeypatch.setattr(preflight, "_probe_tool", lambda *_: pytest.fail("Windows must not probe Fair tools"))
    result = preflight.run_preflight(tmp_path / "shellset", tmp_path / "bw1", tmp_path / "partition.npz", tmp_path / "evidence")
    assert result["decision"] == "BLOCKED_BW1_FAIR_PREFLIGHT"
    assert "Linux-only" in result["failure"]
    assert (tmp_path / "evidence" / "BW1_FAIR_PREFLIGHT_RESULT.json").is_file()


def test_output_manifest_is_repeatable_and_hashes_artifacts(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "result.json").write_text(json.dumps({"decision": "BLOCKED"}, sort_keys=True), encoding="utf-8")
    (evidence / "nested.log").write_text("fixture log\n", encoding="utf-8")
    preflight._seal_preflight_manifest(evidence)
    manifest_path = evidence / "BW1_FAIR_PREFLIGHT_ARTIFACT_MANIFEST.json"
    first = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    first_doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    preflight._seal_preflight_manifest(evidence)
    second = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    assert first == second
    assert {entry["path"] for entry in first_doc["artifacts"]} == {"nested.log", "result.json"}


def test_artifact_hash_gate_rejects_missing_and_modified_inputs(tmp_path: Path) -> None:
    source = tmp_path / "derived.feg"
    source.write_bytes(b"governed test fixture\n")
    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    assert preflight._require_sha256(source, expected, "fixture") == expected
    source.write_bytes(b"tampered fixture\n")
    with pytest.raises(preflight.BW1PreflightError, match="SHA256 mismatch"):
        preflight._require_sha256(source, expected, "fixture")
    with pytest.raises(preflight.BW1PreflightError, match="is missing"):
        preflight._require_sha256(tmp_path / "missing.dat", expected, "fixture")
