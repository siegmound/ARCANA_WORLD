"""Non-production B6N8-Q adapter around the qualified B6N8-O initializer.

Real ARCANA support is accepted only by the metadata preflight API. Numerical
execution and candidate persistence are restricted to explicit TEST_ fixtures.
This module deliberately has no WORLD_HISTORY or canonical publication API.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Iterable, Mapping, Sequence

from . import pre_orbdata_t0_initializer as provider


P_ATTESTATION = "docs/arcana/qualifications/R6_B6N8P_ATTESTATION.json"
O_ATTESTATION = "docs/arcana/qualifications/R6_B6N8O_ATTESTATION.json"
P_RUN_CONTRACT = "docs/arcana/research/B6N8P_T0_RUN_CONTRACT.json"
P_CANDIDATE_CONTRACT = "docs/arcana/research/B6N8P_T0_CANDIDATE_OUTPUT_CONTRACT.json"
EXPECTED_P_SOURCE = "f79ccef337a72152bdbf13369d01960f3df8cb2d"
EXPECTED_O_SOURCE = "73d98ee14f933622f0d3f18f66985b06f364abcd"
EXPECTED_P_ATTESTATION_SHA = "46623eb606434b6066a8268ccfc2346a76936c5ceb5eb175ff8a2957779b6b55"
EXPECTED_O_ATTESTATION_SHA = "e3be3c02ff4a4b1f14e2953063cafd3aec8a19f0332df2a205fea30e1c07d981"
EXPECTED_P_RUN_CONTRACT_ID = "d2e13a8ab13483f24a8086239cb2b9ee73bba8f8ac4861dbe2bb5c40f35f007a"
EXPECTED_P_RUN_CONTRACT_CANONICAL_SHA = "48d4f5d9a4676425ba137f16c33c7f12aee8bcf4f0cd717484acc5714041b602"
EXPECTED_P_CANDIDATE_CONTRACT_ID = "3530e0242eceb776b84ae3b5dfa45d445ad4a5a6561347b0d21c097731930713"
EXPECTED_ADMITTED_SUPPORT_MEMBERSHIP_SHA = "f61f4a89bacdf458636720ed4df67bd97cc731159bb588f6836e065241e1e499"
EXPECTED_SUPPORT = (64800, 63620, 14258, 49362, 1072, 108)
MANIFEST_SCHEMA = "ARCANA_R6_T0_INITIALIZER_CANDIDATE_RUN_MANIFEST_V1"
REQUIRED_CANDIDATE_FIELDS = (
    "support_id", "time", "initializer_family", "scenario_id", "geometry_reference",
    "model_base_semantics", "model_base_depth_m", "crust_depth_m", "thermal_lab_depth_m",
    "thermal_lab_temperature_k", "moho_temperature_k", "surface_heat_flow_w_m2",
    "vertical_coordinate", "segments", "material_roles", "property_tuple_references",
    "material_property_bindings", "derived_kappa_m2_s", "source_term_references",
    "configuration_identities", "support_lineage", "uncertainty", "provenance",
    "validation_status", "canonical_publication",
)
_SCENARIO_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class AdapterError(RuntimeError):
    """Fail-closed adapter error with a stable machine-readable code."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}:{detail}" if detail else code)


class ExecutionMode(str, Enum):
    SYNTHETIC_TEST = "SYNTHETIC_TEST"
    METADATA_PREFLIGHT = "METADATA_PREFLIGHT"
    REAL_CANDIDATE_EXECUTION = "REAL_CANDIDATE_EXECUTION"


@dataclass(frozen=True)
class ScenarioEntry:
    scenario_id: str
    configuration_identity_sha256: str
    boundary_source_configuration_identity: str
    support_ids: tuple[str, ...]


@dataclass(frozen=True)
class ScenarioRoster:
    roster_id: str
    roster_authority: str
    entries: tuple[ScenarioEntry, ...]
    provenance_sha256: str
    qualified: bool
    readiness_status: str
    non_canonical_test_roster: bool = False

    @property
    def scenario_count(self) -> int:
        return len(self.entries)

    @property
    def identity_sha256(self) -> str:
        return _sha(_canonical(_roster_payload(self)))


@dataclass(frozen=True)
class ExecutionAuthorization:
    run_contract_identity_sha256: str
    provider_source_commit: str
    support_binding_identity_sha256: str
    candidate_output_contract_identity_sha256: str
    scenario_roster_identity_sha256: str | None
    execution_mode: ExecutionMode
    candidate_storage_root: str | None
    publication_policy: str
    real_execution_authorized: bool = False


@dataclass(frozen=True)
class SupportExecutionPlan:
    support_id: str
    support_class: str
    material_roles: tuple[str, str]
    property_tuple_references: tuple[str, str]
    source_term_references: tuple[str, str]
    derived_kappa_m2_s: tuple[float, float]
    geometry_reference: str
    t0_world_age_ma: float
    scenario_roster_status: str
    numerical_profile_evaluation: bool = False
    candidate_output_write: bool = False


@dataclass(frozen=True)
class MetadataPreflight:
    native_support_count: int
    admitted_count: int
    continental_count: int
    positive_age_ocean_count: int
    unresolved_positive_age_ocean_excluded: int
    zero_age_ridge_excluded: int
    admitted_unresolved: int
    admitted_ambiguous: int
    support_plan_count: int
    support_plan_sha256: str
    provider_plan_sha256: str
    scenario_roster_status: str
    numerical_profile_evaluation: bool = False
    candidate_output_write: bool = False


@dataclass(frozen=True)
class CandidateRecord:
    candidate_id: str
    run_id: str
    support_id: str
    scenario_id: str
    configuration_identity_sha256: str
    time_ma: float
    provider_source_commit: str
    output_contract_identity_sha256: str
    payload_sha256: str
    payload: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_text_sha256(data: bytes) -> str:
    """Hash canonical UTF-8/LF text, distinct from raw checkout-byte SHA256."""
    text = data.decode("utf-8")
    return _sha(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def verify_authority_hashes(path_label: str, raw_bytes: bytes, *,
                            expected_file_sha256: str,
                            expected_canonical_text_sha256: str) -> None:
    """Check materialized checkout bytes and canonical text as distinct identities."""
    if _sha(raw_bytes) != expected_file_sha256:
        raise AdapterError("AUTHORITY_MISMATCH", f"FILE_SHA256:{path_label}")
    try:
        canonical_sha = canonical_text_sha256(raw_bytes)
    except UnicodeError as exc:
        raise AdapterError("AUTHORITY_MISMATCH", f"CANONICAL_TEXT_UTF8:{path_label}") from exc
    if canonical_sha != expected_canonical_text_sha256:
        raise AdapterError("AUTHORITY_MISMATCH", f"CANONICAL_TEXT_SHA256:{path_label}")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AdapterError("AUTHORITY_MISMATCH", f"cannot read {path.name}") from exc
    if not isinstance(value, dict):
        raise AdapterError("AUTHORITY_MISMATCH", f"invalid object {path.name}")
    return value


def verify_authority(repository_root: str | Path) -> dict[str, Any]:
    """Verify P/O attestations and exact P-governed byte/text input hashes."""
    root = Path(repository_root).resolve()
    p_att = _read_json(root / P_ATTESTATION)
    o_att = _read_json(root / O_ATTESTATION)
    run_path = root / P_RUN_CONTRACT
    candidate_path = root / P_CANDIDATE_CONTRACT
    run = _read_json(run_path)
    candidate = _read_json(candidate_path)
    if (p_att.get("qualified_source_commit") != EXPECTED_P_SOURCE
            or p_att.get("qualification_status") != "PASS"
            or p_att.get("stage_decision") != "BLOCKED_B6N8P_EXECUTION_CONFIGURATION_INCOMPLETE"):
        raise AdapterError("AUTHORITY_MISMATCH", "B6N8P_ATTESTATION")
    if (o_att.get("qualified_source_commit") != EXPECTED_O_SOURCE
            or o_att.get("qualification_status") != "PASS"
            or o_att.get("qualification_verdict") !=
            "PASS_B6N8O_T0_INITIALIZER_IMPLEMENTATION_QUALIFIED_PRODUCTION_EXECUTION_NOT_AUTHORIZED"):
        raise AdapterError("AUTHORITY_MISMATCH", "B6N8O_ATTESTATION")
    if p_att.get("B6N8O_authority", {}).get("attestation_sha256") != EXPECTED_O_ATTESTATION_SHA:
        raise AdapterError("AUTHORITY_MISMATCH", "P_TO_O_ATTESTATION_BINDING")
    if _sha((root / P_ATTESTATION).read_bytes()) != EXPECTED_P_ATTESTATION_SHA:
        raise AdapterError("AUTHORITY_MISMATCH", "B6N8P_ATTESTATION_HASH")
    if _sha((root / O_ATTESTATION).read_bytes()) != EXPECTED_O_ATTESTATION_SHA:
        raise AdapterError("AUTHORITY_MISMATCH", "B6N8O_ATTESTATION_HASH")
    run_sha = _sha(_canonical(run))
    if (run_sha != EXPECTED_P_RUN_CONTRACT_CANONICAL_SHA
            or run.get("run_contract_identity_sha256") != EXPECTED_P_RUN_CONTRACT_ID
            or p_att.get("storage_and_identity", {}).get("run_contract_identity_sha256")
            != EXPECTED_P_RUN_CONTRACT_ID):
        raise AdapterError("AUTHORITY_MISMATCH", "P_RUN_CONTRACT_HASH")
    candidate_sha = _sha(_canonical(candidate))
    if (candidate_sha != EXPECTED_P_CANDIDATE_CONTRACT_ID
            or run.get("candidate_output_contract_identity_sha256") != EXPECTED_P_CANDIDATE_CONTRACT_ID
            or p_att.get("storage_and_identity", {}).get("candidate_output_contract_identity_sha256")
            != EXPECTED_P_CANDIDATE_CONTRACT_ID):
        raise AdapterError("AUTHORITY_MISMATCH", "P_CANDIDATE_CONTRACT_ID")
    if run.get("decision") != "BLOCKED_B6N8P_EXECUTION_CONFIGURATION_INCOMPLETE":
        raise AdapterError("AUTHORITY_MISMATCH", "P_BLOCKED_DECISION_NOT_PRESERVED")
    if (run.get("execution_adapter_required") is not True
            or run.get("executable_scenario_roster_bound") is not False
            or run.get("executable_scenario_count") is not None
            or run.get("real_T0_execution_ready") is not False
            or run.get("expected_candidate_cardinality") != "63620 × N"):
        raise AdapterError("AUTHORITY_MISMATCH", "P_READINESS_OR_ROSTER_SEMANTICS")
    snapshot = run.get("immutable_input_snapshot", {}).get("B6N8N_index_authorities", [])
    if not snapshot:
        raise AdapterError("AUTHORITY_MISMATCH", "P_INPUT_SNAPSHOT_MISSING")
    snapshot_seal: list[dict[str, str]] = []
    for item in snapshot:
        source = root / item["path"]
        raw_bytes = source.read_bytes()
        verify_authority_hashes(
            item["path"], raw_bytes,
            expected_file_sha256=item["file_sha256"],
            expected_canonical_text_sha256=item["canonical_text_sha256"],
        )
        raw_sha = _sha(raw_bytes)
        canonical_sha = canonical_text_sha256(raw_bytes)
        snapshot_seal.append({"path": item["path"], "file_sha256": raw_sha,
                              "canonical_text_sha256": canonical_sha})
    return {
        "p_source_commit": EXPECTED_P_SOURCE,
        "o_source_commit": EXPECTED_O_SOURCE,
        "p_run_contract_identity_sha256": EXPECTED_P_RUN_CONTRACT_ID,
        "p_run_contract_canonical_sha256": run_sha,
        "candidate_output_contract_identity_sha256": EXPECTED_P_CANDIDATE_CONTRACT_ID,
        "authority_snapshot_count": len(snapshot),
        "authority_snapshot_sha256": _sha(_canonical(snapshot_seal)),
        "authority_hashes": snapshot_seal,
        "p_decision": run["decision"],
        "real_scenario_roster_bound": False,
        "real_scenario_count": None,
        "real_t0_execution_ready": False,
    }


def _roster_payload(roster: ScenarioRoster) -> dict[str, Any]:
    return {
        "roster_id": roster.roster_id,
        "roster_authority": roster.roster_authority,
        "entries": [asdict(item) for item in roster.entries],
        "provenance_sha256": roster.provenance_sha256,
        "qualified": roster.qualified,
        "readiness_status": roster.readiness_status,
        "non_canonical_test_roster": roster.non_canonical_test_roster,
    }


def validate_roster(roster: ScenarioRoster | None, *, synthetic: bool) -> None:
    if roster is None:
        raise AdapterError("SCENARIO_ROSTER_REQUIRED")
    if (not roster.roster_id or not roster.roster_authority or not roster.entries
            or not _SHA256.fullmatch(roster.provenance_sha256)):
        raise AdapterError("SCENARIO_ROSTER_NOT_QUALIFIED", "ROSTER_FIELDS_INVALID")
    ids = [entry.scenario_id for entry in roster.entries]
    if len(ids) != len(set(ids)) or any(not _SCENARIO_ID.fullmatch(item) for item in ids):
        raise AdapterError("SCENARIO_ROSTER_NOT_QUALIFIED", "SCENARIO_ID_INVALID_OR_DUPLICATE")
    if any(not _SHA256.fullmatch(entry.configuration_identity_sha256)
           or not entry.boundary_source_configuration_identity
           or not entry.support_ids or len(entry.support_ids) != len(set(entry.support_ids))
           for entry in roster.entries):
        raise AdapterError("SCENARIO_ROSTER_NOT_QUALIFIED", "SCENARIO_CONFIGURATION_INVALID")
    if synthetic:
        if not (roster.non_canonical_test_roster and roster.roster_authority == "TEST_ONLY"):
            raise AdapterError("SCENARIO_ROSTER_NOT_QUALIFIED", "TEST_ROSTER_MARKER_REQUIRED")
        if any(not support_id.startswith("TEST_Q_") for entry in roster.entries for support_id in entry.support_ids):
            raise AdapterError("UNAUTHORIZED_SUPPORT", "TEST_ROSTER_CONTAINS_NONTEST_SUPPORT")
    else:
        if roster.non_canonical_test_roster or not (roster.qualified and roster.readiness_status == "QUALIFIED"):
            raise AdapterError("SCENARIO_ROSTER_NOT_QUALIFIED")
        if any(support_id.startswith("TEST_") for entry in roster.entries for support_id in entry.support_ids):
            raise AdapterError("UNAUTHORIZED_SUPPORT", "REAL_ROSTER_CONTAINS_TEST_SUPPORT")


def validate_authorization(auth: ExecutionAuthorization, *, expected_mode: ExecutionMode) -> None:
    if auth.execution_mode is not expected_mode:
        raise AdapterError("EXECUTION_NOT_AUTHORIZED", "MODE_MISMATCH")
    if auth.publication_policy != "CANDIDATE_ONLY_NO_CANONICAL_PUBLICATION":
        raise AdapterError("EXECUTION_NOT_AUTHORIZED", "PUBLICATION_POLICY")
    if auth.run_contract_identity_sha256 != EXPECTED_P_RUN_CONTRACT_ID:
        raise AdapterError("AUTHORITY_MISMATCH", "RUN_CONTRACT_IDENTITY")
    if auth.provider_source_commit != EXPECTED_O_SOURCE:
        raise AdapterError("AUTHORITY_MISMATCH", "PROVIDER_IDENTITY")
    if auth.candidate_output_contract_identity_sha256 != EXPECTED_P_CANDIDATE_CONTRACT_ID:
        raise AdapterError("AUTHORITY_MISMATCH", "OUTPUT_CONTRACT_IDENTITY")
    if not _SHA256.fullmatch(auth.support_binding_identity_sha256):
        raise AdapterError("AUTHORITY_MISMATCH", "SUPPORT_BINDING_IDENTITY")
    if expected_mode is ExecutionMode.REAL_CANDIDATE_EXECUTION:
        # Q intentionally has no API path capable of granting this authority.
        raise AdapterError("EXECUTION_NOT_AUTHORIZED", "REAL_T0_EXECUTION_NOT_AUTHORIZED")
    if expected_mode is ExecutionMode.SYNTHETIC_TEST and auth.real_execution_authorized:
        raise AdapterError("EXECUTION_NOT_AUTHORIZED", "SYNTHETIC_AUTH_CANNOT_AUTHORIZE_REAL")


def request_real_execution(authorization: ExecutionAuthorization,
                           roster: ScenarioRoster | None) -> None:
    """Q boundary: check roster first, then reject absent final authorization."""
    validate_roster(roster, synthetic=False)
    validate_authorization(authorization, expected_mode=ExecutionMode.REAL_CANDIDATE_EXECUTION)


def _support_class_roles(support_class: str) -> tuple[tuple[str, str], str]:
    if support_class in {"CONTINENTAL_COLD_STABLE", "CONTINENTAL_NORMAL", "CONTINENTAL_HOT_EXTENDED"}:
        return ("CONTINENTAL_CRUST_REFERENCE", "LITHOSPHERIC_MANTLE_REFERENCE"), "CONTINENTAL_AUTHORED_REFERENCE_GEOMETRY"
    if support_class == "OCEAN_POSITIVE_AGE_ADMITTED":
        return ("OCEANIC_CRUST_REFERENCE", "LITHOSPHERIC_MANTLE_REFERENCE"), "POSITIVE_AGE_HWR2_GEOMETRY"
    raise AdapterError("EXCLUDED_SUPPORT", support_class)


def metadata_preflight(repository_root: str | Path, *,
                       authorization: ExecutionAuthorization) -> tuple[MetadataPreflight, tuple[SupportExecutionPlan, ...]]:
    """Validate all admitted real supports without thermal evaluation or writes."""
    root = Path(repository_root).resolve()
    validate_authorization(authorization, expected_mode=ExecutionMode.METADATA_PREFLIGHT)
    if (authorization.support_binding_identity_sha256 != EXPECTED_ADMITTED_SUPPORT_MEMBERSHIP_SHA
            or authorization.scenario_roster_identity_sha256 is not None
            or authorization.candidate_storage_root is not None):
        raise AdapterError("EXECUTION_NOT_AUTHORIZED", "METADATA_PREFLIGHT_SCOPE_INVALID")
    verify_authority(root)
    try:
        result = provider.preflight_admitted_bindings(root)
        index = _read_json(root / "docs/arcana/research/B6N8N_ADMITTED_SUPPORT_BINDING_INDEX.json")
        registry = _read_json(root / "docs/arcana/research/B6N8N_PROPERTY_TUPLE_BINDING_REGISTRY.json")
        binding_cache = {
            role: provider.role_binding_from_registry(registry, role)
            for role in registry["required_roles"]
        }
        fields_path = root / index["field_package"]["path"]
        import numpy as np
        with np.load(fields_path, allow_pickle=False) as fields:
            domain = fields["physical_crust_domain_id"]
            thermal = fields["continental_thermal_domain_id"]
            age = fields["oceanic_lithosphere_age_ma"]
            selected = set(_read_json(root / "R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json")
                           ["derived_fields"]["oceanic_age"]["selected_source_boundary_ids"])
            boundary = _read_json(root / "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json")["segments"]
            excluded, _, _ = provider._reconstruct_ocean_exclusions(domain, age, boundary, selected)
            plans: list[SupportExecutionPlan] = []
            for row in range(domain.shape[0]):
                for column in range(domain.shape[1]):
                    dom = int(domain[row, column])
                    support_id = provider._cell_id(row, column)
                    if dom in (2, 3, 4, 5, 6):
                        thermal_id = int(thermal[row, column])
                        classes = {1: "CONTINENTAL_COLD_STABLE", 2: "CONTINENTAL_NORMAL", 3: "CONTINENTAL_HOT_EXTENDED"}
                        if thermal_id not in classes:
                            continue
                        support_class = classes[thermal_id]
                    elif dom == 1 and math.isfinite(float(age[row, column])) and float(age[row, column]) > 0 and support_id not in excluded:
                        support_class = "OCEAN_POSITIVE_AGE_ADMITTED"
                    else:
                        continue
                    roles, geometry = _support_class_roles(support_class)
                    bindings = tuple(binding_cache[role] for role in roles)
                    plans.append(SupportExecutionPlan(
                        support_id=support_id, support_class=support_class,
                        material_roles=roles, geometry_reference=geometry,
                        property_tuple_references=tuple(item.tuple_reference for item in bindings),
                        source_term_references=tuple(item.source_term_reference for item in bindings),
                        derived_kappa_m2_s=tuple(item.kappa_reference_m2_s for item in bindings),
                        t0_world_age_ma=provider.T0_WORLD_AGE_MA,
                        scenario_roster_status="REQUIRED_BUT_UNBOUND",
                    ))
        plans.sort(key=lambda plan: plan.support_id)
    except AdapterError:
        raise
    except Exception as exc:
        raise AdapterError("AUTHORITY_MISMATCH", f"METADATA_PREFLIGHT:{exc}") from exc
    counts = (result.native_support_count, result.admitted_count, result.continental_count,
              result.positive_age_ocean_count, result.unresolved_positive_age_ocean_excluded,
              result.zero_age_ridge_excluded)
    if counts != EXPECTED_SUPPORT or len(plans) != 63620:
        raise AdapterError("AUTHORITY_MISMATCH", "SUPPORT_CARDINALITY_MISMATCH")
    digest = hashlib.sha256()
    for plan in plans:
        digest.update(_canonical(asdict(plan)) + b"\n")
    summary = MetadataPreflight(
        native_support_count=result.native_support_count,
        admitted_count=result.admitted_count,
        continental_count=result.continental_count,
        positive_age_ocean_count=result.positive_age_ocean_count,
        unresolved_positive_age_ocean_excluded=result.unresolved_positive_age_ocean_excluded,
        zero_age_ridge_excluded=result.zero_age_ridge_excluded,
        admitted_unresolved=result.admitted_unresolved,
        admitted_ambiguous=result.admitted_ambiguous,
        support_plan_count=len(plans), support_plan_sha256=digest.hexdigest(),
        provider_plan_sha256=result.deterministic_plan_sha256,
        scenario_roster_status="REQUIRED_BUT_UNBOUND",
    )
    return summary, tuple(plans)


def _candidate_root(path: str | Path, repository_root: str | Path) -> Path:
    root = Path(path).expanduser().resolve()
    repository = Path(repository_root).resolve()
    try:
        root.relative_to(repository)
    except ValueError:
        pass
    else:
        raise AdapterError("EXECUTION_NOT_AUTHORIZED", "CANDIDATE_ROOT_INSIDE_REPOSITORY")
    if any("WORLD_HISTORY" in part.upper() for part in root.parts):
        raise AdapterError("EXECUTION_NOT_AUTHORIZED", "WORLD_HISTORY_PATH_FORBIDDEN")
    if root == Path(root.anchor):
        raise AdapterError("EXECUTION_NOT_AUTHORIZED", "UNSAFE_CANDIDATE_ROOT")
    return root


def candidate_identity(*, run_id: str, support_id: str, scenario_id: str,
                       configuration_identity_sha256: str, time_ma: float,
                       provider_source_commit: str, output_contract_identity_sha256: str) -> str:
    required_sha = (configuration_identity_sha256, output_contract_identity_sha256)
    if any(not _SHA256.fullmatch(value) for value in required_sha):
        raise AdapterError("INVALID_CONFIGURATION", "IDENTITY_HASH_INVALID")
    if not run_id or not support_id or not _SCENARIO_ID.fullmatch(scenario_id) or not math.isfinite(time_ma):
        raise AdapterError("INVALID_CONFIGURATION", "CANDIDATE_IDENTITY_FIELDS_INVALID")
    return _sha(_canonical({
        "run_id": run_id, "support_id": support_id, "scenario_id": scenario_id,
        "configuration_identity_sha256": configuration_identity_sha256,
        "time_ma": time_ma, "provider_source_commit": provider_source_commit,
        "output_contract_identity_sha256": output_contract_identity_sha256,
    }))


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except OSError as exc:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise AdapterError("CANDIDATE_WRITE_FAILURE", str(path.name)) from exc


def _run_identity(auth: ExecutionAuthorization, roster: ScenarioRoster,
                  support_ids: Sequence[str], authority: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    support_digest = _sha(_canonical(sorted(support_ids)))
    body = {
        "run_contract_identity_sha256": auth.run_contract_identity_sha256,
        "provider_source_commit": auth.provider_source_commit,
        "support_binding_identity_sha256": auth.support_binding_identity_sha256,
        "support_membership_sha256": support_digest,
        "candidate_output_contract_identity_sha256": auth.candidate_output_contract_identity_sha256,
        "scenario_roster_identity_sha256": roster.identity_sha256,
        "execution_mode": auth.execution_mode.value,
        "publication_policy": auth.publication_policy,
        "candidate_storage_policy": "EXTERNAL_NONCANONICAL_STAGING",
        "authority_snapshot_sha256": authority["authority_snapshot_sha256"],
        "authority_hashes": authority["authority_hashes"],
    }
    return _sha(_canonical(body)), body


def _candidate_tasks(fixtures: Sequence[provider.SyntheticColumnFixture],
                     roster: ScenarioRoster, chunk_size: int):
    """Yield only explicitly roster-assigned support/scenario pairs in batches."""
    by_support = {fixture.binding.support_id: fixture for fixture in fixtures}
    for offset in range(0, len(fixtures), chunk_size):
        support_batch = fixtures[offset:offset + chunk_size]
        allowed = {fixture.binding.support_id for fixture in support_batch}
        for entry in roster.entries:
            for support_id in entry.support_ids:
                if support_id in allowed:
                    yield by_support[support_id], entry


def validate_candidate_set(records: Sequence[CandidateRecord], *, expected_count: int,
                           roster: ScenarioRoster) -> dict[str, Any]:
    validate_roster(roster, synthetic=True)
    keys = [(r.support_id, r.scenario_id, r.configuration_identity_sha256) for r in records]
    if len(records) != expected_count:
        raise AdapterError("INCOMPLETE_RUN", "CANDIDATE_COUNT_MISMATCH")
    if len(keys) != len(set(keys)) or len({r.candidate_id for r in records}) != len(records):
        raise AdapterError("MANIFEST_MISMATCH", "DUPLICATE_CANDIDATE")
    scenario_by_id = {e.scenario_id: e for e in roster.entries}
    for record in records:
        entry = scenario_by_id.get(record.scenario_id)
        if (entry is None or entry.configuration_identity_sha256 != record.configuration_identity_sha256
                or record.time_ma != provider.T0_WORLD_AGE_MA
                or record.provider_source_commit != EXPECTED_O_SOURCE
                or record.output_contract_identity_sha256 != EXPECTED_P_CANDIDATE_CONTRACT_ID
                or record.candidate_id != candidate_identity(
                    run_id=record.run_id, support_id=record.support_id,
                    scenario_id=record.scenario_id,
                    configuration_identity_sha256=record.configuration_identity_sha256,
                    time_ma=record.time_ma,
                    provider_source_commit=record.provider_source_commit,
                    output_contract_identity_sha256=record.output_contract_identity_sha256,
                )
                or _sha(_canonical(dict(record.payload))) != record.payload_sha256
                or any(field not in record.payload for field in REQUIRED_CANDIDATE_FIELDS)
                or record.payload.get("time", {}).get("selector") != "T0"
                or record.payload.get("validation_status") != "SYNTHETIC_FIXTURE_NUMERICALLY_VALIDATED"
                or record.payload.get("canonical_publication") is not False
                or record.payload.get("support_id") != record.support_id):
            raise AdapterError("MANIFEST_MISMATCH", "CANDIDATE_PROVENANCE_OR_HASH_INVALID")
        if not record.support_id.startswith("TEST_Q_"):
            raise AdapterError("UNAUTHORIZED_SUPPORT", record.support_id)
    ordered = sorted(records, key=lambda r: (r.support_id, r.scenario_id, r.configuration_identity_sha256))
    return {"candidate_count": len(ordered), "candidate_ids": [r.candidate_id for r in ordered],
            "validation_status": "STRUCTURALLY_VALIDATED_SYNTHETIC_ONLY"}


def validate_synthetic_result(result: provider.InitializerResult) -> None:
    provider.validate_initializer_result(result)
    if not result.support_id.startswith("TEST_Q_"):
        raise AdapterError("UNAUTHORIZED_SUPPORT", result.support_id)
    if result.surface_datum != "LOCAL_MODEL_SURFACE_Z0" or not result.segments:
        raise AdapterError("INVALID_GEOMETRY", result.support_id)
    sample_depths = {0.0, result.crust_depth_m, result.thermal_lab_depth_m}
    temperatures = [result.temperature_at(depth) for depth in sample_depths]
    if not all(math.isfinite(value) for value in temperatures):
        raise AdapterError("NUMERICAL_FAILURE", "NONFINITE_TEMPERATURE")


def run_synthetic_candidates(*, repository_root: str | Path,
                             authorization: ExecutionAuthorization,
                             roster: ScenarioRoster | None,
                             fixtures: Sequence[provider.SyntheticColumnFixture],
                             chunk_size: int = 32,
                             fail_after: int | None = None) -> dict[str, Any]:
    """Numerically run TEST-only fixtures and persist resumable candidates."""
    authority = verify_authority(repository_root)
    validate_authorization(authorization, expected_mode=ExecutionMode.SYNTHETIC_TEST)
    validate_roster(roster, synthetic=True)
    assert roster is not None
    if chunk_size <= 0:
        raise AdapterError("INVALID_CONFIGURATION", "CHUNK_SIZE_MUST_BE_POSITIVE")
    if not fixtures:
        raise AdapterError("INCOMPLETE_RUN", "EMPTY_SUPPORT_SET")
    support_ids = [fixture.binding.support_id for fixture in fixtures]
    if (len(support_ids) != len(set(support_ids))
            or any(not support_id.startswith("TEST_Q_") for support_id in support_ids)):
        raise AdapterError("UNAUTHORIZED_SUPPORT", "SYNTHETIC_FIXTURE_IDS_INVALID")
    if authorization.scenario_roster_identity_sha256 != roster.identity_sha256:
        raise AdapterError("AUTHORITY_MISMATCH", "ROSTER_IDENTITY")
    if authorization.candidate_storage_root is None:
        raise AdapterError("EXECUTION_NOT_AUTHORIZED", "CANDIDATE_ROOT_REQUIRED")
    root = _candidate_root(authorization.candidate_storage_root, repository_root)
    run_id, run_body = _run_identity(authorization, roster, support_ids, authority)
    run_dir = root / run_id
    manifest_path = run_dir / "RUN_MANIFEST.json"
    if manifest_path.exists():
        prior = _read_json(manifest_path)
        if prior.get("run_id") != run_id or prior.get("run_identity") != run_body:
            raise AdapterError("MANIFEST_MISMATCH", "CROSS_RUN_RESUME")
        if prior.get("status") == "COMPLETE_CANDIDATE_SET":
            saved = _verify_existing_records(run_dir, prior)
            validate_candidate_set(tuple(saved.values()),
                                  expected_count=prior["expected_candidate_count"], roster=roster)
            return prior
    run_dir.mkdir(parents=True, exist_ok=True)
    existing: dict[str, CandidateRecord] = {}
    if manifest_path.exists():
        prior = _read_json(manifest_path)
        existing = _verify_existing_records(run_dir, prior)
    roster_by_id = {entry.scenario_id: entry for entry in roster.entries}
    fixture_ids = set(support_ids)
    assigned_ids = {support_id for entry in roster.entries for support_id in entry.support_ids}
    if assigned_ids != fixture_ids:
        raise AdapterError("UNAUTHORIZED_SUPPORT", "ROSTER_FIXTURE_ASSIGNMENT_MISMATCH")
    expected_count = sum(len(entry.support_ids) for entry in roster.entries)
    for fixture in fixtures:
        if not isinstance(fixture, provider.SyntheticColumnFixture) or not fixture.non_canonical_test_fixture:
            raise AdapterError("UNAUTHORIZED_SUPPORT", "NONCANONICAL_FIXTURE_REQUIRED")
        if not fixture.fixture_name.startswith("NON_CANONICAL_"):
            raise AdapterError("UNAUTHORIZED_SUPPORT", "FIXTURE_NAME_REQUIRED")
    records: list[CandidateRecord] = list(existing.values())
    _write_manifest(manifest_path, run_id, run_body, authorization, roster,
                    status="PLANNED", expected_count=expected_count, records=records)
    status = "RUNNING"
    _write_manifest(manifest_path, run_id, run_body, authorization, roster,
                    status=status, expected_count=expected_count, records=records)
    try:
        for fixture, entry in _candidate_tasks(fixtures, roster, chunk_size):
            candidate_id = candidate_identity(
                run_id=run_id, support_id=fixture.binding.support_id,
                scenario_id=entry.scenario_id,
                configuration_identity_sha256=entry.configuration_identity_sha256,
                time_ma=provider.T0_WORLD_AGE_MA,
                provider_source_commit=EXPECTED_O_SOURCE,
                output_contract_identity_sha256=EXPECTED_P_CANDIDATE_CONTRACT_ID,
            )
            if candidate_id in {record.candidate_id for record in records}:
                continue
            # Q accepts no scenario mutation/override. A roster entry must name
            # the exact synthetic fixture configuration already bound by O.
            fixture_config = fixture.binding.configuration_identities
            if entry.configuration_identity_sha256 not in fixture_config.values():
                raise AdapterError("AUTHORITY_MISMATCH", "FIXTURE_CONFIGURATION_NOT_IN_ROSTER")
            result = provider.evaluate_synthetic_fixture(fixture)
            validate_synthetic_result(result)
            raw_payload = json.loads(result.serialize().decode("utf-8"))
            raw_payload["scenario_id"] = entry.scenario_id
            raw_payload["candidate_id"] = candidate_id
            raw_payload["run_id"] = run_id
            raw_payload["candidate_state"] = ["CANDIDATE", "UNPUBLISHED", "NON_CANONICAL", "VALIDATION_PENDING"]
            payload_sha = _sha(_canonical(raw_payload))
            record = CandidateRecord(
                candidate_id, run_id, fixture.binding.support_id, entry.scenario_id,
                entry.configuration_identity_sha256, provider.T0_WORLD_AGE_MA,
                EXPECTED_O_SOURCE, EXPECTED_P_CANDIDATE_CONTRACT_ID, payload_sha, raw_payload,
            )
            _atomic_write(run_dir / f"{candidate_id}.json", _canonical(record.to_dict()) + b"\n")
            records.append(record)
            if fail_after is not None and len(records) >= fail_after:
                raise AdapterError("INCOMPLETE_RUN", "SIMULATED_INTERRUPTION")
        _write_manifest(manifest_path, run_id, run_body, authorization, roster,
                        status="VALIDATION_PENDING", expected_count=expected_count, records=records)
        validated = validate_candidate_set(records, expected_count=expected_count, roster=roster)
        status = "COMPLETE_CANDIDATE_SET"
        _write_manifest(manifest_path, run_id, run_body, authorization, roster,
                        status=status, expected_count=expected_count, records=records,
                        validation=validated)
        return _read_json(manifest_path)
    except Exception as exc:
        _write_manifest(manifest_path, run_id, run_body, authorization, roster,
                        status="INCOMPLETE", expected_count=expected_count,
                        records=records, failure_code=getattr(exc, "code", "EXECUTION_FAILURE"))
        raise


def _write_manifest(path: Path, run_id: str, run_body: Mapping[str, Any],
                    auth: ExecutionAuthorization, roster: ScenarioRoster, *,
                    status: str, expected_count: int, records: Sequence[CandidateRecord],
                    validation: Mapping[str, Any] | None = None,
                    failure_code: str | None = None) -> None:
    manifest = {
        "schema": MANIFEST_SCHEMA, "run_id": run_id, "run_identity": dict(run_body),
        "status": status, "completion_status": status,
        "provider_source_commit": auth.provider_source_commit,
        "adapter": "B6N8Q_REAL_SUPPORT_EXECUTION_ADAPTER_V1",
        "run_contract_identity_sha256": auth.run_contract_identity_sha256,
        "candidate_output_contract_identity_sha256": auth.candidate_output_contract_identity_sha256,
        "scenario_roster": {"roster_id": roster.roster_id,
                             "identity_sha256": roster.identity_sha256,
                             "scenario_count": roster.scenario_count,
                             "non_canonical_test_roster": roster.non_canonical_test_roster},
        "support_count": len({r.support_id for r in records}),
        "expected_candidate_count": expected_count,
        "candidate_count": len(records),
        "candidate_hashes": sorted(r.payload_sha256 for r in records),
        "candidate_ids": sorted(r.candidate_id for r in records),
        "validation": dict(validation or {"status": "PENDING"}),
        "publication_status": "UNPUBLISHED_NO_CANONICAL_PUBLICATION",
        "failure_code": failure_code,
        "real_t0_execution_ready": False,
    }
    _atomic_write(path, _canonical(manifest) + b"\n")


def _verify_existing_records(run_dir: Path, manifest: Mapping[str, Any]) -> dict[str, CandidateRecord]:
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise AdapterError("MANIFEST_MISMATCH", "SCHEMA")
    records: dict[str, CandidateRecord] = {}
    expected_ids = manifest.get("candidate_ids", [])
    expected_files = {f"{candidate_id}.json" for candidate_id in expected_ids} | {"RUN_MANIFEST.json"}
    actual_files = {path.name for path in run_dir.glob("*.json")}
    if actual_files != expected_files or len(expected_ids) != len(set(expected_ids)):
        raise AdapterError("MANIFEST_MISMATCH", "UNLISTED_OR_DUPLICATE_CANDIDATE_FILE")
    for candidate_id in expected_ids:
        path = run_dir / f"{candidate_id}.json"
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            payload = record["payload"]
            candidate = CandidateRecord(
                record["candidate_id"], record["run_id"], record["support_id"],
                record["scenario_id"], record["configuration_identity_sha256"],
                record["time_ma"], record["provider_source_commit"],
                record["output_contract_identity_sha256"], record["payload_sha256"], payload,
            )
        except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise AdapterError("MANIFEST_MISMATCH", f"CANDIDATE_RECORD_INVALID:{candidate_id}") from exc
        if _sha(_canonical(candidate.to_dict())) != _sha(_canonical(record)):
            raise AdapterError("MANIFEST_MISMATCH", f"CANDIDATE_RECORD_HASH:{candidate_id}")
        if _sha(_canonical(dict(payload))) != candidate.payload_sha256:
            raise AdapterError("MANIFEST_MISMATCH", f"CANDIDATE_PAYLOAD_HASH:{candidate_id}")
        if (candidate.run_id != manifest.get("run_id")
                or candidate.candidate_id != candidate_identity(
                    run_id=candidate.run_id, support_id=candidate.support_id,
                    scenario_id=candidate.scenario_id,
                    configuration_identity_sha256=candidate.configuration_identity_sha256,
                    time_ma=candidate.time_ma,
                    provider_source_commit=candidate.provider_source_commit,
                    output_contract_identity_sha256=candidate.output_contract_identity_sha256,
                )):
            raise AdapterError("MANIFEST_MISMATCH", f"CANDIDATE_IDENTITY:{candidate_id}")
        records[candidate_id] = candidate
    if len(records) != manifest.get("candidate_count"):
        raise AdapterError("MANIFEST_MISMATCH", "CANDIDATE_COUNT")
    if sorted(record.payload_sha256 for record in records.values()) != manifest.get("candidate_hashes"):
        raise AdapterError("MANIFEST_MISMATCH", "CANDIDATE_HASH_LIST")
    return records

