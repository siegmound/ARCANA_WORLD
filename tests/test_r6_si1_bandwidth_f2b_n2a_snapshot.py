import copy
import hashlib
import struct

import pytest

from scripts.r6_si1_bandwidth_f2b_d3b_numerical import (
    OFFLINE_VALIDATOR_PASS,
    THRESHOLD_UNJUSTIFIED,
)
from scripts.r6_si1_bandwidth_f2b_n2a_snapshot import (
    SnapshotError,
    decode_snapshot,
    diagnose_snapshot,
    encode_snapshot,
)


def dense_to_band(matrix, kl, ku):
    n = len(matrix)
    ab = [[0.0] * n for _ in range(2 * kl + ku + 1)]
    for i in range(n):
        for j in range(n):
            if -ku <= i - j <= kl:
                ab[kl + ku + i - j][j] = matrix[i][j]
            else:
                assert matrix[i][j] == 0.0
    return ab


def test_sparse_snapshot_survives_destructive_work_buffers_and_matches_dense_oracle():
    dense_a0 = [
        [4.0, 1.0, -1.0, 0.0],
        [2.0, 5.0, 3.0, 7.0],
        [0.0, -2.0, 6.0, 4.0],
        [0.0, 0.0, 1.0, 3.0],
    ]
    kl, ku = 1, 2
    b0 = [8.0, 10.0, -7.0, 1.0]
    x = [1.0, 2.0, -1.0, 0.5]
    original_ab = dense_to_band(dense_a0, kl, ku)
    original_b = list(b0)
    snapshot = encode_snapshot(original_ab, original_b, kl=kl, ku=ku)
    saved_bytes = snapshot.data
    work_ab, work_b = copy.deepcopy(original_ab), list(original_b)

    # Simulate the destructive overwrite contract without calling a solver.
    for i in range(len(dense_a0)):
        for j in range(len(dense_a0)):
            if -ku <= i - j <= kl:
                work_ab[kl + ku + i - j][j] = -123.0 - i - j
        work_b[i] = 9000.0 + i
    assert work_ab != original_ab
    assert work_b != original_b

    recovered_ab, recovered_b, meta = decode_snapshot(
        snapshot.data, expected_sha256=snapshot.sha256
    )
    assert recovered_ab == tuple(tuple(row) for row in original_ab)
    assert recovered_b == tuple(original_b)
    assert meta["scope"] == "SYNTHETIC_FIXTURE_ONLY"
    assert snapshot.data == saved_bytes

    checked = diagnose_snapshot(snapshot, x)
    result = checked["diagnostics"]
    # Independent dense oracle, calculated directly from the literal fixture.
    ax = [sum(dense_a0[i][j] * x[j] for j in range(4)) for i in range(4)]
    residual = [b0[i] - ax[i] for i in range(4)]
    norm_a = max(sum(abs(value) for value in row) for row in dense_a0)
    norm_x = max(abs(value) for value in x)
    norm_b = max(abs(value) for value in b0)
    normwise = max(abs(value) for value in residual) / (norm_a * norm_x + norm_b)
    componentwise = max(
        abs(residual[i])
        / (sum(abs(dense_a0[i][j] * x[j]) for j in range(4)) + abs(b0[i]))
        for i in range(4)
    )
    assert result["status"] == OFFLINE_VALIDATOR_PASS
    assert result["solver_acceptance"] == THRESHOLD_UNJUSTIFIED
    assert result["residual_vector"] == residual == [1.0, -2.5, 1.0, 0.5]
    assert result["absolute_residual_inf"] == 2.5
    assert result["matrix_inf_norm"] == norm_a == 17.0
    assert result["backward_error_normwise"] == normwise == 5 / 88
    assert result["backward_error_componentwise"] == componentwise == 1 / 7
    assert original_ab == dense_to_band(dense_a0, kl, ku)
    assert original_b == b0


def test_snapshot_preserves_subnormal_and_signed_zero_bits():
    kl, ku = 1, 1
    dense = [[2.0, -0.0, 0.0], [5e-324, 3.0, 4.0], [0.0, 6.0, 7.0]]
    ab = dense_to_band(dense, kl, ku)
    rhs = [-0.0, 1.0, 2.0]
    snapshot = encode_snapshot(ab, rhs, kl=kl, ku=ku)
    decoded, decoded_rhs, _ = decode_snapshot(
        snapshot.data, expected_sha256=snapshot.sha256
    )
    assert struct.pack("<d", decoded[kl + ku + 0 - 1][1]) == struct.pack("<d", -0.0)
    assert struct.pack("<d", decoded[kl + ku + 1 - 0][0]) == struct.pack("<d", 5e-324)
    assert struct.pack("<d", decoded_rhs[0]) == struct.pack("<d", -0.0)
    _, _, _, _, record_count, _ = struct.unpack_from("<8sIIII32s", snapshot.data)
    record_size = struct.calcsize("<IIQ")
    for index in range(record_count):
        _, _, bits = struct.unpack_from(
            "<IIQ", snapshot.data, struct.calcsize("<8sIIII32s") + index * record_size
        )
        assert bits != 0


def test_snapshot_rejects_truncation_and_external_digest_mismatch():
    snapshot = encode_snapshot(dense_to_band([[2.0, 1.0], [3.0, 4.0]], 1, 1), [1.0, 2.0], kl=1, ku=1)
    with pytest.raises(SnapshotError):
        decode_snapshot(snapshot.data[:-1], expected_sha256=snapshot.sha256)
    with pytest.raises(SnapshotError, match="SHA256 mismatch"):
        decode_snapshot(snapshot.data, expected_sha256="0" * 64)


def test_snapshot_rejects_altered_value_even_if_outer_digest_is_recomputed():
    snapshot = encode_snapshot(dense_to_band([[2.0, 1.0], [3.0, 4.0]], 1, 1), [1.0, 2.0], kl=1, ku=1)
    altered = bytearray(snapshot.data)
    value_offset = struct.calcsize("<8sIIII32s") + 8
    altered[value_offset] ^= 1
    altered_bytes = bytes(altered)
    # Recomputing the external file SHA cannot forge the independent A0/b0
    # source identity embedded in the authenticated header.
    with pytest.raises(SnapshotError, match="identity digest"):
        decode_snapshot(altered_bytes, expected_sha256=hashlib.sha256(altered_bytes).hexdigest())


def test_snapshot_rejects_omitted_nonzero_even_when_count_and_outer_sha_are_updated():
    snapshot = encode_snapshot(
        dense_to_band([[2.0, 1.0], [3.0, 4.0]], 1, 1), [1.0, 2.0], kl=1, ku=1
    )
    header_format = "<8sIIII32s"
    header_size = struct.calcsize(header_format)
    record_size = struct.calcsize("<IIQ")
    magic, n, kl, ku, count, source_digest = struct.unpack_from(
        header_format, snapshot.data
    )
    assert count > 0
    # Remove one coefficient record, update the declared count and outer file
    # hash, but preserve the source identity digest captured from the original.
    omitted = (
        struct.pack(header_format, magic, n, kl, ku, count - 1, source_digest)
        + snapshot.data[header_size + record_size:]
    )
    with pytest.raises(SnapshotError, match="identity digest"):
        decode_snapshot(omitted, expected_sha256=hashlib.sha256(omitted).hexdigest())


def test_snapshot_rejects_invalid_index_padding_and_duplicate_record():
    snapshot = encode_snapshot(dense_to_band([[2.0, 1.0], [3.0, 4.0]], 1, 1), [1.0, 2.0], kl=1, ku=1)
    header_size = struct.calcsize("<8sIIII32s")

    invalid_index = bytearray(snapshot.data)
    struct.pack_into("<I", invalid_index, header_size, 99)
    invalid_index = bytes(invalid_index)
    with pytest.raises(SnapshotError, match="outside matrix/band"):
        decode_snapshot(invalid_index, expected_sha256=hashlib.sha256(invalid_index).hexdigest())

    duplicate = bytearray(snapshot.data)
    duplicate[header_size + 16:header_size + 24] = duplicate[header_size:header_size + 8]
    duplicate = bytes(duplicate)
    with pytest.raises(SnapshotError, match="duplicate"):
        decode_snapshot(duplicate, expected_sha256=hashlib.sha256(duplicate).hexdigest())

    padded = dense_to_band([[2.0, 1.0], [3.0, 4.0]], 1, 1)
    padded[0][0] = 1.0  # leading LAPACK pivot-fill row is not original A0
    with pytest.raises(SnapshotError, match="reserved/fill/padding"):
        encode_snapshot(padded, [1.0, 2.0], kl=1, ku=1)
