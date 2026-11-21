"""Sparse, noncanonical geological coarse-state and request-scoped refinement.

The 1-degree canonical grid, hierarchical child support, and R6 historical
query/refinement mechanisms ALREADY EXIST. This module adds only an evidence
contract for sparse parent-cell geological candidates and bounded on-demand
queries. It never interpolates parent geology to children, runs T0->T1,
infers an ore/mineral/Deep deposit, or writes HistoryStore.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Mapping

from .hierarchical_refinement import (
    PARENT_GRID_ID, canonical_parent_order, subdivide_parent_cells,
)
from .identity import canonical_bytes, content_hash

SCHEMA = "ARCANA_R6_GEOLOGICAL_COARSE_CANDIDATE_CATALOG_V1"
REQUEST_SCHEMA = "ARCANA_R6_GEOLOGICAL_ON_DEMAND_REQUEST_V1"
OUTPUT_SCHEMA = "ARCANA_R6_GEOLOGICAL_COARSE_ON_DEMAND_RESEARCH_REPORT_V1"
AUTHORITY = "DECLARED_NONCANONICAL_GEOLOGICAL_HYPOTHESIS_ONLY"
INDEX = "docs/arcana/research/B6N8N_ADMITTED_SUPPORT_BINDING_INDEX.json"
INDEX_GIT_SHA = "e06770577ebaf549aa113a4e72ec9f6095a29c2d"
SOURCE_MAIN_FAIR_PARENT = "3805648c36aa70e7ab709e593c33abaaedfb616e"
FAMILIES = {
    "UNRESOLVED", "CLASTIC_SEDIMENT_CANDIDATE",
    "CARBONATE_SEDIMENT_CANDIDATE", "FELSIC_CRUST_CANDIDATE",
    "MAFIC_CRUST_CANDIDATE", "ULTRAMAFIC_CANDIDATE",
    "METAMORPHIC_CANDIDATE", "OTHER_BULK_MATERIAL_CANDIDATE",
}
EVENT_KINDS = {
    "TECTONIC_DEFORMATION", "MAGMATISM", "METAMORPHISM", "EROSION",
    "SEDIMENTATION", "ALTERATION", "FLUID_TRANSPORT", "CRUST_RECYCLING",
    "RESOURCE_ENRICHMENT_HYPOTHESIS",
}
OBSERVABLES = {
    "bulk_density_kg_m3": ("kg/m3", 0.0, 20000.0),
    "crustal_thickness_m": ("m", 0.0, 1.0e7),
    "temperature_k": ("K", 0.0, 1.0e7),
}
_CELL = re.compile(r"^R6G1D-R(\d{3})-C(\d{3})$")
_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{2,99}$")
_SHA = re.compile(r"^[a-f0-9]{64}$")
_MAX_SNAPSHOTS = 512
_MAX_EVENTS = 512
_MAX_REQUEST_PARENTS = 8
_MAX_REQUEST_CHILDREN = 256


class GeologicalContractError(ValueError):
    pass


def require(condition: bool, code: str):
    if not condition:
        raise GeologicalContractError(code)


def _token(value: object, code: str) -> str:
    require(type(value) is str and _TOKEN.fullmatch(value) is not None, code)
    return value


def _time(value: object) -> float:
    require(type(value) in (int, float) and math.isfinite(value)
            and 0.0 <= value <= 210.0, "GEO_TIME_OUTSIDE_T0_TO_PRESENT")
    return float(value)


def _cell_id(value: object) -> str:
    require(type(value) is str and _CELL.fullmatch(value) is not None,
            "GEO_INVALID_PARENT_CELL_ID")
    m = _CELL.fullmatch(value)
    assert m is not None
    require(int(m[1]) < 180 and int(m[2]) < 360,
            "GEO_PARENT_CELL_OUTSIDE_ORIGINAL_GRID")
    return value


def _canonical_cells(values: object, *, nonempty=True) -> list[str]:
    require(type(values) is list and
            (bool(values) or not nonempty),
            "GEO_PARENT_CELL_COLLECTION_INVALID")
    for value in values:
        _cell_id(value)
    try:
        result = list(canonical_parent_order(values))
    except ValueError as exc:
        raise GeologicalContractError("GEO_DUPLICATE_OR_INVALID_PARENT_CELLS") from exc
    return result


def _index(root: Path) -> dict:
    data = (root / INDEX).read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data)
    require(blob.hexdigest() == INDEX_GIT_SHA, "GEO_B6N8N_SOURCE_INDEX_SHA_DRIFT")
    row = json.loads(data)
    require(row.get("schema") == "ARCANA_R6_B6N8N_ADMITTED_SUPPORT_BINDING_INDEX_V1"
            and row["grid"]["grid_id"] == PARENT_GRID_ID
            and row["grid"]["shape"] == [180, 360]
            and row["partition_counts"]["native"] == 64800
            and row["partition_counts"]["admitted"] == 63620,
            "GEO_ORIGINAL_GLOBAL_GRID_IDENTITY_DRIFT")
    return row


def empty_catalog(root: Path) -> dict:
    _index(root)
    return {
        "schema": SCHEMA, "authority": AUTHORITY,
        "original_grid_id": PARENT_GRID_ID,
        "original_index_git_blob": INDEX_GIT_SHA,
        "source_checkpoint_id": None,
        "source_checkpoint_sha256": None,
        "events": [], "snapshots": [],
        "canonical_world_state_authorized": False,
        "world_history_production_authorized": False,
        "physical_T1": None,
    }


def _interval(value: object, metric: str) -> dict | None:
    if value is None:
        return None
    require(metric in OBSERVABLES, "GEO_UNKNOWN_OBSERVABLE")
    unit, minval, maxval = OBSERVABLES[metric]
    require(type(value) is dict and set(value) == {"unit", "low", "high"}
            and value.get("unit") == unit,
            "GEO_MEASUREMENT_INTERVAL_UNIT_OR_FIELDS_INVALID")
    lo, hi = value["low"], value["high"]
    require(all(type(x) in (int, float) and math.isfinite(x)
                and minval <= x <= maxval for x in (lo, hi))
            and lo <= hi, "GEO_MEASUREMENT_INTERVAL_INVALID")
    return {"unit": unit, "low": float(lo), "high": float(hi)}


def _event(row: object) -> dict:
    require(type(row) is dict and set(row) == {
        "event_id", "kind", "at_ma", "parent_cell_ids", "source_claim"},
        "GEO_EVENT_SCHEMA_INVALID")
    event_id = _token(row["event_id"], "GEO_EVENT_ID_INVALID")
    require(row["kind"] in EVENT_KINDS, "GEO_EVENT_KIND_INVALID")
    cells = _canonical_cells(row["parent_cell_ids"])
    require(len(cells) <= 32, "GEO_EVENT_SPATIAL_SUPPORT_EXCEEDS_BUDGET")
    require(row["source_claim"] == "AUTHORIAL_HYPOTHESIS_NOT_PHYSICAL_EVENT",
            "GEO_EVENT_CLAIM_NOT_QUALIFIED")
    return {"event_id": event_id, "kind": row["kind"],
            "at_ma": _time(row["at_ma"]), "parent_cell_ids": cells,
            "source_claim": row["source_claim"]}


def _snapshot(row: object) -> dict:
    require(type(row) is dict and set(row) == {
        "parent_cell_id", "at_ma", "material_family",
        "uncertainty_class", "observables", "event_refs", "source_claim"},
        "GEO_SNAPSHOT_SCHEMA_INVALID")
    cell = _cell_id(row["parent_cell_id"])
    family = row["material_family"]
    require(type(family) is str and family in FAMILIES,
            "GEO_FAMILY_NOT_IN_GENERIC_VOCABULARY")
    observables = row["observables"]
    require(type(observables) is dict and
            set(observables) == set(OBSERVABLES),
            "GEO_COARSE_OBSERVABLES_MISSING_OR_EXTRA")
    vals = {key: _interval(observables[key], key)
            for key in sorted(OBSERVABLES)}
    uncertainty = row["uncertainty_class"]
    has_values = any(value is not None for value in vals.values())
    require((uncertainty == "BOUNDED_AUTHORIAL_HYPOTHESIS"
             if has_values or family != "UNRESOLVED"
             else uncertainty == "UNRESOLVED_UNKNOWN"),
            "GEO_COARSE_UNCERTAINTY_MISMATCH")
    refs = row["event_refs"]
    require(type(refs) is list and all(type(ref) is str and
            _TOKEN.fullmatch(ref) for ref in refs) and
            len(refs) == len(set(refs)),
            "GEO_SNAPSHOT_EVENT_REFS_INVALID")
    require(row["source_claim"] == "AUTHORIAL_HYPOTHESIS_NOT_VERIFIED_GEOLOGY",
            "GEO_UNVERIFIED_SNAPSHOT_SOURCE_PROMOTION")
    return {"parent_cell_id": cell, "at_ma": _time(row["at_ma"]),
            "material_family": family,
            "uncertainty_class": uncertainty,
            "observables": vals, "event_refs": sorted(refs),
            "source_claim": row["source_claim"]}


def validate_catalog(raw: object, root: Path) -> dict:
    idx = _index(root)
    require(type(raw) is dict and set(raw) == {
        "schema", "authority", "original_grid_id",
        "original_index_git_blob", "source_checkpoint_id",
        "source_checkpoint_sha256", "events", "snapshots",
        "canonical_world_state_authorized",
        "world_history_production_authorized", "physical_T1"},
        "GEO_CATALOG_FIELDS_INVALID")
    require(raw["schema"] == SCHEMA and raw["authority"] == AUTHORITY
            and raw["original_grid_id"] == PARENT_GRID_ID
            and raw["original_index_git_blob"] == INDEX_GIT_SHA
            and raw["source_checkpoint_id"] is None
            and raw["source_checkpoint_sha256"] is None
            and raw["canonical_world_state_authorized"] is False
            and raw["world_history_production_authorized"] is False
            and raw["physical_T1"] is None,
            "GEO_CATALOG_CLAIMS_UNAUTHORIZED_HISTORY")
    require(type(raw["events"]) is list and len(raw["events"]) <= _MAX_EVENTS
            and type(raw["snapshots"]) is list
            and len(raw["snapshots"]) <= _MAX_SNAPSHOTS,
            "GEO_SPARSE_CATALOG_BUDGET_EXCEEDED")
    events = [_event(x) for x in raw["events"]]
    event_by_id = {ev["event_id"]: ev for ev in events}
    require(len(event_by_id) == len(events), "GEO_DUPLICATED_EVENT_ID")
    snapshots = [_snapshot(x) for x in raw["snapshots"]]
    keys = [(s["parent_cell_id"], s["at_ma"]) for s in snapshots]
    require(len(keys) == len(set(keys)), "GEO_DUPLICATED_SNAPSHOT_AT_TIME")
    for s in snapshots:
        for event_id in s["event_refs"]:
            event = event_by_id.get(event_id)
            require(event is not None and
                    s["parent_cell_id"] in event["parent_cell_ids"] and
                    s["at_ma"] <= event["at_ma"] <= 210.,
                    "GEO_EVENT_OUTSIDE_CELL_OR_PRIOR_TIME")
    events.sort(key=lambda x: (-x["at_ma"], x["event_id"]))
    snapshots.sort(key=lambda x: (x["parent_cell_id"], -x["at_ma"]))
    catalog = {
        "schema": SCHEMA, "authority": AUTHORITY,
        "original_grid_id": PARENT_GRID_ID,
        "original_index_git_blob": INDEX_GIT_SHA,
        "source_checkpoint_id": None,
        "source_checkpoint_sha256": None,
        "events": events, "snapshots": snapshots,
        "canonical_world_state_authorized": False,
        "world_history_production_authorized": False,
        "physical_T1": None,
    }
    return {
        "catalog": catalog,
        "catalog_digest_sha256": content_hash(catalog),
        "source_index_sha256": hashlib.sha256(
            (root / INDEX).read_bytes()).hexdigest(),
        "native_parent_cell_count": idx["partition_counts"]["native"],
        "thermal_support_cells_NOT_geochemical_mapping":
            idx["partition_counts"]["admitted"],
        "noncanonical_sparse_snapshot_count": len(snapshots),
        "noncanonical_event_reference_count": len(events),
        "genuine_physical_event_count": 0,
        "physical_geological_cell_assignments": 0,
    }


def _density_screen(sample: object, candidates: object) -> dict:
    require(type(candidates) is list and len(candidates) <= 16,
            "GEO_DENSITY_CANDIDATE_BUDGET_OR_SCHEMA_INVALID")
    if sample is None:
        require(not candidates, "GEO_DENSITY_CANDIDATES_WITHOUT_SAMPLE")
        return {"status": "NOT_REQUESTED", "conditional_candidates": []}
    obs = _interval(sample, "bulk_density_kg_m3")
    require(obs is not None, "GEO_DENSITY_SAMPLE_UNKNOWN")
    if not candidates:
        return {"status": "INSUFFICIENT_CALIBRATED_PRIORS",
                "sample_interval": obs,
                "conditional_candidates": [],
                "actual_material_identification": None}
    results = []
    seen = set()
    for row in candidates:
        require(type(row) is dict and set(row) == {
            "candidate_id", "material_family", "hypothetical_density_range",
            "authority"},
            "GEO_DENSITY_CANDIDATE_SCHEMA_INVALID")
        cid = _token(row["candidate_id"], "GEO_DENSITY_CANDIDATE_ID_INVALID")
        require(cid not in seen, "GEO_DUPLICATE_DENSITY_CANDIDATE")
        seen.add(cid)
        require(row["material_family"] in FAMILIES and
                row["material_family"] != "UNRESOLVED" and
                row["authority"] == "DECLARED_UNCALIBRATED_REFERENCE_INTERVAL",
                "GEO_DENSITY_CANDIDATE_AUTHORITY_INVALID")
        bound = _interval(row["hypothetical_density_range"],
                          "bulk_density_kg_m3")
        require(bound is not None, "GEO_DENSITY_CANDIDATE_INTERVAL_REQUIRED")
        overlap = max(obs["low"], bound["low"]) <= min(
            obs["high"], bound["high"])
        results.append({"candidate_id": cid,
            "material_family": row["material_family"],
            "source_density_interval": bound,
            "overlap_under_declared_intervals": overlap,
            "posterior_probability": None,
            "geological_presence_confirmed": False})
    return {"status": "INTERVAL_OVERLAP_ONLY_NOT_IDENTIFICATION",
            "sample_interval": obs,
            "conditional_candidates": results,
            "actual_material_identification": None}


def make_refinement_plan(validated: Mapping[str, Any], request: object) -> dict:
    require(type(request) is dict and set(request) == {
        "schema", "parent_cell_ids", "at_ma", "subdivision_factor",
        "research_question", "sample_density_interval",
        "declared_density_candidates"},
        "GEO_REQUEST_FIELDS_INVALID")
    require(request["schema"] == REQUEST_SCHEMA,
            "GEO_REQUEST_SCHEMA_INVALID")
    parents = _canonical_cells(request["parent_cell_ids"])
    factor = request["subdivision_factor"]
    require(1 <= len(parents) <= _MAX_REQUEST_PARENTS and
            type(factor) is int and 2 <= factor <= 8 and
            len(parents)*factor*factor <= _MAX_REQUEST_CHILDREN,
            "GEO_REFINEMENT_BUDGET_EXCEEDED")
    epoch = _time(request["at_ma"])
    question = _token(request["research_question"], "GEO_RESEARCH_QUESTION_ID_INVALID")
    screening = _density_screen(request["sample_density_interval"],
                                request["declared_density_candidates"])
    catalog = validated["catalog"]
    snapshots = {(s["parent_cell_id"], s["at_ma"]): s for s in
                 catalog["snapshots"]}
    selected = []
    for parent in parents:
        snapshot = snapshots.get((parent, epoch))
        selected.append({"parent_cell_id": parent,
            "coarse_snapshot": snapshot,
            "parent_density_kg_m3_interval":
                (None if snapshot is None else
                 snapshot["observables"]["bulk_density_kg_m3"]),
            "parent_mass_kg": None,
            "geological_event_refs":
                [] if snapshot is None else snapshot["event_refs"],
            "physical_support_proven": False})
    request_identity = {
        "catalog_digest_sha256": validated["catalog_digest_sha256"],
        "parent_cell_ids": parents, "at_ma": epoch,
        "subdivision_factor": factor, "research_question": question,
        "sample_density_interval": request["sample_density_interval"],
        "declared_density_candidates": request["declared_density_candidates"],
    }
    geometry = subdivide_parent_cells(parent_cell_ids=parents,
        subdivision_factor=factor,
        request_scope="GEO_ON_DEMAND_" + content_hash(request_identity))
    return {
        "schema": OUTPUT_SCHEMA,
        "decision": "ON_DEMAND_GEOMETRY_AND_CONSTRAINTS_ONLY_NO_GEOLOGY_CREATED",
        "catalog_digest_sha256": validated["catalog_digest_sha256"],
        "source_original_grid_id": PARENT_GRID_ID,
        "research_epoch_ma": epoch,
        "research_question": question,
        "refinement_request_id": geometry[0].request_id,
        "parent_count": len(parents), "child_geometry_count": len(geometry),
        "parents": selected,
        "children": [{**item.to_dict(),
            "bulk_density_kg_m3": None,
            "material_family": None, "mineral_phase_fractions": None,
            "water_state": None, "ore_deposit_probability": None,
            "Deep_X_accessibility": None,
            "child_mass_kg": None,
            "scientific_provider_attached": False}
            for item in geometry],
        "density_screening": screening,
        "conservation_requirement":
            "FUTURE_PROVIDER_MUST_PRESERVE_AUTHENTIC_PARENT_EXTENSIVE_QUANTITIES",
        "conservation_checked": False,
        "physical_parent_mass_available": False,
        "child_area_is_not_assumed_equal": True,
        "event_history_is_declared_not_replayed": True,
        "history_store_mutations": 0,
        "physical_T1": None,
        "mechanical_solve_authorized": False,
        "world_history_production_authorized": False,
    }


def report(root: Path, catalog: object, request: object | None = None) -> dict:
    validated = validate_catalog(catalog, root)
    if request is None:
        return {"schema": OUTPUT_SCHEMA,
            "decision": "SPARSE_COARSE_CATALOG_CONTRACT_VERIFIED_NO_REAL_T0_STATE",
            "catalog_digest_sha256": validated["catalog_digest_sha256"],
            "native_parent_cell_count": validated["native_parent_cell_count"],
            "thermal_support_cells_NOT_geochemical_mapping":
                validated["thermal_support_cells_NOT_geochemical_mapping"],
            "noncanonical_sparse_snapshot_count":
                validated["noncanonical_sparse_snapshot_count"],
            "noncanonical_event_reference_count":
                validated["noncanonical_event_reference_count"],
            "physical_geological_cell_assignments": 0,
            "history_store_mutations": 0, "physical_T1": None,
            "mechanical_solve_authorized": False,
            "world_history_production_authorized": False}
    return make_refinement_plan(validated, request)


def write_evidence(output: Path, result: Mapping[str, Any],
                   catalog_bytes: bytes, request_bytes: bytes | None) -> None:
    require(not output.exists(), "GEO_OUTPUT_EXISTS_NO_OVERWRITE")
    output.mkdir(parents=True, exist_ok=False)
    dst = output / "REPORT.json"
    dst.write_bytes(json.dumps(result, indent=2,
        ensure_ascii=False, allow_nan=False).encode("utf-8") + b"\n")
    manifest = {
        "schema": "ARCANA_R6_GEOLOGICAL_COARSE_ON_DEMAND_MANIFEST_V1",
        "input_catalog_sha256": hashlib.sha256(catalog_bytes).hexdigest(),
        "input_request_sha256": (
            None if request_bytes is None else
            hashlib.sha256(request_bytes).hexdigest()),
        "files": {"REPORT.json": hashlib.sha256(dst.read_bytes()).hexdigest()},
        "geometry_only": True, "noncanonical_only": True,
        "no_rock_inventory_created": True, "no_physical_T0_or_T1": True,
        "no_world_history": True,
    }
    (output / "MANIFEST.json").write_text(json.dumps(
        manifest, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path,
        default=Path(__file__).resolve().parents[3])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--empty-template-out", type=Path)
    mode.add_argument("--catalog", type=Path)
    parser.add_argument("--query", type=Path)
    parser.add_argument("--output", type=Path)
    a = parser.parse_args()
    if a.empty_template_out is not None:
        require(a.query is None and a.output is None,
                "GEO_TEMPLATE_AND_REPORT_OPTIONS_CONFLICT")
        require(not a.empty_template_out.exists(),
                "GEO_OUTPUT_EXISTS_NO_OVERWRITE")
        data = empty_catalog(a.repo_root)
        a.empty_template_out.write_bytes(
            json.dumps(data, indent=2).encode("utf-8")+b"\n")
        print(json.dumps({"status": "EMPTY_SPARSE_GEOLOGY_TEMPLATE",
              "real_geological_cells": 0, "physical_T1": None}))
    else:
        require(a.output is not None, "GEO_OUTPUT_REQUIRED")
        raw = a.catalog.read_bytes()
        qraw = None if a.query is None else a.query.read_bytes()
        result = report(a.repo_root, json.loads(raw),
                        None if qraw is None else json.loads(qraw))
        write_evidence(a.output, result, raw, qraw)
        print(json.dumps({
            "decision": result["decision"],
            "child_geometry_count": result.get("child_geometry_count", 0),
            "actual_geological_cells": 0,
            "physical_T1": None}))


if __name__ == "__main__":
    main()
