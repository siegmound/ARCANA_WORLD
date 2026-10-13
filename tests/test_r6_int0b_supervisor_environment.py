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
INT1D_OUTPUT = ROOT / "outputs/r6_functional_development/INT1D_TF2B_5_11_R094C025_C026_20261014_02"
INT1D_EVIDENCE = ROOT / "outputs/r6_functional_development/INT1D_SUPERVISION_20261014_02"


def _clean_git_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("GIT_OBJECT_DIRECTORY", None)
    env.pop("GIT_ALTERNATE_OBJECT_DIRECTORIES", None)
    return env


def test_real_supervisor_child_environment_and_limits(tmp_path: Path) -> None:
    pwsh = shutil.which("pwsh")
    assert pwsh is not None, "PowerShell 7 (pwsh) is required for the real supervisor launch-path test"
    supervisor_source = SUPERVISOR.read_text(encoding="utf-8")
    assert "INT0B_R1_SINGLE_ATTEMPT" not in supervisor_source
    assert "INT0B_R4_FOURTH_ATTEMPT_PENDING_AUTHORIZATION" in supervisor_source
    assert not R2_OUTPUT.exists(), "offline smoke test must not create the numerical-run destination"
    assert not INT1D_OUTPUT.exists(), "command verification must not create the INT-1D candidate destination"
    assert not INT1D_EVIDENCE.exists(), "command verification must not create the INT-1D evidence destination"

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, env=_clean_git_env(),
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    child_env = os.environ.copy()
    child_env["GIT_OBJECT_DIRECTORY"] = str(tmp_path / "invalid-parent-objects")
    child_env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = str(tmp_path / "invalid-parent-alternates")

    wrapper = tmp_path / "run-supervisor-selftest.ps1"
    wrapper.write_text(
        "$ErrorActionPreference='Stop'\n"
        f"Set-Location -LiteralPath '{ROOT}'\n"
        f"[Environment]::CurrentDirectory = '{tmp_path}'\n"
        f"& '{SUPERVISOR}' -Mode SelfTest -PythonPath '{Path(sys.base_prefix) / 'python.exe'}' "
        f"-RepositoryRoot '{ROOT}' -EvidenceDirectory '{tmp_path / 'evidence'}' -ExpectedHead '{head}'\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [pwsh, "-NoLogo", "-NoProfile", "-File", str(wrapper)],
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
    assert by_label["tree_wall_limit"]["termination_classification"] == "RESOURCE_LIMIT_TERMINATED"
    assert by_label["working_set_limit"]["stop_reason"] == "PROCESS_TREE_WORKING_SET_LIMIT"
    assert by_label["working_set_limit"]["termination_classification"] == "RESOURCE_LIMIT_TERMINATED"
    assert by_label["output_limit"]["stop_reason"] == "CUMULATIVE_OUTPUT_LIMIT"
    assert by_label["output_limit"]["termination_classification"] == "RESOURCE_LIMIT_TERMINATED"
    assert by_label["exit_code_propagation"]["exit_code"] == 23
    assert by_label["exit_code_propagation"]["termination_classification"] == "NATURAL_EXIT_NONZERO"
    assert Path(by_label["exit_code_propagation"]["stderr_path"]).read_text(
        encoding="utf-8").strip() == "nonzero-error"
    stream_limit = by_label["captured_stream_output_limit"]
    assert stream_limit["stop_reason"] == "CUMULATIVE_OUTPUT_LIMIT"
    assert stream_limit["final_output_bytes"] >= 32768
    assert stream_limit["stdout_bytes"] >= 32768
    streams = by_label["diagnostic_stream_capture"]
    assert streams["stop_reason"] == "NATURAL_EXIT" and streams["exit_code"] == 0
    assert Path(streams["stdout_path"]).read_text(encoding="utf-8").strip() == "stdout-diagnostic"
    assert Path(streams["stderr_path"]).read_text(encoding="utf-8").strip() == "stderr-diagnostic"
    assert streams["stdout_bytes"] > 0 and streams["stderr_bytes"] > 0
    assert len(streams["stdout_sha256"]) == len(streams["stderr_sha256"]) == 64
    assert by_label["natural_exit_between_poll_and_snapshot"]["stop_reason"] == "NATURAL_EXIT"
    assert by_label["natural_exit_between_poll_and_snapshot"]["exit_code"] == 31
    assert by_label["natural_exit_between_poll_and_snapshot"]["termination_classification"] == "NATURAL_EXIT_NONZERO"
    assert by_label["genuine_process_identity_loss"]["stop_reason"] == "MONITOR_ROOT_IDENTITY_LOST"
    assert by_label["genuine_process_identity_loss"]["termination_classification"] == "PROCESS_IDENTITY_LOSS"
    identity = json.loads(report_path.parent.joinpath("git-provenance-result.json").read_text(encoding="utf-8-sig"))
    assert identity["pid"] == by_label["sanitized_child_git_provenance"]["root_pid"]
    assert identity["git_head"] == head
    assert identity["object_type"] == "commit"
    assert identity["git_top_level_returncode"] == identity["git_head_returncode"] == identity["object_returncode"] == 0
    assert identity["git_environment"].get("GIT_OBJECT_DIRECTORY") is None
    assert identity["git_environment"].get("GIT_ALTERNATE_OBJECT_DIRECTORIES") is None
    evidence_root = report_path.parent.resolve()
    assert evidence_root.is_relative_to(tmp_path.resolve())
    for trace_path in evidence_root.glob("*.ndjson"):
        assert trace_path.resolve().parent == evidence_root
        summary_path = Path(str(trace_path) + ".summary.json")
        assert summary_path.resolve().parent == evidence_root
        assert summary_path.is_file()
    for row in rows:
        for key in ("stdout_path", "stderr_path"):
            stream_path = Path(row[key]).resolve()
            assert stream_path.parent == evidence_root
            assert stream_path.is_file()


def test_int1d_verify_run_is_root_anchored_and_does_not_start_or_create(tmp_path: Path) -> None:
    pwsh = shutil.which("pwsh")
    assert pwsh is not None, "PowerShell 7 (pwsh) is required for the real supervisor command-verification test"
    wrapper = tmp_path / "verify-int1d.ps1"
    wrapper.write_text(
        "$ErrorActionPreference='Stop'\n"
        f"Set-Location -LiteralPath '{ROOT}'\n"
        f"[Environment]::CurrentDirectory = '{tmp_path}'\n"
        f"& '{SUPERVISOR}' -Mode VerifyRun -RepositoryRoot '{ROOT}' "
        f"-OutputRelative '{INT1D_OUTPUT.relative_to(ROOT).as_posix()}' "
        f"-EvidenceDirectory '{INT1D_EVIDENCE.relative_to(ROOT).as_posix()}' "
        "-BoundaryId 'R6BND-T0-27e4d497530e681071fb' "
        "-AdditionalResolutionFactor '0.000125' -DiagnosticResolutionFactor '0.000125'\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [pwsh, "-NoLogo", "-NoProfile", "-File", str(wrapper)], cwd=ROOT,
        env=_clean_git_env(), capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"INT-1D command verification failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    plan = json.loads(result.stdout)
    assert plan["status"] == "RUN_COMMAND_VERIFIED_NO_NUMERICAL_CHILD_STARTED"
    assert plan["label"] == "INT1D_DISTINCT_BOUNDARY_NONCANONICAL_ATTEMPT"
    assert plan["working_directory"] == str(ROOT)
    assert plan["output_path"] == str(INT1D_OUTPUT)
    assert plan["evidence_path"] == str(INT1D_EVIDENCE)
    assert plan["output_path_absent"] and plan["evidence_path_absent"]
    assert plan["python_executable_exists"]
    assert plan["arcana_external_root"] == str(ROOT.parents[1] / "_ARCANA_EXTERNAL_SOURCES")
    assert plan["child_git_object_directory_removed"]
    assert plan["child_git_alternate_object_directories_removed"]
    assert plan["wall_seconds"] == 900
    assert plan["process_tree_working_set_limit_bytes"] == 2 * 1024**3
    assert plan["cumulative_output_limit_bytes"] == 512 * 1024**2
    assert plan["arguments"] == [
        str(ROOT / "scripts/r6_functional_development_t_f2b.py"),
        "--repository-root", str(ROOT), "--expected-branch", "r6/si1-bandwidth-f2av",
        "--boundary-id", "R6BND-T0-27e4d497530e681071fb",
        "--additional-resolution-factor", "0.000125",
        "--diagnostic-resolution-factor", "0.000125",
        "--output-relative", INT1D_OUTPUT.relative_to(ROOT).as_posix(),
    ]
    assert not INT1D_OUTPUT.exists()
    assert not INT1D_EVIDENCE.exists()


def test_int1d_verify_run_rejects_incomplete_or_inconsistent_overrides(tmp_path: Path) -> None:
    pwsh = shutil.which("pwsh")
    assert pwsh is not None
    cases = [
        ("-BoundaryId 'R6BND-T0-27e4d497530e681071fb'", "INT1D_OVERRIDES_MUST_BE_COMPLETE"),
        ("-BoundaryId 'R6BND-T0-27e4d497530e681071fb' -AdditionalResolutionFactor '0.000125' -DiagnosticResolutionFactor '0.00025'",
         "INT1D_DIAGNOSTIC_RESOLUTION_MUST_MATCH_ADDITIONAL"),
    ]
    for index, (options, expected_error) in enumerate(cases):
        wrapper = tmp_path / f"invalid-int1d-{index}.ps1"
        wrapper.write_text(
            "$ErrorActionPreference='Stop'\n"
            f"Set-Location -LiteralPath '{ROOT}'\n"
            f"& '{SUPERVISOR}' -Mode VerifyRun -RepositoryRoot '{ROOT}' "
            f"-OutputRelative 'outputs/r6_functional_development/invalid-test-{index}' "
            f"-EvidenceDirectory 'outputs/r6_functional_development/invalid-evidence-{index}' {options}\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [pwsh, "-NoLogo", "-NoProfile", "-File", str(wrapper)], cwd=ROOT,
            env=_clean_git_env(), capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0
        assert expected_error in result.stderr


def test_verify_run_keeps_legacy_r4_defaults(tmp_path: Path) -> None:
    pwsh = shutil.which("pwsh")
    assert pwsh is not None
    evidence = tmp_path / "legacy-evidence"
    output = ROOT / "outputs/r6_functional_development/INT0B_SUPERVISOR_VERIFY_ONLY"
    result = subprocess.run(
        [pwsh, "-NoLogo", "-NoProfile", "-File", str(SUPERVISOR), "-Mode", "VerifyRun",
         "-RepositoryRoot", str(ROOT), "-OutputRelative", output.relative_to(ROOT).as_posix(), "-EvidenceDirectory", str(evidence)],
        cwd=ROOT, env=_clean_git_env(), capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"legacy command verification failed\n{result.stderr}"
    plan = json.loads(result.stdout)
    assert plan["label"] == "INT0B_R4_FOURTH_ATTEMPT_PENDING_AUTHORIZATION"
    assert plan["arguments"] == [
        str(ROOT / "scripts/r6_functional_development_t_f2b.py"),
        "--repository-root", str(ROOT), "--expected-branch", "r6/si1-bandwidth-f2av",
        "--output-relative", output.relative_to(ROOT).as_posix(),
    ]
    assert not evidence.exists() and not output.exists()
