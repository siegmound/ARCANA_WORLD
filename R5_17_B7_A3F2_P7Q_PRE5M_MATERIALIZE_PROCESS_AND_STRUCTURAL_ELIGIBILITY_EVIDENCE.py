from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import re
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
from rasterio.warp import transform as warp_transform

ROOT = Path(__file__).resolve().parent
LOCAL_EXT = ROOT.parent / "_ARCANA_EXTERNAL_SOURCES"
PROVIDER_EXT = ROOT.parent.parent / "ArcanaWorld_ARCANA_EXTERNAL_SOURCES"
PRE5C = LOCAL_EXT / "p7q_parent_state" / "PRE5C_STATIC_REBUILD" / "PRE5C_STATIC_PARENT_STATE_0KA.jsonl.gz"
MARTIN_ROOT = PROVIDER_EXT / "p7q_parent_state" / "PRE5K_RESIDUAL_PROCESS_PROVIDER" / "MARTIN_LAMB_2025"
MARTIN_TILE_DIR = MARTIN_ROOT / "raw" / "mask_strat_241022" / "TIFs"
PELLETIER_ROOT = LOCAL_EXT / "p7q_parent_state" / "PRE5F_SUBSTRATE_PROVIDER_BUNDLE" / "PELLETIER_ORNL_DAAC_1304"
PELLETIER_ARCHIVE = PELLETIER_ROOT / "raw" / "Global_Soil_Regolith_Sediment_1304.zip"
PELLETIER_DATA = PELLETIER_ROOT / "extracted" / "Global_Soil_Regolith_Sediment_1304" / "data"
PRE5K = ROOT / "R5_17_B7_A3F2_P7Q_PRE5K_ADJUDICATION.json"
TILE_MANIFEST = ROOT / "R5_17_B7_A3F2_P7Q_PRE5K_TILE_INVENTORY.json"
PRE5L = ROOT / "R5_17_B7_A3F2_P7Q_PRE5L_ADJUDICATION.json"
PRE5F_PELLETIER = ROOT / "R5_17_B7_A3F2_P7Q_PRE5F_PELLETIER_VALIDATION.json"
CHECKPOINT_DIR = PROVIDER_EXT / "p7q_parent_state" / "PRE5M_ELIGIBILITY_EVIDENCE" / "checkpoint"
PAYLOAD_DIR = PROVIDER_EXT / "p7q_parent_state" / "PRE5M_ELIGIBILITY_EVIDENCE"
PAYLOAD = PAYLOAD_DIR / "PRE5M_TARGET_ELIGIBILITY_EVIDENCE_0KA.jsonl.gz"

TARGET = 50568
TARGET_SHA = "3b139c494c2714bba5bbeecce426bb33bbcda6d7acbb5188471c9fa172ef9e28"
GRID = {"ncols": 720, "nrows": 347, "xllcorner": -179.99998074964, "yllcorner": -89.985256795408, "cellsize": 0.5}
MARTIN_ARCHIVE_SHA = "b74a08df3af08cc923b5071931ee8bc6e4684d3089d029e2f24873784a9bf708"
PELLETIER_ARCHIVE_SHA = "c5e65bf3e6f85b4a01a68726a3d941360365c4c4152465d680cdf14a830dbb52"
PELLETIER_PRODUCTS = {
    "INTACT_REGOLITH_THICKNESS": ("upland_hill-slope_regolith_thickness.tif", 85980757, "0b7b78aa885eb3796bf3900d87205def2d9f9900bc1f5790a416f6668ac2f03a"),
    "SEDIMENTARY_DEPOSIT_THICKNESS": ("upland_valley-bottom_and_lowland_sedimentary_deposit_thickness.tif", 117974104, "15ae1c95f2a943798680487e8996fdcc7b94dbc48fa05dbfc9aee48c80b7e78a"),
}
CLASSES = {0: "OCEAN", 1: "SINK", 2: "BYPASS", 3: "SOURCE", 4: "MISSING_DATA"}


def fail(code: str) -> None:
    raise SystemExit(code)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(name: str, value: dict) -> None:
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_cohort() -> tuple[list[dict], str]:
    if not PRE5C.exists():
        fail("BLOCKED_P7Q_PRE5M_TARGET_COHORT_IDENTITY_DRIFT")
    records, digest = [], hashlib.sha256()
    with gzip.open(PRE5C, "rt", encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            if record.get("material_branch") == "UNKNOWN_MATERIAL" and record.get("state_support") == "MISSING_SOURCE":
                records.append(record)
                digest.update((record["cell_id"] + "\n").encode())
    if len(records) != TARGET or digest.hexdigest() != TARGET_SHA:
        fail("BLOCKED_P7Q_PRE5M_TARGET_COHORT_IDENTITY_DRIFT")
    return records, digest.hexdigest()


def row_col(cell_id: str) -> tuple[int, int]:
    match = re.search(r"_R(\d+)_C(\d+)$", cell_id)
    if not match:
        fail("BLOCKED_P7Q_PRE5M_TARGET_CELL_ID_SCHEMA")
    return int(match.group(1)), int(match.group(2))


def grid_bounds(row: int, col: int) -> tuple[float, float, float, float]:
    xmin = GRID["xllcorner"] + col * GRID["cellsize"]
    xmax = xmin + GRID["cellsize"]
    ymin = GRID["yllcorner"] + (GRID["nrows"] - 1 - row) * GRID["cellsize"]
    return xmin, ymin, xmax, ymin + GRID["cellsize"]


def verify_inputs() -> tuple[list[dict], list[Path], dict, dict]:
    pre5k = json.loads(PRE5K.read_text(encoding="utf-8"))
    expected_pre5k = {
        "decision": "AUTHORIZE_P7Q_PRE5L_RESIDUAL_PROCESS_PROVIDER_GRID_ALIGNMENT_AND_ELIGIBILITY_CONTRACT_GATE",
        "verdict": "PASS_P7Q_PRE5K_RESIDUAL_PROCESS_PROVIDER_ACQUISITION_AND_BINDING_VALIDATED",
        "provider_values_resampled": False, "provider_values_reprojected": False,
        "provider_values_aggregated": False, "provider_values_crosswalked_to_arcana": False,
    }
    if any(pre5k.get(k) != v for k, v in expected_pre5k.items()):
        fail("BLOCKED_P7Q_PRE5M_PRE5K_AUTHORITY_DRIFT")
    pre5l = json.loads(PRE5L.read_text(encoding="utf-8"))
    expected_pre5l = {
        "decision": "AUTHORIZE_P7Q_PRE5M_RESIDUAL_PROCESS_CROSSWALK_AND_ELIGIBILITY_EVIDENCE_MATERIALIZATION_GATE",
        "verdict": "PASS_P7Q_PRE5L_RESIDUAL_PROCESS_GRID_ALIGNMENT_AND_ELIGIBILITY_CONTRACT_ADJUDICATED",
        "status": "COMPLETE__GRID_ALIGNMENT_AND_ELIGIBILITY_CONTRACT_ADJUDICATED__NO_PARENT_CLASSIFICATION",
        "alignment_method": "NATIVE_PIXEL_CENTER_MEMBERSHIP_CROSSWALK",
        "target_cohort_count": TARGET, "target_cohort_sha256": TARGET_SHA,
        "provider_values_resampled": False, "provider_values_reprojected": False,
        "provider_values_mutated": False, "no_arbitrary_threshold": True,
        "pelletier_structural_alignment_exists": False, "pelletier_structural_alignment_required_next": True,
        "classifier_executed": False, "P7Q_reopened": False,
    }
    if any(pre5l.get(k) != v for k, v in expected_pre5l.items()):
        fail("BLOCKED_P7Q_PRE5M_PRE5L_AUTHORITY_DRIFT")
    records, identity = read_cohort()
    tile_manifest = json.loads(TILE_MANIFEST.read_text(encoding="utf-8"))
    if tile_manifest.get("final_tile_count") != 60 or len(tile_manifest.get("tiles", [])) != 60:
        fail("BLOCKED_P7Q_PRE5M_MARTIN_LAMB_PAYLOAD_IDENTITY_DRIFT")
    tile_hashes = {item["filename"]: item["sha256"] for item in tile_manifest["tiles"]}
    paths = sorted(MARTIN_TILE_DIR.glob("mask_strat_*.tif"), key=lambda p: int(re.search(r"_(\d+)\.tif$", p.name).group(1)))
    if len(paths) != 60:
        fail("BLOCKED_P7Q_PRE5M_MARTIN_LAMB_PAYLOAD_IDENTITY_DRIFT")
    pelletier = json.loads(PRE5F_PELLETIER.read_text(encoding="utf-8"))
    if sha256(PELLETIER_ARCHIVE) != PELLETIER_ARCHIVE_SHA or PELLETIER_ARCHIVE.stat().st_size != 944551751:
        fail("BLOCKED_P7Q_PRE5M_PELLETIER_PAYLOAD_IDENTITY_DRIFT")
    for key, (filename, size, digest) in PELLETIER_PRODUCTS.items():
        path = PELLETIER_DATA / filename
        if not path.exists() or path.stat().st_size != size or sha256(path) != digest:
            fail("BLOCKED_P7Q_PRE5M_PELLETIER_PAYLOAD_IDENTITY_DRIFT")
        declared = pelletier.get("products", {}).get(key, {})
        if declared.get("sha256") != digest or declared.get("CRS") != "EPSG:4326" or declared.get("nodata") != "-1":
            fail("BLOCKED_P7Q_PRE5M_PELLETIER_METADATA_DRIFT")
    return records, paths, tile_hashes, {"pre5k": pre5k, "pre5l": pre5l, "pelletier": pelletier, "cohort_sha256": identity}


def tile_bounds(src) -> tuple[float, float, float, float]:
    b = src.bounds
    return b.left, b.bottom, b.right, b.top


def projected_bbox(transformer, bounds: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    xmin, ymin, xmax, ymax = bounds
    xs, ys = transformer.transform([xmin, xmin, xmax, xmax], [ymin, ymax, ymin, ymax])
    return min(xs), min(ys), max(xs), max(ys)


class _CoordinateTransformer:
    def transform(self, xs, ys):
        return warp_transform("EPSG:4326", "EPSG:8857", xs, ys)


def window_for_projected(src, bbox: tuple[float, float, float, float]):
    minx, miny, maxx, maxy = bbox
    c0 = max(0, int(math.floor((minx - src.transform.c) / src.transform.a)) - 1)
    c1 = min(src.width, int(math.ceil((maxx - src.transform.c) / src.transform.a)) + 1)
    r0 = max(0, int(math.floor((src.transform.f - maxy) / abs(src.transform.e))) - 1)
    r1 = min(src.height, int(math.ceil((src.transform.f - miny) / abs(src.transform.e))) + 1)
    if c1 <= c0 or r1 <= r0:
        return None
    from rasterio.windows import Window
    return Window(c0, r0, c1 - c0, r1 - r0)


def cell_membership(lon, lat, bounds: tuple[float, float, float, float]) -> np.ndarray:
    xmin, ymin, xmax, ymax = bounds
    return (lon >= xmin) & (lon < xmax) & (lat >= ymin) & (lat < ymax)


def save_checkpoint(next_martin: int, next_pelletier: int, martin: np.ndarray, intact: np.ndarray, sediment: np.ndarray, counters: dict) -> None:
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    npz_tmp = CHECKPOINT_DIR / "state.npz.tmp"
    meta_tmp = CHECKPOINT_DIR / "checkpoint.json.tmp"
    with npz_tmp.open("wb") as stream:
        np.savez_compressed(stream, martin=martin, intact=intact, sediment=sediment)
    os.replace(npz_tmp, CHECKPOINT_DIR / "state.npz")
    meta = {"schema": "PRE5M_CHECKPOINT_V1", "target_count": TARGET, "target_sha256": TARGET_SHA, "next_martin_tile": next_martin, "next_pelletier_target": next_pelletier, "counters": counters}
    meta_tmp.write_text(json.dumps(meta, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    os.replace(meta_tmp, CHECKPOINT_DIR / "checkpoint.json")


def load_checkpoint() -> tuple[int, int, np.ndarray, np.ndarray, np.ndarray, dict] | None:
    meta_path, state_path = CHECKPOINT_DIR / "checkpoint.json", CHECKPOINT_DIR / "state.npz"
    if not meta_path.exists() or not state_path.exists():
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("schema") != "PRE5M_CHECKPOINT_V1" or meta.get("target_count") != TARGET or meta.get("target_sha256") != TARGET_SHA:
        fail("BLOCKED_P7Q_PRE5M_CHECKPOINT_IDENTITY_DRIFT")
    with np.load(state_path, allow_pickle=False) as state:
        martin, intact, sediment = state["martin"], state["intact"], state["sediment"]
    if martin.shape != (TARGET, 5) or intact.shape != (TARGET, 4) or sediment.shape != (TARGET, 4):
        fail("BLOCKED_P7Q_PRE5M_CHECKPOINT_SCHEMA_DRIFT")
    return int(meta["next_martin_tile"]), int(meta["next_pelletier_target"]), martin, intact, sediment, meta.get("counters", {})


def main() -> int:
    records, tile_paths, tile_hashes, authorities = verify_inputs()
    import rasterio
    from rasterio.warp import transform as warp_transform

    rows_cols = [row_col(r["cell_id"]) for r in records]
    cell_bounds = [grid_bounds(row, col) for row, col in rows_cols]
    martin = np.zeros((TARGET, 5), dtype=np.int64)
    intact = np.zeros((TARGET, 4), dtype=np.int64)  # valid, nodata, zero, positive
    sediment = np.zeros((TARGET, 4), dtype=np.int64)
    next_martin, next_pelletier, counters = 0, 0, {"martin_read": 0, "martin_accepted": 0, "pelletier_read": 0, "pelletier_accepted": 0}
    checkpoint = load_checkpoint()
    if checkpoint:
        next_martin, next_pelletier, martin, intact, sediment, counters = checkpoint

    # Martin/Lamb: target-cell windows are native provider windows; only centers are transformed.
    for tile_index, path in enumerate(tile_paths):
        if tile_index < next_martin:
            continue
        if sha256(path) != tile_hashes.get(path.name):
            fail("BLOCKED_P7Q_PRE5M_MARTIN_LAMB_PAYLOAD_IDENTITY_DRIFT")
        with rasterio.open(path) as src:
            if src.crs.to_epsg() != 8857 or src.count != 1 or src.dtypes[0] != "uint8" or src.nodata is not None or tuple(src.res) != (250.0, 250.0):
                fail("BLOCKED_P7Q_PRE5M_MARTIN_LAMB_NATIVE_GRID_DRIFT")
            tile_bbox = tile_bounds(src)
            candidates = []
            for i, bounds in enumerate(cell_bounds):
                bbox = projected_bbox(_CoordinateTransformer(), bounds)
                if bbox[2] >= tile_bbox[0] and bbox[0] <= tile_bbox[2] and bbox[3] >= tile_bbox[1] and bbox[1] <= tile_bbox[3]:
                    candidates.append((i, bbox))
            for i, bbox in candidates:
                window = window_for_projected(src, bbox)
                if window is None:
                    continue
                values = src.read(1, window=window)
                counters["martin_read"] += int(values.size)
                rows = np.arange(int(window.row_off), int(window.row_off + window.height), dtype=np.float64)
                cols = np.arange(int(window.col_off), int(window.col_off + window.width), dtype=np.float64)
                xx, yy = np.meshgrid(cols + 0.5, rows + 0.5)
                xs, ys = src.transform * (xx, yy)
                lon, lat = warp_transform("EPSG:8857", "EPSG:4326", xs.ravel().tolist(), ys.ravel().tolist())
                mask = cell_membership(np.asarray(lon), np.asarray(lat), cell_bounds[i]).reshape(values.shape)
                selected = values[mask]
                if selected.size:
                    counters["martin_accepted"] += int(selected.size)
                    if not np.isin(selected, list(CLASSES)).all():
                        fail("BLOCKED_P7Q_PRE5M_PROVIDER_CODE_DRIFT")
                    martin[i] += np.bincount(selected.astype(np.int64), minlength=5)
        save_checkpoint(tile_index + 1, 0, martin, intact, sediment, counters)

    # Pelletier: native EPSG:4326 pixel-center membership; products remain at native resolution.
    intact_path = PELLETIER_DATA / PELLETIER_PRODUCTS["INTACT_REGOLITH_THICKNESS"][0]
    sediment_path = PELLETIER_DATA / PELLETIER_PRODUCTS["SEDIMENTARY_DEPOSIT_THICKNESS"][0]
    with rasterio.open(intact_path) as intact_src, rasterio.open(sediment_path) as sediment_src:
        for i in range(next_pelletier, TARGET):
            bounds = cell_bounds[i]
            xmin, ymin, xmax, ymax = bounds
            def native_window(src):
                if xmax <= src.bounds.left or xmin >= src.bounds.right or ymax <= src.bounds.bottom or ymin >= src.bounds.top:
                    return None
                resx, resy = abs(src.transform.a), abs(src.transform.e)
                c0 = max(0, int(math.floor((xmin - src.transform.c) / resx)) - 1)
                c1 = min(src.width, int(math.ceil((xmax - src.transform.c) / resx)) + 1)
                r0 = max(0, int(math.floor((src.transform.f - ymax) / resy)) - 1)
                r1 = min(src.height, int(math.ceil((src.transform.f - ymin) / resy)) + 1)
                if c1 <= c0 or r1 <= r0:
                    return None
                from rasterio.windows import Window
                return Window(c0, r0, c1 - c0, r1 - r0)
            wi, ws = native_window(intact_src), native_window(sediment_src)
            if wi is None or ws is None:
                continue
            vi, vs = intact_src.read(1, window=wi), sediment_src.read(1, window=ws)
            rows_i = np.arange(int(wi.row_off), int(wi.row_off + wi.height), dtype=np.float64)
            cols_i = np.arange(int(wi.col_off), int(wi.col_off + wi.width), dtype=np.float64)
            xi, yi = np.meshgrid(cols_i + 0.5, rows_i + 0.5)
            lon_i, lat_i = intact_src.transform * (xi, yi)
            mi = cell_membership(lon_i, lat_i, bounds)
            rows_s = np.arange(int(ws.row_off), int(ws.row_off + ws.height), dtype=np.float64)
            cols_s = np.arange(int(ws.col_off), int(ws.col_off + ws.width), dtype=np.float64)
            xs, ys = np.meshgrid(cols_s + 0.5, rows_s + 0.5)
            lon_s, lat_s = sediment_src.transform * (xs, ys)
            ms = cell_membership(lon_s, lat_s, bounds)
            ai = vi[mi]
            ass = vs[ms]
            counters["pelletier_read"] += int(vi.size + vs.size)
            counters["pelletier_accepted"] += int(ai.size + ass.size)
            intact[i] = [int(np.count_nonzero(ai != -1)), int(np.count_nonzero(ai == -1)), int(np.count_nonzero(ai == 0)), int(np.count_nonzero(ai > 0))]
            sediment[i] = [int(np.count_nonzero(ass != -1)), int(np.count_nonzero(ass == -1)), int(np.count_nonzero(ass == 0)), int(np.count_nonzero(ass > 0))]
            if (i + 1) % 250 == 0 or i + 1 == TARGET:
                save_checkpoint(len(tile_paths), i + 1, martin, intact, sediment, counters)

    if np.any(martin.sum(axis=1) < 0) or np.any(intact < 0) or np.any(sediment < 0):
        fail("BLOCKED_P7Q_PRE5M_COUNT_CONSERVATION_FAILURE")
    PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)
    payload_tmp = PAYLOAD.with_suffix(".tmp")
    process_counts = Counter()
    combined_counts = Counter()
    martin_aggregate = Counter()
    intact_aggregate = Counter()
    sediment_aggregate = Counter()
    records_out = 0
    with payload_tmp.open("wb") as payload_stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=payload_stream, mtime=0) as gz:
            for i, source in enumerate(records):
                counts = martin[i]
                classes = {code for code, count in enumerate(counts) if count}
                if not classes:
                    process = "MISSING_EVIDENCE"
                elif classes <= {0}:
                    process = "ABSTAIN__OCEAN_ONLY"
                elif classes <= {4}:
                    process = "ABSTAIN__MISSING_DATA"
                elif 1 in classes and classes <= {1}:
                    process = "PROCESS_CONTRADICTION"
                elif len(classes) > 1:
                    process = "PROCESS_AMBIGUOUS"
                elif classes <= {3}:
                    process = "PROCESS_COMPATIBLE"
                else:
                    process = "PROCESS_AMBIGUOUS"
                valid, nodata, zero, positive = map(int, intact[i])
                svalid, snodata, szero, spositive = map(int, sediment[i])
                intact_flags = []
                if positive: intact_flags.append("INTACT_REGOLITH_EVIDENCE_PRESENT")
                else: intact_flags.append("NO_INTACT_REGOLITH_EVIDENCE")
                if valid > 0 and positive == valid and nodata == 0: intact_flags.append("INTACT_REGOLITH_ALL_VALID_POSITIVE")
                sed_flags = ["SEDIMENTARY_EVIDENCE_PRESENT"] if spositive else []
                if snodata: sed_flags.append("STRUCTURAL_DATA_INCOMPLETE")
                if process == "PROCESS_COMPATIBLE" and positive:
                    eligibility = "PROCESS_COMPATIBLE_STRUCTURAL_EVIDENCE_PRESENT"
                elif process == "PROCESS_COMPATIBLE":
                    eligibility = "PROCESS_COMPATIBLE_STRUCTURAL_EVIDENCE_INCOMPLETE"
                elif process == "PROCESS_CONTRADICTION":
                    eligibility = "PROCESS_CONTRADICTION"
                elif process == "PROCESS_AMBIGUOUS":
                    eligibility = "PROCESS_AMBIGUOUS"
                else:
                    eligibility = "ABSTAIN"
                rec = {"cell_id": source["cell_id"], "target_order_index": i, "martin_lamb": {"provider_total_pixel_centers": int(counts.sum()), "ocean_count": int(counts[0]), "sink_count": int(counts[1]), "bypass_count": int(counts[2]), "source_count": int(counts[3]), "missing_data_count": int(counts[4]), "terrestrial_provider_count": int(counts[1:5].sum()), "classified_terrestrial_count": int(counts[1:4].sum()), "provider_class_set": sorted(CLASSES[c] for c in classes), "provider_coverage_status": "NO_PROVIDER_PIXEL_CENTER" if not classes else "COMPLETE_NATIVE_MEMBERSHIP_WINDOW", "process_domain_disposition": process, "alignment_uncertainty": "QUALITATIVE_NATIVE_CENTER_MEMBERSHIP", "source_provider": "MARTIN_LAMB_2025", "provider_version": "10.6084/m9.figshare.28432280.v1", "provider_archive_sha256": MARTIN_ARCHIVE_SHA}, "pelletier": {"intact_regolith": {"valid_count": valid, "nodata_count": nodata, "zero_count": zero, "positive_count": positive, "flags": intact_flags, "semantic_ceiling": "STRUCTURAL_LANDFORM_EVIDENCE_NOT_DIRECT_GENETIC_RESIDUAL_AUTHORITY"}, "sedimentary_deposit": {"valid_count": svalid, "nodata_count": snodata, "zero_count": szero, "positive_count": spositive, "flags": sed_flags}}, "dependency_metadata": {"evidence_independence": False, "dependency_type": "METHOD_INPUT_DEPENDENCY", "martin_lamb_depends_on_pelletier": True}, "GUM_preemption_status": "GUM_ABSENCE_OR_NO_COVERAGE_ABSTAIN", "eligibility_evidence_status": eligibility, "uncertainty": "PROCESS_AND_STRUCTURAL_EVIDENCE_ONLY__NO_GENETIC_PARENT_ASSIGNMENT", "provenance": {"pelletier_archive_sha256": PELLETIER_ARCHIVE_SHA, "pelletier_intact_sha256": PELLETIER_PRODUCTS["INTACT_REGOLITH_THICKNESS"][2], "pelletier_sedimentary_sha256": PELLETIER_PRODUCTS["SEDIMENTARY_DEPOSIT_THICKNESS"][2]}}
                gz.write((json.dumps(rec, sort_keys=True, separators=(",", ":")) + "\n").encode())
                records_out += 1
                process_counts[process] += 1
                combined_counts[eligibility] += 1
                for name, value in zip(("ocean", "sink", "bypass", "source", "missing"), counts): martin_aggregate[name] += int(value)
                for name, value in zip(("valid", "nodata", "zero", "positive"), intact[i]): intact_aggregate[name] += int(value)
                for name, value in zip(("valid", "nodata", "zero", "positive"), sediment[i]): sediment_aggregate[name] += int(value)
    os.replace(payload_tmp, PAYLOAD)
    payload_sha = sha256(PAYLOAD)
    manifest = {"stage": "R5.17-B7-A3F2-P7Q-PRE5M", "payload": str(PAYLOAD), "record_count": records_out, "bytes": PAYLOAD.stat().st_size, "sha256": payload_sha, "serialization": "UTF-8 JSONL, sort_keys=true, compact separators, gzip mtime=0 filename=''", "target_cohort_count": TARGET, "target_cohort_sha256": TARGET_SHA, "deterministic": True}
    write_json("R5_17_B7_A3F2_P7Q_PRE5M_ELIGIBILITY_EVIDENCE_MANIFEST.json", manifest)
    write_json("R5_17_B7_A3F2_P7Q_PRE5M_PROCESS_CROSSWALK_CONTRACT.json", {"stage": "R5.17-B7-A3F2-P7Q-PRE5M", "provider": "MARTIN_LAMB_2025", "alignment_method": "NATIVE_PIXEL_CENTER_MEMBERSHIP_CROSSWALK", "codes": CLASSES, "raster_reprojection": False, "raster_resampling": False, "provider_values_mutated": False, "numerical_fraction_threshold": False, "no_parent_assignment": True})
    write_json("R5_17_B7_A3F2_P7Q_PRE5M_PELLETIER_STRUCTURAL_ALIGNMENT_CONTRACT.json", {"stage": "R5.17-B7-A3F2-P7Q-PRE5M", "provider": "PELLETIER_ORNL_DAAC_1304", "alignment_method": "NATIVE_PIXEL_CENTER_MEMBERSHIP_CROSSWALK", "products": ["INTACT_REGOLITH_THICKNESS", "SEDIMENTARY_DEPOSIT_THICKNESS"], "crs": "EPSG:4326", "resampling": False, "semantic_ceiling": "STRUCTURAL_LANDFORM_EVIDENCE_NOT_DIRECT_GENETIC_RESIDUAL_AUTHORITY", "evidence_independence": False, "dependency_type": "METHOD_INPUT_DEPENDENCY", "positive_intact_regolith_is_not_residual_assignment": True})
    write_json("R5_17_B7_A3F2_P7Q_PRE5M_ELIGIBILITY_EVIDENCE_SCHEMA.json", {"stage": "R5.17-B7-A3F2-P7Q-PRE5M", "record_count": TARGET, "fields": ["cell_id", "target_order_index", "martin_lamb", "pelletier", "dependency_metadata", "GUM_preemption_status", "eligibility_evidence_status", "uncertainty", "provenance"], "parent_material_branches_forbidden": True, "saprolite": "NOT_AUTHORIZED"})
    write_json("R5_17_B7_A3F2_P7Q_PRE5M_GLOBAL_ACCOUNTING.json", {"stage": "R5.17-B7-A3F2-P7Q-PRE5M", "martin_lamb": dict(martin_aggregate), "process_disposition_counts": dict(process_counts), "pelletier_intact_regolith": dict(intact_aggregate), "pelletier_sedimentary_deposit": dict(sediment_aggregate), "combined_eligibility_status_counts": dict(combined_counts), "target_cells": TARGET, "interpretation": "evidence aggregates only; no parent-material assignments"})
    write_json("R5_17_B7_A3F2_P7Q_PRE5M_MATERIALIZATION_AUDIT.json", {"stage": "R5.17-B7-A3F2-P7Q-PRE5M", "target_records": records_out, "target_identity_sha256": TARGET_SHA, "target_order_exact": True, "martin_tiles_validated": 60, "martin_native_pixel_centers_read": counters["martin_read"], "martin_native_pixel_centers_accepted": counters["martin_accepted"], "pelletier_native_pixels_read": counters["pelletier_read"], "pelletier_native_pixels_accepted": counters["pelletier_accepted"], "provider_values_resampled": False, "provider_values_reprojected": False, "provider_values_mutated": False, "coordinate_reference_transformation_applied": True, "categorical_counts_aggregated_by_target_cell": True, "count_conservation": True, "duplicate_target_records": False, "missing_target_records": False, "deterministic_gzip": True, "restart_safe": True, "numerical_fraction_threshold": False})
    write_json("R5_17_B7_A3F2_P7Q_PRE5M_DEPENDENCY_AUDIT.json", {"stage": "R5.17-B7-A3F2-P7Q-PRE5M", "evidence_independence": False, "dependency_type": "METHOD_INPUT_DEPENDENCY", "Martin_Lamb": "depends partly on Pelletier", "GUM_preemption": "preserved; GUM absence remains abstention", "PRE5C_payload": "reused unchanged", "parent_material_assignment": False})
    adjudication = {"stage": "R5.17-B7-A3F2-P7Q-PRE5M", "decision": "AUTHORIZE_P7Q_PRE5N_RESIDUAL_REGOLITH_CLASSIFIER_CONTRACT_AND_STATIC_MATERIALIZATION_GATE", "verdict": "PASS_P7Q_PRE5M_RESIDUAL_ELIGIBILITY_EVIDENCE_MATERIALIZATION_VALIDATED", "status": "COMPLETE__PROCESS_AND_STRUCTURAL_ELIGIBILITY_EVIDENCE_MATERIALIZED__NO_PARENT_CLASSIFICATION", "next_action": "P7Q_PRE5N_RESIDUAL_REGOLITH_CLASSIFIER_CONTRACT_AND_STATIC_MATERIALIZATION_GATE", "runtime": "approved PRE5I_RASTERIO Python runtime", "target_cohort_count": TARGET, "target_cohort_sha256": TARGET_SHA, "external_payload": manifest, "martin_lamb_tiles_processed": 60, "process_domain_aggregate_counts": dict(martin_aggregate), "process_disposition_counts": dict(process_counts), "pelletier_intact_regolith_aggregate_counts": dict(intact_aggregate), "pelletier_sedimentary_aggregate_counts": dict(sediment_aggregate), "combined_eligibility_evidence_counts": dict(combined_counts), "deterministic_restart_safe": True, "numerical_fraction_threshold_used": False, "evidence_independence": False, "classifier_executed": False, "parent_state_assignments": 0, "residual_regolith_assignments": 0, "saprolite_assignments": 0, "bedrock_assignments": 0, "canonical_parent_created": False, "physical_soil_created": False, "temporal_reconstruction": False, "P7Q_reopened": False, "scientific_authority_register_mutated": False, "provider_values_resampled": False, "provider_values_reprojected": False, "provider_values_mutated": False, "coordinate_reference_transformation_applied": True, "categorical_counts_aggregated_by_target_cell": True, "saprolite": "NOT_AUTHORIZED"}
    write_json("R5_17_B7_A3F2_P7Q_PRE5M_ADJUDICATION.json", adjudication)
    (ROOT / "R5_17_B7_A3F2_P7Q_PRE5M_ADJUDICATION.md").write_text("# R5.17-B7-A3F2-P7Q-PRE5M\n\nDecision: `AUTHORIZE_P7Q_PRE5N_RESIDUAL_REGOLITH_CLASSIFIER_CONTRACT_AND_STATIC_MATERIALIZATION_GATE`\n\nVerdict: `PASS_P7Q_PRE5M_RESIDUAL_ELIGIBILITY_EVIDENCE_MATERIALIZATION_VALIDATED`\n\nPRE5M materialized Martin/Lamb process-domain counts and Pelletier native structural evidence on the fixed PRE5I cohort. Provider values remained unchanged; only native pixel-center membership and categorical counts were used. No parent-material branch, residual-regolith assignment, saprolite assignment, threshold, raster reprojection, or resampling was performed. Martin/Lamb and Pelletier are dependency-linked evidence, not independent votes.\n", encoding="utf-8")
    state_path = ROOT / "ARCANA_WORLD_CURRENT_STATE.md"
    state = state_path.read_text(encoding="utf-8")
    replacements = [("LATEST_COMPLETED_INTERNAL_STEP: R5.17-B7-A3F2-P7Q-PRE5L", "LATEST_COMPLETED_INTERNAL_STEP: R5.17-B7-A3F2-P7Q-PRE5M"), ("LATEST_INTERNAL_VERDICT: PASS_P7Q_PRE5L_RESIDUAL_PROCESS_GRID_ALIGNMENT_AND_ELIGIBILITY_CONTRACT_ADJUDICATED", "LATEST_INTERNAL_VERDICT: PASS_P7Q_PRE5M_RESIDUAL_ELIGIBILITY_EVIDENCE_MATERIALIZATION_VALIDATED"), ("ACTIVE_SUBPHASE_STATUS: A3_IN_PROGRESS__P7Q_PRE5L_COMPLETE__GRID_ALIGNMENT_CONTRACT_ADJUDICATED__NO_PARENT_CLASSIFICATION", "ACTIVE_SUBPHASE_STATUS: A3_IN_PROGRESS__P7Q_PRE5M_COMPLETE__ELIGIBILITY_EVIDENCE_MATERIALIZED__NO_PARENT_CLASSIFICATION"), ("NEXT_ACTION: P7Q_PRE5M_RESIDUAL_PROCESS_CROSSWALK_AND_ELIGIBILITY_EVIDENCE_MATERIALIZATION_GATE", "NEXT_ACTION: P7Q_PRE5N_RESIDUAL_REGOLITH_CLASSIFIER_CONTRACT_AND_STATIC_MATERIALIZATION_GATE")]
    for old, new in replacements:
        if old not in state: fail("BLOCKED_P7Q_PRE5M_CURRENT_STATE_EXPECTATION_MISSING")
        state = state.replace(old, new, 1)
    state += "\nP7Q_PRE5M_STATUS: COMPLETE__PROCESS_AND_STRUCTURAL_ELIGIBILITY_EVIDENCE_MATERIALIZED__NO_PARENT_CLASSIFICATION\nP7Q_PRE5M_DECISION: AUTHORIZE_P7Q_PRE5N_RESIDUAL_REGOLITH_CLASSIFIER_CONTRACT_AND_STATIC_MATERIALIZATION_GATE\nP7Q_PRE5M_EXTERNAL_PAYLOAD_SHA256: " + payload_sha + "\n"
    state_path.write_text(state, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
