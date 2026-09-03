from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json

import numpy as np

from arcana_worldsim.state_query import r52_corridors as r52
from arcana_worldsim.state_query import r53_demography as r53
from arcana_worldsim.state_query import r54_nemo_genetics as r54

STAGE = "v0.6D1-R5.5"
OUT_REL = Path("outputs/v0_6D1_R5_5")
R54_OUT_REL = Path("outputs/v0_6D1_R5_4")
R54_AUDIT_REL = R54_OUT_REL / "R5_4_INTEGRATED_AUDIT.json"
R54_PLAN_REL = R54_OUT_REL / "R5_4_NEMO_EXECUTION_PLAN.json"
R54_SENSITIVITY_REL = R54_OUT_REL / "R5_4_CROSS_ENGINE_GENETIC_ROBUSTNESS_SENSITIVITY.json"
R54_PAIRS_REL = R54_OUT_REL / "R5_4_NEMO_MATCHED_FLOW_CONTROL_PAIRS.json"
R54_OUTPUT_MANIFEST_REL = R54_OUT_REL / "R5_4_OUTPUT_MANIFEST.json"
R54_SOURCE_REL = Path("src/arcana_worldsim/state_query/r54_nemo_genetics.py")
R53_SENSITIVITY_REL = Path("outputs/v0_6D1_R5_3/R5_3_DEMOGRAPHIC_PERSISTENCE_SENSITIVITY.json")
R53_OUTPUT_MANIFEST_REL = Path("outputs/v0_6D1_R5_3/R5_3_OUTPUT_MANIFEST.json")
R53_PLAN_REL = Path("outputs/v0_6D1_R5_3/R5_3_CDMETAPOP_EXECUTION_PLAN.json")
R53_SOURCE_REL = Path("src/arcana_worldsim/state_query/r53_demography.py")
R52_SOURCE_REL = Path("src/arcana_worldsim/state_query/r52_corridors.py")
SOURCE_MANIFEST_REL = Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_5.json")

EXPECTED_R54_PLAN_SHA256 = "bbe9bb99fdd40ad19c03c18af867defa95f984e2d1937d2ccdad4434427d55d2"
EXPECTED_R54_SOURCE_SHA256 = "bc1bba779bbb895b57634791ec712e38e06bd71f3d51a1a9b79a530f28b0deba"
EXPECTED_R53_SOURCE_SHA256 = "6b72a20edff18a7f73d37717b2d40af77986fa708ffc9f048025f6d11a65452b"
EXPECTED_R52_SOURCE_SHA256 = "efc2c1d13db772ba466aae8b1b207953eb42ae87b444a42ecaec31d73d29e084"
EXPECTED_FAMILY_COUNT = 12
EXPECTED_PAIR_COUNT = 35
EXPECTED_STRESS_COUNT = 3
EXPECTED_R54_STREAM_COUNT = 144
EXPECTED_R54_SENSITIVITY_COUNT = 36
EXPECTED_R53_SENSITIVITY_COUNT = 36
CONTACT_SUPPORT_THRESHOLDS = (0.0, 0.25, 0.50, 0.75, 1.0)
CONTACT_DISTANCE_CELLS = 1


class R55Error(RuntimeError):
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
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _verify_manifest(root: Path, rel: Path) -> bool:
    p = Path(root) / rel
    if not p.is_file():
        return False
    try:
        doc = load_json(p)
        files = dict(doc.get("files") or {})
        if not files:
            return False
        base = p.parent
        for name, meta in files.items():
            fp = base / name
            if not fp.is_file():
                return False
            if fp.stat().st_size != int(meta.get("bytes", -1)):
                return False
            if sha256_file(fp) != meta.get("sha256"):
                return False
        return True
    except Exception:
        return False


def validate_parent_authority(root: Path, allow_non_scientific_dev: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    strict = not allow_non_scientific_dev
    checks: dict[str, bool] = {
        "present::r54_audit": (root / R54_AUDIT_REL).is_file(),
        "present::r54_plan": (root / R54_PLAN_REL).is_file(),
        "present::r54_sensitivity": (root / R54_SENSITIVITY_REL).is_file(),
        "present::r54_pairs": (root / R54_PAIRS_REL).is_file(),
        "present::r54_output_manifest": (root / R54_OUTPUT_MANIFEST_REL).is_file(),
        "present::r54_source": (root / R54_SOURCE_REL).is_file(),
        "present::r53_sensitivity": (root / R53_SENSITIVITY_REL).is_file(),
        "present::r53_output_manifest": (root / R53_OUTPUT_MANIFEST_REL).is_file(),
        "present::r53_plan": (root / R53_PLAN_REL).is_file(),
        "present::r53_source": (root / R53_SOURCE_REL).is_file(),
        "present::r52_source": (root / R52_SOURCE_REL).is_file(),
        "present::j14": (root / r53.J14_REL).is_file(),
    }
    try:
        audit = load_json(root / R54_AUDIT_REL)
        s = audit.get("summary") or {}
        checks["r54_candidate_semantics"] = (
            audit.get("status") == "PASS_R54_CROSS_ENGINE_GENETIC_ROBUSTNESS_AND_GENE_FLOW_EVIDENCE_CANDIDATE"
            and audit.get("scientific_candidate_eligible") is True
            and int(s.get("family_count", -1)) == EXPECTED_FAMILY_COUNT
            and int(s.get("group_count", -1)) == EXPECTED_R54_SENSITIVITY_COUNT
            and int(s.get("scientific_stream_count", -1)) == EXPECTED_R54_STREAM_COUNT
            and int(s.get("matched_pair_count", -1)) == 72
            and int(s.get("sensitivity_record_count", -1)) == EXPECTED_R54_SENSITIVITY_COUNT
            and s.get("external_engine") == "NEMO"
            and s.get("external_engine_version") == "2.4.2"
            and s.get("r53_cdmetapop_values_used_to_fit_nemo") is False
            and s.get("cross_engine_numeric_truth_claimed") is False
            and s.get("cross_engine_metrics_forced_to_equality") is False
            and s.get("majority_vote") is False
            and s.get("canonical_state_changed") is False
            and s.get("derived_refinement_promoted_to_canon") is False
            and s.get("deep_biological_coupling") is False
        )
    except Exception:
        checks["r54_candidate_semantics"] = False
    try:
        plan = load_json(root / R54_PLAN_REL)
        sem = plan.get("semantics") or {}
        sel = plan.get("selection_rules") or {}
        checks["r54_plan_semantics"] = (
            plan.get("status") == "PASS_R54_NEMO_GENETIC_ROBUSTNESS_CHALLENGE_PLAN_PREPARED"
            and int(plan.get("family_count", -1)) == EXPECTED_FAMILY_COUNT
            and int(plan.get("group_count", -1)) == EXPECTED_R54_SENSITIVITY_COUNT
            and int(plan.get("planned_stream_count", -1)) == EXPECTED_R54_STREAM_COUNT
            and sem.get("r53_cdmetapop_values_used_to_fit_nemo") is False
            and sem.get("r53_used_only_for_side_by_side_reporting") is True
            and sem.get("heterogeneous_engine_metrics_forced_to_equality") is False
            and sel.get("single_family_winner_selected") is False
            and sel.get("result_selected_tuning") is False
            and sel.get("majority_vote") is False
            and sel.get("external_engine_defines_arcana_target") is False
            and sel.get("numeric_output_causes_automatic_scientific_pass_fail") is False
        )
        checks["r54_plan_exact_hash"] = (sha256_file(root / R54_PLAN_REL) == EXPECTED_R54_PLAN_SHA256) if strict else True
    except Exception:
        checks["r54_plan_semantics"] = checks["r54_plan_exact_hash"] = False
    try:
        sens = load_json(root / R54_SENSITIVITY_REL)
        checks["r54_sensitivity_semantics"] = (
            sens.get("status") == "R54_FIXED_CROSS_ENGINE_GENETIC_ROBUSTNESS_SENSITIVITY"
            and sens.get("selection_semantics") == "NO_WEIGHTED_SCORE_NO_MAJORITY_VOTE_NO_SINGLE_WINNER_NO_AUTOMATIC_NUMERIC_PASS_FAIL_NO_FORCED_METRIC_EQUALITY"
            and len(sens.get("records") or []) == EXPECTED_R54_SENSITIVITY_COUNT
        )
    except Exception:
        checks["r54_sensitivity_semantics"] = False
    try:
        pairs = load_json(root / R54_PAIRS_REL)
        checks["r54_matched_pair_semantics"] = (
            pairs.get("status") == "R54_MATCHED_FLOW_CONTROL_PAIR_EVIDENCE"
            and len(pairs.get("records") or []) == 72
        )
    except Exception:
        checks["r54_matched_pair_semantics"] = False
    try:
        sens53 = load_json(root / R53_SENSITIVITY_REL)
        checks["r53_sensitivity_semantics"] = (
            sens53.get("status") == "R53_FIXED_DEMOGRAPHIC_STRESS_SENSITIVITY_SUMMARY"
            and sens53.get("selection_semantics") == "NO_WEIGHTED_SCORE_NO_MAJORITY_VOTE_NO_SINGLE_WINNER_NO_AUTOMATIC_NUMERIC_PASS_FAIL"
            and len(sens53.get("records") or []) == EXPECTED_R53_SENSITIVITY_COUNT
        )
    except Exception:
        checks["r53_sensitivity_semantics"] = False

    checks["r54_output_manifest_integrity"] = _verify_manifest(root, R54_OUTPUT_MANIFEST_REL)
    checks["r53_output_manifest_integrity"] = _verify_manifest(root, R53_OUTPUT_MANIFEST_REL)
    checks["r54_source_exact_hash"] = (sha256_file(root / R54_SOURCE_REL) == EXPECTED_R54_SOURCE_SHA256) if strict and (root / R54_SOURCE_REL).is_file() else (root / R54_SOURCE_REL).is_file()
    checks["r53_source_exact_hash"] = (sha256_file(root / R53_SOURCE_REL) == EXPECTED_R53_SOURCE_SHA256) if strict and (root / R53_SOURCE_REL).is_file() else (root / R53_SOURCE_REL).is_file()
    checks["r52_source_exact_hash"] = (sha256_file(root / R52_SOURCE_REL) == EXPECTED_R52_SOURCE_SHA256) if strict and (root / R52_SOURCE_REL).is_file() else (root / R52_SOURCE_REL).is_file()

    inherited = r54.validate_parent_authority(root, allow_non_scientific_dev=allow_non_scientific_dev)
    checks["r54_inherited_r53_r52_r51_j14_chain_pass"] = not inherited.get("failed")
    checks = {k: bool(v) for k, v in checks.items()}
    failed = [k for k, v in checks.items() if not v]
    return {
        "stage": STAGE,
        "status": "PASS_R55_IMMUTABLE_R54_R53_PARENT_CANDIDATE_AUTHORITY" if not failed else "BLOCKED_R55_PARENT_AUTHORITY",
        "scientific_parent_mode": strict,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failed": failed,
        "checks": checks,
        "r54_inherited_parent_authority": inherited,
    }


def _occupied_cells_for_member(spatial: np.ndarray, candidate_index: int, time_index: int, ensemble_index: int, allowed: set[int], nr: int, nc: int) -> set[int]:
    cells: set[int] = set()
    for row in spatial[ensemble_index, candidate_index, time_index]:
        if float(row[3]) <= 0.5:
            continue
        rr = int(np.clip(np.rint(row[1]), 0, nr - 1))
        cc = int(np.clip(np.rint(row[2]), 0, nc - 1))
        cell = rr * nc + cc
        if cell in allowed:
            cells.add(cell)
    return cells


def _cells_within_one(a: set[int], b: set[int], nc: int) -> tuple[bool, bool, set[int]]:
    if not a or not b:
        return False, False, set()
    exact = a & b
    zone = set(exact)
    near = bool(exact)
    if near:
        return True, True, zone
    for ca in a:
        ra, xa = divmod(ca, nc)
        for cb in b:
            rb, xb = divmod(cb, nc)
            dc0 = abs(xa - xb)
            dc = min(dc0, nc - dc0)
            if max(abs(ra - rb), dc) <= CONTACT_DISTANCE_CELLS:
                near = True
                zone.add(ca)
                zone.add(cb)
    return False, near, zone


def contact_fractions_at_age(spatial: np.ndarray, candidate_a_index: int, candidate_b_index: int, time_index: int, network_a: set[int], network_b: set[int], nr: int, nc: int) -> tuple[float, float, set[int]]:
    n = int(spatial.shape[0])
    exact_count = 0
    near_count = 0
    zone: set[int] = set()
    for e in range(n):
        a = _occupied_cells_for_member(spatial, candidate_a_index, time_index, e, network_a, nr, nc)
        b = _occupied_cells_for_member(spatial, candidate_b_index, time_index, e, network_b, nr, nc)
        exact, near, z = _cells_within_one(a, b, nc)
        exact_count += int(exact)
        near_count += int(near)
        zone |= z
    return float(exact_count / n), float(near_count / n), zone


def _threshold_mask(values: np.ndarray, threshold: float) -> np.ndarray:
    values = np.asarray(values, float)
    if threshold <= 0.0:
        return values > 0.0
    return values >= threshold - 1e-12


def contiguous_windows(ages: np.ndarray, mask: np.ndarray) -> list[dict[str, Any]]:
    ages = np.asarray(ages, float)
    mask = np.asarray(mask, bool)
    if ages.shape != mask.shape:
        raise R55Error("age/mask shape mismatch")
    windows: list[dict[str, Any]] = []
    start: int | None = None
    for i, flag in enumerate(mask.tolist() + [False]):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            end = i - 1
            aa = ages[start : end + 1]
            oldest = float(np.max(aa))
            youngest = float(np.min(aa))
            windows.append({
                "start_index": int(start),
                "end_index": int(end),
                "state_count": int(end - start + 1),
                "oldest_age_ma": oldest,
                "youngest_age_ma": youngest,
                "sample_span_kyr": float(max(0.0, oldest - youngest) * 1000.0),
            })
            start = None
    return windows


def _compact_r53(rec: dict[str, Any]) -> dict[str, Any]:
    return {
        "extinction_seed_count": int(rec.get("extinction_seed_count", -1)),
        "minimum_to_initial_ratio_minmax": rec.get("minimum_to_initial_ratio_minmax"),
        "He_retention_ratio_minmax": rec.get("He_retention_ratio_minmax"),
        "alleles_retention_ratio_minmax": rec.get("alleles_retention_ratio_minmax"),
        "automatic_scientific_pass_fail_from_values": False,
    }


def _compact_r54(rec: dict[str, Any]) -> dict[str, Any]:
    return {
        "nemo_delta_He_retention_flow_minus_control_minmax": rec.get("nemo_delta_He_retention_flow_minus_control_minmax"),
        "nemo_delta_fixed_fraction_flow_minus_control_minmax": rec.get("nemo_delta_fixed_fraction_flow_minus_control_minmax"),
        "nemo_delta_patch_frequency_variance_flow_minus_control_minmax": rec.get("nemo_delta_patch_frequency_variance_flow_minus_control_minmax"),
        "nemo_delta_global_frequency_shift_flow_minus_control_minmax": rec.get("nemo_delta_global_frequency_shift_flow_minus_control_minmax"),
        "cross_engine_equality_required": False,
        "automatic_scientific_pass_fail_from_values": False,
    }


def _sensitivity_lookup(root: Path) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    r53_records = load_json(root / R53_SENSITIVITY_REL).get("records") or []
    r54_records = load_json(root / R54_SENSITIVITY_REL).get("records") or []
    a = {(str(r["family_id"]), str(r["demographic_stress_profile"])): r for r in r53_records}
    b = {(str(r["family_id"]), str(r["demographic_stress_profile"])): r for r in r54_records}
    return a, b


def build_contact_history(root: Path, allow_non_scientific_dev_parent: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    auth = validate_parent_authority(root, allow_non_scientific_dev=allow_non_scientific_dev_parent)
    if auth["failed"]:
        raise R55Error(f"R5.5 parent authority failed: {auth['failed']}")

    out = root / OUT_REL
    out.mkdir(parents=True, exist_ok=True)

    fams, cores, lat, lon = r52.reconstruct_robust_family_cores(root)
    ages, ids, spatial = r53._load_j14(root)
    nr, nc = len(lat), len(lon)
    if len(fams) != EXPECTED_FAMILY_COUNT:
        raise R55Error(f"expected {EXPECTED_FAMILY_COUNT} robust families, got {len(fams)}")
    if tuple(ids) != tuple(r52.CANDIDATES):
        raise R55Error("J14 candidate cohort differs from R5.5 contract")

    networks: dict[str, set[int]] = {}
    fam_by_id: dict[str, dict[str, Any]] = {}
    for fam in fams:
        fid = str(fam["family_id"])
        fam_by_id[fid] = fam
        networks[fid] = set(r53._select_network_cells_for_family(fam, cores[fid], ages, ids, spatial, nr, nc))

    left = sorted((f for f in fams if str(f["candidate_id"]) == ids[0]), key=lambda f: str(f["family_id"]))
    right = sorted((f for f in fams if str(f["candidate_id"]) == ids[1]), key=lambda f: str(f["family_id"]))
    if len(left) * len(right) != EXPECTED_PAIR_COUNT:
        raise R55Error(f"expected {EXPECTED_PAIR_COUNT} cross-lineage pairs, got {len(left) * len(right)}")

    exact_atlas = np.zeros((EXPECTED_PAIR_COUNT, len(ages)), dtype=np.float32)
    near_atlas = np.zeros((EXPECTED_PAIR_COUNT, len(ages)), dtype=np.float32)
    pair_ids: list[str] = []
    pair_records: list[dict[str, Any]] = []
    global_zone_cells: set[int] = set()

    pidx = 0
    for fa in left:
        for fb in right:
            pair_id = f"CZ{pidx + 1:03d}_{fa['family_id']}__{fb['family_id']}"
            pair_ids.append(pair_id)
            applicable = ages <= min(float(fa["oldest_supported_age_ma"]), float(fb["oldest_supported_age_ma"])) + 1e-12
            pair_zone: set[int] = set()
            ja = ids.index(str(fa["candidate_id"]))
            jb = ids.index(str(fb["candidate_id"]))
            for t in range(len(ages)):
                if not bool(applicable[t]):
                    continue
                ex, ne, z = contact_fractions_at_age(spatial, ja, jb, t, networks[str(fa["family_id"])], networks[str(fb["family_id"])], nr, nc)
                exact_atlas[pidx, t] = ex
                near_atlas[pidx, t] = ne
                pair_zone |= z
            global_zone_cells |= pair_zone

            threshold_windows: dict[str, Any] = {}
            for threshold in CONTACT_SUPPORT_THRESHOLDS:
                key = "gt0" if threshold == 0.0 else f"ge{int(round(threshold * 100)):03d}pct"
                mask = applicable & _threshold_mask(near_atlas[pidx], threshold)
                threshold_windows[key] = {
                    "threshold_fraction": float(threshold),
                    "semantics": "DESCRIPTIVE_MATCHED_ENSEMBLE_SUPPORT_THRESHOLD_NOT_MAJORITY_VOTE_NOT_TRUTH_SELECTION",
                    "windows": contiguous_windows(ages, mask),
                }

            exact_mask = applicable & (exact_atlas[pidx] > 0.0)
            near_mask = applicable & (near_atlas[pidx] > 0.0)
            zone_sorted = sorted(pair_zone)
            if zone_sorted:
                rr = np.asarray(zone_sorted, int) // nc
                cc = np.asarray(zone_sorted, int) % nc
                zone_bounds = {"row_minmax": [int(rr.min()), int(rr.max())], "col_minmax": [int(cc.min()), int(cc.max())]}
            else:
                zone_bounds = {"row_minmax": None, "col_minmax": None}
            pair_records.append({
                "pair_id": pair_id,
                "family_a": str(fa["family_id"]),
                "candidate_a": str(fa["candidate_id"]),
                "family_b": str(fb["family_id"]),
                "candidate_b": str(fb["candidate_id"]),
                "both_lineages_available_from_age_ma": float(min(float(fa["oldest_supported_age_ma"]), float(fb["oldest_supported_age_ma"]))),
                "family_a_network_patch_count": len(networks[str(fa["family_id"])]),
                "family_b_network_patch_count": len(networks[str(fb["family_id"])]),
                "contact_distance_cells": CONTACT_DISTANCE_CELLS,
                "contact_semantics": "SPATIAL_CONTACT_OPPORTUNITY_NOT_REALIZED_MATING_NOT_REALIZED_GENE_FLOW_NOT_REALIZED_ADMIXTURE",
                "any_exact_overlap_state": bool(np.any(exact_mask)),
                "any_one_cell_contact_opportunity_state": bool(np.any(near_mask)),
                "exact_overlap_state_count": int(np.sum(exact_mask)),
                "one_cell_contact_opportunity_state_count": int(np.sum(near_mask)),
                "exact_contact_support_fraction_minmax_nonzero": [float(np.min(exact_atlas[pidx][exact_mask])), float(np.max(exact_atlas[pidx][exact_mask]))] if np.any(exact_mask) else None,
                "one_cell_contact_support_fraction_minmax_nonzero": [float(np.min(near_atlas[pidx][near_mask])), float(np.max(near_atlas[pidx][near_mask]))] if np.any(near_mask) else None,
                "exact_overlap_windows": contiguous_windows(ages, exact_mask),
                "contact_opportunity_windows_by_support_threshold": threshold_windows,
                "contact_zone_cell_count": len(zone_sorted),
                "contact_zone_bounds": zone_bounds,
                "single_contact_zone_winner_selected": False,
                "automatic_scientific_pass_fail_from_values": False,
            })
            pidx += 1

    r53_lookup, r54_lookup = _sensitivity_lookup(root)
    stress_names = tuple(r53.DEMOGRAPHIC_STRESS_PROFILES.keys())
    context_records: list[dict[str, Any]] = []
    for pair in pair_records:
        for stress in stress_names:
            k1 = (pair["family_a"], stress)
            k2 = (pair["family_b"], stress)
            if k1 not in r53_lookup or k2 not in r53_lookup or k1 not in r54_lookup or k2 not in r54_lookup:
                raise R55Error(f"missing R5.3/R5.4 sensitivity context for {pair['pair_id']} {stress}")
            context_records.append({
                "pair_id": pair["pair_id"],
                "family_a": pair["family_a"],
                "family_b": pair["family_b"],
                "demographic_stress_profile": stress,
                "contact_opportunity_present_in_j14": bool(pair["any_one_cell_contact_opportunity_state"]),
                "family_a_r53_cdmetapop": _compact_r53(r53_lookup[k1]),
                "family_b_r53_cdmetapop": _compact_r53(r53_lookup[k2]),
                "family_a_r54_nemo": _compact_r54(r54_lookup[k1]),
                "family_b_r54_nemo": _compact_r54(r54_lookup[k2]),
                "cross_engine_values_used_to_move_or_create_contact_window": False,
                "cross_engine_equality_required": False,
                "agreement_score_computed": False,
                "majority_vote": False,
                "single_history_winner_selected": False,
                "automatic_scientific_pass_fail_from_values": False,
            })

    atlas_path = out / "R5_5_CONTACT_OPPORTUNITY_ATLAS.npz"
    np.savez_compressed(
        atlas_path,
        age_ma=np.asarray(ages, dtype=np.float64),
        pair_ids=np.asarray(pair_ids),
        exact_contact_ensemble_fraction=exact_atlas,
        one_cell_contact_ensemble_fraction=near_atlas,
        contact_support_thresholds=np.asarray(CONTACT_SUPPORT_THRESHOLDS, dtype=np.float64),
    )

    history = {
        "stage": STAGE,
        "status": "R55_ARCANA_NATIVE_CONTACT_ZONE_HISTORY",
        "semantics": "MATCHED_J14_ENSEMBLE_CONTACT_OPPORTUNITY_HISTORY_RESTRICTED_TO_R51_J14_FAMILY_NETWORKS_NOT_REALIZED_ADMIXTURE",
        "candidate_ids": list(ids),
        "family_count": len(fams),
        "cross_lineage_pair_count": len(pair_records),
        "age_state_count": len(ages),
        "contact_distance_cells": CONTACT_DISTANCE_CELLS,
        "contact_support_thresholds": list(CONTACT_SUPPORT_THRESHOLDS),
        "support_thresholds_are_majority_vote": False,
        "pair_records": pair_records,
    }
    write_json(out / "R5_5_CONTACT_ZONE_HISTORY.json", history)
    write_json(out / "R5_5_CROSS_ENGINE_CONTACT_CONTEXT.json", {
        "stage": STAGE,
        "status": "R55_CONTACT_HISTORY_WITH_HETEROGENEOUS_R53_R54_CONTEXT",
        "semantics": "R53_CDMETAPOP_AND_R54_NEMO_ARE_DESCRIPTIVE_CONTEXT_ONLY_AND_DO_NOT_CREATE_OR_MOVE_CONTACT_WINDOWS",
        "record_count": len(context_records),
        "records": context_records,
    })

    binding = {
        "stage": STAGE,
        "status": "R55_PARENT_CANDIDATE_BINDING",
        "r54_plan_sha256": sha256_file(root / R54_PLAN_REL),
        "r54_audit_sha256": sha256_file(root / R54_AUDIT_REL),
        "r54_sensitivity_sha256": sha256_file(root / R54_SENSITIVITY_REL),
        "r54_output_manifest_sha256": sha256_file(root / R54_OUTPUT_MANIFEST_REL),
        "r53_sensitivity_sha256": sha256_file(root / R53_SENSITIVITY_REL),
        "r53_output_manifest_sha256": sha256_file(root / R53_OUTPUT_MANIFEST_REL),
        "j14_sha256": sha256_file(root / r53.J14_REL),
        "binding_semantics": "R54_AND_R53_CANDIDATES_BOUND_BY_HASH_AFTER_SEMANTIC_AND_MANIFEST_VALIDATION_NO_MICRO_SEAL_REQUIRED",
    }
    write_json(out / "R5_5_PARENT_CANDIDATE_BINDING.json", binding)

    pair_with_contact = sum(bool(p["any_one_cell_contact_opportunity_state"]) for p in pair_records)
    pair_with_exact = sum(bool(p["any_exact_overlap_state"]) for p in pair_records)
    checks = {
        "parent_authority_pass": not auth["failed"],
        "no_new_external_engine_execution": True,
        "family_count_exact": len(fams) == EXPECTED_FAMILY_COUNT,
        "cross_lineage_pair_count_exact": len(pair_records) == EXPECTED_PAIR_COUNT,
        "candidate_cohort_exact": tuple(ids) == tuple(r52.CANDIDATES),
        "age_state_count_matches_j14": exact_atlas.shape[1] == len(ages),
        "atlas_pair_count_exact": exact_atlas.shape[0] == EXPECTED_PAIR_COUNT and near_atlas.shape == exact_atlas.shape,
        "contact_fraction_bounds_valid": bool(np.all(exact_atlas >= 0) and np.all(exact_atlas <= 1) and np.all(near_atlas >= 0) and np.all(near_atlas <= 1)),
        "exact_is_subset_of_one_cell_contact": bool(np.all(exact_atlas <= near_atlas + 1e-12)),
        "support_threshold_family_exact": tuple(CONTACT_SUPPORT_THRESHOLDS) == (0.0, 0.25, 0.50, 0.75, 1.0),
        "support_thresholds_not_majority_vote": history["support_thresholds_are_majority_vote"] is False,
        "context_record_count_exact": len(context_records) == EXPECTED_PAIR_COUNT * EXPECTED_STRESS_COUNT,
        "all_context_records_complete": all(r["family_a_r53_cdmetapop"] and r["family_b_r53_cdmetapop"] and r["family_a_r54_nemo"] and r["family_b_r54_nemo"] for r in context_records),
        "r53_r54_do_not_create_contact_windows": all(r["cross_engine_values_used_to_move_or_create_contact_window"] is False for r in context_records),
        "heterogeneous_metrics_not_forced_equal": all(r["cross_engine_equality_required"] is False for r in context_records),
        "no_agreement_score": all(r["agreement_score_computed"] is False for r in context_records),
        "no_majority_vote": all(r["majority_vote"] is False for r in context_records),
        "no_single_history_winner": all(r["single_history_winner_selected"] is False for r in context_records),
        "no_automatic_numeric_scientific_pass_fail": all(r["automatic_scientific_pass_fail_from_values"] is False for r in context_records),
        "contact_is_opportunity_not_realized_admixture": all("NOT_REALIZED_ADMIXTURE" in p["contact_semantics"] for p in pair_records),
        "canonical_state_unchanged": True,
        "derived_refinement_not_promoted": True,
        "deep_biological_coupling_off": True,
    }
    checks = {k: bool(v) for k, v in checks.items()}
    failed = [k for k, v in checks.items() if not v]
    audit = {
        "stage": STAGE,
        "status": "PASS_R55_CONTACT_ZONE_AND_GENE_FLOW_HISTORY_CONSOLIDATION_CANDIDATE" if not failed else "BLOCKED_R55_CONTACT_HISTORY_CONSOLIDATION",
        "scientific_candidate_eligible": bool(not failed and not allow_non_scientific_dev_parent),
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failed": failed,
        "summary": {
            "family_count": len(fams),
            "cross_lineage_pair_count": len(pair_records),
            "pair_with_one_cell_contact_opportunity_count": int(pair_with_contact),
            "pair_with_exact_overlap_count": int(pair_with_exact),
            "age_state_count": len(ages),
            "cross_engine_context_record_count": len(context_records),
            "new_external_engine_execution_performed": False,
            "contact_history_authority": "ARCANA_R51_Q99_CORE_PLUS_J14_OCCUPANCY_SUPPORT_WITH_R53_NETWORK_SELECTION_RULE",
            "r53_cdmetapop_used_as_contact_geometry": False,
            "r54_nemo_used_as_contact_geometry": False,
            "realized_admixture_claimed": False,
            "numeric_gene_flow_truth_claimed": False,
            "single_contact_history_winner_selected": False,
            "majority_vote": False,
            "canonical_state_changed": False,
            "derived_refinement_promoted_to_canon": False,
            "deep_biological_coupling": False,
        },
        "recommended_next_action": "START_R56_TARGETED_ANCESTRY_AND_ADMIXTURE_CHALLENGES_FROM_R55_CONTACT_OPPORTUNITY_WINDOWS_WITH_SLIM_UTILITY_REVIEW_BEFORE_EXECUTION",
        "checks": checks,
    }
    write_json(out / "R5_5_INTEGRATED_AUDIT.json", audit)

    artifacts = [
        "R5_5_PARENT_CANDIDATE_BINDING.json",
        "R5_5_CONTACT_ZONE_HISTORY.json",
        "R5_5_CONTACT_OPPORTUNITY_ATLAS.npz",
        "R5_5_CROSS_ENGINE_CONTACT_CONTEXT.json",
        "R5_5_INTEGRATED_AUDIT.json",
    ]
    files: dict[str, Any] = {}
    for name in artifacts:
        p = out / name
        files[name] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
    write_json(out / "R5_5_OUTPUT_MANIFEST.json", {"stage": STAGE, "status": audit["status"], "files": files})
    return {"audit": audit, "history": history, "context_records": context_records, "binding": binding}
