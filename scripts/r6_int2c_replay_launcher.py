"""Linux-only supervised R4 replay CLI. Default is preflight, never evolution.

--execute-authorized is an operator acknowledgement, not an authorization issuer.
Offline tests inject a synthetic runner; the CLI always uses the real adapter.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time

from arcana_worldsim.r6.identity import thaw_json
from arcana_worldsim.r6.replay import execute_replay, validate_replay_inputs
from arcana_worldsim.r6.store import HistoryStore
from r6_int1a_retention_audit import _json_bytes
from r6_int2c_checkpoint_attest import attest_r4
from r6_int2c_replay_adapter import DeterministicKernelAdapter, ReplayBindingError, _text_hash, np

EXPECTED_STATE = "r6state_d36b8094e89671d0d25894bcd4d798efdb426c65fcd6eb5d6652531f92c51d6a"
EXPECTED_PAYLOAD = "2b4836954e688d7aac6d9e26ccb61aa02fa94e9e40550c395922b30fa1b45d7b"
EXPECTED_CHECKPOINT = "r6checkpoint_45ccc437cbe2d5d8d40febbbbc3d7d6d5b5a1a42e7060ca40027048524b71158"
EXPECTED_RECIPE = "r6recipe_46e4b555cd4f996cd58020b840819c6ff468cb4640254fb3bb4efb6e887a4c92"
STORE = "/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/INT2C_C2_ljWdyPsq/isolated_history_store"
RUNTIME = Path("/home/jlpfritas/miniforge3/envs/arcana-r6-replay-r4-py31210")
R4_RELATIVE = "outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04"
LIMITS = (900.0, 2 * 1024**3, 512 * 1024**2)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def runtime_check():
    """No fallback to another interpreter or externally supplied NumPy package."""
    prefix = RUNTIME.resolve()
    numpy_path = Path(np.__file__).resolve()
    if (platform.python_version() != "3.12.10" or np.__version__ != "2.3.5"
            or Path(sys.prefix).resolve() != prefix
            or Path(sys.executable).resolve() != (prefix / "bin/python").resolve()
            or prefix not in numpy_path.parents):
        raise ReplayBindingError("EXACT_ISOLATED_RUNTIME_REQUIRED")
    return {"python": platform.python_version(), "numpy": np.__version__,
            "executable": sys.executable, "prefix": str(prefix),
            "numpy_module": str(numpy_path), "numpy_module_sha256": digest(numpy_path.read_bytes())}


def write_json(path, value):
    with path.open("xb") as handle:
        handle.write(_json_bytes(value))


def inventory(root):
    """Bounded task directories only; reject links and nonregular members."""
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ReplayBindingError("SYMLINK_IN_EVIDENCE")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ReplayBindingError("NONREGULAR_EVIDENCE")
        size, hashed = 0, hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                size += len(chunk)
                hashed.update(chunk)
        result[path.relative_to(root).as_posix()] = {"bytes": size, "sha256": hashed.hexdigest()}
    return result


def check_paths(repository, bundle, store, output):
    paths = [Path(x).absolute() for x in (repository, bundle, store, output)]
    for path in paths:
        if any(part.casefold() in {"world_history", "world_history_bindings"} for part in path.parts):
            raise ReplayBindingError("CANONICAL_PATH_FORBIDDEN")
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ReplayBindingError("SYMLINK_PATH_FORBIDDEN")
    repository, bundle, store, output = [x.resolve() for x in paths]
    if not all(x.is_dir() for x in (repository, bundle, store)):
        raise ReplayBindingError("MISSING_INPUT_DIRECTORY")
    for source in (repository, bundle, store):
        if output == source or output in source.parents or source in output.parents:
            raise ReplayBindingError("OUTPUT_OVERLAPS_INPUT")
    if output.exists() or not output.parent.is_dir():
        raise ReplayBindingError("FRESH_OUTPUT_WITH_EXISTING_PARENT_REQUIRED")
    return repository, bundle, store, output


def source_check(repository, expected_commit):
    env = dict(os.environ)
    for name in ("GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        env.pop(name, None)
    def git(*args):
        return subprocess.run(["git", *args], cwd=repository, env=env,
                              capture_output=True, check=True, timeout=15).stdout.decode().strip()
    if git("rev-parse", "HEAD") != expected_commit:
        raise ReplayBindingError("SOURCE_COMMIT_MISMATCH")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ReplayBindingError("TRACKED_WORKTREE_NOT_CLEAN")
    modules = ("r6_int2c_replay_launcher", "r6_int2c_checkpoint_attest", "r6_int2c_replay_adapter",
               "r6_int1a_retention_audit", "arcana_worldsim.r6.store", "arcana_worldsim.r6.replay",
               "arcana_worldsim.r6.identity", "arcana_worldsim.r6.checkpoint",
               "arcana_worldsim.r6.state", "arcana_worldsim.r6.forcing",
               "arcana_worldsim.r6.provenance", "arcana_worldsim.r6.functional_development")
    hashes = {}
    for name in modules:
        module = sys.modules.get(name)
        path = Path(__file__) if name == "r6_int2c_replay_launcher" else Path(module.__file__)
        try:
            relative = path.absolute().relative_to(repository.absolute()).as_posix()
        except ValueError as exc:
            raise ReplayBindingError("LOADED_MODULE_OUTSIDE_SOURCE_CHECKOUT") from exc
        blob = subprocess.run(["git", "show", f"{expected_commit}:{relative}"],
                              cwd=repository, env=env, capture_output=True, check=True, timeout=15).stdout
        raw = path.read_bytes()
        if _text_hash(raw) != _text_hash(blob):
            raise ReplayBindingError("LOADED_SOURCE_DIFFERS_FROM_GIT_COMMIT:" + relative)
        hashes[relative] = {"byte_sha256": digest(raw), "canonical_text_sha256": _text_hash(raw)}
    return {"commit": expected_commit, "code_files": hashes,
            "launcher_sha256": digest(Path(__file__).read_bytes())}


def copy_store(source, destination):
    before = inventory(source)
    if len(before) != 16 or sum(x["bytes"] for x in before.values()) != 78945:
        raise ReplayBindingError("C2_STORE_INVENTORY_MISMATCH")
    destination.mkdir()
    for name, identity in before.items():
        raw = (source / name).read_bytes()
        if len(raw) != identity["bytes"] or digest(raw) != identity["sha256"]:
            raise ReplayBindingError("C2_CHANGED_DURING_COPY")
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    if inventory(destination) != before or inventory(source) != before:
        raise ReplayBindingError("C2_COPY_IDENTITY_MISMATCH")
    return before


def validate_store(store, attestation):
    readers = {"states": store.read_state, "provenance": store.read_provenance,
               "checkpoints": store.read_checkpoint, "forcings": store.read_forcing,
               "replay_recipes": store.read_replay_recipe}
    with store.read_view():
        for record in attestation.records:
            bucket, key, expected = HistoryStore._transaction_record(record)
            observed = readers[bucket](key)
            if hasattr(observed, "to_dict"):
                observed = observed.to_dict()
            if observed != expected:
                raise ReplayBindingError("PERSISTED_RECORD_MISMATCH:" + key)
        p = attestation.prepared
        if (str(p.checkpoint.checkpoint_id) != EXPECTED_CHECKPOINT
                or str(p.recipe.recipe_id) != EXPECTED_RECIPE
                or p.recipe.expected_output_state_id != EXPECTED_STATE):
            raise ReplayBindingError("PINNED_TECHNICAL_IDENTITY_MISMATCH")
        return validate_replay_inputs(store, p.recipe)


def replay_result(preparation, store, runner=None):
    """Transparent capture: return the same adapter output to B0 unchanged."""
    captured = []
    adapter = DeterministicKernelAdapter(preparation) if runner is None else runner
    def capture(recipe, inputs):
        output = adapter(recipe, inputs)
        captured.append(output)
        return output
    verified = execute_replay(store, preparation.recipe, capture)
    if len(captured) != 1:
        raise ReplayBindingError("EXACTLY_ONE_ADAPTER_EXECUTION_REQUIRED")
    state = captured[0].state
    values = thaw_json(state.value)
    payloads = [digest(_json_bytes(side)) for side in values["side_states"]]
    matched = (verified.status == "VERIFIED" and str(state.state_id) == EXPECTED_STATE
               and len(payloads) == 2 and payloads == [EXPECTED_PAYLOAD] * 2)
    return {"status": "VERIFIED" if matched else "MISMATCH",
            "b0_verification": asdict(verified), "computed_state_id": str(state.state_id),
            "per_support_payload_sha256": payloads, "expected_state_id": EXPECTED_STATE,
            "expected_per_support_payload_sha256": EXPECTED_PAYLOAD}, state.to_dict()


def child(args):
    # Parent owns a fresh evidence directory and releases this exact child only
    # after verifying its /proc identity and initial resource sample.
    if sys.stdin.readline().strip() != "START":
        raise ReplayBindingError("SUPERVISOR_HANDSHAKE_REQUIRED")
    output = Path(args.output)
    result = {"status": "FAILED", "numerical_execution_started": False}
    before, r4_before = None, None
    try:
        runtime = runtime_check()
        source = source_check(Path(args.repository), args.source_commit)
        r4_before = inventory(Path(args.bundle))
        a = attest_r4(Path(args.repository), Path(args.bundle))
        if inventory(Path(args.bundle)) != r4_before:
            raise ReplayBindingError("R4_CHANGED_DURING_ATTESTATION")
        before = copy_store(Path(args.store), output / "store_read_copy")
        store = HistoryStore(output / "store_read_copy")
        validate_store(store, a)
        if args.execute_authorized:
            result["numerical_execution_started"] = True
            metrics, state = replay_result(a.prepared, store)
            result.update(metrics)
            write_json(output / "COMPUTED_STATE.json", state)
        else:
            result["status"] = "PREFLIGHT_PASS_NO_NUMERICAL_EXECUTION"
        result.update(runtime=runtime, source=source, source_identity=thaw_json(a.prepared.source_identity),
                      configuration=thaw_json(a.prepared.configuration), c2_inventory=before)
    except Exception as exc:
        result.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
    finally:
        try:
            if before is not None and inventory(Path(args.store)) != before:
                raise ReplayBindingError("ORIGINAL_C2_STORE_CHANGED")
            if r4_before is not None and inventory(Path(args.bundle)) != r4_before:
                raise ReplayBindingError("ORIGINAL_R4_BUNDLE_CHANGED")
            result["r4_inventory"] = r4_before
        except Exception as exc:
            result.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
        write_json(output / "REPLAY_RESULT.json", result)
    return 0 if result["status"] in {"VERIFIED", "PREFLIGHT_PASS_NO_NUMERICAL_EXECUTION"} else 2


def proc_rows(proc=Path("/proc")):
    rows = {}
    for item in proc.glob("[0-9]*/stat"):
        try:
            fields = item.read_text().rsplit(")", 1)[1].split()
            rows[int(item.parent.name)] = (int(fields[1]), int(fields[2]),
                                          int(fields[19]), int(fields[21]) * os.sysconf("SC_PAGE_SIZE"))
        except FileNotFoundError:
            continue  # A process disappeared between enumeration and sampling.
    return rows


def process_tree(pid, rows, known):
    selected = {p for p, r in rows.items() if p == pid or r[1] == pid
                or known.get(p) == r[2]}
    while True:
        added = {p for p, r in rows.items() if r[0] in selected}
        if added <= selected:
            break
        selected |= added
    members = {p: rows[p][2] for p in selected}
    known.update(members)
    return members, sum(rows[p][3] for p in selected)


def terminate_tree(process, known):
    """New process group plus identity-checked descendants; bounded escalation."""
    for sig in (signal.SIGTERM, signal.SIGKILL):
        rows = proc_rows()
        owned_group = any(r[1] == process.pid and known.get(pid) == r[2]
                          for pid, r in rows.items())
        if process.poll() is None or owned_group:
            try:
                os.killpg(process.pid, sig)
            except ProcessLookupError:
                pass
        for pid, start in known.items():
            if pid in rows and rows[pid][2] == start:
                try:
                    os.kill(pid, sig)
                except ProcessLookupError:
                    pass
        if sig == signal.SIGTERM:
            time.sleep(0.2)
    process.wait(timeout=5)


def output_bytes(root):
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())


def child_command(args):
    command = [sys.executable, "-u", str(Path(__file__).absolute()), "--child",
               "--repository", args.repository, "--bundle", args.bundle,
               "--store", args.store, "--output", args.output,
               "--source-commit", args.source_commit]
    if args.execute_authorized:
        command.append("--execute-authorized")
    return command


def supervise(command, output, *, limits=LIMITS, handshake=True):
    if sys.platform != "linux":
        raise ReplayBindingError("LINUX_PROC_SUPERVISOR_REQUIRED")
    output.mkdir()  # Collision fails; no overwrite, retry or automatic cleanup.
    env = dict(os.environ)
    for name in ("GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        env.pop(name, None)
    env.update(PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1")
    start = time.monotonic()
    known, peak, count, reason, process = {}, 0, 0, "NATURAL_EXIT", None
    identity = {}
    with (output / "stdout.log").open("xb") as stdout, (output / "stderr.log").open("xb") as stderr:
        try:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                       env=env, start_new_session=True)
            rows = proc_rows()
            members, rss = process_tree(process.pid, rows, known)
            if process.pid not in members:
                raise ReplayBindingError("PYTHON_PID_NOT_OBSERVED")
            exe = os.readlink(f"/proc/{process.pid}/exe")
            if Path(exe).resolve() != Path(command[0]).resolve():
                raise ReplayBindingError("CHILD_EXECUTABLE_IDENTITY_MISMATCH")
            identity = {"pid": process.pid, "start_ticks": rows[process.pid][2], "executable": exe}
            peak = rss
            if rss >= limits[1]:
                raise ReplayBindingError("INITIAL_RSS_LIMIT")
            if handshake:
                process.stdin.write(b"START\n")
                process.stdin.flush()
            process.stdin.close()
            while True:
                _, rss = process_tree(process.pid, proc_rows(), known)
                peak, count = max(peak, rss), count + 1
                elapsed, size = time.monotonic() - start, output_bytes(output)
                if elapsed >= limits[0]:
                    reason = "WALL_TIME_LIMIT"
                elif rss >= limits[1]:
                    reason = "PROCESS_TREE_RSS_LIMIT"
                elif size >= limits[2]:
                    reason = "OUTPUT_BYTES_LIMIT"
                if reason != "NATURAL_EXIT":
                    terminate_tree(process, known)
                    break
                exited = process.poll()
                if exited is not None:
                    if exited < 0:
                        reason = "CHILD_SIGNAL_EXIT"
                    # Terminate any observed descendants remaining after root exit.
                    terminate_tree(process, known)
                    break
                time.sleep(0.1)
        except BaseException as exc:
            reason = f"SUPERVISOR_FAILURE:{type(exc).__name__}:{exc}"
            if process is not None:
                terminate_tree(process, known)
        finally:
            elapsed = time.monotonic() - start
            observed_bytes = output_bytes(output)
            result = {"identity": identity, "command": command, "elapsed_seconds": elapsed,
                      "peak_sampled_process_tree_rss_bytes": peak, "samples": count,
                      "observed_process_start_ticks": known,
                      "child_exit_code": None if process is None else process.returncode,
                      "stop_reason": reason, "observed_output_bytes": observed_bytes,
                      "limits": {"seconds": limits[0], "rss_bytes": limits[1], "output_bytes": limits[2]},
                      "poll_interval_seconds": 0.1, "hard_os_quotas": False,
                      "wall_overshoot_seconds": max(0.0, elapsed-limits[0]),
                      "rss_overshoot_bytes": max(0, peak-limits[1]),
                      "output_overshoot_bytes": max(0, observed_bytes-limits[2])}
            write_json(output / "SUPERVISION.json", result)
            write_json(output / "ARTIFACT_MANIFEST.json", {"artifacts": inventory(output)})
            result["post_seal_output_bytes"] = output_bytes(output)
            result["manifest_sha256"] = digest((output / "ARTIFACT_MANIFEST.json").read_bytes())
    return result


def supervisor_exit_status(result):
    if result["stop_reason"] == "NATURAL_EXIT":
        return result["child_exit_code"]
    if result["stop_reason"] == "CHILD_SIGNAL_EXIT":
        return 128 + abs(result["child_exit_code"])
    return 124


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--store", default=STORE)
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--execute-authorized", action="store_true")
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.child:
        return child(args)
    repository, bundle, store, output = check_paths(args.repository, args.bundle, args.store, args.output)
    args.repository, args.bundle, args.store, args.output = map(str, (repository, bundle, store, output))
    runtime_check()
    source_check(repository, args.source_commit)
    attest_r4(repository, bundle)  # Exact runtime/source/input preflight, no kernel.
    result = supervise(child_command(args), output)
    print(json.dumps(result, sort_keys=True))
    return supervisor_exit_status(result)


if __name__ == "__main__":
    raise SystemExit(main())
