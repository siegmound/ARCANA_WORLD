"""Replaceable append-only JSON record store for R6 Wave 1."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import json
import os
import tempfile

from .checkpoint import CheckpointEnvelope
from .identity import canonical_bytes
from .provenance import ProvenanceIntegrityError, ProvenanceRecord
from .state import DomainStateEnvelope
from .temporal import EventRecord, TemporalRecord


class ImmutableRecordConflict(ValueError):
    pass


class HistoryStore:
    """File-backed reference store; identity and query APIs expose no path details."""

    SCHEMA = "ARCANA_R6_FILE_HISTORY_STORE_V0"

    def __init__(self, root: str | Path):
        self.__root = Path(root)
        self.__root.mkdir(parents=True, exist_ok=True)

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
        return json.loads(path.read_text(encoding="utf-8"))

    def _all(self, bucket: str) -> list[dict[str, Any]]:
        directory = self.__root / bucket
        if not directory.exists():
            return []
        return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(directory.glob("*.json"))]

    def append_state(self, state: DomainStateEnvelope) -> str:
        self._write("states", str(state.state_id), state.to_dict())
        return str(state.state_id)

    def read_state(self, state_id: str) -> DomainStateEnvelope:
        return DomainStateEnvelope.from_dict(self._read("states", state_id))

    def states(self) -> tuple[DomainStateEnvelope, ...]:
        return tuple(DomainStateEnvelope.from_dict(row) for row in self._all("states"))

    def append_provenance(self, record: ProvenanceRecord) -> str:
        self._write("provenance", str(record.record_id), record.to_dict())
        return str(record.record_id)

    def read_provenance(self, record_id: str) -> dict[str, Any]:
        return self._read("provenance", record_id)

    def append_event(self, event: EventRecord) -> str:
        self._write("events", event.record_id, event.to_dict())
        return event.record_id

    def read_event(self, event_id: str) -> dict[str, Any]:
        return self._read("events", event_id)

    def append_checkpoint(self, checkpoint: CheckpointEnvelope) -> str:
        self._write("checkpoints", str(checkpoint.checkpoint_id), checkpoint.to_dict())
        return str(checkpoint.checkpoint_id)

    def read_checkpoint(self, checkpoint_id: str) -> dict[str, Any]:
        return CheckpointEnvelope.from_dict(self._read("checkpoints", checkpoint_id)).to_dict()

    def append_provider_binding(self, binding_id: str, record: dict[str, Any]) -> str:
        self._write("provider_bindings", binding_id, record)
        return binding_id

    def read_provider_binding(self, binding_id: str) -> dict[str, Any]:
        return self._read("provider_bindings", binding_id)

    def append_temporal(self, record: TemporalRecord) -> str:
        self._write("temporal", record.record_id, record.to_dict())
        return record.record_id

    def read_temporal(self, record_id: str) -> dict[str, Any]:
        return self._read("temporal", record_id)

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
            if row.get("record_id") != record_id:
                raise ProvenanceIntegrityError(f"provenance key/content mismatch: {record_id}")
            records.append(row)
            sources.update(str(x) for x in row.get("source_refs", []))
            for parent in row.get("parent_provenance_ids", []):
                visit(str(parent))

        for provenance_id in state.provenance_ids:
            visit(provenance_id)
        return {"state_id": str(state.state_id), "provenance_records": records,
                "source_refs": sorted(sources)}
