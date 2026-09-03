from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence
import json

import numpy as np


class EngineRole(str, Enum):
    REFERENCE_ORACLE = "REFERENCE_ORACLE"
    SECONDARY_ORACLE = "SECONDARY_ORACLE"
    CALIBRATED_PROVIDER_CANDIDATE = "CALIBRATED_PROVIDER_CANDIDATE"
    REGIONAL_BACKEND_CANDIDATE = "REGIONAL_BACKEND_CANDIDATE"
    SPECIALIST_BACKEND_CANDIDATE = "SPECIALIST_BACKEND_CANDIDATE"


@dataclass(frozen=True)
class EngineDescriptor:
    name: str
    version: str
    role: EngineRole
    execution_mode: str
    license_id: str | None = None
    canonical_write_allowed: bool = False
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.canonical_write_allowed:
            raise ValueError("External scientific engines may not write ARCANA canonical state directly")


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        raise TypeError("Arrays must be stored in the arrays payload, not JSON metadata")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"Unsupported metadata type: {type(value)!r}")


def _freeze_mapping(mapping: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not mapping:
        return MappingProxyType({})
    return MappingProxyType({str(k): _jsonable(v) for k, v in mapping.items()})


def _freeze_arrays(arrays: Mapping[str, np.ndarray] | None) -> Mapping[str, np.ndarray]:
    out: dict[str, np.ndarray] = {}
    for key, value in (arrays or {}).items():
        arr = np.array(value, copy=True)
        arr.setflags(write=False)
        out[str(key)] = arr
    return MappingProxyType(out)


def _hash_json(obj: Mapping[str, Any]) -> bytes:
    return json.dumps(_jsonable(obj), sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _update_hash_with_arrays(h, arrays: Mapping[str, np.ndarray]) -> None:
    for name in sorted(arrays):
        arr = np.asarray(arrays[name])
        h.update(name.encode("utf-8"))
        h.update(str(arr.dtype).encode("ascii"))
        h.update(json.dumps(list(arr.shape)).encode("ascii"))
        h.update(np.ascontiguousarray(arr).tobytes(order="C"))


@dataclass(frozen=True)
class ScientificExperiment:
    experiment_id: str
    arcana_stage: str
    age_ma: float
    engine: EngineDescriptor
    source_state_sha256: str
    random_seed: int
    replicate_id: int = 0
    spatial_domain: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    arrays: Mapping[str, np.ndarray] = field(default_factory=dict)
    assumptions: tuple[str, ...] = ()
    requested_outputs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.experiment_id:
            raise ValueError("experiment_id is required")
        if len(self.source_state_sha256) != 64:
            raise ValueError("source_state_sha256 must be a SHA-256 hex digest")
        object.__setattr__(self, "spatial_domain", _freeze_mapping(self.spatial_domain))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))
        object.__setattr__(self, "arrays", _freeze_arrays(self.arrays))
        object.__setattr__(self, "assumptions", tuple(str(x) for x in self.assumptions))
        object.__setattr__(self, "requested_outputs", tuple(str(x) for x in self.requested_outputs))

    @property
    def semantic_sha256(self) -> str:
        h = sha256()
        h.update(_hash_json({
            "experiment_id": self.experiment_id,
            "arcana_stage": self.arcana_stage,
            "age_ma": self.age_ma,
            "engine": {
                "name": self.engine.name,
                "version": self.engine.version,
                "role": self.engine.role.value,
                "execution_mode": self.engine.execution_mode,
                "license_id": self.engine.license_id,
                "canonical_write_allowed": self.engine.canonical_write_allowed,
                "notes": self.engine.notes,
            },
            "source_state_sha256": self.source_state_sha256,
            "random_seed": self.random_seed,
            "replicate_id": self.replicate_id,
            "spatial_domain": self.spatial_domain,
            "metadata": self.metadata,
            "assumptions": self.assumptions,
            "requested_outputs": self.requested_outputs,
        }))
        _update_hash_with_arrays(h, self.arrays)
        return h.hexdigest()

    def manifest(self) -> dict[str, Any]:
        return {
            "schema": "ARCANA_SCIENTIFIC_EXPERIMENT_V1",
            "experiment_id": self.experiment_id,
            "semantic_sha256": self.semantic_sha256,
            "arcana_stage": self.arcana_stage,
            "age_ma": float(self.age_ma),
            "source_state_sha256": self.source_state_sha256,
            "engine": {
                "name": self.engine.name,
                "version": self.engine.version,
                "role": self.engine.role.value,
                "execution_mode": self.engine.execution_mode,
                "license_id": self.engine.license_id,
                "canonical_write_allowed": False,
                "notes": list(self.engine.notes),
            },
            "random_seed": int(self.random_seed),
            "replicate_id": int(self.replicate_id),
            "spatial_domain": _jsonable(self.spatial_domain),
            "metadata": _jsonable(self.metadata),
            "assumptions": list(self.assumptions),
            "requested_outputs": list(self.requested_outputs),
            "arrays": {
                k: {"shape": list(v.shape), "dtype": str(v.dtype)} for k, v in sorted(self.arrays.items())
            },
        }


@dataclass(frozen=True)
class ScientificEvidenceBundle:
    experiment_sha256: str
    engine: EngineDescriptor
    engine_run_id: str
    status: str
    metrics: Mapping[str, Any] = field(default_factory=dict)
    arrays: Mapping[str, np.ndarray] = field(default_factory=dict)
    assumptions: tuple[str, ...] = ()
    unsupported_mappings: tuple[str, ...] = ()
    stdout_sha256: str | None = None
    stderr_sha256: str | None = None

    def __post_init__(self) -> None:
        if len(self.experiment_sha256) != 64:
            raise ValueError("experiment_sha256 must be SHA-256")
        object.__setattr__(self, "metrics", _freeze_mapping(self.metrics))
        object.__setattr__(self, "arrays", _freeze_arrays(self.arrays))
        object.__setattr__(self, "assumptions", tuple(str(x) for x in self.assumptions))
        object.__setattr__(self, "unsupported_mappings", tuple(str(x) for x in self.unsupported_mappings))

    @property
    def semantic_sha256(self) -> str:
        h = sha256()
        h.update(_hash_json({
            "experiment_sha256": self.experiment_sha256,
            "engine": {"name": self.engine.name, "version": self.engine.version, "role": self.engine.role.value},
            "engine_run_id": self.engine_run_id,
            "status": self.status,
            "metrics": self.metrics,
            "assumptions": self.assumptions,
            "unsupported_mappings": self.unsupported_mappings,
            "stdout_sha256": self.stdout_sha256,
            "stderr_sha256": self.stderr_sha256,
        }))
        _update_hash_with_arrays(h, self.arrays)
        return h.hexdigest()


@dataclass(frozen=True)
class CalibrationCandidate:
    candidate_id: str
    evidence_sha256: tuple[str, ...]
    proposed_change: Mapping[str, Any]
    rationale: str
    status: str = "REVIEW_REQUIRED"

    def __post_init__(self) -> None:
        if self.status != "REVIEW_REQUIRED":
            raise ValueError("Scientific-engine evidence cannot auto-promote canonical changes")
        object.__setattr__(self, "evidence_sha256", tuple(self.evidence_sha256))
        object.__setattr__(self, "proposed_change", _freeze_mapping(self.proposed_change))
