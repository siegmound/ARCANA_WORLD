#!/usr/bin/env python3
"""Linux-only sampled process-group supervisor for one INT-3 candidate run."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.r6.int3_eng10k import (  # noqa: E402
    Eng10kContractError, _resolve_checked_path, create_evidence_attempt_parent,
    resolve_evidence_destinations,
)

WALL_LIMIT_S = 900.0
RSS_LIMIT_BYTES = 2_147_483_648
OUTPUT_LIMIT_BYTES = 536_870_912
POLL_INTERVAL_S = 0.1
OBSERVE_POLL_INTERVAL_S = 1.0
NATURAL_EXIT_CONFIRMATION_S = 0.5
TERM_GRACE_S = 5.0
_TERMINAL_PROC_STATES = {"Z", "X", "x"}


class SupervisionError(RuntimeError):
    pass


def _update_empty_group_confirmation(return_code: int | None, members: list[int],
                                     now: float, empty_since: float | None
                                     ) -> tuple[bool, float | None]:
    """Confirm repeated empty snapshots only after the leader has exited."""
    if return_code is None or members:
        return False, None
    if empty_since is None:
        return False, now
    return now - empty_since >= NATURAL_EXIT_CONFIRMATION_S, empty_since


def _parse_stat(data: str) -> tuple[str, int, int, int]:
    """Return state, ppid, process group and start ticks from /proc/PID/stat."""
    close = data.rfind(")")
    if close < 0:
        raise SupervisionError("PROC_STAT_FORMAT_INVALID")
    fields = data[close + 1:].strip().split()
    if len(fields) < 20:
        raise SupervisionError("PROC_STAT_FIELDS_MISSING")
    if len(fields[0]) != 1 or fields[0] not in "RSDZTWtXxKWPIN":
        raise SupervisionError("PROC_STAT_STATE_INVALID")
    try:
        return fields[0], int(fields[1]), int(fields[2]), int(fields[19])
    except ValueError as exc:
        raise SupervisionError("PROC_STAT_NUMERIC_FIELD_INVALID") from exc


def _proc_group_snapshot(proc_root: Path, group_id: int, *,
                         expected_leader_start_ticks: int | None = None) -> tuple[int, list[int]]:
    """Sample live members only; tolerate exit races but reject unverifiable live RSS."""
    members: list[int] = []
    total_rss = 0
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            first = _parse_stat((entry / "stat").read_text())
        except (FileNotFoundError, ProcessLookupError):
            continue
        except (OSError, SupervisionError) as exc:
            raise SupervisionError(f"PROC_STAT_UNVERIFIABLE:{entry.name}") from exc
        state, _, pgrp, start_ticks = first
        if pgrp != group_id:
            continue
        if (pid == group_id and expected_leader_start_ticks is not None
                and start_ticks != expected_leader_start_ticks):
            raise SupervisionError(f"PROC_LEADER_IDENTITY_CHANGED:{entry.name}")
        if state in _TERMINAL_PROC_STATES:
            continue
        try:
            status = (entry / "status").read_text()
            rss_line = next(line for line in status.splitlines() if line.startswith("VmRSS:"))
            fields = rss_line.split()
            if len(fields) < 2 or (len(fields) >= 3 and fields[2] != "kB"):
                raise ValueError("invalid VmRSS fields")
            rss_kib = int(fields[1])
            if rss_kib < 0:
                raise ValueError("negative VmRSS")
        except (OSError, StopIteration, ValueError) as exc:
            # /proc may lose a process between stat and status. Recheck identity/state
            # before failing: only a vanished or now-terminal process is ignorable.
            try:
                current = _parse_stat((entry / "stat").read_text())
            except (FileNotFoundError, ProcessLookupError):
                continue
            except (OSError, SupervisionError) as stat_exc:
                raise SupervisionError(f"PROC_RESOURCE_SNAPSHOT_UNVERIFIABLE:{entry.name}") from stat_exc
            if current[3] != start_ticks:
                raise SupervisionError(f"PROC_PID_IDENTITY_CHANGED:{entry.name}") from exc
            if current[2] != group_id or current[0] in _TERMINAL_PROC_STATES:
                continue
            raise SupervisionError(f"PROC_RESOURCE_SNAPSHOT_UNVERIFIABLE:{entry.name}") from exc
        try:
            current = _parse_stat((entry / "stat").read_text())
        except (FileNotFoundError, ProcessLookupError):
            continue
        except (OSError, SupervisionError) as exc:
            raise SupervisionError(f"PROC_STAT_UNVERIFIABLE:{entry.name}") from exc
        if current[3] != start_ticks or current[2] != group_id:
            raise SupervisionError(f"PROC_PID_IDENTITY_CHANGED:{entry.name}")
        if current[0] in _TERMINAL_PROC_STATES:
            continue
        members.append(pid)
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


def _expected_child_command(command: list[str], *, root: Path, output_relative: Path,
                            supervision_relative: Path, r4_bundle: Path,
                            expected_head: str, authorization_json: Path) -> list[str]:
    runner = (ROOT / "scripts/r6_int3_eng10k.py").resolve()
    required = ["--mode", "execute", "--evidence-root", str(root),
        "--output-relative", output_relative.as_posix(),
        "--supervision-relative", supervision_relative.as_posix(),
        "--r4-bundle", str(_resolve_checked_path(r4_bundle, strict=True)),
        "--expected-head", expected_head,
        "--authorization-json", str(_resolve_checked_path(authorization_json, strict=True))]
    if (len(command) != 2 + len(required)
            or Path(command[0]).resolve() != Path(sys.executable).resolve()
            or Path(command[1]).resolve() != runner
            or command[2:] != required):
        raise SupervisionError("ONLY_EXACT_BOUND_INT3_ENG10K_COMMAND_ALLOWED")
    return required


def _validate_observe_authorization(path: Path, *, source_head: str,
                                    evidence_root: Path, output_relative: Path,
                                    output_absolute: Path, supervision_relative: Path,
                                    supervision_absolute: Path) -> None:
    """Require an explicit observe-only record with no legacy budget fields."""
    try:
        value = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as exc:
        raise SupervisionError("OBSERVE_ONLY_AUTHORIZATION_UNREADABLE") from exc
    expected = {
        "decision": "CONDITIONAL_GO_INT3_ENG10K_NONCANONICAL_RUN",
        "supervision_mode": "OBSERVE_ONLY",
        "resource_enforcement": "OBSERVE_ONLY_NO_THRESHOLDS",
        "source_head": source_head,
        "evidence_root_absolute": str(evidence_root),
        "output_relative": output_relative.as_posix(),
        "output_absolute": str(output_absolute),
        "supervision_relative": supervision_relative.as_posix(),
        "supervision_absolute": str(supervision_absolute),
        "one_attempt_only": True,
        "noncanonical": True,
    }
    config_path = ROOT / "configs/r6_int3_eng10k/engineering_case.json"
    try:
        config_sha = hashlib.sha256(config_path.read_bytes()).hexdigest()
    except OSError as exc:
        raise SupervisionError("OBSERVE_ONLY_CONFIGURATION_UNAVAILABLE") from exc
    expected["configuration_sha256"] = config_sha
    if (not isinstance(value, dict) or "limits" in value
            or any(value.get(key) != expected_value for key, expected_value in expected.items())):
        raise SupervisionError("OBSERVE_ONLY_AUTHORIZATION_MISMATCH")


def _proc_telemetry(proc_root: Path, group_id: int, members: list[int], *,
                    expected_leader_start_ticks: int) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Collect best-effort CPU/I/O details for already identity-checked live PIDs."""
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    ticks_per_second = os.sysconf("SC_CLK_TCK")
    for pid in members:
        entry = proc_root / str(pid)
        try:
            stat_text = (entry / "stat").read_text()
            stat_before = _parse_stat(stat_text)
            raw_fields = stat_text.rsplit(")", 1)[1].strip().split()
            if stat_before[2] != group_id:
                raise SupervisionError("PROC_GROUP_CHANGED")
            if stat_before[0] in _TERMINAL_PROC_STATES:
                continue
            if pid == group_id and stat_before[3] != expected_leader_start_ticks:
                raise SupervisionError("PROC_LEADER_IDENTITY_CHANGED")
            utime_ticks, stime_ticks = int(raw_fields[11]), int(raw_fields[12])
            status = (entry / "status").read_text()
            rss_line = next(line for line in status.splitlines() if line.startswith("VmRSS:"))
            rss_kib = int(rss_line.split()[1])
            row: dict[str, Any] = {
                "pid": pid, "ppid": stat_before[1], "process_group_id": stat_before[2],
                "start_ticks": stat_before[3], "state": stat_before[0],
                "rss_bytes": rss_kib * 1024,
                "user_cpu_seconds": utime_ticks / ticks_per_second,
                "system_cpu_seconds": stime_ticks / ticks_per_second,
            }
            try:
                io_values: dict[str, int] = {}
                for line in (entry / "io").read_text().splitlines():
                    key, sep, value = line.partition(":")
                    if sep and key in {"read_bytes", "write_bytes"}:
                        io_values[key] = int(value.strip())
                if set(io_values) != {"read_bytes", "write_bytes"}:
                    raise ValueError("I/O counters incomplete")
                row.update({"read_bytes": io_values["read_bytes"],
                            "write_bytes": io_values["write_bytes"]})
            except (OSError, ValueError) as exc:
                errors.append({"pid": str(pid), "metric": "io_bytes",
                               "error": f"{type(exc).__name__}:{exc}"})
            stat_after = _parse_stat((entry / "stat").read_text())
            if stat_after[3] != stat_before[3] or stat_after[2] != group_id:
                raise SupervisionError("PROC_PID_IDENTITY_CHANGED")
            rows.append(row)
        except (FileNotFoundError, ProcessLookupError):
            errors.append({"pid": str(pid), "metric": "process_detail",
                           "error": "PID_DISAPPEARED_DURING_TELEMETRY"})
        except SupervisionError:
            raise
        except (OSError, ValueError, IndexError) as exc:
            errors.append({"pid": str(pid), "metric": "process_detail",
                           "error": f"{type(exc).__name__}:{exc}"})
    return rows, errors


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _supervise_observe_only(command: list[str], *, root: Path, output_dir: Path,
                            evidence_dir: Path, expected_head: str,
                            proc_root: Path) -> dict[str, Any]:
    stdout_path, stderr_path = evidence_dir / "child.stdout", evidence_dir / "child.stderr"
    samples_path = evidence_dir / "resource_samples.jsonl"
    markers_path = evidence_dir / "TRAJECTORY_MARKERS.jsonl"
    samples_path.touch(exist_ok=False)
    markers_path.touch(exist_ok=False)
    clean_env = dict(os.environ)
    clean_env.pop("GIT_OBJECT_DIRECTORY", None)
    clean_env.pop("GIT_ALTERNATE_OBJECT_DIRECTORIES", None)
    clean_env["ARCANA_INT3_TRAJECTORY_MARKERS"] = str(markers_path.resolve())
    started = time.monotonic()
    start_utc = _utc_now()
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr, \
            samples_path.open("ab", buffering=0) as samples_stream:
        process = subprocess.Popen(command, cwd=ROOT, env=clean_env,
                                   stdout=stdout, stderr=stderr, start_new_session=True)
        pgid = process.pid
        try:
            _, root_ppid, root_group, root_start_ticks = _parse_stat(
                (proc_root / str(process.pid) / "stat").read_text())
            root_exe = os.readlink(proc_root / str(process.pid) / "exe")
            if (root_group != pgid or Path(root_exe).resolve() != Path(command[0]).resolve()):
                raise SupervisionError("CHILD_PROCESS_IDENTITY_MISMATCH")
        except BaseException:
            _terminate_group(pgid, process)
            raise

        previous_handlers: dict[int, Any] = {}
        stop_signal: int | None = None

        def on_signal(signum, _frame):
            nonlocal stop_signal
            stop_signal = signum

        for signum in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[signum] = signal.signal(signum, on_signal)

        sample_count = 0
        lost_samples = 0
        telemetry_errors: list[dict[str, str]] = []
        per_identity_totals: dict[str, dict[str, float]] = {}
        per_identity_peaks: dict[str, dict[str, float]] = {}
        previous_counters: dict[str, tuple[float, float, int, int]] = {}
        peaks = {"process_group_rss_bytes": 0, "cumulative_output_bytes": 0,
                 "sampled_group_cpu_seconds": 0.0, "sampled_group_read_bytes": 0,
                 "sampled_group_write_bytes": 0}
        last_members: list[int] = []
        empty_since: float | None = None
        reason = "UNKNOWN"
        final_group: dict[str, Any] | None = None
        try:
            while True:
                return_code = process.poll()
                try:
                    rss, members = _proc_group_snapshot(
                        proc_root, pgid, expected_leader_start_ticks=root_start_ticks)
                    output_bytes = (_tree_bytes(output_dir) + stdout_path.stat().st_size
                                    + stderr_path.stat().st_size + samples_path.stat().st_size
                                    + markers_path.stat().st_size)
                    details, detail_errors = _proc_telemetry(
                        proc_root, pgid, members,
                        expected_leader_start_ticks=root_start_ticks)
                except (OSError, SupervisionError) as exc:
                    reason = f"MONITORING_FAILURE:{exc}"
                    _terminate_group(pgid, process)
                    break
                now = time.monotonic()
                elapsed = now - started
                aggregate_cpu = sum(float(row["user_cpu_seconds"])
                                     + float(row["system_cpu_seconds"]) for row in details)
                aggregate_read = sum(int(row.get("read_bytes", 0)) for row in details)
                aggregate_write = sum(int(row.get("write_bytes", 0)) for row in details)
                for row in details:
                    identity = f"{row['pid']}:{row['start_ticks']}"
                    counters = (float(row["user_cpu_seconds"]), float(row["system_cpu_seconds"]),
                                int(row.get("read_bytes", 0)), int(row.get("write_bytes", 0)))
                    previous = previous_counters.get(identity)
                    totals = per_identity_totals.setdefault(identity, {
                        "user_cpu_seconds_delta": 0.0, "system_cpu_seconds_delta": 0.0,
                        "read_bytes_delta": 0, "write_bytes_delta": 0})
                    individual_peak = per_identity_peaks.setdefault(identity, {
                        "rss_bytes": 0, "user_cpu_seconds": 0.0,
                        "system_cpu_seconds": 0.0, "read_bytes": 0, "write_bytes": 0})
                    for metric in individual_peak:
                        individual_peak[metric] = max(individual_peak[metric], row.get(metric, 0))
                    if previous is not None:
                        totals["user_cpu_seconds_delta"] += max(0.0, counters[0] - previous[0])
                        totals["system_cpu_seconds_delta"] += max(0.0, counters[1] - previous[1])
                        totals["read_bytes_delta"] += max(0, counters[2] - previous[2])
                        totals["write_bytes_delta"] += max(0, counters[3] - previous[3])
                    previous_counters[identity] = counters
                row = {
                    "schema": "ARCANA_R6_INT3_RESOURCE_SAMPLE_V1",
                    "timestamp_utc": _utc_now(), "elapsed_seconds": elapsed,
                    "root_pid": process.pid, "root_start_ticks": root_start_ticks,
                    "process_group_id": pgid, "live_processes": details,
                    "aggregate_sampled": {"process_group_rss_bytes": rss,
                        "user_plus_system_cpu_seconds": aggregate_cpu,
                        "read_bytes": aggregate_read, "write_bytes": aggregate_write,
                        "cumulative_output_bytes": output_bytes},
                    "metric_errors": detail_errors,
                }
                try:
                    samples_stream.write((json.dumps(row, sort_keys=True, allow_nan=False) + "\n").encode())
                    samples_stream.flush()
                except (OSError, TypeError, ValueError) as exc:
                    lost_samples += 1
                    reason = f"TELEMETRY_WRITE_FAILURE:{type(exc).__name__}:{exc}"
                    _terminate_group(pgid, process)
                    break
                sample_count += 1
                telemetry_errors.extend(detail_errors)
                last_members = members
                peaks["process_group_rss_bytes"] = max(peaks["process_group_rss_bytes"], rss)
                peaks["cumulative_output_bytes"] = max(peaks["cumulative_output_bytes"], output_bytes)
                peaks["sampled_group_cpu_seconds"] = max(peaks["sampled_group_cpu_seconds"], aggregate_cpu)
                peaks["sampled_group_read_bytes"] = max(peaks["sampled_group_read_bytes"], aggregate_read)
                peaks["sampled_group_write_bytes"] = max(peaks["sampled_group_write_bytes"], aggregate_write)
                final_group = row["aggregate_sampled"]
                if stop_signal is not None:
                    reason = f"SUPERVISOR_SIGNAL:{stop_signal}"
                    _terminate_group(pgid, process)
                    break
                confirmed, empty_since = _update_empty_group_confirmation(
                    return_code, members, now, empty_since)
                if confirmed:
                    reason = "NATURAL_EXIT"
                    break
                time.sleep(OBSERVE_POLL_INTERVAL_S)
        finally:
            for signum, handler in previous_handlers.items():
                signal.signal(signum, handler)

    elapsed = time.monotonic() - started
    try:
        final_output_bytes: int | None = (
            _tree_bytes(output_dir) + stdout_path.stat().st_size + stderr_path.stat().st_size
            + samples_path.stat().st_size + markers_path.stat().st_size)
    except (OSError, SupervisionError) as exc:
        final_output_bytes = None
        telemetry_errors.append({"pid": "supervisor", "metric": "final_output_bytes",
                                 "error": f"{type(exc).__name__}:{exc}"})
    process_lifetime_totals = {
        "user_plus_system_cpu_seconds": sum(value[0] + value[1]
                                              for value in previous_counters.values()),
        "read_bytes": sum(value[2] for value in previous_counters.values()),
        "write_bytes": sum(value[3] for value in previous_counters.values()),
        "scope": "sum_of_last_observed_cumulative_counters_per_pid_start_identity",
    }
    result = {"schema": "ARCANA_R6_INT3_ENG10K_SUPERVISION_V2",
        "supervision_mode": "OBSERVE_ONLY", "active_thresholds": [],
        "termination_conditions": ["NATURAL_CHILD_EXIT", "SUPERVISOR_SIGNAL",
                                    "PROCESS_IDENTITY_OR_TELEMETRY_FAILURE"],
        "command": command, "evidence_root_absolute": str(root),
        "output_absolute": str(output_dir), "supervision_absolute": str(evidence_dir),
        "expected_source_head": expected_head,
        "root_pid": process.pid, "root_start_ticks": root_start_ticks,
        "root_parent_pid": root_ppid, "root_executable": root_exe,
        "process_group_id": pgid, "last_observed_group_members": last_members,
        "natural_exit_code": process.returncode, "stop_reason": reason,
        "started_at_utc": start_utc, "elapsed_seconds": elapsed,
        "sample_interval_seconds": OBSERVE_POLL_INTERVAL_S,
        "sample_count": sample_count, "lost_sample_count": lost_samples,
        "telemetry_status": "PARTIAL" if telemetry_errors or lost_samples or final_output_bytes is None else "COMPLETE",
        "telemetry_errors": telemetry_errors,
        "peak_sampled_aggregate": peaks, "final_sampled_aggregate": final_group,
        "last_observed_process_lifetime_counters": process_lifetime_totals,
        "per_process_sampled_totals": per_identity_totals,
        "per_process_sampled_peaks": per_identity_peaks,
        "sampling_limitations": ["short_lived_processes_between_samples_may_be_missed",
                                 "CPU_and_IO_deltas_cover_observed_intervals_only"],
        "resource_samples": {"path": samples_path.name, "bytes": samples_path.stat().st_size},
        "final_cumulative_output_bytes": final_output_bytes,
        "final_output_byte_scope": "candidate_tree_child_logs_and_telemetry_jsonl_excludes_SUPERVISION_json",
        "trajectory_markers": {"path": markers_path.name, "bytes": markers_path.stat().st_size},
        "stdout": {"path": stdout_path.name, "bytes": stdout_path.stat().st_size},
        "stderr": {"path": stderr_path.name, "bytes": stderr_path.stat().st_size},
        "automatic_retry": False,
        "operational_note": "No historical wall/RSS/output thresholds are active in observe-only mode; telemetry incompleteness is not a numerical-result classification."}
    (evidence_dir / "SUPERVISION.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def supervise(command: list[str], *, evidence_root: Path,
              output_relative: Path, supervision_relative: Path,
              r4_bundle: Path, expected_head: str, authorization_json: Path,
              proc_root: Path = Path("/proc"), observe_only: bool = False) -> dict[str, Any]:
    if not sys.platform.startswith("linux"):
        raise SupervisionError("LINUX_PROC_SUPERVISION_REQUIRED")
    world_roots = tuple(Path(value) for value in (os.environ.get("ARCANA_WORLD_HISTORY_ROOT"),)
                        if value) + (ROOT / "WORLD_HISTORY",)
    try:
        root, output_dir, evidence_dir = resolve_evidence_destinations(
            evidence_root, output_relative, supervision_relative, repo_root=ROOT,
            world_history_roots=world_roots, r4_bundle=r4_bundle)
    except Eng10kContractError as exc:
        raise SupervisionError(str(exc)) from exc
    if (not isinstance(expected_head, str) or len(expected_head) != 40
            or any(ch not in "0123456789abcdef" for ch in expected_head)):
        raise SupervisionError("EXPECTED_SOURCE_HEAD_INVALID")
    _expected_child_command(command, root=root,
        output_relative=output_relative, supervision_relative=supervision_relative,
        r4_bundle=r4_bundle, expected_head=expected_head,
        authorization_json=authorization_json)
    if not Path(command[0]).is_file():
        raise SupervisionError("EXECUTABLE_PATH_INVALID")
    if observe_only:
        _validate_observe_authorization(authorization_json, source_head=expected_head,
            evidence_root=root, output_relative=output_relative,
            output_absolute=output_dir, supervision_relative=supervision_relative,
            supervision_absolute=evidence_dir)
    else:
        try:
            declared_auth = json.loads(authorization_json.read_bytes())
        except (OSError, json.JSONDecodeError):
            declared_auth = None  # Preserve legacy child-side validation behavior.
        if isinstance(declared_auth, dict) and declared_auth.get("supervision_mode") == "OBSERVE_ONLY":
            raise SupervisionError("OBSERVE_ONLY_AUTHORIZATION_REQUIRES_OBSERVE_ONLY_SUPERVISOR")
    try:
        attempt = create_evidence_attempt_parent(root, output_relative.parent,
            repo_root=ROOT, world_history_roots=world_roots)
        evidence_dir = attempt / supervision_relative.name
        evidence_dir.mkdir(exist_ok=False)
    except (OSError, Eng10kContractError) as exc:
        raise SupervisionError(f"EVIDENCE_ATTEMPT_CREATION_FAILED:{exc}") from exc
    if observe_only:
        return _supervise_observe_only(command, root=root, output_dir=output_dir,
            evidence_dir=evidence_dir, expected_head=expected_head, proc_root=proc_root)
    stdout_path, stderr_path = evidence_dir / "child.stdout", evidence_dir / "child.stderr"
    clean_env = dict(os.environ)
    clean_env.pop("GIT_OBJECT_DIRECTORY", None)
    clean_env.pop("GIT_ALTERNATE_OBJECT_DIRECTORIES", None)
    start = time.monotonic()
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(command, cwd=ROOT, env=clean_env,
                                   stdout=stdout, stderr=stderr, start_new_session=True)
        pgid = process.pid
        try:
            root_stat = (proc_root / str(process.pid) / "stat").read_text()
            _, _, root_group, root_start_ticks = _parse_stat(root_stat)
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
        empty_group_since: float | None = None
        while True:
            # Observe the leader first. A group snapshot taken before poll() can
            # predate leader exit and miss a child that is still being scheduled
            # or reparented into the same process group.
            return_code = process.poll()
            try:
                rss, members = _proc_group_snapshot(
                    proc_root, pgid, expected_leader_start_ticks=root_start_ticks)
                output_bytes = _tree_bytes(output_dir) + stdout_path.stat().st_size + stderr_path.stat().st_size
            except (OSError, SupervisionError) as exc:
                reason = f"MONITORING_FAILURE:{exc}"
                _terminate_group(pgid, process)
                break
            samples += 1
            last_members = members
            peaks["rss_bytes"] = max(peaks["rss_bytes"], rss)
            peaks["output_bytes"] = max(peaks["output_bytes"], output_bytes)
            # Include polling and /proc scan time in the wall-time decision.
            elapsed = time.monotonic() - start
            if elapsed >= WALL_LIMIT_S:
                reason = "WALL_TIME_LIMIT"
            elif rss > RSS_LIMIT_BYTES:
                reason = "PROCESS_GROUP_RSS_LIMIT"
            elif output_bytes > OUTPUT_LIMIT_BYTES:
                reason = "CUMULATIVE_OUTPUT_LIMIT"
            else:
                confirmed, empty_group_since = _update_empty_group_confirmation(
                    return_code, members, time.monotonic(), empty_group_since)
                if confirmed:
                    reason = "NATURAL_EXIT"
                    break
            if reason != "UNKNOWN":
                _terminate_group(pgid, process)
                break
            time.sleep(POLL_INTERVAL_S)
    elapsed = time.monotonic() - start
    result = {"schema": "ARCANA_R6_INT3_ENG10K_SUPERVISION_V1",
        "command": command, "evidence_root_absolute": str(root),
        "output_absolute": str(output_dir), "supervision_absolute": str(evidence_dir),
        "expected_source_head": expected_head,
        "root_pid": process.pid, "root_start_ticks": root_start_ticks,
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
    parser.add_argument("--evidence-root", type=Path,
                        default=Path(os.environ["ARCANA_EVIDENCE_ROOT"])
                        if os.environ.get("ARCANA_EVIDENCE_ROOT") else None)
    parser.add_argument("--output-relative", type=Path, required=True)
    parser.add_argument("--supervision-relative", type=Path, required=True)
    parser.add_argument("--r4-bundle", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--authorization-json", type=Path, required=True)
    parser.add_argument("--observe-only", action="store_true",
                        help="Sample resources without applying legacy budget thresholds")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        command = args.command[1:] if args.command and args.command[0] == "--" else args.command
        if args.evidence_root is None:
            raise SupervisionError("ARCANA_EVIDENCE_ROOT_REQUIRED")
        result = supervise(command, evidence_root=args.evidence_root,
            output_relative=args.output_relative, supervision_relative=args.supervision_relative,
            r4_bundle=args.r4_bundle, expected_head=args.expected_head,
            authorization_json=args.authorization_json, observe_only=args.observe_only)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["stop_reason"] == "NATURAL_EXIT" and result["natural_exit_code"] == 0 else 1
    except (OSError, SupervisionError) as exc:
        print(f"INT3_ENG10K_SUPERVISION_BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
