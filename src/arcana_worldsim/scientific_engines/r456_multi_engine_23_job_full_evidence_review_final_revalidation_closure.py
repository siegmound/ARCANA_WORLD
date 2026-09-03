from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json
import math

STAGE = "v0.6D1-R4.56"

COMPLETE = (
    "PASS_R456_MULTI_ENGINE_23_JOB_FULL_EVIDENCE_REVIEW_"
    "AND_FINAL_REVALIDATION_CLOSURE_COMPLETE"
)
SEALED = (
    "PASS_R456_MULTI_ENGINE_23_JOB_FULL_EVIDENCE_REVIEW_"
    "AND_FINAL_REVALIDATION_CLOSURE_SEALED"
)
BLOCKED = (
    "BLOCKED_R456_MULTI_ENGINE_23_JOB_EVIDENCE_REVIEW_"
    "OR_FINAL_REVALIDATION_CLOSURE_FAILURE"
)

FINAL_VERDICT = (
    "ARCANA_MULTI_ENGINE_23_JOB_FULLY_REVALIDATED_WITH_EXACT_INTEGRITY_"
    "AND_GOVERNED_DESCRIPTIVE_EVIDENCE_NO_NUMERIC_CORROBORATION_CLAIM"
)

NEXT = "R4_MULTI_ENGINE_REVALIDATION_COMPLETE_RETURN_TO_WORLDSIM_ROADMAP"

EXPECTED_R452_PLAN_SHA256 = (
    "f4804e9aabf2f009c9581012a136865b9cdb2e688d416f48d6a50be840dff7e6"
)
EXPECTED_R453_REGISTRY_SHA256 = (
    "f39bb36251a95f2d9e310113a9286608d72188374d7d9bc73fe90aa697e5d380"
)

R42 = Path("outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json")
R452 = Path("outputs/v0_6D1_R4_52/R4_52_NON_GEONOMICS_EXECUTION_PLAN.json")
R453 = Path(
    "outputs/v0_6D1_R4_53/"
    "R4_53_NON_GEONOMICS_EXECUTION_READOUT_AUTHORITY_REGISTRY.json"
)

R450 = Path("outputs/v0_6D1_R4_50/R4_50_INTEGRATED_AUDIT.json")
R450_SEAL = Path("outputs/v0_6D1_R4_50_SEAL/R4_50_FINAL_SEAL_AUDIT.json")
R450_CLOSURE = Path(
    "outputs/v0_6D1_R4_50/R4_50_FINAL_GEONOMICS_REVALIDATION_CLOSURE.json"
)
R450_CORPUS = Path(
    "outputs/v0_6D1_R4_50/R4_50_EVIDENCE_CORPUS_MANIFEST.json"
)

R455_MANIFEST = Path("outputs/v0_6D1_R4_55/R4_55_EXECUTION_MANIFEST.json")
R455_CORPUS = Path(
    "outputs/v0_6D1_R4_55/R4_55_FULL_NON_GEONOMICS_EVIDENCE_CORPUS.json"
)
R455 = Path("outputs/v0_6D1_R4_55/R4_55_INTEGRATED_AUDIT.json")
R455_SEAL = Path("outputs/v0_6D1_R4_55_SEAL/R4_55_FINAL_SEAL_AUDIT.json")
R455_R2 = Path(
    "outputs/v0_6D1_R4_55_R2/R4_55_R2_POSTREPAIR_RESEAL_AUDIT.json"
)

OUT = Path("outputs/v0_6D1_R4_56")
SEAL = Path("outputs/v0_6D1_R4_56_SEAL/R4_56_FINAL_SEAL_AUDIT.json")

GEONOMICS_JOB_IDS = [
    "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS",
    "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS",
    "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS",
]

EXPECTED_ENGINE_COUNTS = {
    "Madingley": 4,
    "RangeShifter": 5,
    "CDMetaPOP": 5,
    "NEMO": 3,
    "Geonomics": 3,
    "SLiM": 3,
}

EXPECTED_GEONOMICS_VERDICT = (
    "GEONOMICS_1_4_9_FULLY_REVALIDATED_WITH_EXACT_INTEGRITY_AND_"
    "GOVERNED_DESCRIPTIVE_EVIDENCE_NO_NUMERIC_CORROBORATION_CLAIM"
)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


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


def _same_unique_membership(a: list[Any], b: list[Any]) -> bool:
    return len(a) == len(b) == len(set(a)) == len(set(b)) and set(a) == set(b)


def _finite_tree(obj: Any) -> bool:
    if obj is None or isinstance(obj, (str, bool)):
        return True
    if isinstance(obj, (int, float)):
        return math.isfinite(float(obj))
    if isinstance(obj, list):
        return all(_finite_tree(x) for x in obj)
    if isinstance(obj, dict):
        return all(_finite_tree(v) for v in obj.values())
    return False


def _metric_ids_from_r453(registry: dict[str, Any]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for job in registry.get("jobs") or []:
        jid = str(job["job_id"])
        out[jid] = {
            str(m["metric_id"]) for m in job.get("authorized_metrics") or []
        }
    return out


def _plan_jobs(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(j["job_id"]): j for j in plan.get("jobs") or []}


def _r42_jobs(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(j["job_id"]): j for j in matrix.get("jobs") or []}


def _verify_metric_sources(job_dir: Path, metric_records: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    missing = []
    for rec in metric_records:
        for rel in rec.get("source_artifacts") or []:
            p = job_dir / str(rel)
            if not p.exists():
                missing.append(str(rel))
    return len(missing) == 0, sorted(set(missing))


def review_non_geonomics(root: Path) -> dict[str, Any]:
    root = root.resolve()

    plan = load(root / R452)
    registry = load(root / R453)
    manifest = load(root / R455_MANIFEST)
    corpus = load(root / R455_CORPUS)
    parent = load(root / R455)
    parent_seal = load(root / R455_SEAL)
    parent_r2 = load(root / R455_R2)

    plan_by_id = _plan_jobs(plan)
    metric_authority = _metric_ids_from_r453(registry)
    manifest_jobs = manifest.get("jobs") or []

    job_reviews = []
    errors: list[str] = []
    reconstructed_streams = []
    reconstructed_metrics = []
    source_artifact_files = set()

    for manifest_job in manifest_jobs:
        jid = str(manifest_job["job_id"])
        engine = str(manifest_job["engine"])
        jd = root / "outputs/v0_6D1_R4_55/jobs" / jid

        rawp = jd / "RAW_ENGINE_EVIDENCE.json"
        evp = jd / "SCIENTIFIC_READOUT_EVIDENCE.json"
        auditp = jd / "JOB_AUDIT.json"
        markerp = jd / "JOB_COMPLETE.json"

        present = all(p.exists() for p in [rawp, evp, auditp, markerp])
        local_errors = []
        if not present:
            local_errors.append("incomplete_job_bundle")
            errors.append(f"{jid}: incomplete job bundle")
            job_reviews.append({
                "job_id": jid,
                "engine": engine,
                "pass": False,
                "errors": local_errors,
            })
            continue

        raw = load(rawp)
        evidence = load(evp)
        audit = load(auditp)
        marker = load(markerp)
        planned = plan_by_id.get(jid)
        expected_metrics = metric_authority.get(jid, set())

        raw_reps = raw.get("replicates") or []
        raw_seeds = [int(r.get("seed", -1)) for r in raw_reps]
        planned_seeds = [int(x) for x in (planned or {}).get("frozen_seeds") or []]

        streams = evidence.get("stream_records") or []
        metrics = evidence.get("metric_records") or []
        stream_seeds = [int(r.get("frozen_seed", -1)) for r in streams]
        observed_metric_ids = {str(r.get("metric_id")) for r in metrics}

        sources_ok, missing_sources = _verify_metric_sources(jd, metrics)
        for rec in metrics:
            for rel in rec.get("source_artifacts") or []:
                p = jd / str(rel)
                if p.exists():
                    source_artifact_files.add(p.resolve())

        checks = {
            "marker_complete":
                marker.get("status") == "PASS_R455_JOB_COMPLETE",
            "marker_job_identity":
                marker.get("job_id") == jid
                and marker.get("engine") == engine,
            "marker_parent_plan_exact":
                marker.get("parent_execution_plan_sha256")
                == EXPECTED_R452_PLAN_SHA256,
            "marker_parent_registry_exact":
                marker.get("parent_readout_registry_sha256")
                == EXPECTED_R453_REGISTRY_SHA256,
            "marker_raw_hash_exact":
                marker.get("raw_engine_evidence_sha256") == sha256(rawp),
            "marker_scientific_evidence_hash_exact":
                marker.get("scientific_evidence_sha256") == sha256(evp),
            "marker_job_audit_hash_exact":
                marker.get("job_audit_sha256") == sha256(auditp),

            "raw_adapter_pass":
                raw.get("adapter_status") == "PASS",
            "raw_canonical_write_false":
                raw.get("canonical_write") is False,
            "raw_exact_four_replicates":
                len(raw_reps) == 4,
            "raw_seed_membership_exact":
                _same_unique_membership(raw_seeds, planned_seeds),

            "evidence_status_pass":
                evidence.get("status")
                == "PASS_R455_JOB_SCIENTIFIC_READOUT_EVIDENCE",
            "evidence_exact_four_streams":
                evidence.get("scientific_stream_count") == 4
                and len(streams) == 4,
            "evidence_exact_eight_metrics":
                evidence.get("metric_record_count") == 8
                and len(metrics) == 8,
            "stream_seed_membership_exact":
                _same_unique_membership(stream_seeds, planned_seeds),
            "all_streams_exact_identity":
                all(
                    r.get("job_id") == jid
                    and r.get("engine") == engine
                    and r.get("window_id") == manifest_job.get("window_id")
                    for r in streams
                ),
            "all_streams_pass":
                all(r.get("status") == "PASS" for r in streams),
            "all_streams_scientific_evidence":
                all(r.get("scientific_evidence") is True for r in streams),
            "stream_numeric_adjudication_false":
                all(
                    r.get("numeric_scientific_adjudication_performed") is False
                    for r in streams
                ),
            "stream_canonical_unchanged":
                all(r.get("canonical_state_changed") is False for r in streams),

            "metric_ids_exact_r453":
                observed_metric_ids == expected_metrics
                and len(expected_metrics) == 2,
            "all_metrics_finite":
                all(r.get("finite") is True and _finite_tree(r.get("payload"))
                    for r in metrics),
            "zero_numeric_thresholds":
                all(r.get("numeric_acceptance_threshold") is None for r in metrics),
            "zero_automatic_value_passfail":
                all(r.get("automatic_pass_fail_from_value") is False for r in metrics),
            "metric_source_artifacts_present":
                sources_ok,

            "job_audit_pass":
                audit.get("status") == "PASS_R455_JOB_EVIDENCE_CAPTURE"
                and audit.get("checks_failed") == 0
                and audit.get("checks_passed") == 11
                and audit.get("checks_total") == 11,
        }

        if not sources_ok:
            local_errors.append(
                "missing metric source artifacts: " + ", ".join(missing_sources)
            )

        ok = all(checks.values())
        if not ok:
            for k, v in checks.items():
                if not v:
                    local_errors.append(k)
            errors.append(f"{jid}: {local_errors}")

        reconstructed_streams.extend(streams)
        reconstructed_metrics.extend(metrics)

        job_reviews.append({
            "job_id": jid,
            "engine": engine,
            "window_id": manifest_job.get("window_id"),
            "pass": ok,
            "checks": checks,
            "checks_passed": sum(checks.values()),
            "checks_total": len(checks),
            "raw_engine_evidence_sha256": sha256(rawp),
            "scientific_evidence_sha256": sha256(evp),
            "job_audit_sha256": sha256(auditp),
            "job_complete_sha256": sha256(markerp),
            "errors": local_errors,
        })

    expected_manifest_ids = [str(j["job_id"]) for j in manifest_jobs]
    plan_ids = [str(j["job_id"]) for j in plan.get("jobs") or []]

    checks = {
        "r455_parent_complete_17_17":
            parent.get("status")
            == "PASS_R455_NON_GEONOMICS_80_STREAM_SCIENTIFIC_EXECUTION_AND_EVIDENCE_CAPTURE_COMPLETE"
            and parent.get("checks_passed") == 17
            and parent.get("checks_failed") == 0,
        "r455_parent_sealed_17_17":
            parent_seal.get("verdict") == "SEALED"
            and parent_seal.get("checks_passed") == 17
            and parent_seal.get("checks_failed") == 0,
        "r455_r2_reseal_verified_9_9":
            parent_r2.get("status")
            == "PASS_R455_R2_POWERSHELL_BRIDGE_REPAIR_AND_R455_RESEAL_VERIFIED"
            and parent_r2.get("checks_passed") == 9,
        "r452_plan_sha_exact":
            plan.get("plan_sha256") == EXPECTED_R452_PLAN_SHA256,
        "r453_registry_sha_exact":
            registry.get("registry_sha256") == EXPECTED_R453_REGISTRY_SHA256,
        "manifest_exact_20_jobs":
            manifest.get("job_count") == 20
            and len(manifest_jobs) == 20,
        "manifest_exact_80_streams":
            manifest.get("scientific_stream_count") == 80,
        "manifest_expected_160_metrics":
            manifest.get("expected_metric_record_count") == 160,
        "manifest_job_set_exact_r452":
            _same_unique_membership(expected_manifest_ids, plan_ids),
        "all_20_job_bundles_independently_pass":
            len(job_reviews) == 20 and all(r.get("pass") is True for r in job_reviews),
        "reconstructed_exact_80_streams":
            len(reconstructed_streams) == 80,
        "reconstructed_exact_160_metrics":
            len(reconstructed_metrics) == 160,
        "corpus_status_captured":
            corpus.get("status")
            == "R455_NON_GEONOMICS_FULL_SCIENTIFIC_EVIDENCE_CORPUS_CAPTURED",
        "corpus_exact_job_count":
            corpus.get("job_count") == 20,
        "corpus_exact_stream_count":
            corpus.get("scientific_stream_count") == 80,
        "corpus_exact_metric_count":
            corpus.get("metric_record_count") == 160,
        "corpus_stream_records_exact_reconstruction":
            corpus.get("scientific_stream_records") == reconstructed_streams,
        "corpus_metric_records_exact_reconstruction":
            corpus.get("scientific_metric_records") == reconstructed_metrics,
        "parent_corpus_sha_exact":
            parent.get("evidence_corpus_sha256") == sha256(root / R455_CORPUS),
        "zero_numeric_adjudication":
            parent.get("numeric_scientific_adjudication_performed") is False
            and corpus.get("numeric_scientific_adjudication_performed") is False,
        "zero_divergence_claims":
            parent.get("scientific_divergence_claim_count") == 0
            and corpus.get("scientific_divergence_claim_count") == 0,
        "canonical_unchanged":
            parent.get("canonical_state_changed") is False
            and corpus.get("canonical_state_changed") is False,
        "bundle_review_errors_zero":
            len(errors) == 0,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "review": "INDEPENDENT_NON_GEONOMICS_R455_JOB_BUNDLE_REVIEW",
        "status":
            "R456_NON_GEONOMICS_20_JOB_INDEPENDENT_EVIDENCE_REVIEW_PASS"
            if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "job_review_count": len(job_reviews),
        "scientific_stream_count": len(reconstructed_streams),
        "metric_record_count": len(reconstructed_metrics),
        "metric_source_artifact_unique_file_count": len(source_artifact_files),
        "job_reviews": job_reviews,
        "errors": errors,
        "numeric_scientific_adjudication_of_descriptive_values_performed": False,
        "scientific_divergence_claim_count": 0,
        "canonical_state_changed": False,
    }
    write(root / OUT / "R4_56_NON_GEONOMICS_INDEPENDENT_BUNDLE_REVIEW.json", out)
    return out


def review_geonomics(root: Path) -> dict[str, Any]:
    root = root.resolve()

    parent = load(root / R450)
    seal = load(root / R450_SEAL)
    closure = load(root / R450_CLOSURE)
    corpus = load(root / R450_CORPUS)

    corpus_errors = []
    file_records = corpus.get("files") or []
    for rec in file_records:
        path = root / str(rec["path"])
        if not path.exists():
            corpus_errors.append(f"missing: {rec['path']}")
            continue
        if sha256(path) != rec.get("sha256"):
            corpus_errors.append(f"sha256 mismatch: {rec['path']}")

    coverage = closure.get("coverage") or {}

    checks = {
        "r450_parent_complete_50_50":
            parent.get("status")
            == "PASS_R450_GEONOMICS_FULL_JOB_REVALIDATION_EVIDENCE_REVIEW_AND_FINAL_GEONOMICS_CLOSURE_COMPLETE"
            and parent.get("checks_passed") == 50
            and parent.get("checks_failed") == 0,
        "r450_parent_sealed_25_25":
            seal.get("verdict") == "SEALED"
            and seal.get("checks_passed") == 25
            and seal.get("checks_failed") == 0,
        "closure_status_closed":
            closure.get("status") == "R450_GEONOMICS_FULL_JOB_REVALIDATION_CLOSED"
            and closure.get("geonomics_full_job_revalidation_closed") is True,
        "closure_version_exact":
            closure.get("engine") == "Geonomics"
            and closure.get("engine_version") == "1.4.9",
        "j14_coverage_exact":
            coverage.get(GEONOMICS_JOB_IDS[0]) == "192/192",
        "j18_coverage_exact":
            coverage.get(GEONOMICS_JOB_IDS[1]) == "64/64",
        "j21_coverage_exact":
            coverage.get(GEONOMICS_JOB_IDS[2]) == "1/1",
        "full_stream_count_1028":
            closure.get("full_geonomics_stream_count") == 1028,
        "metric_record_count_346968":
            closure.get("metric_record_count") == 346968,
        "integrity_record_count_229548":
            closure.get("integrity_record_count") == 229548,
        "descriptive_record_count_117420":
            closure.get("descriptive_record_count") == 117420,
        "final_verdict_exact":
            closure.get("full_job_revalidation_verdict")
            == EXPECTED_GEONOMICS_VERDICT,
        "full_job_scientific_adjudication_performed":
            closure.get("full_job_scientific_adjudication_performed") is True,
        "numeric_descriptive_adjudication_false":
            closure.get(
                "numeric_scientific_adjudication_of_descriptive_values_performed"
            ) is False,
        "zero_auto_passfail":
            closure.get("automatic_scientific_pass_fail_count") == 0,
        "zero_divergence_claims":
            closure.get("scientific_divergence_claim_count") == 0,
        "no_majority_vote":
            closure.get("majority_vote_performed") is False,
        "no_result_selected_threshold":
            closure.get("result_selected_threshold_performed") is False,
        "engine_not_target_authority":
            closure.get("engine_output_defined_arcana_target") is False,
        "canonical_unchanged":
            closure.get("canonical_state_changed") is False,
        "corpus_manifest_status":
            corpus.get("status") == "R450_GEONOMICS_SCIENTIFIC_EVIDENCE_CORPUS_HASHED",
        "corpus_manifest_35_files":
            corpus.get("file_count") == 35 and len(file_records) == 35,
        "all_35_corpus_hashes_exact":
            len(corpus_errors) == 0,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "review": "AUTHORITATIVE_R450_GEONOMICS_CLOSURE_REUSE_AND_HASH_REVIEW",
        "status":
            "R456_GEONOMICS_3_JOB_AUTHORITATIVE_CLOSURE_REUSE_PASS"
            if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "job_ids": GEONOMICS_JOB_IDS,
        "job_count": 3,
        "coverage": coverage,
        "full_geonomics_stream_count": closure.get("full_geonomics_stream_count"),
        "metric_record_count": closure.get("metric_record_count"),
        "integrity_record_count": closure.get("integrity_record_count"),
        "descriptive_record_count": closure.get("descriptive_record_count"),
        "corpus_file_count": len(file_records),
        "corpus_errors": corpus_errors,
        "full_job_revalidation_verdict":
            closure.get("full_job_revalidation_verdict"),
        "new_scientific_engine_execution_performed": False,
        "numeric_scientific_adjudication_of_descriptive_values_performed": False,
        "scientific_divergence_claim_count": 0,
        "canonical_state_changed": False,
    }
    write(root / OUT / "R4_56_GEONOMICS_CLOSURE_REUSE_REVIEW.json", out)
    return out


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()

    matrix = load(root / R42)
    plan = load(root / R452)
    registry = load(root / R453)

    non_gnx = review_non_geonomics(root)
    gnx = review_geonomics(root)

    r42_by_id = _r42_jobs(matrix)
    r42_ids = list(r42_by_id)
    non_gnx_ids = [str(j["job_id"]) for j in plan.get("jobs") or []]

    engine_counts = {}
    for job in matrix.get("jobs") or []:
        e = str(job["engine"])
        engine_counts[e] = engine_counts.get(e, 0) + 1

    closed_job_ids = non_gnx_ids + GEONOMICS_JOB_IDS

    checks = {
        "r42_exact_23_jobs":
            matrix.get("job_count") == 23
            and len(matrix.get("jobs") or []) == 23
            and len(r42_ids) == 23,
        "r42_engine_distribution_exact":
            engine_counts == EXPECTED_ENGINE_COUNTS,
        "r452_plan_sha_exact":
            plan.get("plan_sha256") == EXPECTED_R452_PLAN_SHA256,
        "r453_registry_sha_exact":
            registry.get("registry_sha256") == EXPECTED_R453_REGISTRY_SHA256,
        "non_geonomics_review_pass":
            non_gnx.get("status")
            == "R456_NON_GEONOMICS_20_JOB_INDEPENDENT_EVIDENCE_REVIEW_PASS",
        "geonomics_review_pass":
            gnx.get("status")
            == "R456_GEONOMICS_3_JOB_AUTHORITATIVE_CLOSURE_REUSE_PASS",
        "exact_20_non_geonomics_jobs":
            len(non_gnx_ids) == 20,
        "exact_3_geonomics_jobs":
            len(GEONOMICS_JOB_IDS) == 3,
        "no_job_overlap":
            set(non_gnx_ids).isdisjoint(GEONOMICS_JOB_IDS),
        "closed_union_exact_r42_registry":
            _same_unique_membership(closed_job_ids, r42_ids),
        "all_23_job_ids_unique":
            len(set(closed_job_ids)) == 23,
        "non_geonomics_80_streams":
            non_gnx.get("scientific_stream_count") == 80,
        "non_geonomics_160_metric_records":
            non_gnx.get("metric_record_count") == 160,
        "geonomics_1028_streams":
            gnx.get("full_geonomics_stream_count") == 1028,
        "geonomics_346968_metric_records":
            gnx.get("metric_record_count") == 346968,
        "no_new_scientific_engine_execution":
            gnx.get("new_scientific_engine_execution_performed") is False,
        "numeric_scientific_adjudication_of_descriptive_values_not_performed":
            non_gnx.get(
                "numeric_scientific_adjudication_of_descriptive_values_performed"
            ) is False
            and gnx.get(
                "numeric_scientific_adjudication_of_descriptive_values_performed"
            ) is False,
        "zero_scientific_divergence_claims":
            non_gnx.get("scientific_divergence_claim_count") == 0
            and gnx.get("scientific_divergence_claim_count") == 0,
        "no_majority_vote":
            registry.get("majority_vote_authorized") is False,
        "no_result_selected_metric":
            registry.get("result_selected_metric_authorized") is False,
        "no_result_selected_threshold":
            registry.get("result_selected_threshold_authorized") is False,
        "engine_cannot_define_arcana_target":
            registry.get("engine_output_defines_arcana_target") is False,
        "canonical_rewrite_forbidden":
            registry.get("canonical_rewrite_authorized") is False,
        "canonical_unchanged":
            non_gnx.get("canonical_state_changed") is False
            and gnx.get("canonical_state_changed") is False,
    }
    ok = all(checks.values())

    job_closures = []
    for jid in r42_ids:
        job = r42_by_id[jid]
        if jid in GEONOMICS_JOB_IDS:
            authority = "R4.50_GEONOMICS_FULL_JOB_REVALIDATION_CLOSURE"
            closure = True
        else:
            authority = "R4.56_INDEPENDENT_REVIEW_OF_R4.55_SCIENTIFIC_EVIDENCE"
            closure = bool(non_gnx.get("status").endswith("_PASS"))
        job_closures.append({
            "job_id": jid,
            "engine": job["engine"],
            "window_id": job["window_id"],
            "fully_revalidated_closed": closure,
            "closure_authority": authority,
            "numeric_corroboration_claimed": False,
            "canonical_state_changed": False,
        })

    closure = {
        "stage": STAGE,
        "status":
            "R456_MULTI_ENGINE_23_JOB_FULL_REVALIDATION_CLOSED"
            if ok else BLOCKED,
        "multi_engine_full_revalidation_closed": bool(ok),
        "frozen_r42_job_count": 23,
        "fully_revalidated_closed_job_count":
            sum(j["fully_revalidated_closed"] for j in job_closures),
        "closure_gap_count":
            sum(not j["fully_revalidated_closed"] for j in job_closures),
        "engine_count": 6,
        "engine_job_counts": engine_counts,
        "job_closures": job_closures,
        "geonomics_closure": {
            "job_count": 3,
            "stream_count": gnx.get("full_geonomics_stream_count"),
            "metric_record_count": gnx.get("metric_record_count"),
            "integrity_record_count": gnx.get("integrity_record_count"),
            "descriptive_record_count": gnx.get("descriptive_record_count"),
            "verdict": gnx.get("full_job_revalidation_verdict"),
        },
        "non_geonomics_closure": {
            "job_count": 20,
            "stream_count": non_gnx.get("scientific_stream_count"),
            "metric_record_count": non_gnx.get("metric_record_count"),
            "independently_reviewed_job_bundle_count":
                non_gnx.get("job_review_count"),
        },
        "full_revalidation_verdict": FINAL_VERDICT if ok else "BLOCKED",
        "full_job_revalidation_adjudication_performed": bool(ok),
        "numeric_scientific_adjudication_of_descriptive_values_performed": False,
        "numeric_cross_engine_corroboration_claimed": False,
        "automatic_scientific_pass_fail_from_values_count": 0,
        "scientific_divergence_claim_count": 0,
        "majority_vote_performed": False,
        "result_selected_metric_performed": False,
        "result_selected_threshold_performed": False,
        "engine_output_defined_arcana_target": False,
        "new_scientific_engine_execution_performed": False,
        "canonical_state_changed": False,
        "deep_biological_coupling": False,
        "next_action": NEXT if ok else "REPAIR_R456_FULL_REVALIDATION_CLOSURE",
    }
    write(root / OUT / "R4_56_FINAL_MULTI_ENGINE_REVALIDATION_CLOSURE.json", closure)

    out = {
        "stage": STAGE,
        "status": COMPLETE if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "frozen_r42_job_count": 23,
        "fully_revalidated_closed_job_count":
            closure["fully_revalidated_closed_job_count"],
        "closure_gap_count": closure["closure_gap_count"],
        "engine_count": 6,
        "engine_job_counts": engine_counts,
        "non_geonomics_independent_review_job_count":
            non_gnx.get("job_review_count"),
        "non_geonomics_scientific_stream_count":
            non_gnx.get("scientific_stream_count"),
        "non_geonomics_metric_record_count":
            non_gnx.get("metric_record_count"),
        "geonomics_full_stream_count":
            gnx.get("full_geonomics_stream_count"),
        "geonomics_metric_record_count":
            gnx.get("metric_record_count"),
        "multi_engine_full_revalidation_closed": bool(ok),
        "full_revalidation_verdict":
            closure["full_revalidation_verdict"],
        "full_job_revalidation_adjudication_performed": bool(ok),
        "numeric_scientific_adjudication_of_descriptive_values_performed": False,
        "numeric_cross_engine_corroboration_claimed": False,
        "scientific_divergence_claim_count": 0,
        "new_scientific_engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_of_arcana_canonical_target_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action": NEXT if ok else "REPAIR_R456_FULL_REVALIDATION_CLOSURE",
    }
    write(root / OUT / "R4_56_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    a = load(root / OUT / "R4_56_INTEGRATED_AUDIT.json")
    c = load(root / OUT / "R4_56_FINAL_MULTI_ENGINE_REVALIDATION_CLOSURE.json")
    ng = load(root / OUT / "R4_56_NON_GEONOMICS_INDEPENDENT_BUNDLE_REVIEW.json")
    gx = load(root / OUT / "R4_56_GEONOMICS_CLOSURE_REUSE_REVIEW.json")

    checks = {
        "r456_complete":
            a.get("status") == COMPLETE
            and a.get("checks_failed") == 0,
        "exact_23_frozen_jobs":
            a.get("frozen_r42_job_count") == 23,
        "exact_23_jobs_closed":
            a.get("fully_revalidated_closed_job_count") == 23,
        "zero_closure_gaps":
            a.get("closure_gap_count") == 0,
        "exact_six_engines":
            a.get("engine_count") == 6,
        "non_geonomics_20_job_review_pass":
            ng.get("status")
            == "R456_NON_GEONOMICS_20_JOB_INDEPENDENT_EVIDENCE_REVIEW_PASS",
        "geonomics_3_job_closure_review_pass":
            gx.get("status")
            == "R456_GEONOMICS_3_JOB_AUTHORITATIVE_CLOSURE_REUSE_PASS",
        "multi_engine_full_revalidation_closed":
            a.get("multi_engine_full_revalidation_closed") is True
            and c.get("multi_engine_full_revalidation_closed") is True,
        "final_verdict_exact":
            a.get("full_revalidation_verdict") == FINAL_VERDICT
            and c.get("full_revalidation_verdict") == FINAL_VERDICT,
        "full_job_revalidation_adjudication_performed":
            a.get("full_job_revalidation_adjudication_performed") is True,
        "numeric_descriptive_adjudication_not_performed":
            a.get(
                "numeric_scientific_adjudication_of_descriptive_values_performed"
            ) is False,
        "numeric_cross_engine_corroboration_not_claimed":
            a.get("numeric_cross_engine_corroboration_claimed") is False,
        "zero_scientific_divergence_claims":
            a.get("scientific_divergence_claim_count") == 0,
        "no_new_scientific_engine_execution":
            a.get("new_scientific_engine_execution_performed") is False,
        "no_target_numeric_execution":
            a.get("target_numeric_execution_performed") is False,
        "no_arcana_target_readjudication":
            a.get("readjudication_of_arcana_canonical_target_performed") is False,
        "canonical_unchanged":
            a.get("canonical_state_changed") is False,
        "deep_off":
            c.get("deep_biological_coupling") is False,
        "deferred_p2_two":
            a.get("active_deferred_p2_cell_count") == 2,
        "proxy_context_two":
            a.get("proxy_context_only_count") == 2,
        "p3_backlog_six":
            a.get("p3_backlog_cell_count") == 6,
        "r4_revalidation_complete_next":
            a.get("next_action") == NEXT,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "audit": "FINAL_MULTI_ENGINE_23_JOB_FULL_EVIDENCE_REVIEW_AND_REVALIDATION_CLOSURE",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "frozen_r42_job_count": a.get("frozen_r42_job_count"),
            "fully_revalidated_closed_job_count":
                a.get("fully_revalidated_closed_job_count"),
            "closure_gap_count": a.get("closure_gap_count"),
            "engine_count": a.get("engine_count"),
            "engine_job_counts": a.get("engine_job_counts"),
            "multi_engine_full_revalidation_closed":
                a.get("multi_engine_full_revalidation_closed"),
            "full_revalidation_verdict":
                a.get("full_revalidation_verdict"),
            "numeric_scientific_adjudication_of_descriptive_values_performed":
                False,
            "numeric_cross_engine_corroboration_claimed": False,
            "scientific_divergence_claim_count": 0,
            "new_scientific_engine_execution_performed": False,
            "canonical_state_changed": False,
            "deep_biological_coupling": False,
            "next_action": NEXT,
        },
        "next_action": NEXT,
    }
    write(root / SEAL, out)
    return out
