from __future__ import annotations

import json
from pathlib import Path

from arcana_worldsim.r6.t0_materialization.specialist_runtime import (
    REFERENCE_FAMILIES,
    RHEOLOGY_FAMILIES,
    build_report,
    render_markdown,
)


ROOT = Path(__file__).resolve().parents[1]


def test_specialist_report_reconciles_b_v2_parent_and_keeps_runtime_blocked():
    parent = json.loads((ROOT / "R6_T0_B_PANGAEA_LIKE_V2_MATERIALIZATION_REPORT.json").read_text())
    report = build_report(ROOT, runtimes={
        name: {"commands_checked": [], "available_on_path": False,
               "resolved_command": None, "resolved_path": None,
               "version": None, "qualification": "BLOCKED_RUNTIME_NOT_FOUND"}
        for name in ("GWB", "OrbData5", "SHELLS", "ShellSet")
    })

    assert report["principal_decision"] == (
        "R6_T0_B_PANGAEA_LIKE_V2_SPECIALIST_PARTIAL__MATERIALIZER_RUNTIME_BLOCKED"
    )
    assert report["parent_state"]["upstream_field_package_sha256"] == parent["field_package_sha256"]
    assert report["parent_state"]["canonical_state_changed"] is False
    assert report["pending_field_ledger"]["PENDING_SPECIALIST_RUNTIME"] == parent[
        "pending_specialist_fields"
    ]
    assert len(report["reference_physical_configuration"]["families"]) == len(REFERENCE_FAMILIES)
    assert len(report["rheology_configuration"]["families"]) == len(RHEOLOGY_FAMILIES)
    assert report["global_heat_flow"]["global_field"] == "MISSING"
    assert report["chemical_density_anomaly"]["zero_assumption_selected"] is False
    assert report["cooling_curvature"]["arbitrary_zero_used"] is False
    assert report["FEG_status"]["shells_ready_fegs"] == 0
    assert report["runtime_manifest"]["runtime_authorized"] is False
    assert report["governance"]["forward_evolution"] is False
    assert report["governance"]["dt_created"] is False


def test_specialist_report_markdown_covers_required_gate_sections():
    report = build_report(ROOT, runtimes={
        name: {"commands_checked": [], "available_on_path": False,
               "resolved_command": None, "resolved_path": None,
               "version": None, "qualification": "BLOCKED_RUNTIME_NOT_FOUND"}
        for name in ("GWB", "OrbData5", "SHELLS", "ShellSet")
    })
    text = render_markdown(report)
    for section in (
        "ALREADY_MATERIALIZED", "PENDING_SPECIALIST_RUNTIME",
        "PENDING_MODEL_CONFIGURATION", "PENDING_NUMERICAL_PROJECTION",
        "NOT_REQUIRED", "UNKNOWN", "Runtime and field result", "Configuration status",
    ):
        assert section in text
