from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any
import csv
import gzip
import hashlib
import json
import math

import numpy as np

STAGE = "v0.6D1-R5.2"
OUT_REL = Path("outputs/v0_6D1_R5_2")
R51_OUT_REL = Path("outputs/v0_6D1_R5_1")
R51_FINAL_SEAL_REL = R51_OUT_REL / "R5_1_FINAL_SEAL.json"
R51_ATLAS_REL = R51_OUT_REL / "R5_1_CRADLE_OPPORTUNITY_ATLAS.npz"
R51_ENVELOPES_REL = R51_OUT_REL / "R5_1_OCCUPIED_ENVIRONMENT_ENVELOPES.json"
R51_CANDIDATE_MANIFEST_REL = R51_OUT_REL / "R5_1_OUTPUT_MANIFEST.json"
R51_STRUCTURE_REL = R51_OUT_REL / "R5_1_CRADLE_STRUCTURE_AND_ENGINE_ADJUDICATION.json"
R51_FAMILIES_REL = R51_OUT_REL / "R5_1_ROBUST_REGION_FAMILIES.json"
R51_STRUCTURE_MANIFEST_REL = R51_OUT_REL / "R5_1_STRUCTURE_ADJUDICATION_MANIFEST.json"
J14_REL = Path("outputs/v0_6D1_R4_30/authority/R4_30_J14_SPATIAL_AUTHORITY_REPLAY_CANDIDATE.npz")
R314_SEAL_REL = Path("outputs/v0_6D1_R3_14/FORMAL_AUDIT_SEALED_v0_6D1_R3_14.json")
R41_R_WRAPPER_REL = Path("benchmarks/r41/run_r_with_conda_libs.sh")
SOURCE_MANIFEST_REL = Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_2.json")

EXPECTED_R51_FINAL_SEAL_SHA256 = "74f13a6b397a2926db0ebcf6b45a4976678b598d241fe05acb3c3317d383e74c"
EXPECTED_R51_ATLAS_SHA256 = "9d4a70780785bdda7d1a51549d3b842450d6b563cab44684229157f073707caa"
EXPECTED_R51_CANDIDATE_MANIFEST_SHA256 = "a7540f66e037df808d2f63a722a4e554fcbb394444f6761e7054ec14d7f5f54d"
EXPECTED_R51_STRUCTURE_MANIFEST_SHA256 = "d97fbe2288391cd1df5bf587eeee6ea77e2d9ccd258ae908bb5b608b95b06509"
EXPECTED_J14_SHA256 = "eed2d1e350783f1d2dc31c5b7e697330ccbfcf63024062bc9f4ed2f8905f4756"
EXPECTED_R314_SEAL_SHA256 = "4a97e2c5aa7e0d7583aff89b3507bbe9555abe151aec96ed1667045080a468f0"
EXPECTED_R41_R_WRAPPER_SHA256 = "bea44c1528862d08d3ff0f4471eb9f913a02b6e09c70968b15a39107036329c6"

CANDIDATES = ("RPT_010_D02", "RPT_009_D02")
EXPECTED_ROBUST_FAMILY_COUNT = 12
HABITAT_PROFILES = (
    "LAND_SUPPORT_UPPER_BOUND",
    "OCCUPIED_ENVELOPE_CORE_DIAGNOSTIC",
)
MOVEMENT_PROFILES = {
    "D1_STANDARDIZED_1_CELL_CHARACTERISTIC": 100.0,
    "D2_STANDARDIZED_2_CELL_CHARACTERISTIC": 200.0,
}
SEEDS = (520201, 520202)
ENGINE_GRID_RESOLUTION = 100.0
ENGINE_STEP_KYR = 20.0
RMAX = 1.5
EMIGRATION_PROBABILITY = 0.1
HABITAT_CARRYING_CAPACITY = 10.0
RANGESHIFTER_INITIALIZATION_MODE = "SPDIST_INITTYPE1_SPTYPE0"
RANGESHIFTER_INIT_TYPE = 1
RANGESHIFTER_SP_TYPE = 0
RANGESHIFTER_INIT_DENS = 1


class R52Error(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def semantic_sha256(arr: np.ndarray) -> str:
    a = np.ascontiguousarray(arr)
    h = hashlib.sha256()
    h.update(str(a.dtype).encode("ascii"))
    h.update(b"|")
    h.update(repr(tuple(a.shape)).encode("ascii"))
    h.update(b"|")
    h.update(a.tobytes(order="C"))
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _verify_output_manifest(root: Path, manifest_rel: Path) -> bool:
    root = Path(root)
    p = root / manifest_rel
    if not p.is_file():
        return False
    try:
        m = load_json(p)
        files = dict(m.get("files") or {})
        out = p.parent
        if not files:
            return False
        return all(
            (out / name).is_file()
            and int(meta.get("bytes", -1)) == (out / name).stat().st_size
            and meta.get("sha256") == sha256_file(out / name)
            for name, meta in files.items()
        )
    except Exception:
        return False


def validate_parent_authority(root: Path, allow_non_scientific_dev: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    strict = not allow_non_scientific_dev
    paths = {
        "r51seal": root / R51_FINAL_SEAL_REL,
        "atlas": root / R51_ATLAS_REL,
        "envelopes": root / R51_ENVELOPES_REL,
        "candidate_manifest": root / R51_CANDIDATE_MANIFEST_REL,
        "structure": root / R51_STRUCTURE_REL,
        "families": root / R51_FAMILIES_REL,
        "structure_manifest": root / R51_STRUCTURE_MANIFEST_REL,
        "j14": root / J14_REL,
        "r314": root / R314_SEAL_REL,
        "r41_wrapper": root / R41_R_WRAPPER_REL,
    }
    checks: dict[str, bool] = {f"present::{k}": p.is_file() for k, p in paths.items()}

    if paths["r51seal"].is_file():
        seal = load_json(paths["r51seal"])
        summary = seal.get("summary") or {}
        checks["r51_sealed_semantics"] = (
            seal.get("sealed") is True
            and seal.get("scientific_seal") is True
            and seal.get("status") == "PASS_R51_EMERGENT_HOMINID_CRADLE_AND_ECOLOGICAL_NICHE_DISCOVERY_SEALED"
            and summary.get("all_threshold_family_count") == EXPECTED_ROBUST_FAMILY_COUNT
            and summary.get("closure_readiness") == "READY_FOR_R51_SEAL_NO_NEW_EXTERNAL_ENGINE_REQUIRED"
            and summary.get("RangeShifter_action") == "DEFER_NEW_EXECUTION_TO_R5_2_TARGETED_CORRIDOR_VALIDATION"
            and summary.get("canonical_state_changed") is False
            and summary.get("derived_refinement_promoted_to_canon") is False
            and summary.get("deep_biological_coupling") is False
        )
        checks["r51_exact_hash"] = (sha256_file(paths["r51seal"]) == EXPECTED_R51_FINAL_SEAL_SHA256) if strict else True
    else:
        checks["r51_sealed_semantics"] = checks["r51_exact_hash"] = False

    checks["r51_atlas_exact_hash"] = (
        paths["atlas"].is_file() and (sha256_file(paths["atlas"]) == EXPECTED_R51_ATLAS_SHA256 if strict else True)
    )
    checks["r51_candidate_manifest_exact_hash"] = (
        paths["candidate_manifest"].is_file()
        and (sha256_file(paths["candidate_manifest"]) == EXPECTED_R51_CANDIDATE_MANIFEST_SHA256 if strict else True)
    )
    checks["r51_structure_manifest_exact_hash"] = (
        paths["structure_manifest"].is_file()
        and (sha256_file(paths["structure_manifest"]) == EXPECTED_R51_STRUCTURE_MANIFEST_SHA256 if strict else True)
    )
    checks["r51_candidate_manifest_integrity"] = _verify_output_manifest(root, R51_CANDIDATE_MANIFEST_REL)
    checks["r51_structure_manifest_integrity"] = _verify_output_manifest(root, R51_STRUCTURE_MANIFEST_REL)

    if paths["structure"].is_file():
        st = load_json(paths["structure"])
        eng = st.get("engine_adjudication") or {}
        rs = eng.get("RangeShifter") or {}
        checks["r51_structure_semantics"] = (
            st.get("status") == "PASS_R51_CRADLE_STRUCTURE_AND_ENGINE_ADJUDICATION"
            and st.get("all_threshold_family_count") == EXPECTED_ROBUST_FAMILY_COUNT
            and st.get("closure_readiness") == "READY_FOR_R51_SEAL_NO_NEW_EXTERNAL_ENGINE_REQUIRED"
            and rs.get("action") == "DEFER_NEW_EXECUTION_TO_R5_2_TARGETED_CORRIDOR_VALIDATION"
            and eng.get("external_engine_defines_arcana_target") is False
            and eng.get("majority_vote") is False
        )
    else:
        checks["r51_structure_semantics"] = False

    if paths["families"].is_file():
        f = load_json(paths["families"])
        fams = list(f.get("families") or [])
        robust = [x for x in fams if x.get("survives_all_thresholds") is True]
        checks["r51_robust_family_count_exact"] = len(robust) == EXPECTED_ROBUST_FAMILY_COUNT
        checks["r51_both_candidates_present"] = set(x.get("candidate_id") for x in robust) == set(CANDIDATES)
    else:
        checks["r51_robust_family_count_exact"] = False
        checks["r51_both_candidates_present"] = False

    checks["j14_exact_hash"] = paths["j14"].is_file() and (sha256_file(paths["j14"]) == EXPECTED_J14_SHA256 if strict else True)
    checks["r314_seal_exact_hash"] = paths["r314"].is_file() and (sha256_file(paths["r314"]) == EXPECTED_R314_SEAL_SHA256 if strict else True)
    if paths["r314"].is_file():
        r314 = load_json(paths["r314"])
        checks["r314_provider_sealed"] = (
            r314.get("verdict") == "PASS_R314_LATE_CENOZOIC_PROVIDER_C2_AND_ADAPTIVE_CLOCK_BOUND__30MA_H0_BIOLOGY_RESTART_BOUNDARY_SEALED"
            and r314.get("failed") == []
        )
    else:
        checks["r314_provider_sealed"] = False
    checks["r41_r_wrapper_exact_hash"] = paths["r41_wrapper"].is_file() and (
        sha256_file(paths["r41_wrapper"]) == EXPECTED_R41_R_WRAPPER_SHA256 if strict else True
    )

    checks = {k: bool(v) for k, v in checks.items()}
    failed = [k for k, v in checks.items() if not v]
    return {
        "stage": STAGE,
        "status": "PASS_R52_IMMUTABLE_PARENT_AUTHORITY" if not failed else "BLOCKED_R52_PARENT_AUTHORITY",
        "scientific_parent_mode": strict,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failed": failed,
        "checks": checks,
    }


def _components(mask: np.ndarray) -> list[list[tuple[int, int]]]:
    nr, nc = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out: list[list[tuple[int, int]]] = []
    for r in range(nr):
        for c in range(nc):
            if not mask[r, c] or seen[r, c]:
                continue
            q = deque([(r, c)])
            seen[r, c] = True
            cells: list[tuple[int, int]] = []
            while q:
                a, b = q.popleft()
                cells.append((a, b))
                for aa, bb in ((a - 1, b), (a + 1, b), (a, (b - 1) % nc), (a, (b + 1) % nc)):
                    if 0 <= aa < nr and mask[aa, bb] and not seen[aa, bb]:
                        seen[aa, bb] = True
                        q.append((aa, bb))
            out.append(cells)
    return out


def reconstruct_robust_family_cores(root: Path) -> tuple[list[dict[str, Any]], dict[str, set[int]], np.ndarray, np.ndarray]:
    root = Path(root)
    with np.load(root / R51_ATLAS_REL, allow_pickle=False) as z:
        ids = tuple(map(str, z["candidate_ids"].tolist()))
        mass_all = np.asarray(z["population_mass_fraction"], float)
        land = np.asarray(z["land_persistence_fraction"], float)
        lat = np.asarray(z["lat"], float)
        lon = np.asarray(z["lon"], float)
    if ids != CANDIDATES:
        raise R52Error(f"R5.1 candidate IDs differ from frozen cohort: {ids}")
    registry = load_json(root / R51_FAMILIES_REL)
    fams = [x for x in list(registry.get("families") or []) if x.get("survives_all_thresholds") is True]
    fams = sorted(fams, key=lambda x: (CANDIDATES.index(str(x["candidate_id"])), str(x["family_id"])))
    if len(fams) != EXPECTED_ROBUST_FAMILY_COUNT:
        raise R52Error(f"Expected {EXPECTED_ROBUST_FAMILY_COUNT} all-threshold families, got {len(fams)}")
    nr, nc = land.shape
    cores: dict[str, set[int]] = {}
    for fam in fams:
        sid = str(fam["candidate_id"])
        j = ids.index(sid)
        positive = mass_all[j][mass_all[j] > 0]
        if not positive.size:
            raise R52Error(f"No positive population mass for {sid}")
        threshold = float(np.quantile(positive, 0.99))
        comps = _components((mass_all[j] >= threshold) & (mass_all[j] > 0) & (land > 0))
        idxs = list((fam.get("component_indices_by_threshold") or {}).get("0.99") or [])
        if not idxs:
            raise R52Error(f"{fam['family_id']} has no q99 component indices")
        cells: set[int] = set()
        for ci in idxs:
            ci = int(ci)
            if ci < 0 or ci >= len(comps):
                raise R52Error(f"{fam['family_id']} q99 component index {ci} out of range")
            cells |= {r * nc + c for r, c in comps[ci]}
        if len(cells) != int(fam.get("core_cell_count", -1)):
            raise R52Error(f"{fam['family_id']} core cell reconstruction mismatch")
        rr = np.asarray(sorted(cells), int) // nc
        cc = np.asarray(sorted(cells), int) % nc
        if [int(rr.min()), int(rr.max())] != list(map(int, fam.get("core_row_minmax") or [])):
            raise R52Error(f"{fam['family_id']} row bounds mismatch")
        if [int(cc.min()), int(cc.max())] != list(map(int, fam.get("core_col_minmax") or [])):
            raise R52Error(f"{fam['family_id']} col bounds mismatch")
        cores[str(fam["family_id"])] = cells
    return fams, cores, lat, lon


def _load_j14_targets(root: Path, nr: int, nc: int) -> tuple[np.ndarray, tuple[str, ...], np.ndarray]:
    with np.load(Path(root) / J14_REL, allow_pickle=False) as z:
        ages = np.asarray(z["age_ma"], float)
        ids = tuple(map(str, z["candidate_ids"].tolist()))
        spatial = np.asarray(z["spatial_state"], float)
    if ids != CANDIDATES or spatial.shape != (96, 2, 141, 8, 4):
        raise R52Error("J14 schema/candidate cohort differs from R5.2 authority")
    targets = np.zeros((len(ids), len(ages), nr, nc), dtype=bool)
    for e in range(spatial.shape[0]):
        for j in range(spatial.shape[1]):
            for t in range(spatial.shape[2]):
                ds = spatial[e, j, t]
                for row in ds[ds[:, 3] > 0.5]:
                    r = int(np.clip(np.rint(row[1]), 0, nr - 1))
                    c = int(np.clip(np.rint(row[2]), 0, nc - 1))
                    targets[j, t, r, c] = True
    return ages, ids, targets


def _load_c2_provider(root: Path):
    from arcana_worldsim.scientific_engines import r314_late_cenozoic_binding as r314

    root = Path(root)
    a1 = r314.load_a1(root)
    bind = root / "local_bindings/v0_6D1_R3_14"
    c2, _ = r314.build_bound_provider_and_clock(
        a1,
        bind / "v0_6_1_SEALED_MINIMAL",
        bind / "v0_6_4B1/exact_120ka_A1_boundary_state.npz",
        bind / "v0_6_4B2/relative_eustatic_shoreline_anomaly_120ka_A1.npz",
    )
    return a1, c2


def _environment_cache(root: Path, ages: np.ndarray) -> dict[str, np.ndarray]:
    a1, c2 = _load_c2_provider(root)
    lat = np.asarray(a1["lat"], float)
    lon = np.asarray(a1["lon"], float)
    nr, nc = len(lat), len(lon)
    T = len(ages)
    out = {
        "land": np.empty((T, nr, nc), dtype=bool),
        "temperature_c": np.empty((T, nr, nc), dtype=np.float32),
        "aridity_index": np.empty((T, nr, nc), dtype=np.float32),
        "total_edible_forage": np.empty((T, nr, nc), dtype=np.float32),
        "wetland_forage": np.empty((T, nr, nc), dtype=np.float32),
    }
    for t, age in enumerate(ages):
        st = c2.state_at(float(age))
        out["land"][t] = np.asarray(st["land_support"], float) > 1e-9
        for key in ("temperature_c", "aridity_index", "total_edible_forage", "wetland_forage"):
            out[key][t] = np.asarray(st[key], dtype=np.float32)
    return out


def _circular_source_col(core_cells: set[int], nc: int, mass: np.ndarray | None = None) -> int:
    idx = np.asarray(sorted(core_cells), int)
    cc = idx % nc
    if mass is None:
        w = np.full(len(cc), 1.0 / len(cc))
    else:
        rr = idx // nc
        vals = np.maximum(np.asarray(mass[rr, cc], float), 0.0)
        w = vals / vals.sum() if vals.sum() > 0 else np.full(len(cc), 1.0 / len(cc))
    ang = 2.0 * np.pi * cc / nc
    a = math.atan2(float(np.sum(np.sin(ang) * w)), float(np.sum(np.cos(ang) * w)))
    if a < 0:
        a += 2.0 * np.pi
    return int(round(a * nc / (2.0 * np.pi))) % nc


def _write_ascii_grid(path: Path, arr: np.ndarray, *, cellsize: float = ENGINE_GRID_RESOLUTION) -> None:
    a = np.asarray(arr)
    if a.ndim != 2:
        raise ValueError("ASCII grid requires 2D array")
    nr, nc = a.shape
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="ascii", newline="\n") as f:
        f.write(f"ncols {nc}\n")
        f.write(f"nrows {nr}\n")
        f.write("xllcorner 0\n")
        f.write("yllcorner 0\n")
        f.write(f"cellsize {cellsize:g}\n")
        f.write("NODATA_value -9999\n")
        # ESRI ASCII starts at the top row. R5.2 intentionally flips the
        # ARCANA row order so RangeShiftR y=0 maps back to ARCANA row=0.
        for row in np.flipud(a):
            f.write(" ".join(str(int(x)) for x in row.tolist()) + "\n")


def _habitat_mask(profile: str, env: dict[str, np.ndarray], envelope: dict[str, Any]) -> np.ndarray:
    land = np.asarray(env["land"], bool)
    if profile == "LAND_SUPPORT_UPPER_BOUND":
        return land.copy()
    if profile != "OCCUPIED_ENVELOPE_CORE_DIAGNOSTIC":
        raise R52Error(f"Unknown habitat profile {profile}")
    mask = land.copy()
    for key in ("temperature_c", "aridity_index", "total_edible_forage", "wetland_forage"):
        rec = envelope.get(key) or {}
        lo, hi = float(rec["q05"]), float(rec["q95"])
        a = np.asarray(env[key], float)
        mask &= np.isfinite(a) & (a >= lo) & (a <= hi)
    return mask


def prepare_corridor_inputs(root: Path, allow_non_scientific_dev_parent: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    auth = validate_parent_authority(root, allow_non_scientific_dev=allow_non_scientific_dev_parent)
    if auth["failed"]:
        raise R52Error(f"R5.2 parent authority failed: {auth['failed']}")

    out = root / OUT_REL
    work = out / "rangeshifter_work"
    work.mkdir(parents=True, exist_ok=True)

    fams, cores, lat, lon = reconstruct_robust_family_cores(root)
    nr, nc = len(lat), len(lon)
    ages, ids, targets = _load_j14_targets(root, nr, nc)
    env = _environment_cache(root, ages)
    envelopes = load_json(root / R51_ENVELOPES_REL).get("candidates") or {}
    with np.load(root / R51_ATLAS_REL, allow_pickle=False) as z:
        mass_all = np.asarray(z["population_mass_fraction"], float)

    groups: list[dict[str, Any]] = []
    group_index = 0
    for fam in fams:
        sid = str(fam["candidate_id"])
        j = ids.index(sid)
        fid = str(fam["family_id"])
        core = cores[fid]
        origin_age = float(fam["oldest_supported_age_ma"])
        candidates = np.where(np.isclose(ages, origin_age, atol=1e-12))[0]
        if len(candidates) != 1:
            raise R52Error(f"{fid}: origin age {origin_age} not unique on J14 axis")
        origin_idx = int(candidates[0])
        source_orig = np.zeros((nr, nc), dtype=bool)
        for cell in core:
            source_orig[cell // nc, cell % nc] = True
        source_orig &= targets[j, origin_idx]
        if not source_orig.any():
            raise R52Error(f"{fid}: reconstructed q99 core has no J14 occupancy at oldest supported age")
        center_col = _circular_source_col(core, nc, mass_all[j])
        roll_cols = int(nc // 2 - center_col)

        envelope = envelopes.get(sid) or {}
        for profile in HABITAT_PROFILES:
            group_index += 1
            gid = f"R52_G{group_index:03d}_{fid}_{'LAND' if profile.startswith('LAND') else 'ENVCORE'}"
            gdir = work / gid
            inputs = gdir / "Inputs"
            evidence = gdir / "Evidence"
            inputs.mkdir(parents=True, exist_ok=True)
            evidence.mkdir(parents=True, exist_ok=True)

            subenv = {k: v[origin_idx:] for k, v in env.items()}
            habitat = _habitat_mask(profile, subenv, envelope)
            habitat = np.roll(habitat, roll_cols, axis=2)
            source = np.roll(source_orig, roll_cols, axis=1)
            source &= habitat[0]
            enough_time_states = (len(ages) - origin_idx) >= 2
            executable = bool(source.any()) and enough_time_states
            if not source.any():
                nonexec_reason = "SOURCE_CORE_HAS_NO_CELL_INSIDE_THIS_PRE_FROZEN_HABITAT_PROFILE_AT_ORIGIN_AGE"
            elif not enough_time_states:
                nonexec_reason = "ORIGIN_IS_FINAL_200KA_STATE_NO_EXPANSION_TRANSITION_TO_CHALLENGE"
            else:
                nonexec_reason = None

            file_records: dict[str, Any] = {}
            if executable:
                for k in range(habitat.shape[0]):
                    name = f"habitat_{k:03d}.asc"
                    p = inputs / name
                    codes = np.where(habitat[k], 1, 2).astype(np.uint8)
                    _write_ascii_grid(p, codes)
                    file_records[name] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
                sp = inputs / "source.asc"
                _write_ascii_grid(sp, source.astype(np.uint8))
                file_records[sp.name] = {"bytes": sp.stat().st_size, "sha256": sha256_file(sp)}
            input_manifest = {
                "stage": STAGE,
                "group_id": gid,
                "status": "R52_RANGE_INPUT_GROUP_READY" if executable else "R52_RANGE_INPUT_GROUP_NOT_APPLICABLE",
                "files": file_records,
            }
            write_json(gdir / "GROUP_INPUT_MANIFEST.json", input_manifest)

            group = {
                "group_id": gid,
                "group_numeric_id": group_index,
                "candidate_id": sid,
                "family_id": fid,
                "habitat_profile": profile,
                "origin_age_ma": origin_age,
                "origin_age_index": origin_idx,
                "final_age_ma": float(ages[-1]),
                "age_state_count": int(len(ages) - origin_idx),
                "engine_years": int(len(ages) - origin_idx - 1),
                "engine_step_kyr": ENGINE_STEP_KYR,
                "time_mapping_semantics": "ONE_RANGESHIFTR_ENGINE_YEAR_EQUALS_ONE_ARCANA_20_KYR_STATE_TRANSITION_FOR_INDEXED_CONNECTIVITY_CHALLENGE_NOT_LITERAL_BIOLOGICAL_YEAR",
                "space_mapping_semantics": "ONE_ARCANA_GRID_CELL_EQUALS_ONE_NORMALIZED_RANGESHIFTR_CELL; RESOLUTION_100_ENGINE_METERS_IS_COMPUTATIONAL_NOT_GEODESIC; LONGITUDE_ROLLED_PER_FAMILY_TO_MOVE_SEAM_AWAY_FROM_SOURCE",
                "roll_columns": roll_cols,
                "source_cell_count_before_profile": int(source_orig.sum()),
                "source_cell_count": int(source.sum()),
                "executable": executable,
                "nonexecution_reason": nonexec_reason,
                "movement_profiles": dict(MOVEMENT_PROFILES),
                "seeds": list(SEEDS),
                "expected_stream_count": len(MOVEMENT_PROFILES) * len(SEEDS) if executable else 0,
                "input_dir": str(inputs.relative_to(root)).replace("\\", "/"),
                "evidence_dir": str(evidence.relative_to(root)).replace("\\", "/"),
                "input_manifest_sha256": sha256_file(gdir / "GROUP_INPUT_MANIFEST.json"),
                "habitat_semantic_sha256": semantic_sha256(habitat.astype(np.uint8)),
                "source_semantic_sha256": semantic_sha256(source.astype(np.uint8)),
            }
            write_json(gdir / "GROUP_CONFIG.json", group)
            groups.append(group)

    plan = {
        "stage": STAGE,
        "status": "PASS_R52_TARGETED_RANGESHIFTER_EXECUTION_PLAN_PREPARED",
        "scientific_parent_mode": not allow_non_scientific_dev_parent,
        "objective": "TARGETED_EXPANSION_CORRIDOR_VALIDATION_OF_R51_ROBUST_CRADLE_FAMILIES_USING_RANGESHIFTR_AS_GOVERNED_DESCRIPTIVE_SUPPORT",
        "candidate_ids": list(CANDIDATES),
        "robust_family_count": len(fams),
        "habitat_profiles": list(HABITAT_PROFILES),
        "movement_profiles": dict(MOVEMENT_PROFILES),
        "seeds": list(SEEDS),
        "group_count": len(groups),
        "executable_group_count": sum(bool(g["executable"]) for g in groups),
        "nonexecutable_group_count": sum(not bool(g["executable"]) for g in groups),
        "planned_stream_count": sum(int(g["expected_stream_count"]) for g in groups),
        "replicates_per_stream": 1,
        "range_multi_replicate_occupancy_output_used": False,
        "occupancy_readout": "ENGINE_NATIVE_PER_YEAR_POPULATION_OUTPUT_X_Y_NIND",
        "r41_parameter_reuse": {
            "Rmax": RMAX,
            "EmigProb": EMIGRATION_PROBABILITY,
            "K": HABITAT_CARRYING_CAPACITY,
            "reason": "Reuse governed executable R4.1 RangeShiftR demographic/dispersal path; R5.2-R1 corrects only the initialisation mode so the already-frozen SpDistFile source mask is actually authoritative.",
        },
        "source_initialization_contract": {
            "mode": RANGESHIFTER_INITIALIZATION_MODE,
            "InitType": RANGESHIFTER_INIT_TYPE,
            "SpType": RANGESHIFTER_SP_TYPE,
            "InitDens": RANGESHIFTER_INIT_DENS,
            "source": "GROUP_INPUT_SOURCE_ASC_SPDISTFILE",
            "repair_semantics": "R52_R1_REPAIR_FREE_INITIALISATION_DEFECT_NO_ORIGIN_HABITAT_MOVEMENT_SEED_OR_TARGET_CHANGED",
        },
        "selection_rules": {
            "single_corridor_winner_selected": False,
            "result_selected_tuning": False,
            "majority_vote": False,
            "external_engine_defines_arcana_target": False,
            "engine_numeric_output_causes_automatic_scientific_pass_fail": False,
        },
        "canonical_state_changed": False,
        "deep_biological_coupling": False,
        "groups": groups,
    }
    plan_path = out / "R5_2_RANGE_EXECUTION_PLAN.json"
    write_json(plan_path, plan)
    return {"authority": auth, "plan": plan, "plan_path": plan_path, "plan_sha256": sha256_file(plan_path)}


def _read_tsv(path: Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _read_occupancy(path: Path) -> list[dict[str, str]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _read_group_source_unrolled(root: Path, group: dict[str, Any], nr: int, nc: int) -> tuple[np.ndarray, bool]:
    """Read the exact frozen source.asc and invert only the writer's flip/roll."""
    p = Path(root) / str(group["input_dir"]) / "source.asc"
    if not p.is_file():
        raise R52Error(f"{group.get('group_id')}: source.asc missing")
    lines = p.read_text(encoding="utf-8").splitlines()
    if len(lines) < 6 + nr:
        raise R52Error(f"{group.get('group_id')}: malformed source.asc")
    header = {}
    for line in lines[:6]:
        parts = line.split()
        if len(parts) >= 2:
            header[parts[0].lower()] = parts[1]
    if int(float(header.get("nrows", -1))) != nr or int(float(header.get("ncols", -1))) != nc:
        raise R52Error(f"{group.get('group_id')}: source.asc shape mismatch")
    data = np.loadtxt(p, skiprows=6, dtype=float)
    if data.shape != (nr, nc):
        raise R52Error(f"{group.get('group_id')}: source.asc data shape mismatch {data.shape}")
    rolled = np.flipud(data) > 0
    semantic_ok = semantic_sha256(rolled.astype(np.uint8)) == str(group.get("source_semantic_sha256"))
    unrolled = np.roll(rolled, -int(group["roll_columns"]), axis=1)
    return unrolled, semantic_ok


def _stream_key(row: dict[str, str]) -> tuple[str, int]:
    return str(row["movement_profile"]), int(row["seed"])


def _decode_engine_xy_exact_source(
    raw_rows: list[tuple[int, float, float, float]],
    expected_source: set[int],
    nr: int,
    nc: int,
    roll: int,
) -> dict[str, Any]:
    """Resolve RangeShiftR x/y file semantics only by exact year-0 source recovery.

    This is a file-format binding check, never corridor result selection. Exactly one
    supported mapping must reconstruct the frozen ARCANA source mask.
    """
    def decode(mode: str, reflect_y: bool) -> tuple[dict[int, set[int]], dict[int, float], bool]:
        by: dict[int, set[int]] = {}
        ab: dict[int, float] = {}
        valid = True
        for year, x, y, nind in raw_rows:
            if mode == "INDEX":
                cr = int(round(x)); rr0 = int(round(y))
            elif mode == "RESOLUTION_FLOOR":
                cr = int(math.floor(x / ENGINE_GRID_RESOLUTION + 1e-12))
                rr0 = int(math.floor(y / ENGINE_GRID_RESOLUTION + 1e-12))
            else:
                raise AssertionError(mode)
            rr1 = nr - 1 - rr0 if reflect_y else rr0
            if not (0 <= rr1 < nr and 0 <= cr < nc):
                valid = False
                continue
            ca = (cr - roll) % nc
            by.setdefault(year, set()).add(rr1 * nc + ca)
            ab[year] = ab.get(year, 0.0) + nind
        return by, ab, valid

    decoded = []
    for mode in ("INDEX", "RESOLUTION_FLOOR"):
        for reflect_y in (False, True):
            by0, ab0, valid0 = decode(mode, reflect_y)
            if valid0 and by0.get(0, set()) == expected_source:
                decoded.append((mode, reflect_y, by0, ab0))
    if len(decoded) != 1:
        return {
            "exact": False,
            "coordinate_mode": "UNRESOLVED" if not decoded else "AMBIGUOUS",
            "y_reflected": None,
            "by_year": decoded[0][2] if decoded else {},
            "abundance_by_year": decoded[0][3] if decoded else {},
            "matching_mapping_count": len(decoded),
        }
    mode, reflect_y, by, ab = decoded[0]
    return {
        "exact": True,
        "coordinate_mode": mode,
        "y_reflected": reflect_y,
        "by_year": by,
        "abundance_by_year": ab,
        "matching_mapping_count": 1,
    }


def validate_source_binding_probe(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    out = root / OUT_REL
    plan = load_json(out / "R5_2_RANGE_EXECUTION_PLAN.json")
    probe_tsv = out / "source_binding_probe" / "Evidence" / "SOURCE_BINDING_PROBE.tsv"
    if not probe_tsv.is_file():
        raise R52Error("R5.2-R1 source binding probe output missing")
    executable = [g for g in (plan.get("groups") or []) if g.get("executable") is True]
    if not executable:
        raise R52Error("R5.2-R1 has no executable group for source binding probe")
    group = executable[0]
    fams, cores, lat, lon = reconstruct_robust_family_cores(root)
    nr, nc = len(lat), len(lon)
    ages, ids, targets = _load_j14_targets(root, nr, nc)
    j = ids.index(str(group["candidate_id"]))
    origin_idx = int(group["origin_age_index"])
    source_orig = np.zeros((nr, nc), dtype=bool)
    for cell in cores[str(group["family_id"])]:
        source_orig[cell // nc, cell % nc] = True
    source_orig &= targets[j, origin_idx]
    source_input, source_semantic_ok = _read_group_source_unrolled(root, group, nr, nc)
    source_subset_ok = bool(np.all(~source_input | source_orig))
    expected_source = {int(r * nc + c) for r, c in zip(*np.where(source_input))}
    raw_rows: list[tuple[int, float, float, float]] = []
    for rr in _read_tsv(probe_tsv):
        raw_rows.append((int(float(rr["Year"])), float(rr["x"]), float(rr["y"]), float(rr.get("NInd", "0") or 0.0)))
    decoded = _decode_engine_xy_exact_source(raw_rows, expected_source, nr, nc, int(group["roll_columns"]))
    checks = {
        "initialization_mode_exact": RANGESHIFTER_INITIALIZATION_MODE == "SPDIST_INITTYPE1_SPTYPE0",
        "source_input_semantic_hash_exact": source_semantic_ok,
        "source_input_subset_of_r51_j14_origin": source_subset_ok,
        "probe_has_year_zero_population": any(y == 0 and n > 0 for y, x, yy, n in raw_rows),
        "probe_year_zero_source_mapping_exact": bool(decoded["exact"]),
        "probe_mapping_unique": int(decoded["matching_mapping_count"]) == 1,
    }
    checks = {k: bool(v) for k, v in checks.items()}
    failed = [k for k, v in checks.items() if not v]
    result = {
        "stage": STAGE,
        "status": "PASS_R52_R1_SOURCE_BINDING_PREFLIGHT" if not failed else "BLOCKED_R52_R1_SOURCE_BINDING_PREFLIGHT",
        "group_id": group["group_id"],
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failed": failed,
        "checks": checks,
        "coordinate_mode": decoded["coordinate_mode"],
        "y_reflected": decoded["y_reflected"],
        "expected_source_cell_count": len(expected_source),
        "probe_year_zero_cell_count": len((decoded["by_year"] or {}).get(0, set())),
        "initialization_mode": RANGESHIFTER_INITIALIZATION_MODE,
    }
    write_json(out / "R5_2_R1_SOURCE_BINDING_PREFLIGHT.json", result)
    return result


def analyze_rangeshifter_evidence(root: Path, allow_non_scientific_dev_parent: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    out = root / OUT_REL
    auth = validate_parent_authority(root, allow_non_scientific_dev=allow_non_scientific_dev_parent)
    if auth["failed"]:
        raise R52Error("R5.2 parent authority failed before evidence analysis")
    plan_path = out / "R5_2_RANGE_EXECUTION_PLAN.json"
    runtime_path = out / "R5_2_RANGESHIFTER_RUNTIME_IDENTITY.json"
    if not plan_path.is_file() or not runtime_path.is_file():
        raise R52Error("R5.2 execution plan or runtime identity missing")
    bridge_path = out / "R5_2_RANGE_EXECUTION_BRIDGE.json"
    if not bridge_path.is_file():
        raise R52Error("R5.2 PowerShell->WSL execution bridge evidence missing")
    plan = load_json(plan_path)
    runtime = load_json(runtime_path)
    bridge = load_json(bridge_path)
    if runtime.get("status") != "PASS_R52_RANGESHIFTR_3_0_1_RUNTIME_IDENTITY" or runtime.get("package_version") != "3.0.1":
        raise R52Error("RangeShiftR runtime identity is not exact 3.0.1")

    fams, cores, lat, lon = reconstruct_robust_family_cores(root)
    nr, nc = len(lat), len(lon)
    ages, ids, targets = _load_j14_targets(root, nr, nc)

    stream_records: list[dict[str, Any]] = []
    raw_files: dict[str, Any] = {}
    group_checks: dict[str, Any] = {}
    expected_combo = {(m, s) for m in MOVEMENT_PROFILES for s in SEEDS}

    for group in plan.get("groups") or []:
        gid = str(group["group_id"])
        if not group.get("executable"):
            group_checks[gid] = {
                "executable": False,
                "reason": group.get("nonexecution_reason"),
                "expected_stream_count": 0,
                "actual_stream_count": 0,
                "execution_integrity": True,
            }
            continue
        gdir = root / str(Path(group["evidence_dir"]).parent)
        evidence_dir = root / group["evidence_dir"]
        summary_path = evidence_dir / "STREAM_SUMMARY.tsv"
        if not summary_path.is_file():
            group_checks[gid] = {"executable": True, "execution_integrity": False, "reason": "STREAM_SUMMARY_MISSING"}
            continue
        rows = _read_tsv(summary_path)
        combos = {_stream_key(r) for r in rows}
        integrity = len(rows) == len(expected_combo) and combos == expected_combo and all(r.get("execution_status") == "PASS" for r in rows)
        raw_files[str(summary_path.relative_to(root)).replace("\\", "/")] = {
            "bytes": summary_path.stat().st_size,
            "sha256": sha256_file(summary_path),
        }

        j = ids.index(str(group["candidate_id"]))
        origin_idx = int(group["origin_age_index"])
        roll = int(group["roll_columns"])
        source_orig = np.zeros((nr, nc), dtype=bool)
        for cell in cores[str(group["family_id"])]:
            source_orig[cell // nc, cell % nc] = True
        source_orig &= targets[j, origin_idx]
        source_input, source_semantic_ok = _read_group_source_unrolled(root, group, nr, nc)
        source_subset_ok = bool(np.all(~source_input | source_orig))
        expected_source = {int(r * nc + c) for r, c in zip(*np.where(source_input))}

        for row in rows:
            mov = str(row["movement_profile"])
            seed = int(row["seed"])
            occ_rel = row.get("occupancy_file") or ""
            occ_path = evidence_dir / occ_rel
            if row.get("execution_status") != "PASS" or not occ_path.is_file():
                integrity = False
                continue
            raw_files[str(occ_path.relative_to(root)).replace("\\", "/")] = {
                "bytes": occ_path.stat().st_size,
                "sha256": sha256_file(occ_path),
            }
            occ_rows = _read_occupancy(occ_path)
            raw_rows: list[tuple[int, float, float, float]] = []
            for rr in occ_rows:
                try:
                    raw_rows.append((int(float(rr["Year"])), float(rr["x"]), float(rr["y"]), float(rr.get("NInd", "0") or 0.0)))
                except Exception:
                    integrity = False
            # Decode the engine's x/y representation by requiring exact recovery
            # of the frozen ARCANA source mask at engine year 0. This is a file-
            # format mapping check, not result-selected corridor tuning.
            decoded = _decode_engine_xy_exact_source(raw_rows, expected_source, nr, nc, roll)
            coordinate_mode = decoded["coordinate_mode"]
            y_reflected = decoded["y_reflected"]
            by_year = decoded["by_year"]
            abund_by_year = decoded["abundance_by_year"]
            initial_source_match = bool(decoded["exact"])
            if not initial_source_match:
                integrity = False
            integrity = integrity and initial_source_match

            nstates = int(group["age_state_count"])
            intersects = []
            target_cov = []
            precision = []
            jaccard = []
            populated = []
            for k in range(nstates):
                eng = by_year.get(k, set())
                targ_rc = np.argwhere(targets[j, origin_idx + k])
                targ = {int(r * nc + c) for r, c in targ_rc}
                inter = len(eng & targ)
                union = len(eng | targ)
                intersects.append(inter > 0)
                target_cov.append(float(inter / len(targ)) if targ else 0.0)
                precision.append(float(inter / len(eng)) if eng else 0.0)
                jaccard.append(float(inter / union) if union else 0.0)
                populated.append(bool(eng))
            first_hit = next((i for i, v in enumerate(intersects) if v), None)
            final_k = nstates - 1
            rec = {
                "group_id": gid,
                "candidate_id": str(group["candidate_id"]),
                "family_id": str(group["family_id"]),
                "habitat_profile": str(group["habitat_profile"]),
                "movement_profile": mov,
                "characteristic_transfer_distance_engine_units": float(MOVEMENT_PROFILES[mov]),
                "seed": seed,
                "execution_status": row.get("execution_status"),
                "package_version": row.get("package_version"),
                "initialization_mode": row.get("initialization_mode"),
                "initial_source_mapping_exact": bool(initial_source_match),
                "engine_coordinate_mode": coordinate_mode,
                "engine_y_reflected": y_reflected,
                "completed_engine_years": int(float(row.get("completed_engine_years") or 0)),
                "global_extinction_before_final": str(row.get("global_extinction_before_final", "FALSE")).strip().upper() == "TRUE",
                "origin_age_ma": float(group["origin_age_ma"]),
                "final_age_ma": float(group["final_age_ma"]),
                "mapped_state_count": nstates,
                "states_with_engine_population": int(sum(populated)),
                "population_state_fraction": float(np.mean(populated)),
                "states_with_arcana_target_intersection": int(sum(intersects)),
                "arcana_target_intersection_state_fraction": float(np.mean(intersects)),
                "first_target_intersection_engine_year": first_hit,
                "first_target_intersection_age_ma": float(ages[origin_idx + first_hit]) if first_hit is not None else None,
                "final_target_intersection": bool(intersects[final_k]),
                "final_target_coverage_fraction": float(target_cov[final_k]),
                "final_engine_precision_fraction": float(precision[final_k]),
                "max_jaccard": float(max(jaccard) if jaccard else 0.0),
                "median_jaccard": float(np.median(jaccard) if jaccard else 0.0),
                "max_target_coverage_fraction": float(max(target_cov) if target_cov else 0.0),
                "final_abundance_engine_native": float(abund_by_year.get(final_k, 0.0)),
                "scientific_semantics": "GOVERNED_DESCRIPTIVE_RANGESHIFTER_CONNECTIVITY_EVIDENCE_NOT_CANONICAL_CORRIDOR_TRUTH",
            }
            stream_records.append(rec)

        integrity = integrity and source_semantic_ok and source_subset_ok
        group_checks[gid] = {
            "executable": True,
            "expected_stream_count": len(expected_combo),
            "actual_stream_count": len(rows),
            "stream_combo_membership_exact": combos == expected_combo,
            "all_stream_execution_status_pass": all(r.get("execution_status") == "PASS" for r in rows),
            "source_input_semantic_hash_exact": bool(source_semantic_ok),
            "source_input_subset_of_r51_j14_origin": bool(source_subset_ok),
            "execution_integrity": bool(integrity),
        }

    expected_stream_count = int(plan.get("planned_stream_count", -1))
    execution_integrity = (
        len(stream_records) == expected_stream_count
        and all(bool(g.get("execution_integrity")) for g in group_checks.values())
        and all(r.get("package_version") == "3.0.1" for r in stream_records)
    )

    # Fixed sensitivity aggregation; no voting or winner selection.
    sensitivity: list[dict[str, Any]] = []
    by_key: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for r in stream_records:
        key = (r["candidate_id"], r["family_id"], r["habitat_profile"], r["movement_profile"])
        by_key.setdefault(key, []).append(r)
    for key in sorted(by_key):
        rs = sorted(by_key[key], key=lambda x: x["seed"])
        sensitivity.append({
            "candidate_id": key[0],
            "family_id": key[1],
            "habitat_profile": key[2],
            "movement_profile": key[3],
            "seed_membership": [r["seed"] for r in rs],
            "seed_membership_exact": tuple(r["seed"] for r in rs) == SEEDS,
            "both_seeds_final_target_intersection": all(bool(r["final_target_intersection"]) for r in rs),
            "any_seed_final_target_intersection": any(bool(r["final_target_intersection"]) for r in rs),
            "target_intersection_state_fraction_minmax": [
                float(min(r["arcana_target_intersection_state_fraction"] for r in rs)),
                float(max(r["arcana_target_intersection_state_fraction"] for r in rs)),
            ],
            "max_jaccard_minmax": [float(min(r["max_jaccard"] for r in rs)), float(max(r["max_jaccard"] for r in rs))],
            "max_target_coverage_fraction_minmax": [
                float(min(r["max_target_coverage_fraction"] for r in rs)),
                float(max(r["max_target_coverage_fraction"] for r in rs)),
            ],
            "automatic_scientific_pass_fail_from_values": False,
        })

    write_json(out / "R5_2_STREAM_EVIDENCE.json", {
        "stage": STAGE,
        "status": "R52_GOVERNED_RANGESHIFTER_STREAM_EVIDENCE",
        "semantics": "RAW_AND_DERIVED_DESCRIPTIVE_CONNECTIVITY_READOUT_NOT_CANONICAL_TARGET_ADJUDICATION",
        "records": stream_records,
    })
    write_json(out / "R5_2_CORRIDOR_SENSITIVITY_SUMMARY.json", {
        "stage": STAGE,
        "status": "R52_FIXED_SENSITIVITY_FAMILY_SUMMARY",
        "habitat_profiles": list(HABITAT_PROFILES),
        "movement_profiles": dict(MOVEMENT_PROFILES),
        "seeds": list(SEEDS),
        "selection_semantics": "NO_WEIGHTED_SCORE_NO_MAJORITY_VOTE_NO_SINGLE_WINNER_NO_AUTOMATIC_NUMERIC_PASS_FAIL",
        "records": sensitivity,
    })
    write_json(out / "R5_2_RAW_EVIDENCE_MANIFEST.json", {
        "stage": STAGE,
        "status": "R52_RAW_RANGESHIFTER_EVIDENCE_CORPUS_MANIFEST",
        "file_count": len(raw_files),
        "files": raw_files,
    })

    checks = {
        "parent_authority_pass": not auth["failed"],
        "runtime_exact_3_0_1": runtime.get("package_version") == "3.0.1",
        "runtime_status_pass": runtime.get("status") == "PASS_R52_RANGESHIFTR_3_0_1_RUNTIME_IDENTITY",
        "powershell_wsl_bridge_status_exact": bridge.get("status") == "R52_POWERSHELL_WSL_RANGESHIFTER_EXECUTION_BRIDGE",
        "powershell_wsl_bridge_group_count_exact": int(bridge.get("group_count", -1)) == int(plan.get("executable_group_count", -2)),
        "powershell_wsl_bridge_all_exit_zero": all(int(x.get("exit_code", -1)) == 0 and x.get("timed_out") is False for x in (bridge.get("records") or [])),
        "r51_robust_family_count_exact": int(plan.get("robust_family_count", -1)) == EXPECTED_ROBUST_FAMILY_COUNT,
        "habitat_profile_family_exact": tuple(plan.get("habitat_profiles") or []) == HABITAT_PROFILES,
        "movement_profile_family_exact": dict(plan.get("movement_profiles") or {}) == MOVEMENT_PROFILES,
        "seed_membership_exact": tuple(plan.get("seeds") or []) == SEEDS,
        "source_initialization_contract_exact": (plan.get("source_initialization_contract") or {}) == {
            "mode": RANGESHIFTER_INITIALIZATION_MODE,
            "InitType": RANGESHIFTER_INIT_TYPE,
            "SpType": RANGESHIFTER_SP_TYPE,
            "InitDens": RANGESHIFTER_INIT_DENS,
            "source": "GROUP_INPUT_SOURCE_ASC_SPDISTFILE",
            "repair_semantics": "R52_R1_REPAIR_FREE_INITIALISATION_DEFECT_NO_ORIGIN_HABITAT_MOVEMENT_SEED_OR_TARGET_CHANGED",
        },
        "all_stream_source_initialization_mode_exact": all(r.get("initialization_mode") == RANGESHIFTER_INITIALIZATION_MODE for r in stream_records),
        "planned_stream_count_matches_evidence": len(stream_records) == expected_stream_count,
        "all_group_execution_integrity": all(bool(g.get("execution_integrity")) for g in group_checks.values()),
        "all_stream_runtime_version_exact": all(r.get("package_version") == "3.0.1" for r in stream_records),
        "all_initial_source_mappings_exact": all(bool(r.get("initial_source_mapping_exact")) for r in stream_records),
        "no_majority_vote": (plan.get("selection_rules") or {}).get("majority_vote") is False,
        "no_result_selected_tuning": (plan.get("selection_rules") or {}).get("result_selected_tuning") is False,
        "no_single_corridor_winner": (plan.get("selection_rules") or {}).get("single_corridor_winner_selected") is False,
        "engine_does_not_define_arcana_target": (plan.get("selection_rules") or {}).get("external_engine_defines_arcana_target") is False,
        "no_automatic_numeric_scientific_pass_fail": (plan.get("selection_rules") or {}).get("engine_numeric_output_causes_automatic_scientific_pass_fail") is False,
        "canonical_state_unchanged": plan.get("canonical_state_changed") is False,
        "deep_biological_coupling_off": plan.get("deep_biological_coupling") is False,
    }
    checks = {k: bool(v) for k, v in checks.items()}
    failed = [k for k, v in checks.items() if not v]
    scientific = bool(not allow_non_scientific_dev_parent and not failed)
    status = (
        "PASS_R52_TARGETED_RANGESHIFTER_EXPANSION_CORRIDOR_EVIDENCE_CANDIDATE"
        if scientific
        else "PASS_R52_NON_SCIENTIFIC_DEV_EVIDENCE_VALIDATION"
        if (allow_non_scientific_dev_parent and not failed)
        else "BLOCKED_R52_TARGETED_RANGESHIFTER_EVIDENCE"
    )
    audit = {
        "stage": STAGE,
        "status": status,
        "scientific_candidate_eligible": scientific,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failed": failed,
        "summary": {
            "robust_family_count": int(plan.get("robust_family_count", -1)),
            "group_count": int(plan.get("group_count", -1)),
            "executable_group_count": int(plan.get("executable_group_count", -1)),
            "nonexecutable_group_count": int(plan.get("nonexecutable_group_count", -1)),
            "scientific_stream_count": len(stream_records),
            "raw_evidence_file_count": len(raw_files),
            "sensitivity_record_count": len(sensitivity),
            "new_external_engine_execution_performed": True,
            "external_engine": "RangeShiftR",
            "external_engine_version": "3.0.1",
            "numeric_corridor_truth_claimed": False,
            "external_engine_defines_arcana_target": False,
            "majority_vote": False,
            "canonical_state_changed": False,
            "derived_refinement_promoted_to_canon": False,
            "deep_biological_coupling": False,
            "corridor_semantics": "RANGESHIFTER_GOVERNED_DESCRIPTIVE_CONNECTIVITY_EVIDENCE_AGAINST_ARCANA_DEFINED_ORIGINS_AND_TARGET_OCCUPANCY",
        },
        "group_execution_integrity": group_checks,
        "checks": checks,
    }
    write_json(out / "R5_2_INTEGRATED_AUDIT.json", audit)

    key_names = (
        "R5_2_RANGESHIFTER_RUNTIME_IDENTITY.json",
        "R5_2_RANGE_EXECUTION_PLAN.json",
        "R5_2_RANGE_EXECUTION_BRIDGE.json",
        "R5_2_RAW_EVIDENCE_MANIFEST.json",
        "R5_2_STREAM_EVIDENCE.json",
        "R5_2_CORRIDOR_SENSITIVITY_SUMMARY.json",
        "R5_2_INTEGRATED_AUDIT.json",
    )
    files = {}
    for name in key_names:
        p = out / name
        if p.is_file():
            files[name] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
    write_json(out / "R5_2_OUTPUT_MANIFEST.json", {"stage": STAGE, "status": status, "files": files})
    return {"audit": audit, "stream_records": stream_records, "sensitivity": sensitivity}
