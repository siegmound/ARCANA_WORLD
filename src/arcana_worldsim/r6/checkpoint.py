"""Restart-complete metadata kept separate from query-retained history."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .identity import CheckpointId, content_hash, freeze_json, thaw_json


@dataclass(frozen=True, slots=True)
class CheckpointEnvelope:
    checkpoint_id: CheckpointId
    history_id: str
    branch_id: str
    time_key: str
    restart_state_ids: tuple[str, ...]
    retained_history_state_ids: tuple[str, ...]
    runtime_identity: Mapping[str, Any]
    configuration_sha256: str
    seed_lineage: Mapping[str, Any]
    upstream_dependency_ids: tuple[str, ...]
    validation_status: str
    restart_compatibility: Mapping[str, Any]
    schema_version: str = "ARCANA_R6_CHECKPOINT_V0"

    def __post_init__(self) -> None:
        object.__setattr__(self, "restart_state_ids", tuple(self.restart_state_ids))
        object.__setattr__(self, "retained_history_state_ids", tuple(self.retained_history_state_ids))
        object.__setattr__(self, "upstream_dependency_ids", tuple(self.upstream_dependency_ids))
        object.__setattr__(self, "runtime_identity", freeze_json(self.runtime_identity))
        object.__setattr__(self, "seed_lineage", freeze_json(self.seed_lineage))
        object.__setattr__(self, "restart_compatibility", freeze_json(self.restart_compatibility))

    @classmethod
    def create(cls, *, history_id: str, branch_id: str, time_key: str,
               restart_state_ids: tuple[str, ...], retained_history_state_ids: tuple[str, ...],
               runtime_identity: Mapping[str, Any], configuration: Mapping[str, Any],
               seed_lineage: Mapping[str, Any], upstream_dependency_ids: tuple[str, ...] = (),
               validation_status: str = "VALIDATED",
               restart_compatibility: Mapping[str, Any] | None = None) -> "CheckpointEnvelope":
        config_hash = content_hash(configuration)
        body = {"schema_version": "ARCANA_R6_CHECKPOINT_V0", "history_id": history_id,
                "branch_id": branch_id, "time_key": time_key,
                "restart_state_ids": list(restart_state_ids),
                "retained_history_state_ids": list(retained_history_state_ids),
                "runtime_identity": dict(runtime_identity),
                "configuration_sha256": config_hash, "seed_lineage": dict(seed_lineage),
                "upstream_dependency_ids": list(upstream_dependency_ids),
                "validation_status": validation_status,
                "restart_compatibility": dict(restart_compatibility or {})}
        return cls(CheckpointId.from_payload(body), history_id, branch_id, time_key,
                   tuple(restart_state_ids), tuple(retained_history_state_ids),
                   dict(runtime_identity), config_hash, dict(seed_lineage),
                   tuple(upstream_dependency_ids), validation_status,
                   dict(restart_compatibility or {}))

    def compatible_with(self, *, runtime_identity: Mapping[str, Any],
                        configuration_sha256: str, seed_lineage: Mapping[str, Any],
                        required_dependencies: tuple[str, ...],
                        restart_compatibility: Mapping[str, Any]) -> bool:
        return (dict(self.runtime_identity) == dict(runtime_identity)
                and self.configuration_sha256 == configuration_sha256
                and thaw_json(self.seed_lineage) == dict(seed_lineage)
                and tuple(self.upstream_dependency_ids) == tuple(required_dependencies)
                and thaw_json(self.restart_compatibility) == dict(restart_compatibility)
                and self.validation_status == "VALIDATED")

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "CheckpointEnvelope":
        if row.get("schema_version") != "ARCANA_R6_CHECKPOINT_V0":
            raise ValueError("checkpoint schema version mismatch")
        checkpoint = cls(
            CheckpointId(str(row["checkpoint_id"])), str(row["history_id"]),
            str(row["branch_id"]), str(row["time_key"]),
            tuple(row["restart_state_ids"]), tuple(row["retained_history_state_ids"]),
            dict(row["runtime_identity"]), str(row["configuration_sha256"]),
            dict(row["seed_lineage"]), tuple(row["upstream_dependency_ids"]),
            str(row["validation_status"]), dict(row["restart_compatibility"]),
            str(row["schema_version"]),
        )
        if len(checkpoint.configuration_sha256) != 64:
            raise ValueError("invalid checkpoint configuration digest")
        identity_body = {
            "schema_version": checkpoint.schema_version,
            "history_id": checkpoint.history_id, "branch_id": checkpoint.branch_id,
            "time_key": checkpoint.time_key,
            "restart_state_ids": list(checkpoint.restart_state_ids),
            "retained_history_state_ids": list(checkpoint.retained_history_state_ids),
            "runtime_identity": thaw_json(checkpoint.runtime_identity),
            "configuration_sha256": checkpoint.configuration_sha256,
            "seed_lineage": thaw_json(checkpoint.seed_lineage),
            "upstream_dependency_ids": list(checkpoint.upstream_dependency_ids),
            "validation_status": checkpoint.validation_status,
            "restart_compatibility": thaw_json(checkpoint.restart_compatibility),
        }
        if CheckpointId.from_payload(identity_body) != checkpoint.checkpoint_id:
            raise ValueError("checkpoint identity does not match serialized content")
        return checkpoint

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "checkpoint_id": str(self.checkpoint_id),
                "history_id": self.history_id, "branch_id": self.branch_id,
                "time_key": self.time_key, "restart_state_ids": list(self.restart_state_ids),
                "retained_history_state_ids": list(self.retained_history_state_ids),
                "runtime_identity": thaw_json(self.runtime_identity),
                "configuration_sha256": self.configuration_sha256,
                "seed_lineage": thaw_json(self.seed_lineage),
                "upstream_dependency_ids": list(self.upstream_dependency_ids),
                "validation_status": self.validation_status,
                "restart_compatibility": thaw_json(self.restart_compatibility)}
