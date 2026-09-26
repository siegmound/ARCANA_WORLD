"""Restart-complete metadata kept separate from query-retained history."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .identity import BranchId, CheckpointId, content_hash, freeze_json, thaw_json

CHECKPOINT_SCHEMA = "ARCANA_R6_CHECKPOINT_V1"
LEGACY_CHECKPOINT_SCHEMA = "ARCANA_R6_CHECKPOINT_V0"


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
    schema_version: str = CHECKPOINT_SCHEMA
    parent_checkpoint_id: str | None = None
    authority_input_refs: tuple[str, ...] = ()
    provider_manifest_refs: tuple[str, ...] = ()
    engine_versions: Mapping[str, Any] = field(default_factory=dict)
    output_manifest: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "restart_state_ids", tuple(self.restart_state_ids))
        object.__setattr__(self, "retained_history_state_ids", tuple(self.retained_history_state_ids))
        object.__setattr__(self, "upstream_dependency_ids", tuple(self.upstream_dependency_ids))
        object.__setattr__(self, "runtime_identity", freeze_json(self.runtime_identity))
        object.__setattr__(self, "seed_lineage", freeze_json(self.seed_lineage))
        object.__setattr__(self, "restart_compatibility", freeze_json(self.restart_compatibility))
        object.__setattr__(self, "authority_input_refs", tuple(self.authority_input_refs))
        object.__setattr__(self, "provider_manifest_refs", tuple(self.provider_manifest_refs))
        object.__setattr__(self, "engine_versions", freeze_json(self.engine_versions))
        object.__setattr__(self, "output_manifest", freeze_json(self.output_manifest))

    @classmethod
    def create(cls, *, history_id: str, branch_id: str, time_key: str,
               restart_state_ids: tuple[str, ...], retained_history_state_ids: tuple[str, ...],
               runtime_identity: Mapping[str, Any], configuration: Mapping[str, Any],
               seed_lineage: Mapping[str, Any], upstream_dependency_ids: tuple[str, ...] = (),
               validation_status: str = "VALIDATED",
               restart_compatibility: Mapping[str, Any] | None = None,
               parent_checkpoint_id: str | None = None,
               authority_input_refs: tuple[str, ...] = (),
               provider_manifest_refs: tuple[str, ...] = (),
               engine_versions: Mapping[str, Any] | None = None,
               output_manifest: Mapping[str, Any] | None = None) -> "CheckpointEnvelope":
        config_hash = content_hash(configuration)
        body = {"schema_version": CHECKPOINT_SCHEMA, "history_id": history_id,
                "branch_id": branch_id, "time_key": time_key,
                "restart_state_ids": list(restart_state_ids),
                "retained_history_state_ids": list(retained_history_state_ids),
                "runtime_identity": dict(runtime_identity),
                "configuration_sha256": config_hash, "seed_lineage": dict(seed_lineage),
                "upstream_dependency_ids": list(upstream_dependency_ids),
                "validation_status": validation_status,
                "restart_compatibility": dict(restart_compatibility or {}),
                "parent_checkpoint_id": parent_checkpoint_id,
                "authority_input_refs": list(authority_input_refs),
                "provider_manifest_refs": list(provider_manifest_refs),
                "engine_versions": dict(engine_versions or {}),
                "output_manifest": dict(output_manifest or {})}
        return cls(CheckpointId.from_payload(body), history_id, branch_id, time_key,
                   tuple(restart_state_ids), tuple(retained_history_state_ids),
                   dict(runtime_identity), config_hash, dict(seed_lineage),
                   tuple(upstream_dependency_ids), validation_status,
                   dict(restart_compatibility or {}), CHECKPOINT_SCHEMA,
                   parent_checkpoint_id, tuple(authority_input_refs),
                   tuple(provider_manifest_refs), dict(engine_versions or {}),
                   dict(output_manifest or {}))

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
        if row.get("schema_version") not in {CHECKPOINT_SCHEMA, LEGACY_CHECKPOINT_SCHEMA}:
            raise ValueError("checkpoint schema version mismatch")
        checkpoint = cls(
            CheckpointId(str(row["checkpoint_id"])), str(row["history_id"]),
            str(row["branch_id"]), str(row["time_key"]),
            tuple(row["restart_state_ids"]), tuple(row["retained_history_state_ids"]),
            dict(row["runtime_identity"]), str(row["configuration_sha256"]),
            dict(row["seed_lineage"]), tuple(row["upstream_dependency_ids"]),
            str(row["validation_status"]), dict(row["restart_compatibility"]),
            str(row["schema_version"]),
            row.get("parent_checkpoint_id"), tuple(row.get("authority_input_refs", ())),
            tuple(row.get("provider_manifest_refs", ())), row.get("engine_versions", {}),
            row.get("output_manifest", {}),
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
        if checkpoint.schema_version == CHECKPOINT_SCHEMA:
            identity_body.update({"parent_checkpoint_id": checkpoint.parent_checkpoint_id,
                "authority_input_refs": list(checkpoint.authority_input_refs),
                "provider_manifest_refs": list(checkpoint.provider_manifest_refs),
                "engine_versions": thaw_json(checkpoint.engine_versions),
                "output_manifest": thaw_json(checkpoint.output_manifest)})
        if CheckpointId.from_payload(identity_body) != checkpoint.checkpoint_id:
            raise ValueError("checkpoint identity does not match serialized content")
        return checkpoint

    def to_dict(self) -> dict[str, Any]:
        result = {"schema_version": self.schema_version, "checkpoint_id": str(self.checkpoint_id),
                "history_id": self.history_id, "branch_id": self.branch_id,
                "time_key": self.time_key, "restart_state_ids": list(self.restart_state_ids),
                "retained_history_state_ids": list(self.retained_history_state_ids),
                "runtime_identity": thaw_json(self.runtime_identity),
                "configuration_sha256": self.configuration_sha256,
                "seed_lineage": thaw_json(self.seed_lineage),
                "upstream_dependency_ids": list(self.upstream_dependency_ids),
                "validation_status": self.validation_status,
                "restart_compatibility": thaw_json(self.restart_compatibility)}
        if self.schema_version == CHECKPOINT_SCHEMA:
            result.update({"parent_checkpoint_id": self.parent_checkpoint_id,
                "authority_input_refs": list(self.authority_input_refs),
                "provider_manifest_refs": list(self.provider_manifest_refs),
                "engine_versions": thaw_json(self.engine_versions),
                "output_manifest": thaw_json(self.output_manifest)})
        return result


@dataclass(frozen=True, slots=True)
class RefinementBranchEnvelope:
    branch_id: BranchId
    history_id: str
    parent_branch_id: str
    base_history_id: str
    refinement_anchor_id: str
    region_id: str
    time_interval: tuple[str, str]
    requested_domains: tuple[str, ...]
    requested_resolution: str
    parent_boundary_conditions: Mapping[str, Any]
    provenance_refs: tuple[str, ...]
    output_state_ids: tuple[str, ...] = ()
    validation_status: str = "NOT_VALIDATED"
    schema_version: str = "ARCANA_R6_REFINEMENT_BRANCH_V0"

    def __post_init__(self) -> None:
        if len(self.time_interval) != 2 or not all(self.time_interval):
            raise ValueError("refinement time interval requires two support keys")
        if not self.region_id or not self.requested_resolution:
            raise ValueError("refinement region and resolution are required")
        object.__setattr__(self, "time_interval", tuple(self.time_interval))
        object.__setattr__(self, "requested_domains", tuple(sorted(set(self.requested_domains))))
        object.__setattr__(self, "parent_boundary_conditions", freeze_json(self.parent_boundary_conditions))
        object.__setattr__(self, "provenance_refs", tuple(self.provenance_refs))
        object.__setattr__(self, "output_state_ids", tuple(self.output_state_ids))
        if BranchId.from_payload(self._identity_body()) != self.branch_id:
            raise ValueError("refinement branch identity does not match content")

    def _identity_body(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "history_id": self.history_id,
            "parent_branch_id": self.parent_branch_id, "base_history_id": self.base_history_id,
            "refinement_anchor_id": self.refinement_anchor_id, "region_id": self.region_id,
            "time_interval": list(self.time_interval), "requested_domains": list(self.requested_domains),
            "requested_resolution": self.requested_resolution,
            "parent_boundary_conditions": thaw_json(self.parent_boundary_conditions),
            "provenance_refs": list(self.provenance_refs),
            "output_state_ids": list(self.output_state_ids),
            "validation_status": self.validation_status}

    @classmethod
    def create(cls, *, history_id: str, parent_branch_id: str, base_history_id: str,
               refinement_anchor_id: str, region_id: str, time_interval: tuple[str, str],
               requested_domains: tuple[str, ...], requested_resolution: str,
               parent_boundary_conditions: Mapping[str, Any] | None = None,
               provenance_refs: tuple[str, ...] = (),
               output_state_ids: tuple[str, ...] = (),
               validation_status: str = "NOT_VALIDATED") -> "RefinementBranchEnvelope":
        body = {"schema_version": "ARCANA_R6_REFINEMENT_BRANCH_V0", "history_id": history_id,
            "parent_branch_id": parent_branch_id, "base_history_id": base_history_id,
            "refinement_anchor_id": refinement_anchor_id, "region_id": region_id,
            "time_interval": list(time_interval), "requested_domains": sorted(set(requested_domains)),
            "requested_resolution": requested_resolution,
            "parent_boundary_conditions": dict(parent_boundary_conditions or {}),
            "provenance_refs": list(provenance_refs),
            "output_state_ids": list(output_state_ids), "validation_status": validation_status}
        return cls(BranchId.from_payload(body), history_id, parent_branch_id, base_history_id,
            refinement_anchor_id, region_id, time_interval, requested_domains,
            requested_resolution, parent_boundary_conditions or {}, provenance_refs,
            output_state_ids, validation_status)

    def to_dict(self) -> dict[str, Any]:
        return {"branch_id": str(self.branch_id), **self._identity_body()}

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "RefinementBranchEnvelope":
        return cls(BranchId(str(row["branch_id"])), str(row["history_id"]),
            str(row["parent_branch_id"]), str(row["base_history_id"]),
            str(row["refinement_anchor_id"]), str(row["region_id"]),
            tuple(row["time_interval"]), tuple(row["requested_domains"]),
            str(row["requested_resolution"]), row["parent_boundary_conditions"],
            tuple(row["provenance_refs"]), tuple(row.get("output_state_ids", ())),
            str(row["validation_status"]),
            str(row["schema_version"]))
