from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
si1 = importlib.import_module("r6_shells_si1_engineering_solve")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_source_lock_requires_exact_fortran_and_makefile_inventory(tmp_path: Path) -> None:
    source = tmp_path / "ShellSet"
    (source / "src").mkdir(parents=True)
    (source / "Makefile").write_text("all:\n", encoding="utf-8")
    (source / "src" / "main.f90").write_text("end\n", encoding="utf-8")
    lock = {"files": {
        "Makefile": _sha(source / "Makefile"),
        "src/main.f90": _sha(source / "src" / "main.f90"),
    }}

    assert si1.verify_source_lock(source, lock) == lock["files"]
    (source / "src" / "unlocked.f90").write_text("! not locked\n", encoding="utf-8")
    with pytest.raises(si1.SI1Error, match="inventory differs from lock"):
        si1.verify_source_lock(source, lock)


def test_reconciliation_keeps_historical_qualification_scopes_distinct() -> None:
    lock = json.loads((ROOT / "configs/r6_shells_si1/shellset_source_lock.json").read_text(encoding="utf-8"))
    hashes = si1.verify_source_lock(ROOT / "external/ShellSet-v1.1.0", lock)
    evidence = si1.reconcile_source_evidence(hashes, lock)

    assert evidence["historical_successor_provenance"]["recorded_source_tree_unavailable"] is True
    assert evidence["historical_successor_provenance"]["current_workspace_source_tree_available"] is True
    assert evidence["historical_successor_provenance"]["successor_patch_identity_recorded"] is None
    assert evidence["historical_shellset_capacity_qualification"]["scope"] == "CAPACITY_AND_UPSTREAM_EXAMPLE_ONLY"
    assert evidence["historical_arcana_runtime_qualification"]["qualified_arcana_commit"] == "62fd474f229b2676fd9d39c5def45137d22d2481"
    assert "does not claim Fair rebuild" in evidence["si1_scope"]


def test_numeric_reproducibility_uses_declared_tolerances() -> None:
    first = {"files": [{"path": "RUN_OUTPUT/model.22", "_values": [1.0, 2.0], "sha256": "a"}]}
    close = {"files": [{"path": "RUN_OUTPUT/model.22", "_values": [1.0 + 1e-13, 2.0], "sha256": "b"}]}
    outside = {"files": [{"path": "RUN_OUTPUT/model.22", "_values": [1.0 + 1e-5, 2.0], "sha256": "b"}]}

    passed = si1._compare_output_sets(first, close, abs_tol=1e-12, rel_tol=1e-10)
    assert passed["status"] == "PASS_NUMERICALLY_REPRODUCIBLE"
    assert passed["max_abs"] == pytest.approx(1e-13)
    assert si1._compare_output_sets(first, outside, 1e-12, 1e-10)["status"] == "FAIL_NUMERIC_OUTPUT_OUTSIDE_TOLERANCE"


def test_numeric_reproducibility_rejects_changed_file_and_value_cardinality() -> None:
    first = {"files": [{"path": "a.22", "_values": [1.0]}]}
    changed_name = {"files": [{"path": "b.22", "_values": [1.0]}]}
    changed_count = {"files": [{"path": "a.22", "_values": [1.0, 2.0]}]}

    assert si1._compare_output_sets(first, changed_name, 0, 0)["status"] == "FAIL_OUTPUT_FILE_SET_CHANGED"
    assert si1._compare_output_sets(first, changed_count, 0, 0)["status"] == "FAIL_NUMERIC_VALUE_COUNT_CHANGED"


def test_convergence_requires_shellset_explicit_success_marker() -> None:
    assert si1._converged("CONVERGED !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    assert not si1._converged("ITERATION LIMIT REACHED BEFORE CONVERGENCE.")
    assert not si1._converged("not converged")


def test_output_parser_retains_numbers_for_comparison_but_public_json_is_compact(tmp_path: Path) -> None:
    output = tmp_path / "RUN_OUTPUT"
    output.mkdir()
    (output / "case.22").write_text("1 2.5D+00\n2 -3.0\n", encoding="ascii")

    parsed = si1._parse_finite_velocity_files(output)
    assert parsed["status"] == "PASS"
    assert parsed["files"][0]["_values"] == [1.0, 2.5, 2.0, -3.0]
    assert "_values" not in si1._public_output_validation(parsed)["files"][0]

    (output / "bad.24").write_text("NaN 1.0\n", encoding="ascii")
    assert si1._parse_finite_velocity_files(output)["status"] == "FAIL_NONFINITE_OR_UNPARSEABLE_SHELLS_OUTPUT"


def test_generated_preflight_stops_after_ksize_and_before_matrix_allocation(tmp_path: Path) -> None:
    source = tmp_path / "SHELLS_v5.0.f90"
    target = tmp_path / "instrumented.f90"
    source.write_text(
        "       INTEGER nRank, nCodiagonals, nKRows, iDiagonal\n"
        "       COMMON  nRank, nCodiagonals, nKRows, iDiagonal\n"
        "       CALL KSize (brief, iUnitP, iUnitLog, mxEl, mxFEl, mxNode, &\n"
        "     & jCol1, jCol2) ! calculate\n"
        "       ALLOCATE ( stiff(nKRows, nRank) )\n",
        encoding="utf-8",
    )

    si1._preflight_source(source, target)
    text = target.read_text(encoding="utf-8")
    assert text.index("SI1_KSIZE nRank=") < text.index("ALLOCATE ( stiff")
    assert text.index("CALL KSize") < text.index("SI1_KSIZE nRank=")
    assert "CALL FatalError('SI1_KSIZE_PREFLIGHT_STOP', ThID)" in text
    assert max(map(len, text.splitlines())) <= 132
    assert "ALLOCATE ( stiff(nKRows, nRank) )" in source.read_text(encoding="utf-8")


def test_input_files_preserve_stock_parser_line_layout_and_no_bc_records(tmp_path: Path) -> None:
    input_dir = tmp_path / "INPUT"
    si1.write_input_files(input_dir)
    lines = (input_dir / "InputFiles.in").read_text(encoding="ascii").splitlines()
    assert len(lines) == 41
    assert lines[0] == "SI1 ARCANA engineering input set"
    assert lines[1] == "SI1_ENGINEERING_REFERENCE.in"
    assert lines[2] == "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg"
    assert lines[13] == "Shells (Main work loop):"
    assert lines[14] == "SI1_NO_VELOCITY.bcs"
    assert lines[23] == "Shells (Final OR Non-Iterating run):"
    assert lines[24] == "SI1_NO_VELOCITY.bcs"
    assert (input_dir / "SI1_NO_VELOCITY.bcs").read_text(encoding="ascii").splitlines() == [
        "ARCANA_SI1_GLOBAL_CONTINUUM_NO_VELOCITY_CONSTRAINTS"
    ]
    assert json.loads((ROOT / "configs/r6_shells_si1/engineering_case.json").read_text(encoding="utf-8"))["solver"]["boundary_condition_records"] == 0


def test_result_never_claims_pre_materialized_or_gauge_success() -> None:
    case = json.loads((ROOT / "configs/r6_shells_si1/engineering_case.json").read_text(encoding="utf-8"))
    assert case["classification"] == "NON_CANONICAL_ENGINEERING_CANDIDATE"
    assert case["solver"]["gauge_policy"].startswith("NO_GAUGE_IN_INITIAL_RUN")
    assert case["preserved_authority_gates"] == {
        "canonical_state_changed": False,
        "WORLD_HISTORY_changed": False,
        "T2_created": False,
        "forward_evolution_authorized": False,
        "canonical_mechanics_authorized": False,
    }
    assert case["parameter_binding_audit"]["values_are_arcana_authority"] is False
    assert case["parameter_binding_audit"]["classification"] == "ENGINEERING_SOLVER_REFERENCE_NOT_ARCANA_GEOLOGY"


def test_staging_uses_selected_shellset_reference_and_does_not_precreate_shellset_output(tmp_path: Path) -> None:
    build = tmp_path / "build"
    build.mkdir()
    (build / "ShellSet.exe").write_bytes(b"engineering-only-test-placeholder")
    geometry = tmp_path / "ARCANA_PLATE_OUTLINES.dig"
    geometry.write_text("fixture geometry\n", encoding="ascii")
    reference = tmp_path / "iEarth5-049.in"
    reference.write_text("reference-only parameters\n", encoding="ascii")
    run_dir = tmp_path / "run"

    si1._copy_executable_and_inputs(build, run_dir, geometry, reference)

    assert (run_dir / "ShellSet.exe").is_file()
    assert (run_dir / "INPUT/SI1_ENGINEERING_REFERENCE.in").read_bytes() == reference.read_bytes()
    assert (run_dir / "INPUT/ARCANA_PLATE_OUTLINES.dig").read_bytes() == geometry.read_bytes()
    assert not (run_dir / "RUN_OUTPUT").exists()


def test_output_manifest_is_relative_and_excludes_itself(tmp_path: Path) -> None:
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "compile.log").write_text("build evidence\n", encoding="utf-8")
    (tmp_path / "SI1_RESULT.json").write_text("{}\n", encoding="utf-8")

    si1._seal_output_manifest(tmp_path)
    manifest = json.loads((tmp_path / "SI1_ARTIFACT_MANIFEST.json").read_text(encoding="utf-8"))
    paths = [item["path"] for item in manifest["artifacts"]]
    assert paths == ["logs/compile.log", "SI1_RESULT.json"]
    assert all(not Path(value).is_absolute() for value in paths)
    assert "SI1_ARTIFACT_MANIFEST.json" not in paths
