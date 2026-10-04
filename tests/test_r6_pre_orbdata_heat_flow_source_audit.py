from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from _git_test_env import isolated_git_environment


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "r6_pre_orbdata_heat_flow_source_audit.py"
SPEC = importlib.util.spec_from_file_location("r6_heat_audit", SCRIPT)
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], check=True,
                            capture_output=True, text=True,
                            env=isolated_git_environment())
    return result.stdout.strip()


def init_fixture_repo(root: Path, branch: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-b", branch, str(root)], check=True,
                   capture_output=True, text=True, env=isolated_git_environment())
    git(root, "config", "user.name", "Audit fixture")
    git(root, "config", "user.email", "audit-fixture@example.invalid")


def commit_fixture_files(root: Path) -> None:
    git(root, "add", "src/OrbData.f90", "INPUT/model.in", "tracked.bin")
    git(root, "commit", "-m", "fixture source evidence")


def test_source_scan_uses_tracked_text_files_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("GIT_OBJECT_DIRECTORY", raising=False)
    monkeypatch.delenv("GIT_ALTERNATE_OBJECT_DIRECTORIES", raising=False)
    root = tmp_path / "ShellSet-fixture"
    init_fixture_repo(root, "fixture-qualified-name")
    source = root / "src" / "OrbData.f90"
    source.parent.mkdir()
    source.write_text("needQ = (heatFl == 0.0D0)\nREAD(unit,*) qLim0\nCALL Assign(heatFl)\n")
    parameters = root / "INPUT" / "model.in"
    parameters.parent.mkdir()
    parameters.write_text("alphaT = configured_by_fixture\n")
    (root / "tracked.bin").write_bytes(b"binary fixture")
    commit_fixture_files(root)
    source.write_text("qLim1 = dirty_worktree_content\n")

    runtime = root / "NVHPC_ARCANA_PATCH_ListEx1_n10_t5_fixture"
    runtime.mkdir()
    (runtime / "untracked.f90").write_text("qArray = qLim1\ndelta_rho_limit = 8\n")
    (runtime / "untracked.txt").write_text("ZBASTH TADIAB GRADIE")

    tracked = audit.iter_text_files(root)
    excerpts = audit.extract_contexts(root, tracked)
    bindings = audit.extract_binding_and_callsite_contexts(root, tracked)

    assert [path.relative_to(root).as_posix() for path in tracked] == ["INPUT/model.in", "src/OrbData.f90"]
    assert len(tracked) == 2
    assert excerpts["heatFl"][0]["path"] == "src/OrbData.f90"
    assert excerpts["alphaT"][0]["path"] == "INPUT/model.in"
    assert excerpts["qArray"] == []
    assert excerpts["qLim1"] == []
    assert excerpts["delta_rho_limit"] == []
    assert excerpts["ZBASTH"] == []
    assert any(hit["line"] == 2 and "qLim0" in hit["matched_symbols_in_neighborhood"] for hit in bindings)
    assert any(hit["line"] == 3 and "heatFl" in hit["matched_symbols_in_neighborhood"] for hit in bindings)
    provenance = audit.source_file_authority_record(len(tracked))
    assert provenance == {
        "method": "GIT_TRACKED_FILES_ONLY",
        "command": "git ls-files -z",
        "untracked_files_scanned": False,
        "tracked_text_files_scanned": 2,
        "content_source": "verified HEAD blobs via git show HEAD:<tracked-path>",
    }


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


def test_branch_and_commit_identity_mismatches_fail_closed(tmp_path: Path) -> None:
    wrong_branch = tmp_path / "wrong-branch"
    init_fixture_repo(wrong_branch, "not-the-qualified-branch")
    with_branch = wrong_branch / "tracked.txt"
    with_branch.write_text("fixture only")
    git(wrong_branch, "add", "tracked.txt")
    git(wrong_branch, "commit", "-m", "wrong branch")
    try:
        audit.verify_checkout(wrong_branch)
    except ValueError as exc:
        assert "unqualified ShellSet branch" in str(exc)
    else:
        raise AssertionError("wrong branch must fail the qualified-source identity gate")

    wrong_commit = tmp_path / "wrong-commit"
    init_fixture_repo(wrong_commit, audit.EXPECTED_BRANCH)
    with_commit = wrong_commit / "tracked.txt"
    with_commit.write_text("fixture only")
    git(wrong_commit, "add", "tracked.txt")
    git(wrong_commit, "commit", "-m", "wrong commit")
    try:
        audit.verify_checkout(wrong_commit)
    except ValueError as exc:
        assert "unqualified ShellSet commit" in str(exc)
    else:
        raise AssertionError("wrong commit must fail the qualified-source identity gate")


def test_audit_outputs_cannot_modify_shellset_checkout(tmp_path: Path) -> None:
    source = tmp_path / "ShellSet"
    source.mkdir()
    try:
        audit.ensure_output_outside_source(source, [source / "audit.json"])
    except ValueError as exc:
        assert "refusing to write audit output inside ShellSet checkout" in str(exc)
    else:
        raise AssertionError("audit output must never be written inside ShellSet")
