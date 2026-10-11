"""Offline structural tests for the isolated N2C-W2 ShellSet overlay."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.r6_si1_bandwidth_f2b_n2c_w2_overlay import (
    OverlayError,
    create_candidate,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "external" / "ShellSet-v1.1.0"
ORIGINAL_MOD = PACKAGE / "src" / "MOD_Shells.f90"
BRIDGE = ROOT / "src" / "fortran" / "r6_n2c_shellset_capture_bridge.f90"
SOURCE_LOCK = ROOT / "configs" / "r6_shells_si1" / "shellset_source_lock.json"


def test_overlay_is_reproducible_isolated_and_places_capture_after_vbcs(tmp_path):
    protected = (
        ORIGINAL_MOD,
        PACKAGE / "src" / "ShellSetMain.f90",
        PACKAGE / "src" / "SHELLS_v5.0.f90",
        PACKAGE / "Makefile",
        ROOT / "src" / "fortran" / "r6_sparse_snapshot_writer.f90",
        SOURCE_LOCK,
    )
    original_hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected}
    candidate = tmp_path / "candidate"
    manifest = create_candidate(PACKAGE, candidate)
    patched = (candidate / "src" / "MOD_Shells.f90").read_text(encoding="utf-8")
    vbc = patched.index("CALL VBCs (iCond, mxBn, mxDOF")
    capture = patched.index("CALL n2c_capture_pre_solver", vbc)
    solver = patched.index("CALL Solver (iUnitT", capture)
    assert vbc < capture < solver
    assert "ERROR STOP 86" in patched[capture:solver]
    assert "n2c_model_num, n2c_process_rank, n2c_rpeat" in patched
    assert "n2c_iteration, n2c_fem_call_ordinal" in patched
    main = (candidate / "src" / "ShellSetMain.f90").read_text(encoding="utf-8")
    shells = (candidate / "src" / "SHELLS_v5.0.f90").read_text(encoding="utf-8")
    assert main.count("call Shells_v5p0(ListVarNames,ListVarValues(1,:),rpeat,SHELLSconv,ModNum)") == 2
    assert "SHELLSconv,n2c_model_num" in shells
    assert "n2c_model_num, rpeat)" in shells
    assert "n2c_fem_call_ordinal = n2c_fem_call_ordinal + 1" in patched
    assert "n2c_model_num, ThID, n2c_rpeat, iter, &" in patched
    assert "n2c_fem_call_ordinal)" in patched
    assert all(hashlib.sha256(path.read_bytes()).hexdigest() == digest for path, digest in original_hashes.items())
    assert all(len(line) <= 132 for line in (candidate / "src" / BRIDGE.name).read_text().splitlines())
    assert all(
        len(line) <= 132
        for source in (patched, shells)
        for line in source.splitlines()
        if "n2c_" in line or "n2c_capture_pre_solver" in line
    )
    assert manifest["runtime_invocation_identity"] == "UNKNOWN; CAPTURE_ONLY is fail-closed"
    assert manifest["si1_eligibility"] == "BLOCKED_W1_SYNTHETIC_DIMENSION_LIMITS"
    assert manifest["source_lock_sha256"] == "8c3174c08cb021ae90257e04880f7e96b9ecd9d4d830034bfc0ea6462ef867f2"
    assert len(manifest["source_locked_file_sha256"]) == 15
    assert manifest["source_commit_claim_from_lock"] == "9fef54f6cd17e6e756db3ec28bfc43ee0230fc27"
    assert manifest["source_parameter_reference_sha256"] == "c07834e17d9c6e21bad0d7cd81af20e8a670e0ae9ed481f999c881129ee4a89e"
    assert manifest["candidate_source_locked_file_sha256"] == {
        relative: hashlib.sha256((candidate / relative).read_bytes()).hexdigest()
        for relative in manifest["source_locked_file_sha256"]
    }
    assert json.loads((candidate / "N2C_W2_CANDIDATE_OVERLAY.json").read_text()) == manifest
    assert (candidate / "src" / BRIDGE.name).read_bytes() == BRIDGE.read_bytes()
    candidate2 = tmp_path / "candidate-repeat"
    manifest2 = create_candidate(PACKAGE, candidate2)
    assert manifest2 == manifest
    for relative in (
        "Makefile",
        "src/MOD_Shells.f90",
        "src/ShellSetMain.f90",
        "src/SHELLS_v5.0.f90",
        "src/r6_sparse_snapshot_writer.f90",
        "src/r6_n2c_shellset_capture_bridge.f90",
        "N2C_W2_CANDIDATE_OVERLAY.json",
    ):
        assert (candidate / relative).read_bytes() == (candidate2 / relative).read_bytes()


def test_overlay_patches_default_debug_and_optimized_dependency_chains(tmp_path):
    candidate = tmp_path / "candidate"
    create_candidate(PACKAGE, candidate)
    makefile = (candidate / "Makefile").read_text(encoding="utf-8")
    assert "r6_sparse_snapshot_writer.o r6_n2c_shellset_capture_bridge.o" in makefile
    assert "r6_sparse_snapshot_writer.DB.o r6_n2c_shellset_capture_bridge.DB.o" in makefile
    assert "r6_sparse_snapshot_writer.OPT.o r6_n2c_shellset_capture_bridge.OPT.o" in makefile
    assert "| r6_n2c_shellset_capture_bridge.o" in makefile
    assert "| r6_n2c_shellset_capture_bridge.DB.o" in makefile
    assert "| r6_n2c_shellset_capture_bridge.OPT.o" in makefile


def test_overlay_fails_closed_for_unexpected_baseline_and_existing_output(tmp_path):
    package = tmp_path / "source"
    import shutil

    shutil.copytree(PACKAGE, package)
    mod = package / "src" / "MOD_Shells.f90"
    mod.write_text(mod.read_text(encoding="utf-8") + "! changed\n", encoding="utf-8")
    with pytest.raises(OverlayError, match="SHA256 differs"):
        create_candidate(package, tmp_path / "bad-candidate")

    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(OverlayError, match="new, nonexistent"):
        create_candidate(PACKAGE, existing)


@pytest.mark.parametrize(
    ("relative", "changed_bytes", "message"),
    [
        ("src/MOD_ShellSet.f90", b"! altered unpatched locked source\n", "source-lock SHA256 differs"),
        ("INPUT/iEarth5-049.in", b"altered parameter reference\n", "parameter reference SHA256 differs"),
    ],
)
def test_overlay_rejects_changes_outside_patched_sources(tmp_path, relative, changed_bytes, message):
    import shutil

    package = tmp_path / "source"
    shutil.copytree(PACKAGE, package)
    (package / relative).write_bytes(changed_bytes)
    with pytest.raises(OverlayError, match=message):
        create_candidate(package, tmp_path / "candidate")


def test_si1_dimensions_are_explicitly_outside_w1_synthetic_bounds():
    n = 128_884
    kl = ku = 727
    ldab = 2 * kl + ku + 1
    storage = ldab * n
    assert ldab == 2_182
    assert storage == 281_224_888
    writer = (ROOT / "src" / "fortran" / "r6_sparse_snapshot_writer.f90").read_text(encoding="utf-8")
    assert "MAX_N = 2048_int64" in writer
    assert "MAX_STORAGE = 2000000_int64" in writer
    assert n > 2_048 and storage > 2_000_000


def test_bridge_defaults_off_and_rejects_unbound_runtime_provenance_before_solver():
    bridge = BRIDGE.read_text(encoding="utf-8").lower()
    assert "arcana_n2c_capture_mode" in bridge
    assert "env_status == 1" in bridge
    assert "config%mode = mode_default_off" in bridge
    assert "type(capture_context) :: context" in bridge
    assert "context_is_test_only" not in bridge  # enforced by the W1 writer
    assert "runtime invocation authority is not currently available" in bridge
    assert "leave context" in bridge and "empty on purpose" in bridge
    assert "capture_failed" in bridge
    assert "solver_may_proceed = writer_status == capture_default_off" in bridge
    assert "no w1 status authorizes entering solver" in bridge
    assert "model_num < 1" in bridge and "process_rank < 1" in bridge
    assert "rpeat < 1" in bridge and "iteration < 1" in bridge and "fem_call_ordinal < 1" in bridge


def test_w1_synthetic_context_contract_remains_the_only_successful_capture_path():
    writer = (ROOT / "src" / "fortran" / "r6_sparse_snapshot_writer.f90").read_text(encoding="utf-8").lower()
    fixture = (ROOT / "tests" / "fixtures" / "r6_si1_bandwidth_f2b_n2c_capture_driver.f90").read_text(encoding="utf-8")
    assert "context%test_only = .true." in fixture
    assert "has_test_prefix(context%run_id)" in writer
    assert "has_test_prefix(context%model_id)" in writer


def test_writer_and_candidate_bridge_accept_only_read_only_array_arguments():
    writer = (ROOT / "src" / "fortran" / "r6_sparse_snapshot_writer.f90").read_text(encoding="utf-8").lower()
    bridge = BRIDGE.read_text(encoding="utf-8").lower()
    assert "real(real64), intent(in) :: ab(:,:), b0(:)" in writer
    assert "real(real64), intent(in) :: ab(:,:), b0(:)" in bridge
    assert "intent(out) :: solver_may_proceed" in bridge
