"""Prepare a closed, noncanonical R4 B0 replay; preparation never runs the kernel.

The derived checkpoint remains CANDIDATE_NONCANONICAL. A later, separately
reviewed technical validation must issue a new VALIDATED checkpoint/recipe
before B0 execute_replay can call the adapter. No store or execution CLI exists.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import math
import os
from pathlib import Path
import platform
import subprocess
from typing import Any, Mapping

import numpy as np

from arcana_worldsim.r6 import functional_development as kernel
from arcana_worldsim.r6.checkpoint import CheckpointEnvelope
from arcana_worldsim.r6.forcing import ForcingRecord
from arcana_worldsim.r6.identity import content_hash, freeze_json, thaw_json
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.replay import ReplayExecutionOutput, ReplayRecipe, ResolvedReplayInputs
from arcana_worldsim.r6.state import DomainStateEnvelope, TimeSupport
from r6_int1a_retention_audit import (
    EXPECTED_SOURCE_COMMIT, _json_bytes, load_verified_bundle, validate_r4_provenance,
)

ADAPTER_ID = "ARCANA_R6_INT2C_TF2B_KERNEL_REPLAY_V1"
KERNEL_PATH = "src/arcana_worldsim/r6/functional_development.py"
KERNEL_SHA256 = "bddedfd7439b328951389012b2af371d106d042018ac4be928325a6395666542"
DECISION = "INT2C_EXECUTABLE_REPLAY_BINDING_CODE_READY__NUMERICAL_VALIDATION_PENDING"


class ReplayBindingError(ValueError):
    """Declared inputs do not close the prepared engineering replay."""


def _text_hash(raw: bytes) -> str:
    return hashlib.sha256(raw.decode("utf-8").replace("\r\n", "\n")
                          .replace("\r", "\n").encode("utf-8")).hexdigest()


def verify_kernel_source(repository_root: Path) -> dict[str, Any]:
    """Compare loaded/current bytes to the pinned historical Git blob, read-only."""
    root = Path(os.path.abspath(repository_root))
    if os.path.normcase(os.path.abspath(kernel.__file__)) != os.path.normcase(str(root / KERNEL_PATH)):
        raise ReplayBindingError("LOADED_KERNEL_SOURCE_PATH_MISMATCH")
    env = dict(os.environ)
    for name in ("GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        env.pop(name, None)
    historical = subprocess.run(
        ["git", "show", f"{EXPECTED_SOURCE_COMMIT}:{KERNEL_PATH}"], cwd=root,
        env=env, capture_output=True, check=False, timeout=15,
    )
    if historical.returncode or _text_hash(historical.stdout) != KERNEL_SHA256:
        raise ReplayBindingError("HISTORICAL_KERNEL_IDENTITY_UNVERIFIED")
    if _text_hash((root / KERNEL_PATH).read_bytes()) != KERNEL_SHA256:
        raise ReplayBindingError("CURRENT_KERNEL_DIFFERS_FROM_HISTORICAL_SOURCE")
    return {"execution_commit": EXPECTED_SOURCE_COMMIT,
            "kernel_path": KERNEL_PATH, "kernel_canonical_text_sha256": KERNEL_SHA256,
            "adapter_canonical_text_sha256": _text_hash(Path(__file__).read_bytes()),
            "python": "3.12.10", "numpy": "2.3.5",
            "scope": "VERIFIED_R4_ENGINEERING_INPUTS_ONLY"}


def _positive(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReplayBindingError(f"INVALID_NUMERIC_TYPE:{name}")
    if not math.isfinite(value) or value <= 0:
        raise ReplayBindingError(f"FINITE_POSITIVE_VALUE_REQUIRED:{name}")
    return float(value)


def _restore(payload: Mapping[str, Any]) -> kernel.ReducedState:
    try:
        numeric = [payload[name] for name in (
            "time_s", "initial_width_m", "width_m", "initial_crust_m", "initial_lithosphere_m",
            "crust_m", "lithosphere_m", "beta", "accumulated_strain", "crust_fraction",
            "surface_temperature_k", "base_temperature_k")]
        numeric.extend(payload["material_coordinate"])
        numeric.extend(payload["temperature_k"])
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x)
               for x in numeric):
            raise ReplayBindingError("INVALID_REDUCED_NUMERIC_VALUE")
        state = kernel.state_from_payload(payload)
        if state.payload() != thaw_json(payload):
            raise ReplayBindingError("INCOMPLETE_OR_INCONSISTENT_REDUCED_PAYLOAD")
        if state.time_s != 0.0 or state.width_m != state.initial_width_m:
            raise ReplayBindingError("INITIAL_T0_STATE_REQUIRED")
        if state.material_coordinate[0] != 0.0 or state.material_coordinate[-1] != 1.0:
            raise ReplayBindingError("MATERIAL_COORDINATE_ENDPOINTS_INVALID")
        for material in state.materials:
            for name in ("k_w_m_k", "rho_kg_m3", "cp_j_kg_k"):
                _positive(getattr(material, name), name)
            if (not isinstance(material.role_id, str) or not material.role_id
                    or isinstance(material.radiogenic_w_m3, bool)
                    or not math.isfinite(material.radiogenic_w_m3)
                    or material.radiogenic_w_m3 < 0):
                raise ReplayBindingError("INVALID_MATERIAL_ROLE_OR_SOURCE")
        return state
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise ReplayBindingError(f"INITIAL_STATE_INVALID:{exc}") from exc


@dataclass(frozen=True)
class ReplayPreparation:
    initial: DomainStateEnvelope
    expected: DomainStateEnvelope
    forcing: ForcingRecord
    checkpoint: CheckpointEnvelope
    recipe: ReplayRecipe
    provenance: ProvenanceRecord
    configuration: Mapping[str, Any]
    source_identity: Mapping[str, Any]
    original_checkpoint: CheckpointEnvelope
    original_recipe: ReplayRecipe
    original_candidate_checkpoint: CheckpointEnvelope | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "configuration", freeze_json(self.configuration))
        object.__setattr__(self, "source_identity", freeze_json(self.source_identity))

    @property
    def records(self) -> tuple[Any, ...]:
        originals = (self.original_checkpoint, self.original_recipe)
        if self.original_candidate_checkpoint is not None:
            originals += (self.original_candidate_checkpoint,)
        return (*originals, self.initial, self.expected, self.forcing, self.provenance,
                self.checkpoint, self.recipe)


def _bind_candidate(initial: DomainStateEnvelope, expected: DomainStateEnvelope,
                    forcing: ForcingRecord, old_checkpoint: CheckpointEnvelope,
                    old_recipe: ReplayRecipe, configuration: Mapping[str, Any],
                    source_identity: Mapping[str, Any], artifact_hashes: Mapping[str, str]
                    ) -> ReplayPreparation:
    """Pure typed construction; this internal function does not authenticate files."""
    value = thaw_json(initial.value)
    supports = tuple(value["support_ids"])
    if (value["pair"] != [5, 11] or len(supports) != 2 or len(set(supports)) != 2
            or initial.spatial_support.cell_ids != supports
            or tuple(forcing.value["support_ids"]) != supports
            or forcing.spatial_support != initial.spatial_support
            or (forcing.history_id, forcing.branch_id, forcing.domain) !=
               (initial.history_id, initial.branch_id, initial.domain)
            or expected.spatial_support != initial.spatial_support
            or (expected.history_id, expected.branch_id, expected.domain) !=
               (initial.history_id, initial.branch_id, initial.domain)
            or initial.applicability.get("canonical_publication") is not False
            or expected.applicability.get("canonical_publication") is not False):
        raise ReplayBindingError("SCOPE_OR_SUPPORT_MISMATCH")
    if (initial.time_support.time_key != "210Ma" or forcing.time_support != initial.time_support
            or forcing.forcing_kind != "FROZEN_INSTANTANEOUS_ENGINEERING_DRIVER"
            or forcing.value["frame"] != "T_F2B_SELECTED_SECTION_NORMAL_PLATE_5_TO_11"
            or forcing.payload_ref is not None):
        raise ReplayBindingError("FORCING_OR_INITIAL_FRAME_MISMATCH")
    duration = _positive(configuration["duration_seconds"], "duration_seconds")
    velocity = _positive(forcing.value["signed_Ux_m_per_year"], "forcing_Ux")
    fraction = _positive(configuration["numerical_configuration"][
        "maximum_kinematic_fraction_per_substep"], "substep_fraction")
    if (fraction > 0.05 or duration > 1000 * kernel.SECONDS_PER_YEAR
            or configuration["signed_Ux_m_per_year"] != velocity
            or configuration["numerical_configuration"]["duration_years"] !=
               duration / kernel.SECONDS_PER_YEAR
            or configuration["numerical_configuration"]["kernel"] !=
               "functional_development.pure_shear_thermal_step"):
        raise ReplayBindingError("NUMERICAL_CONFIGURATION_MISMATCH")
    payloads = value["side_states"]
    if len(payloads) != 2:
        raise ReplayBindingError("INITIAL_SIDE_CARDINALITY_MISMATCH")
    for payload in payloads:
        _restore(payload)
    if (old_checkpoint.validation_status != "CANDIDATE_NONCANONICAL"
            or (old_checkpoint.history_id, old_checkpoint.branch_id) !=
               (initial.history_id, initial.branch_id)
            or (old_recipe.history_id, old_recipe.branch_id) !=
               (initial.history_id, initial.branch_id)
            or old_recipe.runtime_identity != old_checkpoint.runtime_identity
            or old_recipe.seed_lineage != old_checkpoint.seed_lineage
            or old_checkpoint.restart_state_ids != (str(initial.state_id),)
            or old_recipe.expected_output_state_id != str(expected.state_id)
            or old_recipe.base_checkpoint_id != str(old_checkpoint.checkpoint_id)
            or old_recipe.forcing_ids != (str(forcing.forcing_id),)
            or old_recipe.configuration_sha256 != content_hash(configuration)
            or old_checkpoint.configuration_sha256 != content_hash(configuration)):
        raise ReplayBindingError("ORIGINAL_CHECKPOINT_RECIPE_BINDING_MISMATCH")
    if (source_identity.get("execution_commit") != old_checkpoint.runtime_identity.get("source_head")
            or source_identity.get("scope") not in {
                "VERIFIED_R4_ENGINEERING_INPUTS_ONLY", "SYNTHETIC_FIXTURE_ONLY"}
            or (source_identity["scope"] == "VERIFIED_R4_ENGINEERING_INPUTS_ONLY"
                and source_identity["execution_commit"] != EXPECTED_SOURCE_COMMIT)):
        raise ReplayBindingError("SOURCE_EXECUTION_IDENTITY_MISMATCH")
    closed_config = {"historical_configuration": thaw_json(configuration),
                     "source_identity": thaw_json(source_identity),
                     "support_ids": list(supports), "initial_state_id": str(initial.state_id),
                     "forcing_id": str(forcing.forcing_id),
                     "initial_payload_sha256": [content_hash(p) for p in payloads]}
    provenance = ProvenanceRecord.create(
        activity="INT2C_OFFLINE_REPLAY_INPUT_BINDING_PREPARATION",
        input_refs=(str(initial.state_id), str(forcing.forcing_id)),
        source_refs=tuple(sorted(set(artifact_hashes.values()))),
        output_state_ids=(), attributes={
            "artifact_sha256": dict(artifact_hashes), "source_identity": dict(source_identity),
            "original_checkpoint_id": str(old_checkpoint.checkpoint_id),
            "original_recipe_id": str(old_recipe.recipe_id),
            "provider_identities": value["provider_identities"],
            "numerical_replay_executed": False, "canonical_publication": False,
            "physical_authority_promoted": False})
    dependencies = (str(initial.state_id), str(forcing.forcing_id), str(provenance.record_id))
    runtime = {**dict(source_identity), "model_adapter_id": ADAPTER_ID}
    checkpoint = CheckpointEnvelope.create(
        history_id=initial.history_id, branch_id=initial.branch_id, time_key="210Ma",
        restart_state_ids=(str(initial.state_id),), retained_history_state_ids=(str(initial.state_id),),
        runtime_identity=runtime, configuration=closed_config, seed_lineage=dict(old_checkpoint.seed_lineage),
        upstream_dependency_ids=dependencies, validation_status="CANDIDATE_NONCANONICAL",
        parent_checkpoint_id=str(old_checkpoint.checkpoint_id),
        authority_input_refs=old_checkpoint.authority_input_refs,
        provider_manifest_refs=((artifact_hashes["CANDIDATE_MANIFEST.json"],)
                                if "CANDIDATE_MANIFEST.json" in artifact_hashes else ()),
        restart_compatibility={"schema": "ARCANA_R6_FUNCTIONAL_DEVELOPMENT_REDUCED_STATE_V1",
                               "validation_scope": "TECHNICAL_ENGINEERING_INPUT_CLOSURE_ONLY",
                               "canonical_publication": False},
        engine_versions={"adapter": ADAPTER_ID})
    recipe = ReplayRecipe.create(
        history_id=initial.history_id, branch_id=initial.branch_id,
        base_checkpoint_id=str(checkpoint.checkpoint_id), runtime_identity=runtime,
        configuration_sha256=checkpoint.configuration_sha256,
        seed_lineage=dict(old_checkpoint.seed_lineage), forcing_ids=(str(forcing.forcing_id),),
        upstream_dependency_ids=dependencies, provenance_ids=(str(provenance.record_id),),
        expected_output_state_id=str(expected.state_id), model_adapter_id=ADAPTER_ID)
    return ReplayPreparation(initial, expected, forcing, checkpoint, recipe, provenance,
                             closed_config, source_identity, old_checkpoint, old_recipe)


def prepare_r4(repository_root: Path, bundle_root: Path) -> ReplayPreparation:
    """Read/authenticate the existing R4 bundle and prepare records without replay."""
    for path in (repository_root, bundle_root):
        if any(part.casefold() in {"world_history", "world_history_bindings"}
               for part in Path(os.path.abspath(path)).parts):
            raise ReplayBindingError("CANONICAL_PATH_FORBIDDEN")
    docs, _, hashes, _ = load_verified_bundle(bundle_root)
    validate_r4_provenance(docs)
    source = verify_kernel_source(repository_root)
    trajectory = docs["CANDIDATE_TRAJECTORY.json"]
    source["execution_source_composite_sha256"] = trajectory["source_code"]["source_identity_sha256"]
    initial = DomainStateEnvelope.from_dict(trajectory["b0_domain_states"]["initial"])
    expected = DomainStateEnvelope.from_dict(trajectory["b0_domain_states"]["candidate"])
    forcing = ForcingRecord.from_dict(trajectory["b0_forcing_record"])
    old_checkpoint = CheckpointEnvelope.from_dict(trajectory["b0_checkpoints"]["initial"])
    # Parse the candidate checkpoint as well; preserve both original identities.
    old_candidate = CheckpointEnvelope.from_dict(trajectory["b0_checkpoints"]["candidate"])
    old_recipe = ReplayRecipe.from_dict(trajectory["b0_replay_recipe"])
    checkpoint_payload = docs["CANDIDATE_CHECKPOINT.json"]
    if (thaw_json(initial.value)["side_states"] != checkpoint_payload["initial_states"]
            or thaw_json(expected.value)["side_states"] != checkpoint_payload["candidate_states"]
            or [hashlib.sha256(_json_bytes(p)).hexdigest() for p in checkpoint_payload["candidate_states"]] !=
               docs["REPLAY_RESTART.json"]["direct_state_sha256"]
            or trajectory["source_code"]["commit"] != source["execution_commit"]):
        raise ReplayBindingError("CHECKPOINT_PAYLOAD_OR_HISTORICAL_ORACLE_MISMATCH")
    configuration = {"configuration_sha256": trajectory["configuration_sha256"],
                     "numerical_configuration": trajectory["numerical_configuration"],
                     "duration_seconds": trajectory["time_support"]["elapsed_seconds"],
                     "signed_Ux_m_per_year": trajectory["forcing"]["signed_Ux_m_per_year"]}
    if content_hash(configuration) != trajectory["replay_configuration_sha256"]:
        raise ReplayBindingError("HISTORICAL_CONFIGURATION_DIGEST_MISMATCH")
    return replace(_bind_candidate(initial, expected, forcing, old_checkpoint, old_recipe,
                                    configuration, source, hashes),
                   original_candidate_checkpoint=old_candidate)


class DeterministicKernelAdapter:
    """B0 runner boundary. Expected numerical values never enter the computation."""
    def __init__(self, preparation: ReplayPreparation):
        self.preparation = preparation

    def __call__(self, recipe: ReplayRecipe, inputs: ResolvedReplayInputs) -> ReplayExecutionOutput:
        p = self.preparation
        checkpoint = inputs.checkpoint
        if checkpoint.validation_status != "VALIDATED":
            raise ReplayBindingError("TECHNICALLY_VALIDATED_CHECKPOINT_REQUIRED")
        if (recipe.model_adapter_id != ADAPTER_ID
                or (recipe.history_id, recipe.branch_id) != (p.initial.history_id, p.initial.branch_id)
                or (checkpoint.history_id, checkpoint.branch_id) != (recipe.history_id, recipe.branch_id)
                or recipe.runtime_identity != p.recipe.runtime_identity
                or checkpoint.runtime_identity != recipe.runtime_identity
                or recipe.configuration_sha256 != content_hash(thaw_json(p.configuration))
                or checkpoint.configuration_sha256 != recipe.configuration_sha256
                or str(checkpoint.checkpoint_id) != recipe.base_checkpoint_id
                or checkpoint.restart_state_ids != (str(p.initial.state_id),)
                or recipe.upstream_dependency_ids != p.recipe.upstream_dependency_ids
                or checkpoint.upstream_dependency_ids != recipe.upstream_dependency_ids
                or recipe.seed_lineage != p.recipe.seed_lineage
                or checkpoint.seed_lineage != recipe.seed_lineage
                or checkpoint.restart_compatibility != p.checkpoint.restart_compatibility
                or recipe.expected_output_state_id != p.recipe.expected_output_state_id
                or recipe.expected_payload_identity is not None
                or recipe.event_ids or inputs.events or inputs.forcing_payloads
                or len(inputs.base_states) != 1 or inputs.base_states[0] != p.initial
                or inputs.forcings != (p.forcing,)
                or recipe.forcing_ids != (str(p.forcing.forcing_id),)
                or recipe.provenance_ids != (str(p.provenance.record_id),)
                or inputs.provenance != (p.provenance,)):
            raise ReplayBindingError("REPLAY_INPUT_OR_CONFIGURATION_BINDING_MISMATCH")
        self._verify_runtime()
        config = thaw_json(p.configuration)["historical_configuration"]
        value = thaw_json(inputs.base_states[0].value)
        initial_payloads = value["side_states"]
        if [content_hash(x) for x in initial_payloads] != list(p.configuration["initial_payload_sha256"]):
            raise ReplayBindingError("INITIAL_PAYLOAD_IDENTITY_MISMATCH")
        produced = []
        for payload in initial_payloads:
            state = _restore(payload)
            final, _ = kernel.pure_shear_thermal_step(
                state, duration_s=config["duration_seconds"],
                extension_velocity_m_s=inputs.forcings[0].value["signed_Ux_m_per_year"] / kernel.SECONDS_PER_YEAR,
                maximum_kinematic_fraction_per_substep=config["numerical_configuration"][
                    "maximum_kinematic_fraction_per_substep"])
            produced.append(final.payload())
        initial = inputs.base_states[0]
        value["side_states"] = produced
        age = 210.0 - config["duration_seconds"] / kernel.SECONDS_PER_YEAR / 1_000_000.0
        output = DomainStateEnvelope.create(
            history_id=initial.history_id, branch_id=initial.branch_id, domain=initial.domain,
            time_support=TimeSupport(f"{age:.17g}Ma", initial.time_support.coordinate_system),
            spatial_support=initial.spatial_support, support_class=initial.support_class,
            authority_class=initial.authority_class, value=value, uncertainty=thaw_json(initial.uncertainty),
            parent_state_ids=(str(initial.state_id),), model_derived=True,
            applicability=thaw_json(initial.applicability))
        return ReplayExecutionOutput(output)

    def _verify_runtime(self) -> None:
        source = self.preparation.source_identity
        if (source != self.preparation.configuration["source_identity"]
                or _text_hash(Path(kernel.__file__).read_bytes()) != source["kernel_canonical_text_sha256"]
                or _text_hash(Path(__file__).read_bytes()) != source["adapter_canonical_text_sha256"]
                or platform.python_version() != source["python"] or np.__version__ != source["numpy"]):
            raise ReplayBindingError("CODE_OR_RUNTIME_IDENTITY_MISMATCH")
