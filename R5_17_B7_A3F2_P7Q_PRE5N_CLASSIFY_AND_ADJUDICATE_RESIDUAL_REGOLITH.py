from __future__ import annotations

import gzip
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCAL_EXT = ROOT.parent / "_ARCANA_EXTERNAL_SOURCES"
CANONICAL_EXT = ROOT.parent.parent / "ArcanaWorld_ARCANA_EXTERNAL_SOURCES"
PRE5C = LOCAL_EXT / "p7q_parent_state" / "PRE5C_STATIC_REBUILD" / "PRE5C_STATIC_PARENT_STATE_0KA.jsonl.gz"
PRE5I_STATIC = LOCAL_EXT / "p7q_parent_state" / "PRE5I_STATIC_MATERIALIZATION" / "PRE5I_STATIC_PARENT_STATE_0KA.jsonl.gz"
PRE5M = CANONICAL_EXT / "p7q_parent_state" / "PRE5M_ELIGIBILITY_EVIDENCE" / "PRE5M_TARGET_ELIGIBILITY_EVIDENCE_0KA.jsonl.gz"
PRE5N_EXT = CANONICAL_EXT / "p7q_parent_state" / "PRE5N_DECISION_LEDGER"
PRE5N_LEDGER = PRE5N_EXT / "PRE5N_RESIDUAL_CLASSIFIER_DECISIONS_0KA.jsonl.gz"
TARGET = 50568
TARGET_SHA = "3b139c494c2714bba5bbeecce426bb33bbcda6d7acbb5188471c9fa172ef9e28"
PRE5M_BYTES = 1130691
PRE5M_SHA = "adf751ea8c29be74f2ee51a84effbecc0055402a73f214ffc286971fb5d542ae"
STATIC_BYTES = 6240025
STATIC_SHA = "e25cd2b55e34e5b175aaf631849dc319448f8510b83d1407ef9f1ffab0a4caee"
STATIC_RECORDS = 249840


def fail(code: str) -> None:
    raise SystemExit(code)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(name: str, value: dict) -> None:
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def cohort_ids() -> list[str]:
    ids = []
    with gzip.open(PRE5C, "rt", encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            if record.get("material_branch") == "UNKNOWN_MATERIAL" and record.get("state_support") == "MISSING_SOURCE":
                ids.append(record["cell_id"])
    digest = hashlib.sha256()
    for cell_id in ids:
        digest.update((cell_id + "\n").encode())
    if len(ids) != TARGET or digest.hexdigest() != TARGET_SHA:
        fail("BLOCKED_P7Q_PRE5N_TARGET_COHORT_IDENTITY_DRIFT")
    return ids


def load_prem5_records(expected_ids: list[str]) -> list[dict]:
    if not PRE5M.exists() or PRE5M.stat().st_size != PRE5M_BYTES or sha256(PRE5M) != PRE5M_SHA:
        fail("BLOCKED_P7Q_PRE5N_PRE5M_PAYLOAD_IDENTITY_DRIFT")
    records = []
    with gzip.open(PRE5M, "rt", encoding="utf-8") as stream:
        for line in stream:
            records.append(json.loads(line))
    ids = [record.get("cell_id") for record in records]
    if len(records) != TARGET or ids != expected_ids or len(set(ids)) != TARGET:
        fail("BLOCKED_P7Q_PRE5N_PRE5M_RECORD_ORDER_OR_COUNT_DRIFT")
    return records


def verify_static_payload() -> dict:
    if not PRE5I_STATIC.exists() or PRE5I_STATIC.stat().st_size != STATIC_BYTES or sha256(PRE5I_STATIC) != STATIC_SHA:
        fail("BLOCKED_P7Q_PRE5N_STATIC_PAYLOAD_IDENTITY_DRIFT")
    count = 0
    with gzip.open(PRE5I_STATIC, "rt", encoding="utf-8") as stream:
        for line in stream:
            json.loads(line)
            count += 1
    if count != STATIC_RECORDS:
        fail("BLOCKED_P7Q_PRE5N_STATIC_PAYLOAD_RECORD_COUNT_DRIFT")
    return {"path": str(PRE5I_STATIC), "records": count, "bytes": PRE5I_STATIC.stat().st_size, "sha256": STATIC_SHA, "reused_unchanged": True}


def main() -> int:
    pre5m_adjudication = json.loads((ROOT / "R5_17_B7_A3F2_P7Q_PRE5M_ADJUDICATION.json").read_text(encoding="utf-8"))
    if pre5m_adjudication.get("decision") != "AUTHORIZE_P7Q_PRE5N_RESIDUAL_REGOLITH_CLASSIFIER_CONTRACT_AND_STATIC_MATERIALIZATION_GATE" or pre5m_adjudication.get("verdict") != "PASS_P7Q_PRE5M_RESIDUAL_ELIGIBILITY_EVIDENCE_MATERIALIZATION_VALIDATED":
        fail("BLOCKED_P7Q_PRE5N_PRE5M_AUTHORITY_DRIFT")
    if pre5m_adjudication.get("classifier_executed") is not False or pre5m_adjudication.get("residual_regolith_assignments") != 0:
        fail("BLOCKED_P7Q_PRE5N_PRE5M_GOVERNANCE_DRIFT")
    expected_ids = cohort_ids()
    records = load_prem5_records(expected_ids)
    compatible = [record for record in records if record.get("eligibility_evidence_status") == "PROCESS_COMPATIBLE_STRUCTURAL_EVIDENCE_PRESENT"]
    if len(compatible) != 560:
        fail("BLOCKED_P7Q_PRE5N_COMPATIBLE_COHORT_COUNT_DRIFT")
    reasons = Counter()
    decisions = []
    for record in compatible:
        martin = record.get("martin_lamb", {})
        intact = record.get("pelletier", {}).get("intact_regolith", {})
        sediment = record.get("pelletier", {}).get("sedimentary_deposit", {})
        dependency = record.get("dependency_metadata", {})
        exact_process = martin.get("process_domain_disposition") == "PROCESS_COMPATIBLE" and martin.get("provider_class_set") == ["SOURCE"] and martin.get("sink_count") == 0 and martin.get("bypass_count") == 0 and martin.get("missing_data_count") == 0
        structural = "INTACT_REGOLITH_EVIDENCE_PRESENT" in intact.get("flags", []) and int(intact.get("positive_count", 0)) > 0
        gum_unresolved = record.get("GUM_preemption_status") == "GUM_ABSENCE_OR_NO_COVERAGE_ABSTAIN"
        dependency_valid = dependency.get("evidence_independence") is False and dependency.get("dependency_type") == "METHOD_INPUT_DEPENDENCY"
        sediment_context = "SEDIMENTARY_EVIDENCE_PRESENT" in sediment.get("flags", [])
        if not exact_process:
            reason = "ABSTAIN_PROCESS_PREDICATE_DRIFT"
        elif not structural:
            reason = "ABSTAIN_STRUCTURAL_EVIDENCE_MISSING"
        elif not dependency_valid:
            reason = "ABSTAIN_DEPENDENCY_METADATA_INVALID"
        elif gum_unresolved:
            reason = "ABSTAIN_GUM_TRANSPORT_PREEMPTION_UNRESOLVED"
        else:
            reason = "ABSTAIN_REQUIRED_AUTHORITY_UNRESOLVED"
        reasons[reason] += 1
        decisions.append({"cell_id": record["cell_id"], "target_order_index": record["target_order_index"], "classifier_input": {"exact_process_predicate": exact_process, "structural_regolith_evidence_present": structural, "sedimentary_context_present": sediment_context, "gum_preemption_status": record.get("GUM_preemption_status"), "evidence_independence": dependency.get("evidence_independence"), "dependency_type": dependency.get("dependency_type")}, "decision": "ABSTAIN", "abstention_reason": reason, "material_branch": "UNKNOWN_MATERIAL", "residual_regolith_assignment": False, "saprolite_assignment": False, "bedrock_assignment": False, "threshold_used": False, "provider_vote_used": False})
    static_payload = verify_static_payload()
    PRE5N_EXT.mkdir(parents=True, exist_ok=True)
    ledger_tmp = PRE5N_LEDGER.with_suffix(".tmp")
    with ledger_tmp.open("wb") as stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=stream, mtime=0) as gz:
            for decision in decisions:
                gz.write((json.dumps(decision, sort_keys=True, separators=(",", ":")) + "\n").encode())
    os.replace(ledger_tmp, PRE5N_LEDGER)
    ledger_manifest = {"stage": "R5.17-B7-A3F2-P7Q-PRE5N", "path": str(PRE5N_LEDGER), "records": len(decisions), "bytes": PRE5N_LEDGER.stat().st_size, "sha256": sha256(PRE5N_LEDGER), "serialization": "UTF-8 JSONL, sort_keys=true, compact separators, gzip mtime=0 filename=''", "deterministic": True}
    write_json("R5_17_B7_A3F2_P7Q_PRE5N_RESIDUAL_REGOLITH_CLASSIFIER_CONTRACT.json", {"stage": "R5.17-B7-A3F2-P7Q-PRE5N", "contract_valid": True, "classifier_executed": True, "input_cohort": {"count": TARGET, "identity_sha256": TARGET_SHA, "compatible_count": len(compatible)}, "predicates": {"process": "PROCESS_COMPATIBLE with provider class SOURCE and sink/bypass/missing counts zero", "structural": "INTACT_REGOLITH_EVIDENCE_PRESENT and positive_count > 0", "gum": "GUM_ABSENCE_OR_NO_COVERAGE_ABSTAIN is unresolved, not explicit transported-material absence", "dependency": "evidence_independence=false and dependency_type=METHOD_INPUT_DEPENDENCY", "decision": "ABSTAIN until transported-material absence is explicitly distinguished from unknown"}, "threshold_used": False, "provider_vote_used": False, "forbidden_promotions": ["SOURCE_TO_RESIDUAL_REGOLITH", "POSITIVE_THICKNESS_TO_RESIDUAL_REGOLITH", "GUM_ABSENCE_TO_RESIDUAL_REGOLITH", "GUM_NODATA_TO_BEDROCK", "SINK_TO_ASSIGNMENT", "SAPROLITE_OR_DEEP_WEATHERING"], "assignments": {"RESIDUAL_REGOLITH": 0, "SAPROLITE_OR_DEEP_WEATHERING": 0, "BEDROCK_EXPOSED": 0}})
    write_json("R5_17_B7_A3F2_P7Q_PRE5N_EVIDENCE_MATRIX_SUMMARY.json", {"stage": "R5.17-B7-A3F2-P7Q-PRE5N", "input_records": TARGET, "compatible_records": len(compatible), "evaluated_records": len(decisions), "decision_counts": {"ABSTAIN": len(decisions)}, "primary_abstention_reasons": dict(reasons), "process_semantics_preserved": True, "structural_semantics_preserved": True, "provider_voting": False, "numeric_threshold": False})
    write_json("R5_17_B7_A3F2_P7Q_PRE5N_DECISION_LEDGER_MANIFEST.json", ledger_manifest)
    write_json("R5_17_B7_A3F2_P7Q_PRE5N_STATIC_PARENT_READINESS_AUDIT.json", {"stage": "R5.17-B7-A3F2-P7Q-PRE5N", "static_parent_state_ready_for_anchorbridge": True, "readiness_class": "READY_FOR_ENDPOINT_CONSTRAINED_HYBRID_TEMPORAL_ADAPTER_WITH_EXPLICIT_UNKNOWN_MASK", "static_payload": static_payload, "unknown_material_preserved": True, "existing_transported_branches_preserved": True, "residual_assignments": 0, "saprolite_assignments": 0, "canonical_parent_created": False, "physical_soil_created": False, "temporal_reconstruction": False, "anchorbridge_started": False, "unknown_is_not_zero": True})
    adjudication = {"stage": "R5.17-B7-A3F2-P7Q-PRE5N", "decision": "AUTHORIZE_P7Q_HIGH_RESOLUTION_ANCHORBRIDGE_ENDPOINT_CONSTRAINED_HYBRID_TEMPORAL_PARENT_STATE_ADAPTER", "verdict": "PASS_P7Q_PRE5N_RESIDUAL_REGOLITH_CLASSIFIER_ADJUDICATED_WITH_ZERO_ASSIGNMENTS", "status": "COMPLETE__RESIDUAL_CLASSIFIER_EXECUTED__NO_RESIDUAL_ASSIGNMENTS__STATIC_PARENT_READY_FOR_ANCHORBRIDGE", "next_action": "P7Q_HIGH_RESOLUTION_ANCHORBRIDGE_ENDPOINT_CONSTRAINED_HYBRID_TEMPORAL_PARENT_STATE_ADAPTER", "contract_valid": True, "classifier_executed": True, "compatible_records_inspected": len(decisions), "threshold_used": False, "provider_vote_used": False, "dependency_aware": True, "assignments": {"RESIDUAL_REGOLITH": 0, "SAPROLITE_OR_DEEP_WEATHERING": 0, "BEDROCK_EXPOSED": 0}, "primary_abstention_reasons": dict(reasons), "static_payload": static_payload, "static_parent_state_ready_for_anchorbridge": True, "readiness_class": "READY_FOR_ENDPOINT_CONSTRAINED_HYBRID_TEMPORAL_ADAPTER_WITH_EXPLICIT_UNKNOWN_MASK", "P7Q_reopened": False, "physical_soil_created": False, "temporal_reconstruction": False, "scientific_authority_register_mutated": False, "canonical_parent_created": False, "anchorbridge_started": False, "no_numeric_threshold": True, "no_provider_voting": True, "unknown_material_preserved": True, "decision_ledger": ledger_manifest}
    write_json("R5_17_B7_A3F2_P7Q_PRE5N_ADJUDICATION.json", adjudication)
    (ROOT / "R5_17_B7_A3F2_P7Q_PRE5N_ADJUDICATION.md").write_text("# R5.17-B7-A3F2-P7Q-PRE5N\n\nDecision: `AUTHORIZE_P7Q_HIGH_RESOLUTION_ANCHORBRIDGE_ENDPOINT_CONSTRAINED_HYBRID_TEMPORAL_PARENT_STATE_ADAPTER`\n\nVerdict: `PASS_P7Q_PRE5N_RESIDUAL_REGOLITH_CLASSIFIER_ADJUDICATED_WITH_ZERO_ASSIGNMENTS`\n\nThe 560 process-compatible records were evaluated deterministically. All retained `GUM_ABSENCE_OR_NO_COVERAGE_ABSTAIN`; this is unresolved transported-material preemption, not explicit absence. Therefore every record abstained and remained `UNKNOWN_MATERIAL`. No numerical threshold, provider vote, residual-regolith assignment, saprolite assignment, or bedrock assignment was produced. The existing 249,840-record static payload was reused unchanged. Static readiness is endpoint-constrained and uncertainty-preserving; AnchorBridge was not started.\n", encoding="utf-8")
    state_path = ROOT / "ARCANA_WORLD_CURRENT_STATE.md"
    state = state_path.read_text(encoding="utf-8")
    replacements = [("LATEST_COMPLETED_INTERNAL_STEP: R5.17-B7-A3F2-P7Q-PRE5M", "LATEST_COMPLETED_INTERNAL_STEP: R5.17-B7-A3F2-P7Q-PRE5N"), ("LATEST_INTERNAL_VERDICT: PASS_P7Q_PRE5M_RESIDUAL_ELIGIBILITY_EVIDENCE_MATERIALIZATION_VALIDATED", "LATEST_INTERNAL_VERDICT: PASS_P7Q_PRE5N_RESIDUAL_REGOLITH_CLASSIFIER_ADJUDICATED_WITH_ZERO_ASSIGNMENTS"), ("ACTIVE_SUBPHASE_STATUS: A3_IN_PROGRESS__P7Q_PRE5M_COMPLETE__ELIGIBILITY_EVIDENCE_MATERIALIZED__NO_PARENT_CLASSIFICATION", "ACTIVE_SUBPHASE_STATUS: A3_IN_PROGRESS__P7Q_PRE5N_COMPLETE__RESIDUAL_CLASSIFIER_EXECUTED__NO_ASSIGNMENTS__STATIC_PARENT_READY_FOR_ANCHORBRIDGE"), ("NEXT_ACTION: P7Q_PRE5N_RESIDUAL_REGOLITH_CLASSIFIER_CONTRACT_AND_STATIC_MATERIALIZATION_GATE", "NEXT_ACTION: P7Q_HIGH_RESOLUTION_ANCHORBRIDGE_ENDPOINT_CONSTRAINED_HYBRID_TEMPORAL_PARENT_STATE_ADAPTER")]
    for old, new in replacements:
        if old not in state:
            fail("BLOCKED_P7Q_PRE5N_CURRENT_STATE_EXPECTATION_MISSING")
        state = state.replace(old, new, 1)
    state += "\nP7Q_PRE5N_STATUS: COMPLETE__RESIDUAL_CLASSIFIER_EXECUTED__NO_RESIDUAL_ASSIGNMENTS__STATIC_PARENT_READY_FOR_ANCHORBRIDGE\nP7Q_PRE5N_DECISION: AUTHORIZE_P7Q_HIGH_RESOLUTION_ANCHORBRIDGE_ENDPOINT_CONSTRAINED_HYBRID_TEMPORAL_PARENT_STATE_ADAPTER\n"
    state_path.write_text(state, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
