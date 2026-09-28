from __future__ import annotations

import json
from pathlib import Path
from arcana_worldsim.r6.t0_materialization import specialist_runtime

from arcana_worldsim.r6.t0_materialization.specialist_runtime import (
    REFERENCE_FAMILIES,
    RHEOLOGY_FAMILIES,
    build_readjudication,
    load_fair_runtime_evidence,
    build_report,
    render_markdown,
)


ROOT = Path(__file__).resolve().parents[1]


def test_governed_fair_evidence_hash_and_runtime_identity_are_bound():
    evidence, digest = load_fair_runtime_evidence(ROOT)
    assert digest == "ab29de4577c4c4b007d41a7ac5567d7b287c7fed5dee3107aeb69dc35df1a350"
    assert evidence["qualified_runtime"]["commit"] == "09a06ecd061f00b80a52af86e31d609ff5545a8b"
    assert evidence["qualified_runtime"]["executable_sha256"] == (
        "03e1a3f7ac0c4593a4a6eb641bb6d8acd0b752da5c5fd7b1ee74788fb705e349"
    )


def test_readjudication_preserves_windows_history_and_uses_fair_qualification():
    report = build_readjudication(ROOT)
    assert report["historical_windows_observation"]["host_os"].startswith("Windows-")
    assert report["runtime"]["availability"].startswith("AVAILABLE_ON_FAIR")
    assert report["runtime"]["qualified_for_official_upstream_examples"] is True
    assert report["runtime"]["qualified_for_arcana_mesh_capacity"] is True
    assert report["runtime"]["t0_input_transformations_authorized"] is False
    assert report["runtime"]["t0_mechanics_authorized"] is False
    assert report["runtime"]["cross_backend_acceptance"] == "NOT_ADJUDICATED"


def test_orbdata_field_gate_does_not_infer_bathymetry_or_zero_sentinels():
    report = build_readjudication(ROOT)
    fields = {row["field"]: row for row in report["orbdata_capability_matrix"]}
    assert len(fields) == 6
    assert "no source-grounded ocean-age-to-bathymetry" in fields["elevation"]["orbdata_derives"]
    assert fields["elevation"]["zero_or_sentinel"] == "NOT_ESTABLISHED_FOR_THIS_FIELD"
    assert fields["crustal_thickness"]["orbdata_derives"].startswith("No")
    assert report["feg_readiness"]["PRE_ORBDATA_ready"] is False
    assert report["feg_readiness"]["SHELLS_READY_ready"] is False
    assert report["feg_readiness"]["mechanics_authorized"] is False


def test_explicit_shellset_executable_is_available_but_not_assumed_qualified(tmp_path, monkeypatch):
    executable = tmp_path / "ShellSet.exe"
    executable.write_bytes(b"fixture")
    monkeypatch.setenv("ARCANA_SHELLSET_EXE", str(executable))
    monkeypatch.delenv("ARCANA_SHELLSET_ROOT", raising=False)
    monkeypatch.setattr(specialist_runtime.shutil, "which", lambda _: None)

    shellset = specialist_runtime.runtime_inventory()["ShellSet"]

    assert shellset["availability"] == "AVAILABLE"
    assert shellset["qualification"] == "NOT_RUN"
    assert shellset["resolved_path"] == str(executable.resolve())
    assert shellset["binding_source"] == "ARCANA_SHELLSET_EXE"
    assert shellset["executable_sha256"] == "f16d05ec6b29248d2c61adb1e9263f78e4f7bace1b955014a2d17872cfe4064d"


def test_missing_explicit_shellset_root_fails_closed(tmp_path, monkeypatch):
    monkeypatch.delenv("ARCANA_SHELLSET_EXE", raising=False)
    monkeypatch.setenv("ARCANA_SHELLSET_ROOT", str(tmp_path / "missing"))
    monkeypatch.setattr(specialist_runtime.shutil, "which", lambda _: None)

    shellset = specialist_runtime.runtime_inventory()["ShellSet"]

    assert shellset["availability"] == "UNAVAILABLE"
    assert shellset["qualification"] == "BLOCKED_CONFIGURED_RUNTIME_NOT_FOUND"


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
