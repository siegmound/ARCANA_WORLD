"""Replaceable append-only JSON record store for R6 Wave 1."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Iterable, TypeVar
import json
import os
import shutil
import tempfile

from .checkpoint import CheckpointEnvelope, RefinementBranchEnvelope
from .identity import ProviderBindingId, canonical_bytes
from .provenance import ProvenanceIntegrityError, ProvenanceRecord
from .state import DomainStateEnvelope
from .temporal import EventRecord, TemporalRecord, temporal_record_from_dict


class ImmutableRecordConflict(ValueError):
    pass


class StoreSchemaError(ValueError):
    """Raised when a persisted store manifest is incompatible with this reader."""


class RecordIntegrityError(ValueError):
    """Raised when a stored record fails identity or key/content verification."""


class TransactionRecoveryError(RecordIntegrityError):
    """Raised when an interrupted transaction cannot be recovered unambiguously."""


T = TypeVar("T")


class HistoryStore:
    """File-backed reference store; identity and query APIs expose no path details."""

    SCHEMA = "ARCANA_R6_FILE_HISTORY_STORE_V0"
    MANIFEST = {
        "store_kind": "ARCANA_R6_FILE_HISTORY_STORE",
        "schema_version": SCHEMA,
        "identity_format_version": 1,
        "record_layout_version": 1,
    }

    _TRANSACTION_BUCKETS = frozenset({
        "states", "provenance", "events", "checkpoints", "temporal",
        "refinement_branches",
    })

    def __init__(self, root: str | Path, *,
                 _fault_injector: Callable[[str, int], None] | None = None):
        self.__root = Path(root)
        self.__transaction_root = self.__root / ".history_transactions"
        self.__fault_injector = _fault_injector
        self.__root.mkdir(parents=True, exist_ok=True)
        self._initialize_or_validate_manifest()
        self._recover_transactions()

    def _initialize_or_validate_manifest(self) -> None:
        try:
            self._write("metadata", "store_manifest", self.MANIFEST)
        except ImmutableRecordConflict:
            # A concurrent opener may have installed the same manifest, or an
            # incompatible one. The read below distinguishes those cases.
            pass
        try:
            found = self._read("metadata", "store_manifest")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise StoreSchemaError("store manifest is missing or unreadable") from exc
        if found != self.MANIFEST:
            raise StoreSchemaError("incompatible HistoryStore manifest/schema")
        self._fsync_directory(self.__root)

    def _write(self, bucket: str, key: str, body: dict[str, Any]) -> None:
        if not key or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in key):
            raise ValueError("unsafe record key")
        directory = self.__root / bucket
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"{key}.json"
        data = canonical_bytes(body) + b"\n"
        if target.exists():
            if target.read_bytes() == data:
                return
            raise ImmutableRecordConflict(f"immutable {bucket} record already differs: {key}")
        fd, tmp_name = tempfile.mkstemp(prefix=".r6-write-", dir=directory)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(tmp_name, target)
                self._fsync_directory(directory)
            except FileExistsError:
                if target.read_bytes() != data:
                    raise ImmutableRecordConflict(f"concurrent immutable record conflict: {key}")
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
                self._fsync_directory(directory)

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        """Best-effort directory-entry sync where the platform exposes it."""
        if os.name == "nt":
            return
        descriptor = None
        try:
            descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            os.fsync(descriptor)
        except OSError:
            # Directory fsync is not consistently supported by local filesystems.
            pass
        finally:
            if descriptor is not None:
                os.close(descriptor)

    @staticmethod
    def _safe_key(key: str) -> bool:
        return bool(key) and all(c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                                 for c in key)

    def _install_bytes(self, target: Path, data: bytes) -> bool:
        """Install bytes without overwrite; return whether this call created target."""
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=".r6-write-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(tmp_name, target)
                self._fsync_directory(target.parent)
                return True
            except FileExistsError:
                if target.read_bytes() != data:
                    raise ImmutableRecordConflict(f"immutable transaction target differs: {target.name}")
                return False
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
                self._fsync_directory(target.parent)

    def _fault(self, stage: str, published_count: int) -> None:
        if self.__fault_injector is not None:
            self.__fault_injector(stage, published_count)

    @staticmethod
    def _transaction_record(record: Any) -> tuple[str, str, dict[str, Any]]:
        if isinstance(record, DomainStateEnvelope):
            bucket, body, key = "states", record.to_dict(), str(record.state_id)
            parser = DomainStateEnvelope.from_dict
            identity = lambda value: str(value.state_id)
        elif isinstance(record, ProvenanceRecord):
            bucket, body, key = "provenance", record.to_dict(), str(record.record_id)
            parser = ProvenanceRecord.from_dict
            identity = lambda value: str(value.record_id)
        elif isinstance(record, EventRecord):
            bucket, body, key = "events", record.to_dict(), record.record_id
            parser = EventRecord.from_dict
            identity = lambda value: value.record_id
        elif isinstance(record, CheckpointEnvelope):
            bucket, body, key = "checkpoints", record.to_dict(), str(record.checkpoint_id)
            parser = CheckpointEnvelope.from_dict
            identity = lambda value: str(value.checkpoint_id)
        elif isinstance(record, RefinementBranchEnvelope):
            bucket, body, key = "refinement_branches", record.to_dict(), str(record.branch_id)
            parser = RefinementBranchEnvelope.from_dict
            identity = lambda value: str(value.branch_id)
        elif isinstance(record, TemporalRecord):
            bucket, body, key = "temporal", record.to_dict(), record.record_id
            parser = temporal_record_from_dict
            identity = lambda value: value.record_id
        else:
            raise TypeError(f"unsupported HistoryStore transaction record: {type(record).__name__}")
        if not HistoryStore._safe_key(key):
            raise ValueError("unsafe transaction record key")
        try:
            parsed = parser(body)
            if identity(parsed) != key:
                raise ValueError("transaction record identity mismatch")
        except Exception as exc:
            raise RecordIntegrityError(f"invalid transaction record: {key}") from exc
        return bucket, key, body

    @staticmethod
    def _transaction_id(entries: list[dict[str, Any]]) -> str:
        material = {"store_schema": HistoryStore.SCHEMA, "entries": entries}
        return "tx_" + sha256(canonical_bytes(material)).hexdigest()

    def _transaction_target(self, bucket: str, key: str) -> Path:
        if bucket not in self._TRANSACTION_BUCKETS or not self._safe_key(key):
            raise TransactionRecoveryError("transaction journal contains an unsafe target")
        target = self.__root / bucket / f"{key}.json"
        root = self.__root.resolve()
        if root not in target.resolve().parents:
            raise TransactionRecoveryError("transaction target escapes store root")
        return target

    def append_transaction(self, records: Iterable[Any]) -> tuple[str, ...]:
        """Atomically publish a small bundle of already-formed immutable records.

        Guarantees recoverable all-or-none state for one writer after return or
        the next store reopen. Concurrent visibility during publication and
        full power-loss durability are outside this API's contract.
        """
        prepared = []
        seen: set[tuple[str, str]] = set()
        for record in records:
            bucket, key, body = self._transaction_record(record)
            target_key = (bucket, key)
            if target_key in seen:
                raise ValueError(f"duplicate transaction target: {bucket}/{key}")
            seen.add(target_key)
            data = canonical_bytes(body) + b"\n"
            target = self._transaction_target(bucket, key)
            preexisting = target.exists()
            if preexisting and target.read_bytes() != data:
                raise ImmutableRecordConflict(f"immutable {bucket} record already differs: {key}")
            prepared.append({"bucket": bucket, "key": key,
                             "sha256": sha256(data).hexdigest(),
                             "preexisting": preexisting, "data": data})
        if not prepared:
            raise ValueError("transaction requires at least one record")

        prepared.sort(key=lambda item: (item["bucket"], item["key"]))
        entries = [{"bucket": item["bucket"], "key": item["key"],
                    "sha256": item["sha256"], "preexisting": item["preexisting"],
                    "stage": f"staged/{index:06d}.json"}
                   for index, item in enumerate(prepared)]
        transaction_id = self._transaction_id(entries)
        transaction_dir = self.__transaction_root / transaction_id
        if transaction_dir.exists():
            raise TransactionRecoveryError("transaction ID already has an active journal")
        staging_dir = transaction_dir / "staged"
        staging_dir.mkdir(parents=True)
        self._fsync_directory(self.__transaction_root)
        self._fsync_directory(self.__root)
        self._fsync_directory(transaction_dir)

        manifest = {"transaction_id": transaction_id,
                    "store_schema": self.SCHEMA,
                    "entries": entries}
        try:
            for item, entry in zip(prepared, entries):
                self._install_bytes(transaction_dir / entry["stage"], item["data"])
            self._install_bytes(transaction_dir / "manifest.json",
                                canonical_bytes(manifest) + b"\n")
            self._write_marker(transaction_dir, "PREPARED", transaction_id)
            self._write_marker(transaction_dir, "PUBLISHING", transaction_id)
            self._fault("before_publication", 0)
            for index, entry in enumerate(entries, 1):
                staged = transaction_dir / entry["stage"]
                target = self._transaction_target(entry["bucket"], entry["key"])
                created = self._link_staged(staged, target, entry["sha256"])
                if created:
                    self._fsync_directory(target.parent)
                self._fault("after_publication", index)
            self._fault("before_commit", len(entries))
            self._write_marker(transaction_dir, "COMMITTED", transaction_id)
            try:
                self._fault("during_cleanup", len(entries))
                self._retire_transaction(transaction_dir, transaction_id)
            except Exception:
                # Keep the committed journal for deterministic reopen cleanup.
                pass
        except Exception:
            if not self._has_marker(transaction_dir, "COMMITTED"):
                self._recover_one_transaction(transaction_dir)
                raise
            # The commit marker is the logical commit point. Cleanup failure
            # cannot revoke a transaction whose complete targets were published.
            try:
                self._retire_transaction(transaction_dir, transaction_id)
            except OSError:
                pass
        return tuple(entry["key"] for entry in entries)

    def _write_marker(self, transaction_dir: Path, state: str, transaction_id: str) -> None:
        if state not in {"PREPARED", "PUBLISHING", "COMMITTED"}:
            raise ValueError("invalid transaction state")
        marker = transaction_dir / f"{state}.json"
        body = {"transaction_id": transaction_id, "state": state}
        self._install_bytes(marker, canonical_bytes(body) + b"\n")
        self._fsync_directory(transaction_dir)

    @staticmethod
    def _has_marker(transaction_dir: Path, state: str) -> bool:
        return (transaction_dir / f"{state}.json").is_file()

    def _link_staged(self, staged: Path, target: Path, expected_hash: str) -> bool:
        data = staged.read_bytes()
        if sha256(data).hexdigest() != expected_hash:
            raise TransactionRecoveryError("staged record digest mismatch")
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(staged, target)
            self._fsync_directory(target.parent)
            return True
        except FileExistsError:
            if target.read_bytes() != data:
                raise ImmutableRecordConflict(
                    f"immutable transaction target differs: {target.name}")
            return False

    def _retire_transaction(self, transaction_dir: Path, transaction_id: str) -> None:
        retired_root = self.__transaction_root / ".retired"
        retired_root.mkdir(parents=True, exist_ok=True)
        retired = retired_root / transaction_id
        if transaction_dir.exists():
            if retired.exists():
                raise TransactionRecoveryError("both active and retired transaction journals exist")
            os.replace(transaction_dir, retired)
            self._fsync_directory(self.__transaction_root)
        try:
            shutil.rmtree(retired)
            self._fsync_directory(retired_root)
        except OSError:
            # A retired journal is outside the active scan and cannot affect records.
            pass

    def _recover_transactions(self) -> None:
        if not self.__transaction_root.exists():
            return
        for path in sorted(self.__transaction_root.iterdir()):
            if path.name == ".retired":
                if path.is_dir():
                    for retired in sorted(path.iterdir()):
                        if retired.is_dir():
                            try:
                                shutil.rmtree(retired)
                            except OSError:
                                pass
                continue
            if not path.is_dir():
                raise TransactionRecoveryError(f"unexpected transaction metadata entry: {path.name}")
            self._recover_one_transaction(path)

    def _recover_one_transaction(self, transaction_dir: Path) -> None:
        manifest_path = transaction_dir / "manifest.json"
        publishing = self._has_marker(transaction_dir, "PUBLISHING")
        committed = self._has_marker(transaction_dir, "COMMITTED")
        transaction_id = transaction_dir.name
        if not manifest_path.exists():
            staged_content = (transaction_dir / "staged").exists() and any(
                (transaction_dir / "staged").iterdir())
            if (publishing or committed or self._has_marker(transaction_dir, "PREPARED")
                    or staged_content):
                raise TransactionRecoveryError("transaction journal lost its manifest in an ambiguous state")
            self._retire_transaction(transaction_dir, transaction_id)
            return
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict) or manifest.get("store_schema") != self.SCHEMA:
                raise ValueError("transaction store schema mismatch")
            entries = manifest.get("entries")
            if not isinstance(entries, list) or not entries:
                raise ValueError("transaction manifest entries are invalid")
            if manifest.get("transaction_id") != transaction_id or self._transaction_id(entries) != transaction_id:
                raise ValueError("transaction manifest identity mismatch")
            seen: set[tuple[str, str]] = set()
            for entry in entries:
                if (not isinstance(entry, dict) or set(entry) !=
                        {"bucket", "key", "sha256", "preexisting", "stage"}):
                    raise ValueError("transaction manifest entry is malformed")
                bucket, key = entry["bucket"], entry["key"]
                self._transaction_target(bucket, key)
                if not isinstance(entry["preexisting"], bool):
                    raise ValueError("transaction preexisting flag is invalid")
                if not isinstance(entry["sha256"], str) or len(entry["sha256"]) != 64:
                    raise ValueError("transaction content digest is invalid")
                if entry["stage"] != f"staged/{len(seen):06d}.json":
                    raise ValueError("transaction staging path is invalid")
                if (bucket, key) in seen:
                    raise ValueError("transaction manifest contains duplicate targets")
                seen.add((bucket, key))
            for state in ("PREPARED", "PUBLISHING", "COMMITTED"):
                marker_path = transaction_dir / f"{state}.json"
                if marker_path.exists():
                    marker = json.loads(marker_path.read_text(encoding="utf-8"))
                    if marker != {"transaction_id": transaction_id, "state": state}:
                        raise ValueError(f"{state} marker is corrupt")
            if committed:
                self._finalize_committed(transaction_dir, transaction_id, entries)
            else:
                self._rollback_transaction(transaction_dir, transaction_id, entries)
        except TransactionRecoveryError:
            raise
        except Exception as exc:
            raise TransactionRecoveryError(
                f"transaction journal is corrupt or ambiguous: {transaction_id}") from exc

    def _rollback_transaction(self, transaction_dir: Path, transaction_id: str,
                              entries: list[dict[str, Any]]) -> None:
        for entry in entries:
            target = self._transaction_target(entry["bucket"], entry["key"])
            if not target.exists():
                if entry["preexisting"]:
                    raise TransactionRecoveryError(
                        f"pre-existing transaction target is missing: {entry['bucket']}/{entry['key']}")
                continue
            actual_hash = sha256(target.read_bytes()).hexdigest()
            if actual_hash != entry["sha256"]:
                raise TransactionRecoveryError(
                    f"transaction target has ambiguous content: {entry['bucket']}/{entry['key']}")
            if not entry["preexisting"]:
                target.unlink()
                self._fsync_directory(target.parent)
        self._retire_transaction(transaction_dir, transaction_id)

    def _finalize_committed(self, transaction_dir: Path, transaction_id: str,
                            entries: list[dict[str, Any]]) -> None:
        for entry in entries:
            target = self._transaction_target(entry["bucket"], entry["key"])
            if not target.is_file() or sha256(target.read_bytes()).hexdigest() != entry["sha256"]:
                raise TransactionRecoveryError(
                    f"committed transaction target is missing or corrupt: {entry['bucket']}/{entry['key']}")
        self._retire_transaction(transaction_dir, transaction_id)

    def _read(self, bucket: str, key: str) -> dict[str, Any]:
        if not key or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in key):
            raise ValueError("unsafe record key")
        path = self.__root / bucket / f"{key}.json"
        row = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(row, dict):
            raise ValueError(f"{bucket} record must be a JSON object")
        return row

    def _all(self, bucket: str) -> list[dict[str, Any]]:
        directory = self.__root / bucket
        if not directory.exists():
            return []
        rows = []
        for path in sorted(directory.glob("*.json")):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise RecordIntegrityError(
                    f"{bucket} record is unreadable: {path.name}") from exc
            if not isinstance(row, dict):
                raise RecordIntegrityError(f"{bucket} record is not a JSON object: {path.name}")
            rows.append(row)
        return rows

    def _typed(self, bucket: str, key: str, record_type: str,
               parser: Callable[[dict[str, Any]], T],
               identity: Callable[[T], str]) -> T:
        try:
            row = self._read(bucket, key)
            record = parser(row)
            if identity(record) != key:
                raise ValueError("record key does not match its identity")
            return record
        except FileNotFoundError:
            raise
        except Exception as exc:
            raise RecordIntegrityError(
                f"{record_type} record failed identity verification: {key}") from exc

    def _typed_all(self, bucket: str, record_type: str,
                   parser: Callable[[dict[str, Any]], T],
                   identity: Callable[[T], str]) -> tuple[T, ...]:
        result = []
        for row in self._all(bucket):
            try:
                record = parser(row)
                key = row.get("record_id") or row.get("state_id") or row.get("checkpoint_id") or row.get("branch_id")
                if key is None or identity(record) != str(key):
                    raise ValueError("record key does not match its identity")
                result.append(record)
            except Exception as exc:
                raise RecordIntegrityError(f"{record_type} record failed identity verification") from exc
        return tuple(result)

    def append_state(self, state: DomainStateEnvelope) -> str:
        self._write("states", str(state.state_id), state.to_dict())
        return str(state.state_id)

    def read_state(self, state_id: str) -> DomainStateEnvelope:
        return self._typed("states", state_id, "state", DomainStateEnvelope.from_dict,
                           lambda row: str(row.state_id))

    def states(self) -> tuple[DomainStateEnvelope, ...]:
        return self._typed_all("states", "state", DomainStateEnvelope.from_dict,
                               lambda row: str(row.state_id))

    def append_provenance(self, record: ProvenanceRecord) -> str:
        self._write("provenance", str(record.record_id), record.to_dict())
        return str(record.record_id)

    def read_provenance(self, record_id: str) -> dict[str, Any]:
        return self._typed("provenance", record_id, "provenance",
                           ProvenanceRecord.from_dict, lambda row: str(row.record_id)).to_dict()

    def append_event(self, event: EventRecord) -> str:
        self._write("events", event.record_id, event.to_dict())
        return event.record_id

    def read_event(self, event_id: str) -> dict[str, Any]:
        return self._typed("events", event_id, "event", EventRecord.from_dict,
                           lambda row: row.record_id).to_dict()

    def append_checkpoint(self, checkpoint: CheckpointEnvelope) -> str:
        self._write("checkpoints", str(checkpoint.checkpoint_id), checkpoint.to_dict())
        return str(checkpoint.checkpoint_id)

    def read_checkpoint(self, checkpoint_id: str) -> dict[str, Any]:
        return self._typed("checkpoints", checkpoint_id, "checkpoint",
                           CheckpointEnvelope.from_dict,
                           lambda row: str(row.checkpoint_id)).to_dict()

    def append_provider_binding(self, binding_id: str, record: dict[str, Any]) -> str:
        if str(ProviderBindingId.from_payload(record)) != binding_id:
            raise RecordIntegrityError("provider binding identity does not match content")
        self._write("provider_bindings", binding_id, record)
        return binding_id

    def read_provider_binding(self, binding_id: str) -> dict[str, Any]:
        def parse(row: dict[str, Any]) -> dict[str, Any]:
            if str(ProviderBindingId.from_payload(row)) != binding_id:
                raise ValueError("provider binding identity does not match content")
            return row
        return self._typed("provider_bindings", binding_id, "provider binding",
                           parse, lambda row: str(ProviderBindingId.from_payload(row)))

    def append_temporal(self, record: TemporalRecord) -> str:
        self._write("temporal", record.record_id, record.to_dict())
        return record.record_id

    def read_temporal(self, record_id: str) -> dict[str, Any]:
        return self._typed("temporal", record_id, "temporal record",
                           temporal_record_from_dict, lambda row: row.record_id).to_dict()

    def events(self) -> tuple[EventRecord, ...]:
        return self._typed_all("events", "event", EventRecord.from_dict,
                               lambda row: row.record_id)

    def temporal_records(self, *, role: str | None = None) -> tuple[dict[str, Any], ...]:
        records = self._typed_all("temporal", "temporal record",
                                  temporal_record_from_dict, lambda row: row.record_id)
        rows = [record.to_dict() for record in records]
        if role is not None:
            rows = [row for row in rows if row.get("role") == role]
        return tuple(rows)

    def checkpoints(self) -> tuple[CheckpointEnvelope, ...]:
        return self._typed_all("checkpoints", "checkpoint", CheckpointEnvelope.from_dict,
                               lambda row: str(row.checkpoint_id))

    def append_refinement_branch(self, branch: RefinementBranchEnvelope) -> str:
        key = str(branch.branch_id)
        self._write("refinement_branches", key, branch.to_dict())
        return key

    def read_refinement_branch(self, branch_id: str) -> RefinementBranchEnvelope:
        return self._typed("refinement_branches", branch_id, "refinement branch",
                           RefinementBranchEnvelope.from_dict,
                           lambda row: str(row.branch_id))

    def refinement_branches(self) -> tuple[RefinementBranchEnvelope, ...]:
        return self._typed_all("refinement_branches", "refinement branch",
                               RefinementBranchEnvelope.from_dict,
                               lambda row: str(row.branch_id))

    def find_states(self, *, history_id: str, branch_id: str | None = None,
                    domain: str | None = None, time_key: str | None = None,
                    cell_id: str | None = None) -> tuple[DomainStateEnvelope, ...]:
        found = []
        for state in self.states():
            if state.history_id != history_id:
                continue
            if branch_id is not None and state.branch_id != branch_id:
                continue
            if domain is not None and state.domain != domain:
                continue
            if time_key is not None and state.time_support.time_key != time_key:
                continue
            if cell_id is not None and cell_id not in state.spatial_support.cell_ids:
                continue
            found.append(state)
        return tuple(found)

    def trace_provenance(self, state: DomainStateEnvelope) -> dict[str, Any]:
        records: list[dict[str, Any]] = []
        sources: set[str] = set()
        seen: set[str] = set()

        def visit(record_id: str) -> None:
            if record_id in seen:
                return
            seen.add(record_id)
            try:
                row = self.read_provenance(record_id)
            except FileNotFoundError as exc:
                raise ProvenanceIntegrityError(
                    f"missing provenance parent record: {record_id}") from exc
            records.append(row)
            sources.update(str(x) for x in row.get("source_refs", []))
            for parent in row.get("parent_provenance_ids", []):
                visit(str(parent))

        for provenance_id in state.provenance_ids:
            visit(provenance_id)
        return {"state_id": str(state.state_id), "provenance_records": records,
                "source_refs": sorted(sources)}
