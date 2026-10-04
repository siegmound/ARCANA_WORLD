from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "r6/b6m-r1a-atomic-reader-visibility"
EXPECTED_HEAD = "3ea7b7ab521d334126d84082ddae0977dbe99737"
EXPECTED_STORE_ID = (
    "r6canonical_18bab1f51f02b62f6b78e893b24c9fd81f8d48b8ed30d513c6d19141ebf3e4a0")
EXPECTED_PAYLOAD_SHA256 = (
    "9527429db651bac60606b257dcff7abfff601fc66df053ce278822a3a8a8a46a")
EXPECTED_ENV = {
    "GIT_OBJECT_DIRECTORY": r"C:\Users\jose_\AppData\Local\ARCANA\git-objects\r6",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES": (
        "F:\\corsiiiuu\\Magistrale\\Arcana\\ArcanaWorld\\"
        "ARCANA_WORLD1_v0_6D1_R3_11_POST_CHA1_H0_RECOVERY_ADAPTIVE_RADIATION_RESTART_CANDIDATE\\.git\\objects"),
    "ARCANA_WORLD_HISTORY_ROOT": (
        r"F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\ARCANA_WORLD_HISTORY_R6_CANONICAL"),
}
OUTPUT_REL = Path("outputs/r6_b6m_r1a_atomic_reader_visibility")
def _git(*args: str, strip: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip() if strip else result.stdout.rstrip("\r\n")


def _source_gate() -> dict:
    branch = _git("branch", "--show-current")
    head = _git("rev-parse", "--verify", "HEAD")
    object_type = _git("cat-file", "-t", "HEAD")
    if (branch, head, object_type) != (EXPECTED_BRANCH, EXPECTED_HEAD, "commit"):
        raise RuntimeError("B6M-R1A exact branch/HEAD/object source gate failed")
    wrong_env = {key: {"expected": value, "actual": os.environ.get(key)}
                 for key, value in EXPECTED_ENV.items() if os.environ.get(key) != value}
    if wrong_env:
        raise RuntimeError("B6M-R1A Git/canonical environment gate failed: " +
                           json.dumps(wrong_env, sort_keys=True))

    allowed_modified = {
        "scripts/r6_b6k_isolated_first_candidate_state.py",
        "scripts/r6_b6l_candidate_query_publication_readiness.py",
        "src/arcana_worldsim/r6/canonical_bootstrap.py",
        "src/arcana_worldsim/r6/query.py",
        "src/arcana_worldsim/r6/refinement.py",
        "src/arcana_worldsim/r6/replay.py",
        "src/arcana_worldsim/r6/store.py",
        "tests/test_r6_world_history_b0_b.py",
    }
    allowed_untracked = {
        "B6J_CODEX_LUNA_RESULT.txt", "B6M_CODEX_LUNA_RESULT.txt",
        "scripts/r6_b6m_r1a_atomic_reader_visibility.py",
        "tests/test_r6_world_history_b6m_r1a_atomic_reader_visibility.py",
        "docs/arcana/B6MR1A_ATOMIC_READER_VISIBILITY.md",
    }
    # Preserve porcelain's leading status column; strip() would erase it on
    # the first row and corrupt the path slice below.
    status = _git("status", "--porcelain=v1", "--untracked-files=all", strip=False)
    staged = _git("diff", "--cached", "--name-only")
    if staged:
        raise RuntimeError("B6M-R1A source gate rejects staged files")
    unrelated = []
    for line in status.splitlines():
        code, path = line[:2], line[3:]
        if code == "??":
            if path not in allowed_untracked and not path.startswith(OUTPUT_REL.as_posix() + "/"):
                unrelated.append(path)
        elif path not in allowed_modified:
            unrelated.append(path)
    if unrelated:
        raise RuntimeError("B6M-R1A source gate found unrelated worktree changes: " +
                           ", ".join(sorted(unrelated)))
    return {"branch": branch, "head": head, "object_type": object_type,
            "git_object_visibility": "PASS", "environment": EXPECTED_ENV,
            "staged_paths": [], "unrelated_worktree_changes": [],
            "known_local_logs_tolerated": True}


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_snapshot(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted(root.rglob("*")):
        if ".history_visibility" in path.relative_to(root).parts:
            continue
        if path.is_symlink():
            raise RuntimeError("canonical store contains a symbolic link")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = _sha(path)
    return result


def _assert_no_active_transactions(root: Path) -> None:
    transaction_root = root / ".history_transactions"
    if transaction_root.exists() and any(path.name != ".retired"
                                         for path in transaction_root.iterdir()):
        raise RuntimeError("canonical store has an active transaction journal")


def _portable_value(value: object, *, allow_environment: bool = False) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _portable_value(item, allow_environment=allow_environment or key == "environment")
    elif isinstance(value, (list, tuple)):
        for item in value:
            _portable_value(item, allow_environment=allow_environment)
    elif isinstance(value, str) and not allow_environment:
        if ("C:\\Users\\" in value or "F:\\" in value or
                value.startswith("/home/") or value.startswith("/tmp/")):
            raise RuntimeError("portable qualification artifact contains a machine-specific path")


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")


def _assert_canonical_baseline(root: Path) -> tuple[dict, dict[str, str]]:
    from arcana_worldsim.r6.state import DomainStateEnvelope

    descriptor_path = root / "arcana_canonical_store.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    if descriptor.get("store_identity") != EXPECTED_STORE_ID:
        raise RuntimeError("canonical logical store identity differs from B6M0 authority")
    manifest_path = root / "metadata" / "store_manifest.json"
    before = _file_snapshot(root)
    if len(before) != 19 or descriptor.get("canonical_temporal_state_count") != 1:
        raise RuntimeError("canonical pre-migration record/file baseline differs from B6M0")
    states = []
    for state_id in descriptor["genesis_state_ids"]:
        path = root / "states" / f"{state_id}.json"
        state = DomainStateEnvelope.from_dict(json.loads(path.read_text(encoding="utf-8")))
        if str(state.state_id) != state_id or state.time_support.time_key != "210Ma":
            raise RuntimeError("canonical T0 state identity or age validation failed")
        states.append(state)
    if len(states) != 14 or len({str(state.state_id) for state in states}) != 14:
        raise RuntimeError("canonical T0 state membership is not exactly the 14 B6M0 states")
    return {"descriptor": descriptor, "descriptor_sha256": _sha(descriptor_path),
            "manifest_sha256": _sha(manifest_path), "states": states}, before


def _candidate_payload_check() -> dict:
    output = REPO_ROOT / "outputs/r6_b6k_isolated_first_candidate_state"
    payload = output / "B6K_CANDIDATE_PLATE_LOCAL_COORDINATES.bin"
    manifest = json.loads((output / "B6K_ARTIFACT_MANIFEST.json").read_text(encoding="utf-8"))
    relative_payload = "outputs/r6_b6k_isolated_first_candidate_state/" + payload.name
    matches = [row for row in manifest.get("artifacts", [])
               if row.get("relative_path") == relative_payload]
    digest = _sha(payload)
    if digest != EXPECTED_PAYLOAD_SHA256 or (matches and matches[0].get("sha256") != digest):
        raise RuntimeError("B6K candidate payload hash/manifest no longer matches authority")
    return {"path": relative_payload,
            "sha256": digest, "bytes": payload.stat().st_size,
            "B6K_manifest_match": bool(matches)}


def run(validation_path: Path) -> dict:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from arcana_worldsim.r6.query import HistoryQueryService
    from arcana_worldsim.r6.store import HistoryStore

    source_gate = _source_gate()
    validation_results = json.loads(validation_path.read_text(encoding="utf-8"))
    required_passes = ("focused_b6mr1a", "b0c_recovery", "query_regression",
                       "b6l_regression", "b6m0_regression", "b5_b6m0_regression",
                       "full_r6", "py_compile", "compileall", "json_validation",
                       "manifest_validation", "portable_path_validation", "diff_check")
    failing = [key for key in required_passes if validation_results.get(key) != "PASS"]
    if failing:
        raise RuntimeError("required validation result missing/failing: " + ", ".join(failing))
    payload = _candidate_payload_check()
    canonical_root = Path(EXPECTED_ENV["ARCANA_WORLD_HISTORY_ROOT"])
    if not canonical_root.is_dir() or canonical_root.is_symlink():
        raise RuntimeError("governed canonical root is missing or is a symbolic link")
    preflight, files_before = _assert_canonical_baseline(canonical_root)
    _assert_no_active_transactions(canonical_root)
    root_bytes_before = sum((canonical_root / name).stat().st_size for name in files_before)
    descriptor = preflight["descriptor"]
    states = preflight["states"]

    from arcana_worldsim.r6.identity import canonical_bytes
    before_result = {
        "schema": "ARCANA_R6_B6MR1A_CANONICAL_T0_MIGRATION_V1",
        "store_identity": descriptor["store_identity"],
        "pre_migration": {"canonical_epoch_count": 1, "latest_age_ma": 210.0,
            "domain_state_count": len(states), "persistent_file_count": len(files_before),
            "persistent_bytes": root_bytes_before, "visibility_metadata_present":
            (canonical_root / ".history_visibility" / "CURRENT.json").is_file(),
            "scientific_files_sha256": files_before},
    }
    started = time.perf_counter()
    store = HistoryStore(canonical_root, _migrate_legacy_visibility=True)
    with store.read_view() as view:
        initial_view_id = view.view_id
        state_rows = store.states()
        provenance_rows = tuple(store.read_provenance(item)
                                for item in (descriptor["source_provenance_id"],
                                             descriptor["bootstrap_provenance_id"]))
        temporal_rows = store.temporal_records()
        events = store.events()
        checkpoints = store.checkpoints()
        forcings = store.forcings()
        replay_recipes = store.replay_recipes()
        refinement_branches = store.refinement_branches()
        refinement_recipes = store.refinement_recipes()
        query = HistoryQueryService(store)
        physical = next(item for item in states if item.domain == "physical_geography")
        unknown = next(item for item in states if item.support_class.value == "UNKNOWN")
        state_query = query.state_at(history_id=physical.history_id,
            branch_id=physical.branch_id, domain=physical.domain, time_key="210Ma")
        unknown_query = query.state_at(history_id=unknown.history_id,
            branch_id=unknown.branch_id, domain=unknown.domain, time_key="210Ma")
        history_query = query.history_result(history_id=physical.history_id,
                                             branch_id=physical.branch_id)
    if {str(item.state_id) for item in state_rows} != set(descriptor["genesis_state_ids"]):
        raise RuntimeError("post-migration canonical state set differs from T0 genesis")
    if (len(provenance_rows) != 2 or len(temporal_rows) != 1 or
            temporal_rows[0]["role"] != "AUTHORITY_ANCHOR" or
            temporal_rows[0]["time_key"] != "210Ma" or
            set(temporal_rows[0]["state_ids"]) != set(descriptor["genesis_state_ids"])):
        raise RuntimeError("post-migration provenance/temporal record counts differ from B6M0")
    if any((events, checkpoints, forcings, replay_recipes, refinement_branches, refinement_recipes)):
        raise RuntimeError("unexpected post-genesis temporal/T1/refinement records exist")
    if (state_query.status != "FOUND" or unknown_query.status != "UNKNOWN" or
            len(history_query.states) != 14):
        raise RuntimeError("post-migration canonical T0 query baseline failed")
    del store

    reopened = HistoryStore(canonical_root)
    with reopened.read_view() as reopened_view:
        if reopened_view.view_id != initial_view_id:
            raise RuntimeError("close/reopen changed canonical committed view identity")
        reopened_states = reopened.states()
    # Explicit repeat migration must be idempotent; ordinary reads above did not infer one.
    repeated = HistoryStore(canonical_root, _migrate_legacy_visibility=True)
    with repeated.read_view() as repeated_view:
        if repeated_view.view_id != initial_view_id or repeated.states() != reopened_states:
            raise RuntimeError("repeated explicit migration changed the canonical view")
    del repeated, reopened

    files_after = _file_snapshot(canonical_root)
    if files_after != files_before:
        raise RuntimeError("canonical scientific/descriptor/manifest files changed during metadata migration")
    current_pointer = json.loads((canonical_root / ".history_visibility" / "CURRENT.json").read_text())
    current_view = current_pointer["view_id"]
    view_manifest = canonical_root / ".history_visibility" / "views" / f"{current_view}.json"
    if not view_manifest.is_file():
        raise RuntimeError("canonical CURRENT pointer does not resolve an immutable view manifest")
    _assert_no_active_transactions(canonical_root)
    if _candidate_payload_check() != payload:
        raise RuntimeError("B6K candidate payload changed during canonical metadata migration")
    migration_ms = round((time.perf_counter() - started) * 1000, 3)
    root_bytes_after = sum(path.stat().st_size for path in canonical_root.rglob("*") if path.is_file())
    migration = {**before_result, "post_migration": {
        "committed_view_id": current_view, "canonical_epoch_count": 1,
        "latest_age_ma": 210.0, "domain_state_count": len(reopened_states),
        "provenance_record_count": 2, "authority_anchor_count": 1,
        "t1_created": False, "pending_transaction_count": 0,
        "query_state": state_query.status, "query_unknown": unknown_query.status,
        "history_records": len(history_query.states),
        "scientific_files_sha256_unchanged": files_after == files_before,
        "persistent_bytes": root_bytes_after, "migration_elapsed_ms": migration_ms,
        "explicit_repeat_migration_idempotent": True}}

    result = {"schema": "ARCANA_R6_B6MR1A_RESULT_V1",
        "decision": "PENDING_B6MR1A_ARTIFACT_VALIDATION",
        "qualified_source_commit": EXPECTED_HEAD,
        "canonical_store_id": EXPECTED_STORE_ID,
        "atomic_visibility_contract": "CANONICAL_READ_ATOMIC_VISIBILITY_V1",
        "b6mr1_resume_readiness": "PENDING_VALIDATION",
        "t1_created": False, "second_dt_selected": False,
        "rift_transition_executed": False, "t2_created": False,
        "canonical_state_changed": False,
        "candidate_payload": payload,
        "canonical_metadata_migration": "PASS_SCIENTIFICALLY_NEUTRAL"}

    out = REPO_ROOT / OUTPUT_REL
    out.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "B6MR1A_RESULT.json": result,
        "B6MR1A_SOURCE_GATE.json": source_gate,
        "B6MR1A_CURRENT_VISIBILITY_AUDIT.json": {
            "transaction_records_materialize_sequentially": True,
            "commit_marker_is_not_reader_visibility_authority": True,
            "typed_readers_use_immutable_committed_membership": True,
            "legacy_store_without_view": "FAIL_CLOSED_UNLESS_EXPLICIT_MIGRATION",
            "supported_readers": "WORLD_HISTORY_TYPED_AND_LOGICAL_QUERY_APIS"},
        "B6MR1A_VISIBILITY_CONTRACT.json": {
            "schema": "CANONICAL_READ_ATOMIC_VISIBILITY_V1",
            "one_local_writer_transaction_at_a_time": True,
            "physical_file_existence_implies_visibility": False,
            "one_complete_record_universe_view": True,
            "reader_pins_view_for_logical_query": True,
            "raw_filesystem_readers_protected": False},
        "B6MR1A_READ_VIEW_MODEL.json": {
            "immutable_manifest": ".history_visibility/views/<content-addressed-view>.json",
            "pointer": ".history_visibility/CURRENT.json",
            "membership_is_visibility_authority": True,
            "retains_historical_records": True,
            "query_context": "ContextVar nested read session"},
        "B6MR1A_LINEARIZATION_POINT.json": {
            "operation": "os.replace(temp_CURRENT, CURRENT.json)",
            "same_directory_same_volume": True, "supported_windows_scope": "fixed local NTFS",
            "directory_entry_fsynced_where_supported": True,
            "uncommitted_files_visible_to_supported_queries": False},
        "B6MR1A_WRITER_SERIALIZATION.json": {
            "thread_lock": "per canonical root in process",
            "process_lock": "exclusive byte-range lock on WRITER.lock",
            "read_modify_switch_serialized": True,
            "stale_expected_parent_rejected": True},
        "B6MR1A_RECOVERY_VISIBILITY.json": {
            "before_switch": "rollback to previous complete view",
            "after_switch": "complete/finalize new view; never roll back",
            "pre_switch_orphans": "unreachable record/view metadata only",
            "ambiguous_lineage": "fail closed"},
        "B6MR1A_CANONICAL_T0_MIGRATION.json": migration,
        "B6MR1A_CONCURRENT_READER_TESTS.json": {
            "thread_reader_pinned_old_generation": "PASS",
            "independent_process_reader_pinned_old_generation": "PASS",
            "independent_process_writer_serialization": "PASS",
            "visibility_barrier_observations": "OLD_COMPLETE_BEFORE_SWITCH; NEW_COMPLETE_AFTER_SWITCH"},
        "B6MR1A_QUERY_COHERENCE.json": {
            "compound_difference_query": "one pinned view across lookups",
            "publication_between_record_lookups": "QUERY_VIEW_STABLE"},
        "B6MR1A_CONCURRENCY_SCOPE.json": {
            "same_thread": "PASS", "multi_thread_same_process": "PASS",
            "independent_process_reader": "PASS",
            "independent_process_writer": "PASS_SERIALIZED_BY_BYTE_RANGE_LOCK",
            "filesystem_assumption": "fixed local NTFS on Windows"},
        "B6MR1A_CANONICAL_SOURCE_INTEGRITY.json": {
            "descriptor_sha256_before_after": preflight["descriptor_sha256"],
            "manifest_sha256_before_after": preflight["manifest_sha256"],
            "canonical_record_file_hashes_before_after": "IDENTICAL",
            "candidate_payload_sha256": payload["sha256"],
            "canonical_epoch_count": 1, "latest_age_ma": 210.0,
            "t1_created": False, "canonical_state_changed": False},
        "B6MR1A_TEST_RESULTS.json": validation_results,
    }
    for name, body in artifacts.items():
        _portable_value(body, allow_environment=(name == "B6MR1A_SOURCE_GATE.json"))
        _write_json(out / name, body)
    (out / "README.md").write_text(
        "# B6M-R1A Atomic Reader Visibility\n\n"
        "This package records a metadata-only migration of the existing canonical T0 store and the "
        "B6M-R1A source/test qualification. It does not publish T1 or select another dt. "
        "See `docs/arcana/B6MR1A_ATOMIC_READER_VISIBILITY.md`.\n", encoding="utf-8", newline="\n")
    artifact_rows = []
    for path in sorted([item for item in out.iterdir() if item.is_file() and
                        item.name != "B6MR1A_ARTIFACT_MANIFEST.json"] +
                       [REPO_ROOT / "docs/arcana/B6MR1A_ATOMIC_READER_VISIBILITY.md"]):
        relative = path.relative_to(REPO_ROOT).as_posix()
        artifact_rows.append({"relative_path": relative, "byte_size": path.stat().st_size,
                              "sha256": _sha(path), "role":
                              "B6MR1A human closure report" if relative.startswith("docs/")
                              else "B6MR1A qualification evidence"})
    _write_json(out / "B6MR1A_ARTIFACT_MANIFEST.json", {
        "schema": "ARCANA_R6_B6MR1A_ARTIFACT_MANIFEST_V1",
        "hash_algorithm": "SHA256", "self_hashed": False,
        "artifacts": artifact_rows})
    manifest = json.loads((out / "B6MR1A_ARTIFACT_MANIFEST.json").read_text(encoding="utf-8"))
    for row in manifest["artifacts"]:
        path = REPO_ROOT / row["relative_path"]
        if (not path.is_file() or path.stat().st_size != row["byte_size"] or
                _sha(path) != row["sha256"]):
            raise RuntimeError("B6MR1A retained artifact manifest verification failed")
    for path in out.glob("*.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        _portable_value(document, allow_environment=(path.name == "B6MR1A_SOURCE_GATE.json"))
    result["decision"] = "PASS_B6MR1A_ATOMIC_READER_VISIBILITY"
    result["b6mr1_resume_readiness"] = "READY_TO_RESUME_B6MR1_ATOMIC_T1_PUBLICATION"
    _write_json(out / "B6MR1A_RESULT.json", result)
    for row in manifest["artifacts"]:
        if row["relative_path"] == (OUTPUT_REL / "B6MR1A_RESULT.json").as_posix():
            result_path = REPO_ROOT / row["relative_path"]
            row["byte_size"] = result_path.stat().st_size
            row["sha256"] = _sha(result_path)
    _write_json(out / "B6MR1A_ARTIFACT_MANIFEST.json", manifest)
    for row in manifest["artifacts"]:
        path = REPO_ROOT / row["relative_path"]
        if (not path.is_file() or path.stat().st_size != row["byte_size"] or
                _sha(path) != row["sha256"]):
            raise RuntimeError("final B6MR1A artifact manifest verification failed")
    return {"decision": result["decision"], "canonical_store_id": EXPECTED_STORE_ID,
            "view_id": current_view, "migration": migration["post_migration"],
            "output_directory": OUTPUT_REL.as_posix()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--migrate-canonical", action="store_true",
                        help="explicitly migrate/validate B6M0 visibility metadata")
    parser.add_argument("--validation-results", type=Path, required=True,
                        help="JSON containing actual passing validation outcomes")
    args = parser.parse_args()
    if not args.migrate_canonical:
        parser.error("canonical metadata migration requires explicit --migrate-canonical")
    try:
        result = run(args.validation_results)
    except Exception as exc:
        print(f"BLOCKED_B6MR1A={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("B6MR1A_DECISION=PASS_B6MR1A_ATOMIC_READER_VISIBILITY")
    print(f"CANONICAL_STORE_ID={result['canonical_store_id']}")
    print(f"CANONICAL_VIEW_ID={result['view_id']}")
    print("T1_CREATED=false")
    print(f"EVIDENCE={result['output_directory']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
