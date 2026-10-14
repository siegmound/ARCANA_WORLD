"""Read-only R4 technical input attestation; no store writes or kernel execution.

Issuing a derived VALIDATED record qualifies only technical input closure in
the currently checked runtime. It does not qualify Fair or authorize replay.
"""
from dataclasses import dataclass, replace
from pathlib import Path

from arcana_worldsim.r6.checkpoint import CheckpointEnvelope
from arcana_worldsim.r6.identity import CheckpointId, ReplayRecipeId, content_hash
from arcana_worldsim.r6.replay import ReplayRecipe
from arcana_worldsim.r6.store import HistoryStore
from r6_int2c_replay_adapter import (
    DeterministicKernelAdapter, ReplayBindingError, ReplayPreparation, _text_hash, prepare_r4,
)

SCOPE = "TECHNICAL_ENGINEERING_INPUT_CLOSURE_ONLY"


@dataclass(frozen=True)
class TechnicalAttestation:
    original: ReplayPreparation
    prepared: ReplayPreparation
    inventory: tuple[tuple[str, str, str], ...]

    @property
    def records(self):
        return (*self.original.records, self.prepared.checkpoint, self.prepared.recipe)


def attest_r4(repository_root: Path, bundle: Path) -> TechnicalAttestation:
    """Authenticate original inputs afresh, then issue NEW typed technical records.

    No caller-supplied preparation or digest can substitute for the pinned R4
    manifest/historical kernel checks in prepare_r4. Runtime mismatch rejects
    issuance before any VALIDATED record is returned.
    """
    original = prepare_r4(repository_root, bundle)
    DeterministicKernelAdapter(original)._verify_runtime()
    inventory = tuple((bucket, key, content_hash(body)) for bucket, key, body in
                      (HistoryStore._transaction_record(x) for x in original.records))
    if len({key for _, key, _ in inventory}) != len(inventory):
        raise ReplayBindingError("DUPLICATE_TECHNICAL_RECORD")
    deps = {str(original.initial.state_id), str(original.forcing.forcing_id),
            str(original.provenance.record_id)}
    cp, recipe = original.checkpoint, original.recipe
    if (set(cp.upstream_dependency_ids) != deps
            or set(recipe.upstream_dependency_ids) != deps
            or recipe.base_checkpoint_id != str(cp.checkpoint_id)
            or recipe.runtime_identity != cp.runtime_identity
            or recipe.configuration_sha256 != cp.configuration_sha256
            or cp.restart_compatibility.get("validation_scope") != SCOPE):
        raise ReplayBindingError("TECHNICAL_DEPENDENCY_CLOSURE_INCOMPLETE")
    row = cp.to_dict()
    row.pop("checkpoint_id")
    row.update(validation_status="VALIDATED", parent_checkpoint_id=str(cp.checkpoint_id))
    row["output_manifest"] = {
        **row["output_manifest"], "technical_attestation": {
            "scope": SCOPE, "record_inventory_sha256": content_hash(inventory),
            "issuer_canonical_text_sha256": _text_hash(Path(__file__).read_bytes()),
            "runtime_versions_checked": True, "historical_runtime_binaries_verified": False,
            "atomic_store_publication_verified": False, "numerical_replay_executed": False,
            "scientific_promotion_authorized": False, "canonical_publication": False,
        }}
    row["checkpoint_id"] = str(CheckpointId.from_payload(row))
    checked = CheckpointEnvelope.from_dict(row)
    row = recipe.to_dict()
    row.pop("recipe_id")
    row["base_checkpoint_id"] = str(checked.checkpoint_id)
    row["recipe_id"] = str(ReplayRecipeId.from_payload(row))
    derived = ReplayRecipe.from_dict(row)
    for record in (checked, derived):
        HistoryStore._transaction_record(record)
    return TechnicalAttestation(original, replace(original, checkpoint=checked, recipe=derived),
                                inventory)
