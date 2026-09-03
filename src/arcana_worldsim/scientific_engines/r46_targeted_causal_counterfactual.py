from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import ast
import json
import math
import re
import time

import numpy as np

from . import r38_restartable_checkpoint as r38
from . import r311_postcha1_recovery as r311
from . import r312_postcha1_diversity_recovery as r312

STAGE = "v0.6D1-R4.6"
R45_SEALED = "PASS_R45_EARLIEST_AUTHORITY_CAUSAL_DIAGNOSIS_RECALIBRATION_AND_REPLAY_PLAN_SEALED"
R45_COMPLETE = "PASS_R45_EARLIEST_AUTHORITY_CAUSAL_DIAGNOSIS_AND_REPLAY_PLANNING_COMPLETE"
COMPLETE = "PASS_R46_TARGETED_CAUSAL_COUNTERFACTUAL_AND_FORCING_PARITY_DIAGNOSIS_COMPLETE"
SEALED = "PASS_R46_TARGETED_R311_CAUSAL_COUNTERFACTUAL_AND_R43_FORCING_PARITY_AUDIT_SEALED"
BLOCKED = "BLOCKED_R46_PARENT_OR_COUNTERFACTUAL_FAILURE"

CFG_REL = Path("configs/world1_r46_targeted_causal_counterfactual_v0_6D1_R4_6.json")
R45_SEAL_REL = Path("outputs/v0_6D1_R4_5_SEAL/R4_5_FINAL_SEAL_AUDIT.json")
R45_AUDIT_REL = Path("outputs/v0_6D1_R4_5/R4_5_INTEGRATED_AUDIT.json")
R45_DIAG_REL = Path("outputs/v0_6D1_R4_5/R4_5_STRUCTURAL_DISAGREEMENT_DIAGNOSIS.json")
R45_GATE_REL = Path("outputs/v0_6D1_R4_5/R4_5_REPLAY_AUTHORIZATION_GATE.json")
R43_CDMETA_REL = Path("benchmarks/r43/cdmetapop_r43.py")
R43_JOBS_REL = Path("outputs/v0_6D1_R4_3/jobs")
A1_REL = Path("references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz")
META_REL = Path("references/v0_6D1_R3/D1_SPECIES_METADATA.json")
OUT_REL = Path("outputs/v0_6D1_R4_6")
SEAL_REL = Path("outputs/v0_6D1_R4_6_SEAL/R4_6_FINAL_SEAL_AUDIT.json")


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "pass": bool(self.passed), "detail": self.detail}


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path: str | Path, obj: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def finite(x: Any) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _metadata_rows(root: Path) -> list[dict[str, Any]]:
    d = load_json(root / META_REL)
    return d["species"] if isinstance(d, dict) and "species" in d else d


def _extract_authorized_case(root: Path, cfg: dict[str, Any]) -> tuple[dict[str, Any], list[Check]]:
    seal = load_json(root / R45_SEAL_REL) if (root / R45_SEAL_REL).exists() else {}
    audit = load_json(root / R45_AUDIT_REL) if (root / R45_AUDIT_REL).exists() else {}
    diag = load_json(root / R45_DIAG_REL) if (root / R45_DIAG_REL).exists() else {}
    gate = load_json(root / R45_GATE_REL) if (root / R45_GATE_REL).exists() else {}
    expected = cfg["authorized_case"]
    robust = [d for d in diag.get("structural_diagnoses", []) if d.get("robust_structural_disagreement") is True and d.get("diagnostic_counterfactual_authorized") is True]
    row_diags = [r for d in robust for r in d.get("row_diagnoses", []) if r.get("diagnosis_class") == "ROBUST_PRIMARY_STRUCTURAL_DISAGREEMENT"]
    case = {
        "window_id": robust[0].get("window_id") if len(robust) == 1 else None,
        "domain": robust[0].get("domain") if len(robust) == 1 else None,
        "earliest_boundary": robust[0].get("earliest_affected_authority_candidate") if len(robust) == 1 else None,
        "engine": row_diags[0].get("engine") if len(row_diags) == 1 else None,
        "job_id": row_diags[0].get("job_id") if len(row_diags) == 1 else None,
        "r45_row_diagnosis": row_diags[0] if len(row_diags) == 1 else None,
    }
    checks = [
        Check("parent_r45_seal_present", (root / R45_SEAL_REL).exists(), str(R45_SEAL_REL)),
        Check("parent_r45_sealed", seal.get("status") == R45_SEALED, seal.get("status")),
        Check("parent_r45_diagnosis_complete", audit.get("status") == R45_COMPLETE, audit.get("status")),
        Check("parent_r45_authorized_diagnostic_counterfactual", gate.get("diagnostic_counterfactual_authorized") is True, gate.get("diagnostic_counterfactual_authorized")),
        Check("parent_r45_canonical_replay_not_authorized", gate.get("canonical_replay_authorized") is False, gate.get("canonical_replay_authorized")),
        Check("exactly_one_robust_authorized_structural_cell", len(robust) == 1, len(robust)),
        Check("exactly_one_robust_primary_row", len(row_diags) == 1, len(row_diags)),
        Check("authorized_case_matches_frozen_r46_scope", all(case.get(k) == expected.get(k) for k in ("window_id", "domain", "earliest_boundary", "engine", "job_id")), {"observed": {k: case.get(k) for k in ("window_id", "domain", "earliest_boundary", "engine", "job_id")}, "expected": {k: expected.get(k) for k in ("window_id", "domain", "earliest_boundary", "engine", "job_id")}}),
        Check("r45_next_action_matches_r46", gate.get("next_action") == cfg.get("required_parent_next_action"), gate.get("next_action")),
    ]
    return case, checks


def _driver_tokens_from_cdmetapop_source(text: str) -> set[str]:
    """Return driver keys explicitly read from the local ``d`` driver mapping.

    This is deliberately AST-based so comments/docstrings do not count as
    consumed forcing. The R4.3 adapter binds ``d = c['engine_input']['drivers']``.
    """
    tree = ast.parse(text)
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "d":
            sl = node.slice
            if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                out.add(sl.value)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "d" and node.func.attr == "get" and node.args:
                a0 = node.args[0]
                if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                    out.add(a0.value)
    return out


def audit_cdmetapop_forcing_parity(root: Path, job_id: str, cfg: dict[str, Any]) -> dict[str, Any]:
    job_path = root / R43_JOBS_REL / job_id / "JOB_CONTRACT.json"
    job = load_json(job_path)
    src_path = root / R43_CDMETA_REL
    src = src_path.read_text(encoding="utf-8-sig")
    consumed = _driver_tokens_from_cdmetapop_source(src)
    drivers = dict(job.get("engine_input", {}).get("drivers", {}))
    coverage = {k: {"configured_value": v, "explicitly_consumed_by_adapter": k in consumed} for k, v in sorted(drivers.items())}

    env_change = finite(drivers.get("normalized_environment_change"))
    env_change_nonzero = env_change is not None and abs(env_change) > 1e-12
    environment_change_omitted = env_change_nonzero and "normalized_environment_change" not in consumed

    h0 = finite(drivers.get("normalized_habitat_fraction_start"))
    h1 = finite(drivers.get("normalized_habitat_fraction_end"))
    habitat_end_changed = h0 is not None and h1 is not None and abs(h1 - h0) > 1e-12
    habitat_end_omitted = habitat_end_changed and "normalized_habitat_fraction_end" not in consumed

    dynamic_end_tokens = {
        "normalized_environment_change",
        "normalized_habitat_fraction_end",
        "reference_population_ratio",
        "reference_population_end",
        "reference_abundance_support_ratio",
        "normalized_reference_population_change",
    }
    dynamic_end_forcing_consumed = bool(consumed & dynamic_end_tokens)
    source_gap = bool(environment_change_omitted or habitat_end_omitted or not dynamic_end_forcing_consumed)
    affected = list(cfg.get("r47_symmetry_policy", {}).get("affected_frozen_jobs", []))
    domain_row = next((x for x in job.get("unit_mapping", {}).get("domain_mapping", []) if x.get("domain") == "population_persistence"), {})
    return {
        "stage": STAGE,
        "audit": "R43_CDMETAPOP_FORCING_PARITY_SOURCE_AUDIT",
        "job_id": job_id,
        "adapter_source": str(R43_CDMETA_REL),
        "driver_application_declared_by_r43": "start_state_K_N0_and_migration_probability_on_isolated_pinned_generic_patch_network",
        "configured_drivers": coverage,
        "explicit_config_keys_consumed": sorted(consumed),
        "normalized_environment_change_nonzero": env_change_nonzero,
        "normalized_environment_change_value": env_change,
        "normalized_environment_change_explicitly_consumed": "normalized_environment_change" in consumed,
        "habitat_fraction_start": h0,
        "habitat_fraction_end": h1,
        "habitat_fraction_end_changed": habitat_end_changed,
        "normalized_habitat_fraction_end_explicitly_consumed": "normalized_habitat_fraction_end" in consumed,
        "dynamic_end_forcing_explicitly_consumed": dynamic_end_forcing_consumed,
        "start_state_only_parameterization_detected": not dynamic_end_forcing_consumed,
        "population_persistence_authority_role": domain_row.get("authority_role"),
        "population_persistence_comparability": domain_row.get("comparability_class"),
        "forcing_coverage_gap_confirmed": source_gap,
        "finding": "R43_CDMETAPOP_POPULATION_PERSISTENCE_DYNAMIC_FORCING_COVERAGE_GAP_CONFIRMED" if source_gap else "NO_R43_CDMETAPOP_FORCING_COVERAGE_GAP_DETECTED",
        "interpretation_guard": "This is an adapter/input-semantic coverage finding. It is not a scientific verdict against CDMetaPOP and does not prove the ARCANA R3.11 mechanics correct or incorrect.",
        "shared_adapter_symmetry_required": True,
        "symmetrically_affected_frozen_jobs_if_adapter_semantics_change": affected,
        "canonical_state_changed": False,
    }


def canonical_forcing_audit(root: Path, job_id: str) -> dict[str, Any]:
    job = load_json(root / R43_JOBS_REL / job_id / "JOB_CONTRACT.json")
    start_age = float(job["window"]["start_ma"])
    end_age = float(job["window"]["end_ma"])
    with np.load(root / A1_REL, allow_pickle=False) as a1:
        # Use the same barrier/environment provider used by R3.11/R3.12.
        bcfg = r38.r34.barrier_cfg(r311.R311Config())
        e0 = r38.bp.environment_at(start_age, a1, bcfg)
        e1 = r38.bp.environment_at(end_age, a1, bcfg)
        def s(env: dict[str, Any]) -> dict[str, float]:
            return {
                "reference_population_total": float(np.asarray(env["reference_population"], float).sum()),
                "reference_capacity_total": float(np.asarray(env["reference_capacity"], float).sum()),
                "mean_total_edible_forage": float(np.asarray(env["total_edible_forage"], float).mean()),
                "mean_land_support": float(np.asarray(env["land_support"], float).mean()),
                "mean_temperature_c": float(np.asarray(env["temperature_c"], float).mean()),
                "mean_aridity_index": float(np.asarray(env["aridity_index"], float).mean()),
            }
        x0, x1 = s(e0), s(e1)
    def ratio(a: float, b: float) -> float | None:
        return None if abs(a) <= 1e-15 else b / a
    ratios = {
        "reference_population_ratio": ratio(x0["reference_population_total"], x1["reference_population_total"]),
        "reference_capacity_ratio": ratio(x0["reference_capacity_total"], x1["reference_capacity_total"]),
        "edible_forage_ratio": ratio(x0["mean_total_edible_forage"], x1["mean_total_edible_forage"]),
        "land_support_ratio": ratio(x0["mean_land_support"], x1["mean_land_support"]),
    }
    deltas = {k.replace("_total", "").replace("mean_", "") + "_delta": x1[k] - x0[k] for k in x0}
    canonical_ratio = finite(job.get("comparison_target", {}).get("derived_end_response", {}).get("population_ratio"))
    ref_ratio = ratio(x0["reference_population_total"], x1["reference_population_total"])
    return {
        "stage": STAGE,
        "audit": "CANONICAL_POST_CHA1_EXOGENOUS_FORCING_AUDIT",
        "start_age_ma": start_age,
        "end_age_ma": end_age,
        "start": x0,
        "end": x1,
        "ratios": ratios,
        "deltas": deltas,
        "arcana_realized_population_ratio": canonical_ratio,
        "a1_reference_population_ratio": ref_ratio,
        "absolute_ratio_difference_arcana_vs_a1_reference_population": None if canonical_ratio is None or ref_ratio is None else abs(canonical_ratio - ref_ratio),
        "r43_configured_normalized_environment_change": finite(job.get("engine_input", {}).get("drivers", {}).get("normalized_environment_change")),
        "interpretation_guard": "Reference-population tracking is causal evidence about the ARCANA forcing path, not a requirement that CDMetaPOP raw patch abundance equal ARCANA abundance.",
    }


def _direction_ratio(x: float, neutral_factor: float = 1.05) -> int:
    if x > neutral_factor:
        return 1
    if x < 1.0 / neutral_factor:
        return -1
    return 0


def execute_reference_population_hold(root: Path, job_id: str) -> dict[str, Any]:
    """Execute the R4.5-authorized diagnostic branch only; never serialize canonical R3 checkpoints."""
    job = load_json(root / R43_JOBS_REL / job_id / "JOB_CONTRACT.json")
    start_age = float(job["window"]["start_ma"])
    end_age = float(job["window"]["end_ma"])
    if abs(start_age - 65.5) > 1e-12 or abs(end_age - 55.0) > 1e-12:
        raise RuntimeError("R4.6 authorized counterfactual is exactly 65.5->55 Ma")
    parent = r311.validate_parent_r310_authority(root)
    parent_state = parent["state"]
    rows = _metadata_rows(root)
    t0 = time.time()
    original_environment_at = r38.bp.environment_at
    with np.load(root / A1_REL, allow_pickle=False) as a1:
        bcfg = r38.r34.barrier_cfg(r311.R311Config())
        start_env = original_environment_at(start_age, a1, bcfg)
        fixed_reference_population = np.asarray(start_env["reference_population"], dtype=float).copy()

        def held_environment_at(age_ma: float, a1_obj: Any, cfg_obj: Any) -> dict[str, Any]:
            env = original_environment_at(age_ma, a1_obj, cfg_obj)
            env["reference_population"] = fixed_reference_population.copy()
            return env

        r38.bp.environment_at = held_environment_at
        try:
            cfg11 = r311.R311Config()
            state61, records11, thaw = r311.run_recovery(parent_state, a1, rows, cfg11, end_age_ma=61.0)
            cfg12 = r312.R312Config()
            state55, records12 = r312.run_diversity_recovery(state61, a1, rows, cfg12, end_age_ma=55.0)
        finally:
            r38.bp.environment_at = original_environment_at

    start_population = float(parent_state.pop.sum())
    pop61 = float(state61.pop.sum())
    pop55 = float(state55.pop.sum())
    cf_ratio = pop55 / start_population
    canonical_ratio = float(job["comparison_target"]["derived_end_response"]["population_ratio"])
    inv = r312.invariant_report(state55, rows, r312.R312Config())
    delta_events_11 = r311.delta_event_counts(parent_state, state61)
    delta_events_12 = r312.delta_event_counts(state61, state55)
    clipping11 = sum(int(r.get("clipping_count", 0)) for r in records11)
    clipping12 = sum(int(r.get("clipping_count", 0)) for r in records12)
    external_direction = None
    try:
        d = load_json(root / R45_DIAG_REL)
        row = d["structural_diagnoses"][0]["row_diagnoses"][0]
        external_direction = row.get("external_direction")
    except Exception:
        pass
    toward_external = None
    if external_direction in (-1, 1):
        toward_external = ((cf_ratio - canonical_ratio) * int(external_direction)) > 0
    return {
        "stage": STAGE,
        "counterfactual_id": "DIAGNOSTIC_ONLY_REFERENCE_POPULATION_HOLD",
        "status": "PASS_R46_DIAGNOSTIC_COUNTERFACTUAL_EXECUTED" if clipping11 == 0 and clipping12 == 0 else "BLOCKED_R46_COUNTERFACTUAL_NUMERICAL_CLIPPING",
        "start_age_ma": start_age,
        "r311_boundary_age_ma": 61.0,
        "end_age_ma": end_age,
        "wall_seconds": time.time() - t0,
        "ordinary_steps_r311": len(records11),
        "ordinary_steps_r312_to_55ma": len(records12),
        "population": {
            "start_65p5_ma": start_population,
            "counterfactual_61_ma": pop61,
            "counterfactual_55_ma": pop55,
            "counterfactual_65p5_to_55_ratio": cf_ratio,
            "canonical_65p5_to_55_ratio": canonical_ratio,
            "counterfactual_minus_canonical_ratio": cf_ratio - canonical_ratio,
            "canonical_direction_5pct_band": _direction_ratio(canonical_ratio),
            "counterfactual_direction_5pct_band": _direction_ratio(cf_ratio),
            "r45_external_direction": external_direction,
            "counterfactual_moves_toward_external_direction": toward_external,
        },
        "event_counts_delta": {"r311_65p5_to_61": delta_events_11, "r312_61_to_55": delta_events_12},
        "numerical_invariants_at_55ma": inv,
        "clipping_contacts": {"r311": clipping11, "r312_to_55": clipping12},
        "intervention": {
            "held_field": "env.reference_population",
            "held_at_age_ma": start_age,
            "all_other_environment_fields_dynamic": True,
            "all_r311_r312_scientific_parameters_unchanged": True,
            "canonical_checkpoint_written": False,
        },
        "canonical_state_changed": False,
        "canonical_replay_authorized": False,
        "interpretation_guard": "This branch measures sensitivity to the canonical reference-population forcing path. It is not a replacement history and does not authorize changing A1 or R3.11.",
    }


def _counterfactual_checks(cf: dict[str, Any]) -> list[Check]:
    inv = cf.get("numerical_invariants_at_55ma", {})
    return [
        Check("counterfactual_execution_pass", cf.get("status") == "PASS_R46_DIAGNOSTIC_COUNTERFACTUAL_EXECUTED", cf.get("status")),
        Check("counterfactual_exact_65p5_to_55_window", abs(float(cf.get("start_age_ma", -1)) - 65.5) <= 1e-12 and abs(float(cf.get("end_age_ma", -1)) - 55.0) <= 1e-12),
        Check("counterfactual_expected_ordinary_step_count", int(cf.get("ordinary_steps_r311", -1)) == 36 and int(cf.get("ordinary_steps_r312_to_55ma", -1)) == 48, {"r311": cf.get("ordinary_steps_r311"), "r312_to_55": cf.get("ordinary_steps_r312_to_55ma")}),
        Check("counterfactual_zero_clipping", sum(int(v) for v in cf.get("clipping_contacts", {}).values()) == 0, cf.get("clipping_contacts")),
        Check("counterfactual_population_nonnegative", finite(inv.get("population_min")) is not None and float(inv.get("population_min")) >= -1e-14, inv.get("population_min")),
        Check("counterfactual_no_population_on_inaccessible_cells", finite(inv.get("population_on_inaccessible_cells")) is not None and abs(float(inv.get("population_on_inaccessible_cells"))) <= 1e-12, inv.get("population_on_inaccessible_cells")),
        Check("counterfactual_q_ceiling_preserved", finite(inv.get("q_max")) is not None and finite(inv.get("q_ceiling")) is not None and float(inv.get("q_max")) <= float(inv.get("q_ceiling")) + 1e-12, {"q_max": inv.get("q_max"), "q_ceiling": inv.get("q_ceiling")}),
        Check("counterfactual_diagnostic_only_no_canonical_write", cf.get("canonical_state_changed") is False and cf.get("canonical_replay_authorized") is False and cf.get("intervention", {}).get("canonical_checkpoint_written") is False),
    ]


def run(root: Path, execute_counterfactual: bool = True) -> tuple[dict[str, Any], list[Check]]:
    root = Path(root).resolve()
    cfg = load_json(root / CFG_REL)
    case, checks = _extract_authorized_case(root, cfg)
    checks += [
        Check("r46_policy_not_result_selected", cfg.get("policy_freeze", {}).get("result_selected") is False),
        Check("canonical_state_unchanged_by_contract", cfg.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized_by_contract", cfg.get("canonical_replay_authorized") is False),
        Check("canonical_parameter_change_not_authorized", cfg.get("canonical_parameter_change_authorized") is False),
        Check("deep_off", cfg.get("deep_biological_coupling") is False),
        Check("majority_vote_forbidden", cfg.get("majority_vote") is False),
        Check("cdmetapop_adapter_source_present", (root / R43_CDMETA_REL).exists(), str(R43_CDMETA_REL)),
        Check("authorized_job_contract_present", bool(case.get("job_id")) and (root / R43_JOBS_REL / str(case.get("job_id")) / "JOB_CONTRACT.json").exists(), case.get("job_id")),
        Check("a1_reference_present", (root / A1_REL).exists(), str(A1_REL)),
    ]
    if not all(c.passed for c in checks):
        out = {"stage": STAGE, "status": BLOCKED, "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks), "checks": [c.to_dict() for c in checks], "canonical_state_changed": False}
        write_json(root / OUT_REL / "R4_6_INTEGRATED_AUDIT.json", out)
        return out, checks

    job_id = str(case["job_id"])
    parity = audit_cdmetapop_forcing_parity(root, job_id, cfg)
    forcing = canonical_forcing_audit(root, job_id)
    checks += [
        Check("population_persistence_is_primary_cdmetapop_authority", parity.get("population_persistence_authority_role") == "PRIMARY", parity.get("population_persistence_authority_role")),
        Check("population_persistence_was_declared_normalizable", parity.get("population_persistence_comparability") == "NORMALIZABLE", parity.get("population_persistence_comparability")),
        Check("r43_cdmetapop_forcing_parity_audited", isinstance(parity.get("configured_drivers"), dict) and bool(parity.get("configured_drivers"))),
    ]

    cf: dict[str, Any]
    if execute_counterfactual:
        cf = execute_reference_population_hold(root, job_id)
        checks += _counterfactual_checks(cf)
    else:
        cf = {"stage": STAGE, "counterfactual_id": "DIAGNOSTIC_ONLY_REFERENCE_POPULATION_HOLD", "status": "PREPARED_NOT_EXECUTED", "canonical_state_changed": False, "canonical_replay_authorized": False}

    source_gap = parity.get("forcing_coverage_gap_confirmed") is True
    next_action = (
        "BUILD_R47_CDMETAPOP_FORCING_PARITY_REPAIR_OR_COMPARABILITY_DOWNGRADE_AND_SYMMETRIC_REEXECUTION"
        if source_gap
        else "BUILD_R47_R311_INTERNAL_CAUSAL_REVIEW_WITH_COUNTERFACTUAL_EVIDENCE"
    )
    conclusion = {
        "stage": STAGE,
        "authorized_structural_case": {k: case.get(k) for k in ("window_id", "domain", "earliest_boundary", "engine", "job_id")},
        "adapter_forcing_parity_finding": parity.get("finding"),
        "adapter_forcing_coverage_gap_confirmed": source_gap,
        "counterfactual_status": cf.get("status"),
        "counterfactual_population_response": cf.get("population"),
        "causal_interpretation": (
            "R4.3 CDMetaPOP population-persistence evidence for J09 used a common adapter that parameterized only the START-state patch K/N0 and migration/gene-flow controls; it did not explicitly consume the nonzero normalized_environment_change or the changed normalized_habitat_fraction_end. The R3.11 reference-population-hold branch is preserved as diagnostic sensitivity evidence. Repair or comparability downgrade of the shared CDMetaPOP adapter must precede any canonical R3.11 recalibration decision."
            if source_gap else
            "No adapter forcing-coverage gap was detected by the frozen R4.6 source audit. Preserve the diagnostic counterfactual and proceed to an R3.11-internal causal review without automatic retuning."
        ),
        "canonical_r311_recalibration_authorized": False,
        "canonical_replay_authorized": False,
        "canonical_state_changed": False,
        "next_action": next_action,
    }

    # A diagnosis stage may SEALED with a confirmed adapter coverage gap; the seal means the causal audit executed correctly.
    status = COMPLETE if all(c.passed for c in checks) else BLOCKED
    out = {
        "stage": STAGE,
        "status": status,
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.to_dict() for c in checks],
        "adapter_forcing_coverage_gap_confirmed": source_gap,
        "canonical_state_changed": False,
        "canonical_replay_authorized": False,
        "canonical_parameter_change_authorized": False,
        "next_action": next_action,
    }
    write_json(root / OUT_REL / "R4_6_R43_CDMETAPOP_FORCING_PARITY_AUDIT.json", parity)
    write_json(root / OUT_REL / "R4_6_CANONICAL_FORCING_AUDIT.json", forcing)
    write_json(root / OUT_REL / "R4_6_REFERENCE_POPULATION_HOLD_COUNTERFACTUAL.json", cf)
    write_json(root / OUT_REL / "R4_6_CAUSAL_DIAGNOSIS.json", conclusion)
    write_json(root / OUT_REL / "R4_6_INTEGRATED_AUDIT.json", out)
    return out, checks


def final_seal(root: Path) -> tuple[dict[str, Any], list[Check]]:
    root = Path(root).resolve()
    p = load_json(root / R45_SEAL_REL) if (root / R45_SEAL_REL).exists() else {}
    a = load_json(root / OUT_REL / "R4_6_INTEGRATED_AUDIT.json") if (root / OUT_REL / "R4_6_INTEGRATED_AUDIT.json").exists() else {}
    parity = load_json(root / OUT_REL / "R4_6_R43_CDMETAPOP_FORCING_PARITY_AUDIT.json") if (root / OUT_REL / "R4_6_R43_CDMETAPOP_FORCING_PARITY_AUDIT.json").exists() else {}
    cf = load_json(root / OUT_REL / "R4_6_REFERENCE_POPULATION_HOLD_COUNTERFACTUAL.json") if (root / OUT_REL / "R4_6_REFERENCE_POPULATION_HOLD_COUNTERFACTUAL.json").exists() else {}
    d = load_json(root / OUT_REL / "R4_6_CAUSAL_DIAGNOSIS.json") if (root / OUT_REL / "R4_6_CAUSAL_DIAGNOSIS.json").exists() else {}
    checks = [
        Check("parent_r45_sealed", p.get("status") == R45_SEALED, p.get("status")),
        Check("r46_diagnosis_complete", a.get("status") == COMPLETE, a.get("status")),
        Check("r46_zero_process_failures", a.get("checks_failed") == 0, a.get("checks_failed")),
        Check("forcing_parity_audit_present", parity.get("audit") == "R43_CDMETAPOP_FORCING_PARITY_SOURCE_AUDIT", parity.get("audit")),
        Check("diagnostic_counterfactual_executed", cf.get("status") == "PASS_R46_DIAGNOSTIC_COUNTERFACTUAL_EXECUTED", cf.get("status")),
        Check("canonical_state_unchanged", a.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized", a.get("canonical_replay_authorized") is False),
        Check("canonical_parameter_change_not_authorized", a.get("canonical_parameter_change_authorized") is False),
        Check("r311_recalibration_not_authorized", d.get("canonical_r311_recalibration_authorized") is False),
        Check("next_action_present", bool(a.get("next_action")), a.get("next_action")),
    ]
    ok = all(c.passed for c in checks)
    out = {
        "stage": STAGE,
        "audit": "FINAL_TARGETED_R311_CAUSAL_COUNTERFACTUAL_AND_R43_CDMETAPOP_FORCING_PARITY_AUDIT",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.to_dict() for c in checks],
        "summary": {
            "adapter_forcing_coverage_gap_confirmed": parity.get("forcing_coverage_gap_confirmed"),
            "adapter_finding": parity.get("finding"),
            "counterfactual_population_response": cf.get("population"),
            "canonical_state_changed": False,
            "canonical_replay_authorized": False,
            "canonical_parameter_change_authorized": False,
            "deep_biological_coupling": False,
            "next_action": a.get("next_action"),
        },
        "next_action": a.get("next_action"),
    }
    write_json(root / SEAL_REL, out)
    return out, checks
