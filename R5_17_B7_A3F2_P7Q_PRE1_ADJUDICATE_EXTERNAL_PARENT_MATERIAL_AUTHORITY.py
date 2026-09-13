"""Validate the governed P7Q-PRE1 external parent-material adjudication."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "R5_17_B7_A3F2_P7Q_PRE1_EXTERNAL_PARENT_MATERIAL_AUTHORITY_ACQUISITION_ADJUDICATION.json"


def main() -> int:
    document = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert document["stage"] == "P7Q-PRE1"
    assert document["repository"]["head"] == document["repository"]["origin_main"]
    assert document["register_preflight"]["result"] == "PARENT_MATERIAL_ABSENT_AFTER_AUDIT__EXTERNAL_ACQUISITION_REQUIRED"
    assert document["target_temporal_domain"] == "200 ka to 0 ka"
    assert len(document["requirement_matrix"]) == 13
    assert {x["candidate_id"] for x in document["candidates"]} == {"GLiM", "PELLETIER_2016", "SOILGRIDS_2_0"}
    assert document["constraints"]["p7q_reopened"] is False
    assert document["constraints"]["downloads_performed"] is False
    assert document["final_scientific_decision"] == "REQUIRE_ADDITIONAL_PARENT_MATERIAL_DATASET_RESEARCH"
    print("P7Q-PRE1 validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
