from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "scripts" / "r6_int0b_supervisor.ps1"
R2_OUTPUT = ROOT / "outputs/r6_functional_development/INT0B_TF2B_5_11_R2_20261013_03"


def _clean_git_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("GIT_OBJECT_DIRECTORY", None)
    env.pop("GIT_ALTERNATE_OBJECT_DIRECTORIES", None)
    return env


def test_real_supervisor_child_environment_and_limits(tmp_path: Path) -> None:
    pwsh = shutil.which("pwsh")
    assert pwsh is not None, "PowerShell 7 (pwsh) is required for the real supervisor launch-path test"
    assert not R2_OUTPUT.exists(), "offline smoke test must not create the numerical-run destination"

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, env=_clean_git_env(),
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    child_env = os.environ.copy()
    child_env["GIT_OBJECT_DIRECTORY"] = str(tmp_path / "invalid-parent-objects")
    child_env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = str(tmp_path / "invalid-parent-alternates")

    result = subprocess.run(
        [pwsh, "-NoLogo", "-NoProfile", "-File", str(SUPERVISOR),
         "-Mode", "SelfTest", "-PythonPath", str(Path(sys.base_prefix) / "python.exe"),
         "-RepositoryRoot", str(ROOT), "-EvidenceDirectory", str(tmp_path / "evidence"),
         "-ExpectedHead", head],
        cwd=ROOT, env=child_env, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, f"supervisor self-test failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "SUPERVISOR_SELFTEST_PASS" in result.stdout
    assert not R2_OUTPUT.exists(), "smoke test must not invoke the numerical runner or publish its output"

    report_path = next((tmp_path / "evidence").glob("selftest-*/selftest-results.json"))
    rows = json.loads(report_path.read_text(encoding="utf-8-sig"))
    by_label = {row["label"]: row for row in rows}
    assert by_label["expected_environment_failure_without_sanitization"]["exit_code"] != 0
    assert by_label["sanitized_child_git_provenance"]["exit_code"] == 0
    assert set(by_label["sanitized_child_git_provenance"]["child_git_object_environment_removed"]) == {
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"
    }
    assert by_label["tree_wall_limit"]["stop_reason"] == "WALL_TIME_LIMIT"
    assert by_label["working_set_limit"]["stop_reason"] == "PROCESS_TREE_WORKING_SET_LIMIT"
    assert by_label["output_limit"]["stop_reason"] == "CUMULATIVE_OUTPUT_LIMIT"
    assert by_label["exit_code_propagation"]["exit_code"] == 23
    identity = json.loads(report_path.parent.joinpath("git-provenance-result.json").read_text(encoding="utf-8-sig"))
    assert identity["pid"] == by_label["sanitized_child_git_provenance"]["root_pid"]
    assert identity["git_head"] == head
    assert identity["object_type"] == "commit"
    assert identity["git_top_level_returncode"] == identity["git_head_returncode"] == identity["object_returncode"] == 0
    assert identity["git_environment"].get("GIT_OBJECT_DIRECTORY") is None
    assert identity["git_environment"].get("GIT_ALTERNATE_OBJECT_DIRECTORIES") is None
