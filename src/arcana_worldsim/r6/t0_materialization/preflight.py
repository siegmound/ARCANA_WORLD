"""Build deterministic materialization artifacts without inventing T0 values.

The governing authorial template currently leaves each world-defining choice
null. This module emits a candidate envelope and a preflight report, and blocks
physical field/FEG export until those choices and their materializers are
authorized and configured.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

AUTHORIAL_CONSTRAINTS = "R6_TECTONIC_AUTHORIAL_PRIMITIVE_CONSTRAINTS.json"
MATERIALIZATION_DESIGN = "R6_TECTONIC_T0_MATERIALIZATION_DESIGN.json"
SELECTION_TEMPLATE = "R6_TECTONIC_T0_AUTHORIAL_SELECTION_TEMPLATE.json"
RUNTIME_TEMPLATE = "R6_SHELLSET_T0_RUNTIME_INPUT_MANIFEST_TEMPLATE.json"
MESH_CLOSURE = "R6_SHELLSET_MESH_PROVIDER_ADAPTER_CLOSURE.json"
BRANCH_REGISTRY = "R6_T0_CANONICAL_BOUNDARY_BRANCH_REGISTRY.json"

OUTPUT_CANDIDATES = "R6_TECTONIC_T0_AUTHORIAL_REALIZATION_CANDIDATES.json"
OUTPUT_REPORT = "R6_TECTONIC_T0_MATERIALIZATION_IMPLEMENTATION.json"
OUTPUT_MARKDOWN = "R6_TECTONIC_T0_MATERIALIZATION_IMPLEMENTATION.md"

EXPECTED_MESH_SHA256 = "6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad"
EXPECTED_PARTITION_SHA256 = "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
EXPECTED_BOOTSTRAP_SHA256 = "27bdaa065146981d425088db06c7f989c1099e64e4b30d920b04c979d01331bf"


def _read_json(root: Path, name: str) -> dict[str, Any]:
    value = json.loads((root / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{name} must contain a JSON object")
    return value


def _sha256(value: Any) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def build_artifacts(root: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return candidate-envelope and report objects derived from parent files."""
    root = Path(root).resolve()
    constraints = _read_json(root, AUTHORIAL_CONSTRAINTS)
    design = _read_json(root, MATERIALIZATION_DESIGN)
    selection = _read_json(root, SELECTION_TEMPLATE)
    runtime_template = _read_json(root, RUNTIME_TEMPLATE)
    mesh = _read_json(root, MESH_CLOSURE)
    branches = _read_json(root, BRANCH_REGISTRY)

    primitives = constraints["minimum_authorial_vector"]
    choices_by_id = {row["choice_id"]: row for row in selection["choices"]}
    if len(primitives) != 4 or len(choices_by_id) != 4:
        raise ValueError("expected exactly four governed authorial primitives")
    if any(row.get("default") is not None for row in choices_by_id.values()):
        raise ValueError("selection template unexpectedly contains an authorial default")

    unresolved = [
        {"choice_id": choice_id, "primitive_id": choices_by_id[choice_id]["primitive_id"],
         "status": "HUMAN_AUTHORIAL_SELECTION_REQUIRED",
         "parent_constraint": choices_by_id[choice_id]["allowed_constraint_or_range"]}
        for choice_id in sorted(choices_by_id)
    ]
    ref_parameters = design["reference_material_parameter_contract"]["parameter_families"]
    rheology_contract = design["rheology_contract"]
    rheology_parameter_count = int(rheology_contract.get("parameters_families_count", 13))
    if rheology_parameter_count != 13:
        raise ValueError("parent rheology contract no longer states 13 parameter families")

    canonical = constraints["canonical_t0"]
    identities = {
        "physical_geography_sha256": canonical["physical_geography_payload_sha256"],
        "vector_partition_sha256": canonical["vector_partition_sha256"],
        "kinematics_sha256": canonical["canonical_kinematics_sha256"],
        "historical_bootstrap_identity_sha256": canonical["historical_bootstrap_identity_sha256"],
    }
    if (canonical["time_ma"] != 210 or canonical["plate_count"] != 12
            or canonical["parent_face_count"] != 64_800
            or canonical["shared_boundary_segment_count"] != 1_983
            or canonical["canonical_branch_count"] != 30
            or canonical["degree3_junction_count"] != 20
            or identities["vector_partition_sha256"] != EXPECTED_PARTITION_SHA256
            or identities["historical_bootstrap_identity_sha256"] != EXPECTED_BOOTSTRAP_SHA256):
        raise ValueError("canonical R6 T0 identity/count invariant changed")

    mesh_identity = mesh["determinism_validation"]["normalized_sha256"]
    if mesh_identity != EXPECTED_MESH_SHA256:
        raise ValueError("canonical numerical mesh identity changed")
    if (mesh["mesh_topology_audit"]["node_count"] != 64_442
            or mesh["mesh_topology_audit"]["triangle_count"] != 128_880
            or branches["branch_count"] != 30
            or branches["boundary_segment_count"] != 1_983
            or branches["junction_count"] != 20):
        raise ValueError("mesh/branch topology invariant changed")

    choices = [{
        "choice_id": row["choice_id"],
        "primitive_id": row["primitive_id"],
        "selected_value": None,
        "status": "HUMAN_AUTHORIAL_SELECTION_REQUIRED",
        "candidate_forms": row["allowed_constraint_or_range"],
        "uncertainty_class": row["uncertainty_class"],
    } for row in selection["choices"]]
    candidate = {
        "artifact": "R6_TECTONIC_T0_AUTHORIAL_REALIZATION_CANDIDATES",
        "schema_version": "1.0.0",
        "status": "UNRESOLVED_CANDIDATE_ENVELOPE_NOT_A_REALIZATION",
        "canonical_status": False,
        "candidate_realizations": [],
        "candidate_envelopes": [{
            "candidate_id": "ARCANA_R6_T0_AUTHORIAL_SELECTION_PENDING",
            "canonical_status": False,
            "candidate_state": "BLOCKED_UNRESOLVED_AUTHORIAL_SELECTION",
            "primitive_selections": choices,
            "remaining_unresolved_human_choices": unresolved,
            "scientific_uncertainty_policy": {
                "axes": constraints["ensemble_policy"]["recommended_axes"],
                "sampling_authorized": False,
                "seed": None,
                "seed_determines_authorial_choices": False,
                "earth_observation_or_orbscore_selection": False,
            },
            "derived_field_expectations": [
                "ocean thermal/isostatic fields only after pinned model selection",
                "heat flow and thermal structure only from authorized specialist outputs",
                "UNKNOWN support remains explicit; no imputation",
            ],
            "materializer_dependencies": design["materializer_assignments"],
        }],
        "parent_template_status": selection["status"],
        "parent_constraint_decision": constraints["decision"],
    }

    pending = [
        "ocean elevation/bathymetry support",
        "physical crust domains and crustal thickness",
        "oceanic lithosphere age",
        "ocean thermal profile and thermal/isostatic depth",
        "continental thermal profile and structural state",
        "heat flow",
        "mantle-lithosphere thickness",
        "chemical density anomaly",
        "cooling curvature",
    ]
    report = {
        "schema": "R6_TECTONIC_T0_MATERIALIZATION_IMPLEMENTATION_V1",
        "principal_decision": "R6_T0_MATERIALIZATION_PARTIAL__AUTHORIAL_VALUES_REQUIRED",
        "parent_state": {
            "required_mesh_parent_decision": "R6_SHELLSET_MESH_ADAPTER_IMPLEMENTED__READY_FOR_AUTHORIAL_SELECTION_AND_MATERIALIZATION",
            "observed_mesh_decision": mesh["principal_decision"],
            "t0_ma": canonical["time_ma"],
            "canonical_identities": identities,
            "canonical_partition_mutated": False,
            "canonical_payload_mutated": False,
            "bootstrap_identity_sha256": EXPECTED_BOOTSTRAP_SHA256,
            "numerical_mesh_sha256": mesh_identity,
            "mesh_nodes": 64_442,
            "mesh_triangles": 128_880,
            "plates": canonical["plate_count"],
            "parent_faces": canonical["parent_face_count"],
            "boundary_segments": canonical["shared_boundary_segment_count"],
            "branches": canonical["canonical_branch_count"],
            "junctions": canonical["degree3_junction_count"],
        },
        "authorial_candidate_set": {
            "authorial_primitive_families": len(primitives),
            "candidate_authorial_realizations": 0,
            "unresolved_candidate_envelopes": 1,
            "primitive_selections_concretely_resolved": 0,
            "human_authorial_choices_still_unresolved": len(unresolved),
            "candidate_artifact": OUTPUT_CANDIDATES,
            "candidate_artifact_sha256": _sha256(candidate),
            "candidate_is_canonical": False,
        },
        "human_choices_remaining": unresolved,
        "scientific_uncertainty_axes": {
            "count": len(constraints["ensemble_policy"]["recommended_axes"]),
            "axes": constraints["ensemble_policy"]["recommended_axes"],
            "distinct_from_authorial_choices": True,
            "sampling_executed": False,
            "sampling_seed": None,
        },
        "materializer_execution": {
            "authorized_materializers_executed": [],
            "selected_and_version_pinned_materializers": 0,
            "shellset_or_orbdata_executed": False,
            "forward_evolution": False,
            "reason": "No primitive realization or materializer/version/configuration is selected in the governing parent contracts.",
        },
        "materialized_fields": {
            "new_physical_field_families": 0,
            "existing_canonical_land_elevation_rewritten": False,
            "unknown_ocean_bathymetry_imputed": False,
            "field_package_generated": False,
            "field_package_sha256": None,
        },
        "pending_specialist_fields": {"count": len(pending), "fields": pending},
        "reference_parameter_candidates": {
            "reference_physical_parameter_families": len(ref_parameters),
            "reference_parameters_resolved": sum(1 for item in ref_parameters if item["class"] == "ALREADY_CANONICAL"),
            "canonical_values": {"gravity_gMean": 9.82, "radius": 6_371_000},
            "candidate_configurations": 0,
            "unselected_families": [item["id"] for item in ref_parameters if item["class"] != "ALREADY_CANONICAL"],
            "family_assessments": [
                {**item, "resolution_status": (
                    "CANONICAL_VALUE_PRESENT__SOURCE_CONVENTION_BINDING_STILL_REQUIRED"
                    if item["class"] == "ALREADY_CANONICAL"
                    else "UNSELECTED_GOVERNED_MODEL_OR_REFERENCE_PARAMETER")}
                for item in ref_parameters
            ],
            "earth_example_defaults_used": False,
        },
        "rheology_configuration_set": {
            "rheology_parameter_families": rheology_parameter_count,
            "families": ["CFRIC", "FFRIC", "BIOT", "BYERLY", "ACREEP(1)", "ACREEP(2)",
                         "BCREEP(1)", "BCREEP(2)", "CCREEP(1)", "CCREEP(2)",
                         "DCREEP(1)", "DCREEP(2)", "ECREEP"],
            "optional_model_controls_not_counted_as_families": ["TRHMAX", "TAUMAX"],
            "candidate_configurations": 0,
            "policy": rheology_contract["ensemble_policy"],
            "configuration_authority": "SPECIALIST_MODEL_CONFIGURATION",
            "runtime_execution_authorized": False,
            "earth_orbscore_ranking_used": False,
        },
        "FEG_projection": {
            "provider": mesh["selected_mesh_provider"],
            "provider_version": mesh["provider_version"],
            "mesh_sha256": mesh_identity,
            "topology_preserved": True,
            "physical_values_projected": False,
        },
        "PRE_ORBDATA_outputs": {"fegs_generated": 0, "status": "BLOCKED_NO_AUTHORIZED_COMPLETE_ELEVATION_AND_HEAT_FLOW"},
        "SHELLS_READY_outputs": {"fegs_generated": 0, "status": "BLOCKED_REQUIRED_GOVERNED_FIELDS_UNAVAILABLE"},
        "runtime_manifest_candidates": {
            "count": 0,
            "template_status": runtime_template["status"],
            "template_sha256": hashlib.sha256((root / RUNTIME_TEMPLATE).read_bytes()).hexdigest(),
            "runtime_authorized": False,
            "forward_evolution_authorized": False,
        },
        "replay_validation": {
            "candidate_input_sha256": _sha256(candidate),
            "report_normalized_sha256": None,
            "same_inputs_same_artifact": True,
            "scientific_materialization_replayed": False,
            "deterministic_mesh_sha256": mesh_identity,
        },
        "remaining_blockers": [
            "All four authorial T0 primitive selections remain null.",
            "The parent defines no numeric ARCANA bounds or authorized realization rule for the ocean residual or crust template.",
            "No selected/pinned ocean-cooling, geotherm, crust-grid, or OrbData materializer is executable under the parent contract.",
            "No ShellSet reference material family, rheology configuration, or computational reference-frame policy is selected.",
        ],
        "runtime_qualification_readiness": "NOT_READY; authorial realization and required model configuration are unresolved",
        "governance": {
            "one_candidate_canonical": False,
            "authorial_ratification_required": True,
            "shellset_runtime_qualification_authorized": False,
            "first_interval_authorized": False,
            "dt_or_t1_created": False,
            "canonical_state_changed": False,
        },
        "next_stage": "AUTHORIAL_SELECTION_AND_PINNED_MATERIALIZER_CONFIGURATION",
    }
    report["replay_validation"]["report_normalized_sha256"] = _sha256(
        {key: value for key, value in report.items() if key != "replay_validation"})
    return candidate, report


def render_markdown(report: dict[str, Any]) -> str:
    choices = report["human_choices_remaining"]
    uncertainty = report["scientific_uncertainty_axes"]["axes"]
    pending = report["pending_specialist_fields"]["fields"]
    return "\n".join([
        "# R6 T0 authorial realization and materialization implementation", "",
        f"**Decision:** `{report['principal_decision']}`", "",
        "## Candidate and world choices", "",
        "Four primitive families are governed, but the selection template leaves each required value null. The output contains one unresolved candidate envelope and zero concrete authorial realizations; nothing is canonical.", "",
        *[f"- `{row['choice_id']}` ({row['primitive_id']}): **{row['status']}**" for row in choices], "",
        "## Scientific uncertainty", "",
        "These axes are distinct from authorial world choices. No sampling was authorized or run:", "",
        *[f"- {axis}" for axis in uncertainty], "",
        "## Materialization status", "",
        "No new physical field family was materialized. Existing canonical land elevation was left intact and the unknown ocean mask was not imputed. No field package or runtime manifest candidate was emitted.", "",
        f"Pending specialist field families ({report['pending_specialist_fields']['count']}):", "",
        *[f"- {field}" for field in pending], "",
        f"Reference physical parameter families: {report['reference_parameter_candidates']['reference_physical_parameter_families']}; canonical values resolved: {report['reference_parameter_candidates']['reference_parameters_resolved']} (gravity and radius). No candidate parameter configuration was produced.", "",
        f"Rheology parameter families: {report['rheology_configuration_set']['rheology_parameter_families']}; governed candidate configurations: 0.", "",
        f"PRE_ORBDATA FEGs: 0 ({report['PRE_ORBDATA_outputs']['status']}). SHELLS_READY FEGs: 0 ({report['SHELLS_READY_outputs']['status']}).", "",
        "## Preserved numerical state", "",
        f"- Mesh: `{report['parent_state']['numerical_mesh_sha256']}`; {report['parent_state']['mesh_nodes']:,} nodes and {report['parent_state']['mesh_triangles']:,} triangles.",
        f"- Canonical topology: {report['parent_state']['plates']} plates, {report['parent_state']['parent_faces']:,} faces, {report['parent_state']['boundary_segments']:,} boundary segments, {report['parent_state']['branches']} branches, {report['parent_state']['junctions']} junctions.",
        f"- Bootstrap: `{report['parent_state']['bootstrap_identity_sha256']}`. No canonical state changed.", "",
        "## Gate", "",
        "Authorial ratification is required. ShellSet runtime qualification remains unauthorized; no mechanics, OrbData, `dt`, t1, or forward state was run or created.", "",
        "Replay hashes cover the deterministic candidate envelope/report metadata and the previously validated mesh identity. They do not claim a scientific materialization replay.", "",
    ])
