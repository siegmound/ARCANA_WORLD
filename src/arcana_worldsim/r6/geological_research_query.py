"""ARCANA R6: sparse native T0 geological research + physical delta-t readiness.

Read-only consumer of the FAIR-qualified native T0 source adapter. Samples and
material comparisons stay unverified research inputs; no inferred rock map or
physical history. The 100/1000-year horizon audit is a GO/NO-GO, NOT a solver.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

from .geological_coarse_state import (
    REQUEST_SCHEMA, _canonical_cells, _density_screen, _interval,
)
from .geological_source_t0_adapter import extract
from .identity import content_hash

QUERY_SCHEMA = "ARCANA_R6_T0_GEOLOGICAL_RESEARCH_QUERY_V1"
QUERY_REPORT_SCHEMA = "ARCANA_R6_T0_GEOLOGICAL_RESEARCH_QUERY_REPORT_V1"
DT_REPORT_SCHEMA = "ARCANA_R6_T0_SHORT_HORIZON_DT_FEASIBILITY_V1"
DT_SOURCE_PATH = "docs/arcana/research/B6N8H_T0_T1_PHYSICAL_STATE_MATRIX.json"
DT_SOURCE_BLOB = "3d27761f7f0558cf7bba7081a7cc76fad875e204"
T0_MA = 210.0
JULIAN_YEAR_SECONDS = 31557600
_MAYBE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{2,99}$")
SAMPLE_CLASSES = {"SYNTHETIC_RESEARCH_SAMPLE", "USER_REPORTED_UNVERIFIED_SAMPLE"}
MAX_REQUESTS = 8


class ResearchQueryError(ValueError):
    pass


def must(ok: bool, code: str):
    if not ok:
        raise ResearchQueryError(code)


def _id(x, code):
    must(type(x) is str and _MAYBE_ID.fullmatch(x) is not None, code)
    return x


def _sample(data):
    if data is None:
        return None
    must(type(data) is dict and set(data) == {
        "authority", "source_ref", "density_interval"},
        "GEO_RESEARCH_SAMPLE_SCHEMA_INVALID")
    must(data["authority"] in SAMPLE_CLASSES,
         "GEO_SAMPLE_CANNOT_CLAIM_AUTHENTICATED_OBSERVATION")
    _id(data["source_ref"], "GEO_RESEARCH_SAMPLE_SOURCE_REF_REQUIRED")
    density = _interval(data["density_interval"], "bulk_density_kg_m3")
    must(density is not None, "GEO_RESEARCH_SAMPLE_DENSITY_REQUIRED")
    return {"authority": data["authority"],
            "source_ref": data["source_ref"],
            "density_interval": density,
            "verified_natural_observation": False}


def validate_query(data):
    must(type(data) is dict and set(data) == {
        "schema", "at_ma", "research_question", "parent_cell_ids",
        "sample", "candidate_materials", "subdivision_factor"},
        "GEO_RESEARCH_QUERY_SCHEMA_INVALID")
    must(data["schema"] == QUERY_SCHEMA, "GEO_RESEARCH_SCHEMA_NOT_SUPPORTED")
    _id(data["research_question"], "GEO_RESEARCH_QUESTION_ID_INVALID")
    must(type(data["at_ma"]) in (int, float)
         and math.isfinite(data["at_ma"])
         and float(data["at_ma"]) == T0_MA,
         "GEO_QUERY_NON_T0_EPOCH_UNAVAILABLE")
    try:
        ids = _canonical_cells(data["parent_cell_ids"])
    except ValueError as exc:
        raise ResearchQueryError("GEO_QUERY_INVALID_PARENT_SELECTION") from exc
    must(1 <= len(ids) <= MAX_REQUESTS,
         "GEO_QUERY_EXCEEDS_SPARSE_NATIVE_CELL_BUDGET")
    sample = _sample(data["sample"])
    candidates = data["candidate_materials"]
    # This validates all candidate intervals and their asserted provenance,
    # but never interprets reference-model density as a natural observation.
    screening = _density_screen(
        None if sample is None else sample["density_interval"], candidates)
    factor = data["subdivision_factor"]
    must(factor is None or
         (type(factor) is int and 2 <= factor <= 8
          and len(ids) * factor * factor <= 256),
         "GEO_QUERY_REFINEMENT_BUDGET_INVALID")
    canonical = {
        "schema": QUERY_SCHEMA, "at_ma": T0_MA,
        "research_question": data["research_question"],
        "parent_cell_ids": ids, "sample": sample,
        "candidate_materials": candidates,
        "subdivision_factor": factor,
    }
    return canonical, screening


def research(root: Path, request: dict, *,
             field_package: Path | None = None,
             plate_partition: Path | None = None) -> dict:
    canonical, screening = validate_query(request)
    ids = canonical["parent_cell_ids"]
    factor = canonical["subdivision_factor"]
    refine = None
    if factor is not None:
        refine = {
            "schema": REQUEST_SCHEMA,
            "parent_cell_ids": ids, "at_ma": T0_MA,
            "subdivision_factor": factor,
            "research_question": canonical["research_question"],
            "sample_density_interval": (
                None if canonical["sample"] is None
                else canonical["sample"]["density_interval"]),
            "declared_density_candidates": canonical["candidate_materials"],
        }
    source = extract(root, ids, field_package=field_package,
                     plate_partition=plate_partition,
                     refinement_query=refine)
    must(source["selected_cell_count"] == len(ids),
         "GEO_ORIGINAL_SOURCE_CELL_JOIN_INCOMPLETE")
    return {
      "schema": QUERY_REPORT_SCHEMA,
      "decision": "SOURCE_BACKED_T0_RESEARCH_QUERY_ONLY_NO_NATURAL_ROCK_INFERENCE",
      "source_query_identity_sha256": content_hash(canonical),
      "source_original_grid_id": source["original_grid_id"],
      "research_epoch_ma": T0_MA,
      "research_question": canonical["research_question"],
      "sample": canonical["sample"],
      "sample_is_not_a_model_source_fact": True,
      "density_screening": screening,
      "density_screening_produces_posteriors": False,
      "model_reference_density_is_not_local_measurement": True,
      "source_field_package_sha256": source["source_field_package_sha256"],
      "source_vector_partition_sha256": source["source_vector_partition_sha256"],
      "source_document_git_blobs": source["source_document_git_blobs"],
      "source_cells": source["native_cell_source_records"],
      "selected_cell_count": len(ids),
      "refinement": source.get("read_only_geometric_refinement"),
      "actual_natural_material_identification": None,
      "actual_ore_presence": None,
      "actual_Deep_accessibility": None,
      "physical_T1": None,
      "history_store_writes": 0,
      "world_history_production_authorized": False,
      "mechanical_solve_authorized": False,
      "D_024": "ACTIVE",
    }


def _dt_source(root):
    raw = (root / DT_SOURCE_PATH).read_bytes()
    blob = hashlib.sha1(
        b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    must(blob == DT_SOURCE_BLOB, "GEO_DT_AUTHORITY_SOURCE_DRIFT")
    matrix = json.loads(raw)
    must(matrix["gates"]["H2_T0_THERMAL_STATE_AUTHORITY"] == "BLOCKED"
         and matrix["gates"]["H4_T0_TO_T1_EVOLUTION_AUTHORITY"] == "BLOCKED"
         and matrix["gates"]["H5_T1_GEOMETRY_AVAILABLE"] == "BLOCKED"
         and matrix["gates"]["H6_T1_THERMAL_STATE_AVAILABLE"] == "BLOCKED"
         and matrix["evolution"]["status"] ==
             "NO_GOVERNED_REDUCED_EVOLUTION_AVAILABLE",
         "GEO_DT_MATRIX_REQUIRES_FRESH_PHYSICAL_ADJUDICATION")
    return matrix


def dt_feasibility(root: Path, horizons: tuple[int, ...] = (100, 1000)) -> dict:
    must(type(horizons) is tuple and 1 <= len(horizons) <= 2
         and len(horizons) == len(set(horizons))
         and all(type(h) is int and h in (100, 1000) for h in horizons),
         "GEO_DT_ONLY_DECLARED_100_OR_1000_YEARS")
    matrix = _dt_source(Path(root))
    gates = matrix["gates"]
    required = (
        ("T0_GEOMETRY_AUTHORITY", "H1_T0_GEOMETRY_AUTHORITY"),
        ("T0_THERMAL_STATE", "H2_T0_THERMAL_STATE_AUTHORITY"),
        ("THERMAL_PROPERTY_BINDINGS", "H3_THERMAL_PROPERTY_BINDINGS"),
        ("T0_TO_T1_EVOLUTION", "H4_T0_TO_T1_EVOLUTION_AUTHORITY"),
        ("T1_GEOMETRY", "H5_T1_GEOMETRY_AVAILABLE"),
        ("T1_THERMAL_STATE", "H6_T1_THERMAL_STATE_AVAILABLE"),
        ("UNCERTAINTY_AND_VALIDITY", "H8_UNCERTAINTY_VALIDITY_COMPLETE"),
    )
    blockers = [
        {"gate": name, "source_gate": key, "source_status": gates[key],
         "required_status": "PHYSICALLY_QUALIFIED"}
        for name, key in required if gates[key] not in {"PASS", "QUALIFIED"}
    ]
    must(bool(blockers), "GEO_DT_NO_GO_SOURCE_HAS_CHANGED_REASSESS")
    return {
      "schema": DT_REPORT_SCHEMA,
      "decision": "NO_GO_PHYSICAL_T0_TO_T1_FOR_100_OR_1000_YEARS",
      "source_authority_matrix_git_blob": DT_SOURCE_BLOB,
      "source_authority_matrix_path": DT_SOURCE_PATH,
      "source_authority_matrix_age": "EARLIER_R6_GATE_AUDIT_NOT_FULL_CURRENT_G2_G3_STATUS",
      "delta_t_science_gate_is_independent_of_requested_duration": True,
      "source_gates_reviewed": len(required),
      "blocking_gates": blockers,
      "other_unclosed_g2_g3_gouge_normal_load_rheology_and_mantle_cut_forces":
          "REQUIRES_CURRENT_SEPARATE_PHYSICAL_QUALIFICATION",
      "horizons": [
          {"requested_delta_t_years": h,
           "elapsed_seconds_if_julian_year": h * JULIAN_YEAR_SECONDS,
           "arithmetic_target_ma_only_not_a_physical_state":
               T0_MA - h / 1_000_000,
           "physical_T1": None,
           "physical_simulation_executed": False,
           "solver_config_selected": False,
           "go": False}
          for h in sorted(horizons)
      ],
      "required_next_gate": (
        "PIN_T0_P_T_RHO_CP_K_AND_COMPOSITION_OR_VALID_REDUCED_STATE__"
        "BOUNDARY_HISTORY_EVOLUTION_LAW_G2_G3_FORCE_AND_FAULT_CLOSURE__"
        "NUMERICAL_DT_CONVERGENCE_AND_CONSERVATION"),
      "synthetic_noncanonical_experiments_may_be_proposed_separately": True,
      "no_world_history_written": True,
      "history_store_writes": 0,
      "world_history_production_authorized": False,
      "mechanical_solve_authorized": False,
      "D_024": "ACTIVE",
      "physical_T1": None,
    }


def write_new(out: Path, result: dict, *, inputs: dict):
    must(not out.exists(), "GEO_QUERY_EVIDENCE_ALREADY_EXISTS")
    out.mkdir(parents=True, exist_ok=False)
    payload = json.dumps(result, indent=2, ensure_ascii=False,
                         allow_nan=False).encode() + b"\n"
    (out/"REPORT.json").write_bytes(payload)
    manifest = {
        "schema": "ARCANA_R6_GEOLOGICAL_RESEARCH_AND_DT_GATE_EVIDENCE_V1",
        "input_sha256": content_hash(inputs),
        "report_sha256": hashlib.sha256(payload).hexdigest(),
        "no_history_store_mutations": True,
        "no_physical_T1": True,
    }
    (out/"MANIFEST.json").write_text(json.dumps(
        manifest, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path,
        default=Path(__file__).resolve().parents[3])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--request", type=Path)
    mode.add_argument("--dt-gate", action="store_true")
    parser.add_argument("--field-package", type=Path)
    parser.add_argument("--plate-partition", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    if args.dt_gate:
        must(args.field_package is None and args.plate_partition is None,
             "GEO_DT_GATE_DOES_NOT_NEED_SOURCE_BINARY_PATHS")
        result = dt_feasibility(root)
        bindings = {"mode": "dt_gate", "horizons": [100, 1000]}
    else:
        raw = json.loads(args.request.read_text(encoding="utf-8"))
        result = research(root, raw, field_package=args.field_package,
                          plate_partition=args.plate_partition)
        bindings = {"mode": "research", "request": raw,
                    "source_field_package_sha256": result[
                        "source_field_package_sha256"],
                    "source_vector_partition_sha256": result[
                        "source_vector_partition_sha256"]}
    write_new(args.output, result, inputs=bindings)
    print(json.dumps({
        "decision": result["decision"],
        "source_bound_cells": result.get("selected_cell_count", 0),
        "child_geometry_count": (
            result.get("refinement") or {}).get("child_geometry_count", 0),
        "dt_horizon_years": [x["requested_delta_t_years"] for x in
                             result.get("horizons", [])],
        "physical_T1": None,
        "world_history_production_authorized": False,
    }))


if __name__ == "__main__":
    main()
