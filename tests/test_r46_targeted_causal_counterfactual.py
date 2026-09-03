from __future__ import annotations

import json
from pathlib import Path

import pytest

from arcana_worldsim.scientific_engines import r46_targeted_causal_counterfactual as r46


def _write_json(p: Path, d: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d), encoding="utf-8")


def _minimal_cdmeta_job(drivers: dict | None = None) -> dict:
    return {
        "engine_input": {"drivers": drivers or {
            "normalized_habitat_fraction_start": 0.25,
            "normalized_habitat_fraction_end": 0.26,
            "normalized_environment_change": -0.04,
            "engine_gene_flow_rate": 0.02,
        }},
        "unit_mapping": {"domain_mapping": [
            {"domain": "population_persistence", "authority_role": "PRIMARY", "comparability_class": "NORMALIZABLE"}
        ]},
    }


def test_driver_token_parser_counts_only_explicit_cdmetapop_driver_reads():
    src = """
d = c['engine_input']['drivers']
x = d['normalized_habitat_fraction_start']
y = d.get("engine_gene_flow_rate", 0.01)
# normalized_environment_change only appears in a comment
"""
    got = r46._driver_tokens_from_cdmetapop_source(src)
    assert "normalized_habitat_fraction_start" in got
    assert "engine_gene_flow_rate" in got
    assert "normalized_environment_change" not in got


def test_cdmetapop_parity_flags_nonzero_unconsumed_dynamic_forcing(tmp_path: Path):
    job_id = "R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP"
    _write_json(tmp_path / r46.R43_JOBS_REL / job_id / "JOB_CONTRACT.json", _minimal_cdmeta_job())
    p = tmp_path / r46.R43_CDMETA_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("d=c['engine_input']['drivers']\nh=float(d['normalized_habitat_fraction_start'])\ng=float(d['engine_gene_flow_rate'])\n", encoding="utf-8")
    cfg = {"r47_symmetry_policy": {"affected_frozen_jobs": [job_id]}}
    out = r46.audit_cdmetapop_forcing_parity(tmp_path, job_id, cfg)
    assert out["forcing_coverage_gap_confirmed"] is True
    assert out["normalized_environment_change_explicitly_consumed"] is False
    assert out["normalized_habitat_fraction_end_explicitly_consumed"] is False
    assert out["start_state_only_parameterization_detected"] is True
    assert out["finding"] == "R43_CDMETAPOP_POPULATION_PERSISTENCE_DYNAMIC_FORCING_COVERAGE_GAP_CONFIRMED"


def test_cdmetapop_parity_can_pass_when_dynamic_forcing_is_consumed(tmp_path: Path):
    job_id = "J"
    _write_json(tmp_path / r46.R43_JOBS_REL / job_id / "JOB_CONTRACT.json", _minimal_cdmeta_job())
    p = tmp_path / r46.R43_CDMETA_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("d=c['engine_input']['drivers']\na=d['normalized_habitat_fraction_start']\nb=d['normalized_habitat_fraction_end']\ne=d['normalized_environment_change']\n", encoding="utf-8")
    out = r46.audit_cdmetapop_forcing_parity(tmp_path, job_id, {"r47_symmetry_policy": {"affected_frozen_jobs": []}})
    assert out["forcing_coverage_gap_confirmed"] is False
    assert out["dynamic_end_forcing_explicitly_consumed"] is True


def test_extract_authorized_case_requires_exact_r45_cdmetapop_row(tmp_path: Path):
    cfg = {
        "authorized_case": {
            "earliest_boundary": "R3.11_POST_CHA1",
            "window_id": "H0_POST_CHA1_RECOVERY",
            "domain": "population_persistence",
            "engine": "CDMetaPOP",
            "job_id": "R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP",
        },
        "required_parent_next_action": "EXECUTE_R46_TARGETED_CAUSAL_COUNTERFACTUAL_FROM_R3_11_POST_CHA1",
    }
    _write_json(tmp_path / r46.R45_SEAL_REL, {"status": r46.R45_SEALED})
    _write_json(tmp_path / r46.R45_AUDIT_REL, {"status": r46.R45_COMPLETE})
    _write_json(tmp_path / r46.R45_GATE_REL, {
        "diagnostic_counterfactual_authorized": True,
        "canonical_replay_authorized": False,
        "next_action": cfg["required_parent_next_action"],
    })
    _write_json(tmp_path / r46.R45_DIAG_REL, {
        "structural_diagnoses": [{
            "window_id": "H0_POST_CHA1_RECOVERY",
            "domain": "population_persistence",
            "earliest_affected_authority_candidate": "R3.11_POST_CHA1",
            "robust_structural_disagreement": True,
            "diagnostic_counterfactual_authorized": True,
            "row_diagnoses": [{
                "diagnosis_class": "ROBUST_PRIMARY_STRUCTURAL_DISAGREEMENT",
                "engine": "CDMetaPOP",
                "job_id": "R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP",
            }],
        }]
    })
    case, checks = r46._extract_authorized_case(tmp_path, cfg)
    assert all(c.passed for c in checks)
    assert case["job_id"].endswith("CDMETAPOP")


def test_extract_authorized_case_fails_closed_on_old_rangeshiftr_assumption(tmp_path: Path):
    cfg = {
        "authorized_case": {
            "earliest_boundary": "R3.11_POST_CHA1",
            "window_id": "H0_POST_CHA1_RECOVERY",
            "domain": "population_persistence",
            "engine": "CDMetaPOP",
            "job_id": "R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP",
        },
        "required_parent_next_action": "EXECUTE_R46_TARGETED_CAUSAL_COUNTERFACTUAL_FROM_R3_11_POST_CHA1",
    }
    _write_json(tmp_path / r46.R45_SEAL_REL, {"status": r46.R45_SEALED})
    _write_json(tmp_path / r46.R45_AUDIT_REL, {"status": r46.R45_COMPLETE})
    _write_json(tmp_path / r46.R45_GATE_REL, {"diagnostic_counterfactual_authorized": True, "canonical_replay_authorized": False, "next_action": cfg["required_parent_next_action"]})
    _write_json(tmp_path / r46.R45_DIAG_REL, {"structural_diagnoses": [{
        "window_id": "H0_POST_CHA1_RECOVERY", "domain": "population_persistence", "earliest_affected_authority_candidate": "R3.11_POST_CHA1",
        "robust_structural_disagreement": True, "diagnostic_counterfactual_authorized": True,
        "row_diagnoses": [{"diagnosis_class": "ROBUST_PRIMARY_STRUCTURAL_DISAGREEMENT", "engine": "RangeShifter", "job_id": "R42_J08_H0_POST_CHA1_RECOVERY_RANGESHIFTER"}],
    }]})
    _, checks = r46._extract_authorized_case(tmp_path, cfg)
    assert any(c.name == "authorized_case_matches_frozen_r46_scope" and not c.passed for c in checks)


def test_counterfactual_checks_require_exact_step_counts_and_invariants():
    cf = {
        "status": "PASS_R46_DIAGNOSTIC_COUNTERFACTUAL_EXECUTED",
        "start_age_ma": 65.5,
        "end_age_ma": 55.0,
        "ordinary_steps_r311": 36,
        "ordinary_steps_r312_to_55ma": 48,
        "clipping_contacts": {"r311": 0, "r312_to_55": 0},
        "numerical_invariants_at_55ma": {"population_min": 0.0, "population_on_inaccessible_cells": 0.0, "q_max": 0.05, "q_ceiling": 0.08},
        "canonical_state_changed": False,
        "canonical_replay_authorized": False,
        "intervention": {"canonical_checkpoint_written": False},
    }
    assert all(c.passed for c in r46._counterfactual_checks(cf))


def test_ratio_direction_uses_five_percent_neutral_band():
    assert r46._direction_ratio(1.10) == 1
    assert r46._direction_ratio(0.90) == -1
    assert r46._direction_ratio(1.01) == 0


def test_r46_config_freezes_no_canonical_change():
    root = Path(__file__).resolve().parents[1]
    cfg = r46.load_json(root / r46.CFG_REL)
    assert cfg["canonical_state_changed"] is False
    assert cfg["canonical_replay_authorized"] is False
    assert cfg["canonical_parameter_change_authorized"] is False
    assert cfg["deep_biological_coupling"] is False
    assert cfg["majority_vote"] is False
    assert cfg["policy_freeze"]["result_selected"] is False


def test_r46_authorized_scope_is_exact_r45_cdmetapop_case():
    root = Path(__file__).resolve().parents[1]
    cfg = r46.load_json(root / r46.CFG_REL)
    c = cfg["authorized_case"]
    assert c == {
        "earliest_boundary": "R3.11_POST_CHA1",
        "window_id": "H0_POST_CHA1_RECOVERY",
        "domain": "population_persistence",
        "engine": "CDMetaPOP",
        "job_id": "R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP",
        "start_age_ma": 65.5,
        "end_age_ma": 55.0,
    }


def test_r47_symmetry_scope_covers_all_common_cdmetapop_r43_jobs():
    root = Path(__file__).resolve().parents[1]
    cfg = r46.load_json(root / r46.CFG_REL)
    jobs = cfg["r47_symmetry_policy"]["affected_frozen_jobs"]
    assert len(jobs) == 5
    assert "R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP" in jobs
    assert "R42_J20_SAPIENT_200KA_TO_0_CDMETAPOP" in jobs
    assert all(x.endswith("CDMETAPOP") for x in jobs)


def test_r311_constants_remain_frozen():
    root = Path(__file__).resolve().parents[1]
    cfg = r46.load_json(root / r46.CFG_REL)
    c = cfg["r311_scientific_constants_frozen"]
    assert c["mu_per_myr"] == pytest.approx(0.002)
    assert c["b"] == pytest.approx(0.9876543209876544)
    assert c["q_ceiling"] == pytest.approx(0.08)
    assert c["biology_cadence_years"] == pytest.approx(125000.0)


def test_actual_r43_cdmetapop_source_exposes_dynamic_forcing_gap():
    root = Path(__file__).resolve().parents[1]
    cfg = r46.load_json(root / r46.CFG_REL)
    job_id = cfg["authorized_case"]["job_id"]
    out = r46.audit_cdmetapop_forcing_parity(root, job_id, cfg)
    # This locks the audited pre-R4.6 source semantics. A later R4.7 repair
    # must use a new evidence namespace rather than mutating R4.3 history.
    assert out["normalized_environment_change_nonzero"] is True
    assert out["normalized_environment_change_explicitly_consumed"] is False
    assert out["normalized_habitat_fraction_end_explicitly_consumed"] is False
    assert out["forcing_coverage_gap_confirmed"] is True


def test_contract_forbids_result_selected_j09_only_shared_adapter_repair():
    root = Path(__file__).resolve().parents[1]
    cfg = r46.load_json(root / r46.CFG_REL)
    text = cfg["r47_symmetry_policy"]["if_common_cdmetapop_adapter_changes"]
    assert "symmetrically" in text
    assert "do not repair only" in text


def test_cdmetapop_adapter_keeps_pinned_source_read_only_policy():
    root = Path(__file__).resolve().parents[1]
    src = (root / r46.R43_CDMETA_REL).read_text(encoding="utf-8-sig")
    assert "source_tree_modified':False" in src or '"source_tree_modified":False' in src
    assert "compatibility_shim" in src
