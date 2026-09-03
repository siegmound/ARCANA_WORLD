from __future__ import annotations

from pathlib import Path
from typing import Any
import csv
import hashlib
import json
import math
import shutil

import numpy as np

from arcana_worldsim.state_query import r52_corridors as r52

STAGE = "v0.6D1-R5.3"
OUT_REL = Path("outputs/v0_6D1_R5_3")
R52_OUT_REL = Path("outputs/v0_6D1_R5_2")
R52_FINAL_SEAL_REL = R52_OUT_REL / "R5_2_FINAL_SEAL.json"
R52_PLAN_REL = R52_OUT_REL / "R5_2_RANGE_EXECUTION_PLAN.json"
R52_RAW_MANIFEST_REL = R52_OUT_REL / "R5_2_RAW_EVIDENCE_MANIFEST.json"
R52_OUTPUT_MANIFEST_REL = R52_OUT_REL / "R5_2_OUTPUT_MANIFEST.json"
R52_SENSITIVITY_REL = R52_OUT_REL / "R5_2_CORRIDOR_SENSITIVITY_SUMMARY.json"
R52_READOUT_REL = R52_OUT_REL / "R5_2_EVIDENCE_STRUCTURE_AND_NEXT_ENGINE_ADJUDICATION.json"
R51_FAMILIES_REL = Path("outputs/v0_6D1_R5_1/R5_1_ROBUST_REGION_FAMILIES.json")
J14_REL = r52.J14_REL
SOURCE_MANIFEST_REL = Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_3.json")
ENGINE_ROOT_REL = Path(".arcana_engines/CDMetaPOP-3.08")
HISTORICAL_R421_ADAPTER_REL = Path("benchmarks/r421/cdmetapop_r421_matched.py")

EXPECTED_R52_FINAL_SEAL_SHA256 = "6881b7312d7edf1539737d5603455d66712def05fcf4ddc133ae4d63cfde9978"
EXPECTED_R52_PLAN_SHA256 = "49704d285c416714c0c262769e97b34300004be268482a806cd8d9baf4f990dd"
EXPECTED_R52_RAW_MANIFEST_SHA256 = "f5df7bc971e895289cb5e74baa9d306be76dce39a108d93d31b738e55998613c"
EXPECTED_R52_OUTPUT_MANIFEST_SHA256 = "ec91dd7793668138d9daba8b68d5845956e4aa15d2879abd809165254014539c"
EXPECTED_CDMETAPOP_COMMIT = "3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118"
EXPECTED_CDMETAPOP_VERSION = "3.08"
EXPECTED_ROBUST_FAMILY_COUNT = 12
AUTHORIZED_CDMETAPOP_FIELDS = ("Year", "N_Initial", "Alleles", "He", "Ho")

# Standardized diagnostic stress profiles. These are engine-native challenge
# census values, never literal ARCANA individual counts or historical K.
DEMOGRAPHIC_STRESS_PROFILES: dict[str, dict[str, int]] = {
    "D0_STANDARDIZED_BASELINE": {"source_n0": 60, "patch_k": 120},
    "D1_STANDARDIZED_MODERATE_BOTTLENECK": {"source_n0": 30, "patch_k": 90},
    "D2_STANDARDIZED_SEVERE_BOTTLENECK": {"source_n0": 12, "patch_k": 60},
}
SEEDS = (530301, 530302)
ENGINE_RUNTIME_GENERATIONS = 40
MAX_PATCHES_PER_FAMILY = 32
NEUTRAL_LOCI = 16
NEUTRAL_ALLELES = 2
DISPERSAL_PROBABILITY = 0.25
DISTANCE_SCALE_CELLS = 2.0
ENGINE_COORDINATE_SCALE = 100.0


class R53Error(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def semantic_sha256(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _verify_manifest(root: Path, rel: Path) -> bool:
    p = Path(root) / rel
    if not p.is_file():
        return False
    try:
        m = load_json(p)
        files = dict(m.get("files") or {})
        if not files:
            return False
        base = p.parent
        for name, meta in files.items():
            fp = base / name
            if not fp.is_file() or fp.stat().st_size != int(meta.get("bytes", -1)) or sha256_file(fp) != meta.get("sha256"):
                return False
        return True
    except Exception:
        return False


def validate_parent_authority(root: Path, allow_non_scientific_dev: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    strict = not allow_non_scientific_dev
    r52seal = root / R52_FINAL_SEAL_REL
    checks: dict[str, bool] = {
        "present::r52_final_seal": r52seal.is_file(),
        "present::r52_plan": (root / R52_PLAN_REL).is_file(),
        "present::r52_raw_manifest": (root / R52_RAW_MANIFEST_REL).is_file(),
        "present::r52_output_manifest": (root / R52_OUTPUT_MANIFEST_REL).is_file(),
        "present::r52_sensitivity": (root / R52_SENSITIVITY_REL).is_file(),
        "present::r52_readout": (root / R52_READOUT_REL).is_file(),
        "present::r51_families": (root / R51_FAMILIES_REL).is_file(),
        "present::j14": (root / J14_REL).is_file(),
        "present::cdmetapop_engine": (root / ENGINE_ROOT_REL / "src/CDmetaPOP.py").is_file(),
        "present::historical_r421_adapter": (root / HISTORICAL_R421_ADAPTER_REL).is_file(),
    }
    if r52seal.is_file():
        seal = load_json(r52seal)
        s = seal.get("summary") or {}
        checks["r52_seal_semantics"] = (
            seal.get("sealed") is True
            and seal.get("status") == "PASS_R52_TARGETED_EXPANSION_CORRIDOR_VALIDATION_SEALED"
            and int(s.get("robust_family_count", -1)) == EXPECTED_ROBUST_FAMILY_COUNT
            and int(s.get("scientific_stream_count", -1)) == 80
            and s.get("external_engine") == "RangeShiftR"
            and s.get("external_engine_version") == "3.0.1"
            and s.get("numeric_corridor_truth_claimed") is False
            and s.get("external_engine_defines_arcana_target") is False
            and s.get("majority_vote") is False
            and s.get("canonical_state_changed") is False
            and s.get("derived_refinement_promoted_to_canon") is False
            and s.get("deep_biological_coupling") is False
            and s.get("r52_closure_readiness") == "READY_FOR_R52_SEAL_GOVERNED_DESCRIPTIVE_CORRIDOR_EVIDENCE_COMPLETE"
        )
        checks["r52_final_seal_exact_hash"] = (sha256_file(r52seal) == EXPECTED_R52_FINAL_SEAL_SHA256) if strict else True
        authority = seal.get("authority") or {}
        checks["r52_seal_embedded_parent_hashes"] = (
            authority.get("r52_execution_plan_sha256") == EXPECTED_R52_PLAN_SHA256
            and authority.get("r52_raw_evidence_manifest_sha256") == EXPECTED_R52_RAW_MANIFEST_SHA256
            and authority.get("r52_candidate_output_manifest_sha256") == EXPECTED_R52_OUTPUT_MANIFEST_SHA256
        )
    else:
        checks["r52_seal_semantics"] = checks["r52_final_seal_exact_hash"] = checks["r52_seal_embedded_parent_hashes"] = False

    checks["r52_plan_exact_hash"] = (sha256_file(root / R52_PLAN_REL) == EXPECTED_R52_PLAN_SHA256) if strict and (root / R52_PLAN_REL).is_file() else (root / R52_PLAN_REL).is_file()
    checks["r52_raw_manifest_exact_hash"] = (sha256_file(root / R52_RAW_MANIFEST_REL) == EXPECTED_R52_RAW_MANIFEST_SHA256) if strict and (root / R52_RAW_MANIFEST_REL).is_file() else (root / R52_RAW_MANIFEST_REL).is_file()
    checks["r52_output_manifest_exact_hash"] = (sha256_file(root / R52_OUTPUT_MANIFEST_REL) == EXPECTED_R52_OUTPUT_MANIFEST_SHA256) if strict and (root / R52_OUTPUT_MANIFEST_REL).is_file() else (root / R52_OUTPUT_MANIFEST_REL).is_file()
    checks["r52_output_manifest_integrity"] = _verify_manifest(root, R52_OUTPUT_MANIFEST_REL)

    inherited = r52.validate_parent_authority(root, allow_non_scientific_dev=allow_non_scientific_dev)
    checks["r52_inherited_r51_j14_provider_authority_pass"] = not inherited.get("failed")

    try:
        famdoc = load_json(root / R51_FAMILIES_REL)
        robust = [f for f in (famdoc.get("families") or []) if f.get("survives_all_thresholds") is True]
        checks["r51_robust_family_count_exact"] = len(robust) == EXPECTED_ROBUST_FAMILY_COUNT
        checks["r51_candidate_cohort_exact"] = set(f.get("candidate_id") for f in robust) == set(r52.CANDIDATES)
    except Exception:
        checks["r51_robust_family_count_exact"] = False
        checks["r51_candidate_cohort_exact"] = False

    try:
        sens = load_json(root / R52_SENSITIVITY_REL)
        checks["r52_sensitivity_semantics"] = (
            sens.get("status") == "R52_FIXED_SENSITIVITY_FAMILY_SUMMARY"
            and sens.get("selection_semantics") == "NO_WEIGHTED_SCORE_NO_MAJORITY_VOTE_NO_SINGLE_WINNER_NO_AUTOMATIC_NUMERIC_PASS_FAIL"
            and len(sens.get("records") or []) == 40
        )
    except Exception:
        checks["r52_sensitivity_semantics"] = False

    try:
        text = (root / ENGINE_ROOT_REL / "src/CDmetaPOP.py").read_text(encoding="utf-8", errors="replace")
        checks["cdmetapop_source_version_marker_exact"] = 'appVers = "version 3.08"' in text or "appVers = 'version 3.08'" in text
    except Exception:
        checks["cdmetapop_source_version_marker_exact"] = False

    checks = {k: bool(v) for k, v in checks.items()}
    failed = [k for k, v in checks.items() if not v]
    return {
        "stage": STAGE,
        "status": "PASS_R53_IMMUTABLE_PARENT_AUTHORITY" if not failed else "BLOCKED_R53_PARENT_AUTHORITY",
        "scientific_parent_mode": strict,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failed": failed,
        "checks": checks,
        "r52_inherited_parent_authority": inherited,
    }


def _r52_support_by_family(root: Path) -> dict[str, dict[str, Any]]:
    records = list(load_json(Path(root) / R52_SENSITIVITY_REL).get("records") or [])
    by: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        by.setdefault(str(rec["family_id"]), []).append(rec)
    out: dict[str, dict[str, Any]] = {}
    for fid, rows in sorted(by.items()):
        rows = sorted(rows, key=lambda r: (str(r["habitat_profile"]), str(r["movement_profile"])))
        both = sum(bool(r.get("both_seeds_final_target_intersection")) for r in rows)
        anyc = sum(bool(r.get("any_seed_final_target_intersection")) for r in rows)
        if both == len(rows):
            cls = "ALL_EXECUTABLE_SENSITIVITIES_FINAL_INTERSECTION"
        elif both == 0:
            cls = "NO_EXECUTABLE_SENSITIVITY_FINAL_INTERSECTION"
        else:
            cls = "MIXED_EXECUTABLE_SENSITIVITY_FINAL_INTERSECTION"
        out[fid] = {
            "executable_sensitivity_record_count": len(rows),
            "both_seed_final_intersection_record_count": both,
            "any_seed_final_intersection_record_count": anyc,
            "both_seed_final_intersection_fraction": float(both / len(rows)) if rows else 0.0,
            "support_class": cls,
            "used_as_cdmetapop_spatial_geometry": False,
            "used_as_arcana_target_authority": False,
        }
    return out


def _load_j14(root: Path) -> tuple[np.ndarray, tuple[str, ...], np.ndarray]:
    with np.load(Path(root) / J14_REL, allow_pickle=False) as z:
        ages = np.asarray(z["age_ma"], float)
        ids = tuple(map(str, z["candidate_ids"].tolist()))
        spatial = np.asarray(z["spatial_state"], float)
    if ids != r52.CANDIDATES or spatial.shape != (96, 2, 141, 8, 4):
        raise R53Error("J14 schema/candidate authority differs from R5.3 contract")
    return ages, ids, spatial


def _select_network_cells_for_family(
    fam: dict[str, Any], core: set[int], ages: np.ndarray, ids: tuple[str, ...], spatial: np.ndarray, nr: int, nc: int
) -> list[int]:
    sid = str(fam["candidate_id"])
    j = ids.index(sid)
    origin = float(fam["oldest_supported_age_ma"])
    idxs = np.where(np.isclose(ages, origin, atol=1e-12))[0]
    if len(idxs) != 1:
        raise R53Error(f"{fam['family_id']}: origin age not uniquely present in J14")
    origin_idx = int(idxs[0])
    counts: dict[int, int] = {}
    for e in range(spatial.shape[0]):
        for t in range(origin_idx, spatial.shape[2]):
            for row in spatial[e, j, t]:
                if row[3] <= 0.5:
                    continue
                rr = int(np.clip(np.rint(row[1]), 0, nr - 1))
                cc = int(np.clip(np.rint(row[2]), 0, nc - 1))
                cell = rr * nc + cc
                counts[cell] = counts.get(cell, 0) + 1
    if not counts:
        raise R53Error(f"{fam['family_id']}: no downstream J14 occupancy")
    ordered: list[int] = []
    for c in sorted(core):
        if c not in ordered:
            ordered.append(c)
    for c, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        if c not in ordered:
            ordered.append(c)
        if len(ordered) >= MAX_PATCHES_PER_FAMILY:
            break
    if len(ordered) < 2:
        raise R53Error(f"{fam['family_id']}: fewer than two ARCANA/J14 network cells")
    return ordered[:MAX_PATCHES_PER_FAMILY]


def _distance_and_probability(cells: list[int], nr: int, nc: int) -> tuple[np.ndarray, np.ndarray]:
    n = len(cells)
    d = np.zeros((n, n), dtype=float)
    for i, a in enumerate(cells):
        ar, ac = divmod(a, nc)
        for j, b in enumerate(cells):
            br, bc = divmod(b, nc)
            dr = float(ar - br)
            dc0 = abs(ac - bc)
            dc = float(min(dc0, nc - dc0))
            d[i, j] = math.sqrt(dr * dr + dc * dc) * ENGINE_COORDINATE_SCALE
    scale = DISTANCE_SCALE_CELLS * ENGINE_COORDINATE_SCALE
    p = np.exp(-d / max(scale, 1e-12))
    np.fill_diagonal(p, 1.0)
    return d, p


def _read_csv_template(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        rows = list(rd)
        return list(rd.fieldnames or []), rows


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        wr.writeheader()
        for row in rows:
            wr.writerow({k: row.get(k, "") for k in fields})


def _find_template(engine_root: Path, rel: str) -> Path:
    p = engine_root / "example_files" / rel
    if not p.is_file():
        raise R53Error(f"CDMetaPOP pinned example template missing: {p}")
    return p


def _collapse_invariant_template_temporal_values(row: dict[str, str]) -> dict[str, str]:
    """Collapse only invariant pipe-delimited template values for a single-time R5.3 run.

    R5.3 intentionally sets cdclimgentime=0 (no climate/time swapping). Some bundled
    CDMetaPOP 3.08 example PatchVars rows nevertheless contain legacy values such as
    ``155 | 155 | 155``. Leaving those untouched makes CDMetaPOP correctly fail because
    three swapped values are paired with one climate time. We may collapse them only when
    every component is identical; differing components are ambiguous and fail closed.
    """
    out = dict(row)
    for key, raw in list(out.items()):
        if not isinstance(raw, str) or "|" not in raw:
            continue
        parts = [part.strip() for part in raw.split("|")]
        if not parts or any(part == "" for part in parts):
            raise R53Error(f"Malformed pipe-delimited CDMetaPOP template value for {key}: {raw!r}")
        if len(set(parts)) != 1:
            raise R53Error(
                f"R5.3 forbids implicit temporal-template selection with cdclimgentime=0: "
                f"{key}={raw!r}"
            )
        out[key] = parts[0]
    return out


def _build_cdmetapop_input_group(
    root: Path,
    group_dir: Path,
    cells: list[int],
    core: set[int],
    stress: dict[str, int],
    nr: int,
    nc: int,
) -> dict[str, Any]:
    engine = root / ENGINE_ROOT_REL
    run_fields, run_rows = _read_csv_template(_find_template(engine, "RunVars.csv"))
    pop_fields, pop_rows = _read_csv_template(_find_template(engine, "popvars/PopVars.csv"))
    patch_fields, patch_rows = _read_csv_template(_find_template(engine, "patchvars/PatchVars.csv"))
    class_src = _find_template(engine, "classvars/ClassVars_AS1.csv")
    if not run_rows or not pop_rows or not patch_rows:
        raise R53Error("CDMetaPOP template rows missing")

    inp = group_dir / "Inputs"
    (inp / "popvars").mkdir(parents=True, exist_ok=True)
    (inp / "patchvars").mkdir(parents=True, exist_ok=True)
    (inp / "classvars").mkdir(parents=True, exist_ok=True)
    (inp / "cdmats").mkdir(parents=True, exist_ok=True)
    shutil.copy2(class_src, inp / "classvars/ClassVars_AS1.csv")

    run = dict(run_rows[0])
    run.update({
        "Popvars": "popvars/PopVars_R53.csv",
        "sizecontrol": "N",
        "mcruns": "1",
        "runtime": str(ENGINE_RUNTIME_GENERATIONS),
        "output_years": "1",
        "summaryOutput": "N",
        "cdclimgentime": "0",
        "startcomp": "0",
        "implementcomp": "Back",
    })
    _write_csv(inp / "RunVars_R53.csv", run_fields, [run])

    pop = dict(pop_rows[0])
    # Pinned 3.08 source reads implement_disease even though some bundled
    # PopVars templates omit that late-added column. Carry the historical
    # fail-closed repair forward explicitly with disease disabled.
    if "implement_disease" not in pop_fields:
        pop_fields = list(pop_fields) + ["implement_disease"]
    pop.setdefault("implement_disease", "N")
    replacements = {
        "xyfilename": "patchvars/PatchVars_R53.csv",
        "mate_cdmat": "cdmats/distance.csv",
        "migrateout_cdmat": "cdmats/probability.csv",
        "migrateback_cdmat": "cdmats/probability.csv",
        "stray_cdmat": "cdmats/distance.csv",
        "disperseLocal_cdmat": "cdmats/probability.csv",
        "matemoveno": "6",
        "matemovethresh": "max",
        "disperseLocalno": "9",
        "disperseLocalthresh": "max",
        "growth_option": "N",
        "popmodel": "packing",
        "startGenes": "0",
        "loci": str(NEUTRAL_LOCI),
        "alleles": str(NEUTRAL_ALLELES),
        "muterate": "0",
        "cdevolveans": "N",
        "startSelection": "0",
        "plasticgeneans": "N",
        "startPlasticgene": "0",
        "implement_disease": "N",
    }
    for k, v in replacements.items():
        if k in pop:
            pop[k] = v
    _write_csv(inp / "popvars/PopVars_R53.csv", pop_fields, [pop])

    base = _collapse_invariant_template_temporal_values(dict(patch_rows[0]))
    patch_out: list[dict[str, Any]] = []
    source_n0 = int(stress["source_n0"])
    patch_k = int(stress["patch_k"])
    core_set = set(core)
    for i, cell in enumerate(cells, 1):
        rr, cc = divmod(cell, nc)
        rec = dict(base)
        updates = {
            "PatchID": str(i),
            "X": f"{cc * ENGINE_COORDINATE_SCALE:.6f}",
            "Y": f"{rr * ENGINE_COORDINATE_SCALE:.6f}",
            "SubpatchNO": "1",
            "K": str(patch_k),
            "K StDev": "0",
            "N0": str(source_n0 if cell in core_set else 0),
            "Natal Grounds": "1" if cell in core_set else "0",
            "Migration Out Grounds": "0",
            "Genes Initialize": "random",
            "Class Vars": "classvars/ClassVars_AS1.csv",
            "Migration Out Prob": "0",
            "Migration Back Prob": "0",
            "Straying Prob": "0",
            "Dispersal Prob": str(DISPERSAL_PROBABILITY),
            "HabitatOut": "1",
            "HabitatBack": "1",
        }
        for k, v in updates.items():
            if k in rec:
                rec[k] = v
        patch_out.append(rec)
    _write_csv(inp / "patchvars/PatchVars_R53.csv", patch_fields, patch_out)

    dist, prob = _distance_and_probability(cells, nr, nc)
    np.savetxt(inp / "cdmats/distance.csv", dist, delimiter=",", fmt="%.10g")
    np.savetxt(inp / "cdmats/probability.csv", prob, delimiter=",", fmt="%.10g")

    files = {}
    for p in sorted(inp.rglob("*")):
        if p.is_file():
            rel = p.relative_to(inp).as_posix()
            files[rel] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
    write_json(group_dir / "GROUP_INPUT_MANIFEST.json", {
        "stage": STAGE,
        "status": "R53_CDMETAPOP_INPUT_GROUP_READY",
        "files": files,
    })
    return {
        "input_file_count": len(files),
        "input_manifest_sha256": sha256_file(group_dir / "GROUP_INPUT_MANIFEST.json"),
    }


def prepare_demographic_challenges(root: Path, allow_non_scientific_dev_parent: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    auth = validate_parent_authority(root, allow_non_scientific_dev=allow_non_scientific_dev_parent)
    if auth["failed"]:
        raise R53Error(f"R5.3 parent authority failed: {auth['failed']}")
    out = root / OUT_REL
    work = out / "cdmetapop_work"
    work.mkdir(parents=True, exist_ok=True)

    fams, cores, lat, lon = r52.reconstruct_robust_family_cores(root)
    ages, ids, spatial = _load_j14(root)
    nr, nc = len(lat), len(lon)
    r52_support = _r52_support_by_family(root)

    groups: list[dict[str, Any]] = []
    gid_num = 0
    for fam in fams:
        fid = str(fam["family_id"])
        cells = _select_network_cells_for_family(fam, cores[fid], ages, ids, spatial, nr, nc)
        network_semantic = {
            "family_id": fid,
            "candidate_id": str(fam["candidate_id"]),
            "patch_cells": cells,
            "core_cells": sorted(cores[fid]),
            "selection_rule": "R51_Q99_CORE_PLUS_DESCENDING_J14_OCCUPANCY_SUPPORT_FIXED_MAX_32",
            "r52_geometry_used": False,
        }
        network_sha = semantic_sha256(network_semantic)
        for stress_name, stress in DEMOGRAPHIC_STRESS_PROFILES.items():
            gid_num += 1
            gid = f"R53_G{gid_num:03d}_{fid}_{stress_name.split('_')[0]}"
            gdir = work / gid
            gdir.mkdir(parents=True, exist_ok=True)
            inp_meta = _build_cdmetapop_input_group(root, gdir, cells, cores[fid], stress, nr, nc)
            group = {
                "group_id": gid,
                "group_numeric_id": gid_num,
                "candidate_id": str(fam["candidate_id"]),
                "family_id": fid,
                "origin_age_ma": float(fam["oldest_supported_age_ma"]),
                "demographic_stress_profile": stress_name,
                "standardized_source_n0_per_core_patch": int(stress["source_n0"]),
                "standardized_patch_k": int(stress["patch_k"]),
                "stress_values_are_literal_arcana_population": False,
                "patch_count": len(cells),
                "source_core_patch_count": len(cores[fid]),
                "network_semantic_sha256": network_sha,
                "network_authority": "ARCANA_R51_Q99_CORE_PLUS_J14_OCCUPANCY_SUPPORT",
                "r52_corridor_support": r52_support.get(fid),
                "r52_numeric_geometry_used_as_input": False,
                "r52_numeric_output_defines_arcana_target": False,
                "neutral_genetics": {"loci": NEUTRAL_LOCI, "alleles_per_locus": NEUTRAL_ALLELES, "selection": False, "mutation_rate": 0.0},
                "engine_runtime_generations": ENGINE_RUNTIME_GENERATIONS,
                "engine_generation_is_literal_arcana_time": False,
                "seeds": list(SEEDS),
                "expected_stream_count": len(SEEDS),
                "input_dir": str((gdir / "Inputs").relative_to(root)).replace("\\", "/"),
                "evidence_dir": str((gdir / "Evidence").relative_to(root)).replace("\\", "/"),
                **inp_meta,
            }
            write_json(gdir / "GROUP_CONFIG.json", group)
            groups.append(group)

    plan = {
        "stage": STAGE,
        "status": "PASS_R53_CDMETAPOP_DEMOGRAPHIC_CHALLENGE_PLAN_PREPARED",
        "scientific_parent_mode": not allow_non_scientific_dev_parent,
        "objective": "CORRIDOR_CONDITIONED_DEMOGRAPHIC_PERSISTENCE_BOTTLENECK_AND_NEUTRAL_GENE_FLOW_DIAGNOSTIC",
        "primary_governed_engine": "CDMetaPOP",
        "primary_governed_engine_required_version": EXPECTED_CDMETAPOP_VERSION,
        "primary_governed_engine_required_commit": EXPECTED_CDMETAPOP_COMMIT,
        "robust_family_count": len(fams),
        "group_count": len(groups),
        "stress_profiles": DEMOGRAPHIC_STRESS_PROFILES,
        "seeds": list(SEEDS),
        "planned_stream_count": sum(int(g["expected_stream_count"]) for g in groups),
        "authorized_output_fields": list(AUTHORIZED_CDMETAPOP_FIELDS),
        "standardized_diagnostic_semantics": {
            "census_values_are_literal_arcana_population": False,
            "engine_generation_is_literal_arcana_time": False,
            "neutral_loci_are_arcana_canonical_genome": False,
            "r52_range_geometry_used_as_cdmetapop_input": False,
            "r52_used_only_for_reporting_stratification": True,
        },
        "selection_rules": {
            "single_demographic_history_winner_selected": False,
            "result_selected_tuning": False,
            "majority_vote": False,
            "external_engine_defines_arcana_target": False,
            "numeric_output_causes_automatic_scientific_pass_fail": False,
        },
        "canonical_state_changed": False,
        "derived_refinement_promoted_to_canon": False,
        "deep_biological_coupling": False,
        "groups": groups,
    }
    p = out / "R5_3_CDMETAPOP_EXECUTION_PLAN.json"
    write_json(p, plan)
    return {"authority": auth, "plan": plan, "plan_path": p, "plan_sha256": sha256_file(p)}


def _numeric_vector(raw: Any) -> list[float]:
    if raw is None:
        return []
    if isinstance(raw, (int, float)):
        return [float(raw)]
    s = str(raw).strip()
    if not s:
        return []
    vals: list[float] = []
    for part in s.replace(";", "|").split("|"):
        p = part.strip()
        if not p or p.upper() in {"NA", "N", "NAN"}:
            continue
        try:
            x = float(p)
            if math.isfinite(x):
                vals.append(x)
        except ValueError:
            continue
    return vals


def summarize_cdmetapop_summary(path: Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        fields = list(rd.fieldnames or [])
        rows = list(rd)
    missing = [x for x in AUTHORIZED_CDMETAPOP_FIELDS if x not in fields]
    if missing:
        raise R53Error(f"CDMetaPOP summary missing authorized fields: {missing}")
    parsed = []
    for row in rows:
        years = _numeric_vector(row.get("Year"))
        if not years:
            continue
        nv = _numeric_vector(row.get("N_Initial"))
        av = _numeric_vector(row.get("Alleles"))
        hev = _numeric_vector(row.get("He"))
        hov = _numeric_vector(row.get("Ho"))
        parsed.append({
            "year": int(round(years[0])),
            "N_total": float(sum(nv)) if nv else 0.0,
            "Alleles_mean": float(np.mean(av)) if av else None,
            "He_mean": float(np.mean(hev)) if hev else None,
            "Ho_mean": float(np.mean(hov)) if hov else None,
        })
    if not parsed:
        raise R53Error("CDMetaPOP authorized summary contains no parseable rows")
    parsed.sort(key=lambda r: r["year"])
    n = np.asarray([r["N_total"] for r in parsed], float)
    initial = float(n[0])
    final = float(n[-1])
    first_zero = next((int(r["year"]) for r in parsed if r["N_total"] <= 0), None)

    def retention(key: str) -> float | None:
        vals = [(r["year"], r[key]) for r in parsed if r[key] is not None]
        if not vals:
            return None
        a = float(vals[0][1]); b = float(vals[-1][1])
        return float(b / a) if abs(a) > 1e-30 else None

    return {
        "authorized_fields_present": True,
        "row_count": len(parsed),
        "first_year": int(parsed[0]["year"]),
        "last_year": int(parsed[-1]["year"]),
        "initial_population_engine_native": initial,
        "minimum_population_engine_native": float(np.min(n)),
        "final_population_engine_native": final,
        "minimum_to_initial_ratio": float(np.min(n) / initial) if initial > 0 else None,
        "final_to_initial_ratio": float(final / initial) if initial > 0 else None,
        "extinction_observed": bool(np.any(n <= 0)),
        "first_zero_population_engine_generation": first_zero,
        "alleles_retention_ratio": retention("Alleles_mean"),
        "He_retention_ratio": retention("He_mean"),
        "Ho_retention_ratio": retention("Ho_mean"),
        "last_record": parsed[-1],
    }


def analyze_cdmetapop_evidence(root: Path, allow_non_scientific_dev_parent: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    auth = validate_parent_authority(root, allow_non_scientific_dev=allow_non_scientific_dev_parent)
    if auth["failed"]:
        raise R53Error(f"R5.3 parent authority failed: {auth['failed']}")
    out = root / OUT_REL
    plan = load_json(out / "R5_3_CDMETAPOP_EXECUTION_PLAN.json")
    runtime = load_json(out / "R5_3_CDMETAPOP_RUNTIME_IDENTITY.json")
    bridge = load_json(out / "R5_3_CDMETAPOP_EXECUTION_BRIDGE.json")
    groups = list(plan.get("groups") or [])

    stream_records: list[dict[str, Any]] = []
    raw_files: dict[str, Any] = {}
    group_integrity: dict[str, Any] = {}
    for g in groups:
        gid = str(g["group_id"])
        evroot = root / str(g["evidence_dir"])
        input_dir = root / str(g["input_dir"])
        input_manifest = input_dir.parent / "GROUP_INPUT_MANIFEST.json"
        input_manifest_ok = input_manifest.is_file() and sha256_file(input_manifest) == str(g.get("input_manifest_sha256"))
        expected = {(int(s),) for s in SEEDS}
        found: set[tuple[int]] = set()
        ok = bool(input_manifest_ok)
        for seed in SEEDS:
            sdir = evroot / f"seed_{seed}"
            summary = sdir / "summary_popAllTime.csv"
            meta = sdir / "STREAM_RUNTIME.json"
            if not summary.is_file() or not meta.is_file():
                ok = False
                continue
            md = load_json(meta)
            found.add((int(md.get("seed", -1)),))
            if md.get("status") != "PASS_R53_CDMETAPOP_STREAM" or int(md.get("seed", -1)) != seed:
                ok = False
            if md.get("cdmetapop_version") != EXPECTED_CDMETAPOP_VERSION or md.get("cdmetapop_commit") != EXPECTED_CDMETAPOP_COMMIT:
                ok = False
            try:
                metrics = summarize_cdmetapop_summary(summary)
            except Exception:
                ok = False
                continue
            rec = {
                "group_id": gid,
                "candidate_id": g["candidate_id"],
                "family_id": g["family_id"],
                "demographic_stress_profile": g["demographic_stress_profile"],
                "seed": seed,
                "r52_corridor_support": g.get("r52_corridor_support"),
                "metrics": metrics,
                "automatic_scientific_pass_fail_from_values": False,
            }
            stream_records.append(rec)
            for fp in (summary, meta):
                rel = fp.relative_to(root).as_posix()
                raw_files[rel] = {"bytes": fp.stat().st_size, "sha256": sha256_file(fp)}
        group_integrity[gid] = {
            "expected_stream_count": len(SEEDS),
            "actual_stream_count": sum(1 for r in stream_records if r["group_id"] == gid),
            "seed_membership_exact": found == expected,
            "input_manifest_integrity": bool(input_manifest_ok),
            "execution_integrity": bool(ok and found == expected),
        }

    # Fixed 2-seed aggregation only; no vote and no automatic scientific verdict.
    sensitivity: list[dict[str, Any]] = []
    by: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for r in stream_records:
        by.setdefault((r["candidate_id"], r["family_id"], r["demographic_stress_profile"]), []).append(r)
    for key in sorted(by):
        rs = sorted(by[key], key=lambda r: r["seed"])
        mins = [r["metrics"].get("minimum_to_initial_ratio") for r in rs if r["metrics"].get("minimum_to_initial_ratio") is not None]
        hes = [r["metrics"].get("He_retention_ratio") for r in rs if r["metrics"].get("He_retention_ratio") is not None]
        alls = [r["metrics"].get("alleles_retention_ratio") for r in rs if r["metrics"].get("alleles_retention_ratio") is not None]
        sensitivity.append({
            "candidate_id": key[0],
            "family_id": key[1],
            "demographic_stress_profile": key[2],
            "seed_membership": [r["seed"] for r in rs],
            "seed_membership_exact": tuple(r["seed"] for r in rs) == SEEDS,
            "extinction_seed_count": sum(bool(r["metrics"]["extinction_observed"]) for r in rs),
            "minimum_to_initial_ratio_minmax": [float(min(mins)), float(max(mins))] if mins else None,
            "He_retention_ratio_minmax": [float(min(hes)), float(max(hes))] if hes else None,
            "alleles_retention_ratio_minmax": [float(min(alls)), float(max(alls))] if alls else None,
            "r52_corridor_support": rs[0].get("r52_corridor_support") if rs else None,
            "automatic_scientific_pass_fail_from_values": False,
        })

    write_json(out / "R5_3_CDMETAPOP_STREAM_EVIDENCE.json", {
        "stage": STAGE,
        "status": "R53_GOVERNED_CDMETAPOP_STREAM_EVIDENCE",
        "authorized_fields": list(AUTHORIZED_CDMETAPOP_FIELDS),
        "semantics": "ENGINE_NATIVE_DEMOGRAPHIC_AND_NEUTRAL_GENETIC_DIAGNOSTICS_NOT_LITERAL_ARCANA_POPULATION_HISTORY",
        "records": stream_records,
    })
    write_json(out / "R5_3_DEMOGRAPHIC_PERSISTENCE_SENSITIVITY.json", {
        "stage": STAGE,
        "status": "R53_FIXED_DEMOGRAPHIC_STRESS_SENSITIVITY_SUMMARY",
        "stress_profiles": DEMOGRAPHIC_STRESS_PROFILES,
        "seeds": list(SEEDS),
        "selection_semantics": "NO_WEIGHTED_SCORE_NO_MAJORITY_VOTE_NO_SINGLE_WINNER_NO_AUTOMATIC_NUMERIC_PASS_FAIL",
        "records": sensitivity,
    })
    write_json(out / "R5_3_RAW_EVIDENCE_MANIFEST.json", {
        "stage": STAGE,
        "status": "R53_RAW_CDMETAPOP_AUTHORIZED_EVIDENCE_MANIFEST",
        "file_count": len(raw_files),
        "files": raw_files,
    })

    checks = {
        "parent_authority_pass": not auth["failed"],
        "runtime_status_pass": runtime.get("status") == "PASS_R53_CDMETAPOP_3_08_PINNED_RUNTIME_IDENTITY",
        "runtime_version_exact": runtime.get("cdmetapop_version") == EXPECTED_CDMETAPOP_VERSION,
        "runtime_commit_exact": runtime.get("cdmetapop_commit") == EXPECTED_CDMETAPOP_COMMIT,
        "bridge_status_exact": bridge.get("status") == "R53_POWERSHELL_WSL_CDMETAPOP_EXECUTION_BRIDGE",
        "bridge_stream_count_exact": int(bridge.get("stream_count", -1)) == EXPECTED_ROBUST_FAMILY_COUNT * len(DEMOGRAPHIC_STRESS_PROFILES) * len(SEEDS),
        "bridge_all_exit_zero": all(int(r.get("exit_code", -1)) == 0 and r.get("timed_out") is False for r in (bridge.get("records") or [])) and len(bridge.get("records") or []) == EXPECTED_ROBUST_FAMILY_COUNT * len(DEMOGRAPHIC_STRESS_PROFILES) * len(SEEDS),
        "plan_status_exact": plan.get("status") == "PASS_R53_CDMETAPOP_DEMOGRAPHIC_CHALLENGE_PLAN_PREPARED",
        "robust_family_count_exact": int(plan.get("robust_family_count", -1)) == EXPECTED_ROBUST_FAMILY_COUNT,
        "group_count_exact": int(plan.get("group_count", -1)) == EXPECTED_ROBUST_FAMILY_COUNT * len(DEMOGRAPHIC_STRESS_PROFILES),
        "planned_stream_count_exact": int(plan.get("planned_stream_count", -1)) == EXPECTED_ROBUST_FAMILY_COUNT * len(DEMOGRAPHIC_STRESS_PROFILES) * len(SEEDS),
        "stress_profiles_exact": plan.get("stress_profiles") == DEMOGRAPHIC_STRESS_PROFILES,
        "seeds_exact": tuple(plan.get("seeds") or []) == SEEDS,
        "authorized_fields_exact": tuple(plan.get("authorized_output_fields") or []) == AUTHORIZED_CDMETAPOP_FIELDS,
        "r52_geometry_not_used_as_input": all(g.get("r52_numeric_geometry_used_as_input") is False for g in groups),
        "r52_does_not_define_arcana_target": all(g.get("r52_numeric_output_defines_arcana_target") is False for g in groups),
        "all_group_execution_integrity": len(group_integrity) == len(groups) and all(x["execution_integrity"] for x in group_integrity.values()),
        "stream_count_exact": len(stream_records) == int(plan.get("planned_stream_count", -1)),
        "sensitivity_count_exact": len(sensitivity) == len(groups),
        "all_sensitivity_seed_membership_exact": all(r["seed_membership_exact"] for r in sensitivity),
        "extinction_is_not_runtime_failure": True,
        "no_majority_vote": (plan.get("selection_rules") or {}).get("majority_vote") is False,
        "no_result_selected_tuning": (plan.get("selection_rules") or {}).get("result_selected_tuning") is False,
        "no_single_winner": (plan.get("selection_rules") or {}).get("single_demographic_history_winner_selected") is False,
        "engine_does_not_define_arcana_target": (plan.get("selection_rules") or {}).get("external_engine_defines_arcana_target") is False,
        "no_automatic_numeric_scientific_pass_fail": (plan.get("selection_rules") or {}).get("numeric_output_causes_automatic_scientific_pass_fail") is False,
        "canonical_state_unchanged": plan.get("canonical_state_changed") is False,
        "derived_refinement_not_promoted": plan.get("derived_refinement_promoted_to_canon") is False,
        "deep_biological_coupling_off": plan.get("deep_biological_coupling") is False,
    }
    checks = {k: bool(v) for k, v in checks.items()}
    failed = [k for k, v in checks.items() if not v]
    audit = {
        "stage": STAGE,
        "status": "PASS_R53_CORRIDOR_CONDITIONED_DEMOGRAPHIC_PERSISTENCE_AND_BOTTLENECK_EVIDENCE_CANDIDATE" if not failed else "BLOCKED_R53_CDMETAPOP_DEMOGRAPHIC_EVIDENCE",
        "scientific_candidate_eligible": bool(not failed and not allow_non_scientific_dev_parent),
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failed": failed,
        "summary": {
            "robust_family_count": EXPECTED_ROBUST_FAMILY_COUNT,
            "group_count": len(groups),
            "scientific_stream_count": len(stream_records),
            "sensitivity_record_count": len(sensitivity),
            "external_engine": "CDMetaPOP",
            "external_engine_version": EXPECTED_CDMETAPOP_VERSION,
            "external_engine_commit": EXPECTED_CDMETAPOP_COMMIT,
            "new_external_engine_execution_performed": True,
            "numeric_demographic_truth_claimed": False,
            "r52_corridor_geometry_promoted_to_input_authority": False,
            "external_engine_defines_arcana_target": False,
            "majority_vote": False,
            "canonical_state_changed": False,
            "derived_refinement_promoted_to_canon": False,
            "deep_biological_coupling": False,
        },
        "group_execution_integrity": group_integrity,
        "checks": checks,
    }
    write_json(out / "R5_3_INTEGRATED_AUDIT.json", audit)

    artifacts = [
        "R5_3_CDMETAPOP_RUNTIME_IDENTITY.json",
        "R5_3_CDMETAPOP_EXECUTION_PLAN.json",
        "R5_3_CDMETAPOP_EXECUTION_BRIDGE.json",
        "R5_3_RAW_EVIDENCE_MANIFEST.json",
        "R5_3_CDMETAPOP_STREAM_EVIDENCE.json",
        "R5_3_DEMOGRAPHIC_PERSISTENCE_SENSITIVITY.json",
        "R5_3_INTEGRATED_AUDIT.json",
    ]
    files = {}
    for name in artifacts:
        p = out / name
        if p.is_file():
            files[name] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
    write_json(out / "R5_3_OUTPUT_MANIFEST.json", {
        "stage": STAGE,
        "status": audit["status"],
        "files": files,
    })
    return {"audit": audit, "stream_records": stream_records, "sensitivity": sensitivity}
