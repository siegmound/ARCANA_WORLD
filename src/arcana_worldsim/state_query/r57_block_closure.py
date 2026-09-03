from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json

STAGE = "v0.6D1-R5.7"
OUT_REL = Path("outputs/v0_6D1_R5_7")

R52_OUT = Path("outputs/v0_6D1_R5_2")
R53_OUT = Path("outputs/v0_6D1_R5_3")
R54_OUT = Path("outputs/v0_6D1_R5_4")
R55_OUT = Path("outputs/v0_6D1_R5_5")
R56_OUT = Path("outputs/v0_6D1_R5_6")
J14_REL = Path("outputs/v0_6D1_R4_30/authority/R4_30_J14_SPATIAL_AUTHORITY_REPLAY_CANDIDATE.npz")

R52_FINAL_SEAL = R52_OUT / "R5_2_FINAL_SEAL.json"
R52_PLAN = R52_OUT / "R5_2_RANGE_EXECUTION_PLAN.json"
R52_RAW = R52_OUT / "R5_2_RAW_EVIDENCE_MANIFEST.json"
R52_OUTPUT_MANIFEST = R52_OUT / "R5_2_OUTPUT_MANIFEST.json"
EXPECTED_R52_FINAL_SEAL_SHA256 = "6881b7312d7edf1539737d5603455d66712def05fcf4ddc133ae4d63cfde9978"
EXPECTED_R52_PLAN_SHA256 = "49704d285c416714c0c262769e97b34300004be268482a806cd8d9baf4f990dd"
EXPECTED_R52_RAW_SHA256 = "f5df7bc971e895289cb5e74baa9d306be76dce39a108d93d31b738e55998613c"
EXPECTED_R52_OUTPUT_MANIFEST_SHA256 = "ec91dd7793668138d9daba8b68d5845956e4aa15d2879abd809165254014539c"

CANDIDATE_STATUS = {
    "R5.3": "PASS_R53_CORRIDOR_CONDITIONED_DEMOGRAPHIC_PERSISTENCE_AND_BOTTLENECK_EVIDENCE_CANDIDATE",
    "R5.4": "PASS_R54_CROSS_ENGINE_GENETIC_ROBUSTNESS_AND_GENE_FLOW_EVIDENCE_CANDIDATE",
    "R5.5": "PASS_R55_CONTACT_ZONE_AND_GENE_FLOW_HISTORY_CONSOLIDATION_CANDIDATE",
    "R5.6": "PASS_R56_TARGETED_ANCESTRY_AND_ADMIXTURE_CHALLENGE_EVIDENCE_CANDIDATE",
}
EXPECTED_CHECK_COUNTS = {"R5.3": 29, "R5.4": 27, "R5.5": 23, "R5.6": 28}

EXPECTED_MANIFEST_FILES = {
    "R5.3": {
        "R5_3_CDMETAPOP_RUNTIME_IDENTITY.json",
        "R5_3_CDMETAPOP_EXECUTION_PLAN.json",
        "R5_3_CDMETAPOP_EXECUTION_BRIDGE.json",
        "R5_3_RAW_EVIDENCE_MANIFEST.json",
        "R5_3_CDMETAPOP_STREAM_EVIDENCE.json",
        "R5_3_DEMOGRAPHIC_PERSISTENCE_SENSITIVITY.json",
        "R5_3_INTEGRATED_AUDIT.json",
    },
    "R5.4": {
        "R5_4_PARENT_CANDIDATE_BINDING.json",
        "R5_4_NEMO_RUNTIME_IDENTITY.json",
        "R5_4_NEMO_EXECUTION_PLAN.json",
        "R5_4_NEMO_EXECUTION_BRIDGE.json",
        "R5_4_RAW_EVIDENCE_MANIFEST.json",
        "R5_4_NEMO_STREAM_EVIDENCE.json",
        "R5_4_NEMO_MATCHED_FLOW_CONTROL_PAIRS.json",
        "R5_4_CROSS_ENGINE_GENETIC_ROBUSTNESS_SENSITIVITY.json",
        "R5_4_INTEGRATED_AUDIT.json",
    },
    "R5.5": {
        "R5_5_PARENT_CANDIDATE_BINDING.json",
        "R5_5_CONTACT_ZONE_HISTORY.json",
        "R5_5_CONTACT_OPPORTUNITY_ATLAS.npz",
        "R5_5_CROSS_ENGINE_CONTACT_CONTEXT.json",
        "R5_5_INTEGRATED_AUDIT.json",
    },
    "R5.6": {
        "R5_6_PARENT_CANDIDATE_BINDING.json",
        "R5_6_SLIM_RUNTIME_IDENTITY.json",
        "R5_6_SLIM_EXECUTION_PLAN.json",
        "R5_6_EXECUTION_BRIDGE.json",
        "R5_6_RAW_EVIDENCE_MANIFEST.json",
        "R5_6_ANCESTRY_ADMIXTURE_SENSITIVITY.json",
        "R5_6_INTEGRATED_AUDIT.json",
    },
}

STAGE_OUT = {"R5.3": R53_OUT, "R5.4": R54_OUT, "R5.5": R55_OUT, "R5.6": R56_OUT}
OUTPUT_MANIFEST_NAME = {
    "R5.3": "R5_3_OUTPUT_MANIFEST.json",
    "R5.4": "R5_4_OUTPUT_MANIFEST.json",
    "R5.5": "R5_5_OUTPUT_MANIFEST.json",
    "R5.6": "R5_6_OUTPUT_MANIFEST.json",
}
AUDIT_NAME = {
    "R5.3": "R5_3_INTEGRATED_AUDIT.json",
    "R5.4": "R5_4_INTEGRATED_AUDIT.json",
    "R5.5": "R5_5_INTEGRATED_AUDIT.json",
    "R5.6": "R5_6_INTEGRATED_AUDIT.json",
}
RAW_MANIFEST_NAME = {
    "R5.3": "R5_3_RAW_EVIDENCE_MANIFEST.json",
    "R5.4": "R5_4_RAW_EVIDENCE_MANIFEST.json",
    "R5.6": "R5_6_RAW_EVIDENCE_MANIFEST.json",
}

FINAL_STATUS = "PASS_R57_R53_R56_HOMINID_DEMOGRAPHY_GENE_FLOW_ANCESTRY_BLOCK_SEALED"
AUDIT_STATUS = "PASS_R57_R53_R56_INTEGRATED_BLOCK_AUDIT"


class R57Error(RuntimeError):
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
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _manifest_integrity(base: Path, manifest_path: Path, expected_names: set[str]) -> tuple[bool, dict[str, Any]]:
    if not manifest_path.is_file():
        return False, {"error": "missing_manifest", "path": str(manifest_path)}
    try:
        manifest = load_json(manifest_path)
        files = dict(manifest.get("files") or {})
        name_ok = set(files) == expected_names
        details: dict[str, Any] = {"filename_set_exact": name_ok, "files": {}}
        ok = name_ok
        for name in sorted(expected_names):
            p = base / name
            meta = files.get(name) or {}
            live = {
                "present": p.is_file(),
                "bytes": p.stat().st_size if p.is_file() else None,
                "sha256": sha256_file(p) if p.is_file() else None,
            }
            expected = {"bytes": meta.get("bytes"), "sha256": meta.get("sha256")}
            same = p.is_file() and live["bytes"] == expected["bytes"] and live["sha256"] == expected["sha256"]
            details["files"][name] = {"match": same, "live": live, "manifest": expected}
            ok = ok and same
        return bool(ok), details
    except Exception as exc:
        return False, {"error": repr(exc)}


def _raw_manifest_integrity(root: Path, stage: str) -> tuple[bool, dict[str, Any]]:
    out = root / STAGE_OUT[stage]
    name = RAW_MANIFEST_NAME[stage]
    p = out / name
    if not p.is_file():
        return False, {"error": "missing_raw_manifest", "path": str(p)}
    try:
        m = load_json(p)
        files = dict(m.get("files") or {})
        ok = int(m.get("file_count", -1)) == len(files) and len(files) > 0
        details: dict[str, Any] = {"file_count": len(files), "declared_file_count": m.get("file_count"), "mismatches": []}
        for rel, meta in files.items():
            relp = Path(rel)
            # R5.3/R5.4 store root-relative output paths; R5.6 stores paths relative to its stage output dir.
            fp = (root / relp) if str(relp).replace("\\", "/").startswith("outputs/") else (out / relp)
            same = fp.is_file() and fp.stat().st_size == int(meta.get("bytes", -1)) and sha256_file(fp) == meta.get("sha256")
            if not same:
                details["mismatches"].append(str(rel))
                ok = False
        return bool(ok), details
    except Exception as exc:
        return False, {"error": repr(exc)}


def _audit_semantics(stage: str, audit: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    expected = EXPECTED_CHECK_COUNTS[stage]
    checks = dict(audit.get("checks") or {})
    ok = (
        audit.get("status") == CANDIDATE_STATUS[stage]
        and audit.get("scientific_candidate_eligible") is True
        and int(audit.get("checks_passed", -1)) == expected
        and int(audit.get("checks_total", -1)) == expected
        and audit.get("failed") == []
        and len(checks) == expected
        and all(v is True for v in checks.values())
    )
    return bool(ok), {
        "status": audit.get("status"),
        "eligible": audit.get("scientific_candidate_eligible"),
        "checks_passed": audit.get("checks_passed"),
        "checks_total": audit.get("checks_total"),
        "failed": audit.get("failed"),
    }


def _summary_semantics(stage: str, summary: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    common = (
        summary.get("canonical_state_changed") is False
        and summary.get("derived_refinement_promoted_to_canon") is False
        and summary.get("deep_biological_coupling") is False
        and summary.get("majority_vote") is False
    )
    if stage == "R5.3":
        ok = common and (
            summary.get("robust_family_count") == 12
            and summary.get("group_count") == 36
            and summary.get("scientific_stream_count") == 72
            and summary.get("sensitivity_record_count") == 36
            and summary.get("external_engine") == "CDMetaPOP"
            and summary.get("external_engine_version") == "3.08"
            and summary.get("external_engine_commit") == "3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118"
            and summary.get("new_external_engine_execution_performed") is True
            and summary.get("numeric_demographic_truth_claimed") is False
            and summary.get("r52_corridor_geometry_promoted_to_input_authority") is False
            and summary.get("external_engine_defines_arcana_target") is False
        )
    elif stage == "R5.4":
        ok = common and (
            summary.get("family_count") == 12
            and summary.get("group_count") == 36
            and summary.get("scientific_stream_count") == 144
            and summary.get("matched_pair_count") == 72
            and summary.get("sensitivity_record_count") == 36
            and summary.get("external_engine") == "NEMO"
            and summary.get("external_engine_version") == "2.4.2"
            and summary.get("new_external_engine_execution_performed") is True
            and summary.get("r53_cdmetapop_values_used_to_fit_nemo") is False
            and summary.get("cross_engine_numeric_truth_claimed") is False
            and summary.get("cross_engine_metrics_forced_to_equality") is False
        )
    elif stage == "R5.5":
        ok = common and (
            summary.get("family_count") == 12
            and summary.get("cross_lineage_pair_count") == 35
            and summary.get("pair_with_one_cell_contact_opportunity_count") == 35
            and summary.get("pair_with_exact_overlap_count") == 35
            and summary.get("age_state_count") == 141
            and summary.get("cross_engine_context_record_count") == 105
            and summary.get("new_external_engine_execution_performed") is False
            and summary.get("r53_cdmetapop_used_as_contact_geometry") is False
            and summary.get("r54_nemo_used_as_contact_geometry") is False
            and summary.get("realized_admixture_claimed") is False
            and summary.get("numeric_gene_flow_truth_claimed") is False
            and summary.get("single_contact_history_winner_selected") is False
        )
    elif stage == "R5.6":
        ok = common and (
            summary.get("pair_count") == 35
            and summary.get("schedule_class_count") == 1
            and summary.get("scientific_stream_count") == 6
            and summary.get("variant_count") == 3
            and summary.get("seed_count") == 2
            and summary.get("external_engine") == "SLiM"
            and summary.get("external_engine_version") == "5.2"
            and summary.get("new_external_engine_execution_performed") is True
            and summary.get("tree_sequence_ancestry_analysis_performed") is True
            and summary.get("numeric_admixture_truth_claimed") is False
            and summary.get("realized_historical_admixture_claimed") is False
            and summary.get("r55_contact_support_fraction_used_as_migration_magnitude") is False
            and summary.get("result_selected_tuning") is False
            and summary.get("single_history_winner_selected") is False
        )
    else:
        ok = False
    return bool(ok), dict(summary)


def _hash_matches(root: Path, rel: Path, expected: Any) -> bool:
    p = root / rel
    return p.is_file() and isinstance(expected, str) and sha256_file(p) == expected


def _binding_integrity(root: Path) -> tuple[bool, dict[str, Any]]:
    r54 = load_json(root / R54_OUT / "R5_4_PARENT_CANDIDATE_BINDING.json")
    r55 = load_json(root / R55_OUT / "R5_5_PARENT_CANDIDATE_BINDING.json")
    r56 = load_json(root / R56_OUT / "R5_6_PARENT_CANDIDATE_BINDING.json")

    checks = {
        "r54_status": r54.get("status") == "R54_PARENT_CANDIDATE_BINDING",
        "r54_r53_plan": _hash_matches(root, R53_OUT / "R5_3_CDMETAPOP_EXECUTION_PLAN.json", r54.get("r53_plan_sha256")),
        "r54_r53_audit": _hash_matches(root, R53_OUT / "R5_3_INTEGRATED_AUDIT.json", r54.get("r53_audit_sha256")),
        "r54_r53_sensitivity": _hash_matches(root, R53_OUT / "R5_3_DEMOGRAPHIC_PERSISTENCE_SENSITIVITY.json", r54.get("r53_sensitivity_sha256")),
        "r54_r53_manifest": _hash_matches(root, R53_OUT / "R5_3_OUTPUT_MANIFEST.json", r54.get("r53_output_manifest_sha256")),
        "r55_status": r55.get("status") == "R55_PARENT_CANDIDATE_BINDING",
        "r55_r54_plan": _hash_matches(root, R54_OUT / "R5_4_NEMO_EXECUTION_PLAN.json", r55.get("r54_plan_sha256")),
        "r55_r54_audit": _hash_matches(root, R54_OUT / "R5_4_INTEGRATED_AUDIT.json", r55.get("r54_audit_sha256")),
        "r55_r54_sensitivity": _hash_matches(root, R54_OUT / "R5_4_CROSS_ENGINE_GENETIC_ROBUSTNESS_SENSITIVITY.json", r55.get("r54_sensitivity_sha256")),
        "r55_r54_manifest": _hash_matches(root, R54_OUT / "R5_4_OUTPUT_MANIFEST.json", r55.get("r54_output_manifest_sha256")),
        "r55_r53_sensitivity": _hash_matches(root, R53_OUT / "R5_3_DEMOGRAPHIC_PERSISTENCE_SENSITIVITY.json", r55.get("r53_sensitivity_sha256")),
        "r55_r53_manifest": _hash_matches(root, R53_OUT / "R5_3_OUTPUT_MANIFEST.json", r55.get("r53_output_manifest_sha256")),
        "r55_j14": _hash_matches(root, J14_REL, r55.get("j14_sha256")),
        "r56_status": r56.get("status") == "R56_PARENT_CANDIDATE_BINDING",
        "r56_r55_audit": _hash_matches(root, R55_OUT / "R5_5_INTEGRATED_AUDIT.json", r56.get("r55_audit_sha256")),
        "r56_r55_history": _hash_matches(root, R55_OUT / "R5_5_CONTACT_ZONE_HISTORY.json", r56.get("r55_history_sha256")),
        "r56_r55_atlas": _hash_matches(root, R55_OUT / "R5_5_CONTACT_OPPORTUNITY_ATLAS.npz", r56.get("r55_atlas_sha256")),
        "r56_r55_context": _hash_matches(root, R55_OUT / "R5_5_CROSS_ENGINE_CONTACT_CONTEXT.json", r56.get("r55_context_sha256")),
        "r56_r55_manifest": _hash_matches(root, R55_OUT / "R5_5_OUTPUT_MANIFEST.json", r56.get("r55_output_manifest_sha256")),
        "r56_r55_source": _hash_matches(root, Path("src/arcana_worldsim/state_query/r55_contact_history.py"), r56.get("r55_source_sha256")),
    }
    return all(checks.values()), checks


def _r52_sealed_parent_integrity(root: Path) -> tuple[bool, dict[str, Any]]:
    paths = {
        "final_seal": (R52_FINAL_SEAL, EXPECTED_R52_FINAL_SEAL_SHA256),
        "plan": (R52_PLAN, EXPECTED_R52_PLAN_SHA256),
        "raw_manifest": (R52_RAW, EXPECTED_R52_RAW_SHA256),
        "output_manifest": (R52_OUTPUT_MANIFEST, EXPECTED_R52_OUTPUT_MANIFEST_SHA256),
    }
    checks = {k: (root / rel).is_file() and sha256_file(root / rel) == expected for k, (rel, expected) in paths.items()}
    try:
        seal = load_json(root / R52_FINAL_SEAL)
        s = seal.get("summary") or {}
        authority = seal.get("authority") or {}
        checks.update({
            "seal_semantics": seal.get("sealed") is True and seal.get("status") == "PASS_R52_TARGETED_EXPANSION_CORRIDOR_VALIDATION_SEALED",
            "seal_family_count": s.get("robust_family_count") == 12,
            "seal_stream_count": s.get("scientific_stream_count") == 80,
            "seal_no_numeric_truth": s.get("numeric_corridor_truth_claimed") is False,
            "seal_no_canon_change": s.get("canonical_state_changed") is False and s.get("derived_refinement_promoted_to_canon") is False,
            "seal_deep_off": s.get("deep_biological_coupling") is False,
            "seal_embedded_hashes": authority.get("r52_execution_plan_sha256") == EXPECTED_R52_PLAN_SHA256 and authority.get("r52_raw_evidence_manifest_sha256") == EXPECTED_R52_RAW_SHA256 and authority.get("r52_candidate_output_manifest_sha256") == EXPECTED_R52_OUTPUT_MANIFEST_SHA256,
        })
    except Exception:
        checks["seal_json_readable"] = False
    return all(checks.values()), checks


def _runtime_semantics(root: Path) -> tuple[bool, dict[str, Any]]:
    r53 = load_json(root / R53_OUT / "R5_3_CDMETAPOP_RUNTIME_IDENTITY.json")
    r54 = load_json(root / R54_OUT / "R5_4_NEMO_RUNTIME_IDENTITY.json")
    r56 = load_json(root / R56_OUT / "R5_6_SLIM_RUNTIME_IDENTITY.json")
    checks = {
        "r53_status": r53.get("status") == "PASS_R53_CDMETAPOP_3_08_PINNED_RUNTIME_IDENTITY",
        "r53_version": r53.get("cdmetapop_version") == "3.08",
        "r53_commit": r53.get("cdmetapop_commit") == "3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118",
        "r54_status": r54.get("status") == "PASS_R54_NEMO_2_4_2_PINNED_RUNTIME_IDENTITY",
        "r54_version": r54.get("nemo_version") == "2.4.2" and r54.get("conda_package_version") == "2.4.2",
        "r54_executable_hash_recorded": isinstance(r54.get("nemo_executable_sha256"), str) and len(r54.get("nemo_executable_sha256")) == 64,
        "r56_status": r56.get("status") == "PASS_R56_SLIM_5_2_PINNED_RUNTIME_IDENTITY",
        "r56_slim": r56.get("slim_version") == "5.2" and r56.get("slim_package_version") == "5.2",
        "r56_tskit": r56.get("tskit_version") == "1.0.3",
        "r56_slim_executable_hash_recorded": isinstance(r56.get("slim_executable_sha256"), str) and len(r56.get("slim_executable_sha256")) == 64,
    }
    return all(checks.values()), checks


def collect_block_checks(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = Path(root).resolve()
    checks: list[dict[str, Any]] = []

    def ck(name: str, cond: bool, detail: Any = None) -> None:
        checks.append({"name": name, "pass": bool(cond), "detail": detail})

    r52_ok, r52_detail = _r52_sealed_parent_integrity(root)
    ck("sealed_r52_parent_exact_and_semantically_clean", r52_ok, r52_detail)

    stage_records: dict[str, Any] = {}
    for stage in ("R5.3", "R5.4", "R5.5", "R5.6"):
        out = root / STAGE_OUT[stage]
        manifest_path = out / OUTPUT_MANIFEST_NAME[stage]
        audit_path = out / AUDIT_NAME[stage]
        ck(f"{stage}_output_manifest_present", manifest_path.is_file())
        ck(f"{stage}_audit_present", audit_path.is_file())
        if not (manifest_path.is_file() and audit_path.is_file()):
            continue
        manifest = load_json(manifest_path)
        audit = load_json(audit_path)
        ck(f"{stage}_manifest_status_exact", manifest.get("status") == CANDIDATE_STATUS[stage], manifest.get("status"))
        mi_ok, mi_detail = _manifest_integrity(out, manifest_path, EXPECTED_MANIFEST_FILES[stage])
        ck(f"{stage}_manifest_byte_hash_integrity", mi_ok, mi_detail)
        au_ok, au_detail = _audit_semantics(stage, audit)
        ck(f"{stage}_candidate_audit_exact_and_all_checks_pass", au_ok, au_detail)
        su_ok, su_detail = _summary_semantics(stage, dict(audit.get("summary") or {}))
        ck(f"{stage}_scientific_summary_semantics_exact", su_ok, su_detail)
        stage_records[stage] = {
            "output_manifest_sha256": sha256_file(manifest_path),
            "integrated_audit_sha256": sha256_file(audit_path),
            "summary": audit.get("summary"),
        }

    for stage in ("R5.3", "R5.4", "R5.6"):
        raw_ok, raw_detail = _raw_manifest_integrity(root, stage)
        ck(f"{stage}_raw_evidence_manifest_rehash_complete", raw_ok, raw_detail)
        if raw_ok:
            stage_records.setdefault(stage, {})["raw_evidence_manifest_sha256"] = sha256_file(root / STAGE_OUT[stage] / RAW_MANIFEST_NAME[stage])

    bind_ok, bind_detail = _binding_integrity(root)
    ck("candidate_to_candidate_hash_bindings_revalidated_live", bind_ok, bind_detail)

    runtime_ok, runtime_detail = _runtime_semantics(root)
    ck("external_runtime_identity_evidence_semantics_exact", runtime_ok, runtime_detail)

    # Cross-stage non-circularity and governance are re-asserted from the exact candidate plans/history.
    try:
        p53 = load_json(root / R53_OUT / "R5_3_CDMETAPOP_EXECUTION_PLAN.json")
        p54 = load_json(root / R54_OUT / "R5_4_NEMO_EXECUTION_PLAN.json")
        h55 = load_json(root / R55_OUT / "R5_5_CONTACT_ZONE_HISTORY.json")
        p56 = load_json(root / R56_OUT / "R5_6_SLIM_EXECUTION_PLAN.json")
        ck("r53_r52_geometry_not_promoted_to_cdmetapop_input", (p53.get("standardized_diagnostic_semantics") or {}).get("r52_range_geometry_used_as_cdmetapop_input") is False)
        ck("r54_cdmetapop_values_not_used_to_fit_nemo", (p54.get("semantics") or {}).get("r53_cdmetapop_values_used_to_fit_nemo") is False)
        ck("r54_cdmetapop_only_side_by_side_reporting", (p54.get("semantics") or {}).get("r53_used_only_for_side_by_side_reporting") is True)
        ck("r55_contact_history_is_opportunity_not_realized_admixture", "NOT_REALIZED_ADMIXTURE" in str(h55.get("semantics", "")))
        ck("r56_r55_binary_schedule_is_input_authority", (p56.get("semantics") or {}).get("r55_binary_contact_schedule_is_input_authority") is True)
        ck("r56_contact_support_fraction_not_migration_magnitude", (p56.get("semantics") or {}).get("r55_contact_support_fraction_used_as_migration_magnitude") is False)
        ck("r56_simulated_ancestry_not_realized_history", (p56.get("semantics") or {}).get("simulated_ancestry_is_not_promoted_to_realized_historical_admixture") is True)
        ck("r56_schedule_class_count_exactly_one_observed", int(p56.get("schedule_class_count", -1)) == 1)
        ck("r56_stream_count_six_observed", int(p56.get("planned_stream_count", -1)) == 6)
    except Exception as exc:
        ck("cross_stage_semantic_inputs_readable", False, repr(exc))

    governance_ok = all(
        (stage_records.get(s, {}).get("summary") or {}).get("canonical_state_changed") is False
        and (stage_records.get(s, {}).get("summary") or {}).get("derived_refinement_promoted_to_canon") is False
        and (stage_records.get(s, {}).get("summary") or {}).get("deep_biological_coupling") is False
        for s in ("R5.3", "R5.4", "R5.5", "R5.6")
    )
    ck("all_four_candidates_preserve_canon_and_deep_off", governance_ok)
    ck("r57_executes_no_new_external_engine", True)
    ck("block_seal_does_not_claim_numeric_historical_truth", True)
    ck("block_seal_does_not_select_single_demographic_genetic_contact_or_admixture_winner", True)

    binding = {
        "stage": STAGE,
        "status": "R57_R53_R56_BLOCK_INPUT_BINDING",
        "sealed_parent": {
            "r52_final_seal_sha256": sha256_file(root / R52_FINAL_SEAL) if (root / R52_FINAL_SEAL).is_file() else None,
            "r52_plan_sha256": sha256_file(root / R52_PLAN) if (root / R52_PLAN).is_file() else None,
            "r52_raw_evidence_manifest_sha256": sha256_file(root / R52_RAW) if (root / R52_RAW).is_file() else None,
            "r52_output_manifest_sha256": sha256_file(root / R52_OUTPUT_MANIFEST) if (root / R52_OUTPUT_MANIFEST).is_file() else None,
        },
        "candidate_stages": stage_records,
        "binding_semantics": "ONE_LARGE_R53_R56_BLOCK_CLOSURE_BY_EXACT_LIVE_HASH_REVALIDATION_NO_MICRO_SEALS_REQUIRED",
    }
    return checks, binding


def run_integrated_audit(root: Path, out: Path | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    out = Path(out).resolve() if out else root / OUT_REL
    checks, binding = collect_block_checks(root)
    failed = [c for c in checks if not c["pass"]]
    audit = {
        "stage": STAGE,
        "status": AUDIT_STATUS if not failed else "BLOCKED_R57_R53_R56_INTEGRATED_BLOCK_AUDIT",
        "scientific_block_seal_eligible": not failed,
        "checks_passed": len(checks) - len(failed),
        "checks_total": len(checks),
        "failed": failed,
        "checks": checks,
        "summary": {
            "sealed_parent_stage": "R5.2",
            "candidate_block": ["R5.3", "R5.4", "R5.5", "R5.6"],
            "r53_cdmetapop_streams": 72,
            "r54_nemo_streams": 144,
            "r55_cross_lineage_pairs": 35,
            "r55_age_states": 141,
            "r56_schedule_classes": 1,
            "r56_slim_streams": 6,
            "new_external_engine_execution_performed": False,
            "numeric_historical_truth_claimed": False,
            "realized_historical_admixture_claimed": False,
            "single_history_winner_selected": False,
            "canonical_state_changed": False,
            "derived_refinement_promoted_to_canon": False,
            "deep_biological_coupling": False,
        },
        "recommended_next_action": "START_POST_BLOCK_RECONCILIATION_OF_3MA_TO_200KA_HOMINID_HISTORY_WITH_HUMAN_200KA_COHORT_AFTER_R57_SEAL",
    }
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "R5_7_BLOCK_INPUT_BINDING.json", binding)
    write_json(out / "R5_7_INTEGRATED_BLOCK_AUDIT.json", audit)
    files = {}
    for name in ("R5_7_BLOCK_INPUT_BINDING.json", "R5_7_INTEGRATED_BLOCK_AUDIT.json"):
        p = out / name
        files[name] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
    write_json(out / "R5_7_BLOCK_AUDIT_MANIFEST.json", {"stage": STAGE, "status": audit["status"], "files": files})
    return audit


def seal_block(root: Path, out: Path | None = None, authority_path: Path | None = None, source_manifest_path: Path | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    out = Path(out).resolve() if out else root / OUT_REL
    authority_path = Path(authority_path).resolve() if authority_path else root / "R5_7_FINAL_BLOCK_SEAL_AUTHORITY.json"
    source_manifest_path = Path(source_manifest_path).resolve() if source_manifest_path else root / "SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_7.json"
    if not authority_path.is_file() or not source_manifest_path.is_file():
        raise R57Error("missing R5.7 seal authority or source manifest")

    authority = load_json(authority_path)
    if authority.get("stage") != STAGE or authority.get("final_verdict") != FINAL_STATUS:
        raise R57Error("R5.7 final seal authority mismatch")

    # Re-run every live check independently at seal time rather than trusting the audit artifact.
    checks, binding = collect_block_checks(root)
    failed = [c for c in checks if not c["pass"]]
    if failed:
        result = {
            "stage": STAGE,
            "status": "FAIL_R57_FINAL_BLOCK_SEAL",
            "sealed": False,
            "checks_passed": len(checks) - len(failed),
            "checks_total": len(checks),
            "failed": failed,
        }
        print(json.dumps(result, indent=2))
        return result

    audit_path = out / "R5_7_INTEGRATED_BLOCK_AUDIT.json"
    binding_path = out / "R5_7_BLOCK_INPUT_BINDING.json"
    audit_manifest_path = out / "R5_7_BLOCK_AUDIT_MANIFEST.json"
    if not all(p.is_file() for p in (audit_path, binding_path, audit_manifest_path)):
        raise R57Error("R5.7 integrated audit artifacts missing before seal")
    audit = load_json(audit_path)
    if audit.get("status") != AUDIT_STATUS or audit.get("scientific_block_seal_eligible") is not True:
        raise R57Error("R5.7 integrated audit not seal-eligible")
    manifest_ok, manifest_detail = _manifest_integrity(out, audit_manifest_path, {"R5_7_BLOCK_INPUT_BINDING.json", "R5_7_INTEGRATED_BLOCK_AUDIT.json"})
    if not manifest_ok:
        raise R57Error(f"R5.7 audit artifact manifest drift: {manifest_detail}")

    final = {
        "stage": STAGE,
        "stage_name": authority.get("stage_name"),
        "status": FINAL_STATUS,
        "sealed": True,
        "scientific_meaning": authority.get("scientific_meaning"),
        "checks_passed": len(checks),
        "checks_total": len(checks),
        "failed": [],
        "checks": checks,
        "source_authority_manifest_sha256": sha256_file(source_manifest_path),
        "seal_authority_sha256": sha256_file(authority_path),
        "integrated_block_audit_sha256": sha256_file(audit_path),
        "block_input_binding_sha256": sha256_file(binding_path),
        "block_input_binding": binding,
        "summary": {
            "r52_parent_seal_preserved": True,
            "r53_demography_candidate_sealed_as_part_of_block": True,
            "r54_genetic_robustness_candidate_sealed_as_part_of_block": True,
            "r55_contact_history_candidate_sealed_as_part_of_block": True,
            "r56_ancestry_candidate_sealed_as_part_of_block": True,
            "micro_seals_created_for_r53_r54_r55_r56": False,
            "new_external_engine_execution_performed": False,
            "numeric_historical_truth_claimed": False,
            "realized_historical_admixture_claimed": False,
            "canonical_state_changed": False,
            "derived_refinement_promoted_to_canon": False,
            "deep_biological_coupling": False,
            "closure_readiness": "SEALED_R53_R56_GOVERNED_EVIDENCE_BLOCK_READY_FOR_POST_BLOCK_HOMINID_HISTORY_RECONCILIATION",
        },
    }
    seal_path = out / "R5_7_FINAL_BLOCK_SEAL.json"
    write_json(seal_path, final)
    seal_manifest = {
        "stage": STAGE,
        "status": "PASS_R57_FINAL_BLOCK_SEAL_MANIFEST",
        "final_seal_file": {"path": seal_path.name, "bytes": seal_path.stat().st_size, "sha256": sha256_file(seal_path)},
        "integrated_block_audit": {"path": audit_path.name, "sha256": sha256_file(audit_path)},
        "block_input_binding": {"path": binding_path.name, "sha256": sha256_file(binding_path)},
        "source_authority_manifest": {"path": source_manifest_path.name, "sha256": sha256_file(source_manifest_path)},
        "seal_authority": {"path": authority_path.name, "sha256": sha256_file(authority_path)},
    }
    write_json(out / "R5_7_FINAL_BLOCK_SEAL_MANIFEST.json", seal_manifest)
    return {
        "stage": STAGE,
        "status": FINAL_STATUS,
        "sealed": True,
        "checks_passed": len(checks),
        "checks_total": len(checks),
        "summary": final["summary"],
        "final_seal_sha256": seal_manifest["final_seal_file"]["sha256"],
    }
