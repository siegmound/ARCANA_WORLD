"""Validate the governed, non-materializing P7Q-PRE2 adjudication."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "R5_17_B7_A3F2_P7Q_PRE2_TARGETED_PARENT_MATERIAL_DATASET_COMPLETION_ADJUDICATION.json"


def main() -> int:
    d = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert d["stage"] == "P7Q-PRE2"
    assert d["repository"]["head"] == d["repository"]["origin_main"] == "ac6cd67b3ec553cfa2585ff75f2e57d45d7c301d"
    assert d["pre1"]["decision"] == "REQUIRE_ADDITIONAL_PARENT_MATERIAL_DATASET_RESEARCH"
    assert d["target_temporal_domain"] == "200 ka to 0 ka"
    assert d["constraints"] == {"p7q_reopened": False, "large_downloads_performed": False, "simulation_performed": False, "provider_installed": False, "materialization_performed": False, "scientific_authority_register_mutated": False}
    assert d["minimum_sufficient_parent_state_contract"]
    assert d["gum_assessment"]["coverage_semantics_assessed"]
    assert d["temporal_class_matrix"]
    assert d["vertical_profile_adjudication"]["adjudicated"]
    assert d["composite_architecture"]["assessment"]
    assert d["final_scientific_decision"] in {"AUTHORIZE_P7Q_PRE3_COMPOSITE_PARENT_STATE_PROVIDER_SCHEMA_AND_ACQUISITION_GATE", "REQUIRE_P7Q_PRE3_TEMPORAL_PARENT_MATERIAL_RECONSTRUCTION_METHOD_RESEARCH", "REQUIRE_ADDITIONAL_RESIDUAL_PARENT_MATERIAL_AUTHORITY", "REQUIRE_ADDITIONAL_TEXTURE_OR_PROFILE_AUTHORITY", "BLOCKED_NO_DEFENSIBLE_GLOBAL_PARENT_MATERIAL_COMPLETION_PATH"}
    print("P7Q-PRE2 validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
