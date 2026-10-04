"""Replaceable append-only JSON record store for R6 Wave 1."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Iterable, TypeVar
import json
import os
import shutil
import tempfile
import threading
import ctypes

from .checkpoint import CheckpointEnvelope, RefinementBranchEnvelope
from .forcing import ForcingRecord
from .identity import ProviderBindingId, canonical_bytes, content_hash, thaw_json
from .provenance import ProvenanceIntegrityError, ProvenanceRecord
from .refinement import RefinementReconstructionRecipe
from .replay import ReplayRecipe
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


class ReadViewMigrationRequired(StoreSchemaError):
    """A legacy store must be migrated explicitly before typed reads are allowed."""


class ReadViewIntegrityError(RecordIntegrityError):
    """The committed visibility pointer or immutable read-view failed validation."""


@dataclass(frozen=True, slots=True)
class ReadView:
    """Immutable membership snapshot for one logical WORLD_HISTORY read session."""

    view_id: str
    records: Any


_LOCKS_GUARD = threading.Lock()
_PROCESS_LOCKS: dict[str, threading.RLock] = {}
_VIEW_SCHEMA = "ARCANA_R6_COMMITTED_READ_VIEW_V1"
_VIEW_BUCKETS = (
    "states", "provenance", "events", "checkpoints", "temporal",
    "refinement_branches", "refinement_recipes", "forcings", "replay_recipes",
    "provider_bindings",
)


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
        "refinement_branches", "refinement_recipes", "forcings", "replay_recipes",
    })

    def __init__(self, root: str | Path, *,
                 _fault_injector: Callable[[str, int], None] | None = None,
                 _migrate_legacy_visibility: bool = False):
        self.__root = Path(root)
        self.__transaction_root = self.__root / ".history_transactions"
        self.__visibility_root = self.__root / ".history_visibility"
        self.__views_root = self.__visibility_root / "views"
        self.__current_view_path = self.__visibility_root / "CURRENT.json"
        self.__writer_lock_path = self.__visibility_root / "WRITER.lock"
        lock_key = str(self.__root.resolve())
        with _LOCKS_GUARD:
            self.__process_lock = _PROCESS_LOCKS.setdefault(lock_key, threading.RLock())
        self.__read_view_context: ContextVar[ReadView | None] = ContextVar(
            f"r6_read_view_{id(self)}", default=None)
        self.__fault_injector = _fault_injector
        self.__root.mkdir(parents=True, exist_ok=True)
        self._verify_atomic_visibility_filesystem()
        if (not self.__current_view_path.is_file() and self._has_record_files()
                and not _migrate_legacy_visibility):
            raise ReadViewMigrationRequired(
                "legacy WORLD_HISTORY records lack committed read-view metadata; "
                "run explicit deterministic migration before opening")
        self._initialize_or_validate_manifest()
        has_view = self.__current_view_path.is_file()
        has_records = self._has_record_files()
        if not has_view and has_records and not _migrate_legacy_visibility:
            raise ReadViewMigrationRequired(
                "legacy WORLD_HISTORY records lack committed read-view metadata; "
                "run explicit deterministic migration before opening")
        if not has_view and has_records:
            with self._writer_lock():
                self._recover_transactions()
            self.migrate_legacy_visibility()
        else:
            if not has_view:
                self.__visibility_root.mkdir(parents=True, exist_ok=True)
                self.__views_root.mkdir(parents=True, exist_ok=True)
                empty = {bucket: () for bucket in _VIEW_BUCKETS}
                view_id = self._write_view_manifest(empty)
                self._switch_current_view(view_id)
            else:
                self._load_committed_view()
            with self._writer_lock():
                self._recover_transactions()

    @property
    def root(self) -> Path:
        """Filesystem location for explicit operational accounting only."""
        return self.__root

    @contextmanager
    def _writer_lock(self):
        """Serialize local writers across threads and independent processes."""
        self.__visibility_root.mkdir(parents=True, exist_ok=True)
        with self.__process_lock:
            handle = self.__writer_lock_path.open("a+b")
            try:
                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b"\0")
                    handle.flush()
                    os.fsync(handle.fileno())
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    if os.name == "nt":
                        import msvcrt
                        handle.seek(0)
                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()

    def _has_record_files(self) -> bool:
        return any((self.__root / bucket).exists() and
                   any((self.__root / bucket).glob("*.json"))
                   for bucket in _VIEW_BUCKETS)

    def _verify_atomic_visibility_filesystem(self) -> None:
        """Fail closed on Windows volumes outside the qualified local NTFS scope."""
        if os.name != "nt":
            return
        root = str(self.__root.resolve())
        volume = ctypes.create_unicode_buffer(32768)
        kernel32 = ctypes.windll.kernel32
        if not kernel32.GetVolumePathNameW(root, volume, len(volume)):
            raise StoreSchemaError("cannot determine WORLD_HISTORY filesystem volume")
        drive_type = kernel32.GetDriveTypeW(volume.value)
        if drive_type != 3:  # DRIVE_FIXED
            raise StoreSchemaError("atomic read-view publication requires a fixed local Windows volume")
        fs_name = ctypes.create_unicode_buffer(256)
        if not kernel32.GetVolumeInformationW(volume.value, None, 0, None, None, None,
                                               fs_name, len(fs_name)):
            raise StoreSchemaError("cannot determine WORLD_HISTORY filesystem type")
        if fs_name.value.upper() != "NTFS":
            raise StoreSchemaError("atomic read-view publication is qualified only on local NTFS")

    @staticmethod
    def _view_material(records: dict[str, Iterable[str]]) -> dict[str, Any]:
        return {"schema": _VIEW_SCHEMA,
                "records": {bucket: sorted(set(records.get(bucket, ())))
                            for bucket in _VIEW_BUCKETS}}

    def _write_view_manifest(self, records: dict[str, Iterable[str]]) -> str:
        body = self._view_material(records)
        view_id = "view_" + sha256(canonical_bytes(body)).hexdigest()
        data = canonical_bytes({"view_id": view_id, **body}) + b"\n"
        path = self.__views_root / f"{view_id}.json"
        self._install_bytes(path, data)
        return view_id

    def _switch_current_view(self, view_id: str) -> None:
        """The os.replace of CURRENT.json is the single visibility linearization point."""
        target = self.__views_root / f"{view_id}.json"
        if not target.is_file():
            raise ReadViewIntegrityError("cannot publish a missing committed read-view")
        body = {"schema": _VIEW_SCHEMA, "view_id": view_id}
        data = canonical_bytes(body) + b"\n"
        fd, temp_name = tempfile.mkstemp(prefix=".CURRENT-", dir=self.__visibility_root)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.__current_view_path)
            self._fsync_directory(self.__visibility_root)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def _load_view_by_id(self, view_id: str) -> ReadView:
        try:
            if not view_id.startswith("view_") or not self._safe_key(view_id):
                raise ValueError("read-view identity is unsafe")
            body = json.loads((self.__views_root / f"{view_id}.json").read_text(encoding="utf-8"))
            material = {"schema": body.get("schema"), "records": body.get("records")}
            if (body.get("view_id") != view_id or body.get("schema") != _VIEW_SCHEMA or
                    "records" not in body or
                    "view_" + sha256(canonical_bytes(material)).hexdigest() != view_id):
                raise ValueError("immutable read-view identity mismatch")
            records = body["records"]
            if set(records) != set(_VIEW_BUCKETS):
                raise ValueError("read-view bucket set mismatch")
            normalized = {}
            for bucket in _VIEW_BUCKETS:
                values = records[bucket]
                if (not isinstance(values, list) or values != sorted(set(values)) or
                        any(not isinstance(value, str) or not self._safe_key(value)
                            for value in values)):
                    raise ValueError(f"read-view membership is invalid: {bucket}")
                normalized[bucket] = frozenset(values)
            return ReadView(view_id, MappingProxyType(normalized))
        except Exception as exc:
            raise ReadViewIntegrityError("immutable read-view is missing or corrupt") from exc

    def _load_committed_view(self) -> ReadView:
        try:
            pointer = json.loads(self.__current_view_path.read_text(encoding="utf-8"))
            if pointer.get("schema") != _VIEW_SCHEMA:
                raise ValueError("read-view pointer schema mismatch")
            return self._load_view_by_id(str(pointer["view_id"]))
        except Exception as exc:
            if isinstance(exc, ReadViewIntegrityError):
                raise
            raise ReadViewIntegrityError("committed read-view pointer is missing or corrupt") from exc

    @contextmanager
    def read_view(self):
        """Pin one immutable committed view for a complete logical read operation."""
        active = self.__read_view_context.get()
        if active is not None:
            yield active
            return
        view = self._load_committed_view()
        token = self.__read_view_context.set(view)
        try:
            yield view
        finally:
            self.__read_view_context.reset(token)

    def _active_read_view(self) -> ReadView:
        return self.__read_view_context.get() or self._load_committed_view()

    def migrate_legacy_visibility(self) -> ReadView:
        """Explicitly validate raw legacy records and publish their initial view."""
        if self.__current_view_path.exists():
            return self._load_committed_view()
        with self._writer_lock():
            if self.__current_view_path.exists():
                return self._load_committed_view()
            parsers: dict[str, tuple[Callable[[dict[str, Any]], Any], Callable[[Any], str]]] = {
                "states": (DomainStateEnvelope.from_dict, lambda x: str(x.state_id)),
                "provenance": (ProvenanceRecord.from_dict, lambda x: str(x.record_id)),
                "events": (EventRecord.from_dict, lambda x: x.record_id),
                "checkpoints": (CheckpointEnvelope.from_dict, lambda x: str(x.checkpoint_id)),
                "temporal": (temporal_record_from_dict, lambda x: x.record_id),
                "refinement_branches": (RefinementBranchEnvelope.from_dict, lambda x: str(x.branch_id)),
                "refinement_recipes": (RefinementReconstructionRecipe.from_dict, lambda x: str(x.recipe_id)),
                "forcings": (ForcingRecord.from_dict, lambda x: str(x.forcing_id)),
                "replay_recipes": (ReplayRecipe.from_dict, lambda x: str(x.recipe_id)),
            }
            records: dict[str, list[str]] = {bucket: [] for bucket in _VIEW_BUCKETS}
            for bucket in _VIEW_BUCKETS:
                directory = self.__root / bucket
                if not directory.exists():
                    continue
                for path in sorted(directory.glob("*.json")):
                    row = json.loads(path.read_text(encoding="utf-8"))
                    if bucket == "provider_bindings":
                        record_id = str(ProviderBindingId.from_payload(row))
                        if record_id != path.stem:
                            raise ReadViewIntegrityError("legacy provider binding identity mismatch")
                    else:
                        parser, identity = parsers[bucket]
                        record_id = identity(parser(row))
                        if record_id != path.stem:
                            raise ReadViewIntegrityError(f"legacy {bucket} record identity mismatch")
                    records[bucket].append(record_id)
            view_id = self._write_view_manifest(records)
            self._switch_current_view(view_id)
            return self._load_committed_view()

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
        elif isinstance(record, ForcingRecord):
            bucket, body, key = "forcings", record.to_dict(), str(record.forcing_id)
            parser = ForcingRecord.from_dict
            identity = lambda value: str(value.forcing_id)
        elif isinstance(record, ReplayRecipe):
            bucket, body, key = "replay_recipes", record.to_dict(), str(record.recipe_id)
            parser = ReplayRecipe.from_dict
            identity = lambda value: str(value.recipe_id)
        elif isinstance(record, RefinementReconstructionRecipe):
            bucket, body, key = "refinement_recipes", record.to_dict(), str(record.recipe_id)
            parser = RefinementReconstructionRecipe.from_dict
            identity = lambda value: str(value.recipe_id)
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

    def append_transaction(self, records: Iterable[Any], *,
                           _refinement_branch_id: str | None = None,
                           expected_parent_view_id: str | None = None) -> tuple[str, ...]:
        """Publish a record bundle by atomically switching committed read views."""
        with self._writer_lock():
            parent_view = self._load_committed_view()
            if (expected_parent_view_id is not None and
                    expected_parent_view_id != parent_view.view_id):
                raise ImmutableRecordConflict("writer parent read-view is stale")
            return self._append_transaction_locked(records,
                _refinement_branch_id=_refinement_branch_id, parent_view=parent_view)

    def _append_transaction_locked(self, records: Iterable[Any], *,
                                   _refinement_branch_id: str | None,
                                   parent_view: ReadView) -> tuple[str, ...]:
        records = tuple(records)
        declared_refinement_ids = {str(record.branch_id) for record in records
                                   if isinstance(record, RefinementBranchEnvelope)}
        for record in records:
            if not isinstance(record, DomainStateEnvelope):
                continue
            candidate_branch_id = record.branch_id
            is_refinement_branch = candidate_branch_id in declared_refinement_ids
            if not is_refinement_branch:
                try:
                    self.read_refinement_branch(candidate_branch_id)
                    is_refinement_branch = True
                except FileNotFoundError:
                    pass
            if is_refinement_branch and _refinement_branch_id != candidate_branch_id:
                raise ValueError("refinement child states require branch-bound transaction API")
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
        next_records = {bucket: set(parent_view.records[bucket]) for bucket in _VIEW_BUCKETS}
        for entry in entries:
            next_records[entry["bucket"]].add(entry["key"])
        next_view_id = self._write_view_manifest(next_records)
        if next_view_id == parent_view.view_id:
            return tuple(entry["key"] for entry in entries)
        self._fault("after_view_preparation", len(entries))
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
                    "parent_view_id": parent_view.view_id,
                    "next_view_id": next_view_id,
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
            self._fault("before_visibility_switch", len(entries))
            self._switch_current_view(next_view_id)
            self._fault("after_visibility_switch", len(entries))
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
            # The current-view switch is the logical commit point.
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
            parent_view_id = manifest.get("parent_view_id")
            next_view_id = manifest.get("next_view_id")
            if (parent_view_id is None) != (next_view_id is None):
                raise ValueError("transaction view lineage is incomplete")
            if parent_view_id is not None and any(
                    not isinstance(value, str) or not self._safe_key(value)
                    for value in (parent_view_id, next_view_id)):
                raise ValueError("transaction view lineage is invalid")
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
            if parent_view_id is not None:
                parent_view = self._load_view_by_id(parent_view_id)
                next_view = self._load_view_by_id(next_view_id)
                expected_records = {bucket: set(parent_view.records[bucket])
                                    for bucket in _VIEW_BUCKETS}
                for entry in entries:
                    if entry["bucket"] not in expected_records:
                        raise ValueError("transaction target is outside read-view membership")
                    expected_records[entry["bucket"]].add(entry["key"])
                expected_material = self._view_material(expected_records)
                expected_view_id = "view_" + sha256(canonical_bytes(expected_material)).hexdigest()
                if next_view.view_id != expected_view_id:
                    raise TransactionRecoveryError("transaction next read-view is not the declared parent plus records")
                current_view_id = self._load_committed_view().view_id
                if current_view_id == next_view_id:
                    # The atomic CURRENT switch is the commit point. A crash
                    # afterward is completed, never rolled back.
                    if not committed:
                        self._write_marker(transaction_dir, "COMMITTED", transaction_id)
                    self._finalize_committed(transaction_dir, transaction_id, entries)
                elif current_view_id == parent_view_id:
                    if committed:
                        raise TransactionRecoveryError(
                            "COMMITTED transaction is not present in the current read-view")
                    self._rollback_transaction(transaction_dir, transaction_id, entries)
                else:
                    raise TransactionRecoveryError(
                        "transaction parent/current read-view lineage is ambiguous")
            elif committed:
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
            if bucket in _VIEW_BUCKETS and key not in self._active_read_view().records[bucket]:
                raise FileNotFoundError(f"{bucket} record is not visible in the pinned read-view: {key}")
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
        # Pin before touching raw files. A writer may materialize records and
        # switch CURRENT between enumeration and membership filtering.
        view = self._active_read_view()
        result = []
        rows = self._all(bucket)
        if bucket in _VIEW_BUCKETS:
            keys = view.records[bucket]
            key_fields = {"states": ("state_id",), "provenance": ("record_id",),
                "events": ("record_id",), "checkpoints": ("checkpoint_id",),
                "temporal": ("record_id",), "refinement_branches": ("branch_id",),
                "refinement_recipes": ("recipe_id",), "forcings": ("forcing_id",),
                "replay_recipes": ("recipe_id",), "provider_bindings": ("binding_id", "provider_binding_id")}
            field_names = key_fields[bucket]
            by_key = {str(next((row[name] for name in field_names if name in row), "")): row
                      for row in rows}
            missing = keys - by_key.keys()
            if missing:
                raise RecordIntegrityError(
                    f"committed read-view references missing {bucket} records: {sorted(missing)[:3]}")
            rows = [by_key[key] for key in sorted(keys)]
        for row in rows:
            try:
                record = parser(row)
                key = (row.get("record_id") or row.get("state_id") or row.get("checkpoint_id")
                       or row.get("forcing_id") or row.get("recipe_id") or row.get("branch_id"))
                if key is None or identity(record) != str(key):
                    raise ValueError("record key does not match its identity")
                result.append(record)
            except Exception as exc:
                raise RecordIntegrityError(f"{record_type} record failed identity verification") from exc
        return tuple(result)

    def append_state(self, state: DomainStateEnvelope) -> str:
        try:
            self.read_refinement_branch(state.branch_id)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("refinement child states must use append_refinement_transaction")
        self._append_single("states", str(state.state_id), state.to_dict())
        return str(state.state_id)

    def _append_single(self, bucket: str, key: str, body: dict[str, Any]) -> None:
        """Materialize one immutable record and publish it with a view switch."""
        with self._writer_lock():
            parent = self._load_committed_view()
            if bucket == "states":
                branch_id = str(body.get("branch_id", ""))
                if branch_id in parent.records["refinement_branches"]:
                    raise ValueError("refinement child states require branch-bound transaction API")
            self._write(bucket, key, body)
            next_records = {name: set(parent.records[name]) for name in _VIEW_BUCKETS}
            next_records[bucket].add(key)
            next_view_id = self._write_view_manifest(next_records)
            if next_view_id != parent.view_id:
                self._switch_current_view(next_view_id)

    def read_state(self, state_id: str) -> DomainStateEnvelope:
        return self._typed("states", state_id, "state", DomainStateEnvelope.from_dict,
                           lambda row: str(row.state_id))

    def states(self) -> tuple[DomainStateEnvelope, ...]:
        return self._typed_all("states", "state", DomainStateEnvelope.from_dict,
                               lambda row: str(row.state_id))

    def append_provenance(self, record: ProvenanceRecord) -> str:
        self._append_single("provenance", str(record.record_id), record.to_dict())
        return str(record.record_id)

    def read_provenance(self, record_id: str) -> dict[str, Any]:
        return self._typed("provenance", record_id, "provenance",
                           ProvenanceRecord.from_dict, lambda row: str(row.record_id)).to_dict()

    def append_event(self, event: EventRecord) -> str:
        self._append_single("events", event.record_id, event.to_dict())
        return event.record_id

    def read_event(self, event_id: str) -> dict[str, Any]:
        return self._typed("events", event_id, "event", EventRecord.from_dict,
                           lambda row: row.record_id).to_dict()

    def append_checkpoint(self, checkpoint: CheckpointEnvelope) -> str:
        self._append_single("checkpoints", str(checkpoint.checkpoint_id), checkpoint.to_dict())
        return str(checkpoint.checkpoint_id)

    def read_checkpoint(self, checkpoint_id: str) -> dict[str, Any]:
        return self._typed("checkpoints", checkpoint_id, "checkpoint",
                           CheckpointEnvelope.from_dict,
                           lambda row: str(row.checkpoint_id)).to_dict()

    def append_provider_binding(self, binding_id: str, record: dict[str, Any]) -> str:
        if str(ProviderBindingId.from_payload(record)) != binding_id:
            raise RecordIntegrityError("provider binding identity does not match content")
        self._append_single("provider_bindings", binding_id, record)
        return binding_id

    def read_provider_binding(self, binding_id: str) -> dict[str, Any]:
        def parse(row: dict[str, Any]) -> dict[str, Any]:
            if str(ProviderBindingId.from_payload(row)) != binding_id:
                raise ValueError("provider binding identity does not match content")
            return row
        return self._typed("provider_bindings", binding_id, "provider binding",
                           parse, lambda row: str(ProviderBindingId.from_payload(row)))

    def append_temporal(self, record: TemporalRecord) -> str:
        self._append_single("temporal", record.record_id, record.to_dict())
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
        self._append_single("refinement_branches", key, branch.to_dict())
        return key

    def read_refinement_branch(self, branch_id: str) -> RefinementBranchEnvelope:
        return self._typed("refinement_branches", branch_id, "refinement branch",
                           RefinementBranchEnvelope.from_dict,
                           lambda row: str(row.branch_id))

    def refinement_branches(self) -> tuple[RefinementBranchEnvelope, ...]:
        return self._typed_all("refinement_branches", "refinement branch",
                               RefinementBranchEnvelope.from_dict,
                               lambda row: str(row.branch_id))

    def read_refinement_recipe(self, recipe_id: str) -> RefinementReconstructionRecipe:
        return self._typed("refinement_recipes", recipe_id, "refinement recipe",
                           RefinementReconstructionRecipe.from_dict,
                           lambda row: str(row.recipe_id))

    def refinement_recipes(self) -> tuple[RefinementReconstructionRecipe, ...]:
        return self._typed_all("refinement_recipes", "refinement recipe",
                               RefinementReconstructionRecipe.from_dict,
                               lambda row: str(row.recipe_id))

    def append_refinement_recipe(self, recipe: RefinementReconstructionRecipe) -> str:
        key = str(recipe.recipe_id)
        self._append_single("refinement_recipes", key, recipe.to_dict())
        return key

    def append_refinement_transaction(self, branch: RefinementBranchEnvelope,
                                      recipe: RefinementReconstructionRecipe,
                                      child_records: Iterable[Any]) -> tuple[str, ...]:
        """Atomically declare a child branch, its recipe, and branch-local outputs."""
        records = tuple(child_records)
        if str(branch.branch_id) == branch.parent_branch_id:
            raise ValueError("refinement child branch cannot reuse its parent branch ID")
        if branch.base_history_id != branch.history_id:
            raise ValueError("refinement child and base history IDs must match")
        if (recipe.branch_id != str(branch.branch_id) or recipe.history_id != branch.history_id
                or recipe.parent_branch_id != branch.parent_branch_id):
            raise ValueError("refinement recipe scope differs from branch envelope")
        if recipe.boundary_conditions_sha256 != content_hash(thaw_json(branch.parent_boundary_conditions)):
            raise ValueError("refinement recipe boundary identity differs from branch")
        output_ids = tuple(item.state_id for item in recipe.output_manifest)
        if branch.output_state_ids and tuple(branch.output_state_ids) != output_ids:
            raise ValueError("branch output list differs from refinement recipe manifest")
        if recipe.materialization_status != "MATERIALIZED":
            raise ValueError("only verified MATERIALIZED refinement outputs may be published")
        checkpoint = CheckpointEnvelope.from_dict(self.read_checkpoint(recipe.base_checkpoint_id))
        if (checkpoint.history_id, checkpoint.branch_id) != (branch.history_id, branch.parent_branch_id):
            raise ValueError("base checkpoint does not match parent branch/history")
        if checkpoint.validation_status != "VALIDATED":
            raise ValueError("base checkpoint must be validated")
        checkpoint_states = set(checkpoint.restart_state_ids) | set(checkpoint.retained_history_state_ids)
        if not set(recipe.parent_state_ids).issubset(checkpoint_states):
            raise ValueError("parent states must be declared by the base checkpoint")
        parent_records = tuple(self.read_state(state_id) for state_id in recipe.parent_state_ids)
        if any((state.history_id, state.branch_id) !=
               (branch.history_id, branch.parent_branch_id) for state in parent_records):
            raise ValueError("parent state scope differs from refinement branch")
        parent_cells = {cell for state in parent_records for cell in state.spatial_support.cell_ids}
        if not set(recipe.parent_region_cell_ids).issubset(parent_cells):
            raise ValueError("refinement region is outside parent state support")
        child_states = tuple(record for record in records if isinstance(record, DomainStateEnvelope))
        if {str(state.state_id) for state in child_states} != set(output_ids):
            raise ValueError("transaction child states do not equal declared output manifest")
        for state in child_states:
            if (state.history_id, state.branch_id) != (branch.history_id, str(branch.branch_id)):
                raise ValueError("child state is not scoped to the declared refinement branch")
            if state.domain not in branch.requested_domains:
                raise ValueError("child state domain is outside declared refinement domains")
            if state.time_support.time_key not in branch.time_interval:
                raise ValueError("child state time is outside declared refinement interval")
        by_id = {str(state.state_id): state for state in child_states}
        for entry in recipe.output_manifest:
            state = by_id[entry.state_id]
            if tuple(state.spatial_support.cell_ids) != entry.child_cell_ids:
                raise ValueError("child state support differs from output manifest")
            if not set(entry.parent_cell_ids).issubset(recipe.parent_region_cell_ids):
                raise ValueError("child output maps outside declared parent region")
            payload_identity = None if state.payload_reference is None else state.payload_reference.identity
            if payload_identity != entry.payload_identity:
                raise ValueError("child state payload identity differs from output manifest")
        if any(not isinstance(record, (DomainStateEnvelope, ProvenanceRecord, EventRecord))
               for record in records):
            raise TypeError("refinement bundle accepts child states, provenance, and events only")
        # All new child states in this atomic bundle must pass the branch-bound API.
        return self.append_transaction((branch, recipe, *records),
                                       _refinement_branch_id=str(branch.branch_id))

    def append_forcing(self, forcing: ForcingRecord) -> str:
        key = str(forcing.forcing_id)
        self._append_single("forcings", key, forcing.to_dict())
        return key

    def read_forcing(self, forcing_id: str) -> dict[str, Any]:
        return self._typed("forcings", forcing_id, "forcing", ForcingRecord.from_dict,
                           lambda row: str(row.forcing_id)).to_dict()

    def forcings(self) -> tuple[ForcingRecord, ...]:
        return self._typed_all("forcings", "forcing", ForcingRecord.from_dict,
                               lambda row: str(row.forcing_id))

    def append_replay_recipe(self, recipe: ReplayRecipe) -> str:
        key = str(recipe.recipe_id)
        self._append_single("replay_recipes", key, recipe.to_dict())
        return key

    def read_replay_recipe(self, recipe_id: str) -> ReplayRecipe:
        return self._typed("replay_recipes", recipe_id, "replay recipe",
                           ReplayRecipe.from_dict, lambda row: str(row.recipe_id))

    def replay_recipes(self) -> tuple[ReplayRecipe, ...]:
        return self._typed_all("replay_recipes", "replay recipe", ReplayRecipe.from_dict,
                               lambda row: str(row.recipe_id))

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
