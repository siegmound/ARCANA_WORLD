"""Independent-oracle checks for bounded synthetic N2C capture payloads.

This verifier does not establish ShellSet invocation provenance or runtime
durability. The caller must provide an independently computed payload digest,
source-value digest, and original band/RHS oracle.
"""

from __future__ import annotations

import hashlib
import math
import re
import struct
from typing import Sequence

from scripts.r6_si1_bandwidth_f2b_n2a_snapshot import SnapshotError, decode_snapshot


_U32 = struct.Struct("<I")
_U64 = struct.Struct("<Q")
_SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")
_IDENTITY_PREFIX = b"ARCANA-A0-B0-IDENTITY-V1\0"


def _bits(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SnapshotError(f"{label} must be a binary64 scalar")
    try:
        number = float(value)
        if not math.isfinite(number):
            raise SnapshotError(f"{label} must be finite")
        return _U64.unpack(_U64.pack(struct.unpack("<Q", struct.pack("<d", number))[0]))[0]
    except (OverflowError, TypeError, ValueError, struct.error) as exc:
        raise SnapshotError(f"{label} is outside binary64") from exc


def canonical_oracle_sha256(
    ab: Sequence[Sequence[float]], b0: Sequence[float], *, kl: int, ku: int
) -> str:
    """Calculate N2A source-value identity directly from the independent oracle."""
    if isinstance(kl, bool) or isinstance(ku, bool) or not isinstance(kl, int) or not isinstance(ku, int):
        raise SnapshotError("KL/KU must be integers")
    if isinstance(b0, (str, bytes)) or len(b0) < 1:
        raise SnapshotError("oracle RHS must be nonempty")
    n = len(b0)
    if n > 2048 or kl < 0 or ku < 0 or kl >= n or ku >= n:
        raise SnapshotError("oracle dimensions outside bounded scope")
    ldab = 2 * kl + ku + 1
    if isinstance(ab, (str, bytes)) or len(ab) != ldab or any(len(row) != n for row in ab):
        raise SnapshotError("oracle AB shape mismatch")
    digest = hashlib.sha256()
    digest.update(_IDENTITY_PREFIX)
    digest.update(struct.pack("<III", n, kl, ku))
    diagonal = kl + ku
    for i in range(n):
        for j in range(max(0, i - kl), min(n - 1, i + ku) + 1):
            digest.update(_U64.pack(_bits(ab[diagonal + i - j][j], "oracle coefficient")))
    for value in b0:
        digest.update(_U64.pack(_bits(value, "oracle RHS")))
    return digest.hexdigest()


def verify_capture_payload(
    payload: bytes,
    *,
    expected_payload_sha256: str,
    expected_source_sha256: str,
    oracle_ab: Sequence[Sequence[float]],
    oracle_b0: Sequence[float],
    kl: int,
    ku: int,
) -> dict[str, object]:
    """Verify wire integrity and every logical binary64 value against an oracle.

    The digests are checked against caller-supplied identities, but this helper
    does not establish that those identities came from a real FEM invocation.
    """
    if not isinstance(payload, bytes):
        raise SnapshotError("payload must be acquired as immutable bytes")
    if not isinstance(expected_payload_sha256, str) or not _SHA256.fullmatch(expected_payload_sha256):
        raise SnapshotError("independent payload SHA256 is required")
    if not isinstance(expected_source_sha256, str) or not _SHA256.fullmatch(expected_source_sha256):
        raise SnapshotError("independent source-value SHA256 is required")

    oracle_sha = canonical_oracle_sha256(oracle_ab, oracle_b0, kl=kl, ku=ku)
    if oracle_sha.lower() != expected_source_sha256.lower():
        raise SnapshotError("provided source-value SHA256 disagrees with independent oracle")

    decoded_ab, decoded_b0, metadata = decode_snapshot(
        payload, expected_sha256=expected_payload_sha256
    )
    n = len(oracle_b0)
    if (metadata["n"], metadata["kl"], metadata["ku"]) != (n, kl, ku):
        raise SnapshotError("snapshot dimensions disagree with oracle")
    if str(metadata["matrix_source_sha256"]).lower() != oracle_sha:
        raise SnapshotError("embedded source-value digest disagrees with independent oracle")

    diagonal = kl + ku
    for i in range(n):
        for j in range(max(0, i - kl), min(n - 1, i + ku) + 1):
            expected = _bits(oracle_ab[diagonal + i - j][j], "oracle coefficient")
            observed = _bits(decoded_ab[diagonal + i - j][j], "decoded coefficient")
            if observed != expected:
                raise SnapshotError(f"snapshot coefficient bits differ from oracle at ({i},{j})")
    for index, (observed_value, expected_value) in enumerate(zip(decoded_b0, oracle_b0)):
        if _bits(observed_value, "decoded RHS") != _bits(expected_value, "oracle RHS"):
            raise SnapshotError(f"snapshot RHS bits differ from oracle at index {index}")

    return {
        "status": "SYNTHETIC_SNAPSHOT_VERIFIED_AGAINST_INDEPENDENT_ORACLE",
        "scope": "SYNTHETIC_FIXTURE_ONLY",
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "source_value_sha256": oracle_sha,
        "n": n,
        "kl": kl,
        "ku": ku,
        "stored_matrix_records": metadata["stored_matrix_records"],
        "runtime_invocation_provenance": "NOT_ESTABLISHED",
    }


__all__ = ["canonical_oracle_sha256", "verify_capture_payload"]
