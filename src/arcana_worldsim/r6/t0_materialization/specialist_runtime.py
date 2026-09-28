"""Build the integrated, evidence-backed B-v2 specialist materialization gate.

This module inventories parent artifacts and local runtime availability. It
does not synthesize scientific fields or invoke third-party engines.
"""
from __future__ import annotations

import hashlib
import json
import platform
import shutil
import os
import subprocess
from pathlib import Path
from typing import Any


REPORT_JSON = "R6_T0_B_PANGAEA_LIKE_V2_SPECIALIST_MATERIALIZATION.json"
REPORT_MD = "R6_T0_B_PANGAEA_LIKE_V2_SPECIALIST_MATERIALIZATION.md"
READJUDICATION_JSON = "R6_T0_B_PANGAEA_LIKE_V2_RUNTIME_BINDING_AND_INPUT_READJUDICATION.json"
READJUDICATION_MD = "R6_T0_B_PANGAEA_LIKE_V2_RUNTIME_BINDING_AND_INPUT_READJUDICATION.md"
FAIR_EVIDENCE = "R6_SHELLSET_FAIR_RUNTIME_QUALIFICATION.json"
FAIR_EVIDENCE_SHA256 = "ab29de4577c4c4b007d41a7ac5567d7b287c7fed5dee3107aeb69dc35df1a350"

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
    """Inventory explicitly configured or PATH-visible tools without launching them.

    ShellSet may be bound through ARCANA_SHELLSET_EXE or ARCANA_SHELLSET_ROOT.
    A configured binary is AVAILABLE, but never QUALIFIED merely by existing.
    """
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
            "availability": "AVAILABLE" if found else "UNAVAILABLE",
        }
    explicit_exe = os.environ.get("ARCANA_SHELLSET_EXE")
    explicit_root = os.environ.get("ARCANA_SHELLSET_ROOT")
    configured = Path(explicit_exe).expanduser() if explicit_exe else (
        Path(explicit_root).expanduser() / "ShellSet.exe" if explicit_root else None
    )
    if configured is not None:
        configured = configured.resolve()
        exists = configured.is_file()
        digest = None
        if exists:
            hasher = hashlib.sha256()
            with configured.open("rb") as executable_file:
                for block in iter(lambda: executable_file.read(1024 * 1024), b""):
                    hasher.update(block)
            digest = hasher.hexdigest()
        result["ShellSet"] = {
            "commands_checked": [], "available_on_path": False,
            "resolved_command": str(configured) if exists else None,
            "resolved_path": str(configured) if exists else None,
            "version": None,
            "availability": "AVAILABLE" if exists else "UNAVAILABLE",
            "qualification": "NOT_RUN" if exists else "BLOCKED_CONFIGURED_RUNTIME_NOT_FOUND",
            "binding_source": "ARCANA_SHELLSET_EXE" if explicit_exe else "ARCANA_SHELLSET_ROOT",
            "executable_sha256": digest,
        }
    return result


def load_fair_runtime_evidence(root: str | Path) -> tuple[dict[str, Any], str]:
    """Read immutable qualification evidence and verify its committed bytes.

    Git's committed blob is hashed so Windows ``core.autocrlf`` cannot turn a
    valid LF evidence artifact into a false digest mismatch.
    """
    root = Path(root).resolve()
    path = root / FAIR_EVIDENCE
    if not path.is_file():
        raise FileNotFoundError(f"governed FAIR qualification evidence missing: {path}")
    result = subprocess.run(
        ["git", "show", f"HEAD:{FAIR_EVIDENCE}"], cwd=root,
        capture_output=True, check=False,
    )
    if result.returncode:
        raise ValueError("FAIR qualification evidence must be committed before it is consumed")
    blob_sha256 = hashlib.sha256(result.stdout).hexdigest()
    if blob_sha256 != FAIR_EVIDENCE_SHA256:
        raise ValueError(
            f"FAIR evidence committed SHA256 mismatch: expected {FAIR_EVIDENCE_SHA256}, found {blob_sha256}"
        )
    evidence = _read_json(root, FAIR_EVIDENCE)
    runtime = evidence.get("qualified_runtime", {})
    source = evidence.get("scientific_source", {})
    if (evidence.get("schema") != "ARCANA_SHELLSET_FAIR_RUNTIME_QUALIFICATION_V1"
            or evidence.get("evidence_identity_sha256") != "8265b998a8ddb8e3fdfd7371c9bfe076e6697fbbd7fcb922d77a37317ef59afe"
            or runtime.get("commit") != "09a06ecd061f00b80a52af86e31d609ff5545a8b"
            or runtime.get("executable_sha256") != "03e1a3f7ac0c4593a4a6eb641bb6d8acd0b752da5c5fd7b1ee74788fb705e349"
            or source.get("upstream_commit") != "e4a6fbd5997b6c4978924649dff1abab0c96ca57"):
        raise ValueError("FAIR evidence content differs from governed runtime identities")
    return evidence, blob_sha256


def build_readjudication(root: str | Path) -> dict[str, Any]:
    """Build the current R6 runtime/input gate without rewriting history."""
    root = Path(root).resolve()
    evidence, evidence_sha = load_fair_runtime_evidence(root)
    parent = _read_json(root, PARENT_FILES[0])
    implementation = _read_json(root, PARENT_FILES[2])
    source_contract = _read_json(root, PARENT_FILES[5])
    source_closure = _read_json(root, PARENT_FILES[6])
    configuration = _read_json(root, PARENT_FILES[11])
    historical = _read_json(root, REPORT_JSON)

    evidence_auth = evidence["authorization_boundary"]
    q = evidence["qualification"]
    rt = evidence["qualified_runtime"]
    # Verified source semantics supplied for pinned OrbData5.f90 / MOD_Data.f90.
    # Keep these distinctions explicit: the four final shell fields below are
    # recomputed outputs, not PRE_ORBDATA nodal values.
    pre_feg_inputs = ["longitude", "latitude", "elevation", "heat_flow"]
    auxiliary_inputs = ["aArray", "cArray", "sArray (age >= 200 Ma)",
                        "eArray (only if needE)", "qArray (only if needQ)"]
    derived_outputs = ["crustal_thickness", "mantle_lithosphere_thickness",
                       "chemical_delta_rho", "cooling_curvature"]
    fields = [
        {"field": "elevation", "pre_orbdata_semantics": "FEG nodal input. Any exact 0.0 sets needE and requests an elevation grid; stock copies Earth INPUT/ETOPO20.grd.",
         "zero_or_sentinel": "0.0 IS SOURCE-DEFINED NEED_E GRID SENTINEL; genuine zero is ambiguous",
         "preserved_or_modified": "Node value is used; zero invokes the auxiliary elevation-grid path.",
         "orbdata_derives": "No bathymetry from age; complete elevation remains independent ARCANA physical state.",
         "stock_earth_dependency": "Stock Earth ETOPO20 fallback is prohibited as ARCANA authority.",
         "arcana_equivalent": "Complete governed ocean elevation and an ARCANA grid/adapter or qualified interface change are still required.",
         "readiness": ["STILL_MISSING_AUTHORIAL_PHYSICAL_STATE", "ADAPTER_INTERFACE_DECISION_REQUIRED"]},
        {"field": "heat_flow", "pre_orbdata_semantics": "FEG nodal input. Any exact 0.0 sets needQ. Only zero-valued nodes enter qArray then conditional age-law fill; nonzero values skip that branch.",
         "zero_or_sentinel": "0.0 IS SOURCE-DEFINED NEED_Q GRID SENTINEL",
         "preserved_or_modified": "For heatFl==0: interpolate qArray; age<200 overrides with pinned ocean law; age<=0 uses qLim1; then apply heat-flow limits. Nonzero heat flow does not get age-overridden.",
         "orbdata_derives": "Conditional zero-node fill only; age is not a global override.",
         "stock_earth_dependency": "Earth qArray/eArray sources cannot be promoted as ARCANA authority.",
         "arcana_equivalent": "A governed global heat-flow policy must ensure intended zero routing and provide ARCANA qArray whenever any node is zero.",
         "readiness": ["MODEL_CONFIGURATION_REQUIRED", "AUXILIARY_GRID_EXPORT_REQUIRED"]},
        {"field": "crustal_thickness", "pre_orbdata_semantics": "Not a required PRE_ORBDATA nodal input; Assign always reads cArray and ignores the input FEG value.",
         "zero_or_sentinel": "Not applicable to FEG input; cArray is mandatory",
         "preserved_or_modified": "Recomputed/interpolated from cArray each run.", "orbdata_derives": "Output from governed ARCANA cArray input.",
         "stock_earth_dependency": "Stock Earth crust grid is not authority.",
         "arcana_equivalent": "Governed crustal_thickness_m exists on cell support and can be exported deterministically without cell-to-FEG projection.",
         "readiness": ["ARCANA_EXISTING_AUTHORITY", "ORBDATA_GRID_EXPORTER_REQUIRED"]},
        {"field": "mantle_lithosphere_thickness", "pre_orbdata_semantics": "Not a required PRE_ORBDATA nodal input; Assign ignores input FEG value. Interpolated age selects the method.",
         "zero_or_sentinel": "Not applicable to FEG input; auxiliary age and continental path inputs govern",
         "preserved_or_modified": "Age<200 Ma uses pinned ocean model; age>=200 Ma uses stock continental/unknown S-wave anomaly sArray path.",
         "orbdata_derives": "Ocean thickness from age; continental stock path requires sArray, not prescribed ARCANA thickness.",
         "stock_earth_dependency": "Earth delta_ts/sArray values are prohibited as ARCANA authority.",
         "arcana_equivalent": "Governed continental_reference_lithosphere_thickness_m is not consumed by stock OrbData. Require a qualified source generalization, governed equivalent producer, or retain blocker; no synthetic delta_ts inversion.",
         "readiness": ["CONTINENTAL_SARRAY_INTEROPERABILITY_BLOCKER", "MODEL_CONFIGURATION_REQUIRED"]},
        {"field": "chemical_delta_rho", "pre_orbdata_semantics": "Not a PRE_ORBDATA sentinel/input. Assign initializes then derives/limits final value internally.",
         "zero_or_sentinel": "Not a PRE_ORBDATA sentinel", "preserved_or_modified": "Derived/limited from structural/isostatic calculation and delta_rho_limit.",
         "orbdata_derives": "Yes; ORBDATA_DERIVED_FROM_GOVERNED_INPUT + MODEL_CONFIGURATION_REQUIRED.",
         "stock_earth_dependency": "No Earth output transfer.", "arcana_equivalent": "No independent raster required absent another governed contract; configure delta_rho_limit and material parameters.",
         "readiness": ["ORBDATA_DERIVED_FROM_GOVERNED_INPUT", "MODEL_CONFIGURATION_REQUIRED"]},
        {"field": "cooling_curvature", "pre_orbdata_semantics": "Not a PRE_ORBDATA sentinel/input. Assign computes curvature from thermal/geotherm state.",
         "zero_or_sentinel": "Not a PRE_ORBDATA sentinel", "preserved_or_modified": "Derived thermally and may modify mantle thickness while enforcing profile conditions.",
         "orbdata_derives": "Yes; ORBDATA_DERIVED_FROM_GOVERNED_INPUT + MODEL_CONFIGURATION_REQUIRED.",
         "stock_earth_dependency": "No Earth output transfer.", "arcana_equivalent": "No independent raster required absent another governed contract; thermal model and limits remain unselected.",
         "readiness": ["ORBDATA_DERIVED_FROM_GOVERNED_INPUT", "MODEL_CONFIGURATION_REQUIRED"]},
    ]
    # T0 state in this branch now contains a physical crust-thickness grid and age.
    parent_hashes = parent["normalized_field_hashes"]
    if parent_hashes["oceanic_lithosphere_age_ma"] != "aed3d311296947aad0f4cc041cfbb1b2784763704b23b1a3e746d2079a607dc2":
        raise ValueError("authoritative ocean age identity changed")
    historical_runtime = historical["specialist_runtime_qualification"]
    bootstrap_sha = implementation["parent_state"]["bootstrap_sha256"]
    if bootstrap_sha != "27bdaa065146981d425088db06c7f989c1099e64e4b30d920b04c979d01331bf":
        raise ValueError("historical bootstrap identity changed")
    reference_rows = configuration["reference_physical_parameters"]["families"]
    unresolved_reference = [row["id"] for row in reference_rows if not row["selected"]]
    mesh_payload = root / "_ARCANA_EXTERNAL_SOURCES/r6/tectonic_t0/R6_T0_VECTOR_PLATE_PARTITION.npz"
    projection_available = mesh_payload.is_file()
    arcana_capacity = evidence["capacity_delta"]["OrbData5"]["maxNod"] >= 64_442 and evidence["capacity_delta"]["OrbData5"]["maxEl"] >= 128_880
    return {
        "schema": "R6_T0_B_PANGAEA_LIKE_V2_RUNTIME_BINDING_AND_INPUT_READJUDICATION_V2",
        "decision": "R6_T0_SPECIALIST_RUNTIME_QUALIFIED_FOR_EXAMPLES_AND_ARCANA_CAPACITY__INPUTS_REMAIN_OPEN",
        "t0_ma": 210,
        "fair_evidence": {"path": FAIR_EVIDENCE, "committed_blob_sha256": evidence_sha,
                          "evidence_identity_sha256": evidence["evidence_identity_sha256"],
                          "recorded_at_utc": evidence["recorded_at_utc"], "host": evidence["host"]},
        "historical_windows_observation": {"host_os": historical_runtime["host_os"],
                                           "runtimes": historical_runtime["runtimes"],
                                           "official_build_qualification": historical_runtime["official_build_qualification"],
                                           "status": "PRESERVED_HISTORICAL_OBSERVATION; not current FAIR qualification"},
        "runtime": {"scientific_source_repository": evidence["scientific_source"]["repository"],
                    "scientific_source_commit": evidence["scientific_source"]["upstream_commit"],
                    "qualified_runtime_commit": rt["commit"], "runtime_branch": rt["branch"],
                    "executable_sha256": rt["executable_sha256"], "host": evidence["host"],
                    "compiler_backend": rt["backend"], "compiler": rt["compiler"],
                    "blas_lapack": rt["blas_lapack"], "mpi": rt["mpi"],
                    "runtime_root": rt["root"], "runtime_executable": rt["executable"],
                    "portability_delta": evidence["portability_delta"],
                    "capacity_delta": evidence["capacity_delta"],
                    "numerical_change_classification": evidence["capacity_delta"]["classification"],
                    "availability": "AVAILABLE_ON_FAIR_PER_GOVERNED_EVIDENCE; local executable not required",
                    "qualified_for_official_upstream_examples": evidence_auth["qualified_for_upstream_scientific_example"],
                    "qualified_for_arcana_mesh_capacity": arcana_capacity and evidence_auth["qualified_capacity_patch"],
                    "arcana_mesh_capacity_check": {"nodes": 64_442, "triangles": 128_880,
                                                   "OrbData5_maxNod": evidence["capacity_delta"]["OrbData5"]["maxNod"],
                                                   "OrbData5_maxEl": evidence["capacity_delta"]["OrbData5"]["maxEl"],
                                                   "OrbScore2_maxNod": evidence["capacity_delta"]["OrbScore2"]["maxNod"],
                                                   "OrbScore2_maxEl": evidence["capacity_delta"]["OrbScore2"]["maxEl"]},
                    "t0_input_transformations_authorized": False,
                    "t0_mechanics_authorized": evidence_auth["arcana_t0_mechanics_authorized"],
                    "qualification_results": q,
                    "cross_backend_acceptance": evidence["qualification"]["official_stored_vs_nvidia"]["cross_backend_acceptance_tolerance"]},
        "source_audit_basis": {"upstream_commit_pinned": evidence["scientific_source"]["upstream_commit"],
                               "official_source_urls": [
                                   "https://github.com/JonBMay/ShellSet/blob/e4a6fbd5997b6c4978924649dff1abab0c96ca57/src/MOD_Data.f90",
                                   "https://github.com/JonBMay/ShellSet/blob/e4a6fbd5997b6c4978924649dff1abab0c96ca57/src/OrbData5.f90",
                                   "https://github.com/JonBMay/ShellSet/blob/e4a6fbd5997b6c4978924649dff1abab0c96ca57/INPUT/iEarth5-049.in"],
                               "contracts": ["R6_SHELLSET_MINIMUM_THERMOMECHANICAL_STATE_CONTRACT.json", "R6_SHELLSET_PRERUNTIME_INPUT_CLOSURE.json"],
                               "line_level_upstream_source_present_locally": False,
                               "scope_note": "Source-grounding correction records verified behavior for pinned OrbData5.f90 and MOD_Data.f90 at the stated commit: elevation/heat-flow exact-zero sentinels; conditional heat fill order; always-read age and cArray; age-selected ocean versus continental sArray mantle path; and four FEG fields ignored and recomputed. Source body is not vendored.",
                               "verified_semantics": {"feg_node_inputs": pre_feg_inputs,
                                   "auxiliary_grid_inputs": auxiliary_inputs,
                                   "orbdata_derived_outputs": derived_outputs,
                                   "age_classification": "aArray is always read; bilinear interpolation occurs before age<200 classification. >=200 is continental/unknown interface marker only, never physical continental age.",
                                   "coastal_interpolation": "Potential category leakage is unqualified on ARCANA FEG; adapter/interface blocker until protected classification is validated.",
                                   "crustal_thickness": "Always from cArray; input FEG thickness ignored.",
                                   "bathymetry": "Not derived from age."}},
        "orbdata_capability_matrix": fields,
        "arcana_state": {"mesh_nodes": 64_442, "mesh_triangles": 128_880,
                         "mesh_sha256": "6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad",
                         "field_package_sha256": parent["field_package_sha256"],
                         "ocean_age_sha256": parent_hashes["oceanic_lithosphere_age_ma"],
                         "ocean_age_regenerated": False,
                         "historical_bootstrap_sha256": bootstrap_sha,
                         "existing_materialized_fields": [{"field": row["field"], "sha256": row["normalized_sha256"]}
                                                            for row in historical["pending_field_ledger"]["ALREADY_MATERIALIZED"]]},
        "physical_configuration": {"canonical": {"gMean_m_s2": 9.82, "radius_m": 6_371_000},
                                   "unresolved_reference_families": unresolved_reference,
                                   "rheology_families": list(RHEOLOGY_FAMILIES),
                                   "nFl": 0, "FFRIC": "INACTIVE", "BYERLY": "INACTIVE",
                                   "numeric_rheology_selected": False,
                                   "earth_defaults_or_orbscore_optimum_used": False},
        "projection": {"implementation": "existing shellset_mesh adapter project_cell_field_to_nodes",
                       "status": "OPTIONAL_FOR_ORBDATA_GRIDS; not a PRE_ORBDATA dependency" if not projection_available else "AVAILABLE_FOR_OTHER_NODAL_FIELDS",
                       "classification": "NUMERICAL_DERIVED_SUPPORT",
                       "rule": "lexicographic first incident cell for continuous values; categorical value only when all incident cells agree; any UNKNOWN incident source keeps output UNKNOWN",
                       "lineage": "per-node incident source cells, selected cell/weight, categorical support, uncertainty, unknown count and coverage",
                       "error": "no interpolation error asserted; source-cell support retained",
                       "production_mesh_source_payload_available": projection_available,
                       "production_projection_replay": "NOT_RUN; partition payload absence does not block aArray/cArray grid export"},
        "pre_orbdata_contract": {"feg_node_inputs": pre_feg_inputs,
                                  "readiness": "BLOCKED", "materialized": False,
                                  "blockers": ["complete governed T0 ocean elevation/bathymetry", "resolve zero-elevation sentinel and ARCANA eArray/interface path", "close global heat-flow policy and conditional qArray path"]},
        "auxiliary_input_readiness": {"ready": False,
                                      "inputs": {"aArray": "ARCANA ocean age authority exists; exporter and coast classification qualification required; >=200 marker only from governed land/ocean identity", "cArray": "governed crust thickness exists; OrbData-compatible deterministic grid exporter required", "sArray": "stock continental/unknown path incompatible with prescribed ARCANA continental thickness", "eArray": "conditional on any zero elevation; governed ARCANA source/path unresolved", "qArray": "conditional on any zero heat flow; governed ARCANA source/path unresolved"},
                                      "age_coastal_classification": "ADAPTER_QUALIFICATION_REQUIRED_POTENTIAL_CATEGORY_LEAKAGE"},
        "orbdata_transformation_readiness": {"ready": False, "blockers": ["required auxiliary grid inputs are not exported/qualified", "continental sArray path incompatible with governed ARCANA thickness", "material, thermal and numerical model configuration unresolved"]},
        "feg_readiness": {"required_final_fields": [row["field"] for row in fields],
                           "PRE_ORBDATA_ready": False, "PRE_ORBDATA_materialized": False,
                           "SHELLS_READY_ready": False, "mechanics_authorized": False,
                           "reason": "PRE_ORBDATA requires longitude/latitude/elevation/heat-flow nodal inputs; elevation and heat-flow exact-zero sentinels invoke conditional grids. Complete ocean elevation, heat-flow policy, and interface paths remain unresolved. The other four physical fields are OrbData outputs, not PRE inputs."},
        "scientific_blockers": [
            "Author complete T0 ocean elevation/bathymetry with datum, support and uncertainty; OrbData age does not establish bathymetry generation.",
            "Resolve aArray coastal category-leakage qualification and governed ocean heat-flow/thickness parameters; age >=200 may only encode interface classification, not physical continental age.",
            "Constrain all nine reference material/thermal configuration families and numeric continuum rheology; no Earth defaults/OrbScore optimum.",
            "Resolve stock continental sArray incompatibility: governed ARCANA continental_reference_lithosphere_thickness_m is not consumed; choose qualified source generalization/equivalent producer or retain blocker.",
            "Close delta_rho_limit, material parameters, and thermal/geotherm controls for derived chemical_delta_rho and cooling_curvature outputs."],
        "implementation_blockers": [
            "Implement and qualify deterministic OrbData-compatible aArray/cArray exporters with source support and lineage; no resolution increase.",
            "Qualify age-grid coast classification strategy because bilinear aArray interpolation precedes the 200 Ma branch.",
            "Select ARCANA eArray/qArray adapter path if any FEG node uses exact-zero elevation/heat flow.",
            "After required scientific fields close, materialize PRE_ORBDATA and execute the prepared FAIR OrbData validation; do not run ShellSet mechanics here.",
            "Global sphere uniqueness/reference-frame and rigid-rotation nullspace qualification remains open."],
        "fair_validation": {"script": "scripts/r6_t0_fair_validate_orbdata_result.sh",
                            "command_after_input_gates_close": "bash scripts/r6_t0_fair_validate_orbdata_result.sh",
                            "behavior": "fail-fast identity/input/output hash and status validation; does not start mechanics or evolution",
                            "input_result_manifest": "R6_T0_ORBDATA_FAIR_RESULT_MANIFEST.json (not yet present; PRE_ORBDATA is not ready)"},
        "governance": {"historical_evidence_rewritten": False, "canonical_payload_mutated": False,
                       "canonical_promoted": False, "t1_created": False, "dt_selected": False,
                       "forward_evolution": False, "orbdata_executed": False,
                       "shellset_mechanics_executed": False},
        "exact_next_action": "Resolve the authorial T0 ocean elevation/bathymetry and thermal-model configuration first. When a complete governed PRE_ORBDATA manifest exists, run the prepared FAIR identity/input validation script; mechanics remain separately unauthorized."
    }


def render_readjudication_markdown(report: dict[str, Any]) -> str:
    lines = ["# R6 T0 FAIR ShellSet runtime binding and input readjudication", "",
             f"**Decision:** `{report['decision']}`", "",
             f"- FAIR evidence: `{report['fair_evidence']['path']}`; committed SHA256 `{report['fair_evidence']['committed_blob_sha256']}`.",
             f"- Evidence identity: `{report['fair_evidence']['evidence_identity_sha256']}`.",
             f"- Runtime: upstream `{report['runtime']['scientific_source_commit']}`, qualified `{report['runtime']['qualified_runtime_commit']}`, executable SHA256 `{report['runtime']['executable_sha256']}`.",
             f"- Historical Windows observation: `{report['historical_windows_observation']['status']}`; preserved unchanged.",
             f"- Upstream examples qualified: **{str(report['runtime']['qualified_for_official_upstream_examples']).lower()}**; ARCANA mesh capacity qualified: **{str(report['runtime']['qualified_for_arcana_mesh_capacity']).lower()}**.",
             f"- T0 input transformation authorization: **{str(report['runtime']['t0_input_transformations_authorized']).lower()}**; T0 mechanics authorization: **{str(report['runtime']['t0_mechanics_authorized']).lower()}**.",
             f"- Cross-backend Intel/NVIDIA tolerance: `{report['runtime']['cross_backend_acceptance']}`.", "",
             "## OrbData5 field behavior and ARCANA readiness", "",
             "Pinned-source semantics are recorded from OrbData5.f90 and MOD_Data.f90 at the qualified upstream commit. PRE_ORBDATA nodal inputs, auxiliary grids, recomputed outputs, and final FEG fields are distinct contracts.", "",
             "### PRE_ORBDATA FEG node inputs", "",
             "Longitude/latitude, elevation, and heat flow. Any elevation exactly 0.0 sets `needE` and selects the stock ETOPO20 grid fallback; that Earth fallback is prohibited for ARCANA and an exact-zero physical elevation is ambiguous. Any heat flow exactly 0.0 sets `needQ`; only those nodes take the qArray/age-law fill branch. Nonzero heat flow is not globally overridden by age.", "",
             "### OrbData auxiliary grid inputs", "",
             "`aArray` and `cArray` are always read. `sArray` is used for the age >=200 Ma continental/unknown mantle path. `eArray` and `qArray` are conditional on exact-zero elevation/heat flow. The >=200 age value is an interface classification marker derived from governed land/ocean identity, never a physical continental age. Because bilinear age interpolation precedes classification, coastal category leakage remains an adapter qualification blocker.", "",
             "### OrbData-derived output fields", "",
             "OrbData ignores input FEG crustal thickness, mantle-lithosphere thickness, chemical_delta_rho, and cooling_curvature, then recomputes all four. Crust thickness comes from cArray; ocean mantle thickness uses the age model; continental/unknown mantle thickness uses stock sArray. Chemical density anomaly and cooling curvature are derived under model/material/thermal configuration, including delta_rho_limit.", "",
             "### SHELLS_READY final FEG fields", "",
             "Elevation, heat flow, crustal thickness, mantle-lithosphere thickness, chemical_delta_rho, and cooling_curvature must all be present in the final FEG.", "",
             "| Field | Source behavior | Sentinel / route | ARCANA disposition |", "|---|---|---|---|"]
    for row in report["orbdata_capability_matrix"]:
        lines.append("| `{field}` | {pre_orbdata_semantics} | {zero_or_sentinel}; {preserved_or_modified} {orbdata_derives} | {arcana_equivalent} |".format(**row))
    lines += ["", "## Projection and FEG gates", "",
              f"- Projection: `{report['projection']['status']}` using {report['projection']['implementation']}; class `{report['projection']['classification']}`.",
              "- Cell-to-node projection is not required before OrbData for age or crust thickness when exported as auxiliary grids; the missing partition NPZ no longer blocks these inputs.",
              f"- PRE_ORBDATA ready/materialized: **{str(report['feg_readiness']['PRE_ORBDATA_ready']).lower()} / {str(report['feg_readiness']['PRE_ORBDATA_materialized']).lower()}**.",
              f"- Auxiliary inputs ready: **{str(report['auxiliary_input_readiness']['ready']).lower()}**; OrbData transformation ready: **{str(report['orbdata_transformation_readiness']['ready']).lower()}**.",
              f"- SHELLS_READY ready: **{str(report['feg_readiness']['SHELLS_READY_ready']).lower()}**; mechanics authorized: **{str(report['feg_readiness']['mechanics_authorized']).lower()}**.", "",
              "## Scientific blockers", ""]
    lines.extend(f"- {item}" for item in report["scientific_blockers"])
    config = report["physical_configuration"]
    lines += ["", "## Physical configuration", "",
              f"- Canonical values: `gMean={config['canonical']['gMean_m_s2']} m/s²`, `radius={config['canonical']['radius_m']} m`.",
              f"- Unresolved reference families: {', '.join(config['unresolved_reference_families'])}.",
              f"- Rheology: {', '.join(config['rheology_families'])}; `nFl=0`, FFRIC and BYERLY inactive; no numeric baseline selected.",
              "- No Earth defaults or Earth OrbScore optimum were used."]
    lines += ["", "## Implementation blockers", ""]
    lines.extend(f"- {item}" for item in report["implementation_blockers"])
    lines += ["", f"**FAIR validation command after input gates close:** `{report['fair_validation']['command_after_input_gates_close']}`.",
              f"Required result manifest: `{report['fair_validation']['input_result_manifest']}`.", "",
              f"**Next action:** {report['exact_next_action']}", "",
              "No OrbData or mechanics execution, forward evolution, `dt`, or `t1` was performed or created.", ""]
    return "\n".join(lines)


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
