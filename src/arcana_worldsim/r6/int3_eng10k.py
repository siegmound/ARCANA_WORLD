"""Bounded INT-3 ENG10K continuation contract; no canonical history integration."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping

from .functional_development import ReducedState, state_from_payload

SECONDS_PER_YEAR = 31_557_600.0
R4_MANIFEST_SHA256 = "191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236"
R4_SOURCE_COMMIT = "91fc83d50ec15d8bb9b826926ac2f2dc859281e8"
R4_KERNEL_SHA256 = "bddedfd7439b328951389012b2af371d106d042018ac4be928325a6395666542"
R4_BOUNDARY_ID = "R6BND-T0-3eb57747e6f0a3f3305f"
R4_SUPPORT_IDS = ("R6G1D-R091-C029", "R6G1D-R091-C028")
RESOLUTION_FACTORS = (0.001, 0.0005, 0.00025)
MAX_RETAINED_SAMPLES_PER_SUPPORT = 1002
MAX_SAMPLE_RECORD_BYTES = 16_384
MAX_FIXED_OUTPUT_BYTES = 1_048_576
MAX_PROJECTED_OUTPUT_BYTES = (
    4 * MAX_RETAINED_SAMPLES_PER_SUPPORT * MAX_SAMPLE_RECORD_BYTES
    + MAX_FIXED_OUTPUT_BYTES
)


class Eng10kContractError(ValueError):
    """A source, input, checkpoint or execution contract is incomplete."""


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class R4ContinuationInputs:
    manifest_sha256: str
    initial_states: tuple[ReducedState, ReducedState]
    checkpoint_states: tuple[ReducedState, ReducedState]
    forcing_m_per_year: float
    support_ids: tuple[str, str]
    boundary_id: str
    source_identity: Mapping[str, Any]
    provider_identities: Mapping[str, str]
    configuration_identity: str


def _json_document(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Eng10kContractError(f"R4_JSON_INVALID:{label}") from exc
    if not isinstance(value, dict):
        raise Eng10kContractError(f"R4_JSON_NOT_OBJECT:{label}")
    return value


def _state(row: Mapping[str, Any], *, expected_time_s: float, label: str) -> ReducedState:
    try:
        value = state_from_payload(row)
    except (KeyError, TypeError, ValueError) as exc:
        raise Eng10kContractError(f"R4_STATE_INVALID:{label}") from exc
    if value.payload() != dict(row):
        raise Eng10kContractError(f"R4_STATE_PAYLOAD_INCOMPLETE_OR_CHANGED:{label}")
    if value.time_s != expected_time_s:
        raise Eng10kContractError(f"R4_STATE_TIME_MISMATCH:{label}")
    return value


def load_r4_continuation_bundle(bundle: Path) -> R4ContinuationInputs:
    """Authenticate exact R4 bytes; parse only the byte buffers just hashed."""
    bundle = Path(bundle)
    if bundle.is_symlink() or not bundle.is_dir():
        raise Eng10kContractError("R4_BUNDLE_PATH_INVALID")
    for parent in (bundle, *bundle.parents):
        if parent.is_symlink():
            raise Eng10kContractError("R4_BUNDLE_SYMLINK_FORBIDDEN")
    if any((bundle / name).is_symlink() for name in bundle.iterdir()):
        raise Eng10kContractError("R4_BUNDLE_SYMLINK_FORBIDDEN")
    manifest_path = bundle / "CANDIDATE_MANIFEST.json"
    try:
        manifest_raw = manifest_path.read_bytes()
    except OSError as exc:
        raise Eng10kContractError("R4_MANIFEST_UNAVAILABLE") from exc
    manifest_hash = sha256_bytes(manifest_raw)
    if manifest_hash != R4_MANIFEST_SHA256:
        raise Eng10kContractError("R4_MANIFEST_IDENTITY_MISMATCH")
    manifest = _json_document(manifest_raw, manifest_path.name)
    expected_names = {
        "CANDIDATE_CHECKPOINT.json", "CANDIDATE_TRAJECTORY.json",
        "DIAGNOSTIC_NUMERICAL_SAMPLES.json", "EDGE_AUDIT_MATRIX.json",
        "REPLAY_RESTART.json", "SELECTED_SECTION_AND_PROFILES.json",
        "THERMAL_CONVERGENCE.json",
    }
    if set(manifest.get("files", {})) != expected_names:
        raise Eng10kContractError("R4_MANIFEST_MEMBER_SET_MISMATCH")
    if set(p.name for p in bundle.iterdir()) != expected_names | {
        "RUN_RESULT.json", "CANDIDATE_MANIFEST.json"
    }:
        raise Eng10kContractError("R4_BUNDLE_DIRECTORY_MEMBERSHIP_MISMATCH")
    raw_by_name: dict[str, bytes] = {}
    for name, metadata in manifest["files"].items():
        try:
            raw = (bundle / name).read_bytes()
        except OSError as exc:
            raise Eng10kContractError(f"R4_MEMBER_UNAVAILABLE:{name}") from exc
        if (not (bundle / name).is_file() or len(raw) != metadata.get("bytes")
                or sha256_bytes(raw) != metadata.get("sha256")):
            raise Eng10kContractError(f"R4_MEMBER_IDENTITY_MISMATCH:{name}")
        raw_by_name[name] = raw
    try:
        result_raw = (bundle / "RUN_RESULT.json").read_bytes()
    except OSError as exc:
        raise Eng10kContractError("R4_RUN_RESULT_UNAVAILABLE") from exc
    result_meta = manifest.get("RUN_RESULT.json", {})
    if (not (bundle / "RUN_RESULT.json").is_file()
            or len(result_raw) != result_meta.get("bytes")
            or sha256_bytes(result_raw) != result_meta.get("sha256")):
        raise Eng10kContractError("R4_RUN_RESULT_IDENTITY_MISMATCH")
    raw_by_name["RUN_RESULT.json"] = result_raw
    docs = {name: _json_document(raw, name) for name, raw in raw_by_name.items()}
    checkpoint = docs["CANDIDATE_CHECKPOINT.json"]
    trajectory = docs["CANDIDATE_TRAJECTORY.json"]
    section = docs["SELECTED_SECTION_AND_PROFILES.json"]
    result = docs["RUN_RESULT.json"]
    expected_checkpoint_time = 1000.0 * SECONDS_PER_YEAR
    if (manifest.get("canonical_publication") is not False
            or checkpoint.get("canonical_publication") is not False
            or checkpoint.get("elapsed_years") != 1000.0
            or section.get("boundary_id") != R4_BOUNDARY_ID
            or tuple(section.get("support_ids", ())) != R4_SUPPORT_IDS
            or tuple(result.get("selected_support_ids", ())) != R4_SUPPORT_IDS
            or result.get("selected_boundary_id") != R4_BOUNDARY_ID
            or result.get("checkpoint_commit") != R4_SOURCE_COMMIT
            or result.get("duration_years") != 1000.0
            or tuple(result.get("resolution_factors", ())) != RESOLUTION_FACTORS
            or result.get("signed_Ux_m_per_year") != section.get("signed_candidate_Ux_m_per_year")
            or section.get("forcing_mode") != "FROZEN_INSTANTANEOUS_ENGINEERING_DRIVER"
            or section.get("temperature_boundary_conditions") !=
               "EXISTING_TF1_COLUMN_CONTRACT_FIXED_SURFACE_AND_MODEL_BASE"
            or section.get("lateral_thermal_coupling") !=
               "NOT_MODELED_IN_REDUCED_1D_COLUMN_PAIR"):
        raise Eng10kContractError("R4_CONTINUATION_SCOPE_OR_FORCING_MISMATCH")
    source = trajectory.get("source_code", {})
    provider_ids = manifest.get("provider_identities", {})
    provider_keys = {"source_set", "kinematics_semantic", "kinematics_artifact", "mapping",
                      "vector_partition", "thermal_field_package", "support_binding_index", "event_census"}
    expected_source_refs = [provider_ids.get(key) for key in (
        "source_set", "kinematics_semantic", "kinematics_artifact", "mapping",
        "vector_partition", "thermal_field_package", "support_binding_index", "event_census")]
    if (set(provider_ids) != provider_keys
            or any(not isinstance(value, str) or len(value) != 64
                   or set(value) - set("0123456789abcdef") for value in provider_ids.values())
            or source.get("commit") != R4_SOURCE_COMMIT
            or source.get("source_identity_sha256") != provider_ids.get("source_set")
            or trajectory.get("b0_forcing_record", {}).get("source_refs") != expected_source_refs):
        raise Eng10kContractError("R4_SOURCE_IDENTITY_MISMATCH")
    numerical_config = trajectory.get("numerical_configuration", {})
    source_candidate_checkpoint = trajectory.get("b0_checkpoints", {}).get("candidate", {})
    if (numerical_config.get("duration_years") != 1000.0
            or numerical_config.get("maximum_kinematic_fraction_per_substep") != 0.0005
            or numerical_config.get("kernel") != "functional_development.pure_shear_thermal_step"
            or source_candidate_checkpoint.get("validation_status") != "CANDIDATE_NONCANONICAL"):
        raise Eng10kContractError("R4_REFERENCE_CONFIGURATION_OR_CANDIDATE_STATUS_INVALID")
    initial_rows = checkpoint.get("initial_states", ())
    candidate_rows = checkpoint.get("candidate_states", ())
    if len(initial_rows) != 2 or len(candidate_rows) != 2:
        raise Eng10kContractError("R4_STATE_CARDINALITY_INVALID")
    initial_time = 0.0
    start_states = tuple(_state(row, expected_time_s=initial_time,
                                label=f"initial-{i}") for i, row in enumerate(initial_rows))
    checkpoint_states = tuple(_state(row, expected_time_s=expected_checkpoint_time,
                                     label=f"candidate-{i}") for i, row in enumerate(candidate_rows))
    if any(len(state.temperature_k) != 73 for state in (*start_states, *checkpoint_states)):
        raise Eng10kContractError("R4_SUPPORT_PROFILE_NODE_COUNT_MISMATCH")
    for i, (start, saved) in enumerate(zip(start_states, checkpoint_states)):
        if (start.initial_width_m != saved.initial_width_m
                or start.initial_crust_m != saved.initial_crust_m
                or start.initial_lithosphere_m != saved.initial_lithosphere_m
                or start.material_coordinate != saved.material_coordinate
                or start.materials != saved.materials
                or start.surface_temperature_k != saved.surface_temperature_k
                or start.base_temperature_k != saved.base_temperature_k):
            raise Eng10kContractError(f"R4_CHECKPOINT_INITIAL_DEPENDENCIES_CHANGED:{i}")
    value = trajectory.get("b0_domain_states", {}).get("candidate", {}).get("value", {})
    if value.get("side_states") != candidate_rows or tuple(value.get("support_ids", ())) != R4_SUPPORT_IDS:
        raise Eng10kContractError("R4_TYPED_CANDIDATE_STATE_BINDING_MISMATCH")
    if source_candidate_checkpoint.get("time_key") != "209.999Ma":
        raise Eng10kContractError("R4_CANDIDATE_CHECKPOINT_TIME_KEY_MISMATCH")
    initial_value = trajectory.get("b0_domain_states", {}).get("initial", {}).get("value", {})
    if initial_value.get("side_states") != initial_rows or tuple(initial_value.get("support_ids", ())) != R4_SUPPORT_IDS:
        raise Eng10kContractError("R4_TYPED_INITIAL_STATE_BINDING_MISMATCH")
    forcing = trajectory.get("b0_forcing_record", {})
    forcing_value = forcing.get("value", {})
    velocity = forcing_value.get("signed_Ux_m_per_year")
    if (forcing.get("forcing_kind") != "FROZEN_INSTANTANEOUS_ENGINEERING_DRIVER"
            or forcing_value.get("signed_Ux_m_per_year") != result["signed_Ux_m_per_year"]
            or forcing_value.get("frame") != "T_F2B_SELECTED_SECTION_NORMAL_PLATE_5_TO_11"
            or tuple(forcing_value.get("support_ids", ())) != R4_SUPPORT_IDS
            or not isinstance(velocity, (int, float)) or isinstance(velocity, bool)
            or not math.isfinite(velocity) or velocity <= 0):
        raise Eng10kContractError("R4_FORCING_RECORD_INVALID")
    return R4ContinuationInputs(
        manifest_sha256=manifest_hash,
        initial_states=start_states, checkpoint_states=checkpoint_states,
        forcing_m_per_year=float(velocity), support_ids=R4_SUPPORT_IDS,
        boundary_id=R4_BOUNDARY_ID,
        source_identity={"r4_execution_commit": R4_SOURCE_COMMIT,
                         "r4_source_composite_sha256": source["source_identity_sha256"],
                         "current_kernel_canonical_sha256": R4_KERNEL_SHA256},
        provider_identities=dict(provider_ids),
        configuration_identity=manifest.get("configuration_sha256", "UNKNOWN"),
    )


def provider_component_bindings_match(current: Mapping[str, str], historical: Mapping[str, str]) -> bool:
    """Compare immutable data-provider identities, excluding HEAD-bound source_set."""
    if set(current) != set(historical) or "source_set" not in current:
        return False
    return all(current[key] == historical[key] for key in current if key != "source_set")


def _sample_record(support_id: str, state: ReducedState, record_type: str) -> dict[str, Any]:
    record = {
        "support_id": support_id, "record_type": record_type,
        "time_s": state.time_s, "elapsed_years": state.time_s / SECONDS_PER_YEAR,
        "width_m": state.width_m, "crust_m": state.crust_m,
        "lithosphere_m": state.lithosphere_m, "beta": state.beta,
        "accumulated_strain": state.accumulated_strain,
        "material_coordinate": list(state.material_coordinate),
        "z_m": [x * state.lithosphere_m for x in state.material_coordinate],
        "temperature_k": list(state.temperature_k),
    }
    if len(canonical_bytes(record)) > MAX_SAMPLE_RECORD_BYTES:
        raise Eng10kContractError("SAMPLE_RECORD_EXCEEDS_PROJECTED_SIZE_BOUND")
    return record


def advance_with_bounded_samples(
    state: ReducedState, *, support_id: str, duration_years: float,
    extension_velocity_m_per_year: float, resolution_factor: float,
    sample_interval_years: float = 10.0,
) -> tuple[ReducedState, dict[str, Any]]:
    """Call the existing kernel; retain scheduled observations, never interpolate."""
    from .functional_development import pure_shear_thermal_step
    for value, label in ((duration_years, "duration"),
                         (extension_velocity_m_per_year, "velocity"),
                         (resolution_factor, "resolution"),
                         (sample_interval_years, "sample_interval")):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise Eng10kContractError(f"NONFINITE_OR_INVALID_{label.upper()}")
    if duration_years <= 0 or extension_velocity_m_per_year <= 0 or sample_interval_years <= 0:
        raise Eng10kContractError("POSITIVE_DURATION_VELOCITY_AND_SAMPLE_INTERVAL_REQUIRED")
    if resolution_factor not in RESOLUTION_FACTORS:
        raise Eng10kContractError("UNQUALIFIED_RESOLUTION_FACTOR")
    samples = [_sample_record(support_id, state, "INITIAL")]
    next_target = (math.floor(state.time_s / SECONDS_PER_YEAR / sample_interval_years) + 1) * sample_interval_years
    missed_schedule_targets = 0

    def observe(current: ReducedState) -> None:
        nonlocal next_target, missed_schedule_targets
        elapsed_years = current.time_s / SECONDS_PER_YEAR
        if elapsed_years >= next_target:
            crossed = math.floor((elapsed_years - next_target) / sample_interval_years) + 1
            if len(samples) >= MAX_RETAINED_SAMPLES_PER_SUPPORT:
                raise Eng10kContractError("RETAINED_DIAGNOSTIC_LIMIT_EXCEEDED")
            samples.append(_sample_record(support_id, current, "SCHEDULED_STEP_SAMPLE"))
            missed_schedule_targets += max(0, crossed - 1)
            next_target += crossed * sample_interval_years

    final, diagnostics = pure_shear_thermal_step(
        state, duration_s=duration_years * SECONDS_PER_YEAR,
        extension_velocity_m_s=extension_velocity_m_per_year / SECONDS_PER_YEAR,
        maximum_kinematic_fraction_per_substep=resolution_factor,
        state_observer=observe,
    )
    final_time_expected = state.time_s + duration_years * SECONDS_PER_YEAR
    time_roundoff_bound_s = max(1, diagnostics.substeps + 1) * math.ulp(final_time_expected)
    time_error_s = final.time_s - final_time_expected
    if abs(time_error_s) > time_roundoff_bound_s:
        raise Eng10kContractError("ELAPSED_TIME_OUTSIDE_FLOATING_POINT_ACCUMULATION_BOUND")
    if samples[-1]["time_s"] == final.time_s:
        samples[-1] = _sample_record(support_id, final, "FINAL_COMPLETE_STATE")
    else:
        if len(samples) >= MAX_RETAINED_SAMPLES_PER_SUPPORT:
            raise Eng10kContractError("RETAINED_DIAGNOSTIC_LIMIT_EXCEEDED")
        samples.append(_sample_record(support_id, final, "FINAL_COMPLETE_STATE"))
    if len(samples) > MAX_RETAINED_SAMPLES_PER_SUPPORT:
        raise Eng10kContractError("RETAINED_DIAGNOSTIC_LIMIT_EXCEEDED")
    captured_steps = len(samples)
    summary = {
        "integration_substeps": diagnostics.substeps,
        "integration_observations_including_initial": diagnostics.substeps + 1,
        "retained_diagnostic_samples": captured_steps,
        "omitted_integration_observations": diagnostics.substeps + 1 - captured_steps,
        "missed_schedule_targets": missed_schedule_targets,
        "sample_interval_years": sample_interval_years,
        "interpolation": "NONE",
        "samples": samples,
        "time_endpoint_expected_s": final_time_expected,
        "time_endpoint_observed_s": final.time_s,
        "time_accumulation_roundoff_bound_s": time_roundoff_bound_s,
        "time_endpoint_delta_s": time_error_s,
    }
    return final, summary


def compare_reduced_states(expected: ReducedState, observed: ReducedState) -> dict[str, Any]:
    """Report fieldwise differences; no acceptance tolerance is applied."""
    scalar_fields = ("time_s", "width_m", "crust_m", "lithosphere_m", "beta", "accumulated_strain")
    result: dict[str, Any] = {"scope": "ENGINEERING_PATH_COMPARISON_NO_SCIENTIFIC_THRESHOLD"}
    for name in scalar_fields:
        left, right = getattr(expected, name), getattr(observed, name)
        delta = abs(left - right)
        result[name] = {"reference": left, "observed": right, "absolute_difference": delta,
                        "relative_difference": (delta / abs(left) if left != 0.0 else
                                                (0.0 if delta == 0.0 else None)),
                        "relative_status": ("DEFINED" if left != 0.0 else
                                            ("BOTH_ZERO" if delta == 0.0 else "UNDEFINED_ZERO_REFERENCE"))}
    if (len(expected.temperature_k) != len(observed.temperature_k)
            or len(expected.material_coordinate) != len(observed.material_coordinate)
            or expected.materials != observed.materials):
        raise Eng10kContractError("STATE_GRID_OR_MATERIAL_IDENTITY_MISMATCH")
    tdelta = [abs(a - b) for a, b in zip(expected.temperature_k, observed.temperature_k)]
    result["temperature_k"] = {
        "node_count": len(tdelta), "maximum_absolute_difference": max(tdelta),
        "maximum_relative_difference": max(
            (d / abs(a) if a != 0 else (0 if d == 0 else math.inf))
            for a, d in zip(expected.temperature_k, tdelta)),
        "identical": expected.temperature_k == observed.temperature_k,
    }
    result["material_coordinate"] = {"identical": expected.material_coordinate == observed.material_coordinate}
    result["materials_identical"] = expected.materials == observed.materials
    return result
