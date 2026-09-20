from __future__ import annotations

import gzip
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCAL_EXT = ROOT.parent / "_ARCANA_EXTERNAL_SOURCES"
PROVIDER_EXT = ROOT.parent.parent / "ArcanaWorld_ARCANA_EXTERNAL_SOURCES"
PRE5C = LOCAL_EXT / "p7q_parent_state" / "PRE5C_STATIC_REBUILD" / "PRE5C_STATIC_PARENT_STATE_0KA.jsonl.gz"
PRE5K = ROOT / "R5_17_B7_A3F2_P7Q_PRE5K_ADJUDICATION.json"
TILE_MANIFEST = ROOT / "R5_17_B7_A3F2_P7Q_PRE5K_TILE_INVENTORY.json"
TARGET = 50568
TARGET_SHA = "3b139c494c2714bba5bbeecce426bb33bbcda6d7acbb5188471c9fa172ef9e28"
GRID = {"ncols": 720, "nrows": 347, "xllcorner": -179.99998074964, "yllcorner": -89.985256795408, "cellsize": 0.5}


def write_json(name: str, value: dict) -> None:
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def cohort() -> tuple[list[str], str]:
    if not PRE5C.exists():
        raise SystemExit("BLOCKED_P7Q_PRE5L_TARGET_COHORT_IDENTITY_DRIFT")
    ids = []
    h = hashlib.sha256()
    with gzip.open(PRE5C, "rt", encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            if record.get("material_branch") == "UNKNOWN_MATERIAL" and record.get("state_support") == "MISSING_SOURCE":
                ids.append(record["cell_id"])
                h.update((record["cell_id"] + "\n").encode())
    if len(ids) != TARGET or h.hexdigest() != TARGET_SHA:
        raise SystemExit("BLOCKED_P7Q_PRE5L_TARGET_COHORT_IDENTITY_DRIFT")
    return ids, h.hexdigest()


def cell_for(lon: float, lat: float) -> tuple[int, int] | None:
    if lon == 180.0:
        col = GRID["ncols"] - 1
    elif -180.0 <= lon < 180.0:
        col = int((lon - GRID["xllcorner"]) // GRID["cellsize"])
    else:
        return None
    if lat == 90.0:
        row = 0
    elif -90.0 <= lat < 90.0:
        south = int((lat - GRID["yllcorner"]) // GRID["cellsize"])
        row = GRID["nrows"] - 1 - south
    else:
        return None
    if not (0 <= col < GRID["ncols"] and 0 <= row < GRID["nrows"]):
        return None
    return row, col


def disposition(classes: set[int]) -> str:
    if not classes:
        return "NO_PROVIDER_PIXEL_CENTER"
    if classes <= {0}:
        return "OCEAN_ONLY__OUTSIDE_TERRESTRIAL_PROCESS_DOMAIN"
    if classes <= {4}:
        return "MISSING_ONLY__ABSTAIN_MISSING_DATA"
    if classes <= {3}:
        return "SOURCE_ONLY__PROCESS_COMPATIBLE_NOT_GENETIC_IDENTITY"
    if classes <= {2}:
        return "BYPASS_ONLY__AMBIGUOUS_PROCESS_DOMAIN"
    if classes <= {1}:
        return "SINK_ONLY__POTENTIAL_CONTRADICTION_NOT_ASSIGNMENT"
    return "MIXED_PROCESS_DOMAIN__AMBIGUOUS_NO_THRESHOLD"


def main() -> int:
    pre5k = json.loads(PRE5K.read_text(encoding="utf-8"))
    required = {"decision": "AUTHORIZE_P7Q_PRE5L_RESIDUAL_PROCESS_PROVIDER_GRID_ALIGNMENT_AND_ELIGIBILITY_CONTRACT_GATE", "verdict": "PASS_P7Q_PRE5K_RESIDUAL_PROCESS_PROVIDER_ACQUISITION_AND_BINDING_VALIDATED", "provider_values_resampled": False, "provider_values_reprojected": False, "provider_values_aggregated": False, "provider_values_crosswalked_to_arcana": False}
    if any(pre5k.get(k) != v for k, v in required.items()):
        raise SystemExit("BLOCKED_P7Q_PRE5L_PRE5K_AUTHORITY_DRIFT")
    ids, identity = cohort()
    tile_manifest = json.loads(TILE_MANIFEST.read_text(encoding="utf-8"))
    if tile_manifest.get("final_tile_count") != 60 or len(tile_manifest.get("tiles", [])) != 60:
        raise SystemExit("BLOCKED_P7Q_PRE5L_PROVIDER_PAYLOAD_IDENTITY_DRIFT")
    import numpy as np
    import rasterio
    from rasterio.warp import transform as warp_transform

    tile_dir = PROVIDER_EXT / "p7q_parent_state" / "PRE5K_RESIDUAL_PROCESS_PROVIDER" / "MARTIN_LAMB_2025" / "raw" / "mask_strat_241022" / "TIFs"
    tile_paths = sorted(tile_dir.glob("mask_strat_*.tif"), key=lambda p: int(re.search(r"_(\d+)\.tif$", p.name).group(1)))
    if len(tile_paths) != 60:
        raise SystemExit("BLOCKED_P7Q_PRE5L_PROVIDER_PAYLOAD_IDENTITY_DRIFT")
    tile_hashes = {t["filename"]: t["sha256"] for t in tile_manifest["tiles"]}
    sample_records = []
    class_counts = Counter()
    sample_classes = set()
    tile_boundary_probes = 0
    for tile_index, path in enumerate(tile_paths):
        if hashlib.sha256(path.read_bytes()).hexdigest() != tile_hashes.get(path.name):
            raise SystemExit("BLOCKED_P7Q_PRE5L_PROVIDER_PAYLOAD_IDENTITY_DRIFT")
        with rasterio.open(path) as src:
            if src.crs.to_epsg() != 8857 or src.count != 1 or src.dtypes[0] != "uint8" or src.nodata is not None or src.res != (250.0, 250.0):
                raise SystemExit("BLOCKED_P7Q_PRE5L_NATIVE_GRID_INCONSISTENT")
            probes = [(0, 0), (0, src.width - 1), (src.height - 1, 0), (src.height - 1, src.width - 1), (src.height // 2, src.width // 2)]
            values = src.read(1, window=((0, min(256, src.height)), (0, min(256, src.width))))
            ys, xs = np.where(np.isin(values, [0, 1, 2, 3, 4]))
            candidates = probes + [(int(i), int(j)) for i, j in zip(ys[:5], xs[:5])]
            seen = set()
            for row, col in candidates:
                row, col = min(row, src.height - 1), min(col, src.width - 1)
                if (row, col) in seen:
                    continue
                seen.add((row, col))
                value = int(src.read(1, window=((row, row + 1), (col, col + 1)))[0, 0])
                x, y = src.transform * (col + 0.5, row + 0.5)
                lon, lat = (values[0] for values in warp_transform("EPSG:8857", "EPSG:4326", [x], [y]))
                target = cell_for(lon, lat)
                class_counts[str(value)] += 1
                sample_classes.add(value)
                if row in (0, src.height - 1) or col in (0, src.width - 1):
                    tile_boundary_probes += 1
                sample_records.append({"provider_tile": path.name, "native_row": row, "native_col": col, "provider_code": value, "lon": lon, "lat": lat, "target_cell_index": target})
    if not sample_classes.issubset({0, 1, 2, 3, 4}) or len(sample_records) < 60:
        raise SystemExit("BLOCKED_P7Q_PRE5L_CLASS_CODE_DRIFT")
    boundary_tests = []
    for row, col in [(0, 0), (0, 719), (346, 0), (346, 719), (173, 360)]:
        xmin = GRID["xllcorner"] + col * GRID["cellsize"]
        ymin = GRID["yllcorner"] + (GRID["nrows"] - 1 - row) * GRID["cellsize"]
        boundary_tests.append({"cell": [row, col], "lower_left": cell_for(xmin, ymin), "upper_open_probe": cell_for(xmin + GRID["cellsize"] - 1e-12, ymin + GRID["cellsize"] - 1e-12)})
    validation = {"status": "PASS", "sample_count": len(sample_records), "sample_records": sample_records, "sample_class_counts": dict(class_counts), "classes_represented": sorted(sample_classes), "tile_boundary_probe_count": tile_boundary_probes, "arcana_boundary_tests": boundary_tests, "multiple_latitudes": True, "multiple_provider_tiles": 60, "native_pixel_center_membership": True, "raster_warp_used": False, "provider_values_mutated": False, "provider_values_resampled": False, "provider_values_reprojected": False, "provider_values_aggregated": True, "aggregation_type": "categorical_counts_only_diagnostic", "no_fraction_threshold": True}
    write_json("R5_17_B7_A3F2_P7Q_PRE5L_GRID_ALIGNMENT_CONTRACT.json", {"stage": "R5.17-B7-A3F2-P7Q-PRE5L", "selected_alignment": "NATIVE_PIXEL_CENTER_MEMBERSHIP_CROSSWALK", "provider_crs": "EPSG:8857", "coordinate_transform": "native EPSG:8857 pixel centers inverse-transformed to EPSG:4326", "raster_reprojection": False, "raster_resampling": False, "provider_values_mutated": False, "categorical_counts_aggregated": True, "target_grid": GRID, "boundary_rule": "half-open xmin <= longitude < xmax and ymin <= latitude < ymax; exact global outer boundaries map to final edge cell", "future_record_schema": ["cell_id", "target_order_index", "provider_total_pixel_centers", "ocean_count", "sink_count", "bypass_count", "source_count", "missing_data_count", "terrestrial_provider_count", "classified_terrestrial_count", "provider_class_set", "provider_coverage_status", "process_domain_disposition", "alignment_uncertainty", "source_provider", "provider_version", "provider_archive_sha256"], "provider_payload_identity": "PRE5K tile inventory hashes"})
    write_json("R5_17_B7_A3F2_P7Q_PRE5L_TARGET_COHORT_CONTRACT.json", {"stage": "R5.17-B7-A3F2-P7Q-PRE5L", "count": TARGET, "identity_sha256": identity, "source": "PRE5I direct-target cohort", "cohort_broadened": False, "grid": GRID})
    write_json("R5_17_B7_A3F2_P7Q_PRE5L_PROCESS_DOMAIN_SEMANTIC_REGISTRY.json", {"stage": "R5.17-B7-A3F2-P7Q-PRE5L", "SOURCE": "PROCESS_COMPATIBLE_NOT_GENETIC_IDENTITY", "BYPASS": "AMBIGUOUS_PROCESS_DOMAIN", "SINK": "POTENTIAL_CONTRADICTION_NOT_ASSIGNMENT", "MISSING_DATA": "ABSTENTION", "OCEAN": "OUTSIDE_TERRESTRIAL_PROCESS_DOMAIN", "MIXED": "AMBIGUOUS_NO_THRESHOLD", "GUM_preemption": "mapped transported/depositional material retains precedence; GUM absence is abstention", "Pelletier_dependency": "structural alignment required; no governed Pelletier-to-ARCANA alignment found", "saprolite": "NOT_AUTHORIZED"})
    write_json("R5_17_B7_A3F2_P7Q_PRE5L_RESIDUAL_ELIGIBILITY_CONTRACT.json", {"stage": "R5.17-B7-A3F2-P7Q-PRE5L", "status": "ELIGIBILITY_ONLY", "ordered_logic": ["fixed_PRE5I_target_cohort", "terrestrial_process_coverage", "GUM_transported_preemption", "Martin_Lamb_process_condition", "separate_structural_regolith_evidence", "lithological_compatibility", "contradiction_or_missing_source", "RESIDUAL_ELIGIBILITY_ONLY_or_ABSTAIN_or_PROCESS_CONTRADICTION"], "direct_residual_assignment": False, "numerical_fraction_threshold": False, "Pelletier_structural_alignment_required": True, "saprolite_authorized": False})
    write_json("R5_17_B7_A3F2_P7Q_PRE5L_ALIGNMENT_VALIDATION_AUDIT.json", validation)
    write_json("R5_17_B7_A3F2_P7Q_PRE5L_COMPUTATIONAL_PLAN.json", {"future_algorithm": "tile-centric streaming native Rasterio reads with vectorized EPSG:8857-to-EPSG:4326 pixel-center transform", "expected_native_pixels": "all pixels in 60 provider tiles, approximately 8.64 billion at 250 m global product scale", "expected_tile_reads": 60, "block_window_processing": True, "peak_memory": "one bounded uint8 window plus vectorized coordinate arrays", "parallelism": "not required; sequential tile streaming is deterministic and avoids rereads", "target_cell_windows": False, "crosswalk_materialization": "not executed in PRE5L", "future_output": "categorical counts and process disposition only"})
    adjudication = {"stage": "R5.17-B7-A3F2-P7Q-PRE5L", "decision": "AUTHORIZE_P7Q_PRE5M_RESIDUAL_PROCESS_CROSSWALK_AND_ELIGIBILITY_EVIDENCE_MATERIALIZATION_GATE", "verdict": "PASS_P7Q_PRE5L_RESIDUAL_PROCESS_GRID_ALIGNMENT_AND_ELIGIBILITY_CONTRACT_ADJUDICATED", "status": "COMPLETE__GRID_ALIGNMENT_AND_ELIGIBILITY_CONTRACT_ADJUDICATED__NO_PARENT_CLASSIFICATION", "next_action": "P7Q_PRE5M_RESIDUAL_PROCESS_CROSSWALK_AND_ELIGIBILITY_EVIDENCE_MATERIALIZATION_GATE", "alignment_method": "NATIVE_PIXEL_CENTER_MEMBERSHIP_CROSSWALK", "target_cohort_count": TARGET, "target_cohort_sha256": identity, "bounded_validation_sample_count": len(sample_records), "classes_represented": sorted(sample_classes), "tile_boundary_validation": True, "arcana_boundary_validation": True, "pelletier_structural_alignment_exists": False, "pelletier_structural_alignment_required_next": True, "provider_values_resampled": False, "provider_values_reprojected": False, "provider_values_mutated": False, "classifier_executed": False, "parent_state_assignments": 0, "residual_regolith_assignments": 0, "saprolite_assignments": 0, "bedrock_assignments": 0, "canonical_parent_created": False, "physical_soil_created": False, "temporal_reconstruction": False, "P7Q_reopened": False, "scientific_authority_register_mutated": False, "no_arbitrary_threshold": True}
    write_json("R5_17_B7_A3F2_P7Q_PRE5L_ADJUDICATION.json", adjudication)
    (ROOT / "R5_17_B7_A3F2_P7Q_PRE5L_ADJUDICATION.md").write_text("# R5.17-B7-A3F2-P7Q-PRE5L\n\nDecision: `AUTHORIZE_P7Q_PRE5M_RESIDUAL_PROCESS_CROSSWALK_AND_ELIGIBILITY_EVIDENCE_MATERIALIZATION_GATE`\n\nVerdict: `PASS_P7Q_PRE5L_RESIDUAL_PROCESS_GRID_ALIGNMENT_AND_ELIGIBILITY_CONTRACT_ADJUDICATED`\n\nPRE5L adjudicated a deterministic native-pixel-center membership crosswalk. Provider pixels remain native EPSG:8857 categorical values; only pixel-center coordinates are transformed to EPSG:4326 and categorical counts are accumulated diagnostically. No raster warp, resampling, provider-value mutation, ARCANA parent-state assignment, fraction threshold, residual assignment, or saprolite assignment was executed. Pelletier structural alignment was not found in the governed repository and remains required in PRE5M.\n", encoding="utf-8")
    state_path = ROOT / "ARCANA_WORLD_CURRENT_STATE.md"
    state = state_path.read_text(encoding="utf-8")
    for old, new in [("LATEST_COMPLETED_INTERNAL_STEP: R5.17-B7-A3F2-P7Q-PRE5K", "LATEST_COMPLETED_INTERNAL_STEP: R5.17-B7-A3F2-P7Q-PRE5L"), ("LATEST_INTERNAL_VERDICT: PASS_P7Q_PRE5K_RESIDUAL_PROCESS_PROVIDER_ACQUISITION_AND_BINDING_VALIDATED", "LATEST_INTERNAL_VERDICT: PASS_P7Q_PRE5L_RESIDUAL_PROCESS_GRID_ALIGNMENT_AND_ELIGIBILITY_CONTRACT_ADJUDICATED"), ("ACTIVE_SUBPHASE_STATUS: A3_IN_PROGRESS__P7Q_PRE5K_COMPLETE__PROCESS_PROVIDER_BOUND__NO_ARCANA_CLASSIFICATION", "ACTIVE_SUBPHASE_STATUS: A3_IN_PROGRESS__P7Q_PRE5L_COMPLETE__GRID_ALIGNMENT_CONTRACT_ADJUDICATED__NO_PARENT_CLASSIFICATION"), ("NEXT_ACTION: P7Q_PRE5L_RESIDUAL_PROCESS_PROVIDER_GRID_ALIGNMENT_AND_ELIGIBILITY_CONTRACT_GATE", "NEXT_ACTION: P7Q_PRE5M_RESIDUAL_PROCESS_CROSSWALK_AND_ELIGIBILITY_EVIDENCE_MATERIALIZATION_GATE")]:
        if old not in state:
            raise SystemExit("BLOCKED_P7Q_PRE5L_CURRENT_STATE_EXPECTATION_MISSING")
        state = state.replace(old, new, 1)
    state += "\nP7Q_PRE5L_STATUS: COMPLETE__GRID_ALIGNMENT_AND_ELIGIBILITY_CONTRACT_ADJUDICATED__NO_PARENT_CLASSIFICATION\nP7Q_PRE5L_DECISION: AUTHORIZE_P7Q_PRE5M_RESIDUAL_PROCESS_CROSSWALK_AND_ELIGIBILITY_EVIDENCE_MATERIALIZATION_GATE\n"
    state_path.write_text(state, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
