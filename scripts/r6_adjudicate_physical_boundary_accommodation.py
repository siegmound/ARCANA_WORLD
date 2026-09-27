from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.physical_boundary_accommodation import (
    adjudicate_boundary_accommodation, render_markdown,
)


def main() -> int:
    report = adjudicate_boundary_accommodation(ROOT)
    (ROOT / "R6_PHYSICAL_BOUNDARY_ACCOMMODATION_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8")
    (ROOT / "R6_PHYSICAL_BOUNDARY_ACCOMMODATION_REPORT.md").write_text(
        render_markdown(report), encoding="utf-8")
    print(json.dumps({"decision": report["decision"],
        "branches": report["canonical_boundary_graph"]["branch_count"],
        "sections": report["canonical_boundary_graph"]["section_count"],
        "resolved_demand_segments": report["relative_motion"]["segments_with_resolved_normal_and_tangent"],
        "positive_accommodation_sections": report["accommodation_law"]["positive_physical_accommodation_sections"],
        "junction_outcomes": report["junctions"]["outcome_counts"]},
        ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
