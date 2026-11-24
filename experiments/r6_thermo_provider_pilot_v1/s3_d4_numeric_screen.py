"""ARCANA R6 S3-D4: non-executable, fail-closed numerical-screen design.

Reads pinned repository JSON and accepts only *already parsed* native summaries.
It never launches an engine, writes evidence, certifies scientific applicability,
or approves numerical repeatability in the absence of preregistered thresholds.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from experiments.r6_thermo_provider_pilot_v1.s3_design_contract import (
    git_blob_sha,
    load as load_design,
    validate as validate_design,
    )
from experiments.r6_thermo_provider_pilot_v1.s3_native_readback import (
    source_point,
)

ROOT = Path(__file__).resolve().parent
POLICY_FILE = ROOT / "s3_d4_numeric_gate_candidate_v1.json"
DESIGN_FILE = ROOT / "s3_pt_design_candidate_v1.json"
RISK_FILE = ROOT / "s3_d4_primary_source_model_risk_v2.json"

EXPECTED_PINS = {
    "candidate_file": "s3_pt_design_candidate_v1.json",
    "candidate_git_blob": "1a69ac7be3d9970c94f91fe7e7213a8037af8286",
    "source_risk_file": "s3_d4_primary_source_model_risk_v2.json",
    "source_risk_git_blob": "708830146ecb18287e6c6800be83f6c160a11003",
    "source_original_S2_manifest_sha256":
        "74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604",
    "last_S3_Python_FAIR_tested_sha":
        "9a9c996b909d7752114165f7f036ebf2b00fb966",
    "pinned_Perple_X_solution_model_git_blob":
        "564742a569998a768c2d8e15d2b9599ee90438d1",
}
EXPECTED_SANITY = {
    "mag_P_T_serialization_max_ulp": 16,
    "per_P_T_native_printed_abs_source_units_max": 0.1,
    "magemin_phase_weight_sum_abs_fraction_max": 1e-8,
    "magemin_native_component_closure_abs_max": 1e-10,
    "magemin_source_bulk_component_closure_abs_max": 1e-12,
    "magemin_bulk_residual_norm_max": 1e-9,
    "perplex_phase_weight_sum_abs_pct_max": 0.05,
    "perplex_native_component_check":
        "DECIMAL_PRINTED_INTERVAL_INTERSECTION_ONLY",
    "magemin_gibbs_density":
        "REQUIRE_FINITE_GIBBS_AND_POSITIVE_FINITE_DENSITY_WHEN_NATIVE",
    "perplex_native_gibbs_density": "NOT_AVAILABLE_DO_NOT_SYNTHESIZE",
}
EXPECTED_PHASE_FLAGS = {
    "g25_phase_boundary_illustrative_uncertainty_P_kbar": 1,
    "g25_phase_boundary_illustrative_uncertainty_T_C": 50,
    "not_numerical_threshold": True,
    "accessory_phase_presence": "WARNING_SCIENCE_UNCERTAINTY",
    "Fsp_C1_structural_state": "UNADJUDICATED",
    "Augite_G_phase_Na_richness": "UNADJUDICATED",
    "cAmph_G_Fe3_Ti_simplification":
        "DOCUMENTED_NOT_CALIBRATED_FOR_ORIGINAL_BULK",
    "full_50_cell_P_T_X_calibration": "UNKNOWN_NOT_APPROVED",
    "cross_provider_bulk_equivalence": False,
}
EXPECTED_REPEATS = {
    "fresh_independent_processes_required": True,
    "numeric_phase_mass_fraction_abs_max": None,
    "numeric_gibbs_absolute_max": None,
    "numeric_density_relative_max": None,
    "same_pt_phase_membership_changes": "REVIEW_NOT_AUTOMATIC_PASS",
    "even_identical_printed_values": "NOT_SCIENTIFIC_CALIBRATION",
    "no_missing_as_zero": True,
}
EXPECTED_CROSS = {
    "different_P_T_phase_set_change": "OBSERVATION_ONLY",
    "no_boundary_location_claim_at_grid_resolution": True,
    "no_precognition_of_absent_phase": True,
    "no_shared_cross_provider_comparison": True,
}
EXPECTED_FUTURE = {
    "write_once_S3_evidence_id_required": True,
    "new_source_locked_manifest_required": True,
    "manifest_SHA256_verification_required": True,
    "failed_runs_and_logs_preserved": True,
    "peak_rss_memory_bytes_budget": None,
    "per_run_walltime_budget_s": None,
    "per_run_IO_bytes_budget": None,
    "no_default_interpretation_of_null_as_unlimited": True,
    "pilot_authorized": False,
    "full_grid_authorized": False,
}
EXPECTED_STATUS = {
    "software_screen": "DIAGNOSTIC_ONLY",
    "science": "UNKNOWN",
    "S3_numeric_repetition_acceptance":
        "BLOCKED_NO_PREREGISTERED_THRESHOLDS",
    "S3_executable_promotion": "BLOCKED",
}


class S3D4GateError(ValueError):
    """A candidate source/provenance or native-readback diagnostic failed."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise S3D4GateError(code)


def finite(value: Any) -> bool:
    return type(value) in (float, int) and math.isfinite(value)


def load_json(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    require(type(obj) is dict, "D4_JSON_OBJECT_REQUIRED")
    return obj


def validate_contract(config: dict, *, design: dict | None = None,
                      risk: dict | None = None) -> dict:
    """Strictly detect altered gates, risk, chemistry and scope."""
    require(type(config) is dict and config.get("schema") ==
            "ARCANA_R6_THERMO_S3_D4_NUMERICAL_GATES_CANDIDATE_V1" and
            config.get("state") ==
            "SOURCE_ONLY_SCREENING_DESIGN__NOT_NUMERICALLY_OR_SCIENTIFICALLY_RATIFIED",
            "D4_INVALID_SCHEMA_OR_STATE")
    require(config.get("executable") is False and
            config.get("run_allowed") is False and
            type(config.get("engine_executions_authorized")) is int and
            config["engine_executions_authorized"] == 0,
            "D4_ENGINE_NOT_AUTHORIZED")
    require(config.get("authority") == {
        "D_024": "ACTIVE", "physical_T1": None,
        "mechanical_solve_authorized": False,
        "WORLD_HISTORY_PRODUCTION_AUTHORIZED": False,
        "arcana_original_materials_assigned": 0,
    }, "D4_AUTHORITY_DRIFT")
    pins = config.get("immutable_inputs")
    require(pins == EXPECTED_PINS, "D4_SOURCE_PINS_CHANGED")
    require(git_blob_sha(DESIGN_FILE.read_bytes()) ==
            EXPECTED_PINS["candidate_git_blob"] and
            git_blob_sha(RISK_FILE.read_bytes()) ==
            EXPECTED_PINS["source_risk_git_blob"],
            "D4_PINNED_SOURCE_FILE_BYTES_DRIFT")
    design = load_design() if design is None else validate_design(design)
    require(type(design) is dict and
            design.get("engine_executions_authorized") == 0 and
            design.get("executable") is False,
            "D4_CANDIDATE_PROMOTION_FORBIDDEN")
    risk = load_json(RISK_FILE) if risk is None else risk
    require(type(risk) is dict and
            risk.get("schema") ==
            "ARCANA_R6_THERMO_S3_D4_PRIMARY_MODEL_SOURCE_RISK_REVIEW_V2" and
            risk.get("executable") is False and
            risk.get("engine_executions_authorized") == 0 and
            risk.get("pins", {}).get("perplex_solution_model_git_blob") ==
            EXPECTED_PINS["pinned_Perple_X_solution_model_git_blob"] and
            risk.get("counts") == {
                "candidate_cells": 50,
                "scientifically_approved": 0,
                "unknown": 50,
                "source_engine_anchors": 2,
                "engine_runs_S3": 0,
            }, "D4_SCIENCE_RISK_PROMOTED")
    origin = {(x["id"], p, t) for x in design["candidate_tracks"]
              for p in x["P"] for t in x["T"]}
    seen = set()
    anchors = 0
    grids = risk.get("grids")
    require(type(grids) is list and len(grids) == 2,
            "D4_RISK_GRID_SHAPE_DRIFT")
    for row in grids:
        require(type(row) is dict and type(row.get("cells")) is list
                and len(row["cells"]) == 25,
                "D4_RISK_GRID_SHAPE_DRIFT")
        for cell in row["cells"]:
            require(type(cell) is dict and
                    (row["id"], cell.get("P"), cell.get("T")) in origin and
                    cell.get("PT_X_scientific_domain") == "UNKNOWN" and
                    cell.get("authority") == "NOT_APPROVED" and
                    type(cell.get("S3_engine_runs")) is int and
                    cell["S3_engine_runs"] == 0,
                    "D4_UNSUPPORTED_SCIENCE_PROMOTION")
            key = (row["id"], cell["P"], cell["T"])
            require(key not in seen, "D4_DUPLICATE_GRID_CELL")
            seen.add(key)
            anchor = next(t["anchor"] for t in design["candidate_tracks"]
                          if t["id"] == row["id"])
            must_anchor = cell["P"] == anchor["P"] and cell["T"] == anchor["T"]
            require(cell.get("engine_origin_anchor") is must_anchor,
                    "D4_S2_REFERENCE_ANCHOR_DRIFT")
            anchors += int(must_anchor)
    require(seen == origin and anchors == 2,
            "D4_GRID_NOT_FULL_OR_MISSING_ANCHORS")
    require(config.get("engineering_screen_only") == EXPECTED_SANITY,
            "D4_ENGINEERING_SCREEN_NOT_FROZEN_AS_DESIGN")
    require(config.get("science_context") == EXPECTED_PHASE_FLAGS,
            "D4_MODEL_UNCERTAINTY_OR_SCIENCE_DRIFT")
    require(config.get("same_point_repeatability") == EXPECTED_REPEATS,
            "D4_REPEATABILITY_TOLERANCE_UNRATIFIED")
    require(config.get("cross_point") == EXPECTED_CROSS,
            "D4_CROSS_PT_OR_PROVIDER_PROMOTION")
    require(config.get("future_run_evidence") == EXPECTED_FUTURE,
            "D4_FUTURE_RUN_BUDGET_OR_AUTHORITY_DRIFT")
    require(config.get("status_outcome") == EXPECTED_STATUS,
            "D4_FORBIDDEN_NUMERIC_OR_SCIENCE_PASS")
    return config


def load() -> dict:
    return validate_contract(load_json(POLICY_FILE))


def inspect_readback(value: dict, *, design: dict) -> dict:
    """Inspect D3 parser summary only; cannot attest raw evidence SHA."""
    require(type(value) is dict, "D4_NATIVE_SUMMARY_NOT_OBJECT")
    provider = value.get("provider")
    track_id = {
        "MAGEMin_C.jl": "S3A_MAGEMIN_CUSTOM_IG",
        "Perple_X": "S3B_PERPLEX_BL691",
    }.get(provider)
    require(track_id is not None, "D4_UNKNOWN_PROVIDER")
    p, t = value.get("P"), value.get("T")
    source_point(design, track_id, p, t)
    require(type(value.get("status")) is str and
            value["status"] in (
                "SOURCE_NATIVE_READBACK_ONLY__S3_SCIENCE_UNQUALIFIED",
                "PRINTED_RESOLUTION_READBACK_ONLY__S3_SCIENCE_UNQUALIFIED",
            ), "D4_NATIVE_STATUS_NOT_UNQUALIFIED")
    require(
        (provider == "MAGEMin_C.jl" and
         value["status"].startswith("SOURCE_NATIVE")) or
        (provider == "Perple_X" and
         value["status"].startswith("PRINTED_RESOLUTION")),
        "D4_NATIVE_STATUS_WRONG_PROVIDER")
    phases = value.get("phases")
    require(type(phases) is dict and bool(phases) and
            all(type(k) is str and k.strip() and finite(v) and
                0 <= v <= (1.0 if provider == "MAGEMin_C.jl" else 100.0)
                for k, v in phases.items()),
            "D4_NATIVE_PHASE_SUMMARY_INVALID")
    target = 1 if provider == "MAGEMin_C.jl" else 100
    ceiling = 1e-8 if provider == "MAGEMin_C.jl" else 0.05
    require(abs(sum(phases.values()) - target) <= ceiling,
            "D4_NATIVE_PHASE_TOTAL_INVALID")
    if provider == "MAGEMin_C.jl":
        require(finite(value.get("G_system")) and
                finite(value.get("rho_kg_m3")) and
                value["rho_kg_m3"] > 0 and
                finite(value.get("max_native_component_delta")) and
                0 <= value["max_native_component_delta"] <= 1e-10 and
                finite(value.get("max_source_component_delta")) and
                0 <= value["max_source_component_delta"] <= 1e-12 and
                finite(value.get("bulk_res_norm")) and
                0 <= value["bulk_res_norm"] <= 1e-9,
                "D4_MAGEMIN_READBACK_CHEMISTRY_INVALID")
    else:
        require(type(value.get("printed_component_coverage")) is int and
                value["printed_component_coverage"] == 10 and
                type(value.get("printed_oxide_molar_rounding_audit")) is dict
                and set(value["printed_oxide_molar_rounding_audit"]) ==
                set(design["candidate_tracks"][1]
                    ["fixed_original_molar_input"]["names"]) and
                all(type(row) is dict and
                    set(row) == {"reconstructed_mol", "reported_mol"} and
                    all(type(token) is str and token.strip()
                        for token in row.values())
                    for row in value["printed_oxide_molar_rounding_audit"].values()) and
                "G_system" not in value and "rho_kg_m3" not in value,
                "D4_PERPLEX_READBACK_INVENTED_OBSERVABLES")
    return value


def compare_readbacks(a: dict, b: dict,
                      *, config: dict | None = None,
                      design: dict | None = None) -> dict:
    """No comparison path is an acceptance grant or a physical solver run."""
    config = load() if config is None else validate_contract(config)
    design = load_design() if design is None else validate_design(design)
    inspect_readback(a, design=design)
    inspect_readback(b, design=design)
    require(a["provider"] == b["provider"],
            "D4_CROSS_PROVIDER_COMPARISON_FORBIDDEN")
    left = a["phases"]
    right = b["phases"]
    appeared = sorted(right.keys() - left.keys())
    disappeared = sorted(left.keys() - right.keys())
    same_pt = a["P"] == b["P"] and a["T"] == b["T"]
    detail = {
        "provider": a["provider"],
        "same_pt": same_pt,
        "added_phases": appeared,
        "removed_phases": disappeared,
        "common_phases": sorted(left.keys() & right.keys()),
        "physical_model_validation": "UNKNOWN",
        "numeric_acceptance": "NOT_RATIFIED",
        "write_once_manifest_attested": False,
        "scientific_cross_provider_equivalence": False,
        "engine_executions_authorized": 0,
        "science_caveats": (
            ["G25_BOUNDARY_UNCERTAINTY_APPROX_1KBAR_50C",
             "ACCESSORY_PHASE_OCCURRENCE_UNCERTAIN"] if a["provider"] ==
            "MAGEMin_C.jl" else
            ["Fsp_C1_I1_C1_STRUCTURAL_STATE_UNADJUDICATED",
             "Augite_G_PHASE_NA_RICHNESS_UNADJUDICATED",
             "cAmph_G_SIMPLIFIED_FE3_TI_CHEMISTRY"]
        ),
    }
    if not same_pt:
        return {
            **detail,
            "decision": "CROSS_PT_OBSERVATION_ONLY__NOT_PHASE_BOUNDARY_PROOF",
            "max_abs_phase_fraction_delta": None,
            "gibbs_abs_delta": None,
            "density_rel_delta": None,
            "repeatability_pass": None,
        }
    if appeared or disappeared:
        return {
            **detail,
            "decision": "SAME_PT_PHASE_DISAGREEMENT_REQUIRES_ADJUDICATION",
            "max_abs_phase_fraction_delta": None,
            "gibbs_abs_delta": None,
            "density_rel_delta": None,
            "repeatability_pass": False,
        }
    max_phase = max(abs(left[k] - right[k]) for k in left)
    if a["provider"] == "MAGEMin_C.jl":
        gdelta = abs(a["G_system"] - b["G_system"])
        rdelta = abs(a["rho_kg_m3"] - b["rho_kg_m3"]) / max(
            abs(a["rho_kg_m3"]), abs(b["rho_kg_m3"]))
    else:
        gdelta = None
        rdelta = None
    return {
        **detail,
        "decision": "SAME_PT_DELTAS_RECORDED__NUMERIC_GATE_NOT_RATIFIED",
        "max_abs_phase_fraction_delta": max_phase,
        "gibbs_abs_delta": gdelta,
        "density_rel_delta": rdelta,
        "repeatability_pass": None,
        "same_as_printed": max_phase == 0 and
            (gdelta is None or gdelta == 0) and
            (rdelta is None or rdelta == 0),
    }
