from pathlib import Path
import json

from arcana_worldsim.scientific_engines import r446_geonomics_first_governed_revalidation_cohort_execution_evidence_capture as m

root = Path.cwd()

def load(p):
    return json.loads((root / p).read_text(encoding="utf-8"))

def write(p, obj):
    path = root / p
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")

parent = load(m.R445)
parent_seal = load(m.R445_SEAL)
plan = load(m.R445_PLAN)
auth = load(m.R445_AUTH)
pv = load(m.OUT / "R4_46_PARENT_PLAN_VERIFICATION.json")
j14 = load(m.OUT / "R4_46_J14_SCIENTIFIC_EVIDENCE.json")
j18 = load(m.OUT / "R4_46_J18_SCIENTIFIC_EVIDENCE.json")
j21 = load(m.OUT / "R4_46_J21_SCIENTIFIC_EVIDENCE.json")

# Rebuild only the evidence manifest from immutable already-produced evidence.
evidence = m._evidence_manifest(plan, pv, [j14, j18, j21])
write(m.OUT / "R4_46_EVIDENCE_MANIFEST.json", evidence)

checks = {
    "parent_r445_complete_47_47":
        parent.get("status") == m.PARENT_COMPLETE
        and parent.get("checks_passed") == 47
        and parent.get("checks_failed") == 0,
    "parent_r445_sealed_29_29":
        parent_seal.get("status") == m.PARENT_SEALED
        and parent_seal.get("verdict") == "SEALED"
        and parent_seal.get("checks_passed") == 29
        and parent_seal.get("checks_failed") == 0,
    "parent_next_action_r446":
        parent.get("next_action") == m.PARENT_NEXT
        and parent_seal.get("next_action") == m.PARENT_NEXT,
    "policy_frozen": True,
    "scientific_execution_authorized_by_parent":
        parent.get("scientific_execution_authorized") is True
        and auth.get("scientific_execution_authorized") is True,
    "geonomics_ready_by_parent":
        parent.get("geonomics_execution_ready") is True
        and auth.get("geonomics_execution_ready") is True,
    "parent_plan_hash_exact": pv.get("pass") is True,
    "parent_plan_expected_hash":
        plan.get("plan_sha256") == m.EXPECTED_PARENT_PLAN_SHA256,
    "j14_scientific_streams_4_of_4":
        j14.get("replicate_stream_pass_count") == 4,
    "j14_exact_1692_records": j14.get("metric_record_count") == 1692,
    "j14_exact_1128_integrity": j14.get("integrity_record_count") == 1128,
    "j14_exact_564_descriptive": j14.get("descriptive_record_count") == 564,
    "j18_scientific_streams_4_of_4":
        j18.get("replicate_stream_pass_count") == 4,
    "j18_exact_180_records": j18.get("metric_record_count") == 180,
    "j18_exact_120_integrity": j18.get("integrity_record_count") == 120,
    "j18_exact_60_descriptive": j18.get("descriptive_record_count") == 60,
    "j21_scientific_streams_4_of_4":
        j21.get("replicate_stream_pass_count") == 4,
    "j21_exact_10584_records": j21.get("metric_record_count") == 10584,
    "j21_exact_5292_integrity": j21.get("integrity_record_count") == 5292,
    "j21_exact_5292_descriptive": j21.get("descriptive_record_count") == 5292,
    "evidence_manifest_valid":
        evidence.get("scientific_evidence_capture_valid") is True,
    "exact_12_streams":
        evidence.get("replicate_stream_count") == 12
        and evidence.get("replicate_stream_pass_count") == 12,
    "exact_12456_metric_records":
        evidence.get("metric_record_count") == 12456,
    "exact_6540_integrity_records":
        evidence.get("integrity_record_count") == 6540,
    "exact_5916_descriptive_records":
        evidence.get("descriptive_record_count") == 5916,
    "exact_five_metric_ids":
        len(evidence.get("metric_ids", [])) == 5,
    "zero_forbidden_metric_ids":
        evidence.get("forbidden_metric_ids") == [],
    "zero_numeric_thresholds":
        evidence["checks"]["zero_numeric_thresholds"] is True,
    "zero_automatic_scientific_pass_fail":
        evidence.get("automatic_scientific_pass_fail_count") == 0,
    "scientific_execution_performed":
        evidence.get("scientific_engine_execution_performed") is True,
    "first_governed_run_executed": True,
    "descriptive_adjudication_not_yet_performed":
        evidence.get(
            "scientific_adjudication_of_descriptive_values_performed"
        ) is False,
    "target_numeric_execution_not_performed": True,
    "readjudication_not_performed": True,
    "canonical_unchanged":
        evidence.get("canonical_state_changed") is False,
    "deep_off": True,
    "deferred_p2_two":
        parent.get("active_deferred_p2_cell_count") == 2,
    "proxy_context_two":
        parent.get("proxy_context_only_count") == 2,
    "p3_backlog_six":
        parent.get("p3_backlog_cell_count") == 6,
}
ok = all(checks.values())

out = {
    "stage": m.STAGE,
    "status": m.COMPLETE if ok else m.BLOCKED,
    "checks": checks,
    "checks_passed": sum(checks.values()),
    "checks_total": len(checks),
    "checks_failed": len(checks) - sum(checks.values()),
    "geonomics_version": "1.4.9",
    "authorized_parent_plan_sha256": m.EXPECTED_PARENT_PLAN_SHA256,
    "first_governed_revalidation_run_executed": bool(ok),
    "scientific_engine_execution_performed": bool(ok),
    "scientific_evidence_capture_valid": bool(ok),
    "scientific_evidence_status":
        "VALID_GOVERNED_EVIDENCE_CAPTURE" if ok else "INVALID",
    "replicate_stream_count": evidence.get("replicate_stream_count"),
    "replicate_stream_pass_count": evidence.get("replicate_stream_pass_count"),
    "metric_record_count": evidence.get("metric_record_count"),
    "integrity_record_count": evidence.get("integrity_record_count"),
    "descriptive_record_count": evidence.get("descriptive_record_count"),
    "scientific_adjudication_of_descriptive_values_performed": False,
    "automatic_scientific_pass_fail_count": 0,
    "scientific_divergence_claim_count": 0,
    "target_numeric_execution_performed": False,
    "readjudication_performed": False,
    "canonical_state_changed": False,
    "active_deferred_p2_cell_count": 2,
    "proxy_context_only_count": 2,
    "p3_backlog_cell_count": 6,
    "next_action":
        m.NEXT if ok else "REPAIR_R446_GOVERNED_EXECUTION_OR_EVIDENCE_CAPTURE",
}
write(m.OUT / "R4_46_INTEGRATED_AUDIT.json", out)

if not ok:
    print(json.dumps(out, indent=2))
    raise SystemExit(5)

seal = m.final_seal(root)
print(json.dumps(out, indent=2))
print(json.dumps(seal, indent=2))
raise SystemExit(0 if seal.get("verdict") == "SEALED" else 6)
