from pathlib import Path
import json

root = Path.cwd()
ia = json.loads((root/"outputs/v0_6D1_R4_46/R4_46_INTEGRATED_AUDIT.json").read_text(encoding="utf-8"))
ev = json.loads((root/"outputs/v0_6D1_R4_46/R4_46_EVIDENCE_MANIFEST.json").read_text(encoding="utf-8"))
seal = json.loads((root/"outputs/v0_6D1_R4_46_SEAL/R4_46_FINAL_SEAL_AUDIT.json").read_text(encoding="utf-8"))

checks = {
    "r446_complete": str(ia.get("status","")).startswith("PASS_R446_") and ia.get("checks_failed")==0,
    "r446_sealed": seal.get("verdict")=="SEALED" and seal.get("checks_failed")==0,
    "evidence_manifest_valid": ev.get("scientific_evidence_capture_valid") is True,
    "exact_metric_id_gate": ev.get("checks",{}).get("exact_five_metric_ids") is True,
    "exact_12_streams": ia.get("replicate_stream_count")==12 and ia.get("replicate_stream_pass_count")==12,
    "exact_12456_records": ia.get("metric_record_count")==12456,
    "exact_6540_integrity": ia.get("integrity_record_count")==6540,
    "exact_5916_descriptive": ia.get("descriptive_record_count")==5916,
    "scientific_execution_recorded": ia.get("scientific_engine_execution_performed") is True,
    "first_run_recorded_executed": ia.get("first_governed_revalidation_run_executed") is True,
    "zero_thresholds": ev.get("checks",{}).get("zero_numeric_thresholds") is True,
    "zero_auto_pass_fail": ia.get("automatic_scientific_pass_fail_count")==0,
    "zero_divergence_claims": ia.get("scientific_divergence_claim_count")==0,
    "descriptive_adjudication_pending": ia.get("scientific_adjudication_of_descriptive_values_performed") is False,
    "canonical_unchanged": ia.get("canonical_state_changed") is False,
    "next_r447": "BUILD_R447_" in str(ia.get("next_action","")),
}
ok = all(checks.values())
out = {
    "stage":"v0.6D1-R4.46-R1",
    "status":"PASS_R446_R1_EVIDENCE_MANIFEST_ORDER_REPAIR_AND_R446_RESEAL_VERIFIED" if ok else "BLOCKED_R446_R1_POSTREPAIR_RESEAL_FAILURE",
    "checks":checks,
    "checks_passed":sum(checks.values()),
    "checks_total":len(checks),
    "r446_status":ia.get("status"),
    "seal_status":seal.get("status"),
    "seal_verdict":seal.get("verdict"),
    "next_action":ia.get("next_action"),
}
p=root/"outputs/v0_6D1_R4_46_R1/R4_46_R1_POSTREPAIR_RESEAL_AUDIT.json"
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,indent=2))
raise SystemExit(0 if ok else 7)
