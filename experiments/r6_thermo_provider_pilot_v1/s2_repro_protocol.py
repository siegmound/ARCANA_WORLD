"""S2 pre-run contract. No physical provider is executed by this module."""
from __future__ import annotations
import json
import math
from pathlib import Path

FILE = Path(__file__).with_name("s2_repeatability_protocol_v1.json")

class S2ProtocolError(ValueError):
    pass

def check(test, code):
    if not test:
        raise S2ProtocolError(code)

def finite_positive(x):
    return type(x) in (int, float) and math.isfinite(x) and 0 < x < 1e4

def load(path=FILE):
    return validate(json.loads(Path(path).read_text()))

def validate(p):
    check(p.get("schema") == "ARCANA_R6_THERMO_S2_REPEATABILITY_PROTOCOL_V1"
          and p.get("status") == "CANDIDATE_NOT_FAIR_TESTED__NO_REAL_S2_RUNS"
          and p.get("scope") == "EARTH_UPSTREAM_FIXTURES_ONLY",
          "S2_PROTOCOL_STATUS_OR_SCOPE_INVALID")
    check(p.get("s1_source_sha") == "f8d659042a739789e7a131dfc926cda1ceca30a4"
          and p.get("s1_evidence_manifest_sha256") ==
              "538c1b61f801c9902f8aa9b1b189b07ba38357eec339eb2b0211713f83299227",
          "S2_S1_PROVENANCE_DRIFT")
    check(p.get("runs_per_case") == 5 and p.get("new_process_each_run") is True
          and p.get("threads") == 1, "S2_PROCESS_INDEPENDENCE_INVALID")
    names = [c.get("id") for c in p.get("cases", [])]
    check(names == ["MAGEMIN_PREDEFINED_KLB1", "MAGEMIN_CUSTOM_IG",
                   "PERPLEX_BL691_MEEMUM"], "S2_CASE_IDENTITIES_INVALID")
    pins = p.get("pins", {})
    check(pins.get("julia_version") == "1.10.4"
          and pins.get("magemin_c_version") == "2.4.5"
          and pins.get("magemin_jll_version") == "2.1.0+0"
          and pins.get("magemin_c_upstream_commit") ==
             "f4fd5ce3670b73693d046e65585e2b79d45c8e3a"
          and pins.get("perplex_version") == "v7.3.3"
          and pins.get("perplex_source_commit") ==
             "950d882bb6a9325a627109aa7154f7b526aa3087"
          and pins.get("perplex_linux_archive_sha256") ==
             "ace6f81064c25709b401c3c49bc88410badad95fd7a876831c120eeed45f28e7",
          "S2_UPSTREAM_PROVIDER_PIN_DRIFT")
    m = p.get("magemin_tolerances", {})
    x = p.get("perplex_tolerances", {})
    mexpected = {"phase_fraction_abs","phase_fraction_rel",
                 "rho_abs_kg_per_m3","rho_rel","g_system_abs_kj_per_mol",
                 "g_system_rel","native_oxide_component_closure_abs",
                 "source_to_native_component_closure_abs",
                 "bulk_res_norm_max","phase_fraction_sum_abs"}
    xexpected = {"phase_percent_abs_pp","phase_percent_rel",
                 "pressure_abs_bar","temperature_abs_kelvin",
                 "printed_molar_component_closure"}
    check(set(m) == mexpected and set(x) == xexpected
          and all(finite_positive(m[k]) for k in mexpected)
          and all(finite_positive(x[k]) for k in xexpected -
                  {"printed_molar_component_closure"})
          and x["printed_molar_component_closure"] ==
              "EACH_COMPONENT_DECIMAL_ROUNDING_INTERVAL_OVERLAP",
          "S2_TOLERANCES_UNDECLARED")
    check(m["phase_fraction_abs"] <= 1e-3
          and m["native_oxide_component_closure_abs"] <= 1e-9
          and m["source_to_native_component_closure_abs"] <= 1e-10
          and m["bulk_res_norm_max"] <= 1e-8
          and m["g_system_abs_kj_per_mol"] <= 1e-2
          and x["phase_percent_abs_pp"] <= .2,
          "S2_SCREEN_TOO_PERMISSIVE")
    need_m = {"status","P_kbar","T_C","G_system","rho_kg_m3","phases",
              "phase_mass_fractions","oxides","bulk_wt","phase_comp_wt",
              "bulk_res_norm","iterations","source_native_basis_closure_custom"}
    need_x = {"status","official_P_bar","official_T_K","phase_wt_percent",
              "raw_prn_sha256","raw_stdout_sha256",
              "printed_molar_component_rounding_audit"}
    check(set(p.get("per_run_fields_magemin", [])) == need_m
          and set(p.get("per_run_fields_perplex", [])) == need_x,
          "S2_OUTPUT_FIELDS_INSUFFICIENT")
    rules = p.get("rules", {})
    exact = {"compare_phase_sets_by_name":True,
             "no_phase_alias_without_reviewer_crosswalk":True,
             "scalar_stability_comparison":
                "ABS_DELTA_LE_ABS_TOL_PLUS_REL_TOL_TIMES_MAX_ABS",
             "report_max_observed_absolute_and_relative_deltas":True,
             "times_are_descriptive_not_acceptance":True,
             "all_raw_runs_write_once":True,
             "preserve_partial_evidence_on_failure":True,
             "no_same_database_or_chemistry_cross_provider_equivalence":True,
             "no_oxide_basis_conversion_without_documented_stoichiometry":True,
             "absolute_tolerances_are_engineering_repeatability_screens_not_physical_uncertainties":True,
             "D_024":"ACTIVE","physical_T1":None,
             "mechanical_solve_authorized":False,
             "WORLD_HISTORY_PRODUCTION_AUTHORIZED":False}
    check(set(rules) == set(exact)
          and all(rules.get(k,object()) == v for k,v in exact.items()),
          "S2_GOVERNANCE_DRIFT")
    return p

def stability_screen(a, b, abs_tol, rel_tol):
    check(finite_positive(abs_tol) and finite_positive(rel_tol),
          "S2_INVALID_COMPARISON_TOLERANCE")
    check(all(type(x) in (int,float) and math.isfinite(x) for x in (a,b)),
          "S2_NONFINITE_OBSERVABLE")
    return abs(a-b) <= abs_tol+rel_tol*max(abs(a),abs(b))
