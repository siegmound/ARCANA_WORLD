from __future__ import annotations

from pathlib import Path
from typing import Any
import copy
import hashlib
import json

STAGE = "v0.6D1-R4.53"

PARENT_COMPLETE = (
    "PASS_R452_NON_GEONOMICS_JOB_SPECIFIC_EVIDENCE_ADJUDICATION_"
    "AND_EXECUTION_PLAN_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R452_NON_GEONOMICS_JOB_SPECIFIC_EVIDENCE_ADJUDICATION_"
    "AND_EXECUTION_PLAN_SEALED"
)
PARENT_NEXT = (
    "BUILD_R453_NON_GEONOMICS_SCIENTIFIC_EXECUTION_INTERFACE_"
    "AND_READOUT_AUTHORITY_PREFLIGHT"
)
EXPECTED_R452_PLAN_SHA256 = (
    "f4804e9aabf2f009c9581012a136865b9cdb2e688d416f48d6a50be840dff7e6"
)

COMPLETE = (
    "PASS_R453_NON_GEONOMICS_SCIENTIFIC_EXECUTION_INTERFACE_"
    "AND_READOUT_AUTHORITY_PREFLIGHT_COMPLETE"
)
SEALED = (
    "PASS_R453_NON_GEONOMICS_SCIENTIFIC_EXECUTION_INTERFACE_"
    "AND_READOUT_AUTHORITY_PREFLIGHT_SEALED"
)
BLOCKED = "BLOCKED_R453_EXECUTION_INTERFACE_OR_READOUT_AUTHORITY_PREFLIGHT_FAILURE"
NEXT = (
    "BUILD_R454_NON_GEONOMICS_EXACT_SEED_INJECTION_READOUT_EXTRACTION_"
    "DRY_RUN_AND_SCHEMA_VALIDATION"
)

OUT = Path("outputs/v0_6D1_R4_53")
SEAL = Path("outputs/v0_6D1_R4_53_SEAL/R4_53_FINAL_SEAL_AUDIT.json")
CFG = Path(
    "configs/world1_r453_non_geonomics_scientific_execution_interface_"
    "readout_authority_preflight_v0_6D1_R4_53.json"
)

R452 = Path("outputs/v0_6D1_R4_52/R4_52_INTEGRATED_AUDIT.json")
R452_SEAL = Path("outputs/v0_6D1_R4_52_SEAL/R4_52_FINAL_SEAL_AUDIT.json")
R452_PLAN = Path("outputs/v0_6D1_R4_52/R4_52_NON_GEONOMICS_EXECUTION_PLAN.json")
R41_CONFIG = Path("configs/world1_r41_semantic_calibration_v0_6D1_R4_1.json")
R41_HOST = Path("outputs/v0_6D1_R4_1/R4_1_HOST_MICROBENCHMARK_EVIDENCE.json")

EXPECTED_VERSIONS = {
    "Madingley": "MadingleyR-1.0.6__CPP-2.02",
    "RangeShifter": "3.0.1",
    "CDMetaPOP": "3.08",
    "NEMO": "2.4.2",
    "SLiM": "5.2",
}

R41_BENCHMARK_IDS = {
    "Madingley": "R41_MADINGLEY_ONE_YEAR_ECOSYSTEM",
    "RangeShifter": "R41_RANGESHIFTR_DEFAULT_RANGE_DYNAMICS",
    "CDMetaPOP": "R41_CDMETAPOP_BUNDLED_5GEN_EXAMPLE",
    "NEMO": "R41_NEMO_B1_ADMIXTURE_CONVERGENCE",
    "SLiM": "R41_SLIM_TWO_POP_TREESEQ_GENE_FLOW",
}

READOUT_AUTHORITY = {
    "Madingley": {
        "execution_interface": {
            "runtime": "GOVERNED_RSCRIPT_MADINGLEYR_1_0_6_CPP_2_02",
            "seed_requirement": "EXACT_R452_FROZEN_SEED_INJECTION_REQUIRED",
            "isolated_output_root_required": True,
        },
        "authorized_artifacts": [
            "MADINGLEY_NATIVE_GRID_AND_COHORT_STOCK_OUTPUTS"
        ],
        "metrics": [
            {
                "metric_id": "MADINGLEY_COHORT_COUNT_TRAJECTORY",
                "role": "SCIENTIFIC_DESCRIPTIVE_ECOSYSTEM_STATE",
                "semantics": "functional cohort count trajectory; not ARCANA species identity",
            },
            {
                "metric_id": "MADINGLEY_STOCK_COUNT_TRAJECTORY",
                "role": "SCIENTIFIC_DESCRIPTIVE_ECOSYSTEM_STATE",
                "semantics": "functional autotroph stock count trajectory; not ARCANA species identity",
            },
        ],
        "integrity_fields": ["runtime_version", "frozen_seed", "time_axis", "output_artifact_hashes"],
    },
    "RangeShifter": {
        "execution_interface": {
            "runtime": "GOVERNED_RSCRIPT_RANGESHIFTR_3_0_1",
            "seed_requirement": "EXACT_R452_FROZEN_SEED_INJECTION_REQUIRED",
            "isolated_output_root_required": True,
        },
        "authorized_artifacts": ["RANGESHIFTER_NATIVE_RANGE_OUTPUTS"],
        "metrics": [
            {
                "metric_id": "RANGESHIFTER_ABUNDANCE_TRAJECTORY",
                "role": "SCIENTIFIC_DESCRIPTIVE_RANGE_STATE",
                "semantics": "native abundance trajectory; no literal ARCANA population-unit equality",
            },
            {
                "metric_id": "RANGESHIFTER_OCCUPIED_CELL_TRAJECTORY",
                "role": "SCIENTIFIC_DESCRIPTIVE_RANGE_STATE",
                "semantics": "native occupied-cell trajectory under explicit eligible-habitat denominator",
            },
        ],
        "integrity_fields": ["runtime_version", "frozen_seed", "time_axis", "output_artifact_hashes"],
    },
    "CDMetaPOP": {
        "execution_interface": {
            "runtime": "GOVERNED_WSL_PYTHON38_CDMETAPOP_3_08_PINNED_COMMIT",
            "source_commit": "3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118",
            "seed_requirement": "EXACT_R452_FROZEN_SEED_INJECTION_REQUIRED",
            "isolated_output_root_required": True,
        },
        "authorized_artifacts": [
            "summary_popAllTime.csv",
            "summary_classAllTime.csv",
        ],
        "metrics": [
            {
                "metric_id": "CDMETAPOP_POPULATION_STATE_TRAJECTORY",
                "role": "SCIENTIFIC_DESCRIPTIVE_DEMOGRAPHIC_STATE",
                "source_fields": ["Year", "N_Initial"],
                "semantics": "native patch-vector demographic state; no literal ARCANA population-unit equality",
            },
            {
                "metric_id": "CDMETAPOP_GENETIC_DIVERSITY_TRAJECTORY",
                "role": "SCIENTIFIC_DESCRIPTIVE_GENETIC_STATE",
                "source_fields": ["Year", "Alleles", "He", "Ho"],
                "semantics": "native genetic diversity trajectory where populated by the job configuration",
            },
        ],
        "integrity_fields": [
            "runtime_version", "source_commit", "frozen_seed", "Year",
            "summary_schema", "output_artifact_hashes"
        ],
    },
    "NEMO": {
        "execution_interface": {
            "runtime": "GOVERNED_WSL_NEMO_2_4_2",
            "seed_requirement": "EXACT_R452_FROZEN_SEED_INJECTION_REQUIRED",
            "isolated_output_root_required": True,
        },
        "authorized_artifacts": ["NEMO_NATIVE_QFREQ_OUTPUT"],
        "metrics": [
            {
                "metric_id": "NEMO_ALLELE_FREQUENCY_TRAJECTORY",
                "role": "SCIENTIFIC_DESCRIPTIVE_GENETIC_STATE",
                "semantics": "raw realized qfreq/allele-frequency trajectory",
            },
            {
                "metric_id": "NEMO_REALIZED_FREQUENCY_CHANGE_SUMMARY",
                "role": "SCIENTIFIC_DESCRIPTIVE_GENETIC_STATE",
                "semantics": "distributional summary derived only from the raw authorized qfreq trajectory",
            },
        ],
        "integrity_fields": [
            "runtime_version", "frozen_seed", "generation_axis",
            "patch_axis", "locus_axis", "output_artifact_hashes"
        ],
    },
    "SLiM": {
        "execution_interface": {
            "runtime": "GOVERNED_WSL_SLIM_5_2_TSKIT_1_0_3_MSPRIME_1_4_2_PYSLIM_1_1_1",
            "seed_requirement": "EXACT_R452_FROZEN_SEED_INJECTION_REQUIRED",
            "isolated_output_root_required": True,
        },
        "authorized_artifacts": ["SLIM_TREE_SEQUENCE_RAW"],
        "metrics": [
            {
                "metric_id": "SLIM_TREE_SEQUENCE_STRUCTURAL_SUMMARY",
                "role": "SCIENTIFIC_DESCRIPTIVE_GENETIC_STATE",
                "source_fields": ["nodes", "edges", "individuals", "mutations", "sequence_length"],
                "semantics": "native tree-sequence structural state; raw tree sequence remains primary evidence",
            },
            {
                "metric_id": "SLIM_ANCESTRY_GENE_FLOW_SUMMARY",
                "role": "SCIENTIFIC_DESCRIPTIVE_GENETIC_STATE",
                "semantics": "derived from the raw tree sequence under a frozen R4.54 extractor; no result-selected statistic",
            },
        ],
        "integrity_fields": [
            "runtime_version", "frozen_seed", "generation_axis",
            "sequence_length", "raw_tree_sequence_hash"
        ],
    },
}

FORBIDDEN = [
    "LITERAL_CROSS_ENGINE_POPULATION_N_EQUALITY",
    "IMPLICIT_YEAR_GENERATION_EQUIVALENCE",
    "RESULT_SELECTED_METRIC",
    "RESULT_SELECTED_THRESHOLD",
    "MAJORITY_VOTE",
    "ENGINE_OUTPUT_DEFINES_ARCANA_TARGET",
    "DIRECT_EXTERNAL_ENGINE_CANONICAL_WRITE",
    "MADINGLEY_COHORT_AS_ARCANA_SPECIES_IDENTITY",
    "CDMETAPOP_OUTPUT_FILE_COUNT_AS_SCIENTIFIC_BIOLOGICAL_EVIDENCE",
    "R41_MICROBENCHMARK_VALUE_AS_HISTORICAL_SCIENTIFIC_EVIDENCE",
]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha_json(obj: Any) -> str:
    payload = json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verify_r452_plan(plan: dict[str, Any]) -> dict[str, Any]:
    embedded = str(plan.get("plan_sha256", ""))
    bare = copy.deepcopy(plan)
    bare.pop("plan_sha256", None)
    recomputed = _sha_json(bare)
    return {
        "embedded": embedded,
        "recomputed": recomputed,
        "expected": EXPECTED_R452_PLAN_SHA256,
        "pass": embedded == recomputed == EXPECTED_R452_PLAN_SHA256,
    }


def _r41_rows(host: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(x["engine"]): x
        for x in (host.get("benchmarks") or [])
        if isinstance(x, dict) and x.get("engine") in EXPECTED_VERSIONS
    }


def _validate_r41_authority(
    r41_cfg: dict[str, Any],
    host: dict[str, Any],
) -> dict[str, Any]:
    rows = _r41_rows(host)
    by_id = {
        str(x["id"]): x
        for x in r41_cfg.get("microbenchmarks", [])
    }
    checks = {}
    details = {}

    for engine in EXPECTED_VERSIONS:
        bid = R41_BENCHMARK_IDS[engine]
        spec = by_id.get(bid)
        row = rows.get(engine)
        checks[f"{engine}_benchmark_spec_present"] = spec is not None
        checks[f"{engine}_host_row_present"] = row is not None
        checks[f"{engine}_benchmark_id_exact"] = (
            spec is not None and spec.get("engine") == engine
        )
        checks[f"{engine}_runtime_version_exact"] = (
            row is not None
            and str(row.get("confirmed_version")) == EXPECTED_VERSIONS[engine]
        )
        checks[f"{engine}_microbenchmark_pass"] = (
            row is not None
            and row.get("returncode") == 0
            and row.get("status") == "PASS"
        )
        details[engine] = {
            "benchmark_id": bid,
            "purpose": None if spec is None else spec.get("purpose"),
            "scientific_domains":
                [] if spec is None else spec.get("scientific_domains", []),
            "required_metrics":
                [] if spec is None else spec.get("required_metrics", []),
            "confirmed_version":
                None if row is None else row.get("confirmed_version"),
        }

    checks["semantic_no_literal_N_equivalence"] = (
        r41_cfg["semantic_rules"]["population_scale"]["rule"]
        == "NO_LITERAL_CROSS_ENGINE_N_EQUIVALENCE"
    )
    checks["semantic_explicit_time_mapping"] = (
        r41_cfg["semantic_rules"]["time_scale"][
            "historical_window_execution_requires_generation_interval"
        ] is True
    )
    checks["semantic_explicit_space_denominator"] = (
        r41_cfg["semantic_rules"]["space_scale"]["rule"]
        == "EXPLICIT_CELL_AREA_AND_ELIGIBLE_HABITAT_DENOMINATOR_REQUIRED"
    )
    checks["semantic_no_identical_genetic_parameter_assumption"] = (
        r41_cfg["semantic_rules"]["genetic_scale"]["rule"]
        == "PARAMETER_SEMANTICS_ARE_NOT_ASSUMED_IDENTICAL"
    )
    checks["semantic_madingley_no_species_identity"] = (
        r41_cfg["semantic_rules"]["ecosystem_scale"]["rule"]
        == "MADINGLEY_FUNCTIONAL_COHORTS_AND_STOCKS_DO_NOT_DEFINE_ARCANA_SPECIES_IDENTITY"
    )
    checks["r41_single_runs_not_promotional"] = (
        r41_cfg["semantic_rules"]["uncertainty"]["single_run_use"]
        == "SEMANTIC_AND_EXECUTABLE_GATE_ONLY"
    )
    return {
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "details": details,
        "pass": all(checks.values()),
    }


def _freeze_registry(plan: dict[str, Any]) -> dict[str, Any]:
    jobs = []
    for job in plan["jobs"]:
        engine = job["engine"]
        authority = READOUT_AUTHORITY[engine]
        jobs.append({
            "job_id": job["job_id"],
            "engine": engine,
            "window_id": job["window_id"],
            "frozen_seeds": job["frozen_seeds"],
            "r42_job_record_sha256": job["r42_job_record_sha256"],
            "execution_interface": authority["execution_interface"],
            "authorized_artifacts": authority["authorized_artifacts"],
            "authorized_metrics": authority["metrics"],
            "integrity_fields": authority["integrity_fields"],
            "numeric_acceptance_threshold_count": 0,
            "automatic_scientific_pass_fail_count": 0,
            "historical_prediction_claim": False,
            "scientific_execution_authorized": False,
            "r454_seed_and_readout_dry_run_required": True,
        })

    registry = {
        "stage": STAGE,
        "status": "R453_NON_GEONOMICS_EXECUTION_AND_READOUT_AUTHORITY_FROZEN",
        "parent_execution_plan_sha256": plan["plan_sha256"],
        "job_count": len(jobs),
        "engine_count": 5,
        "jobs": jobs,
        "engine_authority": READOUT_AUTHORITY,
        "forbidden_readouts_and_claims": FORBIDDEN,
        "numeric_acceptance_threshold_count": 0,
        "automatic_scientific_pass_fail_count": 0,
        "majority_vote_authorized": False,
        "result_selected_metric_authorized": False,
        "result_selected_threshold_authorized": False,
        "engine_output_defines_arcana_target": False,
        "canonical_rewrite_authorized": False,
        "r41_microbenchmarks_are_historical_scientific_evidence": False,
        "scientific_execution_authorized": False,
        "dry_run_validated": False,
    }
    registry["registry_sha256"] = _sha_json(registry)
    return registry


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    parent = load(root / R452)
    parent_seal = load(root / R452_SEAL)
    plan = load(root / R452_PLAN)
    r41_cfg = load(root / R41_CONFIG)
    r41_host = load(root / R41_HOST)

    pv = _verify_r452_plan(plan)
    r41 = _validate_r41_authority(r41_cfg, r41_host)
    registry = _freeze_registry(plan)

    write(root / OUT / "R4_53_R41_ENGINE_SEMANTIC_AUTHORITY_AUDIT.json", r41)
    write(root / OUT / "R4_53_NON_GEONOMICS_EXECUTION_READOUT_AUTHORITY_REGISTRY.json", registry)

    engine_job_counts = {}
    for engine in EXPECTED_VERSIONS:
        engine_job_counts[engine] = sum(
            j["engine"] == engine for j in registry["jobs"]
        )

    metric_ids = [
        m["metric_id"]
        for authority in READOUT_AUTHORITY.values()
        for m in authority["metrics"]
    ]

    checks = {
        "parent_r452_complete_34_34":
            parent.get("status") == PARENT_COMPLETE
            and parent.get("checks_passed") == 34
            and parent.get("checks_failed") == 0,
        "parent_r452_sealed_21_21":
            parent_seal.get("status") == PARENT_SEALED
            and parent_seal.get("verdict") == "SEALED"
            and parent_seal.get("checks_passed") == 21
            and parent_seal.get("checks_failed") == 0,
        "parent_next_action_r453":
            parent.get("next_action") == PARENT_NEXT
            and parent_seal.get("next_action") == PARENT_NEXT,
        "policy_frozen":
            cfg.get("policy")
            == "R453_FREEZE_ENGINE_SPECIFIC_EXECUTION_AND_READOUT_AUTHORITY_BEFORE_80_STREAM_RUN",
        "r452_plan_hash_exact":
            pv.get("pass") is True,
        "r452_exact_20_jobs":
            len(plan["jobs"]) == 20
            and parent.get("execution_required_job_count") == 20,
        "r452_exact_80_streams":
            parent.get("planned_scientific_stream_count") == 80,
        "r41_semantic_authority_valid":
            r41.get("pass") is True,
        "five_engine_authorities":
            set(READOUT_AUTHORITY) == set(EXPECTED_VERSIONS),
        "exact_20_registry_jobs":
            registry.get("job_count") == 20,
        "engine_job_distribution_preserved":
            engine_job_counts == {
                "Madingley": 4,
                "RangeShifter": 5,
                "CDMetaPOP": 5,
                "NEMO": 3,
                "SLiM": 3,
            },
        "all_jobs_preserve_four_frozen_seeds":
            all(len(j["frozen_seeds"]) == 4 for j in registry["jobs"]),
        "exact_ten_unique_metric_ids":
            len(metric_ids) == 10 and len(set(metric_ids)) == 10,
        "madingley_two_descriptive_metrics":
            len(READOUT_AUTHORITY["Madingley"]["metrics"]) == 2,
        "rangeshifter_two_descriptive_metrics":
            len(READOUT_AUTHORITY["RangeShifter"]["metrics"]) == 2,
        "cdmetapop_two_descriptive_metrics":
            len(READOUT_AUTHORITY["CDMetaPOP"]["metrics"]) == 2,
        "nemo_two_descriptive_metrics":
            len(READOUT_AUTHORITY["NEMO"]["metrics"]) == 2,
        "slim_two_descriptive_metrics":
            len(READOUT_AUTHORITY["SLiM"]["metrics"]) == 2,
        "cdmetapop_csv_count_forbidden_as_scientific_metric":
            "CDMETAPOP_OUTPUT_FILE_COUNT_AS_SCIENTIFIC_BIOLOGICAL_EVIDENCE"
            in FORBIDDEN,
        "madingley_species_identity_claim_forbidden":
            "MADINGLEY_COHORT_AS_ARCANA_SPECIES_IDENTITY" in FORBIDDEN,
        "r41_microbenchmark_not_historical_evidence":
            registry["r41_microbenchmarks_are_historical_scientific_evidence"]
            is False,
        "zero_numeric_thresholds":
            registry["numeric_acceptance_threshold_count"] == 0,
        "zero_automatic_pass_fail":
            registry["automatic_scientific_pass_fail_count"] == 0,
        "no_majority_vote":
            registry["majority_vote_authorized"] is False,
        "no_result_selected_metric":
            registry["result_selected_metric_authorized"] is False,
        "no_result_selected_threshold":
            registry["result_selected_threshold_authorized"] is False,
        "engine_cannot_define_arcana_target":
            registry["engine_output_defines_arcana_target"] is False,
        "canonical_rewrite_forbidden":
            registry["canonical_rewrite_authorized"] is False,
        "all_jobs_require_r454_dry_run":
            all(j["r454_seed_and_readout_dry_run_required"] is True
                for j in registry["jobs"]),
        "scientific_execution_not_authorized":
            registry["scientific_execution_authorized"] is False,
        "dry_run_not_yet_validated":
            registry["dry_run_validated"] is False,
        "no_scientific_execution_in_r453":
            cfg.get("scientific_engine_execution_performed") is False,
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

    out = {
        "stage": STAGE,
        "status": COMPLETE if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "parent_execution_plan_sha256": plan.get("plan_sha256"),
        "readout_authority_registry_sha256": registry.get("registry_sha256"),
        "engine_count": 5,
        "job_count": 20,
        "planned_scientific_stream_count": 80,
        "authorized_metric_definition_count": 10,
        "numeric_acceptance_threshold_count": 0,
        "scientific_execution_authorized": False,
        "exact_seed_injection_dry_run_validated": False,
        "readout_extraction_dry_run_validated": False,
        "scientific_engine_execution_performed": False,
        "multi_engine_full_revalidation_closed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action":
            NEXT if ok else "REPAIR_R453_EXECUTION_OR_READOUT_AUTHORITY",
    }
    write(root / OUT / "R4_53_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    a = load(root / OUT / "R4_53_INTEGRATED_AUDIT.json")
    r = load(
        root / OUT /
        "R4_53_NON_GEONOMICS_EXECUTION_READOUT_AUTHORITY_REGISTRY.json"
    )

    checks = {
        "r453_complete":
            a.get("status") == COMPLETE and a.get("checks_failed") == 0,
        "exact_five_engines":
            a.get("engine_count") == 5,
        "exact_20_jobs":
            a.get("job_count") == 20,
        "exact_80_planned_streams":
            a.get("planned_scientific_stream_count") == 80,
        "exact_10_metric_definitions":
            a.get("authorized_metric_definition_count") == 10,
        "registry_hash_present":
            len(str(a.get("readout_authority_registry_sha256", ""))) == 64,
        "zero_numeric_thresholds":
            a.get("numeric_acceptance_threshold_count") == 0,
        "no_majority_vote":
            r.get("majority_vote_authorized") is False,
        "no_result_selected_metric":
            r.get("result_selected_metric_authorized") is False,
        "no_result_selected_threshold":
            r.get("result_selected_threshold_authorized") is False,
        "r41_not_historical_evidence":
            r.get("r41_microbenchmarks_are_historical_scientific_evidence")
            is False,
        "scientific_execution_not_authorized":
            a.get("scientific_execution_authorized") is False,
        "seed_dry_run_pending":
            a.get("exact_seed_injection_dry_run_validated") is False,
        "readout_dry_run_pending":
            a.get("readout_extraction_dry_run_validated") is False,
        "no_scientific_execution":
            a.get("scientific_engine_execution_performed") is False,
        "multi_engine_not_closed":
            a.get("multi_engine_full_revalidation_closed") is False,
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
        "next_r454":
            a.get("next_action") == NEXT,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "audit":
            "FINAL_NON_GEONOMICS_SCIENTIFIC_EXECUTION_INTERFACE_"
            "AND_READOUT_AUTHORITY_PREFLIGHT",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "engine_count": 5,
            "job_count": 20,
            "planned_scientific_stream_count": 80,
            "authorized_metric_definition_count": 10,
            "readout_authority_registry_sha256":
                a.get("readout_authority_registry_sha256"),
            "scientific_execution_authorized": False,
            "exact_seed_injection_dry_run_validated": False,
            "readout_extraction_dry_run_validated": False,
            "scientific_engine_execution_performed": False,
            "multi_engine_full_revalidation_closed": False,
            "canonical_state_changed": False,
            "deep_biological_coupling": False,
            "next_action": NEXT,
        },
        "next_action": NEXT,
    }
    write(root / SEAL, out)
    return out
