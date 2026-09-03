from pathlib import Path
import json

root = Path.cwd()

ia = json.loads(
    (root / "outputs/v0_6D1_R4_39/R4_39_INTEGRATED_AUDIT.json").read_text(
        encoding="utf-8"
    )
)
seal = json.loads(
    (root / "outputs/v0_6D1_R4_39_SEAL/R4_39_FINAL_SEAL_AUDIT.json").read_text(
        encoding="utf-8"
    )
)
dyn = json.loads(
    (
        root
        / "outputs/v0_6D1_R4_39/"
        "R4_39_J21_NATIVE_DYNAMIC_LAYER_CHANGER_PREFLIGHT.json"
    ).read_text(encoding="utf-8")
)
pay = json.loads(
    (
        root
        / "outputs/v0_6D1_R4_39/"
        "R4_39_J21_DYNAMIC_CANONICAL_PAYLOAD_AUTHORITY.json"
    ).read_text(encoding="utf-8")
)
gate = json.loads(
    (
        root
        / "outputs/v0_6D1_R4_39/"
        "R4_39_NONLITERAL_CARRIER_DYNAMICS_AUTHORITY_GATE.json"
    ).read_text(encoding="utf-8")
)

checks = {
    "complete":
        str(ia.get("status", "")).startswith("PASS_R439_")
        and ia.get("checks_failed") == 0,
    "sealed":
        seal.get("verdict") == "SEALED"
        and seal.get("checks_failed") == 0,
    "dynamic_147_plus_4":
        pay.get("native_identity_layer_count") == 147
        and pay.get("canonical_dynamic_sidecar_count") == 4,
    "four_seed_bindings":
        dyn.get("seed_binding_pass_count") == 4
        and dyn.get("all_four_frozen_seed_bindings_exact") is True,
    "bounded_probe":
        dyn.get("bounded_native_changer_probe_pass") is True,
    "full_1176_series":
        dyn.get("full_direct_native_series_validation_pass_count") == 1176
        and dyn.get("full_direct_native_series_validation_exact") is True,
    "probe_repairs_8":
        dyn.get(
            "bounded_native_changer_probe_adapter_evidence", {}
        ).get("metadata_repair_count") == 8,
    "direct_repairs_1176":
        dyn.get(
            "full_direct_native_series_adapter_evidence", {}
        ).get("metadata_repair_count") == 1176,
    "no_full_147_changer":
        dyn.get("full_147_layer_landscape_changer_materialized") is False,
    "no_fourfold_redundancy":
        dyn.get("fourfold_redundant_changer_compilation_performed") is False,
    "carrier_gap_frozen":
        gate.get("status")
        == "R439_NONLITERAL_CARRIER_DYNAMICS_AUTHORITY_GAP_FROZEN",
    "no_run":
        ia.get("model_run_performed_count") == 0,
    "not_ready":
        ia.get("geonomics_execution_ready") is False,
    "no_scientific":
        ia.get("scientific_engine_execution_performed") is False,
    "canonical_unchanged":
        ia.get("canonical_state_changed") is False,
    "next_r440":
        "BUILD_R440_" in str(ia.get("next_action", "")),
}

ok = all(checks.values())

out = {
    "stage": "v0.6D1-R4.39-R5",
    "status":
        "PASS_R439_R5_BOUNDED_PREFLIGHT_AND_R439_RESEAL_VERIFIED"
        if ok
        else "BLOCKED_R439_R5_POSTREPAIR_RESEAL_FAILURE",
    "checks": checks,
    "checks_passed": sum(checks.values()),
    "checks_total": len(checks),
    "r439_status": ia.get("status"),
    "seal_status": seal.get("status"),
    "seal_verdict": seal.get("verdict"),
    "next_action": ia.get("next_action"),
}

p = (
    root
    / "outputs/v0_6D1_R4_39_R5/"
    "R4_39_R5_POSTREPAIR_RESEAL_AUDIT.json"
)
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(
    json.dumps(out, indent=2) + "\n",
    encoding="utf-8",
)

print(json.dumps(out, indent=2))
raise SystemExit(0 if ok else 5)
