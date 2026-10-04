"""Governed, idempotent B6M0 initialization of canonical WORLD_HISTORY."""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from .identity import canonical_bytes, content_hash
from .provenance import ProvenanceRecord
from .query import HistoryQueryService
from .state import DomainStateEnvelope, SupportClass
from .store import HistoryStore
from .t0_world_history_adapter import (
    T0AuthorityError, authority_inventory, build_records, source_snapshot,
)
from .temporal import AuthorityAnchor

EXPECTED_BRANCH = "r6/b6m0-canonical-world-history-bootstrap"
EXPECTED_HEAD = "d20c3533f2729a31d5c5823d1233a3ffc0b9a56a"
ROOT_ENV = "ARCANA_WORLD_HISTORY_ROOT"
STORE_ROLE = "ARCANA_R6_CANONICAL_WORLD_HISTORY"
STORE_DESCRIPTOR = "arcana_canonical_store.json"
DISCOVERY_SCHEMA = "ARCANA_R6_CANONICAL_WORLD_HISTORY_DISCOVERY_V1"


class CanonicalBootstrapError(RuntimeError):
    """B6M0 precondition, identity, or integrity failure."""


def _git(root: Path, *args: str, strip: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True,
                            capture_output=True, check=False)
    if result.returncode:
        raise CanonicalBootstrapError(
            f"git {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip() if strip else result.stdout.rstrip("\r\n")


def verify_source_gate(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    branch = _git(root, "branch", "--show-current")
    head = _git(root, "rev-parse", "--verify", "HEAD")
    object_type = _git(root, "cat-file", "-t", "HEAD")
    commit = _git(root, "log", "-1", "--format=%H%n%s", "HEAD").splitlines()
    if branch != EXPECTED_BRANCH or head != EXPECTED_HEAD or object_type != "commit":
        raise CanonicalBootstrapError("B6M0 source identity does not match the qualified baseline")
    if len(commit) < 2 or commit[0] != EXPECTED_HEAD:
        raise CanonicalBootstrapError("B6M0 HEAD commit log did not resolve expected commit")

    # The two named logs and B6M0 deliverables are permitted untracked evidence;
    # all tracked modifications and unrelated untracked paths fail closed.
    status = _git(root, "status", "--porcelain", "--untracked-files=all", strip=False)
    staged = _git(root, "diff", "--cached", "--name-only")
    if staged:
        raise CanonicalBootstrapError("B6M0 source gate rejects staged changes")
    allowed_untracked = {
        "B6J_CODEX_LUNA_RESULT.txt", "B6M_CODEX_LUNA_RESULT.txt",
        "scripts/r6_world_history_b6m0_canonical_bootstrap.py",
        "tests/test_r6_world_history_b6m0_canonical_bootstrap.py",
        "docs/arcana/B6M0_CANONICAL_WORLD_HISTORY_BOOTSTRAP.md",
    }
    unrelated: list[str] = []
    for line in status.splitlines():
        code, path = line[:2], line[3:]
        if code != "??" and path != "src/arcana_worldsim/r6/t0_world_history_adapter.py":
            unrelated.append(path)
        elif code == "??" and path not in allowed_untracked and path not in {
                "src/arcana_worldsim/r6/canonical_bootstrap.py",
                "src/arcana_worldsim/r6/t0_world_history_adapter.py"} and not path.startswith(
                "outputs/r6_b6m0_canonical_world_history_bootstrap/"):
            unrelated.append(path)
    if unrelated:
        raise CanonicalBootstrapError(
            "unrelated tracked modifications or untracked files: " + ", ".join(sorted(unrelated)))
    adapter_diff = _git(root, "diff", "--unified=0", "--",
                         "src/arcana_worldsim/r6/t0_world_history_adapter.py")
    changed_lines = [line for line in adapter_diff.splitlines()
                     if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))]
    expected_lines = [
        "-def authority_inventory(root: str | Path) -> dict[str, Any]:",
        "+def authority_inventory(root: str | Path, *,",
        '+                       expected_branch: str = "r6/b3-governed-t0-read-only-ingest"',
        "+                       ) -> dict[str, Any]:",
        '-    if branch != "r6/b3-governed-t0-read-only-ingest":',
        "+    if branch != expected_branch:",
    ]
    if changed_lines != expected_lines:
        raise CanonicalBootstrapError("T0 adapter diff exceeds the B6M0 branch-parameter extension")
    return {"branch": branch, "head": head, "object_type": object_type,
            "commit_subject": commit[1], "worktree_status": status.splitlines(),
            "known_local_logs_tolerated": True, "unrelated_worktree_changes": []}


def _expected_environment() -> dict[str, str]:
    expected = {
        "GIT_OBJECT_DIRECTORY": r"C:\Users\jose_\AppData\Local\ARCANA\git-objects\r6",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": (
            "F:\\corsiiiuu\\Magistrale\\Arcana\\ArcanaWorld\\"
            "ARCANA_WORLD1_v0_6D1_R3_11_POST_CHA1_H0_RECOVERY_ADAPTIVE_RADIATION_RESTART_CANDIDATE\\.git\\objects"),
        ROOT_ENV: r"F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\ARCANA_WORLD_HISTORY_R6_CANONICAL",
    }
    missing_or_different = {key: {"expected": value, "actual": os.environ.get(key)}
                            for key, value in expected.items()
                            if os.environ.get(key) != value}
    if missing_or_different:
        raise CanonicalBootstrapError(
            "B6M0 environment differs from supplied execution contract: "
            + json.dumps(missing_or_different, sort_keys=True))
    return expected


def _descriptor_identity(inventory: dict[str, Any], states: tuple[DomainStateEnvelope, ...],
                         state_info: dict[str, Any]
                         ) -> tuple[str, dict[str, Any]]:
    authority_hashes = sorted(item["sha256_actual"] for item in
                              inventory["tracked_authority_documents"])
    state_ids = sorted(str(state.state_id) for state in states)
    body = {
        "role": STORE_ROLE,
        "store_schema": HistoryStore.SCHEMA,
        "identity_format_version": HistoryStore.MANIFEST["identity_format_version"],
        "record_layout_version": HistoryStore.MANIFEST["record_layout_version"],
        "model_family": "ARCANA_R6_WORLD_HISTORY",
        "genesis_authority": "ARCANA_CURRENT_GOVERNED_T0",
        "source_authority_sha256": authority_hashes,
        "history_id": state_info["history_id"],
        "branch_id": state_info["branch_id"],
        "genesis_state_ids": state_ids,
        "canonical_temporal_state_count": 1,
        "transaction_contract": "B0_C_APPEND_TRANSACTION_V1",
        "semantic_identity_policy": "R6_CONTENT_DERIVED_PATH_INDEPENDENT_V1",
        "payload_reference_policy": "REFERENCE_EXISTING_GOVERNED_PAYLOADS",
    }
    store_id = "r6canonical_" + content_hash(body)
    return store_id, body


def _write_descriptor(root: Path, descriptor: dict[str, Any]) -> None:
    data = canonical_bytes(descriptor) + b"\n"
    target = root / STORE_DESCRIPTOR
    fd, name = tempfile.mkstemp(prefix=".b6m0-descriptor-", dir=root)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, target)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _read_descriptor(root: Path) -> dict[str, Any]:
    try:
        value = json.loads((root / STORE_DESCRIPTOR).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CanonicalBootstrapError("canonical target has no readable B6M0 descriptor") from exc
    if not isinstance(value, dict):
        raise CanonicalBootstrapError("canonical B6M0 descriptor is not an object")
    return value


def classify_canonical_root(root: str | Path, expected_store_id: str) -> str:
    """Classify a target without creating, deleting, or repairing any content."""
    path = Path(root)
    if path.is_symlink():
        return "NONEMPTY_UNRECOGNIZED_TARGET"
    if not path.exists():
        return "ABSENT"
    if not path.is_dir():
        return "NONEMPTY_UNRECOGNIZED_TARGET"
    if not any(path.iterdir()):
        return "EMPTY"
    descriptor_path = path / STORE_DESCRIPTOR
    if not descriptor_path.is_file():
        return "NONEMPTY_UNRECOGNIZED_TARGET"
    descriptor = _read_descriptor(path)
    if descriptor.get("store_identity") != expected_store_id:
        return "CONFLICTING_CANONICAL_STORE"
    return "VALID_EXISTING_CANONICAL_STORE"


def publish_staged_store(staging: str | Path, canonical_root: str | Path) -> None:
    """Install a complete private store with one same-volume directory rename."""
    staged, target = Path(staging), Path(canonical_root)
    if not staged.is_dir() or not (staged / STORE_DESCRIPTOR).is_file():
        raise CanonicalBootstrapError("staged canonical store is incomplete")
    if target.exists():
        if not target.is_dir() or any(target.iterdir()):
            raise CanonicalBootstrapError("canonical root changed before publication")
        target.rmdir()
    os.rename(staged, target)


def _validate_store(root: Path, expected: dict[str, Any],
                    states: tuple[DomainStateEnvelope, ...],
                    source_provenance: ProvenanceRecord) -> dict[str, Any]:
    descriptor = _read_descriptor(root)
    if descriptor.get("store_identity") != expected["store_identity"]:
        raise CanonicalBootstrapError("canonical target conflicts with expected store identity")
    if descriptor.get("store_identity_material") != expected["store_identity_material"]:
        raise CanonicalBootstrapError("canonical target identity material differs")
    manifest_path = root / "metadata" / "store_manifest.json"
    try:
        found_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CanonicalBootstrapError("canonical HistoryStore manifest is missing or unreadable") from exc
    if found_manifest != HistoryStore.MANIFEST:
        raise CanonicalBootstrapError("canonical HistoryStore schema manifest mismatch")
    store = HistoryStore(root)
    stored_manifest = store._read("metadata", "store_manifest")
    if stored_manifest != HistoryStore.MANIFEST:
        raise CanonicalBootstrapError("canonical HistoryStore schema manifest mismatch")
    state_rows = store.states()
    expected_ids = {str(item.state_id) for item in states}
    if {str(item.state_id) for item in state_rows} != expected_ids or len(state_rows) != len(states):
        raise CanonicalBootstrapError("canonical genesis state set is not exactly the governed T0 set")
    if {item.time_support.time_key for item in state_rows} != {"210Ma"}:
        raise CanonicalBootstrapError("canonical genesis includes an unexpected age")
    if any(item.support_class == SupportClass.UNKNOWN and item.value is not None
           for item in state_rows):
        raise CanonicalBootstrapError("UNKNOWN T0 semantics were not preserved")
    if store.read_provenance(str(source_provenance.record_id)) != source_provenance.to_dict():
        raise CanonicalBootstrapError("source T0 provenance is missing or changed")
    provenance_dir = root / "provenance"
    provenance_ids = {
        str(ProvenanceRecord.from_dict(json.loads(path.read_text(encoding="utf-8"))).record_id)
        for path in provenance_dir.glob("*.json")
    }
    expected_provenance_ids = {str(source_provenance.record_id),
                               str(descriptor.get("bootstrap_provenance_id"))}
    if provenance_ids != expected_provenance_ids:
        raise CanonicalBootstrapError("canonical provenance records differ from the declared genesis set")
    bootstrap_provenance = ProvenanceRecord.from_dict(json.loads(
        (provenance_dir / f"{descriptor['bootstrap_provenance_id']}.json").read_text(encoding="utf-8")))
    if (bootstrap_provenance.activity != "R6_B6M0_CANONICAL_HISTORY_INITIALIZATION"
            or str(source_provenance.record_id) not in bootstrap_provenance.parent_provenance_ids
            or bootstrap_provenance.attributes.get("simulation_step") is not False
            or bootstrap_provenance.attributes.get("canonical_state_changed") is not False):
        raise CanonicalBootstrapError("canonical bootstrap provenance is invalid")
    temporal = store.temporal_records(role="AUTHORITY_ANCHOR")
    anchors = [item for item in temporal if item["record_id"] == descriptor.get("genesis_anchor_id")]
    if len(anchors) != 1 or set(anchors[0]["state_ids"]) != expected_ids:
        raise CanonicalBootstrapError("canonical genesis authority anchor is missing or inconsistent")
    unexpected_records = {
        "events": store.events(), "checkpoints": store.checkpoints(),
        "forcings": store.forcings(), "replay_recipes": store.replay_recipes(),
        "refinement_branches": store.refinement_branches(),
        "refinement_recipes": store.refinement_recipes(),
    }
    if any(unexpected_records.values()):
        raise CanonicalBootstrapError("genesis store contains records outside the B6M0 scope")
    expected_files = {
        STORE_DESCRIPTOR, "metadata/store_manifest.json",
        *(f"states/{state_id}.json" for state_id in expected_ids),
        *(f"provenance/{provenance_id}.json" for provenance_id in expected_provenance_ids),
        f"temporal/{descriptor['genesis_anchor_id']}.json",
    }
    actual_files: set[str] = set()
    allowed_dirs = {"metadata", "states", "provenance", "temporal",
                    ".history_transactions", ".history_transactions/.retired"}
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise CanonicalBootstrapError("canonical store contains a symbolic link")
        if path.is_file():
            actual_files.add(relative)
        elif relative not in allowed_dirs:
            raise CanonicalBootstrapError("canonical store contains an unexpected directory")
    if actual_files != expected_files:
        raise CanonicalBootstrapError("canonical store file set differs from declared genesis contents")
    active_transactions = root / ".history_transactions"
    pending = []
    if active_transactions.exists():
        pending = [str(item.name) for item in active_transactions.iterdir()
                   if item.name != ".retired"]
    if pending:
        raise CanonicalBootstrapError("canonical store contains pending transaction journals")
    query = HistoryQueryService(store)
    physical = next(item for item in states if item.domain == "physical_geography")
    unknown = next(item for item in states if item.domain == "bathymetry")
    state_result = query.state_at(history_id=physical.history_id, branch_id=physical.branch_id,
                                  domain=physical.domain, time_key="210Ma")
    unknown_result = query.state_at(history_id=unknown.history_id, branch_id=unknown.branch_id,
                                    domain=unknown.domain, time_key="210Ma")
    history_result = query.history_result(history_id=physical.history_id,
                                          branch_id=physical.branch_id)
    why = query.why(str(physical.state_id))
    support = query.available_resolution(history_id=physical.history_id,
                                         branch_id=physical.branch_id,
                                         domain=physical.domain, time_key="210Ma")
    if (state_result.status != "FOUND" or unknown_result.status != "UNKNOWN"
            or len(history_result.states) != len(states)
            or len({s.time_support.time_key for s in history_result.states}) != 1
            or not why.provenance_records or why.unresolved_references
            or not any(record.activity == "R6_B3_GOVERNED_T0_READ_ONLY_WORLD_HISTORY_INGEST"
                       and record.attributes.get("forward_evolution") is False
                       for record in why.provenance_records)
            or support["status"] != "AVAILABLE"):
        raise CanonicalBootstrapError("canonical genesis query baseline failed")
    state_files = [root / "states" / f"{state_id}.json" for state_id in sorted(expected_ids)]
    payload_refs = sorted({str(state.payload_ref) for state in state_rows
                           if state.payload_ref is not None})
    byte_count = sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
    descriptor_hash = sha256((root / STORE_DESCRIPTOR).read_bytes()).hexdigest()
    manifest_hash = sha256((root / "metadata" / "store_manifest.json").read_bytes()).hexdigest()
    return {"store_identity": descriptor["store_identity"],
            "descriptor_sha256": descriptor_hash, "manifest_sha256": manifest_hash,
            "canonical_temporal_state_count": 1, "domain_state_record_count": len(state_rows),
            "genesis_state_ids": sorted(expected_ids), "latest_age_ma": 210.0,
            "state_query": state_result.status, "history_state_records": len(history_result.states),
            "why_provenance_records": len(why.provenance_records),
            "why_unresolved_references": list(why.unresolved_references),
            "support_status": support["status"], "unknown_status": unknown_result.status,
            "payload_references": payload_refs, "payload_bytes_copied": 0,
            "pending_transaction_count": len(pending), "persistent_bytes": byte_count,
            "runtime_root_exists": root.is_dir(), "state_record_files": len(state_files)}


def inspect_and_bootstrap(repo_root: str | Path, canonical_root: str | Path | None = None
                          ) -> dict[str, Any]:
    """Initialize or idempotently validate the sole env-governed canonical store."""
    environment = _expected_environment()
    git_gate = verify_source_gate(repo_root)
    root = Path(environment[ROOT_ENV]).absolute()
    if root.is_symlink():
        raise CanonicalBootstrapError("canonical root must not be a symbolic link")
    if canonical_root is not None and Path(canonical_root).resolve() != root:
        raise CanonicalBootstrapError("explicit canonical root differs from governed environment root")
    inventory = authority_inventory(repo_root, expected_branch=EXPECTED_BRANCH)
    if inventory["head"] != EXPECTED_HEAD:
        raise CanonicalBootstrapError("T0 adapter resolved a different source commit")
    before = source_snapshot(inventory)
    states, source_provenance, state_info = build_records(repo_root, inventory)
    after = source_snapshot(inventory)
    if before != after:
        raise CanonicalBootstrapError("governed T0 source changed while building genesis records")
    store_id, identity_material = _descriptor_identity(inventory, states, state_info)
    bootstrap_provenance = ProvenanceRecord.create(
        activity="R6_B6M0_CANONICAL_HISTORY_INITIALIZATION",
        input_refs=tuple(sorted(str(item.state_id) for item in states)),
        source_refs=tuple(sorted(f"artifact:{item['logical_path']}#sha256:{item['sha256_actual']}"
                                 for item in inventory["tracked_authority_documents"])),
        parent_provenance_ids=(str(source_provenance.record_id),),
        attributes={"operation": "CANONICAL_HISTORY_INITIALIZATION",
                    "genesis_age_ma": 210.0, "simulation_step": False,
                    "forward_evolution": False, "t1_created": False,
                    "canonical_state_changed": False, "store_identity": store_id})
    authority_refs = tuple(sorted(f"artifact:{item['logical_path']}#sha256:{item['sha256_actual']}"
                                  for item in inventory["tracked_authority_documents"]))
    anchor = AuthorityAnchor.create(
        history_id=state_info["history_id"], branch_id=state_info["branch_id"],
        time_key="210Ma", domain_ids=tuple(sorted(state_info["domains"])),
        state_ids=tuple(sorted(str(item.state_id) for item in states)),
        authority_refs=authority_refs,
        provenance_refs=(str(source_provenance.record_id), str(bootstrap_provenance.record_id)),
        validation_status="VALIDATED",
        details={"classification": "CANONICAL_GOVERNED_T0_GENESIS",
                 "preceding_world_history_state": None,
                 "initialization_is_not_forward_evolution": True,
                 "asynchronous_domains_not_advanced": True})
    descriptor = {"schema": DISCOVERY_SCHEMA, "store_role": STORE_ROLE,
        "store_identity": store_id, "store_identity_material": identity_material,
        "store_schema": HistoryStore.SCHEMA, "canonical_role": "CANONICAL_R6_GENESIS_HISTORY",
        "runtime_root_source": ROOT_ENV, "expected_genesis_authority": "ARCANA_CURRENT_GOVERNED_T0",
        "history_id": state_info["history_id"], "branch_id": state_info["branch_id"],
        "genesis_state_ids": sorted(str(item.state_id) for item in states),
        "genesis_anchor_id": anchor.record_id, "source_provenance_id": str(source_provenance.record_id),
        "bootstrap_provenance_id": str(bootstrap_provenance.record_id),
        "canonical_temporal_state_count": 1, "domain_state_record_count": len(states),
        "latest_age_ma": 210.0, "payload_policy": "REFERENCE_EXISTING_GOVERNED_PAYLOADS",
        "discovery_rules": ["read ARCANA_WORLD_HISTORY_ROOT", "require this descriptor",
                            "verify logical store identity and HistoryStore manifest"],
        "fail_closed": True,
        "scientific_gates": {"t1_created": False, "canonical_state_changed": False,
            "forward_evolution_authorized": False, "mechanics_authorized": False,
            "topology_transition_executed": False}}
    expected = {"store_identity": store_id, "store_identity_material": identity_material,
                "genesis_anchor_id": anchor.record_id}

    classification = classify_canonical_root(root, store_id)
    if classification == "CONFLICTING_CANONICAL_STORE":
        raise CanonicalBootstrapError(classification)
    if classification == "NONEMPTY_UNRECOGNIZED_TARGET":
        raise CanonicalBootstrapError(classification)
    if classification == "VALID_EXISTING_CANONICAL_STORE":
        snapshot = _validate_store(root, expected, states, source_provenance)
        return {"decision": "ALREADY_INITIALIZED_IDENTICAL", "root_status": classification,
                "store_identity": store_id, "git_source_gate": git_gate,
                "inventory": {k: v for k, v in inventory.items()
                              if k not in {"_repository_root", "source_paths_internal"}},
                "state_info": state_info, "integrity": snapshot,
                "store_identity_material": identity_material,
                "genesis_anchor_id": anchor.record_id,
                "bootstrap_provenance_id": str(bootstrap_provenance.record_id),
                "environment_status": "EXPECTED_VARIABLES_VERIFIED",
                "source_integrity": "PASS_UNCHANGED"}

    root.parent.mkdir(parents=True, exist_ok=True)
    staging = root.parent / f".{root.name}.b6m0-staging-{store_id[-12:]}"
    if staging.exists():
        raise CanonicalBootstrapError("unrecognized prior B6M0 staging directory exists")
    staging.mkdir()
    try:
        staged_store = HistoryStore(staging)
        published = staged_store.append_transaction((*states, source_provenance,
                                                       bootstrap_provenance, anchor))
        _write_descriptor(staging, descriptor)
        del staged_store
        # Reopen and validate the complete private staging tree before its atomic
        # same-volume directory rename makes it discoverable as canonical.
        _validate_store(staging, expected, states, source_provenance)
        publish_staged_store(staging, root)
    except Exception:
        # Leave staging evidence intact on failure; never erase ambiguous records.
        raise
    snapshot = _validate_store(root, expected, states, source_provenance)
    if source_snapshot(inventory) != before:
        raise CanonicalBootstrapError("governed scientific sources changed during canonical bootstrap")
    return {"decision": "INITIALIZED_CANONICAL_T0_GENESIS", "root_status": classification,
            "store_identity": store_id, "git_source_gate": git_gate,
            "inventory": {k: v for k, v in inventory.items()
                          if k not in {"_repository_root", "source_paths_internal"}},
            "state_info": state_info, "integrity": snapshot,
            "store_identity_material": identity_material,
            "genesis_anchor_id": anchor.record_id,
            "bootstrap_provenance_id": str(bootstrap_provenance.record_id),
            "initialization_transaction_record_ids": list(published),
            "environment_status": "EXPECTED_VARIABLES_VERIFIED",
            "source_integrity": "PASS_UNCHANGED"}


def discovery_contract(store_identity: str, genesis_state_ids: list[str]) -> dict[str, Any]:
    return {"schema": DISCOVERY_SCHEMA, "store_role": STORE_ROLE,
            "logical_store_id": store_identity, "store_schema": HistoryStore.SCHEMA,
            "canonical_role": "CANONICAL_R6_GENESIS_HISTORY",
            "runtime_root_source": ROOT_ENV,
            "expected_genesis_authority": "ARCANA_CURRENT_GOVERNED_T0",
            "expected_genesis_state_ids": sorted(genesis_state_ids),
            "expected_canonical_temporal_state_count": 1,
            "discovery": "resolve env root, verify descriptor identity and typed store records",
            "fail_closed": ["missing env", "missing root", "missing descriptor",
                            "identity mismatch", "manifest mismatch", "record integrity failure"],
            "absolute_path_in_semantic_identity": False}

