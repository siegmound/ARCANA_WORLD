"""Synthetic-only sparse immutable A0/b0 snapshot prototype.

This module is not connected to ShellSet. It defines a deterministic portable
little-endian fixture format and delegates residual diagnostics to the bounded
D3B-P0 validator after reconstructing general-band storage.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import struct
from typing import Sequence

from scripts.r6_si1_bandwidth_f2b_d3b_numerical import diagnose_system


MAGIC = b"ARCNSNP1"
MAX_N = 2048
MAX_RECORDS = 2_000_000
_HEADER = struct.Struct("<8sIIII32s")
_RECORD = struct.Struct("<IIQ")
_U64 = struct.Struct("<Q")


class SnapshotError(ValueError):
    """Snapshot is malformed, incomplete, altered, or outside bounded scope."""


@dataclass(frozen=True)
class ImmutableSystemSnapshot:
    data: bytes
    sha256: str


def _real_bits(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SnapshotError(f"{label} must be a real scalar")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise SnapshotError(f"{label} is outside binary64") from exc
    if not math.isfinite(number):
        raise SnapshotError(f"{label} must be finite")
    return _U64.unpack(struct.pack("<d", number))[0]


def _check_dimensions(n: int, kl: int, ku: int) -> None:
    if any(isinstance(v, bool) or not isinstance(v, int) for v in (n, kl, ku)):
        raise SnapshotError("n, kl and ku must be integers")
    if n < 1 or n > MAX_N or kl < 0 or ku < 0 or kl >= n or ku >= n:
        raise SnapshotError("dimensions outside bounded synthetic scope")
    if (2 * kl + ku + 1) * n > MAX_RECORDS:
        raise SnapshotError("general-band storage exceeds synthetic record/work cap")


def _matrix_source_digest(n: int, kl: int, ku: int, ab: Sequence[Sequence[float]], b0: Sequence[float]) -> bytes:
    digest = hashlib.sha256()
    digest.update(b"ARCANA-A0-B0-IDENTITY-V1\0")
    digest.update(struct.pack("<III", n, kl, ku))
    diagonal0 = kl + ku
    # Hash every logical matrix coefficient in row-major order, including both
    # signed-zero encodings; fill/padding storage is deliberately excluded.
    for i in range(n):
        for j in range(max(0, i - kl), min(n - 1, i + ku) + 1):
            bits = _real_bits(ab[diagonal0 + i - j][j], "A0 coefficient")
            digest.update(_U64.pack(bits))
    for value in b0:
        digest.update(_U64.pack(_real_bits(value, "b0 value")))
    return digest.digest()


def encode_snapshot(
    ab: Sequence[Sequence[float]], b0: Sequence[float], *, kl: int, ku: int
) -> ImmutableSystemSnapshot:
    """Encode original DGBSV AB and b0, preserving binary64 coefficient bits.

    Positive zero matrix entries are implicit. Negative-zero coefficients are
    explicit records. All RHS bit patterns, including signed zero, are stored.
    """
    if isinstance(b0, (str, bytes)) or len(b0) < 1:
        raise SnapshotError("b0 must be a nonempty vector")
    n = len(b0)
    _check_dimensions(n, kl, ku)
    ldab = 2 * kl + ku + 1
    if isinstance(ab, (str, bytes)) or len(ab) != ldab:
        raise SnapshotError(f"AB must have LDAB={ldab} rows")
    for row in ab:
        if isinstance(row, (str, bytes)) or len(row) != n:
            raise SnapshotError("every AB row must contain exactly n entries")
    diagonal0 = kl + ku
    for row0, row in enumerate(ab):
        for j, value in enumerate(row):
            i = row0 - diagonal0 + j
            in_matrix_band = 0 <= i < n and -ku <= i - j <= kl
            number_bits = _real_bits(value, "AB storage")
            if not in_matrix_band and number_bits & 0x7FFFFFFFFFFFFFFF:
                raise SnapshotError("nonzero reserved/fill/padding storage is not A0")
    b_bits = [_real_bits(value, "b0 value") for value in b0]
    records: list[tuple[int, int, int]] = []
    for i in range(n):
        for j in range(max(0, i - kl), min(n - 1, i + ku) + 1):
            bits = _real_bits(ab[diagonal0 + i - j][j], "A0 coefficient")
            if bits != 0:  # preserve every nonzero, subnormal, and negative zero
                records.append((i, j, bits))
    if len(records) > MAX_RECORDS:
        raise SnapshotError("sparse record count exceeds synthetic cap")
    source_digest = _matrix_source_digest(n, kl, ku, ab, b0)
    data = bytearray(_HEADER.pack(MAGIC, n, kl, ku, len(records), source_digest))
    for i, j, bits in records:
        data.extend(_RECORD.pack(i, j, bits))
    for bits in b_bits:
        data.extend(_U64.pack(bits))
    raw = bytes(data)
    return ImmutableSystemSnapshot(raw, hashlib.sha256(raw).hexdigest())


def decode_snapshot(
    data: bytes, *, expected_sha256: str
) -> tuple[tuple[tuple[float, ...], ...], tuple[float, ...], dict[str, object]]:
    """Fail-closed decode; expected SHA is supplied independently by caller."""
    if not isinstance(data, bytes) or not isinstance(expected_sha256, str):
        raise SnapshotError("snapshot bytes and independently retained SHA256 are required")
    actual_sha = hashlib.sha256(data).hexdigest()
    if actual_sha != expected_sha256.lower():
        raise SnapshotError("snapshot SHA256 mismatch")
    if len(data) < _HEADER.size:
        raise SnapshotError("snapshot header is incomplete")
    magic, n, kl, ku, count, source_digest = _HEADER.unpack_from(data)
    if magic != MAGIC:
        raise SnapshotError("snapshot magic/version mismatch")
    _check_dimensions(n, kl, ku)
    max_logical = n * min(n, kl + ku + 1)
    if count > min(MAX_RECORDS, max_logical):
        raise SnapshotError("record count exceeds logical matrix capacity")
    expected_size = _HEADER.size + count * _RECORD.size + n * _U64.size
    if len(data) != expected_size:
        raise SnapshotError("snapshot length does not match declared records and RHS")

    ldab = 2 * kl + ku + 1
    ab = [[0.0] * n for _ in range(ldab)]
    seen: set[tuple[int, int]] = set()
    previous: tuple[int, int] | None = None
    offset = _HEADER.size
    for _ in range(count):
        i, j, bits = _RECORD.unpack_from(data, offset)
        offset += _RECORD.size
        key = (i, j)
        if i >= n or j >= n or not (-ku <= i - j <= kl):
            raise SnapshotError("coefficient index outside matrix/band")
        if key in seen or (previous is not None and key <= previous):
            raise SnapshotError("duplicate or noncanonical coefficient ordering")
        if bits == 0:
            raise SnapshotError("positive-zero entries must be implicit")
        number = struct.unpack("<d", _U64.pack(bits))[0]
        if not math.isfinite(number):
            raise SnapshotError("snapshot contains a nonfinite coefficient")
        ab[kl + ku + i - j][j] = number
        seen.add(key)
        previous = key
    b_bits = [_U64.unpack_from(data, offset + i * _U64.size)[0] for i in range(n)]
    b0 = tuple(struct.unpack("<d", _U64.pack(bits))[0] for bits in b_bits)
    if not all(math.isfinite(value) for value in b0):
        raise SnapshotError("snapshot contains nonfinite RHS")
    if _matrix_source_digest(n, kl, ku, ab, b0) != source_digest:
        raise SnapshotError("reconstructed A0/b0 identity digest mismatch")
    metadata: dict[str, object] = {
        "format": "ARCANA_SPARSE_A0_B0_SNAPSHOT_V1",
        "n": n,
        "kl": kl,
        "ku": ku,
        "ldab": ldab,
        "stored_matrix_records": count,
        "matrix_source_sha256": source_digest.hex(),
        "snapshot_sha256": actual_sha,
        "zero_policy": "positive_zero_implicit; negative_zero_explicit; RHS bits always explicit",
        "scope": "SYNTHETIC_FIXTURE_ONLY",
    }
    return tuple(tuple(row) for row in ab), b0, metadata


def diagnose_snapshot(
    snapshot: ImmutableSystemSnapshot, x: Sequence[float]
) -> dict[str, object]:
    """Run existing D3B diagnostics using only authenticated decoded snapshot."""
    ab, b0, metadata = decode_snapshot(snapshot.data, expected_sha256=snapshot.sha256)
    result = diagnose_system(ab, b0, x, kl=int(metadata["kl"]), ku=int(metadata["ku"]))
    return {"snapshot": metadata, "diagnostics": result}


__all__ = ["ImmutableSystemSnapshot", "SnapshotError", "decode_snapshot", "diagnose_snapshot", "encode_snapshot"]
