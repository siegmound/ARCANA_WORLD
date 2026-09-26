"""Deterministic immutable identity envelope for a governed R6 bootstrap."""

from __future__ import annotations

from typing import Any, Mapping

from .identity import BranchId, HistoryId, R6RunId, content_hash


REQUIRED = {
    "canonical_initial_binding_ref", "canonical_initial_binding_status",
    "canonical_law_refs", "cha_contract_refs", "provider_refs",
    "dependency_sha256", "engine_registry", "seed_ensemble_lineage",
    "grid_ref", "time_ref", "runtime_environment_identity",
    "known_gaps", "unknown_policy", "repository_identity",
}


def create_bootstrap_manifest(inputs: Mapping[str, Any]) -> dict[str, Any]:
    missing = REQUIRED - set(inputs)
    if missing:
        raise ValueError(f"bootstrap identity missing fields: {sorted(missing)}")
    if not isinstance(inputs["dependency_sha256"], Mapping):
        raise ValueError("dependency_sha256 must be a source-to-digest mapping")
    for name, digest in inputs["dependency_sha256"].items():
        if len(str(digest)) != 64 or any(c not in "0123456789abcdef" for c in str(digest)):
            raise ValueError(f"invalid dependency SHA-256 for {name}")
    identity = {"schema": "ARCANA_R6_BOOTSTRAP_IDENTITY_V0",
                "inputs": dict(inputs)}
    digest = content_hash(identity)
    return {
        "schema_version": "ARCANA_R6_BOOTSTRAP_MANIFEST_V0",
        "bootstrap_identity_sha256": digest,
        "run_id": str(R6RunId.from_payload(identity)),
        "history_id": str(HistoryId.from_payload(identity)),
        "branch_id": str(BranchId.from_payload({"bootstrap_identity_sha256": digest,
                                                 "branch_role": "canonical-mainline"})),
        "identity": identity,
        "canonical_initial_state_bound": inputs["canonical_initial_binding_status"] == "BOUND",
        "scientific_execution_authorized": False,
    }
