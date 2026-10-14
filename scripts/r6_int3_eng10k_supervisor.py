#!/usr/bin/env python3
"""Linux-only sampled process-group supervisor for one INT-3 candidate run."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any

WALL_LIMIT_S = 900.0
RSS_LIMIT_BYTES = 2_147_483_648
OUTPUT_LIMIT_BYTES = 536_870_912
POLL_INTERVAL_S = 0.1
TERM_GRACE_S = 5.0


class SupervisionError(RuntimeError):
    pass


def _parse_stat(data: str) -> tuple[int, int, int]:
    """Return ppid, process group and start ticks from /proc/PID/stat."""
    close = data.rfind(")")
    if close < 0:
        raise SupervisionError("PROC_STAT_FORMAT_INVALID")
    fields = data[close + 1:].strip().split()
    if len(fields) < 20:
        raise SupervisionError("PROC_STAT_FIELDS_MISSING")
    try:
        return int(fields[1]), int(fields[2]), int(fields[19])
    except ValueError as exc:
        raise SupervisionError("PROC_STAT_NUMERIC_FIELD_INVALID") from exc


def _proc_group_snapshot(proc_root: Path, group_id: int) -> tuple[int, list[int]]:
    members: list[int] = []
    total_rss = 0
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            _, pgrp, _ = _parse_stat((entry / "stat").read_text())
            if pgrp != group_id:
                continue
            status = (entry / "status").read_text()
            rss_line = next(line for line in status.splitlines() if line.startswith("VmRSS:"))
            rss_kib = int(rss_line.split()[1])
        except (FileNotFoundError, ProcessLookupError):
            continue
        except (OSError, StopIteration, ValueError) as exc:
            raise SupervisionError(f"PROC_RESOURCE_SNAPSHOT_UNVERIFIABLE:{entry.name}") from exc
        members.append(int(entry.name))
        total_rss += rss_kib * 1024
    return total_rss, sorted(members)


def _tree_bytes(root: Path) -> int:
    if not root.exists():
        return 0
    total = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            raise SupervisionError("OUTPUT_SYMLINK_FORBIDDEN")
        if path.is_file():
            total += path.stat().st_size
    return total


def _terminate_group(pgid: int, process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    deadline = time.monotonic() + TERM_GRACE_S
    while time.monotonic() < deadline:
        process.poll()
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def supervise(command: list[str], *, output_dir: Path, evidence_dir: Path,
              proc_root: Path = Path("/proc")) -> dict[str, Any]:
    if not sys.platform.startswith("linux"):
        raise SupervisionError("LINUX_PROC_SUPERVISION_REQUIRED")
    if output_dir.exists() or evidence_dir.exists():
        raise SupervisionError("OUTPUT_OR_EVIDENCE_COLLISION")
    repo = Path.cwd().resolve()
    allowed_root = (repo / "outputs/r6_functional_development").resolve()
    resolved_output, resolved_evidence = output_dir.resolve(), evidence_dir.resolve()
    if (allowed_root not in resolved_output.parents or allowed_root not in resolved_evidence.parents
            or resolved_output == resolved_evidence):
        raise SupervisionError("SUPERVISION_PATH_OUTSIDE_NONCANONICAL_OUTPUT_ROOT")
    for path in (resolved_output, resolved_evidence):
        for parent in (path, *path.parents):
            if parent.is_symlink():
                raise SupervisionError("SUPERVISION_PATH_SYMLINK_FORBIDDEN")
    expected_runner = (repo / "scripts/r6_int3_eng10k.py").resolve()
    if (len(command) < 4 or Path(command[0]).resolve() != Path(sys.executable).resolve()
            or Path(command[1]).resolve() != expected_runner
            or command[2:4] != ["--mode", "execute"]):
        raise SupervisionError("ONLY_INT3_ENG10K_EXECUTION_COMMAND_ALLOWED")
    if not Path(command[0]).is_file():
        raise SupervisionError("EXECUTABLE_PATH_INVALID")
    output_dir.resolve().parent.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=False)
    stdout_path, stderr_path = evidence_dir / "child.stdout", evidence_dir / "child.stderr"
    clean_env = dict(os.environ)
    clean_env.pop("GIT_OBJECT_DIRECTORY", None)
    clean_env.pop("GIT_ALTERNATE_OBJECT_DIRECTORIES", None)
    start = time.monotonic()
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(command, cwd=Path.cwd(), env=clean_env,
                                   stdout=stdout, stderr=stderr, start_new_session=True)
        pgid = process.pid
        try:
            root_stat = (proc_root / str(process.pid) / "stat").read_text()
            _, root_group, root_start_ticks = _parse_stat(root_stat)
            root_exe = os.readlink(proc_root / str(process.pid) / "exe")
            if root_group != pgid or Path(root_exe).resolve() != Path(command[0]).resolve():
                raise SupervisionError("CHILD_PROCESS_IDENTITY_MISMATCH")
        except BaseException:
            _terminate_group(pgid, process)
            raise
        peaks = {"rss_bytes": 0, "output_bytes": 0}
        samples = 0
        reason = "UNKNOWN"
        last_members: list[int] = []
        while True:
            elapsed = time.monotonic() - start
            try:
                rss, members = _proc_group_snapshot(proc_root, pgid)
                output_bytes = _tree_bytes(output_dir) + stdout_path.stat().st_size + stderr_path.stat().st_size
            except (OSError, SupervisionError) as exc:
                reason = f"MONITORING_FAILURE:{exc}"
                _terminate_group(pgid, process)
                break
            samples += 1
            last_members = members
            peaks["rss_bytes"] = max(peaks["rss_bytes"], rss)
            peaks["output_bytes"] = max(peaks["output_bytes"], output_bytes)
            return_code = process.poll()
            if elapsed >= WALL_LIMIT_S:
                reason = "WALL_TIME_LIMIT"
            elif rss > RSS_LIMIT_BYTES:
                reason = "PROCESS_GROUP_RSS_LIMIT"
            elif output_bytes > OUTPUT_LIMIT_BYTES:
                reason = "CUMULATIVE_OUTPUT_LIMIT"
            elif return_code is not None and not members:
                reason = "NATURAL_EXIT"
                break
            elif return_code is not None:
                # A leader may exit while descendants remain; keep supervising the group.
                if elapsed >= WALL_LIMIT_S:
                    reason = "WALL_TIME_LIMIT"
            if reason != "UNKNOWN":
                _terminate_group(pgid, process)
                break
            time.sleep(POLL_INTERVAL_S)
    elapsed = time.monotonic() - start
    result = {"schema": "ARCANA_R6_INT3_ENG10K_SUPERVISION_V1",
        "command": command, "root_pid": process.pid, "root_start_ticks": root_start_ticks,
        "root_executable": root_exe, "process_group_id": pgid,
        "last_observed_group_members": last_members, "natural_exit_code": process.returncode,
        "stop_reason": reason, "elapsed_seconds": elapsed, "poll_interval_seconds": POLL_INTERVAL_S,
        "sample_count": samples, "peak_sampled_process_group_rss_bytes": peaks["rss_bytes"],
        "peak_sampled_cumulative_output_bytes": peaks["output_bytes"],
        "limits_are_sampled_not_os_enforced": True,
        "termination": "SIGTERM_THEN_SIGKILL_PROCESS_GROUP_ON_LIMIT_OR_MONITOR_FAILURE",
        "stdout": {"path": stdout_path.name, "bytes": stdout_path.stat().st_size},
        "stderr": {"path": stderr_path.name, "bytes": stderr_path.stat().st_size},
        "automatic_retry": False}
    (evidence_dir / "SUPERVISION.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        command = args.command[1:] if args.command and args.command[0] == "--" else args.command
        result = supervise(command, output_dir=args.output_dir, evidence_dir=args.evidence_dir)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["stop_reason"] == "NATURAL_EXIT" and result["natural_exit_code"] == 0 else 1
    except (OSError, SupervisionError) as exc:
        print(f"INT3_ENG10K_SUPERVISION_BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
