from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "r6_si1_bandwidth_f1_fair_preflight.py"
SPEC = importlib.util.spec_from_file_location("bw1_f1_fair_preflight", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
f1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(f1)


def _source() -> str:
    return """SUBROUTINE FEM (f, k)
IMPLICIT NONE
REAL*8, INTENT(INOUT) :: f, k
INTEGER nRank, nKRows, nCodiagonals, iDiagonal
COMMON nRank, nCodiagonals, nKRows, iDiagonal
INTEGER i, j
REAL*8 bDenom, bDen, bDenoN, dVSize
CALL BuildF (f)
CALL BuildK (k)
CALL AddFSt (k)
CALL VBCs (f, k) ! modify
CALL Solver (k, f)
END SUBROUTINE FEM
"""


def _stage(**replace: str) -> str:
    values = {
        "nRank": "128884", "nKRows": "2182", "nCodiagonals": "727", "iDiagonal": "1455",
        "stiff_allocated": "1", "fem_entered": "1", "BuildF_done": "1", "BuildK_done": "1",
        "AddFSt_done": "1", "VBCs_done": "1",
    }
    values.update(replace)
    return "BW1_F1_STAGE " + " ".join(f"{key}={value}" for key, value in values.items()) + "\n"


def _matrix(**replace: str) -> str:
    values = {
        "rows": "2182", "cols": "128884", "bytes": str(8 * 2182 * 128884),
        "finite": str(2182 * 128884), "nonfinite": "0", "nonzero": "1000",
        "diagonal_row": "1455", "diag_zero": "100", "diag_nonzero": "128784", "max_abs": "1.25E+003",
    }
    values.update(replace)
    return "BW1_F1_MATRIX " + " ".join(f"{key}={value}" for key, value in values.items()) + "\n"


def _forcing(**replace: str) -> str:
    values = {"count": "128884", "finite": "128884", "nonfinite": "0", "nonzero": "0", "max_abs": "0.0E+000"}
    values.update(replace)
    return "BW1_F1_FORCING " + " ".join(f"{key}={value}" for key, value in values.items()) + "\n"


def _log(*, order: tuple[str, ...] = ("stage", "matrix", "forcing", "marker", "stop"),
         stage: str | None = None, matrix: str | None = None, forcing: str | None = None,
         marker: str | None = f1.MARKER, stop: str = "ERROR STOP 74\n", extra: str = "") -> str:
    rows = {
        "stage": _stage() if stage is None else stage,
        "matrix": _matrix() if matrix is None else matrix,
        "forcing": _forcing() if forcing is None else forcing,
        "marker": (marker + "\n") if marker else "",
        "stop": stop,
    }
    return extra + "".join(rows[key] for key in order)


def test_instrumentation_is_only_at_fem_vbcs_to_solver_boundary() -> None:
    transformed, proof = f1.instrument_source_text(_source())
    fem = transformed[transformed.index("SUBROUTINE FEM"):]
    assert "USE, INTRINSIC :: IEEE_ARITHMETIC, ONLY: IEEE_IS_FINITE" in fem
    assert fem.index("CALL BuildF") < fem.index("CALL BuildK") < fem.index("CALL AddFSt")
    assert fem.index("CALL AddFSt") < fem.index("CALL VBCs") < fem.index("BW1_F1_MATRIX")
    assert fem.index("BW1_F1_MATRIX") < fem.index("BW1_F1_STOP_BEFORE_SOLVER")
    assert fem.index("FLUSH(6)") < fem.index("ERROR STOP 74") < fem.index("CALL Solver")
    assert proof["normal_solver_reachable"] is False
    assert f1.inspect_instrumentation(transformed)["normal_solver_reachable"] is False


@pytest.mark.parametrize("source", [
    "SUBROUTINE FEM(f,k)\nEND SUBROUTINE FEM\n",
    _source().replace("CALL VBCs", "CALL VBCs", 1).replace("CALL Solver", "CALL Solver\nCALL VBCs", 1),
    _source().replace("CALL BuildK", "CALL BuildK\nCALL BuildK", 1),
    _source().replace("REAL*8 bDenom, bDen, bDenoN, dVSize", "REAL*8 other"),
])
def test_missing_duplicate_or_altered_fem_anchors_fail_closed(source: str) -> None:
    with pytest.raises(f1.F1Error):
        f1.instrument_source_text(source)


def test_instrumentation_is_not_repeatable_or_conditionally_bypassable() -> None:
    transformed, _ = f1.instrument_source_text(_source())
    with pytest.raises(f1.F1Error, match="already present"):
        f1.instrument_source_text(transformed)
    with pytest.raises(f1.F1Error):
        f1.inspect_instrumentation(transformed.replace("ERROR STOP 74", "IF (nRank > 0) ERROR STOP 74"))
    with pytest.raises(f1.F1Error):
        f1.inspect_instrumentation(transformed.replace("FLUSH(6)", ""))


def test_fair_parser_accepts_reordered_combined_stream_and_zero_forcing() -> None:
    log = _log(order=("stop", "forcing", "matrix", "stage", "marker"),
               extra="Warning: ieee_underflow is signaling\nWarning: ieee_inexact is signaling\n")
    result = f1.validate_f1_log(log, mpi_exit_code=74)
    assert result["solver_entered"] is False
    assert result["system"]["forcing"]["all_zero"] is True
    assert result["ieee_warning_counts"] == {"ieee_underflow": 1, "ieee_inexact": 1}


@pytest.mark.parametrize("code", [0, 1, 73, 75])
def test_exit_code_must_be_exactly_74(code: int) -> None:
    with pytest.raises(f1.F1Error, match="exit code"):
        f1.validate_f1_log(_log(), mpi_exit_code=code)


@pytest.mark.parametrize("log", [
    _log(marker=None),
    _log(matrix=""),
    _log(forcing=""),
    _log(stop="ERROR STOP 73\n"),
    _log(extra="DGESV was called\n"),
    _log(extra="CONVERGED !!!\n"),
    _log(extra="NVFORTRAN-S-0038-Symbol not declared\n"),
    _log(extra="MPI_ABORT was invoked\n"),
    _log(stop="ERROR STOP 74\nERROR STOP 1\n"),
    _log() + "BW1_F1_STOP_BEFORE_SOLVER\n",
])
def test_missing_or_forbidden_runtime_evidence_fails_closed(log: str) -> None:
    with pytest.raises(f1.F1Error):
        f1.validate_f1_log(log, mpi_exit_code=74)


@pytest.mark.parametrize("changes", [
    {"finite": "1"}, {"nonfinite": "1"}, {"nonzero": "999999999999999"},
    {"bytes": "100"}, {"diagonal_row": "1"}, {"diag_zero": "0"}, {"max_abs": "NaN"},
])
def test_inconsistent_or_nonfinite_matrix_diagnostics_rejected(changes: dict[str, str]) -> None:
    with pytest.raises(f1.F1Error):
        f1.validate_f1_log(_log(matrix=_matrix(**changes)), mpi_exit_code=74)


@pytest.mark.parametrize("changes", [
    {"finite": "128883", "nonfinite": "1"}, {"nonfinite": "1"},
    {"nonzero": "128885"}, {"max_abs": "Infinity"},
])
def test_nonfinite_or_inconsistent_forcing_diagnostics_rejected(changes: dict[str, str]) -> None:
    with pytest.raises(f1.F1Error):
        f1.validate_f1_log(_log(forcing=_forcing(**changes)), mpi_exit_code=74)


def test_duplicate_malformed_or_inconsistent_rank_diagnostics_rejected() -> None:
    with pytest.raises(f1.F1Error, match="duplicate key"):
        f1.validate_f1_log(_log(matrix="BW1_F1_MATRIX rows=2182 rows=2182\n"), mpi_exit_code=74)
    with pytest.raises(f1.F1Error, match="different rank counts"):
        f1.validate_f1_log(_log() + _matrix(), mpi_exit_code=74)
    with pytest.raises(f1.F1Error, match="inconsistent"):
        f1.validate_f1_log(_log() + _stage(nRank="3") + _matrix() + _forcing() + f1.MARKER + "\nERROR STOP 74\n", mpi_exit_code=74)


def test_parser_has_no_normal_executable_or_solver_override() -> None:
    parser = f1.build_parser()
    help_text = parser.format_help().lower()
    assert "--executable" not in help_text
    assert "--solve" not in help_text
    assert "--runtime-limit-seconds" in help_text
    assert "--memory-cap-gib-per-process" in help_text
    assert "--aggregate-memory-budget-gib" in help_text
    assert "normal executable" not in help_text


def test_operator_limits_require_positive_values_and_aggregate_headroom(tmp_path: Path) -> None:
    with pytest.raises(f1.F1Error, match="positive"):
        f1.run_f1(tmp_path / "source", tmp_path / "bw1", tmp_path / "partition", tmp_path / "out",
                  runtime_limit_seconds=0, memory_cap_gib_per_process=1,
                  aggregate_memory_budget_gib=2)
    with pytest.raises(f1.F1Error, match="aggregate memory budget"):
        f1.run_f1(tmp_path / "source", tmp_path / "bw1", tmp_path / "partition", tmp_path / "out",
                  runtime_limit_seconds=1, memory_cap_gib_per_process=8,
                  aggregate_memory_budget_gib=15)


def test_f1_branch_gate_and_input_validation_precede_toolchain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(f1.sys, "platform", "linux")
    monkeypatch.setattr(f1, "_git", lambda *args: "wrong-branch" if args == ("branch", "--show-current") else "a" * 40)
    monkeypatch.setattr(f1, "_probe_tool", lambda name: pytest.fail("toolchain probe ran before branch/input gate"))
    out = tmp_path / "wrong_branch_evidence"
    result = f1.run_f1(tmp_path / "shellset", tmp_path / "bw1", tmp_path / "partition", out,
        runtime_limit_seconds=60, memory_cap_gib_per_process=2, aggregate_memory_budget_gib=4)
    assert "expected branch" in result["failure"]
    assert (out / "BW1_F1_RESULT.json").is_file()
    assert (out / "BW1_F1_ARTIFACT_MANIFEST.json").is_file()

    monkeypatch.setattr(f1, "_git", lambda *args: f1.EXPECTED_BRANCH if args == ("branch", "--show-current") else f1.F0_BASELINE)
    monkeypatch.setattr(f1.bw1, "validate_bw1_inputs", lambda *args: (_ for _ in ()).throw(f1.F1Error("fixture source-lock/manifest mismatch")))
    out2 = tmp_path / "bad_input_evidence"
    result2 = f1.run_f1(tmp_path / "shellset", tmp_path / "bw1", tmp_path / "partition", out2,
        runtime_limit_seconds=60, memory_cap_gib_per_process=2, aggregate_memory_budget_gib=4)
    assert "fixture source-lock/manifest mismatch" in result2["failure"]
    assert (out2 / "BW1_F1_RESULT.json").is_file()


def test_f1_branch_gate_and_input_validation_precede_toolchain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(f1.sys, "platform", "linux")
    monkeypatch.setattr(f1, "_git", lambda *args: "wrong-branch" if args == ("branch", "--show-current") else "a" * 40)
    monkeypatch.setattr(f1, "_probe_tool", lambda name: pytest.fail("toolchain probe ran before branch/input gate"))
    out = tmp_path / "wrong_branch_evidence"
    result = f1.run_f1(tmp_path / "shellset", tmp_path / "bw1", tmp_path / "partition", out,
        runtime_limit_seconds=60, memory_cap_gib_per_process=2, aggregate_memory_budget_gib=4)
    assert "expected branch" in result["failure"]
    assert (out / "BW1_F1_RESULT.json").is_file()
    assert (out / "BW1_F1_ARTIFACT_MANIFEST.json").is_file()

    monkeypatch.setattr(f1, "_git", lambda *args: f1.EXPECTED_BRANCH if args == ("branch", "--show-current") else f1.F0_BASELINE)
    monkeypatch.setattr(f1.bw1, "validate_bw1_inputs", lambda *args: (_ for _ in ()).throw(f1.F1Error("fixture source-lock/manifest mismatch")))
    out2 = tmp_path / "bad_input_evidence"
    result2 = f1.run_f1(tmp_path / "shellset", tmp_path / "bw1", tmp_path / "partition", out2,
        runtime_limit_seconds=60, memory_cap_gib_per_process=2, aggregate_memory_budget_gib=4)
    assert "fixture source-lock/manifest mismatch" in result2["failure"]
    assert (out2 / "BW1_F1_RESULT.json").is_file()
