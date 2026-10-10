"""Bounded N2B binary-contract tests; compiler-backed cases need gfortran."""

import hashlib
from pathlib import Path
import shutil
import struct
import subprocess

import pytest

from scripts.r6_si1_bandwidth_f2b_d3b_numerical import (
    OFFLINE_VALIDATOR_PASS,
    diagnose_system,
)
from scripts.r6_si1_bandwidth_f2b_n2a_snapshot import (
    SnapshotError,
    decode_snapshot,
    encode_snapshot,
)


ROOT = Path(__file__).resolve().parents[1]
FORTRAN = ROOT / "tests/fixtures/r6_si1_bandwidth_f2b_n2b_interop.f90"
HEADER = struct.Struct("<8sIIII32s")
U64 = struct.Struct("<Q")
GFORTRAN = shutil.which("gfortran")


def _fixture():
    tiny = struct.unpack("<d", U64.pack(1))[0]
    matrix = [
        [4.0, 1.0, -0.0, 0.0],
        [2.0, 5.0, 3.0, 7.0],
        [0.0, tiny, 6.0, 4.0],
        [0.0, 0.0, 1.0, 3.0],
    ]
    rhs = [8.0, 10.0, -7.0, 1.0]
    return matrix, rhs, 1, 2


def _band(matrix, kl, ku):
    n = len(matrix)
    ab = [[0.0] * n for _ in range(2 * kl + ku + 1)]
    for i in range(n):
        for j in range(n):
            if -ku <= i - j <= kl:
                ab[kl + ku + i - j][j] = matrix[i][j]
            else:
                assert matrix[i][j] == 0.0
    return ab


def _oracle_source_digest(matrix, rhs, kl, ku):
    """Independent transcription of the wire contract, not N2A internals."""
    digest = hashlib.sha256(b"ARCANA-A0-B0-IDENTITY-V1\0")
    n = len(rhs)
    digest.update(struct.pack("<III", n, kl, ku))
    for i in range(n):
        for j in range(max(0, i - kl), min(n - 1, i + ku) + 1):
            digest.update(U64.pack(struct.unpack("<Q", struct.pack("<d", matrix[i][j]))[0]))
    for value in rhs:
        digest.update(U64.pack(struct.unpack("<Q", struct.pack("<d", value))[0]))
    return digest.hexdigest()


def _oracle_value_bytes(matrix, rhs, kl, ku):
    out = bytearray()
    n = len(rhs)
    for i in range(n):
        for j in range(max(0, i - kl), min(n - 1, i + ku) + 1):
            out.extend(struct.pack("<d", matrix[i][j]))
    for value in rhs:
        out.extend(struct.pack("<d", value))
    return bytes(out)


def _compile(tmp_path_factory):
    if GFORTRAN is None:
        pytest.skip("Fortran interoperability not run: no local gfortran compiler")
    build = tmp_path_factory.mktemp("n2b-fortran-build")
    exe = build / "n2b_interop.exe"
    result = subprocess.run(
        [GFORTRAN, "-std=f2008", "-O0", "-fno-fast-math", "-fcheck=all", str(FORTRAN), "-o", str(exe)],
        cwd=build,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return exe


def _run(exe, *args, must_fail=False):
    result = subprocess.run([str(exe), *map(str, args)], text=True, capture_output=True, check=False)
    if must_fail:
        assert result.returncode != 0, result.stdout + result.stderr
    else:
        assert result.returncode == 0, result.stdout + result.stderr
    return result


def test_n2a_wire_contract_is_explicit_and_python_oracle_is_independent():
    matrix, rhs, kl, ku = _fixture()
    snapshot = encode_snapshot(_band(matrix, kl, ku), rhs, kl=kl, ku=ku)
    magic, n, got_kl, got_ku, count, digest = HEADER.unpack_from(snapshot.data)
    assert magic == b"ARCNSNP1"
    assert (n, got_kl, got_ku) == (4, 1, 2)
    assert count == 12  # includes explicit -0 and subnormal; omits +0 only
    assert digest.hex() == _oracle_source_digest(matrix, rhs, kl, ku)
    assert hashlib.sha256(snapshot.data).hexdigest() == snapshot.sha256
    decoded, decoded_rhs, metadata = decode_snapshot(snapshot.data, expected_sha256=snapshot.sha256)
    assert metadata["matrix_source_sha256"] == _oracle_source_digest(matrix, rhs, kl, ku)
    for i in range(4):
        for j in range(4):
            if -ku <= i - j <= kl:
                assert struct.pack("<d", decoded[kl + ku + i - j][j]) == struct.pack("<d", matrix[i][j])
    assert b"".join(struct.pack("<d", value) for value in decoded_rhs) == b"".join(struct.pack("<d", value) for value in rhs)
    assert _oracle_value_bytes(matrix, rhs, kl, ku)[-32:] == b"".join(U64.pack(struct.unpack("<Q", struct.pack("<d", x))[0]) for x in rhs)
    assert "call dgbsv" not in FORTRAN.read_text(encoding="utf-8").lower()


def test_python_reader_rejects_interop_payload_digest_and_oracle_disagreement():
    matrix, rhs, kl, ku = _fixture()
    snapshot = encode_snapshot(_band(matrix, kl, ku), rhs, kl=kl, ku=ku)
    with pytest.raises(SnapshotError, match="SHA256 mismatch"):
        decode_snapshot(snapshot.data, expected_sha256="0" * 64)

    altered = bytearray(snapshot.data)
    # Alter the first coefficient while preserving the embedded oracle digest.
    altered[HEADER.size + 8] ^= 1
    altered = bytes(altered)
    with pytest.raises(SnapshotError, match="identity digest"):
        decode_snapshot(altered, expected_sha256=hashlib.sha256(altered).hexdigest())


def test_python_writer_fortran_reader_roundtrip(tmp_path_factory):
    exe = _compile(tmp_path_factory)
    matrix, rhs, kl, ku = _fixture()
    expected_digest = _oracle_source_digest(matrix, rhs, kl, ku)
    snapshot = encode_snapshot(_band(matrix, kl, ku), rhs, kl=kl, ku=ku)
    path = tmp_path_factory.mktemp("n2b-python-to-fortran") / "fixture.n2a"
    path.write_bytes(snapshot.data)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == snapshot.sha256
    _run(exe, "read", path, expected_digest.upper(), 12)
    actual = Path(str(path) + ".raw").read_bytes()
    assert actual == _oracle_value_bytes(matrix, rhs, kl, ku)


def test_fortran_writer_python_reader_and_dense_metric_oracle(tmp_path_factory):
    exe = _compile(tmp_path_factory)
    matrix, rhs, kl, ku = _fixture()
    expected_digest = _oracle_source_digest(matrix, rhs, kl, ku)
    path = tmp_path_factory.mktemp("n2b-fortran-to-python") / "fixture.n2a"
    _run(exe, "write", path, expected_digest.upper())
    payload = path.read_bytes()
    outer_sha = hashlib.sha256(payload).hexdigest()
    ab, decoded_rhs, metadata = decode_snapshot(payload, expected_sha256=outer_sha)
    assert metadata["matrix_source_sha256"] == expected_digest
    assert _oracle_value_bytes(matrix, rhs, kl, ku) == _oracle_value_bytes(
        [list(row) for row in matrix], decoded_rhs, kl, ku
    )
    for i in range(len(rhs)):
        for j in range(len(rhs)):
            if -ku <= i - j <= kl:
                assert struct.pack("<d", ab[kl + ku + i - j][j]) == struct.pack("<d", matrix[i][j])
    x = [1.0, 2.0, -1.0, 0.5]
    diagnostic = diagnose_system(ab, decoded_rhs, x, kl=kl, ku=ku)
    dense_ax = [sum(matrix[i][j] * x[j] for j in range(4)) for i in range(4)]
    dense_r = [rhs[i] - dense_ax[i] for i in range(4)]
    assert diagnostic["status"] == OFFLINE_VALIDATOR_PASS
    assert diagnostic["residual_vector"] == dense_r
    assert diagnostic["absolute_residual_inf"] == max(abs(value) for value in dense_r)


def test_fortran_reader_fails_closed_on_malformed_payloads(tmp_path_factory):
    exe = _compile(tmp_path_factory)
    matrix, rhs, kl, ku = _fixture()
    expected_digest = _oracle_source_digest(matrix, rhs, kl, ku)
    snapshot = encode_snapshot(_band(matrix, kl, ku), rhs, kl=kl, ku=ku)
    root = tmp_path_factory.mktemp("n2b-fortran-negative")

    truncated = root / "truncated.n2a"
    truncated.write_bytes(snapshot.data[:-1])
    _run(exe, "read", truncated, expected_digest.upper(), 12, must_fail=True)

    mismatch = root / "wrong-digest.n2a"
    mismatch.write_bytes(snapshot.data)
    _run(exe, "read", mismatch, "0" * 64, 12, must_fail=True)

    header_size = HEADER.size
    duplicate_bytes = bytearray(snapshot.data)
    duplicate_bytes[header_size + 16:header_size + 24] = duplicate_bytes[header_size:header_size + 8]
    duplicate = root / "duplicate.n2a"
    duplicate.write_bytes(duplicate_bytes)
    _run(exe, "read", duplicate, expected_digest.upper(), 12, must_fail=True)

    invalid_bytes = bytearray(snapshot.data)
    struct.pack_into("<I", invalid_bytes, header_size, 99)
    invalid = root / "invalid-index.n2a"
    invalid.write_bytes(invalid_bytes)
    _run(exe, "read", invalid, expected_digest.upper(), 12, must_fail=True)

    magic, n, kl, ku, count, source_digest = HEADER.unpack_from(snapshot.data)
    omitted_bytes = HEADER.pack(magic, n, kl, ku, count - 1, source_digest) + snapshot.data[header_size + 16:]
    omitted = root / "omitted.n2a"
    omitted.write_bytes(omitted_bytes)
    _run(exe, "read", omitted, expected_digest.upper(), 12, must_fail=True)


def test_python_reader_rejects_missing_duplicate_invalid_and_altered_records():
    matrix, rhs, kl, ku = _fixture()
    snapshot = encode_snapshot(_band(matrix, kl, ku), rhs, kl=kl, ku=ku)
    magic, n, got_kl, got_ku, count, source_digest = HEADER.unpack_from(snapshot.data)
    records_start = HEADER.size

    # Missing record: decrement count, retain original B digest, update A hash.
    omitted = (
        HEADER.pack(magic, n, got_kl, got_ku, count - 1, source_digest)
        + snapshot.data[records_start + 16:]
    )
    with pytest.raises(SnapshotError, match="identity digest"):
        decode_snapshot(omitted, expected_sha256=hashlib.sha256(omitted).hexdigest())

    # Duplicate a record coordinate. The order/uniqueness validator rejects it.
    duplicate = bytearray(snapshot.data)
    duplicate[records_start + 16:records_start + 24] = duplicate[records_start:records_start + 8]
    duplicate = bytes(duplicate)
    with pytest.raises(SnapshotError, match="duplicate|ordering"):
        decode_snapshot(duplicate, expected_sha256=hashlib.sha256(duplicate).hexdigest())

    invalid = bytearray(snapshot.data)
    struct.pack_into("<I", invalid, records_start, 99)
    invalid = bytes(invalid)
    with pytest.raises(SnapshotError, match="outside matrix/band"):
        decode_snapshot(invalid, expected_sha256=hashlib.sha256(invalid).hexdigest())

    altered = bytearray(snapshot.data)
    altered[records_start + 8] ^= 1
    altered = bytes(altered)
    with pytest.raises(SnapshotError, match="identity digest"):
        decode_snapshot(altered, expected_sha256=hashlib.sha256(altered).hexdigest())
