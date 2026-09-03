from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np

from arcana_worldsim.scientific_engines import r314_late_cenozoic_binding as r314
from arcana_worldsim.late_cenozoic.cha2_nested_50y import (
    FORMULA_EQ_ATOL,
    FORMULA_EQ_RTOL,
    IntegratedLateCenozoicProviderC1,
)
from arcana_worldsim.late_cenozoic.late_pleistocene_boundary import IntegratedLateCenozoicProviderC2

STAGE = "v0.6D1-R3.14"
VERDICT = "PASS_R314_LATE_CENOZOIC_PROVIDER_C2_AND_ADAPTIVE_CLOCK_BOUND__30MA_H0_BIOLOGY_RESTART_BOUNDARY_SEALED"


def hfile(path: Path) -> str:
    h = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seal-out", type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve()
    out = args.out.resolve()
    seal_out = args.seal_out.resolve()
    bind = root / "local_bindings/v0_6D1_R3_14"
    summary_path = bind / "R3_14_LATE_CENOZOIC_BINDING_SUMMARY.json"
    clock_path = bind / "R3_14_ADAPTIVE_CLOCK_C2_30Ma_TO_BOOK.json"
    sealed_root = bind / "v0_6_1_SEALED_MINIMAL"
    b1_path = bind / "v0_6_4B1/exact_120ka_A1_boundary_state.npz"
    b2_path = bind / "v0_6_4B2/relative_eustatic_shoreline_anomaly_120ka_A1.npz"
    source_manifest_path = root / "SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_14.json"

    checks: list[dict[str, Any]] = []
    def ck(name: str, ok: bool, detail: Any = None) -> None:
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    # Required evidence surface.
    for name, p in {
        "binding_summary": summary_path,
        "adaptive_clock": clock_path,
        "v061_root": sealed_root,
        "B1_boundary": b1_path,
        "B2_boundary": b2_path,
        "source_manifest": source_manifest_path,
    }.items():
        ck(f"exists:{name}", p.exists(), str(p))
    if not all(x["pass"] for x in checks):
        raise SystemExit("R3.14 sealed audit missing required materialized evidence")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    clock_disk = json.loads(clock_path.read_text(encoding="utf-8"))

    ck("summary_stage", summary.get("stage") == STAGE, summary.get("stage"))
    ck("summary_verdict", summary.get("verdict") == "PASS_R314_LATE_CENOZOIC_PROVIDER_C2_AND_ADAPTIVE_CLOCK_BOUND__BIOLOGY_REPLAY_NOT_STARTED", summary.get("verdict"))
    ck("summary_no_blocker", summary.get("blocker_report") in (None, ""), summary.get("blocker_report"))

    # Parent authority is reloaded, hash-checked, and restored to 30 Ma.
    parent = r314.validate_parent_r313_authority(root)
    ck("parent_age_30ma", abs(float(parent["age_ma"]) - 30.0) <= 1e-12, parent["age_ma"])
    ck("parent_species_111", int(parent["species"]) == 111, parent["species"])
    ck("parent_components_219", int(parent["components"]) == 219, parent["components"])
    ck("parent_population_positive", float(parent["population"]) > 0.0, parent["population"])

    # Final R3.14-R2 code/source authority hashes.
    for group in ("r314_final_files", "late_cenozoic_authorities_unchanged_except_declared_r1_validation_repair"):
        for rel, want in manifest[group].items():
            p = root / rel
            got = hfile(p) if p.is_file() else None
            ck(f"source_sha:{rel}", got == want, {"expected": want, "actual": got})
    ck("formula_replay_rtol_frozen", float(FORMULA_EQ_RTOL) == 1.0e-10, FORMULA_EQ_RTOL)
    ck("formula_replay_atol_frozen", float(FORMULA_EQ_ATOL) == 1.0e-12, FORMULA_EQ_ATOL)
    ck("biology_not_modified_manifest", manifest.get("governance", {}).get("biology_modified") is False)
    ck("scientific_parameters_not_changed_manifest", manifest.get("governance", {}).get("scientific_parameters_changed") is False)

    # Exact five-file v0.6.1 authority is checked directly on disk and against both manifests.
    vproof = r314.b1.verify_v061_sealed_root(sealed_root)
    for key, want in r314.EXPECTED_V061_SHA256.items():
        ck(f"v061_sha:{key}", vproof.get(key) == want, {"expected": want, "actual": vproof.get(key)})
        ck(f"manifest_v061_sha:{key}", manifest["frozen_v061_payload_hashes"].get(key) == want)
        ck(f"summary_discovery_v061_sha:{key}", summary.get("discovery", {}).get("hashes", {}).get(key) == want)
        ck(f"summary_materialized_v061_sha:{key}", summary.get("materialized_boundaries", {}).get("sealed_payload_hashes", {}).get(key) == want)

    # B1/B2 materialization integrity and sealed summary hash binding.
    mat = summary.get("materialized_boundaries", {})
    ck("b1_sha_matches_summary", hfile(b1_path) == mat.get("b1_sha256"), {"actual": hfile(b1_path), "summary": mat.get("b1_sha256")})
    ck("b2_sha_matches_summary", hfile(b2_path) == mat.get("b2_sha256"), {"actual": hfile(b2_path), "summary": mat.get("b2_sha256")})
    b1z = np.load(b1_path, allow_pickle=False)
    b2z = np.load(b2_path, allow_pickle=False)
    ck("b1_age_120ka", np.array_equal(np.asarray(b1z["age_ma"], dtype=float), np.asarray([0.12], dtype=float)), np.asarray(b1z["age_ma"]).tolist())
    ck("b2_age_120ka", np.array_equal(np.asarray(b2z["age_ma"], dtype=float), np.asarray([0.12], dtype=float)), np.asarray(b2z["age_ma"]).tolist())
    for key in ("temperature_c", "aridity_index", "browse_forage", "low_forage", "wetland_forage", "total_edible_forage", "paleo_land_fraction"):
        arr = np.asarray(b1z[key], dtype=float)
        ck(f"b1_finite:{key}", bool(np.all(np.isfinite(arr))))
    for key in ("effective_land_support_120ka", "colonizable_shelf_support_120ka"):
        arr = np.asarray(b2z[key], dtype=float)
        ck(f"b2_finite:{key}", bool(np.all(np.isfinite(arr))))

    # Rebuild the actual C1->C2 provider and adaptive clock from the materialized evidence.
    a1 = r314.load_a1(root)
    c2, clock = r314.build_bound_provider_and_clock(a1, sealed_root, b1_path, b2_path)
    ck("actual_c2_type", isinstance(c2, IntegratedLateCenozoicProviderC2), type(c2).__name__)
    ck("actual_c2_parent_is_c1", isinstance(c2.parent, IntegratedLateCenozoicProviderC1), type(c2.parent).__name__)
    binding = r314.validate_30ma_binding(a1, c2)
    ck("30ma_r313_old_to_late_exact", binding["r313_old_to_late_endpoint_identity_exact"] is True)
    ck("30ma_c2_endpoint_exact", binding["r314_bound_c2_endpoint_identity_exact"] is True)
    for key, row in binding["fields"].items():
        ck(f"30ma_exact:{key}", row["exact"] is True, row)
        ck(f"30ma_zero_error:{key}", float(row["max_abs_error"]) == 0.0, row["max_abs_error"])

    # Stored clock is re-derived and must retain exact scheduler topology.
    cs = r314.summarize_clock(clock)
    ck("clock_status", cs["status"] == "PASS_ADAPTIVE_CLOCK_WITH_200_120KA_REPLAY_SAFE_BOUNDARY_CONTINUATION", cs["status"])
    ck("clock_checkpoint_count_374", int(cs["checkpoint_count"]) == 374, cs["checkpoint_count"])
    ck("clock_interval_count_373", int(cs["interval_count"]) == 373, cs["interval_count"])
    ck("clock_start_30ma", abs(float(cs["start_age_ma"]) - 30.0) <= 1e-12, cs["start_age_ma"])
    ck("clock_end_book", abs(float(cs["end_age_ma"])) <= 1e-12, cs["end_age_ma"])
    ck("clock_contains_200ka", cs["contains_200ka"] is True)
    ck("clock_contains_120ka", cs["contains_120ka"] is True)
    ck("clock_min_dt_50y", int(cs["min_dt_years"]) == 50, cs["min_dt_years"])
    ck("clock_max_dt_2my", int(cs["max_dt_years"]) == 2_000_000, cs["max_dt_years"])
    expected_domains = {
        "SECULAR_30MA_TO_200KA": 18,
        "LATE_PLEISTOCENE_200_120KA_REPLAY_SAFE_BOUNDARY_CONTINUATION": 160,
        "RECENT_WITH_CHA2_50Y_NESTED_AUTHORITY": 195,
    }
    ck("clock_domain_counts", cs["domain_interval_counts"] == expected_domains, cs["domain_interval_counts"])
    val = cs["validation"]
    ck("clock_validation_pass", val.get("status") == "PASS", val.get("status"))
    ck("clock_no_errors", val.get("errors") == [], val.get("errors"))
    ck("clock_no_production_blockers", val.get("production_replay_blockers") == [], val.get("production_replay_blockers"))
    ck("clock_production_replay_ready", val.get("production_replay_ready") is True)
    ck("clock_scope_coarse_natural_history", val.get("production_replay_ready_scope") == "COARSE_NATURAL_HISTORY_30MA_TO_BOOK_WITH_C2_BOUNDARY_CONTINUATION", val.get("production_replay_ready_scope"))
    ck("historical_highres_not_claimed", val.get("high_resolution_200ka_historical_paleoclimate_sealed") is False)
    ck("c2_not_historical_glacial_chronology", val.get("c2_bridge_is_historical_glacial_chronology") is False)
    ck("c2_step_500y", int(val.get("c2_bridge_step_years")) == 500, val.get("c2_bridge_step_years"))
    ck("c2_interval_count_160", int(val.get("c2_bridge_interval_count")) == 160, val.get("c2_bridge_interval_count"))
    ck("120ka_nonphysical_restart_removed", val.get("120ka_nonphysical_restart_removed") is True)
    ck("c1_cha2_50y_authority_preserved", val.get("C1_50y_CHA2_authority_preserved") is True)
    ck("no_canonical_catastrophes_added", int(val.get("canonical_catastrophes_added")) == 0, val.get("canonical_catastrophes_added"))
    ck("clock_biology_not_modified", val.get("biology_modified") is False)
    for i, row in enumerate(val.get("d21_windows", [])):
        ck(f"d21_window_{i}_pass", row.get("pass") is True, row)
    ck("d21_window_count_4", len(val.get("d21_windows", [])) == 4, len(val.get("d21_windows", [])))

    # Stored clock JSON must be exactly the serialization of the rebuilt clock.
    rebuilt_clock_payload = {
        "status": clock["status"],
        "age_ma": [float(x) for x in np.asarray(clock["age_ma"]).tolist()],
        "model_seconds": [int(x) for x in np.asarray(clock["model_seconds"]).tolist()],
        "intervals": list(clock["intervals"]),
        "validation": clock["validation"],
    }
    ck("clock_json_exact_rebuild", clock_disk == rebuilt_clock_payload)
    ck("clock_sha_matches_summary", hfile(clock_path) == summary.get("adaptive_clock_json_sha256"), {"actual": hfile(clock_path), "summary": summary.get("adaptive_clock_json_sha256")})
    ck("summary_clock_matches_rebuild", summary.get("adaptive_clock") == cs)
    ck("summary_binding_matches_rebuild", summary.get("binding_30ma") == binding)

    # Governance gates: R3.14 is only a binding/restart boundary.
    gov = summary.get("governance", {})
    expected_false = (
        "biology_advanced", "deep_biological_coupling", "cha1_reapplied", "lifecycle_thaw_reapplied",
        "preview_boundary_used", "richness_target_used", "guild_target_used", "cross_guild_transition_operator_activated",
    )
    for key in expected_false:
        ck(f"governance_false:{key}", gov.get(key) is False, gov.get(key))
    for key in ("exact_v061_hash_binding_required", "b1_b2_rematerialized_from_existing_authorized_equations", "c2_120ka_replay_safe_boundary_required", "adaptive_clock_is_scheduler_not_new_physics"):
        ck(f"governance_true:{key}", gov.get(key) is True, gov.get(key))

    failed = [x for x in checks if not x["pass"]]
    audit = {
        "schema": "ARCANA_R314_FORMAL_SEALED_BINDING_AUDIT_V1",
        "stage": STAGE,
        "verdict": VERDICT if not failed else "FAIL_R314_SEALED_BINDING_AUDIT",
        "checks": f"{len(checks)-len(failed)}/{len(checks)}",
        "failed": failed,
        "binding_summary_sha256": hfile(summary_path),
        "adaptive_clock_sha256": hfile(clock_path),
        "b1_sha256": hfile(b1_path),
        "b2_sha256": hfile(b2_path),
        "source_authority_manifest_sha256": hfile(source_manifest_path),
        "parent_r313": parent,
        "clock_summary": cs,
        "binding_30ma": binding,
        "interpretation_guard": {
            "biology_replay_started": False,
            "adaptive_clock_is_scheduler_not_new_physics": True,
            "production_replay_ready_does_not_mean_high_resolution_historical_paleoclimate_sealed": True,
            "c2_200_120ka_bridge_is_replay_safe_boundary_continuation_not_historical_glacial_chronology": True,
        },
        "check_rows": checks,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    if failed:
        print(json.dumps({"verdict": audit["verdict"], "checks": audit["checks"], "failed": failed[:10], "out": str(out)}, indent=2))
        return 1

    seal = {
        "schema": "ARCANA_R314_SEAL_SUMMARY_V1",
        "stage": STAGE,
        "verdict": VERDICT,
        "boundary": {
            "age_ma": 30.0,
            "event_side": "LATE_CENOZOIC_C2_PROVIDER_BOUND__BIOLOGY_NOT_ADVANCED",
            "species": int(parent["species"]),
            "components": int(parent["components"]),
            "population": float(parent["population"]),
        },
        "binding": {
            "r313_old_to_late_endpoint_identity_exact": True,
            "r314_bound_c2_endpoint_identity_exact": True,
            "v061_exact_hash_binding": True,
            "B1_B2_materialized": True,
            "C2_parent_type_guarded": True,
            "C1_cross_platform_formula_replay_gate": {"rtol": FORMULA_EQ_RTOL, "atol": FORMULA_EQ_ATOL},
        },
        "adaptive_clock": {
            "checkpoint_count": cs["checkpoint_count"],
            "interval_count": cs["interval_count"],
            "min_dt_years": cs["min_dt_years"],
            "max_dt_years": cs["max_dt_years"],
            "contains_200ka": cs["contains_200ka"],
            "contains_120ka": cs["contains_120ka"],
            "production_replay_ready": True,
            "production_replay_ready_scope": val["production_replay_ready_scope"],
        },
        "artifact_hashes": {
            "binding_summary": hfile(summary_path),
            "adaptive_clock_json": hfile(clock_path),
            "B1_boundary_npz": hfile(b1_path),
            "B2_boundary_npz": hfile(b2_path),
            "source_authority_manifest": hfile(source_manifest_path),
            "formal_audit": hfile(out),
        },
        "v061_payload_hashes": dict(r314.EXPECTED_V061_SHA256),
        "evidence": {
            "formal_audit": audit["checks"] + " PASS",
            "focused_regression_expected": "24/24 PASS",
            "biology_advanced": False,
            "30ma_environment_identity_exact": True,
        },
        "interpretation_guard": "R3.14 seals the 30 Ma environment-provider/adaptive-clock restart boundary only. C2 200-120 ka is replay-safe boundary continuation, not sealed high-resolution historical glacial chronology. Biology remains the R3.13 30 Ma state until R3.15 explicitly couples the scheduler to biological cadence.",
    }
    seal_out.write_text(json.dumps(seal, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": VERDICT, "checks": audit["checks"], "audit": str(out), "seal": str(seal_out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
