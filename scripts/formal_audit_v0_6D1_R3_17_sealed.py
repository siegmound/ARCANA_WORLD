from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import numpy as np

STAGE = "v0.6D1-R3.17"
READY_VERDICT = (
    "PASS_R317_EXACT_120KA_ENVIRONMENTAL_RESTART__"
    "R316_125KA_BIOLOGY_PRESERVED_WITH_5KYR_PENDING_EXPOSURE"
)
SEALED_VERDICT = (
    "PASS_R317_EXACT_120KA_ENVIRONMENTAL_RESTART__"
    "125KA_BIOLOGY_STATE_AND_5KYR_PENDING_EXPOSURE_SEALED"
)
ENVELOPE_SHA256 = "5b800279324afdd19279fa0c395ace822b4104155690191f81c6be884d2aeca8"
ACCUMULATOR_SHA256 = "b191faae44b4db8bc0afaaba942b0f04087758fa554c480375eb0f753ab309cc"
EXPECTED_POP = 1217.8946033288662


def hfile(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def f_eq(a: Any, b: Any, atol: float = 1e-12) -> bool:
    try:
        return abs(float(a) - float(b)) <= atol
    except Exception:
        return False


def _json_core_equal(stored: Mapping[str, Any], live: Mapping[str, Any], key: str) -> bool:
    return stored.get(key) == live.get(key)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seal-out", type=Path, required=True)
    args = ap.parse_args()

    root = args.root.resolve()
    run_dir = args.run_dir.resolve()
    out = args.out.resolve()
    seal_out = args.seal_out.resolve()
    sys.path.insert(0, str(root / "src"))

    from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
    from arcana_worldsim.scientific_engines import r317_recent_restart_sync as r317

    checks: list[dict[str, Any]] = []

    def ck(name: str, cond: bool, actual: Any = None, expected: Any = None) -> None:
        checks.append({"name": name, "pass": bool(cond), "actual": actual, "expected": expected})

    envp = run_dir / "R3_17_120KA_DUAL_CLOCK_RESTART_ENVELOPE.json"
    accp = run_dir / "R3_17_PENDING_125_TO_120KA_EXPOSURE_ACCUMULATOR.npz"
    sump = run_dir / "R3_17_EXACT_120KA_ENVIRONMENTAL_RESTART_SUMMARY.json"
    for p in (envp, accp, sump):
        ck(f"file_exists::{p.name}", p.is_file(), str(p))

    if not all(p.is_file() for p in (envp, accp, sump)):
        failed = [x for x in checks if not x["pass"]]
        audit = {
            "schema": "ARCANA_R317_FORMAL_SEALED_AUDIT_V1",
            "stage": STAGE,
            "verdict": "FAIL_R317_SEALED_AUDIT",
            "checks": f"{len(checks)-len(failed)}/{len(checks)}",
            "failed": failed,
            "check_rows": checks,
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(audit, indent=2), encoding="utf-8")
        print(json.dumps({"verdict": audit["verdict"], "checks": audit["checks"], "audit": str(out)}, indent=2))
        return 2

    env = json.loads(envp.read_text(encoding="utf-8"))
    summary = json.loads(sump.read_text(encoding="utf-8"))
    loaded_acc = r317.load_accumulator(accp)

    # Exact canonical artifact identity from the user's completed run.
    env_sha = hfile(envp)
    acc_sha = hfile(accp)
    sum_sha = hfile(sump)
    ck("restart_envelope_sha", env_sha == ENVELOPE_SHA256, env_sha, ENVELOPE_SHA256)
    ck("pending_accumulator_sha", acc_sha == ACCUMULATOR_SHA256, acc_sha, ACCUMULATOR_SHA256)

    # Summary identity and run projection.
    ck("summary_stage", summary.get("stage") == STAGE, summary.get("stage"), STAGE)
    ck("summary_schema", summary.get("schema") == r317.SUMMARY_SCHEMA, summary.get("schema"), r317.SUMMARY_SCHEMA)
    ck("summary_ready_verdict", summary.get("verdict") == READY_VERDICT, summary.get("verdict"), READY_VERDICT)
    ck("summary_physical_120ka", f_eq(summary.get("physical_restart_age_ma"), 0.120), summary.get("physical_restart_age_ma"), 0.120)
    ck("summary_biology_125ka", f_eq(summary.get("biology_state_age_ma"), 0.125), summary.get("biology_state_age_ma"), 0.125)
    ck("summary_species_134", summary.get("biology_state_species") == 134, summary.get("biology_state_species"), 134)
    ck("summary_components_295", summary.get("biology_state_components") == 295, summary.get("biology_state_components"), 295)
    ck("summary_population_exact", f_eq(summary.get("biology_state_population"), EXPECTED_POP, 1e-9), summary.get("biology_state_population"), EXPECTED_POP)
    ck("summary_biology_not_mutated", summary.get("biology_state_mutated") is False, summary.get("biology_state_mutated"), False)
    ck("summary_biology_identity_exact", summary.get("biology_state_identity_exact") is True, summary.get("biology_state_identity_exact"), True)
    ck("summary_c2_substeps_10", summary.get("environmental_c2_substeps_consumed") == 10, summary.get("environmental_c2_substeps_consumed"), 10)
    ck("summary_pending_5000y", f_eq(summary.get("environmental_years_accumulated"), 5000.0, 1e-9), summary.get("environmental_years_accumulated"), 5000.0)
    ck("summary_remaining_biology_120k", f_eq(summary.get("remaining_to_next_full_biology_boundary_years"), 120000.0, 1e-9), summary.get("remaining_to_next_full_biology_boundary_years"), 120000.0)
    ck("summary_remaining_transport_57500", f_eq(summary.get("remaining_to_next_transport_boundary_years"), 57500.0, 1e-9), summary.get("remaining_to_next_transport_boundary_years"), 57500.0)
    support = summary.get("support_transition_diagnostic", {})
    ck("support_lost_population_zero", f_eq(support.get("parent_population_mass_on_cells_inaccessible_at_120ka"), 0.0, 1e-12), support.get("parent_population_mass_on_cells_inaccessible_at_120ka"), 0.0)
    ck("support_no_reconciliation", support.get("support_reconciliation_applied_in_r317") is False, support.get("support_reconciliation_applied_in_r317"), False)

    # Exact envelope semantics.
    ck("envelope_schema", env.get("schema") == r317.ENVELOPE_SCHEMA, env.get("schema"), r317.ENVELOPE_SCHEMA)
    ck("envelope_stage", env.get("stage") == STAGE, env.get("stage"), STAGE)
    ck("envelope_physical_120", f_eq(env.get("physical_restart_age_ma"), 0.120), env.get("physical_restart_age_ma"), 0.120)
    ck("envelope_biology_125", f_eq(env.get("biology_state_age_ma"), 0.125), env.get("biology_state_age_ma"), 0.125)
    ck("envelope_source_unmodified", env.get("biology_state_source") == "R3.16_SEALED_125KA_CHECKPOINT_UNMODIFIED", env.get("biology_state_source"))
    ck("envelope_not_mutated", env.get("biology_state_mutated") is False, env.get("biology_state_mutated"), False)
    ck("envelope_not_relabelled", env.get("biology_state_relabelled_to_120ka") is False, env.get("biology_state_relabelled_to_120ka"), False)

    phase = env.get("phase", {})
    phase_expected = {
        "physical_age_ma": 0.120,
        "biology_state_age_ma": 0.125,
        "elapsed_since_last_full_biology_boundary_years": 5000.0,
        "remaining_to_next_full_biology_boundary_years": 120000.0,
        "next_full_biology_boundary_age_ma": 0.0,
        "elapsed_since_last_transport_boundary_years": 5000.0,
        "remaining_to_next_transport_boundary_years": 57500.0,
        "next_transport_boundary_age_ma": 0.0625,
    }
    for key, expected in phase_expected.items():
        ck(f"phase::{key}", f_eq(phase.get(key), expected, 1e-9), phase.get(key), expected)
    for key in (
        "gene_flow_due_at_120ka", "transport_due_at_120ka", "lifecycle_gate_due_at_120ka",
        "speciation_gate_due_at_120ka", "extinction_gate_due_at_120ka", "pair_clock_advanced_to_120ka",
        "demography_advanced_to_120ka", "selection_advanced_to_120ka", "variance_advanced_to_120ka",
    ):
        ck(f"phase_false::{key}", phase.get(key) is False, phase.get(key), False)
    ck("phase_semantics", phase.get("semantics") == "DUAL_CLOCK_RESTART_ENVIRONMENT_AT_120KA_WITH_SEALED_BIOLOGY_STATE_CARRIED_FROM_125KA", phase.get("semantics"))

    er = env.get("environmental_restart", {})
    ck("restart_boundary_true", er.get("restart_boundary_at_120ka") is True, er.get("restart_boundary_at_120ka"), True)
    ck("restart_replay_safe", er.get("replay_safe_boundary_continuation") is True, er.get("replay_safe_boundary_continuation"), True)
    ck("no_pre120_historical_claim", er.get("pre_120ka_historical_glacial_chronology_claimed") is False, er.get("pre_120ka_historical_glacial_chronology_claimed"), False)

    pending = env.get("pending_exposure", {})
    ck("pending_duration_5000", f_eq(pending.get("duration_years"), 5000.0, 1e-9), pending.get("duration_years"), 5000.0)
    ck("pending_segments_10", pending.get("segment_count") == 10, pending.get("segment_count"), 10)
    ck("pending_nodes_11", pending.get("node_count") == 11, pending.get("node_count"), 11)
    ck("pending_all_segments_500y", pending.get("all_segments_500y") is True, pending.get("all_segments_500y"), True)
    ck("pending_rule", pending.get("averaging_rule") == "TRAPEZOID_INTEGRAL_ON_R314_C2_500Y_PARTITION", pending.get("averaging_rule"))
    ck("pending_role", pending.get("accumulator_role") == "PENDING_FIRST_5KYR_OF_THE_125KA_TO_0KA_SEALED_BIOLOGY_MACROSTEP", pending.get("accumulator_role"))
    ck("pending_no_biology_mutation", pending.get("biological_state_mutated") is False, pending.get("biological_state_mutated"), False)
    ck("pending_forage_closure", math.isfinite(float(pending.get("total_forage_average_closure_max_abs", float("inf")))) and float(pending.get("total_forage_average_closure_max_abs")) <= 1e-12, pending.get("total_forage_average_closure_max_abs"))
    ck("pending_endpoint_forage_closure", math.isfinite(float(pending.get("endpoint_total_forage_closure_max_abs", float("inf")))) and float(pending.get("endpoint_total_forage_closure_max_abs")) <= 1e-12, pending.get("endpoint_total_forage_closure_max_abs"))

    gov = env.get("governance", {})
    for key in (
        "biology_cadence_changed", "transport_cadence_changed", "gene_flow_step_cadence_changed",
        "lifecycle_gate_cadence_changed", "partial_biology_step_executed", "adaptive_clock_used_as_biology_timestep",
        "deep_biological_coupling", "scientific_parameter_changes", "richness_target_used", "human_lineage_target_used",
    ):
        ck(f"governance_false::{key}", gov.get(key) is False, gov.get(key), False)
    ck("governance_exposure_accumulated", gov.get("environmental_exposure_accumulated_without_biology_update") is True, gov.get("environmental_exposure_accumulated_without_biology_update"), True)

    # Stored accumulator schema/content.
    ck("acc_duration_5000", f_eq(loaded_acc.get("duration_years"), 5000.0), loaded_acc.get("duration_years"), 5000.0)
    ck("acc_older_125ka", f_eq(loaded_acc.get("older_age_ma"), 0.125), loaded_acc.get("older_age_ma"), 0.125)
    ck("acc_younger_120ka", f_eq(loaded_acc.get("younger_age_ma"), 0.120), loaded_acc.get("younger_age_ma"), 0.120)
    ck("acc_fields_exact", set(loaded_acc.get("integrals", {})) == set(r317.r316.AVERAGED_FIELDS), sorted(loaded_acc.get("integrals", {})), sorted(r317.r316.AVERAGED_FIELDS))
    for key in r317.r316.AVERAGED_FIELDS:
        arr = np.asarray(loaded_acc["integrals"][key], dtype=float)
        ck(f"acc_finite::{key}", bool(np.isfinite(arr).all()))

    # Parent authority + independent live replay of the complete R3.17 operation.
    parent = r317.validate_parent_r316_authority(root)
    st = parent["state"]
    a1 = parent["a1"]
    c2 = parent["c2"]
    clock = parent["clock"]
    ck("parent_state_125ka", f_eq(st.age_ma, 0.125), st.age_ma, 0.125)
    ck("parent_state_species_134", len(set(st.current_species)) == 134, len(set(st.current_species)), 134)
    ck("parent_state_components_295", len(st.component_ids) == 295, len(st.component_ids), 295)
    ck("parent_state_population_exact", f_eq(float(st.pop.sum()), EXPECTED_POP, 1e-9), float(st.pop.sum()), EXPECTED_POP)

    before = deepcopy(st)
    live_env, live_acc = r317.build_restart_envelope(st, a1, c2, clock, r317.R317Config())
    state_cmp = r38.compare_runtime_states(before, st, atol=0.0)
    ck("independent_replay_parent_state_unchanged", state_cmp.get("equivalent") is True, state_cmp.get("equivalent"), True)

    for key in (
        "schema", "stage", "physical_restart_age_ma", "biology_state_age_ma", "biology_state_source",
        "biology_state_mutated", "biology_state_relabelled_to_120ka", "phase", "environmental_restart",
        "pending_exposure", "support_transition_diagnostic", "governance",
    ):
        ck(f"independent_envelope_core::{key}", _json_core_equal(env, live_env, key), env.get(key), live_env.get(key))

    ck("independent_acc_field_set", set(live_acc) == set(loaded_acc["integrals"]), sorted(live_acc), sorted(loaded_acc["integrals"]))
    for key in r317.r316.AVERAGED_FIELDS:
        a = np.asarray(live_acc[key], dtype=float)
        b = np.asarray(loaded_acc["integrals"][key], dtype=float)
        ck(f"independent_acc_shape::{key}", a.shape == b.shape, a.shape, b.shape)
        ck(f"independent_acc_exact::{key}", np.array_equal(a, b), float(np.max(np.abs(a-b))) if a.shape == b.shape and a.size else None, 0.0)

    live_support = live_env.get("support_transition_diagnostic", {})
    ck("independent_lost_population_zero", f_eq(live_support.get("parent_population_mass_on_cells_inaccessible_at_120ka"), 0.0, 1e-12), live_support.get("parent_population_mass_on_cells_inaccessible_at_120ka"), 0.0)

    # Artifact pointers in the canonical summary/envelope must bind to the exact received files.
    sa = summary.get("artifacts", {})
    ck("summary_env_sha_pointer", sa.get("restart_envelope_sha256") == ENVELOPE_SHA256, sa.get("restart_envelope_sha256"), ENVELOPE_SHA256)
    ck("summary_acc_sha_pointer", sa.get("pending_exposure_accumulator_sha256") == ACCUMULATOR_SHA256, sa.get("pending_exposure_accumulator_sha256"), ACCUMULATOR_SHA256)
    ck("summary_acc_roundtrip", sa.get("accumulator_roundtrip_exact") is True, sa.get("accumulator_roundtrip_exact"), True)
    ea = env.get("pending_exposure_artifact", {})
    ck("envelope_acc_sha_pointer", ea.get("sha256") == ACCUMULATOR_SHA256, ea.get("sha256"), ACCUMULATOR_SHA256)
    ck("envelope_acc_schema_pointer", ea.get("schema") == r317.ACCUMULATOR_SCHEMA, ea.get("schema"), r317.ACCUMULATOR_SCHEMA)
    ck("envelope_acc_duration_pointer", f_eq(ea.get("duration_years"), 5000.0), ea.get("duration_years"), 5000.0)

    # Next-stage constraints stay fail-closed.
    nxt = summary.get("next_stage_constraint", {})
    for key in (
        "r318_must_combine_pending_5k_exposure_with_120ka_to_0_exposure_before_one_full_125k_biology_step",
        "r318_must_not_treat_120ka_as_new_biology_cadence_origin",
        "r318_must_not_reapply_gene_flow_before_the_next_full_biology_boundary",
        "r318_must_preserve_transport_phase_with_next_boundary_at_62p5ka",
    ):
        ck(f"next_stage_constraint::{key}", nxt.get(key) is True, nxt.get(key), True)

    failed = [x for x in checks if not x["pass"]]
    verdict = SEALED_VERDICT if not failed else "FAIL_R317_SEALED_AUDIT"
    audit = {
        "schema": "ARCANA_R317_FORMAL_SEALED_AUDIT_V1",
        "stage": STAGE,
        "verdict": verdict,
        "checks": f"{len(checks)-len(failed)}/{len(checks)}",
        "failed": failed,
        "decision": "EXACT_120KA_ENVIRONMENTAL_RESTART_WITH_125KA_BIOLOGY_STATE_AND_5KYR_PENDING_EXPOSURE_SEALED",
        "boundary": {
            "physical_environment_age_ma": 0.120,
            "biology_state_age_ma": 0.125,
            "species": 134,
            "components": 295,
            "population": EXPECTED_POP,
            "pending_environmental_years": 5000.0,
            "remaining_to_next_full_biology_boundary_years": 120000.0,
            "remaining_to_next_transport_boundary_years": 57500.0,
            "population_mass_on_cells_inaccessible_at_120ka": 0.0,
        },
        "canonical_artifacts": {
            "restart_envelope": str(envp),
            "restart_envelope_sha256": env_sha,
            "pending_exposure_accumulator": str(accp),
            "pending_exposure_accumulator_sha256": acc_sha,
            "summary": str(sump),
            "summary_sha256": sum_sha,
        },
        "independent_replay": {
            "enabled": True,
            "biology_state_identity_exact": bool(state_cmp.get("equivalent")),
            "accumulator_array_identity_exact": not any((x["name"].startswith("independent_acc_exact::") and not x["pass"]) for x in checks),
            "envelope_core_identity_exact": not any((x["name"].startswith("independent_envelope_core::") and not x["pass"]) for x in checks),
        },
        "scientific_parameter_changes": False,
        "biology_cadence_changes": False,
        "deep_biological_coupling": False,
        "check_rows": checks,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    if not failed:
        seal = {
            "schema": "ARCANA_R317_SEAL_SUMMARY_V1",
            "stage": STAGE,
            "verdict": SEALED_VERDICT,
            "formal_audit": str(out),
            "formal_audit_sha256": hfile(out),
            "formal_audit_checks": audit["checks"],
            "boundary": audit["boundary"],
            "canonical_artifacts": audit["canonical_artifacts"],
            "parent_authority": {
                "stage": "v0.6D1-R3.16",
                "r316_seal_sha256": parent["r316_seal_sha256"],
                "r316_audit_sha256": parent["r316_audit_sha256"],
                "r316_summary_sha256": parent["r316_summary_sha256"],
                "r316_checkpoint_json_sha256": parent["checkpoint_json_sha256"],
                "r316_checkpoint_npz_sha256": parent["checkpoint_npz_sha256"],
            },
            "independent_replay": audit["independent_replay"],
            "governance": {
                "physical_restart_at_120ka_sealed": True,
                "biology_state_remains_at_125ka": True,
                "pending_5k_environmental_exposure_sealed": True,
                "partial_biology_step_executed": False,
                "biology_cadence_changed": False,
                "transport_cadence_changed": False,
                "gene_flow_cadence_changed": False,
                "deep_biological_coupling": False,
                "scientific_parameter_changes": False,
            },
            "next": "v0.6D1-R3.18 — 120ka→0 Recent H0 Exposure Completion & 125ka→0 Fixed-Biology Macrostep Closure",
        }
        seal_out.write_text(json.dumps(seal, indent=2), encoding="utf-8")

    print(json.dumps({"verdict": verdict, "checks": audit["checks"], "audit": str(out), "seal": str(seal_out) if not failed else None}, indent=2))
    try:
        if hasattr(a1, "close"):
            a1.close()
    except Exception:
        pass
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
