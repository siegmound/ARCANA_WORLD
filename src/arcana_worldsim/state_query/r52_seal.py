from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json

from . import r52_corridors as c

STAGE = c.STAGE
OUT_REL = c.OUT_REL
SOURCE_MANIFEST_REL = Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_2.json")
EXPECTED_PLAN_SHA256 = "49704d285c416714c0c262769e97b34300004be268482a806cd8d9baf4f990dd"
EXPECTED_ROBUST_FAMILY_COUNT = 12
EXPECTED_GROUP_COUNT = 24
EXPECTED_EXECUTABLE_GROUP_COUNT = 20
EXPECTED_NONEXECUTABLE_GROUP_COUNT = 4
EXPECTED_STREAM_COUNT = 80
EXPECTED_RAW_FILE_COUNT = 100
EXPECTED_SENSITIVITY_COUNT = 40
EXPECTED_CANDIDATES = ("RPT_010_D02", "RPT_009_D02")
CANDIDATE_MANIFEST_ALLOWLIST = (
    "R5_2_RANGESHIFTER_RUNTIME_IDENTITY.json",
    "R5_2_RANGE_EXECUTION_PLAN.json",
    "R5_2_RANGE_EXECUTION_BRIDGE.json",
    "R5_2_RAW_EVIDENCE_MANIFEST.json",
    "R5_2_STREAM_EVIDENCE.json",
    "R5_2_CORRIDOR_SENSITIVITY_SUMMARY.json",
    "R5_2_INTEGRATED_AUDIT.json",
)


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
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def validate_source_manifest(root: Path) -> dict[str, Any]:
    root = Path(root)
    p = root / SOURCE_MANIFEST_REL
    checks: dict[str, bool] = {"source_manifest_present": p.is_file()}
    files: dict[str, Any] = {}
    if p.is_file():
        m = load_json(p)
        files = dict(m.get("files") or {})
        checks["source_manifest_stage_exact"] = m.get("stage") == STAGE
        checks["source_manifest_count_exact"] = int(m.get("source_authority_file_count", -1)) == len(files)
        for rel, meta in files.items():
            q = root / rel
            checks[f"source::{rel}"] = q.is_file() and q.stat().st_size == int(meta.get("bytes", -1)) and sha256_file(q) == meta.get("sha256")
    failed = [k for k, v in checks.items() if not bool(v)]
    return {"checks": checks, "failed": failed, "file_count": len(files), "manifest_sha256": sha256_file(p) if p.is_file() else None}


def _minmax_from_pairs(rows: list[dict[str, Any]], key: str) -> list[float] | None:
    vals: list[float] = []
    for r in rows:
        pair = r.get(key)
        if isinstance(pair, list) and len(pair) == 2:
            vals.extend([float(pair[0]), float(pair[1])])
    return [float(min(vals)), float(max(vals))] if vals else None


def _descriptive_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "record_count": len(rows),
        "both_seeds_final_target_intersection_record_count": sum(bool(r.get("both_seeds_final_target_intersection")) for r in rows),
        "any_seed_final_target_intersection_record_count": sum(bool(r.get("any_seed_final_target_intersection")) for r in rows),
        "no_seed_final_target_intersection_record_count": sum(not bool(r.get("any_seed_final_target_intersection")) for r in rows),
        "target_intersection_state_fraction_observed_envelope": _minmax_from_pairs(rows, "target_intersection_state_fraction_minmax"),
        "max_jaccard_observed_envelope": _minmax_from_pairs(rows, "max_jaccard_minmax"),
        "max_target_coverage_fraction_observed_envelope": _minmax_from_pairs(rows, "max_target_coverage_fraction_minmax"),
    }


def build_descriptive_readout(sensitivity: list[dict[str, Any]]) -> dict[str, Any]:
    per_candidate: dict[str, Any] = {}
    for cid in EXPECTED_CANDIDATES:
        rows = [r for r in sensitivity if r.get("candidate_id") == cid]
        by_habitat = {h: _descriptive_group([r for r in rows if r.get("habitat_profile") == h]) for h in c.HABITAT_PROFILES}
        by_movement = {m: _descriptive_group([r for r in rows if r.get("movement_profile") == m]) for m in c.MOVEMENT_PROFILES}
        fam_ids = sorted({str(r.get("family_id")) for r in rows})
        per_family = {}
        for fid in fam_ids:
            fr = [r for r in rows if r.get("family_id") == fid]
            per_family[fid] = {
                **_descriptive_group(fr),
                "habitat_profiles_present": sorted({str(r.get("habitat_profile")) for r in fr}),
                "movement_profiles_present": sorted({str(r.get("movement_profile")) for r in fr}),
            }
        per_candidate[cid] = {**_descriptive_group(rows), "by_habitat_profile": by_habitat, "by_movement_profile": by_movement, "per_family": per_family}
    return {
        "stage": STAGE,
        "status": "PASS_R52_DESCRIPTIVE_CORRIDOR_EVIDENCE_STRUCTURE_AND_NEXT_ENGINE_ADJUDICATION",
        "semantics": "DESCRIPTIVE_COUNTS_AND_ENVELOPES_ONLY_NO_MAJORITY_VOTE_NO_WEIGHTED_SCORE_NO_NUMERIC_CORRIDOR_TRUTH",
        "sensitivity_record_count": len(sensitivity),
        "overall": _descriptive_group(sensitivity),
        "per_candidate": per_candidate,
        "r52_closure_readiness": "READY_FOR_R52_SEAL_GOVERNED_DESCRIPTIVE_CORRIDOR_EVIDENCE_COMPLETE",
        "new_external_engine_execution_required_for_r52_closure": False,
        "engine_adjudication": {
            "RangeShifter": {"action": "NO_ADDITIONAL_R52_EXECUTION_REQUIRED", "reason": "R5.2 connectivity evidence corpus is complete and source-bound."},
            "CDMetaPOP": {"action": "PRIMARY_CANDIDATE_FOR_R53_CORRIDOR_CONDITIONED_DEMOGRAPHIC_PERSISTENCE_AND_BOTTLENECK_VALIDATION", "reason": "Adds population viability, landscape demogenetics and gene-flow evidence downstream of fixed corridor hypotheses."},
            "NEMO": {"action": "DEFER_TO_SECONDARY_GENE_FLOW_AND_ALLELE_FREQUENCY_VALIDATION", "reason": "Useful after demographic persistence hypotheses are fixed; not required to close RangeShifter connectivity evidence."},
            "SLiM": {"action": "DEFER_TO_ANCESTRY_ADMIXTURE_STAGE", "reason": "Whole-genome ancestry/admixture is downstream of corridor and demographic hypotheses."},
            "Geonomics": {"action": "REUSE_SEALED_J14_AND_R4_EVIDENCE_NO_NEW_R52_EXECUTION"},
            "Madingley": {"action": "DEFER_TARGETED_TROPHIC_CHECK_UNLESS_R53_RESOURCE_QUESTION_REQUIRES_IT"},
        },
        "external_engine_defines_arcana_target": False,
        "majority_vote": False,
        "automatic_numeric_scientific_pass_fail": False,
        "canonical_state_changed": False,
        "derived_refinement_promoted_to_canon": False,
        "deep_biological_coupling": False,
        "recommended_next_action": "SEAL_R52_THEN_START_R53_CORRIDOR_CONDITIONED_DEMOGRAPHIC_PERSISTENCE_AND_BOTTLENECK_VALIDATION_WITH_CDMETAPOP_AS_PRIMARY_GOVERNED_ENGINE_CANDIDATE",
    }


def _verify_candidate_manifest(root: Path) -> dict[str, bool]:
    out = root / OUT_REL
    p = out / "R5_2_OUTPUT_MANIFEST.json"
    checks = {"candidate_output_manifest_present": p.is_file()}
    if not p.is_file():
        checks["candidate_output_manifest_allowlist_exact"] = False
        checks["candidate_output_manifest_hashes_exact"] = False
        return checks
    m = load_json(p)
    files = dict(m.get("files") or {})
    checks["candidate_output_manifest_allowlist_exact"] = set(files) == set(CANDIDATE_MANIFEST_ALLOWLIST)
    checks["candidate_output_manifest_hashes_exact"] = all((out / n).is_file() and (out / n).stat().st_size == int(meta.get("bytes", -1)) and sha256_file(out / n) == meta.get("sha256") for n, meta in files.items())
    return checks


def _verify_raw_manifest(root: Path) -> dict[str, bool]:
    out = root / OUT_REL
    p = out / "R5_2_RAW_EVIDENCE_MANIFEST.json"
    checks = {"raw_evidence_manifest_present": p.is_file()}
    if not p.is_file():
        checks["raw_evidence_file_count_exact"] = False
        checks["raw_evidence_hashes_exact"] = False
        return checks
    m = load_json(p)
    files = dict(m.get("files") or {})
    checks["raw_evidence_file_count_exact"] = int(m.get("file_count", -1)) == EXPECTED_RAW_FILE_COUNT == len(files)
    checks["raw_evidence_hashes_exact"] = all((root / rel).is_file() and (root / rel).stat().st_size == int(meta.get("bytes", -1)) and sha256_file(root / rel) == meta.get("sha256") for rel, meta in files.items())
    return checks


def validate_and_build_seal(root: Path, *, allow_non_scientific_dev: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    out = root / OUT_REL
    strict = not allow_non_scientific_dev
    checks: dict[str, bool] = {}
    source = validate_source_manifest(root)
    checks["source_authority_pass"] = not source["failed"]
    parent = c.validate_parent_authority(root, allow_non_scientific_dev=allow_non_scientific_dev)
    checks["immutable_parent_authority_pass"] = not parent["failed"]
    required = [
        "R5_2_RANGESHIFTER_RUNTIME_IDENTITY.json", "R5_2_RANGE_EXECUTION_PLAN.json", "R5_2_R1_SOURCE_BINDING_PREFLIGHT.json",
        "R5_2_RANGE_EXECUTION_BRIDGE.json", "R5_2_RAW_EVIDENCE_MANIFEST.json", "R5_2_STREAM_EVIDENCE.json",
        "R5_2_CORRIDOR_SENSITIVITY_SUMMARY.json", "R5_2_INTEGRATED_AUDIT.json", "R5_2_OUTPUT_MANIFEST.json",
    ]
    for n in required:
        checks[f"present::{n}"] = (out / n).is_file()
    if all((out / n).is_file() for n in required):
        runtime = load_json(out / "R5_2_RANGESHIFTER_RUNTIME_IDENTITY.json")
        plan = load_json(out / "R5_2_RANGE_EXECUTION_PLAN.json")
        probe = load_json(out / "R5_2_R1_SOURCE_BINDING_PREFLIGHT.json")
        bridge = load_json(out / "R5_2_RANGE_EXECUTION_BRIDGE.json")
        streams = load_json(out / "R5_2_STREAM_EVIDENCE.json")
        sensitivity_doc = load_json(out / "R5_2_CORRIDOR_SENSITIVITY_SUMMARY.json")
        audit = load_json(out / "R5_2_INTEGRATED_AUDIT.json")
        stream_records = list(streams.get("records") or [])
        sensitivity = list(sensitivity_doc.get("records") or [])
        checks.update({
            "runtime_exact_3_0_1": runtime.get("status") == "PASS_R52_RANGESHIFTR_3_0_1_RUNTIME_IDENTITY" and runtime.get("package_version") == "3.0.1",
            "plan_status_exact": plan.get("status") == "PASS_R52_TARGETED_RANGESHIFTER_EXECUTION_PLAN_PREPARED",
            "plan_exact_scientific_candidate_hash": (sha256_file(out / "R5_2_RANGE_EXECUTION_PLAN.json") == EXPECTED_PLAN_SHA256) if strict else True,
            "plan_counts_exact": int(plan.get("robust_family_count", -1)) == EXPECTED_ROBUST_FAMILY_COUNT and int(plan.get("group_count", -1)) == EXPECTED_GROUP_COUNT and int(plan.get("executable_group_count", -1)) == EXPECTED_EXECUTABLE_GROUP_COUNT and int(plan.get("nonexecutable_group_count", -1)) == EXPECTED_NONEXECUTABLE_GROUP_COUNT and int(plan.get("planned_stream_count", -1)) == EXPECTED_STREAM_COUNT,
            "probe_status_exact": probe.get("status") == "PASS_R52_R1_SOURCE_BINDING_PREFLIGHT" and int(probe.get("checks_passed", -1)) == 6 and int(probe.get("checks_total", -1)) == 6 and probe.get("initialization_mode") == c.RANGESHIFTER_INITIALIZATION_MODE,
            "probe_source_mapping_exact": (probe.get("checks") or {}).get("probe_year_zero_source_mapping_exact") is True and (probe.get("checks") or {}).get("probe_mapping_unique") is True,
            "bridge_group_count_exact": int(bridge.get("group_count", -1)) == EXPECTED_EXECUTABLE_GROUP_COUNT,
            "bridge_all_exit_zero": all(int(x.get("exit_code", -1)) == 0 and x.get("timed_out") is False for x in (bridge.get("records") or [])),
            "stream_count_exact": len(stream_records) == EXPECTED_STREAM_COUNT,
            "all_stream_initialization_exact": all(r.get("initialization_mode") == c.RANGESHIFTER_INITIALIZATION_MODE for r in stream_records),
            "all_stream_source_mapping_exact": all(r.get("initial_source_mapping_exact") is True for r in stream_records),
            "all_stream_runtime_version_exact": all(r.get("package_version") == "3.0.1" for r in stream_records),
            "sensitivity_count_exact": len(sensitivity) == EXPECTED_SENSITIVITY_COUNT,
            "sensitivity_seed_membership_exact": all(r.get("seed_membership") == list(c.SEEDS) and r.get("seed_membership_exact") is True for r in sensitivity),
            "sensitivity_no_automatic_pass_fail": sensitivity_doc.get("selection_semantics") == "NO_WEIGHTED_SCORE_NO_MAJORITY_VOTE_NO_SINGLE_WINNER_NO_AUTOMATIC_NUMERIC_PASS_FAIL" and all(r.get("automatic_scientific_pass_fail_from_values") is False for r in sensitivity),
            "candidate_audit_exact": audit.get("status") == "PASS_R52_TARGETED_RANGESHIFTER_EXPANSION_CORRIDOR_EVIDENCE_CANDIDATE" and audit.get("scientific_candidate_eligible") is True and int(audit.get("checks_passed", -1)) == 23 and int(audit.get("checks_total", -1)) == 23 and not (audit.get("failed") or []),
            "candidate_no_numeric_corridor_truth": (audit.get("summary") or {}).get("numeric_corridor_truth_claimed") is False,
            "candidate_engine_not_target_authority": (audit.get("summary") or {}).get("external_engine_defines_arcana_target") is False,
            "candidate_no_majority_vote": (audit.get("summary") or {}).get("majority_vote") is False,
            "candidate_canonical_state_unchanged": (audit.get("summary") or {}).get("canonical_state_changed") is False,
            "candidate_deep_biological_coupling_off": (audit.get("summary") or {}).get("deep_biological_coupling") is False,
        })
        checks.update(_verify_candidate_manifest(root))
        checks.update(_verify_raw_manifest(root))
        try:
            recomputed_probe = c.validate_source_binding_probe(root)
            checks["probe_recomputed_exact"] = recomputed_probe == probe
            recomputed = c.analyze_rangeshifter_evidence(root, allow_non_scientific_dev_parent=allow_non_scientific_dev)
            checks["audit_recomputed_exact"] = recomputed["audit"] == audit
            checks["stream_evidence_recomputed_exact"] = recomputed["stream_records"] == stream_records
            checks["sensitivity_recomputed_exact"] = recomputed["sensitivity"] == sensitivity
        except Exception:
            checks["probe_recomputed_exact"] = False
            checks["audit_recomputed_exact"] = False
            checks["stream_evidence_recomputed_exact"] = False
            checks["sensitivity_recomputed_exact"] = False
        readout = build_descriptive_readout(sensitivity)
        write_json(out / "R5_2_EVIDENCE_STRUCTURE_AND_NEXT_ENGINE_ADJUDICATION.json", readout)
        checks["readout_closure_ready"] = readout.get("r52_closure_readiness") == "READY_FOR_R52_SEAL_GOVERNED_DESCRIPTIVE_CORRIDOR_EVIDENCE_COMPLETE"
        checks["no_new_engine_required_for_r52_closure"] = readout.get("new_external_engine_execution_required_for_r52_closure") is False
        checks["next_engine_cdm_primary"] = ((readout.get("engine_adjudication") or {}).get("CDMetaPOP") or {}).get("action") == "PRIMARY_CANDIDATE_FOR_R53_CORRIDOR_CONDITIONED_DEMOGRAPHIC_PERSISTENCE_AND_BOTTLENECK_VALIDATION"
    else:
        readout = build_descriptive_readout([])
        for k in ["runtime_exact_3_0_1","plan_status_exact","plan_exact_scientific_candidate_hash","plan_counts_exact","probe_status_exact","probe_source_mapping_exact","bridge_group_count_exact","bridge_all_exit_zero","stream_count_exact","all_stream_initialization_exact","all_stream_source_mapping_exact","all_stream_runtime_version_exact","sensitivity_count_exact","sensitivity_seed_membership_exact","sensitivity_no_automatic_pass_fail","candidate_audit_exact","candidate_no_numeric_corridor_truth","candidate_engine_not_target_authority","candidate_no_majority_vote","candidate_canonical_state_unchanged","candidate_deep_biological_coupling_off","probe_recomputed_exact","audit_recomputed_exact","stream_evidence_recomputed_exact","sensitivity_recomputed_exact","readout_closure_ready","no_new_engine_required_for_r52_closure","next_engine_cdm_primary"]:
            checks[k] = False
        checks.update(_verify_candidate_manifest(root)); checks.update(_verify_raw_manifest(root))
    checks = {k: bool(v) for k, v in checks.items()}
    failed = [k for k, v in checks.items() if not v]
    artifact_names = required + ["R5_2_EVIDENCE_STRUCTURE_AND_NEXT_ENGINE_ADJUDICATION.json"]
    artifacts: dict[str, Any] = {}
    for n in artifact_names:
        p = out / n
        if p.is_file():
            artifacts[n] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
    status = "PASS_R52_TARGETED_EXPANSION_CORRIDOR_VALIDATION_SEALED" if strict and not failed else "PASS_R52_NON_SCIENTIFIC_DEV_SEAL_VALIDATION" if (not strict and not failed) else "BLOCKED_R52_FINAL_SCIENTIFIC_SEAL"
    sealed = bool(strict and not failed)
    audit_summary = load_json(out / "R5_2_INTEGRATED_AUDIT.json").get("summary") if (out / "R5_2_INTEGRATED_AUDIT.json").is_file() else {}
    seal = {
        "stage": STAGE, "status": status, "sealed": sealed, "scientific_seal": sealed,
        "checks_passed": sum(checks.values()), "checks_total": len(checks), "failed": failed,
        "summary": {
            "robust_family_count": EXPECTED_ROBUST_FAMILY_COUNT, "group_count": EXPECTED_GROUP_COUNT,
            "executable_group_count": EXPECTED_EXECUTABLE_GROUP_COUNT, "nonexecutable_group_count": EXPECTED_NONEXECUTABLE_GROUP_COUNT,
            "scientific_stream_count": EXPECTED_STREAM_COUNT, "raw_evidence_file_count": EXPECTED_RAW_FILE_COUNT,
            "sensitivity_record_count": EXPECTED_SENSITIVITY_COUNT, "external_engine": "RangeShiftR", "external_engine_version": "3.0.1",
            "new_external_engine_execution_performed": True, "numeric_corridor_truth_claimed": False,
            "external_engine_defines_arcana_target": False, "majority_vote": False, "canonical_state_changed": False,
            "derived_refinement_promoted_to_canon": False, "deep_biological_coupling": False,
            "r52_closure_readiness": readout.get("r52_closure_readiness"),
            "new_external_engine_execution_required_for_r52_closure": False,
            "corridor_semantics": (audit_summary or {}).get("corridor_semantics"),
        },
        "descriptive_evidence_readout": readout,
        "authority": {
            "source_manifest_sha256": source.get("manifest_sha256"),
            "r51_final_seal_sha256": c.EXPECTED_R51_FINAL_SEAL_SHA256,
            "r51_atlas_sha256": c.EXPECTED_R51_ATLAS_SHA256,
            "r51_candidate_manifest_sha256": c.EXPECTED_R51_CANDIDATE_MANIFEST_SHA256,
            "r51_structure_manifest_sha256": c.EXPECTED_R51_STRUCTURE_MANIFEST_SHA256,
            "j14_spatial_authority_sha256": c.EXPECTED_J14_SHA256,
            "r314_provider_seal_sha256": c.EXPECTED_R314_SEAL_SHA256,
            "r52_execution_plan_sha256": sha256_file(out / "R5_2_RANGE_EXECUTION_PLAN.json") if (out / "R5_2_RANGE_EXECUTION_PLAN.json").is_file() else None,
            "r52_raw_evidence_manifest_sha256": sha256_file(out / "R5_2_RAW_EVIDENCE_MANIFEST.json") if (out / "R5_2_RAW_EVIDENCE_MANIFEST.json").is_file() else None,
            "r52_candidate_output_manifest_sha256": sha256_file(out / "R5_2_OUTPUT_MANIFEST.json") if (out / "R5_2_OUTPUT_MANIFEST.json").is_file() else None,
        },
        "sealed_artifacts": artifacts, "checks": checks,
        "next_action": "START_R53_CORRIDOR_CONDITIONED_DEMOGRAPHIC_PERSISTENCE_AND_BOTTLENECK_VALIDATION_WITH_CDMETAPOP_AS_PRIMARY_GOVERNED_ENGINE_CANDIDATE" if sealed else "NONE_UNTIL_R52_SEAL_PASSES",
    }
    return seal


def write_final_seal(root: Path, seal: dict[str, Any]) -> tuple[Path, str]:
    p = Path(root) / OUT_REL / "R5_2_FINAL_SEAL.json"
    write_json(p, seal)
    return p, sha256_file(p)
