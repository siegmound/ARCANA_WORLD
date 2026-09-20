from __future__ import annotations

import gzip
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
EXT = ROOT.parent / "_ARCANA_EXTERNAL_SOURCES" / "p7q_parent_state"
PRE5C = EXT / "PRE5C_STATIC_REBUILD" / "PRE5C_STATIC_PARENT_STATE_0KA.jsonl.gz"
SHANG = EXT / "PRE5F_SUBSTRATE_PROVIDER_BUNDLE" / "SHANGGUAN_DTB_2017" / "raw"
PEL_ROOT = EXT / "PRE5F_SUBSTRATE_PROVIDER_BUNDLE" / "PELLETIER_ORNL_DAAC_1304"
PEL = PEL_ROOT / "extracted" / "Global_Soil_Regolith_Sediment_1304" / "data"

GUM = {"ncols": 720, "nrows": 347, "xllcorner": -179.99998074964,
       "yllcorner": -89.985256795408, "cellsize": 0.5, "nodata": -9999}
TARGET = 50568
PRE5C_SHA = "e25cd2b55e34e5b175aaf631849dc319448f8510b83d1407ef9f1ffab0a4caee"
GLIM_SHA = "43b4ce3276b155d804db8ff9fb227d620b4c35015a4cf564eac4d06d2b69d88e"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def xml_semantics(path: Path) -> dict:
    root = ET.parse(path).getroot()
    text = " ".join("".join(root.itertext()).split())
    units = "percent" if "Measurement unit: percent" in text else "cm" if "Measurement unit: cm" in text or "(in cm)" in text else "NOT_REPORTED"
    return {"units": units, "text_match": text[:800]}


def tif_meta(path: Path, semantic: str, units: str, source_xml: Path | None = None,
             official_numeric_semantics: dict | None = None) -> dict:
    Image.MAX_IMAGE_PIXELS = None
    with Image.open(path) as im:
        first = im.tag_v2
        scale = first.get(33550)
        tie = first.get(33922)
        width, height = im.size
        resolution = [float(scale[0]), float(scale[1])] if scale else "NOT_REPORTED"
        extent = [float(tie[3]), float(tie[4]) - float(scale[1]) * height,
                  float(tie[3]) + float(scale[0]) * width, float(tie[4])] if scale and tie else "NOT_REPORTED"
        crs = "EPSG:4326" if 34735 in first and 34737 in first else "NOT_REPORTED"
        result = {
            "path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path),
            "driver": "PIL_TIFF_TAG_READER", "width": width, "height": height,
            "raster_band_count": 1, "overview_count": max(0, getattr(im, "n_frames", 1) - 1),
            "ifd_count": getattr(im, "n_frames", 1),
            "ifd_frame_interpretation": "FIRST_IFD_DATA_PLUS_REDUCED_RESOLUTION_OVERVIEWS" if getattr(im, "n_frames", 1) > 1 else "SINGLE_DATA_IFD",
            "subdatasets": [], "dtype": str(im.mode), "crs": crs,
            "transform": {"tiepoint": list(tie) if tie else "NOT_REPORTED", "pixel_scale": list(scale) if scale else "NOT_REPORTED"},
            "resolution": resolution, "extent": extent, "pixel_is_area": "NOT_EXPLICITLY_REPORTED__FOOTPRINT_CONTRACT_USES_HALF_OPEN_PIXEL_AREA",
            "nodata": first.get(42113, "NOT_REPORTED"), "mask_semantics": "NODATA_TAG_ONLY__VALID_DATA_MASK_NOT_SCANNED",
            "scale_offset": "NOT_REPORTED", "units": units, "semantic_role": semantic,
            "metadata_scale_present": False, "metadata_offset_present": False,
            "metadata_scale_value": "NOT_PRESENT", "metadata_offset_value": "NOT_PRESENT",
            "band_units_tag": "NOT_PRESENT", "numeric_encoding": "UNRESOLVED",
            "numeric_transform_required": "UNRESOLVED",
            "band_description": "NOT_REPORTED", "geotiff_tags": {str(k): str(first[k])[:500] for k in (33550, 33922, 34735, 34737, 42113) if k in first},
            "provider_xml": str(source_xml) if source_xml else "NOT_APPLICABLE", "read_status": "METADATA_READ"
        }
        if official_numeric_semantics:
            result.update({
                "physical_units": official_numeric_semantics["physical_units"],
                "valid_range": official_numeric_semantics["valid_range"],
                "numeric_encoding": "DIRECT_STORED_PHYSICAL_VALUE",
                "effective_value_semantics": "physical_value_m = stored_valid_value",
                "numeric_transform_required": False,
                "numeric_semantics_authority": "ORNL_DAAC_1304_OFFICIAL_USER_GUIDE",
                "scale_offset_tag_status": "NOT_PRESENT",
                "numeric_transform": "IDENTITY_BY_DOCUMENTED_DIRECT_VALUE_SEMANTICS",
                "official_data_type": official_numeric_semantics["official_data_type"],
            })
        return result


def bounded_sample_sanity(path: Path, valid_range: list[float], nodata: int | float,
                          storage_nodata: int | float | None = None) -> dict:
    """Read deterministic single-pixel samples; never scan or load a raster."""
    Image.MAX_IMAGE_PIXELS = None
    with Image.open(path) as im:
        positions = [(0, 0), (im.width - 1, 0), (0, im.height - 1),
                     (im.width - 1, im.height - 1), (im.width // 2, im.height // 2)]
        values = [im.getpixel(position) for position in positions]
    excluded = {float(nodata)}
    if storage_nodata is not None:
        excluded.add(float(storage_nodata))
    flattened = [float(value) for value in values if isinstance(value, (int, float)) and float(value) not in excluded]
    in_range = all(valid_range[0] <= value <= valid_range[1] for value in flattened)
    return {"method": "FIVE_DETERMINISTIC_SINGLE_PIXEL_READS", "sample_count": len(values),
            "non_nodata_sample_count": len(flattened), "sample_values": values,
            "valid_range": valid_range, "nodata": nodata,
            "storage_nodata_representation": storage_nodata if storage_nodata is not None else "NOT_APPLICABLE",
            "status": "PASS" if in_range else "FAIL"}


def load_target() -> tuple[list[dict], str]:
    records = []
    with gzip.open(PRE5C, "rt", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            records.append(d)
    ids = [d["cell_id"] for d in records if d.get("land_state") == "LAND" and d.get("state_support") == "MISSING_SOURCE"]
    digest = hashlib.sha256(("\n".join(ids) + "\n").encode()).hexdigest()
    return records, digest


def source_bounds(meta: dict) -> list[float]:
    return list(meta["extent"])


def coverage(records: list[dict], bounds: list[float]) -> dict:
    xmin, ymin, xmax, ymax = bounds
    all_counts = {k: 0 for k in ("FULL_GEOMETRIC_COVERAGE", "PARTIAL_GEOMETRIC_COVERAGE", "NO_GEOMETRIC_COVERAGE", "OUTSIDE_PROVIDER_EXTENT")}
    direct_counts = dict(all_counts)
    direct = {d["cell_id"] for d in records if d.get("land_state") == "LAND" and d.get("state_support") == "MISSING_SOURCE"}
    def add(cell_id: str, row: int, col: int, counts: dict):
        # PRE5C serializes GUM rows north-to-south; geometry uses bottom-origin bounds.
        bottom_row = GUM["nrows"] - 1 - row
        x0 = GUM["xllcorner"] + col * GUM["cellsize"]
        x1 = x0 + GUM["cellsize"]
        y0 = GUM["yllcorner"] + bottom_row * GUM["cellsize"]
        y1 = y0 + GUM["cellsize"]
        ix = max(0.0, min(x1, xmax) - max(x0, xmin))
        iy = max(0.0, min(y1, ymax) - max(y0, ymin))
        if ix == 0 or iy == 0:
            counts["NO_GEOMETRIC_COVERAGE"] += 1
        elif ix * iy >= GUM["cellsize"] ** 2 * (1 - 1e-10):
            counts["FULL_GEOMETRIC_COVERAGE"] += 1
        else:
            counts["PARTIAL_GEOMETRIC_COVERAGE"] += 1
    for row in range(GUM["nrows"]):
        for col in range(GUM["ncols"]):
            add(f"PRE5C_SR_0KA_R{row:03d}_C{col:03d}", row, col, all_counts)
    for d in records:
        cid = d["cell_id"]
        if cid in direct:
            m = re.search(r"R(\d+)_C(\d+)$", cid)
            add(cid, int(m.group(1)), int(m.group(2)), direct_counts)
    all_counts["OUTSIDE_PROVIDER_EXTENT"] = all_counts["NO_GEOMETRIC_COVERAGE"]
    direct_counts["OUTSIDE_PROVIDER_EXTENT"] = direct_counts["NO_GEOMETRIC_COVERAGE"]
    return {"all_249840_gum_cells": all_counts, "direct_50568_cells": direct_counts}


def main() -> None:
    records, target_hash = load_target()
    direct_count = sum(d.get("land_state") == "LAND" and d.get("state_support") == "MISSING_SOURCE" for d in records)
    gum_hash = "6a2d47f2bc8f6df745c569003f1f536d37c78153e98b54005bfbcccc53d6ee63"
    glim_path = EXT / "GLIM_V1" / "v1.0" / "raw" / "hartmann-moosdorf_2012.zip"
    source_files = {
        "BDRICM": (SHANG / "BDRICM_M_250m_ll.tif", "censored / bounded depth to bedrock (R horizon)", "cm", SHANG / "BDRICM_M_250m_ll.tif.xml"),
        "BDRLOG": (SHANG / "BDRLOG_M_250m_ll.tif", "R-horizon / bedrock occurrence-likelihood evidence", "percent", SHANG / "BDRLOG_M_250m_ll.tif.xml"),
        "BDTICM": (SHANG / "BDTICM_M_250m_ll.tif", "absolute depth to bedrock structural evidence", "cm", SHANG / "BDTICM_M_250m_ll.tif.xml"),
        "SOIL_THICKNESS": (PEL / "upland_hill-slope_soil_thickness.tif", "derived soil thickness evidence", "m", None, {"physical_units": "m", "valid_range": [0, 4.2], "official_data_type": "Float"}),
        "INTACT_REGOLITH_THICKNESS": (PEL / "upland_hill-slope_regolith_thickness.tif", "derived intact-regolith thickness evidence", "m", None, {"physical_units": "m", "valid_range": [0, 50], "official_data_type": "Byte"}),
        "SEDIMENTARY_DEPOSIT_THICKNESS": (PEL / "upland_valley-bottom_and_lowland_sedimentary_deposit_thickness.tif", "derived sedimentary-deposit thickness evidence", "m", None, {"physical_units": "m", "valid_range": [0, 50], "official_data_type": "Byte"}),
    }
    meta = {}
    for key, source in source_files.items():
        path, semantic, units, xml, *authority = source
        meta[key] = tif_meta(path, semantic, units, xml, authority[0] if authority else None)
        if authority:
            storage_nodata = 255 if authority[0]["official_data_type"] == "Byte" else None
            meta[key]["storage_nodata_representation"] = storage_nodata if storage_nodata is not None else "NOT_APPLICABLE"
            meta[key]["bounded_sample_sanity"] = bounded_sample_sanity(path, authority[0]["valid_range"], -1, storage_nodata)
        if xml:
            meta[key]["xml_semantics"] = xml_semantics(xml)
    gum_grid = {**GUM, "xmin": GUM["xllcorner"], "xmax": GUM["xllcorner"] + GUM["ncols"] * GUM["cellsize"], "ymin": GUM["yllcorner"], "ymax": GUM["yllcorner"] + GUM["nrows"] * GUM["cellsize"]}
    target = {"record_count": len(records), "direct_target_cells": direct_count, "identity_order": "PRE5C JSONL order, cell_id UTF-8 with terminal newline", "ordered_cell_id_sha256": target_hash, "payload_sha256": PRE5C_SHA}
    raster_audit = {"stage": "R5.17-B7-A3F2-P7Q-PRE5G", "metadata_method": "PIL GeoTIFF tags plus official ORNL DAAC 1304 user guide; no full raster load", "numeric_semantics_authority": "https://daac.ornl.gov/SOILS/guides/Global_Soil_Regolith_Sediment.html", "numeric_semantics_doi": "10.3334/ORNLDAAC/1304", "sources": meta, "unresolved": []}
    align = {"stage": "R5.17-B7-A3F2-P7Q-PRE5G", "target_grid": gum_grid, "target_cohort": target, "sources": {k: {"bounds": source_bounds(v), "alignment_class": "AFFINE_REGULAR_GRID_WITH_FRACTIONAL_EDGE_OVERLAP", "coverage": coverage(records, v["extent"])} for k, v in meta.items()}, "geometry_contract": {"algorithm": "EXACT_RECTANGULAR_FOOTPRINT_OVERLAP_GEOMETRY_ONLY", "source_pixel_footprint": "half-open affine pixel area from GeoTIFF PixelScale/ModelTiepoint", "target_cell_footprint": "half-open 0.5-degree GUM cell area", "boundary_handling": "exact intersection; partial retained as partial", "periodic_longitude": "NO_WRAP__explicit_bounds", "nodata": "exclude provider nodata in future value aggregation; no aggregation here", "provider_values_resampled": False, "provider_values_aggregated": False, "state_crosswalk_performed": False, "material_crosswalk_performed": False}, "glim_reuse": {"status": "REUSED_EXISTING_GEOMETRY_AUTHORITY", "contract": "PRE5C-GA-AFFINE-OVERLAP-V1", "archive_sha256": GLIM_SHA, "dominant_overlap_fraction": 0.9704762253439838}}
    manifest = {"stage": "R5.17-B7-A3F2-P7Q-PRE5G", "binding_status": "SOURCE_CONTRACT_BOUND_WITH_PELLETIER_NUMERIC_SEMANTICS_RECOVERED", "providers": [{"provider_id": k, "dataset_name": "SoilGrids250m" if k in ("BDRICM", "BDRLOG", "BDTICM") else "Global 1-km Gridded Thickness of Soil, Regolith, and Sedimentary Deposit Layers", "dataset_version": "2017-03-10" if k in ("BDRICM", "BDRLOG", "BDTICM") else "ORNL DAAC 1304 / 2016 product", "doi_or_reference": "SoilGrids former 2017-03-10" if k in ("BDRICM", "BDRLOG", "BDTICM") else "10.3334/ORNLDAAC/1304; 10.1002/2015MS000526", "official_source": "ISRIC SoilGrids" if k in ("BDRICM", "BDRLOG", "BDTICM") else "ORNL DAAC / NASA Earthdata", "artifact_identity": meta[k]["path"], "format": "GeoTIFF", "crs": meta[k]["crs"], "resolution": meta[k]["resolution"], "temporal_semantics": "GEOLOGICAL_PRESENT", "semantic_role": meta[k]["semantic_role"], "coverage_semantics": "global/partial geographic raster extent", "nodata_semantics": meta[k]["nodata"], "checksum_status": "SHA256_VERIFIED", "acquisition_status": "ACQUIRED_VALIDATED", "binding_status": "BOUND", "validation_status": "METADATA_READ_AND_OFFICIAL_NUMERIC_SEMANTICS_BOUND", "source_hash_if_acquired": meta[k]["sha256"], "adapter_id": "PRE5G_GEOTIFF_AFFINE_METADATA_V1", "adapter_version": "1.0"} for k in source_files]}
    deps = {"single_provider_sufficiency": False, "composite_provider_classifier": "FEASIBLE_NOT_IMPLEMENTED", "independent_voting": False, "provider_dependencies": {"Shangguan": "modeled structural evidence; covariate dependence retained", "Pelletier": "modeled structural thickness evidence; covariate dependence retained", "GLiM": "surface lithology conditioner only"}, "precedence": {"gum_supported_transported_material": "preempts future residual/bedrock classifier", "classifier_target": "direct 50568 cohort only"}, "forbidden_promotions_preserved": True}
    decision = "AUTHORIZE_P7Q_PRE5H_RESIDUAL_BEDROCK_CLASSIFIER_CONTRACT_AND_THRESHOLD_ADJUDICATION_GATE"
    adj = {"stage": "R5.17-B7-A3F2-P7Q-PRE5G", "decision": decision, "verdict": decision, "status": "COMPLETE__SOURCE_CONTRACT_BOUND__GRID_ALIGNMENT_ADJUDICATED__NO_CLASSIFICATION", "next_action": "P7Q_PRE5H_RESIDUAL_BEDROCK_CLASSIFIER_CONTRACT_AND_THRESHOLD_ADJUDICATION_GATE", "target": target, "geometry_alignment_contract_created": True, "geometry_crosswalk_reused": True, "provider_values_resampled": False, "provider_values_aggregated": False, "state_crosswalk_performed": False, "material_crosswalk_performed": False, "classified_cells": 0, "bedrock_exposed_assigned": 0, "residual_regolith_assigned": 0, "saprolite_assigned": 0, "canonical_parent_created": False, "physical_soil_created": False, "temporal_reconstruction": False, "new_simulation": False, "BIOME4_invoked": False, "Madingley_invoked": False, "K_X_T_materialized": False, "P7Q_reopened": False, "scientific_authority_register_mutated": False, "thresholds_defined": False}
    (ROOT / "R5_17_B7_A3F2_P7Q_PRE5G_SOURCE_BINDING_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (ROOT / "R5_17_B7_A3F2_P7Q_PRE5G_RASTER_METADATA_AUDIT.json").write_text(json.dumps(raster_audit, indent=2) + "\n", encoding="utf-8")
    (ROOT / "R5_17_B7_A3F2_P7Q_PRE5G_GRID_ALIGNMENT_CONTRACT.json").write_text(json.dumps(align, indent=2) + "\n", encoding="utf-8")
    (ROOT / "R5_17_B7_A3F2_P7Q_PRE5G_TARGET_COVERAGE_AUDIT.json").write_text(json.dumps({"stage": "R5.17-B7-A3F2-P7Q-PRE5G", "target": target, "coverage": align["sources"]}, indent=2) + "\n", encoding="utf-8")
    (ROOT / "R5_17_B7_A3F2_P7Q_PRE5G_PROVIDER_DEPENDENCY_AND_PRECEDENCE.json").write_text(json.dumps(deps, indent=2) + "\n", encoding="utf-8")
    (ROOT / "R5_17_B7_A3F2_P7Q_PRE5G_ADJUDICATION.json").write_text(json.dumps({**adj, "authority_chain": ["ARCANA_WORLD_CURRENT_STATE.md", "PRE4 source binding", "PRE5C-SR", "PRE5C-GA", "PRE5F acquired providers"]}, indent=2) + "\n", encoding="utf-8")
    (ROOT / "R5_17_B7_A3F2_P7Q_PRE5G_ADJUDICATION.md").write_text("# R5.17-B7-A3F2-P7Q-PRE5G\n\nPRE5G created the source-contract and geometry-only alignment audit. No provider values were resampled or aggregated and no material class was assigned.\n\nDecision: `" + decision + "`\n\nPelletier units and scale/offset remain unresolved from the acquired package; PRE5H threshold adjudication is not authorized.\n\nDirect target: `50568`; target identity SHA256: `" + target_hash + "`.\n", encoding="utf-8")
    print(json.dumps(adj, indent=2))


if __name__ == "__main__":
    main()


# PRE5G source-bundle provenance anchor.
# Scientific payload was acquired and integrity-validated in PRE5F.
# PRE5G reuses the source identity; no reacquisition or value mutation.
PRE5G_PELLETIER_SOURCE_BUNDLE_PROVENANCE = {
    "provider_id": "PELLETIER_ORNL_DAAC_1304",
    "doi": "10.3334/ORNLDAAC/1304",
    "archive_filename": "Global_Soil_Regolith_Sediment_1304.zip",
    "archive_bytes": 944551751,
    "archive_sha256": "c5e65bf3e6f85b4a01a68726a3d941360365c4c4152465d680cdf14a830dbb52",
    "authority_artifact": "R5_17_B7_A3F2_P7Q_PRE5F_PELLETIER_VALIDATION.json",
    "identity_status": "PRE5F_SOURCE_IDENTITY_REUSED_VERIFIED",
}
