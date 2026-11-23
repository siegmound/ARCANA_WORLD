"""S3 design-candidate guard: pure JSON and upstream identity checks, no engines."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE / "s3_pt_design_candidate_v1.json"
PILOT = HERE / "pilot.json"


class S3DesignError(ValueError):
    pass


def need(condition: bool, code: str) -> None:
    if not condition:
        raise S3DesignError(code)


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def finite_number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def validate_grid(track: dict, pressures: list, temperatures: list,
                  anchor_p: int, anchor_t: int) -> None:
    need(track.get("run_allowed") is False, "S3_TRACK_RUN_UNAUTHORIZED")
    p, t = track.get("P"), track.get("T")
    need(isinstance(p, list) and isinstance(t, list)
         and len(p) == 5 and len(t) == 5
         and all(finite_number(v) and v > 0 for v in p + t)
         and p == sorted(set(p)) and t == sorted(set(t)),
         "S3_AXIS_SHAPE_UNITS_OR_DUPLICATES")
    need(p == pressures and t == temperatures,
         "S3_CANDIDATE_GRID_CHANGED_REQUIRES_VERSION")
    need(track.get("anchor") == {"P": anchor_p, "T": anchor_t}
         and anchor_p in p and anchor_t in t,
         "S3_ORIGINAL_ANCHOR_DRIFT")


def validate(policy: dict) -> dict:
    need(isinstance(policy, dict), "S3_POLICY_NOT_OBJECT")
    need(policy.get("schema") == "ARCANA_R6_THERMO_S3_PT_DESIGN_CANDIDATE_V1"
         and policy.get("state") == "DRAFT_NOT_SCIENTIFICALLY_RATIFIED"
         and policy.get("scope") ==
             "UPSTREAM_EARTH_PROVIDER_NATIVE_PT_SENSITIVITY_ONLY",
         "S3_DESIGN_SCHEMA_SCOPE_DRIFT")
    need(policy.get("executable") is False
         and type(policy.get("engine_executions_authorized")) is int
         and policy["engine_executions_authorized"] == 0,
         "S3_ENGINE_EXECUTION_NOT_AUTHORIZED")
    authority = policy.get("authority", {})
    need(authority.get("D_024") == "ACTIVE"
         and authority.get("physical_T1", object()) is None
         and authority.get("mechanical_solve_authorized") is False
         and authority.get("WORLD_HISTORY_PRODUCTION_AUTHORIZED") is False
         and type(authority.get("arcana_original_materials_assigned")) is int
         and authority["arcana_original_materials_assigned"] == 0,
         "S3_GOVERNANCE_FORBIDDEN_PROMOTION")

    evidence = policy.get("evidence", {})
    pinned = {
        "qualified_s2_code_sha": "632c4a570f876e3963b1dcd8a1f411a143fc8a59",
        "s1_manifest_sha256": "538c1b61f801c9902f8aa9b1b189b07ba38357eec339eb2b0211713f83299227",
        "s2_preflight_manifest_sha256": "e96b52635d9755acd36ae9473c7a75c23eb8d1f0a2d80d384a6e09807a77f08b",
        "s2_real_manifest_sha256": "74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604",
        "s2_audited_members": 68,
        "s2_audited_julia_processes": 5,
        "s2_audited_perplex_processes": 5,
    }
    need(evidence == pinned, "S3_S2_PROVENANCE_DRIFT")

    tracks = policy.get("candidate_tracks")
    need(isinstance(tracks, list) and len(tracks) == 2
         and all(isinstance(x, dict) for x in tracks),
         "S3_PROVIDER_TRACKS_INVALID")
    mag, per = tracks
    need(mag.get("id") == "S3A_MAGEMIN_CUSTOM_IG"
         and mag.get("provider") == "MAGEMin_C.jl"
         and mag.get("version") == "2.4.5"
         and mag.get("database") == "ig"
         and mag.get("dataset") == "tc_ds636"
         and mag.get("fixture") == "MAGEMIN_CUSTOM_IG"
         and mag.get("pressure_unit") == "kbar"
         and mag.get("temperature_unit") == "degC"
         and mag.get("calibrated_domain") == "UNKNOWN_NEEDS_SOURCE",
         "S3_MAGEMIN_TRACK_OR_DOMAIN_DRIFT")
    validate_grid(mag, [8, 9, 10, 11, 12],
                  [1000, 1050, 1100, 1150, 1200], 10, 1100)
    need(per.get("id") == "S3B_PERPLEX_BL691"
         and per.get("provider") == "Perple_X"
         and per.get("version") == "v7.3.3"
         and per.get("source_commit") ==
             "950d882bb6a9325a627109aa7154f7b526aa3087"
         and per.get("database") == "hp62ver.dat"
         and per.get("fixture") == "PERPLEX_BL691_MEEMUM"
         and per.get("solution_model") == "solution_model.dat"
         and per.get("pressure_unit") == "bar"
         and per.get("temperature_unit") == "K"
         and per.get("calibrated_domain") == "UNKNOWN_NEEDS_SOURCE",
         "S3_PERPLEX_TRACK_OR_DOMAIN_DRIFT")
    validate_grid(per, [2000, 3000, 4000, 5000, 6000],
                  [950, 1000, 1050, 1100, 1150], 4000, 1050)
    need(per.get("input_declared_bounds") ==
         {"P_bar": [500, 10000], "T_K": [873, 1323]}
         and per.get("input_bounds_are_calibration_proof") is False,
         "S3_PERPLEX_PROBLEM_BOUND_MISREPRESENTED")
    need(per.get("option_file_referenced") ==
             "bl691_MEEMUM_perplex_option.dat"
         and per.get("option_file_present_in_pinned_test_directory") is False
         and per.get("effective_default_options_verified") is False,
         "S3_UNVERIFIED_EFFECTIVE_OPTIONS_PROMOTED")
    need(per.get("source_problem_definition") ==
             "test/bl691_MEEMUM/bl691_MEEMUM.dat"
         and per.get("source_definition_git_blob") ==
             "3954964480612264838636fd394043aa0fef6324",
         "S3_PERPLEX_ORIGINAL_SOURCE_DRIFT")

    raw_pilot = PILOT.read_bytes()
    need(git_blob_sha(raw_pilot) ==
         "37b958b0137f878a3a3010593ce22fed2cf37a6c",
         "S3_SOURCE_PILOT_BLOB_DRIFT")
    original = json.loads(raw_pilot)["fixtures"]["MAGEMIN_CUSTOM_IG"]
    source_chem = mag.get("fixed_original_oxide_input", {})
    need(mag.get("source_registry_git_blob") ==
             "37b958b0137f878a3a3010593ce22fed2cf37a6c"
         and source_chem == {
             "names": original["oxides"],
             "amounts_wt_percent": original["amounts_wt_percent"],
             "as_reported_sum_wt_percent":
                 original["as_reported_sum_wt_percent"],
             "oxide_basis": original["oxide_basis"],
         }, "S3_MAGEMIN_ORIGINAL_OXIDE_BULK_DRIFT")
    need(abs(sum(source_chem["amounts_wt_percent"]) - 99.75) < 1e-10,
         "S3_MAGEMIN_ORIGINAL_BULK_TOTAL_DRIFT")
    mol = per.get("fixed_original_molar_input", {})
    need(mol == {
        "names": ["Na2O", "MgO", "Al2O3", "K2O", "CaO", "TiO2",
                  "FeO", "O2", "H2O", "SiO2"],
        "amount_tokens": ["2.5416", "8.110", "9.2646", "0.1054",
                          "10.146", "1.346", "10.1382", "0.488",
                          "3.4162", "53.9559"],
        "component_flags": ["1"] * 10,
        "basis": "ORIGINAL_PERPLEX_INPUT_MOLAR_AMOUNTS_NO_RENORMALIZATION",
    }, "S3_PERPLEX_ORIGINAL_MOLAR_BULK_DRIFT")

    grid = policy.get("grid", {})
    need(grid.get("cartesian_points_each") == 25
         and grid.get("candidate_total_two_providers") == 50
         and grid.get("point_order") == "PRESSURE_MAJOR_TEMPERATURE_MINOR"
         and grid.get("selected_same_point_rechecks_index_pairs") ==
             [[0, 0], [0, 4], [2, 2], [4, 0], [4, 4]]
         and grid.get("rechecks_require_fresh_process") is True
         and grid.get("reverse_order_alone_is_not_warm_start") is True
         and grid.get("approved_values") == [],
         "S3_GRID_RECHECK_OR_AUTHORIZATION_DRIFT")
    need(policy.get("units") ==
         {"bar_to_pa": 100000, "kbar_to_pa": 100000000,
          "kelvin_from_celsius_offset": 273.15},
         "S3_UNITS_DRIFT")
    need(all(500 <= p <= 10000 for p in per["P"])
         and all(873 <= t <= 1323 for t in per["T"]),
         "S3_PERPLEX_OUTSIDE_ORIGINAL_PROBLEM_BOUNDS")
    rules = policy.get("science_rules", {})
    required_true = [
        "fixed_original_provider_chemistry",
        "phase_set_may_change_across_distinct_points",
        "check_solver_residual_and_native_component_chemical_closure",
        "perplex_printed_bulk_component_interval_only",
        "new_s3_phase_agnostic_validator_required",
        "no_s2_fixed_phase_or_pt_validator_reuse",
        "numeric_acceptance_require_predeclared_tolerance",
        "source_model_and_chemistry_crosswalk_pending",
        "per_run_full_native_logs_hashes_write_once",
    ]
    required_false = [
        "phase_identical_at_different_points_required",
        "cross_provider_same_chemistry_database_qualified",
        "shared_original_25_point_cross_provider_comparison_authorized",
    ]
    need(all(rules.get(key) is True for key in required_true)
         and all(rules.get(key) is False for key in required_false)
         and rules.get("native_gibbs_or_density_missing") == "NOT_AVAILABLE",
         "S3_SCIENCE_COMPARE_OR_PHASE_BOUNDARY_DRIFT")
    blockers = policy.get("blocking_gates", [])
    need(isinstance(blockers, list) and set(blockers) == {
        "MAGEMIN_IG_TCDS636_CALIBRATION_DOMAIN_AND_COMPOSITION",
        "PERPLEX_BL691_HP62VER_VALIDITY_AND_EFFECTIVE_OPTIONS",
        "PHASE_AGNOSTIC_S3_PARSER_AND_NEGATIVE_TESTS",
        "RECHECK_AND_PREDECLARED_NUMERIC_THRESHOLDS",
        "PER_RUN_TIME_MEMORY_IO_BUDGET_FROM_S2",
        "SOURCE_LOCKED_WRITE_ONCE_S3_PREFLIGHT_AND_EVIDENCE",
        "SEPARATE_S3_REAL_RUN_AUTHORIZATION",
    }, "S3_UNRESOLVED_BLOCKERS_REMOVED")
    return policy


def load(path: Path = CANDIDATE) -> dict:
    return validate(json.loads(Path(path).read_text(encoding="utf-8")))


def proposed_points(policy: dict) -> dict:
    validate(policy)
    return {track["id"]: [
        {"p_source": p, "t_source": t,
         "p_pa": p * policy["units"]["kbar_to_pa"] if
             track["pressure_unit"] == "kbar" else
             p * policy["units"]["bar_to_pa"],
         "t_kelvin": t + policy["units"]["kelvin_from_celsius_offset"]
             if track["temperature_unit"] == "degC" else t}
        for p in track["P"] for t in track["T"]
    ] for track in policy["candidate_tracks"]}
