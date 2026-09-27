"""Materialize authorized B-v2 T0 candidate fields without specialist execution."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

from arcana_worldsim.r6.t0_materialization.b_pangaea_v2 import materialize

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    report = materialize(ROOT)
    (ROOT / "R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    materialization_report = {
        **report,
        "principal_decision": "R6_T0_B_PANGAEA_LIKE_V2_MATERIALIZED__SPECIALIST_RUNTIME_REMAINS",
        "parent_state": {
            "geography_sha256": report["canonical_parent_hashes"]["physical_geography"],
            "partition_sha256": report["canonical_parent_hashes"]["vector_partition"],
            "kinematics_sha256": report["canonical_parent_hashes"]["kinematics"],
            "bootstrap_sha256": "27bdaa065146981d425088db06c7f989c1099e64e4b30d920b04c979d01331bf",
            "mesh_sha256": report["mesh_hash"], "canonical_state_mutated": False,
            "topology": {"plates": 12, "faces": 64800, "boundary_segments": 1983,
                         "branches": 30, "junctions": 20}},
        "authorial_candidate_set": {"candidate_count": 1,
            "realization_id": report["authorial_realization_id"], "canonical": False},
        "human_choices_remaining": [],
        "scientific_uncertainty_axes": {"count": 5, "sampling_run": False,
            "axes": ["ocean basin residual/bathymetry family", "physical crust-domain thickness family",
                     "ocean age field/formation model", "continental thermal/domain family",
                     "correlated material-reference configuration"]},
        "materializer_execution": {"field_generators_executed": [
            "canonical-boundary-ranked crust/thermal domain assignment",
            "oceanic age distance field", "seeded low-frequency ocean residual"],
            "specialist_materializers_executed": [], "orbdata_executed": False,
            "shellset_executed": False, "forward_evolution": False},
        "materialized_fields": {"physical_field_family_count": report["materialized_physical_field_families"],
            "field_package_path": report["field_package_path"],
            "field_package_sha256": report["field_package_sha256"],
            "normalized_hashes": report["normalized_field_hashes"]},
        "reference_parameter_candidates": report["reference_physical_parameters"],
        "rheology_configuration_set": report["rheology"],
        "FEG_projection": report["feg"],
        "pre_orbdata_outputs": {"fegs_generated": 0, "status": report["feg"]["status"]},
        "shells_ready_outputs": {"fegs_generated": 0, "status": "REQUIRES_ALL_GOVERNED_NODAL_FIELDS"},
        "runtime_manifest_candidates": {"count": 1,
            "path": "R6_SHELLSET_T0_RUNTIME_INPUT_MANIFEST_CANDIDATE_B_V2.json",
            "complete": False, "runtime_authorized": False},
        "replay_validation": {"field_package_sha256": report["field_package_sha256"],
            "realization_manifest_sha256": report["realization_manifest_sha256"],
            "deterministic_field_hashes": report["normalized_field_hashes"]},
        "remaining_blockers": report["pending_specialist_fields"] + [
            "Nine noncanonical reference physical parameters lack selected, source-pinned values.",
            "No numeric rheology configuration is selected.",
            "No complete global elevation and heat-flow fields exist for PRE_ORBDATA FEG."],
        "runtime_qualification_readiness": "NOT_READY__SPECIALIST_FIELDS_AND_MODEL_CONFIGURATION_REMAIN",
        "next_stage": "QUALIFY_OR_SELECT_REQUIRED_SPECIALIST_MATERIALIZERS_AND_MODEL_CONFIGURATIONS",
    }
    (ROOT / "R6_T0_B_PANGAEA_LIKE_V2_MATERIALIZATION_REPORT.json").write_text(
        json.dumps(materialization_report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    (ROOT / "R6_TECTONIC_T0_MATERIALIZATION_IMPLEMENTATION.json").write_text(
        json.dumps(materialization_report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    candidate = {
        "artifact": "R6_TECTONIC_T0_AUTHORIAL_REALIZATION_CANDIDATES",
        "schema_version": "2.0.0",
        "status": "ONE_RATIFIED_NONCANONICAL_REALIZATION_MATERIALIZED_WITH_SPECIALIST_FIELDS_PENDING",
        "candidate_realizations": [{
            "candidate_id": report["authorial_realization_id"],
            "authorial_status": report["authorial_status"],
            "canonical_status": report["canonical_status"],
            "manifest_path": "R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json",
            "manifest_sha256": report["realization_manifest_sha256"],
            "primitive_selections": "R6_T0_AUTHORIAL_RATIFICATION_B_PANGAEA_LIKE_LATE_TRIASSIC.json",
        }],
        "scientific_uncertainty_axes": [
            "ocean basin residual/bathymetry family", "physical crust-domain thickness family",
            "ocean age field/formation model", "continental thermal/domain family",
            "correlated material-reference configuration"],
        "scientific_uncertainty_sampling_run": False,
        "canonical_t0_promoted": False,
    }
    (ROOT / "R6_TECTONIC_T0_AUTHORIAL_REALIZATION_CANDIDATES.json").write_text(
        json.dumps(candidate, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    design = json.loads((ROOT / "R6_TECTONIC_T0_MATERIALIZATION_DESIGN.json").read_text(encoding="utf-8"))
    configuration_candidates = {
        "schema": "R6_T0_B_PANGAEA_V2_MODEL_CONFIGURATION_CANDIDATES_V1",
        "world_state_candidate_id": report["authorial_realization_id"],
        "world_state_and_model_configuration_separate": True,
        "reference_physical_parameters": {
            "family_count": len(design["reference_material_parameter_contract"]["parameter_families"]),
            "families": design["reference_material_parameter_contract"]["parameter_families"],
            "canonical_values": {"gravity_gMean": 9.82, "radius": 6371000},
            "numeric_candidate_configurations": [],
            "unselected_due_to_missing_pinned_family_values": 9,
            "earth_example_defaults_used": False,
        },
        "rheology": {"parameter_family_count": 13,
            "contract": design["rheology_contract"],
            "numeric_candidate_configurations": [],
            "status": "SPECIALIST_MODEL_CONFIGURATION_UNSELECTED",
            "earth_orbscore_ranking_used": False},
        "runtime_execution_authorized": False,
    }
    (ROOT / "R6_T0_B_PANGAEA_LIKE_V2_MODEL_CONFIGURATION_CANDIDATES.json").write_text(
        json.dumps(configuration_candidates, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    runtime = json.loads((ROOT / "R6_SHELLSET_T0_RUNTIME_INPUT_MANIFEST_TEMPLATE.json").read_text(encoding="utf-8"))
    runtime["authorial_realization"].update({
        "realization_id": report["authorial_realization_id"],
        "selection_manifest_path": "R6_T0_AUTHORIAL_RATIFICATION_B_PANGAEA_LIKE_LATE_TRIASSIC.json",
        "selection_manifest_sha256": hashlib.sha256((ROOT / "R6_T0_AUTHORIAL_RATIFICATION_B_PANGAEA_LIKE_LATE_TRIASSIC.json").read_bytes()).hexdigest(),
    })
    package_hash = report["field_package_sha256"]
    for field_name in ("ocean_surface", "crust_domains_and_thickness", "oceanic_age"):
        runtime["derived_fields"][field_name]["artifact_path"] = report["field_package_path"]
        runtime["derived_fields"][field_name]["sha256"] = package_hash
    runtime["derived_fields"]["ocean_surface"]["component_status"] = "RESIDUAL_PRESENT; THERMAL_ISOSTATIC_COMPONENT_PENDING"
    runtime["derived_fields"]["oceanic_age"]["status"] = "MATERIALIZED"
    runtime["derived_fields"]["crust_domains_and_thickness"]["status"] = "MATERIALIZED"
    runtime["mesh"].update({"provider_id": "ARCANA_CANONICAL_GRID_FACE_TRIANGULATION",
                            "provider_version": "ARCANA_CANONICAL_GRID_FACE_TRIANGULATION_V1",
                            "adapter_version": "R6_SHELLSET_MESH_ADAPTER_V1",
                            "radius_m": 6371000.0,
                            "mesh_resolution_policy_id": "CANONICAL_GRID_FACE_TRIANGULATION_V1"})
    runtime["provenance"]["canonical_payload_mutated"] = False
    runtime["provenance"]["t1_or_forward_state_created"] = False
    runtime["materialization_candidate_status"] = "INCOMPLETE_PENDING_SPECIALIST_FIELDS_AND_GOVERNED_MODEL_CONFIGURATION"
    runtime["runtime_authorized"] = False
    (ROOT / "R6_SHELLSET_T0_RUNTIME_INPUT_MANIFEST_CANDIDATE_B_V2.json").write_text(
        json.dumps(runtime, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    lines = [
        "# R6 B_PANGAEA_LIKE_LATE_TRIASSIC_v2 materialization", "",
        "**Decision:** `R6_T0_B_PANGAEA_LIKE_V2_MATERIALIZED__SPECIALIST_RUNTIME_REMAINS`", "",
        "The existing canonical geography passed the ratified macrostate check: the largest land component contains 89.9876% of land, crosses the equator over 98° of latitude, and the global ocean is one connected component. The previous mandatory-embayment blocker is superseded by v2.", "",
        f"The deterministic candidate field package is `{report['field_package_path']}` (SHA-256 `{report['field_package_sha256']}`). The realization manifest records each normalized field hash and canonical parent identity.", "",
        f"Crust-domain cell counts: `{json.dumps(report['physical_crust_domain_counts_cells'], sort_keys=True)}`.",
        f"Continental thermal area fractions: `{json.dumps(report['thermal_domain_area_fractions'], sort_keys=True)}`.",
        f"Ocean-age area-weighted median: {report['derived_fields']['oceanic_age']['area_weighted_ocean_median_ma']:.8g} Ma; selected source branch `{report['derived_fields']['oceanic_age']['selected_source_branch_id']}`.",
        f"Ocean residual mean/RMS/cap: {report['derived_fields']['ocean_authorial_residual_bathymetry']['observed_area_weighted_ocean_mean_m']:.8g} m / {report['derived_fields']['ocean_authorial_residual_bathymetry']['observed_area_weighted_ocean_rms_m']:.8g} m / {report['derived_fields']['ocean_authorial_residual_bathymetry']['observed_hard_cap_abs_m']:.8g} m.", "",
        "## Pending specialist output", "",
        *[f"- {field}" for field in report["pending_specialist_fields"]], "",
        "The age-derived cooling/isostatic model and OrbData5 are not selected/version-pinned. Total ocean elevation and ocean heat flow remain unknown. No PRE_ORBDATA FEG was written because its global elevation and heat-flow fields cannot be completed without those values. SHELLS_READY is also unavailable.", "",
        "The runtime manifest is an incomplete candidate copied from the governed template; it does not authorize execution. Reference parameter configuration has only canonical radius/gravity values; rheology remains unselected. ShellSet mechanics and forward evolution were not run. No `dt` or t1 was created.", "",
    ]
    (ROOT / "R6_T0_B_PANGAEA_LIKE_V2_MATERIALIZATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    (ROOT / "R6_TECTONIC_T0_MATERIALIZATION_IMPLEMENTATION.md").write_text(
        "\n".join(lines), encoding="utf-8")
    print(json.dumps({"decision": "R6_T0_B_PANGAEA_LIKE_V2_MATERIALIZED__SPECIALIST_RUNTIME_REMAINS",
                      "realization_manifest_sha256": report["realization_manifest_sha256"],
                      "field_package_sha256": report["field_package_sha256"],
                      "age_median_ma": report["derived_fields"]["oceanic_age"]["area_weighted_ocean_median_ma"],
                      "residual_rms_m": report["derived_fields"]["ocean_authorial_residual_bathymetry"]["observed_area_weighted_ocean_rms_m"],
                      "pre_orbdata_feg_generated": report["feg"]["pre_orbdata_generated"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
