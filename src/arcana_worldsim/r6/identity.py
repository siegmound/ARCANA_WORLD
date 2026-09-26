"""Deterministic, path-independent identities for R6 records."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import Any, ClassVar, Mapping
import json
import math
import re
from pathlib import PurePosixPath


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
