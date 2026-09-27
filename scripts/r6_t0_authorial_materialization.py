"""Emit the governed R6 T0 authorial materialization preflight artifacts."""
from __future__ import annotations

import json
from pathlib import Path

from arcana_worldsim.r6.t0_materialization import build_artifacts, render_markdown

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    candidates, report = build_artifacts(ROOT)
    (ROOT / "R6_TECTONIC_T0_AUTHORIAL_REALIZATION_CANDIDATES.json").write_text(
        json.dumps(candidates, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    (ROOT / "R6_TECTONIC_T0_MATERIALIZATION_IMPLEMENTATION.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    (ROOT / "R6_TECTONIC_T0_MATERIALIZATION_IMPLEMENTATION.md").write_text(
        render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "decision": report["principal_decision"],
        "authorial_realizations": report["authorial_candidate_set"]["candidate_authorial_realizations"],
        "unresolved_choices": report["authorial_candidate_set"]["human_authorial_choices_still_unresolved"],
        "new_physical_fields": report["materialized_fields"]["new_physical_field_families"],
        "pre_orbdata_fegs": report["PRE_ORBDATA_outputs"]["fegs_generated"],
        "shells_ready_fegs": report["SHELLS_READY_outputs"]["fegs_generated"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
