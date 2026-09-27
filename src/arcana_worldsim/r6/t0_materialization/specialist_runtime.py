"""Build the integrated, evidence-backed B-v2 specialist materialization gate.

This module inventories parent artifacts and local runtime availability. It
does not synthesize scientific fields or invoke third-party engines.
"""
from __future__ import annotations

import hashlib
import json
import platform
import shutil
from pathlib import Path
from typing import Any


REPORT_JSON = "R6_T0_B_PANGAEA_LIKE_V2_SPECIALIST_MATERIALIZATION.json"
REPORT_MD = "R6_T0_B_PANGAEA_LIKE_V2_SPECIALIST_MATERIALIZATION.md"

PARENT_FILES = (
    "R6_T0_B_PANGAEA_LIKE_V2_MATERIALIZATION_REPORT.json",
    "R6_T0_B_PANGAEA_LIKE_V2_MATERIALIZATION_REPORT.md",
    "R6_TECTONIC_T0_MATERIALIZATION_IMPLEMENTATION.json",
    "R6_TECTONIC_AUTHORIAL_PRIMITIVE_CONSTRAINTS.json",
    "R6_TECTONIC_T0_MATERIALIZATION_DESIGN.json",
    "R6_SHELLSET_MINIMUM_THERMOMECHANICAL_STATE_CONTRACT.json",
    "R6_SHELLSET_PRERUNTIME_INPUT_CLOSURE.json",
    "R6_SHELLSET_FEG_BC_CONTRACT.json",
    "R6_SHELLSET_MESH_PROVIDER_ADAPTER_CLOSURE.json",
    "R6_T0_CANONICAL_BOUNDARY_BRANCH_REGISTRY.json",
    "R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json",
    "R6_T0_B_PANGAEA_LIKE_V2_MODEL_CONFIGURATION_CANDIDATES.json",
    "R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz",
    "R6_SHELLSET_T0_RUNTIME_INPUT_MANIFEST_CANDIDATE_B_V2.json",
)

REFERENCE_FAMILIES = (
    "rhoBar_crust", "rhoBar_mantle", "rhoAst", "rhoH2O",
    "alphaT_crust_mantle", "conductivity_crust_mantle",
    "radiogenic_heat_production_crust_mantle",
    "surface_temperature_and_temperature_limits", "TADIAB_GRADIE_ZBASTH",
    "gravity_gMean", "radius",
)
RHEOLOGY_FAMILIES = (
    "CFRIC", "FFRIC", "BIOT", "BYERLY", "ACREEP(1)", "ACREEP(2)",
    "BCREEP(1)", "BCREEP(2)", "CCREEP(1)", "CCREEP(2)",
    "DCREEP(1)", "DCREEP(2)", "ECREEP",
)
RHEOLOGY_SOURCE_FAMILIES = {
    "CFRIC": "continuum low-temperature effective friction",
    "FFRIC": "fault-only friction; inactive for Level 1 nFl=0",
    "BIOT": "pore-pressure/effective-stress coefficient; source convention unpinned",
    "BYERLY": "master-fault strength reduction; inactive for Level 1 nFl=0",
    "ACREEP(1)": "crust creep prefactor",
    "ACREEP(2)": "mantle creep prefactor",
    "BCREEP(1)": "crust creep activation parameter",
    "BCREEP(2)": "mantle creep activation parameter",
    "CCREEP(1)": "crust pressure/depth activation parameter",
    "CCREEP(2)": "mantle pressure/depth activation parameter",
    "DCREEP(1)": "crust creep strength cap",
    "DCREEP(2)": "mantle creep strength cap",
    "ECREEP": "inverse stress exponent shared by the selected creep laws",
}


def _read_json(root: Path, name: str) -> dict[str, Any]:
    value = json.loads((root / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{name} must contain a JSON object")
    return value


def runtime_inventory() -> dict[str, dict[str, Any]]:
    """Report PATH-visible runtimes only; never launch or install them."""
    candidates = {
        "GWB": ("worldbuilder", "gwb", "WorldBuilder"),
        "OrbData5": ("OrbData5", "orbdata5", "orbdata"),
        "SHELLS": ("Shells", "shells"),
        "ShellSet": ("ShellSet", "shellset"),
    }
    result = {}
    for name, commands in candidates.items():
        found = next(((command, shutil.which(command)) for command in commands
                      if shutil.which(command)), None)
        result[name] = {
            "commands_checked": list(commands),
            "available_on_path": found is not None,
            "resolved_command": found[0] if found else None,
            "resolved_path": found[1] if found else None,
            "version": None,
            "qualification": "NOT_RUN" if found else "BLOCKED_RUNTIME_NOT_FOUND",
        }
    return result


def build_report(root: str | Path,
                 runtimes: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    missing = [name for name in PARENT_FILES if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError("missing required parent artifacts: " + ", ".join(missing))

    parent = _read_json(root, PARENT_FILES[0])
    implementation = _read_json(root, PARENT_FILES[2])
    design = _read_json(root, PARENT_FILES[4])
    minimum = _read_json(root, PARENT_FILES[5])
    preruntime = _read_json(root, PARENT_FILES[6])
    feg_contract = _read_json(root, PARENT_FILES[7])
    mesh = _read_json(root, PARENT_FILES[8])
    branches = _read_json(root, PARENT_FILES[9])
    manifest = _read_json(root, PARENT_FILES[10])
    config = _read_json(root, PARENT_FILES[11])
    runtime_manifest = _read_json(root, PARENT_FILES[13])
    runtimes = runtimes if runtimes is not None else runtime_inventory()

    if parent["authorial_realization_id"] != "B_PANGAEA_LIKE_LATE_TRIASSIC_v2":
        raise ValueError("B-v2 realization identity changed")
    if parent["canonical_parent_hashes"]["vector_partition"] != (
        "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
    ):
        raise ValueError("canonical partition identity changed")
    if parent["mesh_hash"] != (
        "6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad"
    ):
        raise ValueError("canonical mesh identity changed")

    hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
              for name in PARENT_FILES}
    materialized = parent["normalized_field_hashes"]
    physical = [
        "physical_crust_domain_id", "crustal_thickness_m",
        "continental_thermal_domain_id",
        "continental_reference_surface_heat_flow_w_m2",
        "continental_reference_lithosphere_thickness_m",
        "oceanic_lithosphere_age_ma", "ocean_surface_authorial_residual_m",
    ]
    already = [{"field": field, "normalized_sha256": materialized[field],
                "status": "MATERIALIZED_UPSTREAM"} for field in physical]
    already.extend([
        {"field": "canonical_land_surface_elevation_m",
         "normalized_sha256": materialized["canonical_land_surface_elevation_m"],
         "status": "CANONICAL_LAND_SUPPORT_ONLY"},
        {"field": "unknown_total_ocean_elevation_mask",
         "normalized_sha256": materialized["unknown_total_ocean_elevation_mask"],
         "status": "UNKNOWN_MASK_NOT_NUMERIC_ELEVATION"},
    ])
    specialist_pending = list(parent["pending_specialist_fields"])
    design_assignments = design["materializer_assignments"]
    assignments = [{
        "field": row["field"], "candidate": row["candidate"],
        "parent_status": row["status"],
        "runtime_qualification": "NOT_RUN",
    } for row in design_assignments]

    reference_rows = config["reference_physical_parameters"]["families"]
    if len(reference_rows) != 11:
        raise ValueError("expected 11 reference physical parameter families")
    reference_dispositions = []
    for row in reference_rows:
        status = "CANONICAL_VALUE_BOUND__RUNTIME_CONVENTION_UNVERIFIED" if row["selected"] else "PENDING_VERSION_PINNED_PHYSICAL_CONFIGURATION"
        value = (9.82 if row["id"] == "gravity_gMean" else
                 6_371_000 if row["id"] == "radius" else None)
        reference_dispositions.append({
            "parameter": row["id"], "units": row["units"], "value": value,
            "status": status,
            "authority": "CANONICAL_PLANETARY_CONSTANT" if row["selected"] else "EARTH_LIKE_MODEL_CONFIGURATION_NOT_YET_GOVERNED",
            "rationale": row["constraint"],
        })

    rheology_rows = config["rheology"]["contract"]["configuration_families"]
    if len(RHEOLOGY_FAMILIES) != 13 or len(rheology_rows) != 10:
        raise ValueError("rheology contract shape changed; reconcile its 13 families before reporting")
    rheology = []
    for family in RHEOLOGY_FAMILIES:
        inactive = family in {"FFRIC", "BYERLY"}
        rheology.append({
            "parameter_family": family,
            "meaning": RHEOLOGY_SOURCE_FAMILIES[family],
            "baseline_value": None,
            "status": "INACTIVE_LEVEL1_NO_FAULT_ELEMENTS" if inactive else "PENDING_PINNED_SHELLS_SOURCE_AND_GOVERNED_BASELINE",
        })

    blockers = []
    if not any(row["available_on_path"] for row in runtimes.values()):
        blockers.append("No GWB, OrbData5, SHELLS, or ShellSet executable is available on PATH; specialist version/build smoke and T0 transformation cannot run here.")
    blockers.extend([
        "The design does not select and version-pin the approved ocean plate-cooling/isostatic materializer.",
        "Ocean thermal state, ocean heat flow, ocean mantle-lithosphere thickness, and the thermal/isostatic elevation component remain unmaterialized.",
        "The current age field is an authoritative T0 input; its plate-cooling consequences require the approved specialist runtime and must not be regenerated.",
        "Global elevation, global heat flow, continental geotherm support, chemical_delta_rho, and cooling_curvature do not yet have complete governed FEG-node fields.",
        "Nine noncanonical reference-parameter families and the numerical ShellSet rheology baseline/sensitivity members remain unselected; ShellSet source/version semantics are not pinned locally.",
        "The runtime manifest remains incomplete and runtime_authorized=false; no scientific SHELLS_READY FEG can be written.",
    ])

    report = {
        "schema": "R6_T0_B_PANGAEA_LIKE_V2_SPECIALIST_MATERIALIZATION_V1",
        "principal_decision": "R6_T0_B_PANGAEA_LIKE_V2_SPECIALIST_PARTIAL__MATERIALIZER_RUNTIME_BLOCKED",
        "parent_state": {
            "parent_decision": parent["principal_decision"],
            "realization_id": parent["authorial_realization_id"],
            "authorial_status": parent["authorial_status"],
            "canonical_status": parent["canonical_status"],
            "t0_ma": 210,
            "canonical_geography_sha256": parent["canonical_parent_hashes"]["physical_geography"],
            "canonical_partition_sha256": parent["canonical_parent_hashes"]["vector_partition"],
            "mesh_sha256": parent["mesh_hash"],
            "upstream_field_package_sha256": parent["field_package_sha256"],
            "historical_bootstrap_sha256": implementation["parent_state"]["bootstrap_sha256"],
            "plates": implementation["parent_state"]["topology"]["plates"],
            "boundary_segments": branches["boundary_segment_count"],
            "branches": branches["branch_count"], "junctions": branches["junction_count"],
            "canonical_state_changed": False,
        },
        "pending_field_ledger": {
            "ALREADY_MATERIALIZED": already,
            "PENDING_SPECIALIST_RUNTIME": specialist_pending,
            "PENDING_MODEL_CONFIGURATION": {
                "reference_parameter_families": [x["parameter"] for x in reference_dispositions if x["value"] is None],
                "rheology_families": [x["parameter_family"] for x in rheology if x["baseline_value"] is None],
            },
            "PENDING_NUMERICAL_PROJECTION": [
                "Project governed cell-domain crust/thermal fields to the 64,442-node FEG support with a validated interpolation/error policy.",
                "Project specialist-complete global elevation and heat-flow fields to FEG nodes with lineage per node.",
            ],
            "NOT_REQUIRED": [
                "External absolute lithostatic pressure, EOS density, mineral phase fractions, and a 3-D gravity field; the parent minimum-state contract says SHELLS/OrbData derives or does not consume them.",
                "OrbData5 only if direct ARCANA/specialist producers supply every required physical field with equivalent governed provenance; that condition is not met in this report.",
                "Fault elements and fault-only mechanical values in Level 1 (nFl=0).",
                "Earth observational geography/grids and Earth OrbScore calibration.",
                "SHELLS mechanical solve, finite-time evolution, dt, and t1 at this stage.",
            ],
            "UNKNOWN": [
                "Exact selected/version-pinned plate-cooling/isostatic engine and its local availability.",
                "Exact pinned ShellSet/SHELLS and OrbData source builds and parser conventions.",
                "Computational reference-frame behavior and global gauge; explicitly deferred to runtime qualification.",
                "Whether a validated OrbData-free producer can supply chemical_delta_rho and cooling_curvature without changing their contract semantics.",
            ],
        },
        "specialist_runtime_qualification": {
            "host_os": platform.platform(), "python": platform.python_version(),
            "runtimes": runtimes,
            "wsl": {"available": shutil.which("wsl.exe") is not None,
                    "qualification": "PRESENT_BUT_DISTRIBUTION_QUERY_DENIED"},
            "official_build_qualification": "BLOCKED_NOT_RUN",
            "minimal_smoke": "BLOCKED_NOT_RUN",
            "authorized_t0_transformations": "BLOCKED_NOT_RUN",
            "orbdata_necessity": {
                "decision": "NOT_REQUIRED_IF_ALL_GOVERNED_FIELDS_ARE_PRECOMPUTED",
                "current_assessment": "CANNOT_SKIP_FOR_CURRENT_PARENT_STATE: chemical_delta_rho and cooling_curvature plus several global fields are not supplied by current ARCANA materializers; OrbData is also not installed/qualified.",
                "earth_fallback_prohibited": True,
            },
        },
        "literature_basis": [
            {
                "citation": "Stein and Stein (1992), Nature 359, 123-129",
                "doi": "10.1038/359123a0",
                "use": "Supports using a plate-cooling formulation fitted jointly to age-depth and heat-flow behavior for mature oceanic lithosphere; it supplies no ARCANA observations or field values.",
            },
            {
                "citation": "Holdt et al. (2025), Revised Oceanic Plate Cooling Models, JGR Solid Earth",
                "doi": "10.1029/2024JB029890",
                "use": "Documents the old-age limitation of half-space cooling and plate-model alternatives; method rationale only, not an Earth observational input to ARCANA.",
            },
            {
                "citation": "May, Bird, and Carafa (2024), ShellSet v1.1.0, Geoscientific Model Development 17, 6153-6171",
                "doi": "10.5194/gmd-17-6153-2024",
                "use": "Confirms the ShellSet parameter-family and model roles; does not validate a local build or select ARCANA parameter values.",
            },
        ],
        "materializer_versions": assignments,
        "oceanic_thermal_state": {
            "age_input_authoritative": True,
            "age_input_sha256": materialized["oceanic_lithosphere_age_ma"],
            "age_field_regenerated": False,
            "thermal_state": "PENDING_SPECIALIST_RUNTIME",
            "heat_flow_w_m2": "PENDING_SPECIALIST_RUNTIME",
            "mantle_lithosphere_thickness_m": "PENDING_SPECIALIST_RUNTIME",
            "bathymetric_component_m": "PENDING_SPECIALIST_RUNTIME",
            "approved_plate_model": "NOT_SELECTED_OR_VERSION_PINNED",
            "half_space_extended_to_160_ma": False,
        },
        "global_heat_flow": {
            "status": "INCOMPLETE_CONTINENTAL_SUPPORT_ONLY",
            "continental_domain_references_w_m2": {"COLD_STABLE": 0.045, "NORMAL": 0.060, "HOT_EXTENDED": 0.085},
            "oceanic_field": "MISSING",
            "global_field": "MISSING",
            "positive_complete_node_support": False,
            "per_node_lineage": "NOT_YET_ASSEMBLED",
            "earth_heat_flow_grid_used": False,
            "zero_sentinel_used": False,
        },
        "complete_elevation": {
            "status": "INCOMPLETE_LAND_SUPPORT_PLUS_OCEAN_RESIDUAL_COMPONENT",
            "land_elevation_sha256": materialized["canonical_land_surface_elevation_m"],
            "ocean_residual_sha256": materialized["ocean_surface_authorial_residual_m"],
            "residual_regenerated": False,
            "thermal_isostatic_component": "MISSING",
            "complete_global_surface": False,
            "earth_terrain_used": False,
        },
        "crustal_state": {
            "status": "UPSTREAM_GRID_MATERIALIZED__FEG_NODE_PROJECTION_PENDING",
            "crustal_thickness_sha256": materialized["crustal_thickness_m"],
            "domain_counts_cells": parent["physical_crust_domain_counts_cells"],
            "authorial_field_overwritten": False,
        },
        "lithosphere_thickness": {
            "continental": "UPSTREAM_THERMAL_DOMAIN_REFERENCES_MATERIALIZED__NODE_PROJECTION_PENDING",
            "oceanic": "PENDING_APPROVED_AGE_TO_THERMAL_SPECIALIST",
            "global_node_field": "MISSING",
        },
        "thermal_state": {
            "continental_domains": parent["thermal_domain_area_fractions"],
            "continental_profile": "PENDING_GOVERNED_GEOTHERM_CONFIGURATION_AND_MATERIALIZER",
            "temperature_nodes_authored": False,
        },
        "chemical_density_anomaly": {
            "field": "chemical_delta_rho", "status": "PENDING_SPECIALIST_OR_VALID_EQUIVALENT",
            "zero_assumption_selected": False,
            "reason": "The contract defines a node-wise isostatic/lithosphere correction; no source-valid zero assumption or numeric bound is selected.",
        },
        "cooling_curvature": {
            "status": "PENDING_ORBDATA_OR_VALID_EQUIVALENT",
            "arbitrary_zero_used": False,
            "reason": "The parent defines this as a derived/adjusted thermal field; no governed source is available.",
        },
        "reference_physical_configuration": {
            "configuration_id": None, "status": "INCOMPLETE__9_OF_11_FAMILIES_UNSELECTED",
            "earth_example_defaults_used": False,
            "families": reference_dispositions,
        },
        "rheology_configuration": {
            "baseline_id": None, "baseline_status": "NOT_SELECTED_OR_SOURCE_PINNED",
            "sensitivity_members": [],
            "sensitivity_status": "NOT_DEFINED",
            "earth_orbscore_ranking_used": False,
            "level1_fault_policy": {"nFl": 0, "FFRIC_active": False, "BYERLY_active": False},
            "families": rheology,
            "optional_TRHMAX_TAUMAX": "NOT_SELECTED; source activation is unverified",
        },
        "FEG_status": {
            "pre_orbdata_fegs": 0, "shells_ready_fegs": 0,
            "status": "BLOCKED_REQUIRED_GOVERNED_FIELDS_AND_NODE_PROJECTIONS_MISSING",
            "mesh_sha256": mesh["determinism_validation"]["normalized_sha256"],
            "nodes": mesh["mesh_topology_audit"]["node_count"],
            "triangles": mesh["mesh_topology_audit"]["triangle_count"],
            "expected_fault_elements": 0, "FEG_sha256": None,
            "round_trip": "NOT_RUN_NO_SCIENTIFIC_FEG",
            "topology_contract": "PRESERVED_FROM_VALIDATED_PARENT",
            "contract_required_nodal_fields": [
                row["name"] for row in minimum["shells_consumed_nodal_state"]["minimum_node_fields"]
            ],
            "projection_policy_status": feg_contract.get("provider_and_adapter", {}).get(
                "physical_field_projection", "NOT_CLOSED_OR_NOT_REPORTED"
            ),
        },
        "runtime_manifest": {
            "path": "R6_SHELLSET_T0_RUNTIME_INPUT_MANIFEST_CANDIDATE_B_V2.json",
            "status": runtime_manifest["status"],
            "runtime_authorized": runtime_manifest["runtime_authorized"],
            "sha256": hashes[PARENT_FILES[13]],
        },
        "replay_validation": {
            "upstream_field_package_sha256": parent["field_package_sha256"],
            "upstream_replay_validation": parent["replay_validation"],
            "integrated_report_input_sha256": hashes,
            "integrated_materialization_replay": "NOT_RUN_NO_SPECIALIST_RUNTIME",
        },
        "remaining_blockers": blockers,
        "upstream_contract_decisions": {
            "minimum_thermomechanical_state": minimum["decision"],
            "pre_runtime_input_closure": preruntime["decision"],
            "feg_bc_contract": feg_contract["decision"],
            "mesh_adapter": mesh["principal_decision"],
            "physical_authority": design["decision"],
            "authorial_status": manifest["authorial_status"],
        },
        "shellset_runtime_readiness": "NOT_READY__SPECIALIST_FIELDS_CONFIGURATIONS_NODE_PROJECTION_AND_MANIFEST_INCOMPLETE",
        "governance": {
            "canonical_candidate_promoted": False,
            "canonical_payload_mutated": False,
            "earth_observational_data_used": False,
            "shellset_mechanics_executed": False,
            "runtime_qualification_authorized": False,
            "forward_evolution": False, "dt_created": False, "t1_created": False,
        },
        "next_stage": "QUALIFY_APPROVED_SPECIALIST_RUNTIMES_ON_FAIR_THEN_RESUME_B_V2_T0_MATERIALIZATION",
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    ledger = report["pending_field_ledger"]
    lines = [
        "# R6 B-Pangaea-like v2 specialist materialization", "",
        f"**Decision:** `{report['principal_decision']}`", "",
        "## Parent state", "",
        f"- Realization: `{report['parent_state']['realization_id']}` at T0 = {report['parent_state']['t0_ma']} Ma; still a candidate.",
        f"- Geography `{report['parent_state']['canonical_geography_sha256']}`, partition `{report['parent_state']['canonical_partition_sha256']}`.",
        f"- Mesh `{report['parent_state']['mesh_sha256']}`; upstream field package `{report['parent_state']['upstream_field_package_sha256']}`.",
        "- Canonical state was not modified.", "",
        "## Exact pending-field ledger at entry", "",
        "### ALREADY_MATERIALIZED", "",
    ]
    lines.extend(f"- `{x['field']}` — {x['status']}; SHA256 `{x['normalized_sha256']}`." for x in ledger["ALREADY_MATERIALIZED"])
    lines.extend(["", "### PENDING_SPECIALIST_RUNTIME", ""])
    lines.extend(f"- {x}" for x in ledger["PENDING_SPECIALIST_RUNTIME"])
    lines.extend(["", "### PENDING_MODEL_CONFIGURATION", "",
                  f"- Reference parameters: {', '.join(ledger['PENDING_MODEL_CONFIGURATION']['reference_parameter_families'])}.",
                  f"- Rheology families: {', '.join(ledger['PENDING_MODEL_CONFIGURATION']['rheology_families'])}.",
                  "", "### PENDING_NUMERICAL_PROJECTION", ""])
    lines.extend(f"- {x}" for x in ledger["PENDING_NUMERICAL_PROJECTION"])
    for category in ("NOT_REQUIRED", "UNKNOWN"):
        lines.extend(["", f"### {category}", ""])
        lines.extend(f"- {x}" for x in ledger[category])
    lines.extend(["", "## Runtime and field result", "",
                  f"- Specialist qualification: {report['specialist_runtime_qualification']['official_build_qualification']}; smoke: {report['specialist_runtime_qualification']['minimal_smoke']}.",
                  f"- Ocean heat flow: {report['global_heat_flow']['oceanic_field']}; global heat flow: {report['global_heat_flow']['global_field']}.",
                  f"- Complete elevation: `{report['complete_elevation']['status']}`.",
                  f"- Mantle-lithosphere thickness: oceanic `{report['lithosphere_thickness']['oceanic']}`; no global nodal field.",
                  f"- `chemical_delta_rho`: {report['chemical_density_anomaly']['status']}; no zero placeholder.",
                  f"- Cooling curvature: {report['cooling_curvature']['status']}; no arbitrary zero.",
                  f"- FEGs: PRE_ORBDATA {report['FEG_status']['pre_orbdata_fegs']}; SHELLS_READY {report['FEG_status']['shells_ready_fegs']}.",
                  "- Runtime manifest remains incomplete and unauthorized.", "",
                  "## Configuration status", "",
                  f"Reference configuration: {report['reference_physical_configuration']['status']}. Two canonical constants are bound; nine other families remain open.",
                  f"Rheology: {report['rheology_configuration']['baseline_status']}; no sensitivity members were generated.",
                  "Level 1 retains nFl=0; fault-only parameters are inactive.", "",
                  "## Why execution stopped", ""])
    lines.extend(f"- {x}" for x in report["remaining_blockers"])
    lines.extend(["", "## Gate", "",
                  f"ShellSet runtime readiness: `{report['shellset_runtime_readiness']}`.",
                  "ShellSet mechanics, OrbData, forward evolution, dt, and t1 were not run or created. The B-v2 candidate was not promoted.", ""])
    return "\n".join(lines)
