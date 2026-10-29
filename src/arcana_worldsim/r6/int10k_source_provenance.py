"""Git provenance for the measured INT10K implementation source files."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Sequence


_FULL_GIT_OBJECT_ID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def inspect_measured_sources_git(
    repository: Path,
    source_paths: Sequence[str],
    *,
    expected_commit: str | None = None,
    git_executable: str = "git",
) -> dict[str, Any]:
    """Return HEAD and path-scoped dirty state; Git failures remain UNKNOWN.

    `git status --porcelain --untracked-files=all -- <paths>` includes staged,
    unstaged, deleted, and untracked entries for the measured paths only.
    """
    if expected_commit is not None and not _FULL_GIT_OBJECT_ID.fullmatch(expected_commit):
        raise ValueError("EXPECTED_COMMIT_MUST_BE_FULL_LOWERCASE_GIT_OBJECT_ID")
    paths = tuple(source_paths)
    if not paths or any(Path(path).is_absolute() or ".." in Path(path).parts for path in paths):
        raise ValueError("MEASURED_SOURCE_PATHS_MUST_BE_REPOSITORY_RELATIVE")

    result: dict[str, Any] = {
        "commit": None,
        "status": "UNKNOWN",
        "dirty": None,
        "dirty_paths": None,
        "expected_commit": expected_commit,
        "qualification_status": "NOT_REQUESTED" if expected_commit is None else "UNKNOWN",
        "qualification_reasons": [],
    }
    try:
        commit_run = subprocess.run(
            [git_executable, "rev-parse", "--verify", "HEAD"],
            cwd=repository, check=True, capture_output=True, text=True)
        commit = commit_run.stdout.strip()
        if not _FULL_GIT_OBJECT_ID.fullmatch(commit):
            return result
        status_run = subprocess.run(
            [git_executable, "status", "--porcelain=v1", "--untracked-files=all", "--", *paths],
            cwd=repository, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        return result

    dirty_rows = [line for line in status_run.stdout.splitlines() if line]
    dirty_paths = sorted({line[3:] for line in dirty_rows})
    result.update({"commit": commit, "status": "DIRTY" if dirty_rows else "CLEAN",
                   "dirty": bool(dirty_rows), "dirty_paths": dirty_paths})
    if expected_commit is not None:
        reasons = []
        if commit != expected_commit:
            reasons.append("COMMIT_MISMATCH")
        if dirty_rows:
            reasons.append("MEASURED_SOURCES_DIRTY")
        result["qualification_status"] = "FAIL" if reasons else "PASS"
        result["qualification_reasons"] = reasons
    return result


def qualification_exit_code(git_provenance: dict[str, Any]) -> int:
    """Nonzero when an explicitly requested exact-source gate did not pass."""
    if git_provenance.get("expected_commit") is not None:
        return 0 if git_provenance.get("qualification_status") == "PASS" else 3
    return 0


def qualification_may_execute(git_provenance: dict[str, Any]) -> bool:
    """Diagnostic mode may run; requested exact qualification needs a PASS gate."""
    return (git_provenance.get("expected_commit") is None
            or git_provenance.get("qualification_status") == "PASS")
