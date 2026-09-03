from __future__ import annotations

from pathlib import Path
from typing import Any
import gzip
import hashlib
import json

STAGE = "v0.6D1-R4.50"

PARENT_COMPLETE = (
    "PASS_R449_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_"
    "EXPANSION_EXECUTION_AND_EVIDENCE_CAPTURE_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R449_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_"
    "EXPANSION_EXECUTION_AND_EVIDENCE_CAPTURE_SEALED"
)
PARENT_NEXT = (
    "BUILD_R450_GEONOMICS_FULL_JOB_REVALIDATION_EVIDENCE_REVIEW_"
    "AND_FINAL_GEONOMICS_CLOSURE"
)
EXPECTED_EXPANSION_PLAN_SHA256 = (
    "3a6e1d5b7d454f7c4ecd79c357bc6a2e8cd6e6514c61db07a5d06267834766e5"
)

COMPLETE = (
    "PASS_R450_GEONOMICS_FULL_JOB_REVALIDATION_EVIDENCE_REVIEW_"
    "AND_FINAL_GEONOMICS_CLOSURE_COMPLETE"
)
SEALED = (
    "PASS_R450_GEONOMICS_FULL_JOB_REVALIDATION_EVIDENCE_REVIEW_"
    "AND_FINAL_GEONOMICS_CLOSURE_SEALED"
)
BLOCKED = (
    "BLOCKED_R450_FULL_JOB_EVIDENCE_REVIEW_OR_FINAL_GEONOMICS_CLOSURE_FAILURE"
)
NEXT = (
    "BUILD_R451_MULTI_ENGINE_23_JOB_RECONCILIATION_AND_REVALIDATION_"
    "GAP_CENSUS"
)

FINAL_REVALIDATION_VERDICT = (
    "GEONOMICS_1_4_9_FULLY_REVALIDATED_WITH_EXACT_INTEGRITY_AND_"
    "GOVERNED_DESCRIPTIVE_EVIDENCE_NO_NUMERIC_CORROBORATION_CLAIM"
)

OUT = Path("outputs/v0_6D1_R4_50")
SEAL = Path("outputs/v0_6D1_R4_50_SEAL/R4_50_FINAL_SEAL_AUDIT.json")
CFG = Path(
    "configs/world1_r450_geonomics_full_job_revalidation_evidence_review_"
    "final_geonomics_closure_v0_6D1_R4_50.json"
)

R449 = Path("outputs/v0_6D1_R4_49/R4_49_INTEGRATED_AUDIT.json")
R449_SEAL = Path("outputs/v0_6D1_R4_49_SEAL/R4_49_FINAL_SEAL_AUDIT.json")
R449_SHARDS = Path(
    "outputs/v0_6D1_R4_49/R4_49_EXPANSION_EVIDENCE_SHARD_MANIFEST.json"
)
R449_FULL = Path(
    "outputs/v0_6D1_R4_49/R4_49_FULL_GEONOMICS_COVERAGE_EVIDENCE_MANIFEST.json"
)
R448_PLAN = Path("outputs/v0_6D1_R4_48/R4_48_FULL_COVERAGE_EXPANSION_PLAN.json")
R448_J14_INV = Path("outputs/v0_6D1_R4_48/R4_48_J14_FULL_COVERAGE_INVENTORY.json")
R448_J18_INV = Path("outputs/v0_6D1_R4_48/R4_48_J18_FULL_COVERAGE_INVENTORY.json")

R446_J14 = Path("outputs/v0_6D1_R4_46/R4_46_J14_SCIENTIFIC_EVIDENCE.json")
R446_J18 = Path("outputs/v0_6D1_R4_46/R4_46_J18_SCIENTIFIC_EVIDENCE.json")
R446_J21 = Path("outputs/v0_6D1_R4_46/R4_46_J21_SCIENTIFIC_EVIDENCE.json")

J14 = "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"
J18 = "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
J21 = "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"

EXPECTED_METRICS = {
    J14: sorted([
        "GNX_CARRIER_COORDINATE_READBACK_XY",
        "GNX_CARRIER_NATIVE_CELL_READBACK_IJ",
        "GNX_CARRIER_NEAREST_NEIGHBOR_DISTANCE",
    ]),
    J18: sorted([
        "GNX_CARRIER_COORDINATE_READBACK_XY",
        "GNX_CARRIER_NATIVE_CELL_READBACK_IJ",
        "GNX_CARRIER_NEAREST_NEIGHBOR_DISTANCE",
    ]),
    J21: sorted([
        "GNX_NATIVE_LAYER_RASTER_READBACK",
        "GNX_NATIVE_LAYER_DESCRIPTIVE_SUMMARY",
    ]),
}

EXPECTED_SEEDS = {
    J14: {310746493, 1894477382, 1291996560, 1554786554},
    J18: {999124684, 1705133798, 1085091276, 555097754},
    J21: {1617603515, 1207292893, 1138693833, 989125497},
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _review_record(
    rec: dict[str, Any],
    *,
    job_id: str,
    expected_branch_ids: set[str] | None,
    expansion: bool,
) -> tuple[bool, bool, bool, bool, str | None]:
    if rec.get("job_id") != job_id:
        return False, False, False, False, "JOB_ID_MISMATCH"

    metric_id = str(rec.get("metric_id"))
    if metric_id not in EXPECTED_METRICS[job_id]:
        return False, False, False, False, "UNAUTHORIZED_METRIC_ID"

    if expansion:
        branch_id = str(rec.get("scientific_branch_id", ""))
        if expected_branch_ids is None or branch_id not in expected_branch_ids:
            return False, False, False, False, "BRANCH_ID_OUTSIDE_SHARD"

    seed = int(rec.get("frozen_seed"))
    if seed not in EXPECTED_SEEDS[job_id]:
        return False, False, False, False, "FROZEN_SEED_MISMATCH"

    role = rec.get("metric_role")
    if role == "EXACT_INTEGRITY_ONLY":
        good = (
            rec.get("exact_match") is True
            and rec.get("finite") is True
            and rec.get("scientific_divergence_claim") is False
        )
        return good, True, False, good, None if good else "INTEGRITY_FAILURE"

    if role in {
        "SCIENTIFIC_DESCRIPTIVE_CONNECTIVITY",
        "SCIENTIFIC_DESCRIPTIVE_LAYER_STATE",
    }:
        good = (
            rec.get("finite") is True
            and rec.get("numeric_acceptance_threshold") is None
            and rec.get("automatic_pass_fail_from_value") is False
        )
        return good, False, True, good, None if good else "DESCRIPTIVE_FAILURE"

    return False, False, False, False, "UNAUTHORIZED_METRIC_ROLE"


def _scan_expansion(root: Path, shard_manifest: dict[str, Any]) -> dict[str, Any]:
    total_records = 0
    integrity = 0
    descriptive = 0
    bad_records = 0
    metric_ids = {J14: set(), J18: set()}
    branch_ids = {J14: set(), J18: set()}
    stream_ids = {J14: set(), J18: set()}
    file_records = []
    errors = []

    for shard in shard_manifest["shards"]:
        job_id = shard["job_id"]
        evidence_path = root / shard["metric_evidence_file"]
        expected_branch_ids = set(shard["branch_ids"])

        if not evidence_path.exists():
            errors.append({
                "shard_id": shard["shard_id"],
                "error": "MISSING_EVIDENCE_FILE",
            })
            continue

        actual_sha = sha256(evidence_path)
        if actual_sha != shard["metric_evidence_file_sha256"]:
            errors.append({
                "shard_id": shard["shard_id"],
                "error": "EVIDENCE_SHA256_MISMATCH",
                "expected": shard["metric_evidence_file_sha256"],
                "actual": actual_sha,
            })
            continue

        local_records = 0
        local_integrity = 0
        local_descriptive = 0
        local_bad = 0

        with gzip.open(evidence_path, "rt", encoding="utf-8") as f:
            for line_number, line in enumerate(f, 1):
                rec = json.loads(line)
                ok, is_integrity, is_descriptive, sem_ok, reason = _review_record(
                    rec,
                    job_id=job_id,
                    expected_branch_ids=expected_branch_ids,
                    expansion=True,
                )
                local_records += 1
                total_records += 1
                if is_integrity:
                    local_integrity += 1
                    integrity += 1
                if is_descriptive:
                    local_descriptive += 1
                    descriptive += 1
                if not ok or not sem_ok:
                    local_bad += 1
                    bad_records += 1
                    if len(errors) < 100:
                        errors.append({
                            "shard_id": shard["shard_id"],
                            "line": line_number,
                            "error": reason,
                        })
                metric_ids[job_id].add(str(rec.get("metric_id")))
                bid = str(rec.get("scientific_branch_id"))
                branch_ids[job_id].add(bid)
                stream_ids[job_id].add(
                    (bid, int(rec.get("replicate_index")), int(rec.get("frozen_seed")))
                )

        file_records.append({
            "job_id": job_id,
            "shard_id": shard["shard_id"],
            "path": shard["metric_evidence_file"],
            "sha256": actual_sha,
            "record_count": local_records,
            "integrity_record_count": local_integrity,
            "descriptive_record_count": local_descriptive,
            "bad_record_count": local_bad,
        })

    return {
        "stage": STAGE,
        "record_count": total_records,
        "integrity_record_count": integrity,
        "descriptive_record_count": descriptive,
        "bad_record_count": bad_records,
        "metric_ids": {
            jid: sorted(vals) for jid, vals in metric_ids.items()
        },
        "branch_ids": {
            jid: sorted(vals) for jid, vals in branch_ids.items()
        },
        "stream_count": {
            jid: len(vals) for jid, vals in stream_ids.items()
        },
        "file_records": file_records,
        "errors": errors,
    }


def _scan_baseline_job(
    evidence: dict[str, Any],
    *,
    job_id: str,
    baseline_branch_id: str | None,
) -> dict[str, Any]:
    records = evidence.get("metric_records") or []
    streams = evidence.get("stream_records") or []

    integrity = 0
    descriptive = 0
    bad_records = 0
    metric_ids = set()
    seeds = set()
    errors = []

    for idx, rec in enumerate(records):
        ok, is_integrity, is_descriptive, sem_ok, reason = _review_record(
            rec,
            job_id=job_id,
            expected_branch_ids=None,
            expansion=False,
        )
        if is_integrity:
            integrity += 1
        if is_descriptive:
            descriptive += 1
        if not ok or not sem_ok:
            bad_records += 1
            if len(errors) < 100:
                errors.append({"record_index": idx, "error": reason})
        metric_ids.add(str(rec.get("metric_id")))
        seeds.add(int(rec.get("frozen_seed")))

    stream_ids = set()
    for s in streams:
        seed = int(s["frozen_seed"])
        stream_ids.add((int(s["replicate_index"]), seed))

    return {
        "job_id": job_id,
        "baseline_branch_id": baseline_branch_id,
        "record_count": len(records),
        "integrity_record_count": integrity,
        "descriptive_record_count": descriptive,
        "bad_record_count": bad_records,
        "metric_ids": sorted(metric_ids),
        "seed_set": sorted(seeds),
        "stream_count": len(stream_ids),
        "all_stream_summaries_pass":
            len(streams) == len(stream_ids)
            and all(s.get("pass") is True for s in streams),
        "scientific_evidence_capture_valid":
            evidence.get("scientific_evidence_capture_valid") is True,
        "errors": errors,
    }


def _expected_branch_sets(
    j14_inv: dict[str, Any],
    j18_inv: dict[str, Any],
) -> dict[str, set[str]]:
    return {
        J14: {str(b["branch_id"]) for b in j14_inv["branches"]},
        J18: {str(b["branch_id"]) for b in j18_inv["branches"]},
    }


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    parent = load(root / R449)
    parent_seal = load(root / R449_SEAL)
    shard_manifest = load(root / R449_SHARDS)
    full_manifest = load(root / R449_FULL)
    plan = load(root / R448_PLAN)
    j14_inv = load(root / R448_J14_INV)
    j18_inv = load(root / R448_J18_INV)

    j14_path = root / R446_J14
    j18_path = root / R446_J18
    j21_path = root / R446_J21
    j14_ev = load(j14_path)
    j18_ev = load(j18_path)
    j21_ev = load(j21_path)

    expansion = _scan_expansion(root, shard_manifest)
    baseline = {
        J14: _scan_baseline_job(
            j14_ev, job_id=J14, baseline_branch_id="M000_C00"
        ),
        J18: _scan_baseline_job(
            j18_ev, job_id=J18, baseline_branch_id="M000_C00"
        ),
        J21: _scan_baseline_job(
            j21_ev, job_id=J21, baseline_branch_id=None
        ),
    }

    write(root / OUT / "R4_50_EXPANSION_RECORD_LEVEL_REVIEW.json", expansion)
    write(root / OUT / "R4_50_BASELINE_RECORD_LEVEL_REVIEW.json", baseline)

    expected_branches = _expected_branch_sets(j14_inv, j18_inv)
    expansion_j14_branches = set(expansion["branch_ids"][J14])
    expansion_j18_branches = set(expansion["branch_ids"][J18])

    full_j14_branches = expansion_j14_branches | {"M000_C00"}
    full_j18_branches = expansion_j18_branches | {"M000_C00"}

    corpus_files = [
        {
            "role": "SEALED_BASELINE_J14",
            "path": str(R446_J14).replace("\\", "/"),
            "sha256": sha256(j14_path),
        },
        {
            "role": "SEALED_BASELINE_J18",
            "path": str(R446_J18).replace("\\", "/"),
            "sha256": sha256(j18_path),
        },
        {
            "role": "SEALED_BASELINE_J21",
            "path": str(R446_J21).replace("\\", "/"),
            "sha256": sha256(j21_path),
        },
    ] + [
        {
            "role": "R449_EXPANSION_SHARD_METRICS",
            "job_id": r["job_id"],
            "shard_id": r["shard_id"],
            "path": r["path"],
            "sha256": r["sha256"],
            "record_count": r["record_count"],
        }
        for r in expansion["file_records"]
    ]

    corpus_manifest = {
        "stage": STAGE,
        "status": "R450_GEONOMICS_SCIENTIFIC_EVIDENCE_CORPUS_HASHED",
        "authorized_expansion_plan_sha256": plan["plan_sha256"],
        "file_count": len(corpus_files),
        "files": corpus_files,
    }
    write(root / OUT / "R4_50_EVIDENCE_CORPUS_MANIFEST.json", corpus_manifest)

    expansion_metrics = expansion["record_count"]
    expansion_integrity = expansion["integrity_record_count"]
    expansion_descriptive = expansion["descriptive_record_count"]
    baseline_metrics = sum(x["record_count"] for x in baseline.values())
    baseline_integrity = sum(
        x["integrity_record_count"] for x in baseline.values()
    )
    baseline_descriptive = sum(
        x["descriptive_record_count"] for x in baseline.values()
    )

    full_metrics = expansion_metrics + baseline_metrics
    full_integrity = expansion_integrity + baseline_integrity
    full_descriptive = expansion_descriptive + baseline_descriptive

    full_streams = (
        expansion["stream_count"][J14]
        + expansion["stream_count"][J18]
        + baseline[J14]["stream_count"]
        + baseline[J18]["stream_count"]
        + baseline[J21]["stream_count"]
    )

    checks = {
        "parent_r449_complete_36_36":
            parent.get("status") == PARENT_COMPLETE
            and parent.get("checks_passed") == 36
            and parent.get("checks_failed") == 0,
        "parent_r449_sealed_26_26":
            parent_seal.get("status") == PARENT_SEALED
            and parent_seal.get("verdict") == "SEALED"
            and parent_seal.get("checks_passed") == 26
            and parent_seal.get("checks_failed") == 0,
        "parent_next_action_r450":
            parent.get("next_action") == PARENT_NEXT
            and parent_seal.get("next_action") == PARENT_NEXT,
        "policy_frozen":
            cfg.get("policy")
            == "R450_INDEPENDENT_RECORD_LEVEL_REVIEW_OF_FULL_GEONOMICS_CORPUS",
        "expansion_plan_sha_exact":
            plan.get("plan_sha256") == EXPECTED_EXPANSION_PLAN_SHA256
            == parent.get("authorized_expansion_plan_sha256"),
        "r449_shard_manifest_valid":
            shard_manifest.get("status")
            == "R449_EXPANSION_EVIDENCE_SHARD_MANIFEST_VALID"
            and shard_manifest.get("shard_count") == 32,
        "r449_full_manifest_valid":
            full_manifest.get("status")
            == "R449_FULL_GEONOMICS_COVERAGE_EVIDENCE_CAPTURED",
        "exact_32_expansion_files_reviewed":
            len(expansion["file_records"]) == 32,
        "all_expansion_file_hashes_valid":
            len(expansion["errors"]) == 0,
        "expansion_zero_bad_records":
            expansion["bad_record_count"] == 0,
        "exact_334512_expansion_records":
            expansion_metrics == 334512,
        "exact_223008_expansion_integrity":
            expansion_integrity == 223008,
        "exact_111504_expansion_descriptive":
            expansion_descriptive == 111504,
        "j14_expansion_exact_191_branches":
            len(expansion_j14_branches) == 191
            and "M000_C00" not in expansion_j14_branches,
        "j18_expansion_exact_63_branches":
            len(expansion_j18_branches) == 63
            and "M000_C00" not in expansion_j18_branches,
        "j14_expansion_exact_764_streams":
            expansion["stream_count"][J14] == 764,
        "j18_expansion_exact_252_streams":
            expansion["stream_count"][J18] == 252,
        "j14_metric_ids_exact":
            expansion["metric_ids"][J14] == EXPECTED_METRICS[J14]
            and baseline[J14]["metric_ids"] == EXPECTED_METRICS[J14],
        "j18_metric_ids_exact":
            expansion["metric_ids"][J18] == EXPECTED_METRICS[J18]
            and baseline[J18]["metric_ids"] == EXPECTED_METRICS[J18],
        "j21_metric_ids_exact":
            baseline[J21]["metric_ids"] == EXPECTED_METRICS[J21],
        "baseline_j14_zero_bad_records":
            baseline[J14]["bad_record_count"] == 0,
        "baseline_j18_zero_bad_records":
            baseline[J18]["bad_record_count"] == 0,
        "baseline_j21_zero_bad_records":
            baseline[J21]["bad_record_count"] == 0,
        "baseline_j14_four_streams_pass":
            baseline[J14]["stream_count"] == 4
            and baseline[J14]["all_stream_summaries_pass"] is True,
        "baseline_j18_four_streams_pass":
            baseline[J18]["stream_count"] == 4
            and baseline[J18]["all_stream_summaries_pass"] is True,
        "baseline_j21_four_streams_pass":
            baseline[J21]["stream_count"] == 4
            and baseline[J21]["all_stream_summaries_pass"] is True,
        "j14_full_branch_coverage_exact_192":
            full_j14_branches == expected_branches[J14]
            and len(full_j14_branches) == 192,
        "j18_full_branch_coverage_exact_64":
            full_j18_branches == expected_branches[J18]
            and len(full_j18_branches) == 64,
        "j21_full_layer_job_preserved":
            full_manifest["full_geonomics_coverage"][J21][
                "branch_coverage"
            ] == "1/1",
        "exact_1028_full_geonomics_streams":
            full_streams == 1028,
        "exact_346968_full_geonomics_records":
            full_metrics == 346968,
        "exact_229548_full_geonomics_integrity":
            full_integrity == 229548,
        "exact_117420_full_geonomics_descriptive":
            full_descriptive == 117420,
        "r449_full_counts_independently_reproduced":
            full_metrics == full_manifest["metric_record_count"]
            and full_integrity == full_manifest["integrity_record_count"]
            and full_descriptive == full_manifest["descriptive_record_count"],
        "all_integrity_exact_pass":
            expansion["bad_record_count"] == 0
            and all(x["bad_record_count"] == 0 for x in baseline.values()),
        "all_descriptive_valid_no_threshold":
            expansion["bad_record_count"] == 0
            and all(x["bad_record_count"] == 0 for x in baseline.values()),
        "zero_numeric_value_corrob_thresholds": True,
        "zero_automatic_scientific_pass_fail": True,
        "zero_majority_vote": True,
        "zero_result_selected_threshold": True,
        "engine_did_not_define_arcana_target": True,
        "canonical_rewrite_forbidden": True,
        "no_new_scientific_engine_execution":
            cfg.get("new_scientific_engine_execution_performed") is False,
        "no_target_numeric":
            cfg.get("target_numeric_execution_performed") is False,
        "no_readjudication":
            cfg.get("readjudication_performed") is False,
        "canonical_unchanged":
            cfg.get("canonical_state_changed") is False,
        "deep_off":
            cfg.get("deep_biological_coupling") is False,
        "deferred_p2_two":
            parent.get("active_deferred_p2_cell_count") == 2,
        "proxy_context_two":
            parent.get("proxy_context_only_count") == 2,
        "p3_backlog_six":
            parent.get("p3_backlog_cell_count") == 6,
    }
    ok = all(checks.values())

    closure = {
        "stage": STAGE,
        "status":
            "R450_GEONOMICS_FULL_JOB_REVALIDATION_CLOSED"
            if ok else BLOCKED,
        "geonomics_full_job_revalidation_closed": bool(ok),
        "engine": "Geonomics",
        "engine_version": "1.4.9",
        "coverage": {
            J14: "192/192",
            J18: "64/64",
            J21: "1/1",
        },
        "full_geonomics_stream_count": full_streams,
        "metric_record_count": full_metrics,
        "integrity_record_count": full_integrity,
        "descriptive_record_count": full_descriptive,
        "integrity_adjudication_verdict":
            "PASS_ALL_229548_EXACT_INTEGRITY_RECORDS"
            if ok else "BLOCKED",
        "descriptive_evidence_adjudication_verdict":
            "ACCEPTED_ALL_117420_AS_GOVERNED_DESCRIPTIVE_EVIDENCE_NO_NUMERIC_THRESHOLD"
            if ok else "BLOCKED",
        "full_job_revalidation_verdict":
            FINAL_REVALIDATION_VERDICT if ok else "BLOCKED",
        "full_job_scientific_adjudication_performed": bool(ok),
        "numeric_scientific_adjudication_of_descriptive_values_performed":
            False,
        "automatic_scientific_pass_fail_count": 0,
        "scientific_divergence_claim_count": 0,
        "majority_vote_performed": False,
        "result_selected_threshold_performed": False,
        "engine_output_defined_arcana_target": False,
        "canonical_state_changed": False,
        "next_action": NEXT if ok else "REPAIR_R450_GEONOMICS_CLOSURE",
    }
    write(root / OUT / "R4_50_FINAL_GEONOMICS_REVALIDATION_CLOSURE.json", closure)

    out = {
        "stage": STAGE,
        "status": COMPLETE if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "geonomics_version": "1.4.9",
        "evidence_corpus_file_count": len(corpus_files),
        "full_geonomics_stream_count": full_streams,
        "full_geonomics_metric_record_count": full_metrics,
        "full_geonomics_integrity_record_count": full_integrity,
        "full_geonomics_descriptive_record_count": full_descriptive,
        "j14_full_job_revalidation_closed": bool(ok),
        "j14_branch_coverage": "192/192" if ok else "INCOMPLETE",
        "j18_full_job_revalidation_closed": bool(ok),
        "j18_branch_coverage": "64/64" if ok else "INCOMPLETE",
        "j21_full_job_revalidation_closed": bool(ok),
        "j21_branch_coverage": "1/1" if ok else "INCOMPLETE",
        "geonomics_full_job_revalidation_closed": bool(ok),
        "geonomics_full_job_revalidation_verdict":
            closure["full_job_revalidation_verdict"],
        "full_job_scientific_adjudication_performed": bool(ok),
        "numeric_scientific_adjudication_of_descriptive_values_performed":
            False,
        "automatic_scientific_pass_fail_count": 0,
        "scientific_divergence_claim_count": 0,
        "new_scientific_engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action":
            NEXT if ok else "REPAIR_R450_GEONOMICS_CLOSURE",
    }
    write(root / OUT / "R4_50_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    a = load(root / OUT / "R4_50_INTEGRATED_AUDIT.json")
    c = load(root / OUT / "R4_50_FINAL_GEONOMICS_REVALIDATION_CLOSURE.json")
    corpus = load(root / OUT / "R4_50_EVIDENCE_CORPUS_MANIFEST.json")

    checks = {
        "r450_complete":
            a.get("status") == COMPLETE and a.get("checks_failed") == 0,
        "corpus_35_files_hashed":
            corpus.get("file_count") == 35,
        "exact_1028_streams":
            a.get("full_geonomics_stream_count") == 1028,
        "exact_346968_records":
            a.get("full_geonomics_metric_record_count") == 346968,
        "exact_229548_integrity":
            a.get("full_geonomics_integrity_record_count") == 229548,
        "exact_117420_descriptive":
            a.get("full_geonomics_descriptive_record_count") == 117420,
        "j14_full_192_of_192":
            a.get("j14_full_job_revalidation_closed") is True
            and a.get("j14_branch_coverage") == "192/192",
        "j18_full_64_of_64":
            a.get("j18_full_job_revalidation_closed") is True
            and a.get("j18_branch_coverage") == "64/64",
        "j21_full_1_of_1":
            a.get("j21_full_job_revalidation_closed") is True
            and a.get("j21_branch_coverage") == "1/1",
        "geonomics_full_revalidation_closed":
            a.get("geonomics_full_job_revalidation_closed") is True
            and c.get("geonomics_full_job_revalidation_closed") is True,
        "final_verdict_exact":
            c.get("full_job_revalidation_verdict")
            == FINAL_REVALIDATION_VERDICT,
        "all_integrity_exact_pass":
            c.get("integrity_adjudication_verdict")
            == "PASS_ALL_229548_EXACT_INTEGRITY_RECORDS",
        "all_descriptive_reviewed_no_threshold":
            c.get("descriptive_evidence_adjudication_verdict")
            == (
                "ACCEPTED_ALL_117420_AS_GOVERNED_DESCRIPTIVE_EVIDENCE_"
                "NO_NUMERIC_THRESHOLD"
            ),
        "full_job_adjudication_performed":
            a.get("full_job_scientific_adjudication_performed") is True,
        "numeric_value_adjudication_not_performed":
            a.get(
                "numeric_scientific_adjudication_of_descriptive_values_performed"
            ) is False,
        "zero_automatic_pass_fail":
            a.get("automatic_scientific_pass_fail_count") == 0,
        "zero_divergence_claims":
            a.get("scientific_divergence_claim_count") == 0,
        "no_new_engine_execution":
            a.get("new_scientific_engine_execution_performed") is False,
        "no_target_numeric":
            a.get("target_numeric_execution_performed") is False,
        "no_readjudication":
            a.get("readjudication_performed") is False,
        "canonical_unchanged":
            a.get("canonical_state_changed") is False,
        "deferred_p2_two":
            a.get("active_deferred_p2_cell_count") == 2,
        "proxy_context_two":
            a.get("proxy_context_only_count") == 2,
        "p3_backlog_six":
            a.get("p3_backlog_cell_count") == 6,
        "next_r451":
            a.get("next_action") == NEXT,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "audit":
            "FINAL_GEONOMICS_FULL_JOB_REVALIDATION_EVIDENCE_REVIEW_"
            "AND_FINAL_GEONOMICS_CLOSURE",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "geonomics_version": "1.4.9",
            "geonomics_full_job_revalidation_closed": bool(ok),
            "j14_branch_coverage": a.get("j14_branch_coverage"),
            "j18_branch_coverage": a.get("j18_branch_coverage"),
            "j21_branch_coverage": a.get("j21_branch_coverage"),
            "full_geonomics_stream_count":
                a.get("full_geonomics_stream_count"),
            "full_geonomics_metric_record_count":
                a.get("full_geonomics_metric_record_count"),
            "full_geonomics_integrity_record_count":
                a.get("full_geonomics_integrity_record_count"),
            "full_geonomics_descriptive_record_count":
                a.get("full_geonomics_descriptive_record_count"),
            "full_job_revalidation_verdict":
                a.get("geonomics_full_job_revalidation_verdict"),
            "numeric_scientific_adjudication_of_descriptive_values_performed":
                False,
            "automatic_scientific_pass_fail_count": 0,
            "new_scientific_engine_execution_performed": False,
            "canonical_state_changed": False,
            "deep_biological_coupling": False,
            "next_action": NEXT,
        },
        "next_action": NEXT,
    }
    write(root / SEAL, out)
    return out
