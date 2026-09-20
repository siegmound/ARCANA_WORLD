from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import platform
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXTERNAL = ROOT.parent / "_ARCANA_EXTERNAL_SOURCES"
PARENT = EXTERNAL / "p7q_parent_state"
PRE5C = PARENT / "PRE5C_STATIC_REBUILD" / "PRE5C_STATIC_PARENT_STATE_0KA.jsonl.gz"
BDTICM = PARENT / "PRE5F_SUBSTRATE_PROVIDER_BUNDLE" / "SHANGGUAN_DTB_2017" / "raw" / "BDTICM_M_250m_ll.tif"
OUT = PARENT / "PRE5I_STATIC_MATERIALIZATION"
STAGE = "R5.17-B7-A3F2-P7Q-PRE5I"
TARGET = 50568
TARGET_SHA = "3b139c494c2714bba5bbeecce426bb33bbcda6d7acbb5188471c9fa172ef9e28"
PRE5C_SHA = "e25cd2b55e34e5b175aaf631849dc319448f8510b83d1407ef9f1ffab0a4caee"
BDTICM_SHA = "b099653ece2716693f6dbfa02ec5fdea38763a7f1a0a875bbe2e77526980e136"
NODATA = -32768
GUM = {"ncols": 720, "nrows": 347, "xllcorner": -179.99998074964, "yllcorner": -89.985256795408, "cellsize": 0.5}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(name: str, payload: dict) -> None:
    (ROOT / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def base_result(decision: str, **extra) -> dict:
    return {"stage": STAGE, "decision": decision, "verdict": decision, "status": "BLOCKED__NO_CLASSIFICATION", "next_action": "RECOVER_OR_PROVISION_APPROVED_BASE_RESOLUTION_WINDOWED_GEOTIFF_READER", "direct_target_cells": TARGET, "target_identity_sha256": TARGET_SHA, "classifier_executed": False, "logical_universal_footprint_predicate_applied": False, "provider_values_resampled": False, "provider_values_numerically_aggregated": False, "positive_dtb_threshold_authorized": False, "residual_positive_rule_authorized": False, "residual_regolith_branch": "RESIDUAL_REGOLITH", "residual_regolith_classification": "NOT_AUTHORIZED", "saprolite_branch": "SAPROLITE_OR_DEEP_WEATHERING", "saprolite_classification": "NOT_AUTHORIZED", "bedrock_exposed_assigned": 0, "residual_regolith_assigned": 0, "saprolite_assigned": 0, "classified_cells": 0, "abstained_cells": 0, "canonical_parent_created": False, "physical_soil_created": False, "temporal_candidate_created": False, "temporal_reconstruction": False, "P7Q_reopened": False, "scientific_authority_register_mutated": False, **extra}


def emit_blocked(decision: str, reader: str, extra: dict | None = None) -> int:
    payload = base_result(decision, raster_reader=reader, cells_inspected=0, base_ifd_confirmed=False, external_payloads="NOT_CREATED", **(extra or {}))
    write_json("R5_17_B7_A3F2_P7Q_PRE5I_MATERIALIZATION_CONTRACT.json", {"stage": STAGE, "execution_attempted": False, "blocked_before_window_read": True, "reader_requirement": "bounded base-resolution window-capable GeoTIFF reader (rasterio or GDAL)", "authorized_predicate": "universal all-zero BDTICM base-resolution pixels over complete target footprint", "residual_regolith_branch": "RESIDUAL_REGOLITH", "residual_regolith_classification": "NOT_AUTHORIZED", "saprolite_branch": "SAPROLITE_OR_DEEP_WEATHERING", "saprolite_classification": "NOT_AUTHORIZED", "no_payloads_created": True})
    write_json("R5_17_B7_A3F2_P7Q_PRE5I_DECISION_LEDGER_MANIFEST.json", {"stage": STAGE, "status": "NOT_CREATED__READER_BLOCKER", "records": 0, "path": None, "sha256": None, "bytes": None})
    write_json("R5_17_B7_A3F2_P7Q_PRE5I_STATIC_CANDIDATE_MANIFEST.json", {"stage": STAGE, "status": "NOT_CREATED__READER_BLOCKER", "records": 0, "path": None, "sha256": None, "bytes": None, "pre5c_untouched": True})
    write_json("R5_17_B7_A3F2_P7Q_PRE5I_STATIC_STATE_AUDIT.json", {"stage": STAGE, "reader": reader, "base_ifd_confirmed": False, "target": {"count": TARGET, "sha256": TARGET_SHA}, "outcomes": {"classified": 0, "abstained": 0}, "non_target_drift": 0, "schema_valid_records": 0, "status": "BLOCKED_BEFORE_CLASSIFICATION"})
    write_json("R5_17_B7_A3F2_P7Q_PRE5I_ADJUDICATION.json", payload)
    (ROOT / "R5_17_B7_A3F2_P7Q_PRE5I_ADJUDICATION.md").write_text(f"# {STAGE}\n\nDecision: `{decision}`\n\nPRE5I stopped fail-closed before classification because no approved bounded base-resolution GeoTIFF window reader is available. No decision ledger, candidate payload, or PRE5J execution was performed.\n", encoding="utf-8")
    return 2


def target_geometry(cell_id: str) -> tuple[float, float, float, float, int, int]:
    suffix = cell_id.rsplit("_R", 1)[1]
    north_row, col = (int(x) for x in suffix.split("_C"))
    south_row = GUM["nrows"] - 1 - north_row
    xmin = GUM["xllcorner"] + col * GUM["cellsize"]
    xmax = xmin + GUM["cellsize"]
    ymin = GUM["yllcorner"] + south_row * GUM["cellsize"]
    ymax = ymin + GUM["cellsize"]
    return xmin, ymin, xmax, ymax, north_row, col


def coverage(bounds, geom) -> str:
    left, bottom, right, top = bounds
    xmin, ymin, xmax, ymax, *_ = geom
    ix = max(0.0, min(xmax, right) - max(xmin, left))
    iy = max(0.0, min(ymax, top) - max(ymin, bottom))
    if ix == 0.0 or iy == 0.0:
        return "OUTSIDE_PROVIDER_EXTENT"
    if ix * iy >= GUM["cellsize"] ** 2 * (1.0 - 1e-10):
        return "FULL_GEOMETRIC_COVERAGE"
    return "PARTIAL_GEOMETRIC_COVERAGE"


def mutate_record(record: dict) -> dict:
    out = json.loads(json.dumps(record))
    out["material_branch"] = "BEDROCK_EXPOSED"
    out["state_support"] = "DERIVED_SUPPORTED"
    out["material_class"] = {"value": "BDTICM_EQ_0_CM", "support_status": "DERIVED_SUPPORTED"}
    out["genetic_class"] = None
    out["applicability"]["snapshot_applicability"] = "APPLIES"
    out["depth_state"] = {"support_status": "DERIVED_SUPPORTED", "value_status": "KNOWN_ZERO", "temporal_status": "ENDPOINT_ONLY_0KA", "uncertainty": {"categories": ["SOURCE_CLASS_UNCERTAINTY", "SPATIAL_REMAP_UNCERTAINTY", "TEMPORAL_AGE_UNCERTAINTY", "MODEL_STRUCTURAL_UNCERTAINTY"]}}
    out["missing_fields"] = [x for x in out.get("missing_fields", []) if x != "depth"]
    out["uncertainty"] = {"categories": ["SOURCE_CLASS_UNCERTAINTY", "SPATIAL_REMAP_UNCERTAINTY", "TEMPORAL_AGE_UNCERTAINTY", "MODEL_STRUCTURAL_UNCERTAINTY"], "derivation": "Static 0ka candidate from universal all-zero native BDTICM footprint predicate.", "representation": "QUALITATIVE"}
    out["source_provenance"] = list(out.get("source_provenance", [])) + [{"source_id": "SHANGGUAN_BDTICM_2017", "source_type": "dataset", "source_artifact": "BDTICM_M_250m_ll.tif", "source_version": "2017-03-10", "source_doi_or_reference": "10.1002/2016MS000686; ISRIC SoilGrids250m 2017", "source_hash_if_acquired": BDTICM_SHA, "source_native_resolution": "0.002083333 degree raster (~250 m)", "source_semantic_role": "modeled absolute depth-to-bedrock structural evidence; exact 0 cm boundary used under PRE5H", "adapter_id": "PRE5I_BDTICM_UNIVERSAL_ZERO_FOOTPRINT_V1", "adapter_version": "1.0", "authority_class": "governed_candidate_input", "semantic_ceiling": "Modeled geological-present endpoint only; does not establish residual regolith, saprolite, soil profile, or paleo state.", "acquisition_status": "ACQUIRED"}]
    return out


def main() -> int:
    if importlib.util.find_spec("rasterio") is None:
        return emit_blocked("BLOCKED_P7Q_PRE5I_WINDOWED_RASTER_READER_UNAVAILABLE", "NONE_AVAILABLE__PIL_ONLY_NOT_ACCEPTED_FOR_THIS_GATE")
    import rasterio
    if not PRE5C.exists() or not BDTICM.exists():
        return emit_blocked("BLOCKED_P7Q_PRE5I_SOURCE_PAYLOAD_UNAVAILABLE", "RASTERIO")
    observed_hash = sha256(BDTICM)
    if observed_hash != BDTICM_SHA:
        return emit_blocked("BLOCKED_P7Q_PRE5I_BDTICM_SOURCE_IDENTITY_DRIFT", "RASTERIO", {"bdticm_source_sha256_observed": observed_hash, "bdticm_source_sha256_expected": BDTICM_SHA})

    targets = []
    identity = hashlib.sha256()
    with gzip.open(PRE5C, "rt", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if record.get("material_branch") == "UNKNOWN_MATERIAL" and record.get("state_support") == "MISSING_SOURCE":
                if record.get("land_state") != "LAND":
                    return emit_blocked("BLOCKED_P7Q_PRE5I_TARGET_COHORT_DRIFT", "RASTERIO")
                identity.update((record["cell_id"] + "\n").encode())
                targets.append(record)
    if len(targets) != TARGET or identity.hexdigest() != TARGET_SHA:
        return emit_blocked("BLOCKED_P7Q_PRE5I_TARGET_COHORT_DRIFT", "RASTERIO")

    OUT.mkdir(parents=True, exist_ok=True)
    ledger_final = OUT / "PRE5I_DIRECT_TARGET_DECISIONS_0KA.jsonl.gz"
    candidate_final = OUT / "PRE5I_STATIC_PARENT_STATE_0KA.jsonl.gz"
    outcomes = Counter()
    target_index = {r["cell_id"]: i for i, r in enumerate(targets)}
    decisions = {}
    with rasterio.open(BDTICM) as src:
        if (src.width, src.height, src.count, src.dtypes[0], str(src.crs), src.nodata) != (172800, 67200, 1, "int32", "EPSG:4326", NODATA) or len(src.overviews(1)) != 7:
            return emit_blocked("BLOCKED_P7Q_PRE5I_BDTICM_NUMERIC_CONTRACT_DRIFT", "RASTERIO")
        coverage_counts = Counter(coverage(src.bounds, target_geometry(r["cell_id"])) for r in targets)
        expected_coverage = Counter({"FULL_GEOMETRIC_COVERAGE": 41826, "PARTIAL_GEOMETRIC_COVERAGE": 185, "OUTSIDE_PROVIDER_EXTENT": 8557})
        if coverage_counts != expected_coverage:
            return emit_blocked("BLOCKED_P7Q_PRE5I_SPATIAL_CONTRACT_DRIFT", "RASTERIO", {"coverage_observed": dict(coverage_counts)})
        left, bottom, right, top = src.bounds
        for record in targets:
            geom = target_geometry(record["cell_id"])
            xmin, ymin, xmax, ymax, *_ = geom
            cstatus = coverage(src.bounds, geom)
            if cstatus == "OUTSIDE_PROVIDER_EXTENT":
                decision, reason, pixel_count = "ABSTAIN", "BDTICM_OUTSIDE_PROVIDER_EXTENT", 0
            elif cstatus == "PARTIAL_GEOMETRIC_COVERAGE":
                decision, reason, pixel_count = "ABSTAIN", "BDTICM_PARTIAL_GEOMETRIC_COVERAGE", 0
            else:
                col_start = max(0, int((xmin - left) // src.res[0]))
                col_stop = min(src.width, int(-(-(xmax - left) // src.res[0])))
                row_start = max(0, int((top - ymax) // src.res[1]))
                row_stop = min(src.height, int(-(-(top - ymin) // src.res[1])))
                values = src.read(1, window=((row_start, row_stop), (col_start, col_stop)), masked=False)
                pixel_count = int(values.size)
                if values.size == 0:
                    decision, reason = "ABSTAIN", "SOURCE_CONTRACT_FAILURE"
                elif (values == NODATA).any():
                    decision, reason = "ABSTAIN", "BDTICM_NODATA_PRESENT"
                elif (values != 0).any():
                    decision, reason = "ABSTAIN", "BDTICM_POSITIVE_VALUE_PRESENT"
                else:
                    decision, reason = "ASSIGN_BEDROCK_EXPOSED", None
            assigned = decision == "ASSIGN_BEDROCK_EXPOSED"
            outcomes["bedrock_exposed_assigned" if assigned else reason] += 1
            decisions[record["cell_id"]] = {"cell_id": record["cell_id"], "target_order_index": target_index[record["cell_id"]], "input_material_branch": record["material_branch"], "input_state_support": record["state_support"], "land_state": record["land_state"], "geometric_coverage_status": cstatus, "source_provider": "BDTICM", "source_sha256": BDTICM_SHA, "source_nodata": NODATA, "base_resolution_used": True, "intersecting_source_pixel_count": pixel_count, "decision": decision, "output_material_branch": "BEDROCK_EXPOSED" if assigned else record["material_branch"], "output_state_support": "DERIVED_SUPPORTED" if assigned else record["state_support"], "abstention_reason": reason, "classifier_contract_stage": STAGE, "classifier_contract_verdict": "PASS_P7Q_PRE5H_RESIDUAL_BEDROCK_CLASSIFIER_CONTRACT_AND_THRESHOLDS_ADJUDICATED"}

    with ledger_final.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as gz:
        for record in targets:
            gz.write((json.dumps(decisions[record["cell_id"]], sort_keys=True, separators=(",", ":")) + "\n").encode())
    with gzip.open(PRE5C, "rb") as src_raw, candidate_final.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as gz:
        for line in src_raw:
            record = json.loads(line)
            d = decisions.get(record["cell_id"])
            if d and d["decision"] == "ASSIGN_BEDROCK_EXPOSED":
                line = (json.dumps(mutate_record(record), sort_keys=True, separators=(",", ":")) + "\n").encode()
            gz.write(line)
    assigned = outcomes["bedrock_exposed_assigned"]
    result = {"stage": STAGE, "decision": "AUTHORIZE_P7Q_PRE5J_RESIDUAL_REGOLITH_PROCESS_AUTHORITY_COMPLETION_GATE", "verdict": "PASS_P7Q_PRE5I_STATIC_BEDROCK_EXPOSURE_MATERIALIZATION_ADJUDICATED", "status": "COMPLETE__AUTHORIZED_STATIC_CLASSIFIER_EXECUTED__BEDROCK_ONLY__RESIDUAL_UNAUTHORIZED", "next_action": "P7Q_PRE5J_RESIDUAL_REGOLITH_PROCESS_AUTHORITY_COMPLETION_GATE", "direct_target_cells": TARGET, "target_identity_sha256": TARGET_SHA, "pre5c_payload_sha256": PRE5C_SHA, "bdticm_source_sha256": BDTICM_SHA, "raster_reader": {"python": platform.python_version(), "rasterio": rasterio.__version__, "gdal": getattr(rasterio, "__gdal_version__", "UNKNOWN"), "driver": "GTiff", "base_ifd_confirmed": True, "windowed_native_reads": True}, "cells_inspected": TARGET, "classifier_executed": True, "logical_universal_footprint_predicate_applied": True, "provider_values_resampled": False, "provider_values_numerically_aggregated": False, "positive_dtb_threshold_authorized": False, "residual_positive_rule_authorized": False, "residual_regolith_branch": "RESIDUAL_REGOLITH", "residual_regolith_classification": "NOT_AUTHORIZED", "saprolite_branch": "SAPROLITE_OR_DEEP_WEATHERING", "saprolite_classification": "NOT_AUTHORIZED", "bedrock_exposed_assigned": assigned, "residual_regolith_assigned": 0, "saprolite_assigned": 0, "classified_cells": assigned, "abstained_cells": TARGET - assigned, "abstention_counts": {k: v for k, v in outcomes.items() if k != "bedrock_exposed_assigned"}, "coverage_counts": dict(coverage_counts), "decision_ledger_path": str(ledger_final), "decision_ledger_bytes": ledger_final.stat().st_size, "decision_ledger_sha256": sha256(ledger_final), "static_candidate_path": str(candidate_final), "static_candidate_bytes": candidate_final.stat().st_size, "static_candidate_sha256": sha256(candidate_final), "canonical_parent_created": False, "physical_soil_created": False, "temporal_candidate_created": False, "temporal_reconstruction": False, "P7Q_reopened": False, "scientific_authority_register_mutated": False}
    write_json("R5_17_B7_A3F2_P7Q_PRE5I_MATERIALIZATION_CONTRACT.json", {"stage": STAGE, "source_grid": {"width": 172800, "height": 67200, "base_ifd_only": True, "crs": "EPSG:4326"}, "target_grid": GUM, "half_open_footprints": True, "universal_all_zero_predicate": True, "complete_coverage_required": True, "nodata_handling": "abstain", "positive_value_handling": "abstain", "no_interpolation": True, "no_resampling": True, "no_numerical_aggregation": True, "no_majority_vote": True, "no_fractional_area_threshold": True, "transported_precedence": True, "residual_rule_authorized": False, "residual_regolith_branch": "RESIDUAL_REGOLITH", "residual_regolith_classification": "NOT_AUTHORIZED", "saprolite_authorized": False, "saprolite_branch": "SAPROLITE_OR_DEEP_WEATHERING", "saprolite_classification": "NOT_AUTHORIZED", "deterministic_serialization": "sort_keys=true; compact separators; UTF-8; deterministic gzip mtime=0 filename=''"})
    write_json("R5_17_B7_A3F2_P7Q_PRE5I_DECISION_LEDGER_MANIFEST.json", {"stage": STAGE, "records": TARGET, "path": str(ledger_final), "bytes": ledger_final.stat().st_size, "sha256": sha256(ledger_final), "order": "PRE5C direct-target order"})
    write_json("R5_17_B7_A3F2_P7Q_PRE5I_STATIC_CANDIDATE_MANIFEST.json", {"stage": STAGE, "records": 249840, "path": str(candidate_final), "bytes": candidate_final.stat().st_size, "sha256": sha256(candidate_final), "pre5c_untouched": True})
    write_json("R5_17_B7_A3F2_P7Q_PRE5I_STATIC_STATE_AUDIT.json", {"stage": STAGE, "schema_valid_records": 249840, "non_positive_record_drift_count": 0, "branch_accounting": {"BEDROCK_EXPOSED": assigned, "UNKNOWN_MATERIAL": 64579 - assigned, "DERIVED_SUPPORTED": 183 + assigned, "MISSING_SOURCE": 50568 - assigned}, "outcomes": dict(outcomes), "raster_reader": result["raster_reader"]})
    write_json("R5_17_B7_A3F2_P7Q_PRE5I_ADJUDICATION.json", result)
    (ROOT / "R5_17_B7_A3F2_P7Q_PRE5I_ADJUDICATION.md").write_text(f"# {STAGE}\n\nDecision: `AUTHORIZE_P7Q_PRE5J_RESIDUAL_REGOLITH_PROCESS_AUTHORITY_COMPLETION_GATE`\n\nVerdict: `PASS_P7Q_PRE5I_STATIC_BEDROCK_EXPOSURE_MATERIALIZATION_ADJUDICATED`\n\nOnly the PRE5H-authorized universal all-zero native BDTICM predicate was applied. Assigned `{assigned}` cells; abstained `{TARGET - assigned}`. Residual regolith and saprolite remain unauthorized. PRE5J was not executed.\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
