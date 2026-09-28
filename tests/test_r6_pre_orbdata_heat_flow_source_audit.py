from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "r6_pre_orbdata_heat_flow_source_audit.py"
SPEC = importlib.util.spec_from_file_location("r6_heat_audit", SCRIPT)
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def test_extract_contexts_reads_source_and_parameter_fixtures(tmp_path: Path) -> None:
    source = tmp_path / "src" / "OrbData.f90"
    source.parent.mkdir()
    source.write_text("before\nneedQ = (heatFl == 0.0D0)\nREAD(unit,*) qLim0\nCALL Assign(heatFl)\nqArray(i,j) = qLim1\nafter\n")
    (tmp_path / "INPUT").mkdir()
    (tmp_path / "INPUT" / "model.in").write_text("qLim0 = 1.0\ndQL_dE = 2.0\n")
    (tmp_path / "ignored.bin").write_bytes(b"qArray\x00")

    excerpts = audit.extract_contexts(tmp_path)

    assert excerpts["needQ"][0]["path"] == "src/OrbData.f90"
    assert excerpts["heatFl"][0]["line"] == 2
    assert excerpts["qArray"][0]["line"] == 5
    assert excerpts["qLim0"][0]["path"] == "INPUT/model.in"
    assert excerpts["dQL_dE"][0]["path"] == "INPUT/model.in"
    bindings = audit.extract_binding_and_callsite_contexts(tmp_path)
    assert any(hit["line"] == 3 and "qLim0" in hit["matched_symbols_in_neighborhood"] for hit in bindings)
    assert any(hit["line"] == 4 and "heatFl" in hit["matched_symbols_in_neighborhood"] for hit in bindings)


def test_category_contract_keeps_source_semantics_unassigned() -> None:
    expected = {
        "WORLD_HISTORY_PHYSICAL_INPUT",
        "SPECIALIST_MODEL_CONFIGURATION",
        "NUMERICAL_GUARD_OR_LIMIT",
        "DERIVED_ORBDATA_STATE",
        "UNRESOLVED_PENDING_SOURCE_ADJUDICATION",
    }
    assert set(audit.EVIDENCE_CATEGORY_SCHEMA) == expected
    assert all(not audit.EVIDENCE_CATEGORY_SCHEMA[name].get("symbol_assignments") for name in expected - {"UNRESOLVED_PENDING_SOURCE_ADJUDICATION"})
    assert set(audit.EVIDENCE_CATEGORY_SCHEMA["UNRESOLVED_PENDING_SOURCE_ADJUDICATION"]["symbols"]) == set(audit.TERMS)


def test_qualified_checkout_guard_rejects_fixture_repository(tmp_path: Path) -> None:
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "switch", "-c", audit.EXPECTED_BRANCH], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--allow-empty", "-m", "fixture identity"], check=True, capture_output=True)

    try:
        audit.verify_checkout(tmp_path)
    except ValueError as exc:
        assert "unqualified ShellSet commit" in str(exc)
    else:
        raise AssertionError("fixture git checkout must never pass the qualified-source identity gate")


def test_audit_outputs_cannot_modify_shellset_checkout(tmp_path: Path) -> None:
    source = tmp_path / "ShellSet"
    source.mkdir()
    try:
        audit.ensure_output_outside_source(source, [source / "audit.json"])
    except ValueError as exc:
        assert "refusing to write audit output inside ShellSet checkout" in str(exc)
    else:
        raise AssertionError("audit output must never be written inside ShellSet")
