"""Validate the governed, non-materializing P7Q-PRE3 method adjudication."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "R5_17_B7_A3F2_P7Q_PRE3_TEMPORAL_PARENT_MATERIAL_RECONSTRUCTION_METHOD_ADJUDICATION.json"

def main() -> int:
    d = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert d["stage"] == "P7Q-PRE3"
    assert d["repository"]["head"] == d["repository"]["origin_main"] == "a624d9119817566be31481699232c01f8528ba5c"
    assert d["register_preflight"]["p7q_reopened"] is False
    assert d["constraints"] == {"simulation_performed": False, "materialization_performed": False, "large_downloads_performed": False, "provider_installed": False, "scientific_authority_register_mutated": False, "execution_indexes_mutated": False}
    assert len(d["target_temporal_domain"]["snapshot_ages_ka"]) == 12
    assert len(d["reference_model_assessments"]) >= 5
    assert d["inverse_problem_adjudication"]["backward_reconstruction"] == "UNJUSTIFIED"
    assert d["hybrid_ensemble_assessment"]["preferred"] is True
    assert d["uncertainty_contract"]["unknown_is_preserved"] is True
    assert d["validation_contract"]["observational_200ka_validation_claimed"] is False
    assert d["final_scientific_decision"] == "AUTHORIZE_P7Q_PRE4_HYBRID_TEMPORAL_PARENT_STATE_ADAPTER_SCHEMA_GATE"
    assert d["pass_verdict"] == "PASS_P7Q_PRE3_TEMPORAL_PARENT_MATERIAL_RECONSTRUCTION_METHOD_ADJUDICATED"
    print("P7Q-PRE3 validation passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
