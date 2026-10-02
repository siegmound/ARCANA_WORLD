"""Replaceable append-only JSON record store for R6 Wave 1."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, TypeVar
import json
import os
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

    def __init__(self, root: str | Path):
        self.__root = Path(root)
        self.__root.mkdir(parents=True, exist_ok=True)
        self._initialize_or_validate_manifest()

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
            except FileExistsError:
                if target.read_bytes() != data:
                    raise ImmutableRecordConflict(f"concurrent immutable record conflict: {key}")
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

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
