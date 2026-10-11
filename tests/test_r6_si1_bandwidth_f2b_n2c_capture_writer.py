"""W1 synthetic contract tests; compiler-backed tests are conditional."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import struct
import subprocess

import pytest

from scripts.r6_si1_bandwidth_f2b_n2a_snapshot import SnapshotError, encode_snapshot
from scripts.r6_si1_bandwidth_f2b_n2c_capture_verify import (
    canonical_oracle_sha256,
    verify_capture_payload,
)


ROOT = Path(__file__).resolve().parents[1]
WRITER = ROOT / "src/fortran/r6_sparse_snapshot_writer.f90"
DRIVER = ROOT / "tests/fixtures/r6_si1_bandwidth_f2b_n2c_capture_driver.f90"
FLAGS = {
    "gfortran": ("-std=f2008", "-O0", "-fno-fast-math", "-fcheck=all"),
    "nvfortran": ("-O0", "-Kieee", "-Mnodaz", "-Mnoflushz", "-Mbounds"),
}
U64 = struct.Struct("<Q")


def _fixture(n: int, kl: int, ku: int):
    ldab = 2 * kl + ku + 1
    ab = [[0.0] * n for _ in range(ldab)]
    b0 = [0.0] * n
    for i in range(n):
        for j in range(max(0, i - kl), min(n - 1, i + ku) + 1):
            row = kl + ku + i - j
            if i == 0 and j == 1:
                value = -0.0
            elif i == 1 and j == 0 and kl >= 1:
                value = struct.unpack("<d", U64.pack(1))[0]
            elif i == j:
                value = float(i + 2)
            elif (i + j) % 3 != 0:
                value = float(10 * i - j + 1) / 8.0
            else:
                value = 0.0
            ab[row][j] = value
        b0[i] = -0.0 if i == 0 else float(2 * i - 3) / 4.0
    return ab, b0


def _compiler():
    requested = os.environ.get("ARCANA_N2B_FC")
    compiler = requested if requested is not None else "gfortran"
    if compiler not in FLAGS:
        pytest.fail(f"unsupported ARCANA_N2B_FC={compiler!r}", pytrace=False)
    exe = shutil.which(compiler)
    if exe is None:
        if requested is None:
            pytest.skip(f"Fortran capture execution not run: default compiler {compiler!r} unavailable")
        pytest.fail(f"requested ARCANA_N2B_FC compiler {compiler!r} unavailable", pytrace=False)
    return exe, FLAGS[compiler]


def _compile(tmp_path: Path) -> Path:
    compiler, flags = _compiler()
    exe = tmp_path / "n2c_capture_driver.exe"
    result = subprocess.run(
        [compiler, *flags, str(WRITER), str(DRIVER), "-o", str(exe)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return exe


def _run(exe: Path, mode: str, ab, b0, kl: int, ku: int, target: Path, marker: Path, case="NORMAL", digest=None):
    n = len(b0)
    source_digest = digest or canonical_oracle_sha256(ab, b0, kl=kl, ku=ku)
    proc = subprocess.run(
        [str(exe), mode, str(n), str(kl), str(ku), str(target), source_digest, case, str(marker)],
        cwd=target.parent,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    status_line = next(line for line in proc.stdout.splitlines() if line.startswith("CAPTURE_STATUS="))
    return int(status_line.partition("=")[2]), proc.stdout


def test_python_external_verifier_checks_independent_oracle_and_exact_bits():
    ab, b0 = _fixture(4, 1, 2)
    snapshot = encode_snapshot(ab, b0, kl=1, ku=2)
    result = verify_capture_payload(
        snapshot.data,
        expected_payload_sha256=hashlib.sha256(snapshot.data).hexdigest(),
        expected_source_sha256=canonical_oracle_sha256(ab, b0, kl=1, ku=2),
        oracle_ab=ab,
        oracle_b0=b0,
        kl=1,
        ku=2,
    )
    assert result["status"] == "SYNTHETIC_SNAPSHOT_VERIFIED_AGAINST_INDEPENDENT_ORACLE"
    assert result["scope"] == "SYNTHETIC_FIXTURE_ONLY"
    assert result["runtime_invocation_provenance"] == "NOT_ESTABLISHED"


def test_python_external_verifier_rejects_wrong_oracle_and_outer_digest():
    ab, b0 = _fixture(4, 1, 2)
    snapshot = encode_snapshot(ab, b0, kl=1, ku=2)
    wrong_ab = [list(row) for row in ab]
    # DGBSV diagonal row is kl+ku in zero-based Python storage.
    wrong_ab[3][0] = 123.0
    args = dict(
        expected_payload_sha256=hashlib.sha256(snapshot.data).hexdigest(),
        expected_source_sha256=canonical_oracle_sha256(ab, b0, kl=1, ku=2),
        oracle_ab=wrong_ab,
        oracle_b0=b0,
        kl=1,
        ku=2,
    )
    with pytest.raises(SnapshotError, match="source-value SHA256 disagrees"):
        verify_capture_payload(snapshot.data, **args)
    args["oracle_ab"] = ab
    args["expected_payload_sha256"] = "0" * 64
    with pytest.raises(SnapshotError, match="SHA256 mismatch"):
        verify_capture_payload(snapshot.data, **args)


def test_fortran_module_is_bounded_read_only_and_contains_no_solver_call():
    text = WRITER.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "module r6_sparse_snapshot_writer" in lowered
    assert "status='new'" in lowered
    assert "access='stream'" in lowered
    assert "mode_default_off" in lowered
    assert "capture_only_stop_required" in lowered
    assert "capture_failed" in lowered
    assert "source_value_sha256" in lowered
    assert "ieee_support_datatype" in lowered
    assert "is_contiguous(ab)" in lowered
    assert "do i = max(0_int64,j-ku), min(n-1_int64,j+kl)" in lowered
    assert "call dgbsv" not in lowered
    assert "allocate(" not in lowered
    assert "threshold" not in lowered
    assert all(len(line) <= 132 for line in text.splitlines())


def test_fortran_driver_has_explicit_pre_solver_capture_gate():
    text = DRIVER.read_text(encoding="utf-8").lower()
    assert "status == capture_default_off .or. status == capture_only_stop_required .or. status == capture_failed" in text
    assert text.index("status == capture_only_stop_required") < text.index("call mark_solver_called")
    assert "call dgbsv" not in text
    assert all(len(line) <= 132 for line in DRIVER.read_text(encoding="utf-8").splitlines())


def test_compiled_fortran_writer_variable_bands_and_fail_closed_paths(tmp_path):
    exe = _compile(tmp_path)
    solver_marker = tmp_path / "solver-called.marker"

    # Both non-symmetric bandwidth orientations, a diagonal-only case, and the
    # N2B reference shape are compared byte-for-byte with N2A and an oracle.
    for index, (n, kl, ku) in enumerate(((4, 1, 2), (3, 0, 2), (5, 2, 1), (2, 0, 0))):
        ab, b0 = _fixture(n, kl, ku)
        target = tmp_path / f"capture-{index}.tmp"
        status, _ = _run(exe, "CAPTURE_ONLY", ab, b0, kl, ku, target, solver_marker)
        assert status == 1  # CAPTURE_ONLY_STOP_REQUIRED
        assert not solver_marker.exists()
        payload = target.read_bytes()
        expected = encode_snapshot(ab, b0, kl=kl, ku=ku)
        assert payload == expected.data
        report = verify_capture_payload(
            payload,
            expected_payload_sha256=hashlib.sha256(payload).hexdigest(),
            expected_source_sha256=canonical_oracle_sha256(ab, b0, kl=kl, ku=ku),
            oracle_ab=ab,
            oracle_b0=b0,
            kl=kl,
            ku=ku,
        )
        assert report["scope"] == "SYNTHETIC_FIXTURE_ONLY"

    ab, b0 = _fixture(4, 1, 2)
    default_target = tmp_path / "default-off.tmp"
    status, _ = _run(exe, "DEFAULT_OFF", ab, b0, 1, 2, default_target, solver_marker)
    assert status == 0
    assert not default_target.exists()
    assert not solver_marker.exists()

    bad_shape = tmp_path / "incomplete.tmp"
    status, _ = _run(exe, "CAPTURE_ONLY", ab, b0, 1, 2, bad_shape, solver_marker, case="BAD_SHAPE")
    assert status == 2
    assert not solver_marker.exists()

    io_failure = tmp_path / "missing-parent" / "io-failure.tmp"
    status, _ = _run(exe, "CAPTURE_ONLY", ab, b0, 1, 2, io_failure, solver_marker)
    assert status == 2
    assert not io_failure.exists()
    assert not solver_marker.exists()
    assert not bad_shape.exists()

    bad_context = tmp_path / "missing-context.tmp"
    status, _ = _run(exe, "CAPTURE_ONLY", ab, b0, 1, 2, bad_context, solver_marker, case="BAD_CONTEXT")
    assert status == 2
    assert not bad_context.exists()
    assert not solver_marker.exists()

    nonfinite = tmp_path / "nonfinite.tmp"
    status, _ = _run(exe, "CAPTURE_ONLY", ab, b0, 1, 2, nonfinite, solver_marker, case="NONFINITE")
    assert status == 2
    assert not nonfinite.exists()
    assert not solver_marker.exists()

    collision = tmp_path / "collision.tmp"
    collision.write_bytes(b"preexisting")
    status, _ = _run(exe, "CAPTURE_ONLY", ab, b0, 1, 2, collision, solver_marker)
    assert status == 2
    assert collision.read_bytes() == b"preexisting"
    assert not solver_marker.exists()

    bad_digest = tmp_path / "bad-source-digest.tmp"
    status, _ = _run(exe, "CAPTURE_ONLY", ab, b0, 1, 2, bad_digest, solver_marker, digest="0" * 64)
    assert status == 1  # writer serializes a supplied B; it does not claim to authenticate B
    payload = bad_digest.read_bytes()
    with pytest.raises(SnapshotError, match="identity digest"):
        verify_capture_payload(
            payload,
            expected_payload_sha256=hashlib.sha256(payload).hexdigest(),
            expected_source_sha256=canonical_oracle_sha256(ab, b0, kl=1, ku=2),
            oracle_ab=ab,
            oracle_b0=b0,
            kl=1,
            ku=2,
        )
    assert not solver_marker.exists()
