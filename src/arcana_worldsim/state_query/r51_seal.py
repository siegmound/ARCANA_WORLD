from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json
import numpy as np

from . import r51_cradle as c
from . import r51_structure as s

STAGE = c.STAGE
OUT_REL = Path("outputs/v0_6D1_R5_1")
SOURCE_MANIFEST_REL = Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_1.json")

EXPECTED_ATLAS_SHA256 = "9d4a70780785bdda7d1a51549d3b842450d6b563cab44684229157f073707caa"
EXPECTED_STRUCTURE_MANIFEST_SHA256 = "d97fbe2288391cd1df5bf587eeee6ea77e2d9ccd258ae908bb5b608b95b06509"
EXPECTED_CANDIDATE_IDS = ("RPT_010_D02", "RPT_009_D02")
EXPECTED_REGION_RECORD_COUNT = 300
EXPECTED_PARETO_REGION_RECORD_COUNT = 157
EXPECTED_FAMILY_COUNT = 161
EXPECTED_ALL_THRESHOLD_FAMILY_COUNT = 12
EXPECTED_PER_CANDIDATE = {
    "RPT_010_D02": {
        "family_count": 79,
        "all_threshold_family_count": 7,
        "three_plus_threshold_family_count": 19,
        "q99_survivor_count": 7,
    },
    "RPT_009_D02": {
        "family_count": 82,
        "all_threshold_family_count": 5,
        "three_plus_threshold_family_count": 19,
        "q99_survivor_count": 5,
    },
}
EXPECTED_CROSS_LINEAGE_OVERLAP_PAIR_COUNT = 4
EXPECTED_CROSS_LINEAGE_MAX_JACCARD = 0.5
EXPECTED_CLOSURE_READINESS = "READY_FOR_R51_SEAL_NO_NEW_EXTERNAL_ENGINE_REQUIRED"
EXPECTED_NEXT_ACTION = "SEAL_R51_THEN_USE_RANGESHIFTER_IN_R52_FOR_TARGETED_EXPANSION_CORRIDOR_VALIDATION"
EXPECTED_RANGESHIFTER_ACTION = "DEFER_NEW_EXECUTION_TO_R5_2_TARGETED_CORRIDOR_VALIDATION"

CANDIDATE_ALLOWLIST = (
    "R5_1_ENGINE_UTILITY_REVIEW.json",
    "R5_1_CRADLE_OPPORTUNITY_ATLAS.npz",
    "R5_1_OCCUPIED_ENVIRONMENT_ENVELOPES.json",
    "R5_1_CRADLE_CANDIDATE_REGISTRY.json",
    "R5_1_INTEGRATED_AUDIT.json",
)
STRUCTURE_ALLOWLIST = (
    "R5_1_CRADLE_STRUCTURE_AND_ENGINE_ADJUDICATION.json",
    "R5_1_ROBUST_REGION_FAMILIES.json",
    "R5_1_REGION_FAMILY_TEMPORAL_SUPPORT.npz",
)


class R51SealError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def validate_source_manifest(root: Path) -> dict[str, Any]:
    root = Path(root)
    manifest_path = root / SOURCE_MANIFEST_REL
    checks: dict[str, bool] = {"source_manifest_present": manifest_path.is_file()}
    files: dict[str, Any] = {}
    if manifest_path.is_file():
        manifest = load_json(manifest_path)
        files = dict(manifest.get("files") or {})
        checks["source_manifest_stage_exact"] = manifest.get("stage") == STAGE
        checks["source_manifest_count_exact"] = int(manifest.get("source_authority_file_count", -1)) == len(files)
        checks["source_manifest_nonempty"] = len(files) > 0
        for rel, meta in files.items():
            p = root / rel
            checks[f"source::{rel}"] = (
                p.is_file()
                and p.stat().st_size == int(meta.get("bytes", -1))
                and sha256_file(p) == meta.get("sha256")
            )
    else:
        checks["source_manifest_stage_exact"] = False
        checks["source_manifest_count_exact"] = False
        checks["source_manifest_nonempty"] = False
    failed = [k for k, v in checks.items() if not bool(v)]
    return {
        "status": "PASS_R51_SEAL_SOURCE_AUTHORITY" if not failed else "BLOCKED_R51_SEAL_SOURCE_AUTHORITY",
        "checks": checks,
        "failed": failed,
        "file_count": len(files),
        "manifest_sha256": sha256_file(manifest_path) if manifest_path.is_file() else None,
    }


def validate_structure_semantics(structure: dict[str, Any], *, strict_expected_run: bool = True) -> dict[str, bool]:
    per = structure.get("per_candidate") or {}
    overlap = structure.get("cross_lineage_all_threshold_core_overlap") or {}
    engine = structure.get("engine_adjudication") or {}
    rs = engine.get("RangeShifter") or {}
    checks: dict[str, bool] = {
        "structure_status_exact": structure.get("status") == "PASS_R51_CRADLE_STRUCTURE_AND_ENGINE_ADJUDICATION",
        "structure_semantics_no_weighted_single_winner": structure.get("semantics") == "THRESHOLD_NESTED_REGION_FAMILIES_AND_TEMPORAL_SUPPORT_NO_WEIGHTED_SCORE_NO_SINGLE_WINNER",
        "candidate_ids_exact": tuple(structure.get("candidate_ids") or []) == EXPECTED_CANDIDATE_IDS,
        "registry_reconstruction_exact": structure.get("registry_reconstruction_exact") is True,
        "pareto_not_final_selection": structure.get("pareto_front_is_final_selection") is False,
        "both_lineages_have_all_threshold_family": all(int((per.get(cid) or {}).get("all_threshold_family_count", 0)) > 0 for cid in EXPECTED_CANDIDATE_IDS),
        "closure_readiness_exact": structure.get("closure_readiness") == EXPECTED_CLOSURE_READINESS,
        "recommended_next_action_exact": structure.get("recommended_next_action") == EXPECTED_NEXT_ACTION,
        "no_new_external_engine_required": engine.get("new_external_engine_execution_required_for_r51_closure") is False,
        "no_new_external_engine_authorized": engine.get("new_external_engine_execution_authorized_in_r51") is False,
        "rangeshifter_deferred_to_r52": rs.get("action") == EXPECTED_RANGESHIFTER_ACTION,
        "external_engine_not_target_authority": engine.get("external_engine_defines_arcana_target") is False,
        "no_majority_vote": engine.get("majority_vote") is False,
        "canonical_state_unchanged": structure.get("canonical_state_changed") is False,
        "derived_refinement_not_promoted": structure.get("derived_refinement_promoted_to_canon") is False,
        "deep_biological_coupling_off": structure.get("deep_biological_coupling") is False,
    }
    if strict_expected_run:
        checks.update({
            "region_record_count_exact": int(structure.get("region_record_count", -1)) == EXPECTED_REGION_RECORD_COUNT,
            "pareto_region_record_count_exact": int(structure.get("pareto_region_record_count", -1)) == EXPECTED_PARETO_REGION_RECORD_COUNT,
            "family_count_exact": int(structure.get("family_count", -1)) == EXPECTED_FAMILY_COUNT,
            "all_threshold_family_count_exact": int(structure.get("all_threshold_family_count", -1)) == EXPECTED_ALL_THRESHOLD_FAMILY_COUNT,
            "per_candidate_counts_exact": per == EXPECTED_PER_CANDIDATE,
            "cross_lineage_overlap_pair_count_exact": int(overlap.get("nonzero_overlap_pair_count", -1)) == EXPECTED_CROSS_LINEAGE_OVERLAP_PAIR_COUNT,
            "cross_lineage_max_jaccard_exact": abs(float(overlap.get("max_jaccard", float("nan"))) - EXPECTED_CROSS_LINEAGE_MAX_JACCARD) < 1e-12,
        })
    return {k: bool(v) for k, v in checks.items()}


def _verify_manifest(root: Path, manifest_path: Path, expected_allowlist: tuple[str, ...]) -> dict[str, bool]:
    out = Path(root) / OUT_REL
    checks: dict[str, bool] = {f"present::{manifest_path.name}": manifest_path.is_file()}
    if not manifest_path.is_file():
        checks["manifest_allowlist_exact"] = False
        checks["manifest_hashes_exact"] = False
        return checks
    m = load_json(manifest_path)
    files = dict(m.get("files") or {})
    checks["manifest_allowlist_exact"] = set(files) == set(expected_allowlist)
    checks["manifest_hashes_exact"] = all(
        (out / name).is_file()
        and (out / name).stat().st_size == int(meta.get("bytes", -1))
        and sha256_file(out / name) == meta.get("sha256")
        for name, meta in files.items()
    )
    return checks


def _json_exact(a: Any, b: Any) -> bool:
    return a == b


def _npz_exact(path: Path, expected_arrays: dict[str, np.ndarray]) -> bool:
    try:
        with np.load(path, allow_pickle=False) as z:
            if set(z.files) != set(expected_arrays):
                return False
            for key, expected in expected_arrays.items():
                actual = np.asarray(z[key])
                expected = np.asarray(expected)
                if actual.dtype.kind in "fc" or expected.dtype.kind in "fc":
                    if actual.shape != expected.shape or not np.array_equal(actual, expected, equal_nan=True):
                        return False
                else:
                    if not np.array_equal(actual, expected):
                        return False
        return True
    except Exception:
        return False


def validate_and_build_seal(root: Path, *, allow_non_scientific_dev: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    out = root / OUT_REL
    strict = not allow_non_scientific_dev
    checks: dict[str, bool] = {}

    source = validate_source_manifest(root)
    checks["source_authority_pass"] = not source["failed"]

    parent = c.validate_authority(root, allow_non_scientific_dev)
    checks["immutable_parent_authority_pass"] = not parent["failed"]

    candidate_integrity = s.validate_candidate_outputs(root, allow_non_scientific_dev=allow_non_scientific_dev)
    checks["candidate_output_integrity_pass"] = not candidate_integrity["failed"]

    candidate_manifest_path = out / "R5_1_OUTPUT_MANIFEST.json"
    structure_manifest_path = out / "R5_1_STRUCTURE_ADJUDICATION_MANIFEST.json"
    checks.update({f"candidate_{k}": v for k, v in _verify_manifest(root, candidate_manifest_path, CANDIDATE_ALLOWLIST).items()})
    checks.update({f"structure_{k}": v for k, v in _verify_manifest(root, structure_manifest_path, STRUCTURE_ALLOWLIST).items()})

    audit_path = out / "R5_1_INTEGRATED_AUDIT.json"
    structure_path = out / "R5_1_CRADLE_STRUCTURE_AND_ENGINE_ADJUDICATION.json"
    families_path = out / "R5_1_ROBUST_REGION_FAMILIES.json"
    temporal_path = out / "R5_1_REGION_FAMILY_TEMPORAL_SUPPORT.npz"
    engine_review_path = out / "R5_1_ENGINE_UTILITY_REVIEW.json"
    atlas_path = out / "R5_1_CRADLE_OPPORTUNITY_ATLAS.npz"
    required_paths = (audit_path, structure_path, families_path, temporal_path, engine_review_path, atlas_path)
    for p in required_paths:
        checks[f"present::{p.name}"] = p.is_file()

    if all(p.is_file() for p in required_paths):
        audit = load_json(audit_path)
        structure = load_json(structure_path)
        families = load_json(families_path)
        engine_review = load_json(engine_review_path)

        checks["candidate_status_exact"] = audit.get("status") == "PASS_R51_EMERGENT_HOMINID_CRADLE_ECOLOGICAL_NICHE_DISCOVERY_CANDIDATE"
        checks["candidate_scientific_eligible"] = (audit.get("scientific_candidate_eligible") is True) if strict else True
        summary = audit.get("summary") or {}
        checks["candidate_atlas_hash_self_consistent"] = summary.get("atlas_sha256") == sha256_file(atlas_path)
        checks["atlas_exact_scientific_candidate_hash"] = (sha256_file(atlas_path) == EXPECTED_ATLAS_SHA256) if strict else True
        checks["structure_manifest_exact_scientific_candidate_hash"] = (sha256_file(structure_manifest_path) == EXPECTED_STRUCTURE_MANIFEST_SHA256) if strict else True
        checks["candidate_no_external_engine_execution"] = summary.get("new_external_engine_execution_performed") is False
        checks["candidate_canonical_state_unchanged"] = summary.get("canonical_state_changed") is False
        checks["candidate_deep_biological_coupling_off"] = summary.get("deep_biological_coupling") is False
        checks["candidate_cradle_semantics_exact"] = summary.get("cradle_semantics") == "MODEL_DERIVED_CRADLE_OPPORTUNITY_REGIONS_NOT_OBSERVED_LITERAL_BIRTHPLACE"
        checks["engine_utility_review_exact"] = engine_review == c.engine_utility_review()

        checks.update(validate_structure_semantics(structure, strict_expected_run=strict))

        try:
            recomputed = s.analyze_structure(root, allow_non_scientific_dev=allow_non_scientific_dev)
            checks["structure_recomputed_exact"] = _json_exact(recomputed["structure"], structure)
            expected_families = {
                "stage": STAGE,
                "status": "R51_THRESHOLD_NESTED_REGION_FAMILY_REGISTRY",
                "semantics": "FAMILIES_TRACK_CONNECTED_COMPONENT_DESCENDANTS_ACROSS_FIXED_90_95_97P5_99_PERCENTILE_THRESHOLDS",
                "families": recomputed["families"],
            }
            checks["family_registry_recomputed_exact"] = _json_exact(expected_families, families)
            expected_npz = {
                "age_ma": recomputed["age_ma"],
                "family_ids": recomputed["family_ids"],
                "ensemble_occupancy_fraction_by_age": recomputed["occupancy"],
            }
            checks["temporal_support_recomputed_exact"] = _npz_exact(temporal_path, expected_npz)
        except Exception:
            checks["structure_recomputed_exact"] = False
            checks["family_registry_recomputed_exact"] = False
            checks["temporal_support_recomputed_exact"] = False
    else:
        for key in (
            "candidate_status_exact", "candidate_scientific_eligible", "candidate_atlas_hash_self_consistent",
            "atlas_exact_scientific_candidate_hash", "structure_manifest_exact_scientific_candidate_hash",
            "candidate_no_external_engine_execution", "candidate_canonical_state_unchanged",
            "candidate_deep_biological_coupling_off", "candidate_cradle_semantics_exact",
            "engine_utility_review_exact", "structure_recomputed_exact", "family_registry_recomputed_exact",
            "temporal_support_recomputed_exact",
        ):
            checks[key] = False

    checks = {k: bool(v) for k, v in checks.items()}
    failed = [k for k, v in checks.items() if not v]

    artifact_names = list(CANDIDATE_ALLOWLIST) + ["R5_1_OUTPUT_MANIFEST.json"] + list(STRUCTURE_ALLOWLIST) + ["R5_1_STRUCTURE_ADJUDICATION_MANIFEST.json"]
    artifacts: dict[str, Any] = {}
    for name in artifact_names:
        p = out / name
        if p.is_file():
            artifacts[name] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}

    status = (
        "PASS_R51_EMERGENT_HOMINID_CRADLE_AND_ECOLOGICAL_NICHE_DISCOVERY_SEALED"
        if strict and not failed
        else "PASS_R51_NON_SCIENTIFIC_DEV_SEAL_VALIDATION"
        if (not strict and not failed)
        else "BLOCKED_R51_FINAL_SCIENTIFIC_SEAL"
    )
    sealed = bool(strict and not failed)
    seal = {
        "stage": STAGE,
        "status": status,
        "sealed": sealed,
        "scientific_seal": sealed,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failed": failed,
        "summary": {
            "candidate_ids": list(EXPECTED_CANDIDATE_IDS),
            "region_record_count": int(load_json(structure_path).get("region_record_count", -1)) if structure_path.is_file() else None,
            "pareto_region_record_count": int(load_json(structure_path).get("pareto_region_record_count", -1)) if structure_path.is_file() else None,
            "family_count": int(load_json(structure_path).get("family_count", -1)) if structure_path.is_file() else None,
            "all_threshold_family_count": int(load_json(structure_path).get("all_threshold_family_count", -1)) if structure_path.is_file() else None,
            "per_candidate": (load_json(structure_path).get("per_candidate") if structure_path.is_file() else None),
            "cross_lineage_overlap_pair_count": int(((load_json(structure_path).get("cross_lineage_all_threshold_core_overlap") or {}).get("nonzero_overlap_pair_count", -1))) if structure_path.is_file() else None,
            "cross_lineage_max_jaccard": float(((load_json(structure_path).get("cross_lineage_all_threshold_core_overlap") or {}).get("max_jaccard", float("nan")))) if structure_path.is_file() else None,
            "closure_readiness": load_json(structure_path).get("closure_readiness") if structure_path.is_file() else None,
            "RangeShifter_action": (((load_json(structure_path).get("engine_adjudication") or {}).get("RangeShifter") or {}).get("action")) if structure_path.is_file() else None,
            "new_external_engine_execution_performed": False,
            "new_external_engine_execution_required_for_r51_closure": False,
            "new_external_engine_execution_authorized_in_r51": False,
            "external_engine_defines_arcana_target": False,
            "majority_vote": False,
            "canonical_state_changed": False,
            "derived_refinement_promoted_to_canon": False,
            "deep_biological_coupling": False,
            "cradle_semantics": "MODEL_DERIVED_CRADLE_OPPORTUNITY_REGIONS_NOT_OBSERVED_LITERAL_BIRTHPLACE",
        },
        "authority": {
            "source_manifest_sha256": source.get("manifest_sha256"),
            "r50_final_seal_sha256": c.EXPECTED_R50_SEAL_SHA,
            "j14_spatial_authority_sha256": c.EXPECTED_J14_SHA,
            "j14_validation_seal_sha256": c.EXPECTED_J14_SEAL_SHA,
            "r327_macro_replay_sha256": c.EXPECTED_R327_SHA,
            "r327_human_200ka_checkpoint_sha256": c.EXPECTED_R327_CP_SHA,
            "r314_provider_seal_sha256": c.EXPECTED_R314_SEAL_SHA,
            "r51_atlas_sha256": sha256_file(atlas_path) if atlas_path.is_file() else None,
            "r51_candidate_output_manifest_sha256": sha256_file(candidate_manifest_path) if candidate_manifest_path.is_file() else None,
            "r51_structure_adjudication_manifest_sha256": sha256_file(structure_manifest_path) if structure_manifest_path.is_file() else None,
        },
        "sealed_artifacts": artifacts,
        "checks": checks,
        "next_action": "START_R52_TARGETED_EXPANSION_CORRIDOR_VALIDATION_WITH_RANGESHIFTER_AS_GOVERNED_SUPPORT_NOT_CANONICAL_AUTHORITY" if sealed else "NONE_UNTIL_R51_SEAL_PASSES",
    }
    return seal


def write_final_seal(root: Path, seal: dict[str, Any]) -> tuple[Path, str]:
    path = Path(root) / OUT_REL / "R5_1_FINAL_SEAL.json"
    write_json(path, seal)
    return path, sha256_file(path)
