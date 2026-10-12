"""Small noncanonical orchestration contract for the existing T-F2B providers.

This module binds the audited 5:11 support/kinematics output to its two T0
profiles and the existing reduced thermal kernel. It adds no physical law.
Calling ``prepare_pair_5_11`` reads governed inputs; calling ``advance_pair``
performs the already-defined engineering kernel and belongs to INT-0B.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping

from .functional_development import (
    NodeMaterial, ReducedState, T0Profile, T0_WORLD_AGE_MA, initial_reduced_state,
    pure_shear_thermal_step,
)
from .functional_spatial_support import audit_pair_5_11
from .pre_orbdata_t0_initializer import INITIALIZER_FAMILY
from .checkpoint import CheckpointEnvelope
from .forcing import ForcingRecord
from .identity import BranchId, HistoryId, content_hash
from .replay import ReplayRecipe
from .state import (AuthorityClass, DomainStateEnvelope, SpatialSupport,
                    SupportClass, TimeSupport)

SCHEMA = "ARCANA_R6_INT0_NONCANONICAL_CANDIDATE_V1"
SECONDS_PER_YEAR = 31_557_600.0
MAX_DIAGNOSTIC_SAMPLES_PER_SUPPORT = 10_001
_HEX = set("0123456789abcdef")


class IntegrationContractError(ValueError):
    """A provider result cannot be bound on a common support/time contract."""


def _sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _is_sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= _HEX


def profile_from_provider_mapping(side: Mapping[str, Any], *,
                                  require_verified_initializer: bool = False) -> T0Profile:
    """Adapt the existing support provider's T0 profile record without resampling."""
    try:
        raw = side["t0_profile"]
        lineage = raw["support_lineage"]
        if lineage.get("support_id") != side["support_id"]:
            raise IntegrationContractError("PROFILE_SUPPORT_ID_MISMATCH")
        if require_verified_initializer:
            provenance = lineage.get("profile_provenance", {})
            config_hashes = (provenance.get("thermal_reference_config_canonical_text_sha256"),
                             provenance.get("material_reference_config_canonical_text_sha256"))
            if (lineage.get("grid_id") != "R6_GLOBAL_GEOGRAPHY_1DEG_V1"
                    or provenance.get("initializer_family") != INITIALIZER_FAMILY
                    or provenance.get("b6n8n_binding_status") != "EXACTLY_ONE_INITIALIZER_BINDING"
                    or provenance.get("canonical_state") is not False
                    or "NOT_B6N8R_EXECUTION_ROSTER" not in provenance.get("scenario_roster_status", "")
                    or not all(_is_sha(value) for value in config_hashes)):
                raise IntegrationContractError("T0_INITIALIZER_PROVENANCE_UNVERIFIED")
        materials = tuple(NodeMaterial(**item) for item in raw["material_properties"])
        temperatures = tuple(float(x) for x in raw["temperature_k"])
        z = tuple(float(x) for x in raw["z_m"])
        profile = T0Profile(
            support_id=str(side["support_id"]),
            support_class=str(side["support_class"]),
            scenario_id=str(raw["scenario_id"]), crust_m=float(raw["crust_m"]),
            model_base_m=float(raw["model_base_m"]),
            surface_temperature_k=float(raw["surface_temperature_k"]),
            base_temperature_k=temperatures[-1],
            surface_heat_flow_w_m2=float(raw["surface_heat_flow_w_m2"]),
            z_m=z, temperature_k=temperatures, materials=materials,
            material_roles=tuple(raw["material_roles"]),
            provenance=dict(lineage),
        )
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        if isinstance(exc, IntegrationContractError):
            raise
        raise IntegrationContractError("T0_PROFILE_RECORD_INVALID") from exc
    if (not profile.support_id or not profile.support_class.startswith("CONTINENTAL_")
            or profile.scenario_id != "REFERENCE_ENGINEERING_SCENARIO"
            or len(z) < 3 or len(z) != len(temperatures) or len(z) != len(materials)
            or len(profile.material_roles) != 2 or z[0] != 0.0
            or any(not math.isfinite(x) for x in (*z, *temperatures))
            or any(a >= b for a, b in zip(z, z[1:]))
            or not (0 < profile.crust_m < profile.model_base_m)
            or z[-1] != profile.model_base_m
            or temperatures[0] != profile.surface_temperature_k
            or temperatures[-1] != profile.base_temperature_k
            or not math.isfinite(profile.surface_heat_flow_w_m2)
            or profile.surface_heat_flow_w_m2 <= 0
            or any(not all(math.isfinite(v) for v in (m.k_w_m_k, m.rho_kg_m3,
                                                       m.cp_j_kg_k, m.radiogenic_w_m3))
                   or min(m.k_w_m_k, m.rho_kg_m3, m.cp_j_kg_k) <= 0
                   or m.radiogenic_w_m3 < 0 for m in materials)
            or tuple(dict.fromkeys(m.role_id for m in materials)) != profile.material_roles):
        raise IntegrationContractError("T0_PROFILE_SUPPORT_UNITS_OR_CARDINALITY_INVALID")
    return profile


def _center_xyz(row: int, column: int, radius_m: float) -> tuple[float, float, float]:
    latitude = math.radians(-90.0 + row + 0.5)
    longitude = math.radians(-180.0 + column + 0.5)
    return (radius_m * math.cos(latitude) * math.cos(longitude),
            radius_m * math.cos(latitude) * math.sin(longitude),
            radius_m * math.sin(latitude))


def _distance_m(first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
    dot = sum(a * b for a, b in zip(first, second))
    norm_first = math.sqrt(sum(x * x for x in first))
    norm_second = math.sqrt(sum(x * x for x in second))
    cosine = max(-1.0, min(1.0, dot / (norm_first * norm_second)))
    return norm_first * math.acos(cosine)


@dataclass(frozen=True)
class PairIntegrationPlan:
    assessment: Mapping[str, Any]
    selected_section: Mapping[str, Any]
    profiles: tuple[T0Profile, T0Profile]
    support_ids: tuple[str, str]
    initial_width_m: float
    signed_extension_m_per_year: float
    t0_age_ma: float
    provider_identities: Mapping[str, str]
    configuration_sha256: str
    authority_scope: str


def _build_pair_plan(assessment: Mapping[str, Any], *, authority_scope: str) -> PairIntegrationPlan:
    """Bind audited records; ``authority_scope`` is set by trusted entrypoints only."""
    if (assessment.get("stage") != "T-F2B"
            or assessment.get("selected_ordered_plate_pair") != [5, 11]
            or assessment.get("no_world_history_access_or_publication") is not True
            or assessment.get("canonical_state_changed") is not False):
        raise IntegrationContractError("ASSESSMENT_SCOPE_OR_CANONICAL_GUARD_INVALID")
    selected_rows = [row for row in assessment.get("edge_matrix", ())
                     if row.get("boundary_id") == assessment.get("selected_boundary_id")]
    if len(selected_rows) != 1:
        raise IntegrationContractError("SELECTED_SECTION_NOT_UNIQUE")
    selected = selected_rows[0]
    sides = selected.get("sides_plate_a_then_plate_b", ())
    if (selected.get("ordered_plate_pair") != [5, 11]
            or selected.get("SECTION_ELIGIBILITY") != "ELIGIBLE"
            or selected.get("SIGNED_EXTENSION") != "EXTENSION"
            or selected.get("junction_adjacent") is not False
            or len(sides) != 2 or [side.get("plate_id") for side in sides] != [5, 11]
            or not all(side.get("admitted_continental_binding") is True for side in sides)):
        raise IntegrationContractError("SECTION_SUPPORT_OR_FORCING_NOT_ADMITTED")
    pair_census = assessment.get("pair_event_census", {})
    if (pair_census.get("pair_id") != "5:11"
            or pair_census.get("eligibility") != "ELIGIBLE_QUIESCENT"
            or pair_census.get("scope_is_activation_authority") is not False):
        raise IntegrationContractError("PAIR_EVENT_CENSUS_OR_AUTHORITY_SCOPE_INVALID")
    profiles = tuple(profile_from_provider_mapping(
        side, require_verified_initializer=(authority_scope == "REPOSITORY_VERIFIED_PROVIDER_AUDIT"))
        for side in sides)
    support_ids = tuple(str(side["support_id"]) for side in sides)
    if (len(set(support_ids)) != 2
            or tuple(profile.support_id for profile in profiles) != support_ids
            or profiles[0].material_roles != profiles[1].material_roles):
        raise IntegrationContractError("TWO_SIDED_SUPPORT_BINDING_INVALID")
    edge = selected.get("parent_grid_edge", {})
    if any(type(edge.get(name)) is not int for name in ("row", "column")):
        raise IntegrationContractError("PARENT_GRID_COORDINATE_INVALID")
    radius = float(assessment.get("source_grid_radius_m", float("nan")))
    ux = float(selected.get("signed_Ux_m_per_year", float("nan")))
    if not (math.isfinite(radius) and radius > 0 and math.isfinite(ux) and ux > 0):
        raise IntegrationContractError("RADIUS_OR_SIGNED_EULER_FORCING_INVALID")
    rows_columns = [(int(side["row"]), int(side["column"])) for side in sides]
    width = _distance_m(_center_xyz(*rows_columns[0], radius),
                        _center_xyz(*rows_columns[1], radius))
    if not math.isfinite(width) or width <= 0:
        raise IntegrationContractError("ENGINEERING_SUPPORT_DISTANCE_INVALID")
    frame = selected.get("velocity_components", {})
    try:
        normal = tuple(float(x) for x in frame["normal_ab_xyz"])
        tangent = tuple(float(x) for x in frame["tangent_xyz"])
    except (KeyError, TypeError, ValueError) as exc:
        raise IntegrationContractError("SECTION_FRAME_MISSING") from exc
    if (len(normal) != 3 or len(tangent) != 3
            or not all(math.isfinite(x) for x in (*normal, *tangent))
            or abs(sum(x*x for x in normal) - 1.0) > 1e-10
            or abs(sum(x*x for x in tangent) - 1.0) > 1e-10
            or abs(sum(a*b for a, b in zip(normal, tangent))) > 1e-10):
        raise IntegrationContractError("SECTION_FRAME_INVALID")
    provider_ids = {
        "source_set": assessment.get("source_identity_sha256"),
        "kinematics_semantic": assessment.get("kinematics_semantic_identity_sha256"),
        "kinematics_artifact": assessment.get("kinematics_artifact_sha256"),
        "mapping": assessment.get("mapping_join", {}).get("mapping_sha256"),
        "vector_partition": assessment.get("vector_partition_payload_sha256"),
        "thermal_field_package": assessment.get("b6n8n_field_package_sha256"),
        "support_binding_index": assessment.get("b6n8n_index_sha256"),
        "event_census": assessment.get("event_eligibility_census_sha256"),
    }
    if not all(_is_sha(value) for value in provider_ids.values()):
        raise IntegrationContractError("PROVIDER_IDENTITY_UNKNOWN_OR_INVALID")
    source_head = assessment.get("source_head")
    source_branch = assessment.get("source_branch")
    if (not isinstance(source_head, str) or len(source_head) != 40
            or set(source_head) - set("0123456789abcdef")
            or not isinstance(source_branch, str) or not source_branch):
        raise IntegrationContractError("SOURCE_CHECKOUT_IDENTITY_UNKNOWN_OR_INVALID")
    config = {"schema": SCHEMA, "pair": [5, 11], "support_ids": support_ids,
              "boundary_id": selected["boundary_id"], "width_m": width,
              "signed_extension_m_per_year": ux,
              "source_head": source_head, "source_branch": source_branch,
              "provider_identities": provider_ids,
              "authority_scope": authority_scope,
              "time_origin": "T0_WORLD_AGE_MA_FROM_ADMITTED_T0_INITIALIZER",
              "kernel": "functional_development.pure_shear_thermal_step"}
    return PairIntegrationPlan(assessment, selected, profiles, support_ids, width, ux,
                              T0_WORLD_AGE_MA, provider_ids, _sha(config), authority_scope)


def build_fixture_pair_plan(assessment: Mapping[str, Any]) -> PairIntegrationPlan:
    """Build a synthetic-only plan; never an authority path for INT-0B."""
    if assessment.get("fixture_marker") != "SYNTHETIC_FIXTURE_ONLY":
        raise IntegrationContractError("SYNTHETIC_FIXTURE_MARKER_REQUIRED")
    return _build_pair_plan(assessment, authority_scope="SYNTHETIC_FIXTURE_ONLY")


def prepare_pair_5_11(repository_root: str | Path, *, expected_branch: str) -> PairIntegrationPlan:
    """Read and validate the existing provider chain; performs no evolution."""
    assessment = audit_pair_5_11(repository_root, expected_branch=expected_branch)
    return _build_pair_plan(assessment, authority_scope="REPOSITORY_VERIFIED_PROVIDER_AUDIT")


def advance_pair(plan: PairIntegrationPlan, *, duration_s: float,
                 maximum_kinematic_fraction_per_substep: float,
                 state_observer: Callable[[str, ReducedState], None] | None = None
                 ) -> tuple[tuple[ReducedState, ...], tuple[dict[str, Any], ...]]:
    """Pass audited profiles and Euler forcing into the existing thermal kernel."""
    if not math.isfinite(duration_s) or duration_s <= 0:
        raise IntegrationContractError("DURATION_MUST_BE_FINITE_AND_POSITIVE")
    initial = tuple(initial_reduced_state(profile, initial_width_m=plan.initial_width_m)
                    for profile in plan.profiles)
    final: list[ReducedState] = []
    diagnostics: list[dict[str, Any]] = []
    velocity_m_s = plan.signed_extension_m_per_year / SECONDS_PER_YEAR
    for support_id, state in zip(plan.support_ids, initial):
        observer = (None if state_observer is None else
                    lambda current, selected_support=support_id:
                    state_observer(selected_support, current))
        evolved, diag = pure_shear_thermal_step(
            state, duration_s=duration_s, extension_velocity_m_s=velocity_m_s,
            maximum_kinematic_fraction_per_substep=maximum_kinematic_fraction_per_substep,
            state_observer=observer)
        final.append(evolved)
        diagnostics.append(asdict(diag))
    return tuple(final), tuple(diagnostics)


def capture_numerical_step_samples(
    plan: PairIntegrationPlan, *, duration_s: float,
    maximum_kinematic_fraction_per_substep: float,
    maximum_samples_per_support: int = MAX_DIAGNOSTIC_SAMPLES_PER_SUPPORT,
) -> tuple[tuple[ReducedState, ...], tuple[dict[str, Any], ...],
           dict[str, list[dict[str, Any]]]]:
    """Capture the initial state and every numerical substep without interpolation."""
    if (isinstance(maximum_samples_per_support, bool)
            or not isinstance(maximum_samples_per_support, int)
            or maximum_samples_per_support < 2):
        raise IntegrationContractError("DIAGNOSTIC_SAMPLE_LIMIT_INVALID")
    samples: dict[str, list[dict[str, Any]]] = {key: [] for key in plan.support_ids}

    def observe(support_id: str, state: ReducedState) -> None:
        records = samples[support_id]
        if len(records) >= maximum_samples_per_support:
            raise IntegrationContractError("DIAGNOSTIC_SAMPLE_LIMIT_EXCEEDED")
        records.append({
            "time_s": state.time_s,
            "elapsed_years": state.time_s / SECONDS_PER_YEAR,
            "width_m": state.width_m,
            "crust_m": state.crust_m,
            "lithosphere_m": state.lithosphere_m,
            "beta": state.beta,
            "accumulated_strain": state.accumulated_strain,
            "material_coordinate": list(state.material_coordinate),
            "z_m": [value * state.lithosphere_m for value in state.material_coordinate],
            "temperature_k": list(state.temperature_k),
        })

    final, diagnostics = advance_pair(plan, duration_s=duration_s,
        maximum_kinematic_fraction_per_substep=maximum_kinematic_fraction_per_substep,
        state_observer=observe)
    return final, diagnostics, samples


def trajectory_document(plan: PairIntegrationPlan, states: tuple[ReducedState, ...], *,
                        duration_s: float, numerical_configuration: Mapping[str, Any]) -> dict[str, Any]:
    if len(states) != 2 or not math.isfinite(duration_s) or duration_s <= 0:
        raise IntegrationContractError("CANDIDATE_TRAJECTORY_CARDINALITY_OR_TIME_INVALID")
    duration_years = duration_s / SECONDS_PER_YEAR
    initial = tuple(initial_reduced_state(profile, initial_width_m=plan.initial_width_m)
                    for profile in plan.profiles)
    fields = [{"support_id": support_id, "initial": start.payload(),
               "candidate": end.payload(),
               "delta_temperature_k": [b-a for a, b in zip(start.temperature_k, end.temperature_k)],
               "delta_width_m": end.width_m-start.width_m,
               "delta_crust_m": end.crust_m-start.crust_m,
               "delta_lithosphere_m": end.lithosphere_m-start.lithosphere_m}
              for support_id, start, end in zip(plan.support_ids, initial, states)]
    age = plan.t0_age_ma - duration_years / 1_000_000.0
    history_id = str(HistoryId.from_payload({"scope": "INT0_NONCANONICAL_CANDIDATE",
        "configuration_sha256": plan.configuration_sha256,
        "source_head": plan.assessment.get("source_head")}))
    branch_id = str(BranchId.from_payload({"history_id": history_id,
        "pair": [5, 11], "support_ids": plan.support_ids,
        "scope": plan.authority_scope}))
    domain = "continental_lithospheric_thermal_engineering_candidate"
    spatial = SpatialSupport("R6_GLOBAL_GEOGRAPHY_1DEG_V1", plan.support_ids,
                             "1-degree parent-cell support; no subcell promotion", "CELL_SET")
    uncertainty = {"physical_temporal_validity": "UNKNOWN",
        "lateral_thermal_coupling": "NOT_MODELED",
        "kinematics": plan.assessment.get("kinematics_uncertainty", "UNKNOWN"),
        "thermal_and_material": "SOURCE_REFERENCE_SCENARIO; DISTRIBUTION_NOT_ESTABLISHED"}
    applicability = {"candidate_only": True,
        "provider_input_scope": plan.authority_scope,
        "canonical_publication": False,
        "physical_section_selected": False,
        "physical_Xe_authority": "UNKNOWN"}
    initial_envelope = DomainStateEnvelope.create(
        history_id=history_id, branch_id=branch_id, domain=domain,
        time_support=TimeSupport("210Ma", "R6_GLOBAL_MA_OLDER_TO_YOUNGER", "INSTANT"),
        spatial_support=spatial,
        support_class=(SupportClass.FIXTURE_ONLY if plan.authority_scope == "SYNTHETIC_FIXTURE_ONLY"
                       else SupportClass.DERIVED_SUPPORTED),
        authority_class=(AuthorityClass.FIXTURE_ONLY if plan.authority_scope == "SYNTHETIC_FIXTURE_ONLY"
                         else AuthorityClass.DERIVED_AUTHORITY),
        value={"pair": [5, 11], "support_ids": list(plan.support_ids),
               "side_states": [state.payload() for state in initial],
               "provider_identities": dict(plan.provider_identities)},
        uncertainty=uncertainty, model_derived=True, applicability=applicability)
    candidate_envelope = DomainStateEnvelope.create(
        history_id=history_id, branch_id=branch_id, domain=domain,
        time_support=TimeSupport(f"{age:.17g}Ma", "R6_GLOBAL_MA_OLDER_TO_YOUNGER", "INSTANT"),
        spatial_support=spatial,
        support_class=(SupportClass.FIXTURE_ONLY if plan.authority_scope == "SYNTHETIC_FIXTURE_ONLY"
                       else SupportClass.DERIVED_SUPPORTED),
        authority_class=(AuthorityClass.FIXTURE_ONLY if plan.authority_scope == "SYNTHETIC_FIXTURE_ONLY"
                         else AuthorityClass.DERIVED_AUTHORITY),
        value={"pair": [5, 11], "support_ids": list(plan.support_ids),
               "side_states": [state.payload() for state in states],
               "provider_identities": dict(plan.provider_identities)},
        uncertainty=uncertainty, parent_state_ids=(str(initial_envelope.state_id),),
        model_derived=True, applicability=applicability)
    configuration = {"configuration_sha256": plan.configuration_sha256,
        "numerical_configuration": dict(numerical_configuration),
        "duration_seconds": duration_s, "signed_Ux_m_per_year": plan.signed_extension_m_per_year}
    replay_configuration_sha256 = content_hash(configuration)
    runtime_identity = {"source_head": plan.assessment.get("source_head"),
        "model_adapter_id": "ARCANA_R6_TF2B_PURE_SHEAR_THERMAL_STEP_V0",
        "provider_input_scope": plan.authority_scope}
    dependencies = tuple(plan.provider_identities.values())
    initial_checkpoint = CheckpointEnvelope.create(
        history_id=history_id, branch_id=branch_id, time_key="210Ma",
        restart_state_ids=(str(initial_envelope.state_id),),
        retained_history_state_ids=(str(initial_envelope.state_id),),
        runtime_identity=runtime_identity, configuration=configuration,
        seed_lineage={"status": "DETERMINISTIC_NO_RANDOM_SEED"},
        upstream_dependency_ids=dependencies, validation_status="CANDIDATE_NONCANONICAL",
        restart_compatibility={"schema": "ARCANA_R6_FUNCTIONAL_DEVELOPMENT_REDUCED_STATE_V1"},
        authority_input_refs=dependencies, engine_versions={"adapter": "TF2B_V0"})
    candidate_checkpoint = CheckpointEnvelope.create(
        history_id=history_id, branch_id=branch_id, time_key=f"{age:.17g}Ma",
        restart_state_ids=(str(candidate_envelope.state_id),),
        retained_history_state_ids=(str(initial_envelope.state_id), str(candidate_envelope.state_id)),
        runtime_identity=runtime_identity, configuration=configuration,
        seed_lineage={"status": "DETERMINISTIC_NO_RANDOM_SEED"},
        upstream_dependency_ids=dependencies, validation_status="CANDIDATE_NONCANONICAL",
        restart_compatibility={"schema": "ARCANA_R6_FUNCTIONAL_DEVELOPMENT_REDUCED_STATE_V1"},
        parent_checkpoint_id=str(initial_checkpoint.checkpoint_id),
        authority_input_refs=dependencies, engine_versions={"adapter": "TF2B_V0"})
    forcing_record = ForcingRecord.create(
        history_id=history_id, branch_id=branch_id,
        forcing_kind="FROZEN_INSTANTANEOUS_ENGINEERING_DRIVER",
        domain=domain,
        time_support=TimeSupport("210Ma", "R6_GLOBAL_MA_OLDER_TO_YOUNGER", "INSTANT"),
        spatial_support=spatial,
        support_class=(SupportClass.FIXTURE_ONLY if plan.authority_scope == "SYNTHETIC_FIXTURE_ONLY"
                       else SupportClass.DERIVED_SUPPORTED),
        authority_class=(AuthorityClass.FIXTURE_ONLY if plan.authority_scope == "SYNTHETIC_FIXTURE_ONLY"
                         else AuthorityClass.DERIVED_AUTHORITY),
        value={"signed_Ux_m_per_year": plan.signed_extension_m_per_year,
               "frame": "T_F2B_SELECTED_SECTION_NORMAL_PLATE_5_TO_11",
               "support_ids": list(plan.support_ids)},
        source_refs=dependencies)
    forcing_id = forcing_record.forcing_id
    recipe = ReplayRecipe.create(
        history_id=history_id, branch_id=branch_id,
        base_checkpoint_id=str(initial_checkpoint.checkpoint_id),
        runtime_identity=runtime_identity,
        seed_lineage={"status": "DETERMINISTIC_NO_RANDOM_SEED"},
        forcing_ids=(str(forcing_id),), expected_output_state_id=str(candidate_envelope.state_id),
        configuration_sha256=replay_configuration_sha256,
        model_adapter_id="ARCANA_R6_TF2B_PURE_SHEAR_THERMAL_STEP_V0",
        upstream_dependency_ids=(str(initial_envelope.state_id), *dependencies))
    return {
        "schema": SCHEMA, "canonical_publication": False,
        "world_history_accessed": False, "world_history_mutated": False,
        "pair": [5, 11], "boundary_id": plan.selected_section["boundary_id"],
        "time_support": {"t0_age_ma": plan.t0_age_ma,
            "candidate_age_ma": plan.t0_age_ma - duration_years / 1_000_000.0,
            "elapsed_seconds": duration_s, "elapsed_years": duration_years,
            "validity": "ENGINEERING_FROZEN_FORCING; GEOLOGICAL_TEMPORAL_VALIDITY_UNKNOWN"},
        "spatial_support": {"support_ids": list(plan.support_ids),
            "grid_id": "R6_GLOBAL_GEOGRAPHY_1DEG_V1",
            "selector": "EXACT_SELECTED_TF2B_ADJACENT_PARENT_CELLS",
            "engineering_width_m": plan.initial_width_m,
            "physical_Xe_authority": "UNKNOWN"},
        "forcing": {"signed_Ux_m_per_year": plan.signed_extension_m_per_year,
            "frame": "T_F2B_SELECTED_SECTION_NORMAL_PLATE_5_TO_11",
            "mode": "FROZEN_INSTANTANEOUS_ENGINEERING_DRIVER"},
        "providers": dict(plan.provider_identities),
        "provider_input_scope": plan.authority_scope,
        "source_code": {"branch": plan.assessment.get("source_branch"),
            "commit": plan.assessment.get("source_head"),
            "source_identity_sha256": plan.assessment.get("source_identity_sha256")},
        "configuration_sha256": plan.configuration_sha256,
        "replay_configuration_sha256": replay_configuration_sha256,
        "numerical_configuration": dict(numerical_configuration),
        "fields": fields,
        "event_candidates": {"status": "UNKNOWN_NO_EVENT_TRANSITION_PROVIDER",
            "candidates": [], "not_equivalent_to_proven_no_event": True},
        "uncertainty": {"kinematics": plan.assessment.get("kinematics_uncertainty", "UNKNOWN"),
            "thermal_and_material": "SOURCE_REFERENCE_SCENARIO; DISTRIBUTION_NOT_ESTABLISHED",
            "lateral_coupling": "NOT_MODELED", "temporal_applicability": "UNKNOWN"},
        "b0_domain_states": {"initial": initial_envelope.to_dict(),
                              "candidate": candidate_envelope.to_dict()},
        "b0_checkpoints": {"initial": initial_checkpoint.to_dict(),
                           "candidate": candidate_checkpoint.to_dict()},
        "b0_forcing_record": forcing_record.to_dict(),
        "b0_replay_recipe": recipe.to_dict(),
        "b0_replay_status": "DESCRIPTOR_ONLY_NOT_REGISTERED_IN_HISTORYSTORE",
        "restart_recipe": {"restore_from_checkpoint_id": str(candidate_checkpoint.checkpoint_id),
            "state_schema": "ARCANA_R6_FUNCTIONAL_DEVELOPMENT_REDUCED_STATE_V1",
            "continuation_kernel": "arcana_worldsim.r6.functional_development.pure_shear_thermal_step",
            "remaining_duration_must_be_explicit": True,
            "determinism_scope": "same code/runtime/configuration; cross-runtime equivalence not attested"},
    }


def write_candidate_bundle(document: Mapping[str, Any], output_dir: str | Path, *,
                           repository_root: str | Path,
                           protected_roots: tuple[str | Path, ...]) -> dict[str, Any]:
    """Write a new noncanonical bundle and per-file manifest; refuse overlap/overwrite."""
    root = Path(repository_root).resolve()
    destination = Path(output_dir).resolve()
    if not protected_roots:
        raise IntegrationContractError("PROTECTED_ROOTS_MUST_BE_EXPLICIT")
    guards = (root, *(Path(item).resolve() for item in protected_roots))
    for guard in guards:
        if destination == guard or destination in guard.parents or guard in destination.parents:
            raise IntegrationContractError("OUTPUT_OVERLAPS_PROTECTED_ROOT")
    if destination.exists():
        raise IntegrationContractError("OUTPUT_DIRECTORY_ALREADY_EXISTS")
    data = (json.dumps(document, sort_keys=True, ensure_ascii=False, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    manifest = {"schema": "ARCANA_R6_INT0_CANDIDATE_MANIFEST_V1",
        "canonical_publication": False,
        "files": {"CANDIDATE_TRAJECTORY.json": {"bytes": len(data), "sha256": digest}}}
    manifest_bytes = (json.dumps(manifest, sort_keys=True, ensure_ascii=False, indent=2,
                                 allow_nan=False) + "\n").encode("utf-8")
    try:
        destination.mkdir(parents=True, exist_ok=False)
        trajectory_path = destination / "CANDIDATE_TRAJECTORY.json"
        if trajectory_path.write_bytes(data) != len(data) or trajectory_path.read_bytes() != data:
            raise IntegrationContractError("CANDIDATE_TRAJECTORY_READBACK_MISMATCH")
        manifest_path = destination / "CANDIDATE_MANIFEST.json"
        if manifest_path.write_bytes(manifest_bytes) != len(manifest_bytes):
            raise IntegrationContractError("CANDIDATE_MANIFEST_WRITE_INCOMPLETE")
        if manifest_path.read_bytes() != manifest_bytes:
            raise IntegrationContractError("CANDIDATE_MANIFEST_READBACK_MISMATCH")
    except OSError:
        # Partial directories/files remain non-authoritative; never claim a seal.
        raise
    return {"manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "trajectory_sha256": digest, "trajectory_bytes": len(data),
            "output_dir": str(destination), "canonical_publication": False}
