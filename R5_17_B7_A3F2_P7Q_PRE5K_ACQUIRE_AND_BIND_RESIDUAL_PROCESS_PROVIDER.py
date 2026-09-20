from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXT = ROOT.parent.parent / "ArcanaWorld_ARCANA_EXTERNAL_SOURCES" / "p7q_parent_state" / "PRE5K_RESIDUAL_PROCESS_PROVIDER" / "MARTIN_LAMB_2025"
META = EXT / "metadata" / "figshare_article_28432280_v1.json"
ZIP = EXT / "raw" / "mask_strat_241022.zip"
TILES = EXT / "raw" / "mask_strat_241022" / "TIFs"
PRE5J = ROOT / "R5_17_B7_A3F2_P7Q_PRE5J_ADJUDICATION.json"


def digest(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(name: str, value: dict) -> None:
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    if not PRE5J.exists():
        raise SystemExit("BLOCKED_P7Q_PRE5K_PRE5J_AUTHORITY_DRIFT")
    pre5j = json.loads(PRE5J.read_text(encoding="utf-8"))
    required = {
        "decision": "AUTHORIZE_P7Q_PRE5K_RESIDUAL_PROCESS_PROVIDER_ACQUISITION_AND_BINDING_GATE",
        "verdict": "PASS_P7Q_PRE5J_RESIDUAL_PROCESS_AUTHORITY_COMPLETION_ADJUDICATED",
        "status": "COMPLETE__RESIDUAL_PROCESS_AUTHORITY_FEASIBLE__CLASSIFICATION_NOT_EXECUTED",
    }
    if any(pre5j.get(k) != v for k, v in required.items()) or pre5j.get("P7Q_reopened") is not False:
        raise SystemExit("BLOCKED_P7Q_PRE5K_PRE5J_AUTHORITY_DRIFT")
    if not META.exists() or not ZIP.exists() or not TILES.exists():
        raise SystemExit("BLOCKED_P7Q_PRE5K_FIGSHARE_METADATA_OR_PAYLOAD_UNAVAILABLE")
    metadata = json.loads(META.read_text(encoding="utf-8"))
    if metadata["id"] != 28432280 or metadata["version"] != 1 or metadata["doi"] != "10.6084/m9.figshare.28432280.v1":
        raise SystemExit("BLOCKED_P7Q_PRE5K_PROVIDER_VERSION_UNRESOLVED")
    if metadata["license"]["name"] != "CC BY 4.0":
        raise SystemExit("BLOCKED_P7Q_PRE5K_PROVIDER_LICENSE_UNRESOLVED")
    final_file = next((f for f in metadata["files"] if f["id"] == 52426700), None)
    if not final_file or final_file["name"] != "mask_strat_241022.zip":
        raise SystemExit("BLOCKED_P7Q_PRE5K_FINAL_PRODUCT_IDENTITY_UNRESOLVED")
    if ZIP.stat().st_size != final_file["size"] or digest(ZIP, "md5") != final_file["supplied_md5"]:
        raise SystemExit("BLOCKED_P7Q_PRE5K_PROVIDER_CHECKSUM_MISMATCH")
    import rasterio
    import numpy as np
    files = sorted(TILES.glob("mask_strat_*.tif"), key=lambda p: int(re.search(r"_(\d+)\.tif$", p.name).group(1)))
    if len(files) != 60 or {int(re.search(r"_(\d+)\.tif$", p.name).group(1)) for p in files} != set(range(60)):
        raise SystemExit("BLOCKED_P7Q_PRE5K_TILE_TOPOLOGY_INCONSISTENT")
    inventory = []
    crs_wkt = None
    bounds = []
    observed = set()
    signatures = set()
    for path in files:
        with rasterio.open(path) as src:
            if src.crs is None or src.crs.to_epsg() != 8857 or src.driver != "GTiff" or src.count != 1 or src.dtypes[0] != "uint8" or src.nodata is not None or src.res != (250.0, 250.0) or src.compression.value != "PACKBITS":
                raise SystemExit("BLOCKED_P7Q_PRE5K_RASTER_METADATA_UNREADABLE")
            crs_wkt = crs_wkt or src.crs.to_wkt()
            if src.crs.to_wkt() != crs_wkt:
                raise SystemExit("BLOCKED_P7Q_PRE5K_CRS_INCONSISTENT")
            signatures.add((src.width, src.height, src.count, src.dtypes[0], src.nodata, src.res, src.compression.value))
            tile_values = set()
            for row in range(0, src.height, 1024):
                tile_values.update(int(v) for v in np.unique(src.read(1, window=((row, min(row + 1024, src.height)), (0, src.width)))))
            if not tile_values <= {0, 1, 2, 3, 4}:
                raise SystemExit("BLOCKED_P7Q_PRE5K_CLASS_ENCODING_UNRESOLVED")
            observed.update(tile_values)
            bounds.append(tuple(src.bounds))
            inventory.append({"provider_file_id": final_file["id"], "filename": path.name, "role": "FINAL_CLASSIFICATION_TILE", "bytes": path.stat().st_size, "sha256": digest(path), "width": src.width, "height": src.height, "crs_authority": "EPSG:8857", "crs_wkt": crs_wkt, "transform": list(src.transform), "bounds": list(src.bounds), "nodata": None, "dtype": "uint8", "band_count": 1, "overviews": len(src.overviews(1)), "compression": "PACKBITS", "class_values_observed": sorted(tile_values)})
    structural_signatures = {(dtype, nodata, res, compression) for _, _, _, dtype, nodata, res, compression in signatures}
    if len(structural_signatures) != 1 or not observed <= {0, 1, 2, 3, 4}:
        raise SystemExit("BLOCKED_P7Q_PRE5K_TILE_TOPOLOGY_INCONSISTENT")
    total_bytes = sum(x["bytes"] for x in inventory)
    manifest = {"provider_id": "MARTIN_LAMB_2025", "dataset_name": metadata["title"], "authors": metadata["authors"], "paper_doi": "10.1130/G53289.1", "base_dataset_doi": "10.6084/m9.figshare.28432280", "version_doi": metadata["doi"], "figshare_article_id": metadata["id"], "version": metadata["version"], "license": metadata["license"], "official_metadata_endpoint": metadata["url_public_api"], "official_download_source": final_file["download_url"], "acquisition_status": "ACQUIRED_VALIDATED", "file_inventory": inventory, "archive": {"filename": ZIP.name, "bytes": ZIP.stat().st_size, "sha256": digest(ZIP), "md5": digest(ZIP, "md5"), "provider_md5": final_file["supplied_md5"]}, "total_acquired_bytes": total_bytes, "external_cache_root": str(EXT)}
    binding = {"provider_id": "MARTIN_LAMB_2025", "format": "GeoTIFF tiles", "crs_authority": "EPSG:8857", "crs_wkt": crs_wkt, "projection": "WGS 84 / Equal Earth Greenwich", "resolution_m": [250.0, 250.0], "extent_projected": [min(b[0] for b in bounds), min(b[1] for b in bounds), max(b[2] for b in bounds), max(b[3] for b in bounds)], "tile_topology": {"count": 60, "naming": "mask_strat_0.tif through mask_strat_59.tif", "overlap": "not observed in native bounds", "gaps": "none in provider tile inventory", "antarctica": "not mapped by source method", "ocean_code": 0, "unclassified_land_code": 4}, "nodata": None, "dtype": "uint8", "band_count": 1, "class_encoding": {"0": "OCEAN", "1": "SINK", "2": "BYPASS", "3": "SOURCE", "4": "MISSING_DATA"}, "temporal_semantics": "LONG_TIMESCALE_MODERN_PRESENT_GEOMORPHIC_PROCESS_DOMAIN", "semantic_role": "LONG_TIMESCALE_SEDIMENT_PROCESS_DOMAIN_CONDITIONER", "semantic_ceiling": "Provider source/bypass/sink semantics only; no residual, saprolite, bedrock or genetic parent-material identity.", "dependency_class": "METHOD_INPUT_DEPENDENCY_ON_PELLETIER_2016", "provider_values_resampled": False, "provider_values_reprojected": False, "provider_values_aggregated": False, "provider_values_crosswalked_to_arcana": False}
    write_json("R5_17_B7_A3F2_P7Q_PRE5K_SOURCE_ACQUISITION_MANIFEST.json", manifest)
    write_json("R5_17_B7_A3F2_P7Q_PRE5K_PROVIDER_BINDING.json", binding)
    write_json("R5_17_B7_A3F2_P7Q_PRE5K_TILE_INVENTORY.json", {"provider_id": "MARTIN_LAMB_2025", "final_tile_count": 60, "tiles": inventory})
    write_json("R5_17_B7_A3F2_P7Q_PRE5K_CLASS_ENCODING_CONTRACT.json", {"provider_id": "MARTIN_LAMB_2025", "codes": {"0": "OCEAN", "1": "SINK", "2": "BYPASS", "3": "SOURCE", "4": "MISSING_DATA"}, "metadata_source": "Figshare article 28432280 v1 description", "no_color_inference": True, "no_arcana_crosswalk": True})
    write_json("R5_17_B7_A3F2_P7Q_PRE5K_DEPENDENCY_BINDING.json", {"provider_id": "MARTIN_LAMB_2025", "dependencies": [{"provider": "PELLETIER_2016", "dependency_type": "METHOD_INPUT_DEPENDENCY", "role": "upland/lowland land-domain construction"}, {"provider": "GUM_2018", "dependency_type": "METHOD_INPUT_DEPENDENCY", "role": "glacial/unconsolidated sediment conditioning"}], "independent_vote_counting": False})
    write_json("R5_17_B7_A3F2_P7Q_PRE5K_PROVIDER_VALIDATION_AUDIT.json", {"provider_id": "MARTIN_LAMB_2025", "status": "PASS", "final_tiles": 60, "same_crs": True, "same_dtype": True, "same_band_structure": True, "class_values_observed": sorted(observed), "native_validation_only": True, "webmap_used_as_analytical_input": False, "provider_values_resampled": False, "provider_values_reprojected": False, "provider_values_aggregated": False, "classifier_executed": False, "parent_state_assignments": 0, "residual_regolith_assignments": 0, "saprolite_assignments": 0, "bedrock_assignments": 0, "P7Q_reopened": False, "canonical_parent_created": False, "physical_soil_created": False, "temporal_reconstruction": False})
    adjudication = {"stage": "R5.17-B7-A3F2-P7Q-PRE5K", "decision": "AUTHORIZE_P7Q_PRE5L_RESIDUAL_PROCESS_PROVIDER_GRID_ALIGNMENT_AND_ELIGIBILITY_CONTRACT_GATE", "verdict": "PASS_P7Q_PRE5K_RESIDUAL_PROCESS_PROVIDER_ACQUISITION_AND_BINDING_VALIDATED", "status": "COMPLETE__PROCESS_PROVIDER_ACQUIRED_AND_BOUND__NO_ARCANA_CLASSIFICATION", "next_action": "P7Q_PRE5L_RESIDUAL_PROCESS_PROVIDER_GRID_ALIGNMENT_AND_ELIGIBILITY_CONTRACT_GATE", "dataset_title": metadata["title"], "version_doi": metadata["doi"], "license": metadata["license"], "final_classification_tile_count": 60, "total_acquired_bytes": total_bytes, "provider_semantic_ceiling": binding["semantic_ceiling"], "provider_values_resampled": False, "provider_values_reprojected": False, "provider_values_aggregated": False, "provider_values_crosswalked_to_arcana": False, "classifier_executed": False, "parent_state_assignments": 0, "residual_regolith_assignments": 0, "saprolite_assignments": 0, "bedrock_assignments": 0, "P7Q_reopened": False, "scientific_authority_register_mutated": False}
    write_json("R5_17_B7_A3F2_P7Q_PRE5K_ADJUDICATION.json", adjudication)
    (ROOT / "R5_17_B7_A3F2_P7Q_PRE5K_ADJUDICATION.md").write_text("# R5.17-B7-A3F2-P7Q-PRE5K\n\nDecision: `AUTHORIZE_P7Q_PRE5L_RESIDUAL_PROCESS_PROVIDER_GRID_ALIGNMENT_AND_ELIGIBILITY_CONTRACT_GATE`\n\nVerdict: `PASS_P7Q_PRE5K_RESIDUAL_PROCESS_PROVIDER_ACQUISITION_AND_BINDING_VALIDATED`\n\nThe official Figshare v1 final classification product was acquired and validated as 60 native 250 m Equal Earth GeoTIFF tiles. Codes are bound from the official item description: 0 ocean, 1 sink, 2 bypass, 3 source, 4 missing data. Martin/Lamb remains a long-timescale sediment process-domain conditioner and is method-dependent on Pelletier; no ARCANA crosswalk or parent-state classification was executed. PRE5L is the next gate.\n", encoding="utf-8")
    state_path = ROOT / "ARCANA_WORLD_CURRENT_STATE.md"
    state = state_path.read_text(encoding="utf-8")
    for old, new in [("LATEST_COMPLETED_INTERNAL_STEP: R5.17-B7-A3F2-P7Q-PRE5J", "LATEST_COMPLETED_INTERNAL_STEP: R5.17-B7-A3F2-P7Q-PRE5K"), ("LATEST_INTERNAL_VERDICT: PASS_P7Q_PRE5J_RESIDUAL_PROCESS_AUTHORITY_COMPLETION_ADJUDICATED", "LATEST_INTERNAL_VERDICT: PASS_P7Q_PRE5K_RESIDUAL_PROCESS_PROVIDER_ACQUISITION_AND_BINDING_VALIDATED"), ("ACTIVE_SUBPHASE_STATUS: A3_IN_PROGRESS__P7Q_PRE5J_COMPLETE__RESIDUAL_PROCESS_AUTHORITY_ACQUISITION_REQUIRED", "ACTIVE_SUBPHASE_STATUS: A3_IN_PROGRESS__P7Q_PRE5K_COMPLETE__PROCESS_PROVIDER_BOUND__NO_ARCANA_CLASSIFICATION"), ("NEXT_ACTION: P7Q_PRE5K_RESIDUAL_PROCESS_PROVIDER_ACQUISITION_AND_BINDING_GATE", "NEXT_ACTION: P7Q_PRE5L_RESIDUAL_PROCESS_PROVIDER_GRID_ALIGNMENT_AND_ELIGIBILITY_CONTRACT_GATE")]:
        if old not in state:
            raise SystemExit("BLOCKED_P7Q_PRE5K_CURRENT_STATE_EXPECTATION_MISSING")
        state = state.replace(old, new, 1)
    state += "\nP7Q_PRE5K_STATUS: COMPLETE__PROCESS_PROVIDER_ACQUIRED_AND_BOUND__NO_ARCANA_CLASSIFICATION\nP7Q_PRE5K_DECISION: AUTHORIZE_P7Q_PRE5L_RESIDUAL_PROCESS_PROVIDER_GRID_ALIGNMENT_AND_ELIGIBILITY_CONTRACT_GATE\n"
    state_path.write_text(state, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
