from __future__ import annotations

import subprocess

from arcana_worldsim.r6.int10k_source_provenance import (
    inspect_measured_sources_git,
    qualification_exit_code,
    qualification_may_execute,
)


_PATHS = ("scripts/runner.py", "src/engine.py")


def _git(path, *args):
    return subprocess.run(["git", *args], cwd=path, check=True,
                          capture_output=True, text=True)


def _repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.invalid")
    (repo / "scripts").mkdir()
    (repo / "src").mkdir()
    (repo / _PATHS[0]).write_text("runner\n", encoding="utf-8")
    (repo / _PATHS[1]).write_text("engine\n", encoding="utf-8")
    _git(repo, "add", *(_PATHS))
    _git(repo, "commit", "-qm", "base")
    return repo, _git(repo, "rev-parse", "HEAD").stdout.strip()


def test_git_provenance_accepts_clean_exact_checkout(tmp_path):
    repo, commit = _repo(tmp_path)
    result = inspect_measured_sources_git(repo, _PATHS, expected_commit=commit)
    assert result["commit"] == commit
    assert result["status"] == "CLEAN"
    assert result["dirty"] is False
    assert result["dirty_paths"] == []
    assert result["qualification_status"] == "PASS"
    assert qualification_exit_code(result) == 0
    assert qualification_may_execute(result)


def test_git_provenance_reports_only_measured_source_changes(tmp_path):
    repo, commit = _repo(tmp_path)
    (repo / _PATHS[1]).write_text("changed\n", encoding="utf-8")
    result = inspect_measured_sources_git(repo, _PATHS, expected_commit=commit)
    assert result["status"] == "DIRTY"
    assert result["dirty"] is True
    assert result["dirty_paths"] == [_PATHS[1]]
    assert result["qualification_status"] == "FAIL"
    assert "MEASURED_SOURCES_DIRTY" in result["qualification_reasons"]
    assert qualification_exit_code(result) == 3
    assert not qualification_may_execute(result)


def test_git_provenance_detects_staged_measured_source_change(tmp_path):
    repo, commit = _repo(tmp_path)
    (repo / _PATHS[0]).write_text("staged change\n", encoding="utf-8")
    _git(repo, "add", _PATHS[0])
    result = inspect_measured_sources_git(repo, _PATHS, expected_commit=commit)
    assert result["dirty"] is True
    assert result["qualification_status"] == "FAIL"
    assert not qualification_may_execute(result)
    assert result["dirty_paths"] == [_PATHS[0]]


def test_git_provenance_detects_untracked_measured_source(tmp_path):
    repo, commit = _repo(tmp_path)
    extra = "src/new_measured.py"
    (repo / extra).write_text("new\n", encoding="utf-8")
    result = inspect_measured_sources_git(repo, (*_PATHS, extra), expected_commit=commit)
    assert result["status"] == "DIRTY"
    assert result["dirty"] is True
    assert result["dirty_paths"] == [extra]
    assert result["qualification_status"] == "FAIL"


def test_git_provenance_ignores_changes_outside_measured_sources(tmp_path):
    repo, commit = _repo(tmp_path)
    (repo / "notes.txt").write_text("unrelated\n", encoding="utf-8")
    result = inspect_measured_sources_git(repo, _PATHS, expected_commit=commit)
    assert result["status"] == "CLEAN"
    assert result["dirty"] is False
    assert result["qualification_status"] == "PASS"
    assert qualification_may_execute(result)


def test_git_provenance_keeps_unavailable_git_unknown(tmp_path):
    repo, _ = _repo(tmp_path)
    result = inspect_measured_sources_git(
        repo, _PATHS, expected_commit="a" * 40,
        git_executable="arcana-git-command-that-does-not-exist")
    assert result["commit"] is None
    assert result["status"] == "UNKNOWN"
    assert result["dirty"] is None
    assert result["dirty_paths"] is None
    assert result["qualification_status"] == "UNKNOWN"
    assert qualification_exit_code(result) == 3
    assert not qualification_may_execute(result)


def test_git_provenance_rejects_unexpected_commit_but_allows_diagnostic_mode(tmp_path):
    repo, commit = _repo(tmp_path)
    result = inspect_measured_sources_git(repo, _PATHS, expected_commit="f" * 40)
    assert result["commit"] == commit
    assert result["dirty"] is False
    assert result["qualification_status"] == "FAIL"
    assert "COMMIT_MISMATCH" in result["qualification_reasons"]
    assert qualification_exit_code(result) == 3
    assert not qualification_may_execute(result)

    diagnostic = inspect_measured_sources_git(repo, _PATHS)
    assert diagnostic["qualification_status"] == "NOT_REQUESTED"
    assert qualification_exit_code(diagnostic) == 0
    assert qualification_may_execute(diagnostic)
