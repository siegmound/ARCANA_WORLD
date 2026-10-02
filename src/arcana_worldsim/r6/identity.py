"""Deterministic, path-independent identities for R6 records."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, BinaryIO, ClassVar, Mapping
import json
import math
import re


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def content_hash(value: Any) -> str:
    return sha256(canonical_bytes(value)).hexdigest()


def freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): freeze_json(v) for k, v in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(freeze_json(v) for v in value)
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite numbers are not valid R6 metadata")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"value is not JSON-compatible: {type(value)!r}")


def thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): thaw_json(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [thaw_json(v) for v in value]
    return value


def _reject_machine_paths(value: Any, where: str = "identity") -> None:
    if isinstance(value, str):
        if re.match(r"^[A-Za-z]:[\\/]", value) or value.startswith("\\\\"):
            raise ValueError(f"{where} must not contain an absolute machine path")
        if value.startswith("/") and "://" not in value and value.count("/") >= 2:
            if PurePosixPath(value).is_absolute():
                raise ValueError(f"{where} must not contain an absolute machine path")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_machine_paths(key, where)
            _reject_machine_paths(item, where)
    elif isinstance(value, (tuple, list)):
        for item in value:
            _reject_machine_paths(item, where)


@dataclass(frozen=True, slots=True)
class DeterministicId:
    value: str
    PREFIX: ClassVar[str] = "r6id"

    def __post_init__(self) -> None:
        if not re.fullmatch(rf"{re.escape(self.PREFIX)}_[0-9a-f]{{64}}", self.value):
            raise ValueError(f"invalid {self.PREFIX} identity")

    @classmethod
    def from_payload(cls, payload: Any) -> "DeterministicId":
        _reject_machine_paths(payload)
        return cls(f"{cls.PREFIX}_{content_hash(payload)}")

    def __str__(self) -> str:
        return self.value


class R6RunId(DeterministicId):
    PREFIX = "r6run"


class HistoryId(DeterministicId):
    PREFIX = "r6hist"


class BranchId(DeterministicId):
    PREFIX = "r6branch"


class DomainStateId(DeterministicId):
    PREFIX = "r6state"


class CheckpointId(DeterministicId):
    PREFIX = "r6checkpoint"


class EventId(DeterministicId):
    PREFIX = "r6event"


class ProviderBindingId(DeterministicId):
    PREFIX = "r6provider"


class ProvenanceRecordId(DeterministicId):
    PREFIX = "r6prov"


class ForcingId(DeterministicId):
    PREFIX = "r6forcing"


class ReplayRecipeId(DeterministicId):
    PREFIX = "r6recipe"


@dataclass(frozen=True, slots=True)
class PayloadIdentity:
    """Content identity for payload bytes, separate from semantic record IDs."""

    algorithm: str
    digest: str

    def __post_init__(self) -> None:
        if self.algorithm != "sha256" or not re.fullmatch(r"[0-9a-f]{64}", self.digest):
            raise ValueError("payload identity requires a lowercase SHA-256 digest")

    @classmethod
    def from_bytes(cls, data: bytes) -> "PayloadIdentity":
        return cls("sha256", sha256(data).hexdigest())

    def to_dict(self) -> dict[str, str]:
        return {"algorithm": self.algorithm, "digest": self.digest}


@dataclass(frozen=True, slots=True)
class PayloadReference:
    """Backend-neutral reference; legacy opaque references remain representable."""

    reference: str
    identity: PayloadIdentity | None = None
    locator: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.reference, str) or not self.reference:
            raise ValueError("payload reference must be a non-empty string")

    @classmethod
    def parse(cls, reference: str | "PayloadReference") -> "PayloadReference":
        if isinstance(reference, cls):
            return reference
        if not isinstance(reference, str) or not reference:
            raise ValueError("payload reference must be a non-empty string")
        match = re.fullmatch(r"sha256:([0-9a-f]{64})", reference)
        if match:
            return cls(reference, PayloadIdentity("sha256", match.group(1)))
        match = re.fullmatch(r"payload:sha256:([0-9a-f]{64})", reference)
        if match:
            return cls(reference, PayloadIdentity("sha256", match.group(1)), "payload:")
        match = re.fullmatch(r"payload://sha256/([0-9a-f]{64})(#[^\s]+)?", reference)
        if match:
            return cls(reference, PayloadIdentity("sha256", match.group(1)),
                       f"payload://sha256/{match.group(1)}{match.group(2) or ''}")
        return cls(reference, None, reference)

    def to_legacy_string(self) -> str:
        return self.reference


class PayloadIntegrityError(ValueError):
    """Raised when payload bytes do not match their declared content identity."""


def verify_payload(reference: str | PayloadReference,
                   source: bytes | bytearray | memoryview | Path | str | BinaryIO) -> PayloadIdentity:
    """Explicitly verify available bytes against a SHA-256 payload reference."""
    payload_ref = PayloadReference.parse(reference)
    if payload_ref.identity is None:
        raise PayloadIntegrityError("payload reference has no verifiable content identity")
    try:
        if isinstance(source, (bytes, bytearray, memoryview)):
            data = bytes(source)
        elif isinstance(source, (Path, str)):
            data = Path(source).read_bytes()
        else:
            data = source.read()
            if not isinstance(data, bytes):
                raise TypeError("payload stream must return bytes")
    except (OSError, TypeError) as exc:
        raise PayloadIntegrityError("payload source could not be read") from exc
    actual = PayloadIdentity.from_bytes(data)
    if actual != payload_ref.identity:
        raise PayloadIntegrityError("payload content digest does not match reference")
    return actual
