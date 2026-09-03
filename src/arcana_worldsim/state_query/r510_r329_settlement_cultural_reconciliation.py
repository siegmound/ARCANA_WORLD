from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json
import numpy as np

STAGE = "v0.6D1-R5.10"
OUT_REL = Path("outputs/v0_6D1_R5_10")
TARGET_COHORT = ("RPT_010_D02", "RPT_009_D02")
EXPECTED_PARENT_MEMBER_INDICES = tuple(range(0, 96, 3))
FINAL_STATUS = "PASS_R510_R59_TO_R329_POPULATION_SETTLEMENT_CULTURAL_PRECONDITION_RECONCILIATION_CANDIDATE"

# Immutable R3.29 sealed authority hashes from the historical WorldSim branch.
EXPECTED_R329_FINAL_SEAL_AUDIT_SHA256 = "79f507601eb9feba69c305a3407fafe5f96d8069d1498a68c6824374d32ba196"
EXPECTED_R329_FINAL_SEAL_MANIFEST_SHA256 = "6e5d6c710f0ea1e089e931a8ba8ac7ed195478d2b9a88c4602f429530b6cda59"
EXPECTED_R329_OUTPUT_MANIFEST_SHA256 = "560dfc91224ee8d96e44e9e2484f6fd47e0846ccb5f289f07b89bf7ce2bb7ce2"
EXPECTED_R329_REPLAY_SHA256 = "bbdde55933575153a88e570e3dc5709b38a09f696ffc2777c28299fc3cd3112a"
EXPECTED_R329_AUTHORITY_SHA256 = "dd6e5384168ca07cae32cc8669559384f906104fd0c5662f83205274ca921452"
EXPECTED_R329_CHECKPOINT_SHA256 = "3da6f2225eda800608995e74373c955f91504b9bef6845db4234845d471165e2"
EXPECTED_R329_OUTCOMES_SHA256 = "d723cce645585fb9edacc1900d6219d477328de962fa737ee21c8ee2bec84320"
EXPECTED_R329_AUDIT_SHA256 = "eb040b5bc215dd75b08721bf41809c0e8ad37bbe42060f1b58dddf7d2b7d9ed7"
EXPECTED_R329_SOURCE_MANIFEST_SHA256 = "b5e9f566c4d5dcd7d1b9bc27deec683f825a635f0d1798183c5cce684f970898"
EXPECTED_R329_SOURCE_MODULE_SHA256 = "5b2c21bb22c3582167e29f10d1002a7892f58d6b2a3cb554bc42ea9231442268"
EXPECTED_R329_CONFIG_SHA256 = "b3f171860fb885a20c079b522a1e2bbaf75bdea9561b804f9da78ee3f5e9391f"
EXPECTED_R329_CONTRACT_SHA256 = "c278b28d5773eb41dfeb4653f798a2336f9a05d7664c18ad5b1c9c9350f137f4"
EXPECTED_R328_REPLAY_SHA256 = "16a48a3ec8736b4b6297186222d7274a5ce376085f27bfa9108d7ba5cd0ec99a"

R59_OUT = Path("outputs/v0_6D1_R5_9")
R59_MANIFEST = R59_OUT / "R5_9_OUTPUT_MANIFEST.json"
R59_AUDIT = R59_OUT / "R5_9_INTEGRATED_RECONCILIATION.json"
R59_HANDOFF = R59_OUT / "R5_9_0KA_RECONCILED_HANDOFF.json"
R59_BINDING = R59_OUT / "R5_9_PARENT_AUTHORITY_BINDING.json"
R328_REPLAY = Path("outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz")
R328_AUTHORITY = Path("outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_REPLAY_AUTHORITY.json")
R329_OUT = Path("outputs/v0_6D1_R3_29")
R329_SEAL_OUT = Path("outputs/v0_6D1_R3_29_SEAL")
R329_REPLAY = R329_OUT / "R3_29_COMMUNITY_NETWORK_REPLAY.npz"
R329_AUTHORITY = R329_OUT / "R3_29_COMMUNITY_PRECONDITION_AUTHORITY.json"
R329_CHECKPOINT = R329_OUT / "R3_29_COMMUNITY_PRECONDITION_CHECKPOINT.json"
R329_OUTCOMES = R329_OUT / "R3_29_LINEAGE_COMMUNITY_OUTCOMES.json"
R329_SENSITIVITY = R329_OUT / "R3_29_SENSITIVITY_AND_ROBUSTNESS.json"
R329_AUDIT = R329_OUT / "R3_29_INTEGRATED_AUDIT.json"
R329_OUTPUT_MANIFEST = R329_OUT / "R3_29_OUTPUT_MANIFEST.json"
R329_SEAL_AUDIT = R329_SEAL_OUT / "R3_29_FINAL_SEAL_AUDIT.json"
R329_SEAL_MANIFEST = R329_SEAL_OUT / "R3_29_FINAL_SEAL_MANIFEST.json"
R329_SOURCE_MANIFEST = Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_29.json")
R329_SOURCE_MODULE = Path("src/arcana_worldsim/scientific_engines/r329_population_settlement_culture.py")
R329_CONFIG = Path("configs/world1_r329_population_settlement_cultural_preconditions_v0_6D1_R3_29.json")
R329_CONTRACT = Path("R3_29_POPULATION_SETTLEMENT_CULTURAL_PRECONDITIONS_CONTRACT.md")

EXPECTED_R329_TIME_NAMES = (
    "population_support_norm", "residential_mobility_index", "aggregation_potential",
    "network_connectivity", "cultural_transmission_support", "cumulative_culture_precondition_stock",
    "settlement_persistence_potential", "resource_stress_proxy", "interlineage_exchange_opportunity",
    "cha2_community_disruption",
)
EXPECTED_R329_ANCHOR_NAMES = (
    "population_proxy", "grid_row", "grid_col", "community_viability", "mobility_pressure",
    "settlement_persistence_potential", "network_access_proxy",
)
EXPECTED_R329_PRIOR_NAMES = ("social_learning", "coordination", "mobility", "flexibility", "development", "cognition")


class R510Error(RuntimeError):
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


def _manifest_integrity(base: Path, manifest_path: Path) -> tuple[bool, dict[str, Any]]:
    if not manifest_path.is_file():
        return False, {"error": "missing_manifest", "path": str(manifest_path)}
    try:
        m = load_json(manifest_path)
        files = dict(m.get("files") or {})
        mismatches: list[str] = []
        ok = bool(files)
        for name, meta in files.items():
            p = base / name
            same = p.is_file() and p.stat().st_size == int(meta.get("bytes", -1)) and sha256_file(p) == meta.get("sha256")
            if not same:
                mismatches.append(name)
                ok = False
        return bool(ok), {"file_count": len(files), "mismatches": mismatches}
    except Exception as exc:
        return False, {"error": repr(exc)}


def validate_parent_authority(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    checks: dict[str, bool] = {}
    required = [
        R59_MANIFEST, R59_AUDIT, R59_HANDOFF, R59_BINDING, R328_REPLAY, R328_AUTHORITY,
        R329_REPLAY, R329_AUTHORITY, R329_CHECKPOINT, R329_OUTCOMES, R329_SENSITIVITY,
        R329_AUDIT, R329_OUTPUT_MANIFEST, R329_SEAL_AUDIT, R329_SEAL_MANIFEST,
        R329_SOURCE_MANIFEST, R329_SOURCE_MODULE, R329_CONFIG, R329_CONTRACT,
    ]
    for rel in required:
        checks[f"present::{rel.as_posix()}"] = (root / rel).is_file()

    try:
        mi59, _ = _manifest_integrity(root / R59_OUT, root / R59_MANIFEST)
        a59 = load_json(root / R59_AUDIT)
        h59 = load_json(root / R59_HANDOFF)
        b59 = load_json(root / R59_BINDING)
        checks["r59_output_manifest_integrity"] = mi59
        checks["r59_candidate_semantics"] = (
            a59.get("status") == "PASS_R59_R58_TO_R328_200KA_0KA_HIGH_RESOLUTION_RECONCILIATION_CANDIDATE"
            and a59.get("scientific_candidate_eligible") is True
            and int(a59.get("checks_passed", -1)) == 30
            and int(a59.get("checks_total", -1)) == 30
            and not (a59.get("failed") or [])
        )
        checks["r59_handoff_exact"] = (
            h59.get("status") == "R59_RECONCILED_0KA_HANDOFF"
            and float(h59.get("age_ka", -1)) == 0.0
            and tuple(h59.get("candidate_cohort") or []) == TARGET_COHORT
            and int(h59.get("candidate_count", -1)) == 2
            and h59.get("unique_human_identity") is None
            and h59.get("unique_human_identity_materialized") is False
            and h59.get("downstream_r329_reconciliation_required") is True
            and h59.get("downstream_r329_auto_authorized") is False
            and h59.get("ready_for_post_r328_population_settlement_reconciliation") is True
        )
        checks["r59_preserves_r328_diagnostic_admixture_semantics"] = (
            h59.get("admixture_semantics") == "R328_ADMIXTURE_OPPORTUNITY_PROXY_ONLY_NOT_REALIZED_HISTORICAL_ADMIXTURE_OR_TRUE_LOCAL_ANCESTRY"
        )
        checks["r59_binds_live_r328_replay"] = (
            (root / R328_REPLAY).is_file()
            and sha256_file(root / R328_REPLAY) == EXPECTED_R328_REPLAY_SHA256
            and b59.get("r328_replay_sha256") == EXPECTED_R328_REPLAY_SHA256
            and h59.get("source_r328_replay_sha256") == EXPECTED_R328_REPLAY_SHA256
        )
    except Exception:
        for k in ["r59_output_manifest_integrity", "r59_candidate_semantics", "r59_handoff_exact", "r59_preserves_r328_diagnostic_admixture_semantics", "r59_binds_live_r328_replay"]:
            checks[k] = False

    try:
        seal = load_json(root / R329_SEAL_AUDIT)
        sm = load_json(root / R329_SEAL_MANIFEST)
        ia = load_json(root / R329_AUDIT)
        auth = load_json(root / R329_AUTHORITY)
        cp = load_json(root / R329_CHECKPOINT)
        checks["r329_final_seal_exact_hash"] = sha256_file(root / R329_SEAL_AUDIT) == EXPECTED_R329_FINAL_SEAL_AUDIT_SHA256
        checks["r329_final_seal_manifest_exact_hash"] = sha256_file(root / R329_SEAL_MANIFEST) == EXPECTED_R329_FINAL_SEAL_MANIFEST_SHA256
        checks["r329_final_seal_manifest_binds_audit"] = (((sm.get("files") or {}).get("R3_29_FINAL_SEAL_AUDIT.json") or {}).get("sha256") == EXPECTED_R329_FINAL_SEAL_AUDIT_SHA256)
        checks["r329_final_seal_semantics"] = (
            seal.get("verdict") == "SEALED"
            and seal.get("status") == "PASS_R329_POPULATION_MOBILITY_SETTLEMENT_CULTURAL_TRANSMISSION_PRECONDITIONS_AND_CHA2_COMMUNITY_EXPOSURE_SEALED"
            and int(seal.get("checks_passed", -1)) == 37
            and int(seal.get("checks_failed", -1)) == 0
        )
        checks["r329_output_manifest_exact_hash"] = sha256_file(root / R329_OUTPUT_MANIFEST) == EXPECTED_R329_OUTPUT_MANIFEST_SHA256
        mi29, _ = _manifest_integrity(root / R329_OUT, root / R329_OUTPUT_MANIFEST)
        checks["r329_output_manifest_integrity"] = mi29
        checks["r329_replay_exact_hash"] = sha256_file(root / R329_REPLAY) == EXPECTED_R329_REPLAY_SHA256
        checks["r329_authority_exact_hash"] = sha256_file(root / R329_AUTHORITY) == EXPECTED_R329_AUTHORITY_SHA256
        checks["r329_checkpoint_exact_hash"] = sha256_file(root / R329_CHECKPOINT) == EXPECTED_R329_CHECKPOINT_SHA256
        checks["r329_outcomes_exact_hash"] = sha256_file(root / R329_OUTCOMES) == EXPECTED_R329_OUTCOMES_SHA256
        checks["r329_integrated_audit_exact_hash"] = sha256_file(root / R329_AUDIT) == EXPECTED_R329_AUDIT_SHA256
        checks["r329_integrated_audit_semantics"] = (
            ia.get("status") == "PASS_R329_POPULATION_MOBILITY_SETTLEMENT_AND_CULTURAL_PRECONDITIONS_CANDIDATE"
            and int(ia.get("checks_passed", -1)) == 24 and int(ia.get("checks_total", -1)) == 24
            and int(ia.get("checks_failed", -1)) == 0
        )
        checks["r329_authority_semantics"] = (
            tuple(auth.get("candidate_cohort") or []) == TARGET_COHORT
            and auth.get("parent") == "PASS_R328_HIGH_RESOLUTION_200KA_TO_0_POPULATION_STRUCTURE_MIGRATION_ADMIXTURE_CHA2_EXPOSURE_AND_HUMAN_0KA_CHECKPOINT_SEALED"
            and auth.get("population_semantics") == "R328_POPULATION_PROXY_NOT_LITERAL_CENSUS"
            and auth.get("settlement_semantics") == "PERSISTENCE_POTENTIAL_NOT_ARCHAEOLOGICALLY_OBSERVED_SETTLEMENT"
            and auth.get("culture_semantics") == "TRANSMISSION_AND_CUMULATION_PRECONDITIONS_NOT_LANGUAGE_RELIGION_TECHNOLOGY_OR_CULTURAL_IDENTITY"
            and auth.get("spatial_semantics") == "R328_EXPLICIT_DEME_SNAPSHOT_ANCHORS_ONLY_NO_INVENTED_CONTINUOUS_DEME_PATHS"
            and auth.get("deep_biological_coupling") is False
            and auth.get("human_similarity_target") is False
            and auth.get("unique_human_identity_materialized") is False
        )
        checks["r329_checkpoint_semantics"] = (
            float(cp.get("age_ka", -1)) == 0.0
            and tuple(cp.get("candidate_cohort") or []) == TARGET_COHORT
            and int(cp.get("candidate_count", -1)) == 2
            and cp.get("unique_human_identity") is None
            and cp.get("unique_human_identity_materialized") is False
            and all(cp.get(k) is False for k in ("language_materialized", "religion_materialized", "agriculture_materialized", "city_state_materialized"))
        )
        checks["r329_source_manifest_exact_hash"] = sha256_file(root / R329_SOURCE_MANIFEST) == EXPECTED_R329_SOURCE_MANIFEST_SHA256
        checks["r329_source_module_exact_hash"] = sha256_file(root / R329_SOURCE_MODULE) == EXPECTED_R329_SOURCE_MODULE_SHA256
        checks["r329_config_exact_hash"] = sha256_file(root / R329_CONFIG) == EXPECTED_R329_CONFIG_SHA256
        checks["r329_contract_exact_hash"] = sha256_file(root / R329_CONTRACT) == EXPECTED_R329_CONTRACT_SHA256
    except Exception:
        for k in [
            "r329_final_seal_exact_hash", "r329_final_seal_manifest_exact_hash", "r329_final_seal_manifest_binds_audit",
            "r329_final_seal_semantics", "r329_output_manifest_exact_hash", "r329_output_manifest_integrity",
            "r329_replay_exact_hash", "r329_authority_exact_hash", "r329_checkpoint_exact_hash", "r329_outcomes_exact_hash",
            "r329_integrated_audit_exact_hash", "r329_integrated_audit_semantics", "r329_authority_semantics",
            "r329_checkpoint_semantics", "r329_source_manifest_exact_hash", "r329_source_module_exact_hash",
            "r329_config_exact_hash", "r329_contract_exact_hash",
        ]:
            checks[k] = False

    failed = [k for k, v in checks.items() if not bool(v)]
    return {
        "stage": STAGE,
        "status": "PASS_R510_IMMUTABLE_R59_R329_PARENT_AUTHORITY" if not failed else "BLOCKED_R510_PARENT_AUTHORITY",
        "checks_passed": sum(bool(v) for v in checks.values()),
        "checks_total": len(checks),
        "failed": failed,
        "checks": checks,
    }


def reconcile(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    out = root / OUT_REL
    cfg = load_json(root / "configs/world1_r510_r329_settlement_cultural_reconciliation_v0_6D1_R5_10.json")
    parent = validate_parent_authority(root)

    h59 = load_json(root / R59_HANDOFF)
    a328 = load_json(root / R328_AUTHORITY)
    auth29 = load_json(root / R329_AUTHORITY)
    cp29 = load_json(root / R329_CHECKPOINT)
    outcomes = load_json(root / R329_OUTCOMES)
    sens = load_json(root / R329_SENSITIVITY)
    cfg29 = load_json(root / R329_CONFIG)
    src29 = (root / R329_SOURCE_MODULE).read_text(encoding="utf-8")

    with np.load(root / R328_REPLAY, allow_pickle=False) as z28, np.load(root / R329_REPLAY, allow_pickle=False) as z29:
        ids28 = tuple(map(str, z28["candidate_ids"].tolist()))
        ids29 = tuple(map(str, z29["candidate_ids"].tolist()))
        p28 = tuple(map(int, z28["parent_member_indices"].tolist()))
        p29 = tuple(map(int, z29["parent_member_indices"].tolist()))
        ages28 = np.asarray(z28["age_ka"], dtype=float)
        ages29 = np.asarray(z29["age_ka"], dtype=float)
        expected_ages29 = ages28[ages28 <= float(cfg29["start_age_ka"]) + 1e-12]
        time_names = tuple(map(str, z29["community_variable_names"].tolist()))
        pri_names = tuple(map(str, z29["functional_prior_names"].tolist()))
        X = np.asarray(z29["community_summary"], dtype=float)
        P = np.asarray(z29["functional_priors"], dtype=float)
        anchor_age29 = np.asarray(z29["anchor_age_ka"], dtype=float)
        expected_anchor_age = np.asarray(z28["snapshot_age_ka"], dtype=float)
        smask = expected_anchor_age <= float(cfg29["start_age_ka"]) + 1e-12
        expected_anchor_age = expected_anchor_age[smask]
        anchor_names = tuple(map(str, z29["community_anchor_variable_names"].tolist()))
        A29 = np.asarray(z29["community_anchor_state"], dtype=float)
        active29 = np.asarray(z29["community_anchor_active"], dtype=np.uint8)
        D28 = np.asarray(z28["snapshot_deme_state"][:, :, smask, :, :], dtype=float)
        active28 = np.asarray(z28["snapshot_active"][:, :, smask, :], dtype=np.uint8)
        anchor_parent_err = float(np.max(np.abs(A29[..., :3] - D28[..., :3])))
        active_exact = bool(np.array_equal(active29, active28))
        summary_names28 = tuple(map(str, z28["species_summary_variable_names"].tolist()))

    by_id = {str(x.get("species_id")): x for x in outcomes.get("candidates") or []}
    both_baseline = all(by_id.get(sid, {}).get("baseline_qualified") is True for sid in TARGET_COHORT)
    both_precondition = tuple(outcomes.get("community_precondition_cohort") or []) == TARGET_COHORT
    robust = tuple(outcomes.get("robust_priority_cohort") or [])
    borderline = tuple(outcomes.get("borderline_retained_cohort") or [])

    checks: dict[str, bool] = {}
    checks["parent_authority_pass"] = not parent.get("failed")
    checks["config_target_cohort_exact"] = tuple(cfg.get("target_cohort") or []) == TARGET_COHORT
    checks["r59_0ka_handoff_cohort_exact"] = tuple(h59.get("candidate_cohort") or []) == TARGET_COHORT and int(h59.get("candidate_count", -1)) == 2
    checks["r329_candidate_order_exact"] = ids29 == TARGET_COHORT == ids28
    checks["r329_parent_member_indices_exact"] = p29 == EXPECTED_PARENT_MEMBER_INDICES == p28
    checks["r329_age_axis_exact_r328_subset_50ka_to_0"] = np.array_equal(ages29, expected_ages29) and len(ages29) == 175 and float(ages29[0]) == 50.0 and float(ages29[-1]) == 0.0
    checks["r329_time_variable_names_exact"] = time_names == EXPECTED_R329_TIME_NAMES
    checks["r329_community_geometry_exact"] = X.shape == (32, 2, 175, 10)
    checks["r329_functional_prior_geometry_exact"] = pri_names == EXPECTED_R329_PRIOR_NAMES and P.shape == (32, 2, 6) and np.isfinite(P).all()
    checks["r329_anchor_age_axis_exact_r328_snapshots"] = np.array_equal(anchor_age29, expected_anchor_age) and len(anchor_age29) == 11
    checks["r329_anchor_variable_names_exact"] = anchor_names == EXPECTED_R329_ANCHOR_NAMES
    checks["r329_anchor_geometry_exact"] = A29.shape == (32, 2, 11, 6, 7) and active29.shape == (32, 2, 11, 6)
    checks["r329_anchor_parent_population_coordinates_exact"] = anchor_parent_err <= 1e-5
    checks["r329_anchor_activity_exact"] = active_exact
    checks["r329_uses_r328_admixture_proxy_only_as_exchange_opportunity_modifier"] = (
        len(summary_names28) > 5 and summary_names28[5] == "admixture_fraction_proxy"
        and "admix=np.clip(S[...,5],0,1)" in src29
        and "exch=np.clip(contact[:,t,None]" in src29
        and "interlineage_exchange_opportunity" in time_names
    )
    checks["r329_exchange_remains_opportunity_not_realized_gene_flow"] = (
        a328.get("contact_semantics") == "SYMMETRIC_ADMIXTURE_OPPORTUNITY_DIAGNOSTIC_NO_FORCED_REPLACEMENT"
        and auth29.get("state_semantics") == "DIMENSIONLESS_COMMUNITY_AND_CULTURAL_PRECONDITION_INDICES_CONDITIONED_ON_R328_POPULATION_REPLAY"
        and h59.get("admixture_semantics") == "R328_ADMIXTURE_OPPORTUNITY_PROXY_ONLY_NOT_REALIZED_HISTORICAL_ADMIXTURE_OR_TRUE_LOCAL_ANCESTRY"
    )
    checks["r329_checkpoint_matches_r59_0ka_cohort"] = tuple(cp29.get("candidate_cohort") or []) == tuple(h59.get("candidate_cohort") or []) == TARGET_COHORT
    checks["both_lineages_baseline_capable_and_retained"] = both_baseline and both_precondition
    checks["robust_priority_subset_exact_but_diagnostic_only"] = robust == ("RPT_010_D02",) and borderline == ("RPT_009_D02",) and cp29.get("candidate_count") == 2
    checks["sensitivity_priority_not_identity_gate"] = outcomes.get("interpretation") == "PRECONDITIONS_ONLY;_BASELINE_CAPABLE_LINEAGES_RETAINED;_SENSITIVITY_USED_AS_PRIORITY_NOT_EXTINCTION_OR_IDENTITY_GATE"
    checks["sensitivity_variant_count_exact"] = int(sens.get("variant_count", -1)) == 11 and len(sens.get("variants") or []) == 11
    checks["legacy_calibration_declared_diagnostic_not_historical_truth"] = (
        float(cfg29.get("culture_stock_rate_per_kyr", -1)) == 0.09
        and set((cfg29.get("qualification") or {}).keys()) == {"network_min", "transmission_min", "culture_stock_min", "settlement_min", "cha2_stock_retention_min", "sensitivity_frequency_min"}
        and cfg.get("r329_legacy_numeric_parameters_historical_truth") is False
    )
    checks["no_culture_identity_materialized"] = all(cp29.get(k) is False for k in ("language_materialized", "religion_materialized", "agriculture_materialized", "city_state_materialized"))
    checks["no_unique_human_identity_materialized"] = cp29.get("unique_human_identity_materialized") is False and cp29.get("unique_human_identity") is None
    checks["population_proxy_not_literal_census"] = auth29.get("population_semantics") == "R328_POPULATION_PROXY_NOT_LITERAL_CENSUS"
    checks["settlement_is_potential_not_archaeological_observation"] = auth29.get("settlement_semantics") == "PERSISTENCE_POTENTIAL_NOT_ARCHAEOLOGICALLY_OBSERVED_SETTLEMENT"
    checks["no_new_external_engine_execution"] = cfg.get("external_engine_execution") is False
    checks["r329_not_rerun_or_mutated"] = cfg.get("rerun_r329") is False and sha256_file(root / R329_REPLAY) == EXPECTED_R329_REPLAY_SHA256
    checks["numeric_historical_truth_not_claimed"] = cfg.get("numeric_historical_truth_claimed") is False
    checks["canonical_state_unchanged"] = cfg.get("canonical_state_changed") is False
    checks["derived_refinement_not_promoted"] = cfg.get("derived_refinement_promoted_to_canon") is False
    checks["deep_biological_coupling_off"] = cfg.get("deep_biological_coupling") is False and auth29.get("deep_biological_coupling") is False
    checks["downstream_r330_not_auto_authorized"] = cfg.get("auto_authorize_downstream_r330") is False

    checks = {k: bool(v) for k, v in checks.items()}
    failed = [k for k, v in checks.items() if not v]
    out.mkdir(parents=True, exist_ok=True)

    utility = {
        "stage": STAGE,
        "status": "PASS_R510_RUNTIME_UTILITY_REVIEW_NO_NEW_ENGINE_REQUIRED",
        "new_external_engine_execution_performed": False,
        "decision": "NO_NEW_ENGINE_REQUIRED_FOR_R329_RECONCILIATION",
        "reason": "R3.29 is already SEALED and derives its community/cultural-precondition diagnostics directly from the sealed R3.28 replay plus sealed R3.23 functional priors. R5.10 verifies continuity and semantics only.",
        "considered": {
            "SLiM_5_2": "NOT_RERUN_NO_NEW_ANCESTRY_QUESTION",
            "NEMO_2_4_2": "NOT_RERUN_NO_NEW_GENE_FLOW_ROBUSTNESS_QUESTION",
            "CDMetaPOP_3_08": "NOT_RERUN_NO_NEW_DEMOGRAPHIC_PERSISTENCE_QUESTION",
            "RangeShiftR_3_0_1": "NOT_RERUN_NO_NEW_CORRIDOR_QUESTION",
            "agent_based_runtime": "NOT_INTRODUCED_R329_IS_RECONCILED_AS_SEALED_DIAGNOSTIC_PRECONDITION_LAYER",
        },
    }
    write_json(out / "R5_10_RUNTIME_UTILITY_REVIEW.json", utility)

    binding = {
        "stage": STAGE,
        "status": "R510_PARENT_AUTHORITY_BINDING",
        "r59_output_manifest_sha256": sha256_file(root / R59_MANIFEST),
        "r59_handoff_sha256": sha256_file(root / R59_HANDOFF),
        "r328_replay_sha256": sha256_file(root / R328_REPLAY),
        "r329_final_seal_audit_sha256": sha256_file(root / R329_SEAL_AUDIT),
        "r329_output_manifest_sha256": sha256_file(root / R329_OUTPUT_MANIFEST),
        "r329_replay_sha256": sha256_file(root / R329_REPLAY),
        "r329_checkpoint_sha256": sha256_file(root / R329_CHECKPOINT),
        "binding_semantics": "R59_RECONCILED_0KA_HANDOFF_PLUS_IMMUTABLE_SEALED_R329_COMMUNITY_PRECONDITION_LAYER",
    }
    write_json(out / "R5_10_PARENT_AUTHORITY_BINDING.json", binding)

    alignment = {
        "stage": STAGE,
        "status": "PASS_R510_R329_PIPELINE_ALIGNMENT" if not failed else "BLOCKED_R510_R329_PIPELINE_ALIGNMENT",
        "candidate_cohort": list(TARGET_COHORT),
        "parent_member_indices": list(p29),
        "r329_time_state_count": int(len(ages29)),
        "r329_time_window_ka": [float(ages29[0]), float(ages29[-1])],
        "r329_anchor_state_count": int(len(anchor_age29)),
        "r329_anchor_ages_ka": anchor_age29.tolist(),
        "anchor_parent_population_coordinate_max_abs_error": anchor_parent_err,
        "anchor_activity_exact": active_exact,
        "semantics": "R329_REUSES_THE_EXACT_R328_50KA_TO_0_TIME_SUBSET_AND_EXPLICIT_SPATIAL_SNAPSHOT_ANCHORS; NO_CONTINUOUS_SETTLEMENT_PATH_IS_INVENTED",
    }
    write_json(out / "R5_10_R329_PIPELINE_ALIGNMENT.json", alignment)

    legacy = {
        "stage": STAGE,
        "status": "R510_R329_LEGACY_DIAGNOSTIC_CLASSIFICATION",
        "culture_stock_rate_per_kyr": cfg29["culture_stock_rate_per_kyr"],
        "qualification_thresholds": cfg29["qualification"],
        "sensitivity_multipliers": cfg29["sensitivity_multipliers"],
        "classification": "SEALED_LEGACY_DIAGNOSTIC_HYPERPARAMETERS_NOT_OBSERVED_HISTORICAL_VALUES_AND_NOT_CANONICAL_NUMERIC_TRUTH",
        "robust_priority_cohort": list(robust),
        "borderline_retained_cohort": list(borderline),
        "priority_semantics": "ROBUSTNESS_PRIORITY_ONLY_NOT_EXTINCTION_IDENTITY_OR_HUMAN_LINEAGE_SELECTION_GATE",
        "admixture_proxy_semantics": "R328_ADMIXTURE_FRACTION_PROXY_MAY_MODULATE_R329_INTERLINEAGE_EXCHANGE_OPPORTUNITY_ONLY; IT_IS_NOT_TRUE_LOCAL_ANCESTRY_OR_REALIZED_GENE_FLOW",
        "cultural_semantics": "CULTURAL_TRANSMISSION_AND_CUMULATION_PRECONDITIONS_ONLY; NO_LANGUAGE_RELIGION_TECHNOLOGY_ETHNICITY_OR_CULTURAL_IDENTITY",
    }
    write_json(out / "R5_10_R329_LEGACY_DIAGNOSTIC_CLASSIFICATION.json", legacy)

    handoff = {
        "stage": STAGE,
        "status": "R510_RECONCILED_COMMUNITY_PRECONDITION_HANDOFF_0KA",
        "age_ka": 0.0,
        "candidate_cohort": list(cp29.get("candidate_cohort") or []),
        "candidate_count": int(cp29.get("candidate_count", -1)),
        "community_precondition_cohort": list(outcomes.get("community_precondition_cohort") or []),
        "robust_priority_cohort": list(robust),
        "borderline_retained_cohort": list(borderline),
        "unique_human_identity": None,
        "unique_human_identity_materialized": False,
        "language_materialized": False,
        "religion_materialized": False,
        "agriculture_materialized": False,
        "city_state_materialized": False,
        "absolute_census_materialized": False,
        "settlement_semantics": auth29.get("settlement_semantics"),
        "culture_semantics": auth29.get("culture_semantics"),
        "gene_flow_semantics": "R329_INTERLINEAGE_EXCHANGE_OPPORTUNITY_IS_DIAGNOSTIC_ONLY_NOT_REALIZED_GENE_FLOW_OR_ADMIXTURE",
        "source_r59_handoff_sha256": sha256_file(root / R59_HANDOFF),
        "source_r329_final_seal_audit_sha256": sha256_file(root / R329_SEAL_AUDIT),
        "source_r329_replay_sha256": sha256_file(root / R329_REPLAY),
        "ready_for_r330_reconciliation": not failed,
        "downstream_r330_auto_authorized": False,
    }
    write_json(out / "R5_10_0KA_COMMUNITY_PRECONDITION_HANDOFF.json", handoff)

    audit = {
        "stage": STAGE,
        "status": FINAL_STATUS if not failed else "BLOCKED_R510_R59_TO_R329_RECONCILIATION",
        "scientific_candidate_eligible": not failed,
        "checks_passed": len(checks) - len(failed),
        "checks_total": len(checks),
        "failed": failed,
        "checks": checks,
        "summary": {
            "target_cohort": list(TARGET_COHORT),
            "r329_time_states": int(len(ages29)),
            "r329_spatial_anchor_states": int(len(anchor_age29)),
            "r329_ensemble_members": 32,
            "community_precondition_cohort": list(outcomes.get("community_precondition_cohort") or []),
            "robust_priority_cohort": list(robust),
            "borderline_retained_cohort": list(borderline),
            "final_human_species_identity_materialized": False,
            "cultural_identity_materialized": False,
            "absolute_census_materialized": False,
            "new_external_engine_execution_performed": False,
            "r329_rerun_performed": False,
            "numeric_historical_truth_claimed": False,
            "realized_historical_gene_flow_claimed": False,
            "canonical_state_changed": False,
            "derived_refinement_promoted_to_canon": False,
            "deep_biological_coupling": False,
        },
        "recommended_next_action": "RECONCILE_SEALED_R330_CENSUS_CALIBRATION_GROUP_ABM_AND_LATE_PLEISTOCENE_COMMUNITY_HISTORY_AGAINST_R510_HANDOFF_BEFORE_ACCEPTING_DOWNSTREAM_HISTORY",
    }
    write_json(out / "R5_10_INTEGRATED_RECONCILIATION.json", audit)

    names = [
        "R5_10_RUNTIME_UTILITY_REVIEW.json", "R5_10_PARENT_AUTHORITY_BINDING.json",
        "R5_10_R329_PIPELINE_ALIGNMENT.json", "R5_10_R329_LEGACY_DIAGNOSTIC_CLASSIFICATION.json",
        "R5_10_0KA_COMMUNITY_PRECONDITION_HANDOFF.json", "R5_10_INTEGRATED_RECONCILIATION.json",
    ]
    files = {n: {"bytes": (out / n).stat().st_size, "sha256": sha256_file(out / n)} for n in names}
    write_json(out / "R5_10_OUTPUT_MANIFEST.json", {"stage": STAGE, "status": audit["status"], "files": files})
    return audit
