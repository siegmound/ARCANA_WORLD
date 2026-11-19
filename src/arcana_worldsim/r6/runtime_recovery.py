"""REC1 noncanonical R2 controller using B0's sole atomic visibility pointer.

Immutable blobs are in this run's root; eligibility comes only from typed B0
records in a committed read-view. Orphans never become restart authority.
Native solver checkpoints and payloads retain their original formats.
"""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

from . import int10k_runtime_compact as c
from .checkpoint import CheckpointEnvelope
from .identity import HistoryId, BranchId, content_hash, thaw_json
from .state import DomainStateEnvelope, TimeSupport, SpatialSupport, SupportClass, AuthorityClass
from .store import HistoryStore
from .int10k_history_independent import verify_history_independent_checkpoint
from .geological_surface_microdomain import SUPPORTS

DOMAIN = "R2_REC1_COUPLED_RESTART_DESCRIPTOR"
SCHEMA = "ARCANA_R6_REC1_COMMITTED_PAIR_V1"


class RecoveryError(ValueError):
    pass


def require(value, message):
    if not value:
        raise RecoveryError(message)


def file_sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


class _Journal:
    def __init__(self, root):
        self.root = root
        self.sequence = 0
        self.first = 0
        self.head = self.initial = None
        self.pending = []
        self.encode_write_s = 0.0
        self._open()

    def _open(self):
        self.path = self.root / "active" / (uuid.uuid4().hex + ".jsonl")
        self.stream = self.path.open("xb", buffering=1024*1024)
        self.counts = Counter()

    def bind(self, head):
        self.head = self.initial = head
        for kind, payload in self.pending:
            self.emit(kind, payload)
        self.pending.clear()

    def emit(self, kind, payload):
        started = time.perf_counter()
        if self.head is None:
            self.pending.append((kind, c._copy(payload)))
            return
        body = {"schema": c.STREAM_SCHEMA, "sequence": self.sequence,
                "parent_sha256": self.head, "kind": kind, "payload": payload}
        self.head = c._sha(body)
        self.stream.write(c.regional._canonical({**body, "sha256": self.head}) + b"\n")
        self.sequence += 1
        self.counts[kind] += 1
        self.encode_write_s += time.perf_counter() - started

    def flush(self):
        self.stream.flush()
        os.fsync(self.stream.fileno())

    def rotate(self):
        self.stream.close()
        self.path.unlink()  # only this run's staged hard link, after B0 visibility
        HistoryStore._fsync_directory(self.path.parent)
        self.first = self.sequence
        self.initial = self.head
        self._open()

    def close(self):
        if not self.stream.closed:
            self.flush()
            self.stream.close()


class RecoveryController:
    def __init__(self, root, initial_states, source_identity, *, config, run_id,
                 run_plan=None, fault=None):
        self.root = Path(root)
        for name in ("chunks", "frontiers", "active"):
            (self.root/name).mkdir(parents=True, exist_ok=True)
        self.initial = {s: c.unified._state_from_payload(c._copy(v.payload())) for s, v in initial_states.items()}
        self.source = c._copy(dict(source_identity))
        self.config, self.plan, self.fault = config, run_plan, fault
        self.plan_record = run_plan.to_dict() if run_plan else None
        self.run_id = run_id
        self.history_id = str(HistoryId.from_payload({"rec1_run": run_id}))
        self.branch_id = str(BranchId.from_payload({"rec1_history": self.history_id}))
        self.runtime_identity = {"adapter": SCHEMA, "sources": {
            path.name: file_sha(path) for path in sorted(Path(__file__).parent.glob("*.py"))}}
        template = c.CompactRuntime(self.initial, self.source, config=config,
                                   runtime_compact_history=True, run_plan=run_plan)
        self.configuration = template.configuration
        self.store = HistoryStore(self.root/"b0", _fault_injector=self._fault)
        self.runtime = self.writer = None
        self.last_id = None
        self.last_native = None
        self.global_count = 0
        self.failed = False
        self.metrics = []
        with self.store.read_view() as view:
            self.parent_view = view.view_id

    def _fault(self, stage, count=0):
        if self.fault:
            self.fault(stage, count)

    def _new_runtime(self, checkpoint=None):
        self.writer = _Journal(self.root)
        self.runtime = c.CompactRuntime(self.initial, self.source, config=self.config,
            runtime_compact_history=True, checkpoint=checkpoint, consumer=self.writer.emit,
            run_plan=self.plan)
        self.writer.bind(self.runtime.initial_head)
        require(self.writer.head == self.runtime.head, "JOURNAL_INITIAL_HEAD_MISMATCH")

    def start(self):
        require(self.recover() is None, "RUN_ALREADY_COMMITTED_USE_RECOVER")
        self._new_runtime()
        return self

    def advance(self, years=1):
        require(not self.failed and self.runtime is not None, "CONTROLLER_REQUIRES_RECOVERY")
        try:
            result = self.runtime.advance(years)
            require(self.writer.head == self.runtime.head, "JOURNAL_RUNTIME_HEAD_MISMATCH")
            return result
        except BaseException:
            self.failed = True
            raise

    def _install(self, staged, bucket, digest):
        target = self.root/bucket/(digest + (".jsonl" if bucket == "chunks" else ".json"))
        try:
            os.link(staged, target)
        except FileExistsError:
            require(file_sha(target) == digest, "IMMUTABLE_BLOB_CONFLICT")
        HistoryStore._fsync_directory(target.parent)
        return target

    def _blob(self, bucket, digest):
        require(isinstance(digest, str) and len(digest) == 64 and all(x in "0123456789abcdef" for x in digest),
                "BLOB_DIGEST_INVALID")
        path = self.root/bucket/(digest + (".jsonl" if bucket == "chunks" else ".json"))
        require(path.is_file() and not path.is_symlink() and file_sha(path) == digest,
                "COMMITTED_BLOB_MISSING_OR_CORRUPT")
        return path

    def _rows(self, descriptor):
        path = self._blob("chunks", descriptor["chunk_sha256"])
        require(path.stat().st_size == descriptor["byte_length"], "CHUNK_LENGTH_MISMATCH")
        previous = descriptor["initial_head"]
        counts = Counter()
        count = 0
        try:
            with path.open("rb") as stream:
                for line in stream:
                    entry = json.loads(line)
                    require(set(entry) == {"schema", "sequence", "parent_sha256", "kind", "payload", "sha256"},
                            "CHUNK_FIELDS_INVALID")
                    require(entry["schema"] == c.STREAM_SCHEMA
                            and entry["sequence"] == descriptor["local_first"] + count
                            and entry["parent_sha256"] == previous, "CHUNK_SEQUENCE_OR_PARENT_MISMATCH")
                    require(c._sha({k: v for k, v in entry.items() if k != "sha256"}) == entry["sha256"],
                            "CHUNK_RECORD_DIGEST_MISMATCH")
                    previous = entry["sha256"]
                    count += 1
                    counts[entry["kind"]] += 1
                    yield entry["kind"], entry["payload"]
        except (ValueError, TypeError, KeyError) as exc:
            raise RecoveryError("COMMITTED_CHUNK_INVALID") from exc
        require(count == descriptor["records"] and dict(counts) == descriptor["counts"]
                and previous == descriptor["head"]
                and descriptor["local_last"] == descriptor["local_first"] + count - 1,
                "CHUNK_HIGH_WATER_MISMATCH")

    def _validate_pair(self, descriptor, native, parent_native):
        verify_history_independent_checkpoint(native, source_identity=self.source, configuration=self.configuration)
        require(native["time_year"] == descriptor["end_year"]
                and native["history_high_water_mark"] == descriptor["end_year"], "COUPLED_CLOCK_MISMATCH")
        state = None if parent_native is None else c._copy({"time_year": parent_native["time_year"],
            "cells": parent_native["regional_checkpoint"]["regional_state"]["cells"]})
        unified_year = descriptor["start_year"]
        regional_year = descriptor["start_year"]
        last_unified = None
        for kind, payload in self._rows(descriptor):
            if kind == "REGIONAL_SNAPSHOT":
                require(state is None and payload["time_year"] == 0, "UNEXPECTED_ROOT_SNAPSHOT")
                state = payload
            elif kind == "UNIFIED_STEP":
                require(payload["step"] == unified_year + 1, "UNIFIED_SEQUENCE_MISMATCH")
                unified_year += 1
                last_unified = payload
            elif kind == "REGIONAL_YEAR_RECORD":
                require(payload["time_year"] == regional_year + 1 == unified_year, "REGIONAL_SEQUENCE_MISMATCH")
                regional_year += 1
                for key, tolerance in (("water_balance_m3", "roundoff_tolerance"),
                                       ("solid_mass_balance_kg", "roundoff_tolerance_kg")):
                    require(abs(payload[key]["residual"]) <= payload[key][tolerance], "PHYSICAL_BALANCE_INVALID")
            elif kind == "REGIONAL_DELTA":
                require(state is not None and payload["year"] == regional_year, "DELTA_CLOCK_MISMATCH")
                require(payload["schema"] == c.FRAME_SCHEMA and payload["canonical_sha_status"] ==
                        "DEFERRED_UNTIL_MATERIALIZATION" and payload["target_snapshot_sha256"] is None
                        and payload["parent_snapshot_sha256"] is None, "DELTA_HASH_SEMANTICS_INVALID")
                state = c._apply_owned(state, payload)
            else:
                require(kind == "REGIONAL_EVENT", "UNKNOWN_COMPACT_KIND")
        require(state is not None and last_unified is not None
                and state["time_year"] == unified_year == regional_year == descriptor["end_year"],
                "INCOMPLETE_COUPLED_HISTORY")
        region = native["regional_checkpoint"]["regional_state"]
        saved = native["regional_checkpoint"]["unified_checkpoint"]["state"]
        require(c._sha(state["cells"]) == c._sha(region["cells"]), "CHECKPOINT_HISTORY_PHYSICAL_MISMATCH")
        for support, payload in saved["thermal_states_by_support"].items():
            require(c.unified._state_digest(c.unified._state_from_payload(payload)) ==
                    last_unified["thermal"][support]["state_sha256"], "THERMAL_FRONTIER_MISMATCH")
        for volume, stock in zip(saved["deep_volume_ids"], saved["deep_inventory_j_by_support"]):
            require(stock == last_unified["deep"]["inventory_j_by_material_volume"][volume], "DEEP_FRONTIER_MISMATCH")
        require(saved["total_strain_history"] == last_unified["mechanics"]["total_strain_by_material_volume"]
                if "total_strain_history" in saved else
                saved["total_strain"] == last_unified["mechanics"]["total_strain_by_material_volume"],
                "MECHANICAL_FRONTIER_MISMATCH")
        require(saved["viscous_strain"] == last_unified["mechanics"]["viscous_strain_by_material_volume"],
                "VISCOUS_FRONTIER_MISMATCH")

    def commit(self):
        require(not self.failed and self.runtime is not None, "CONTROLLER_REQUIRES_RECOVERY")
        require(self.writer.sequence > self.writer.first, "NO_NEW_RECORDS_TO_COMMIT")
        metrics = {}
        started = time.perf_counter()
        try:
            self._fault("before_journal_fsync")
            tick = time.perf_counter(); self.writer.flush()
            chunk_sha = file_sha(self.writer.path)
            self._install(self.writer.path, "chunks", chunk_sha)
            metrics["journal_seal_fsync_s"] = time.perf_counter() - tick
            self._fault("after_journal_fsync")
            self._fault("before_checkpoint_seal")
            tick = time.perf_counter(); native = self.runtime.checkpoint()
            encoded = c.regional._canonical(native); native_sha = hashlib.sha256(encoded).hexdigest()
            staged = self.root/"active"/(uuid.uuid4().hex + ".json")
            with staged.open("xb") as stream:
                stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
            self._install(staged, "frontiers", native_sha)
            metrics["checkpoint_seal_persist_s"] = time.perf_counter() - tick
            self._fault("after_checkpoint_persistence")
            n = self.writer.sequence - self.writer.first
            descriptor = {"schema": SCHEMA, "run_id": self.run_id, "plan": self.plan_record,
                "source_sha256": c._sha(self.source), "configuration_sha256": c._sha(self.configuration),
                "start_year": self.last_native["time_year"] if self.last_native else 0,
                "end_year": native["time_year"], "regional_clock": native["time_year"],
                "unified_clock": native["regional_checkpoint"]["unified_checkpoint"]["state"]["elapsed_external_steps"],
                "parent_checkpoint_id": self.last_id, "first_global_sequence": self.global_count,
                "last_global_sequence": self.global_count + n - 1,
                "local_first": self.writer.first, "local_last": self.writer.sequence - 1,
                "records": n, "byte_length": self.writer.path.stat().st_size,
                "counts": dict(self.writer.counts), "initial_head": self.writer.initial,
                "head": self.writer.head, "chunk_sha256": chunk_sha, "native_sha256": native_sha}
            tick = time.perf_counter(); self._validate_pair(descriptor, native, self.last_native)
            metrics["pair_validation_s"] = time.perf_counter() - tick
            state = DomainStateEnvelope.create(history_id=self.history_id, branch_id=self.branch_id,
                domain=DOMAIN, time_support=TimeSupport(f"YEAR_{native['time_year']}", "SYNTHETIC_MODEL_YEARS"),
                spatial_support=SpatialSupport("REC1_SYNTHETIC_3X3", SUPPORTS),
                support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
                value=descriptor, parent_state_ids=())
            envelope = CheckpointEnvelope.create(history_id=self.history_id, branch_id=self.branch_id,
                time_key=state.time_support.time_key, restart_state_ids=(str(state.state_id),),
                retained_history_state_ids=(str(state.state_id),), runtime_identity=self.runtime_identity,
                configuration=self.configuration, seed_lineage={"mode": "DETERMINISTIC_SELECTED_OPERATORS"},
                parent_checkpoint_id=self.last_id,
                restart_compatibility={"native_schema": native["schema"], "adapter": SCHEMA},
                output_manifest={"descriptor_id": str(state.state_id), "descriptor_sha256": content_hash(descriptor)})
            tick = time.perf_counter()
            self.store.append_transaction((state, envelope), expected_parent_view_id=self.parent_view)
            metrics["b0_atomic_publication_s"] = time.perf_counter() - tick
            self.last_id, self.last_native = str(envelope.checkpoint_id), native
            self.global_count += n
            with self.store.read_view() as view:
                self.parent_view = view.view_id
            self._fault("during_adapter_cleanup")
            staged.unlink(); self.writer.rotate()
            self._fault("after_adapter_cleanup")
        except BaseException:
            self.failed = True
            raise
        metrics["total_commit_s"] = time.perf_counter() - started
        metrics["year"] = native["time_year"]
        self.metrics.append(metrics)
        return self.last_id

    def _load_chain(self):
        with self.store.read_view() as view:
            candidates = {str(x.checkpoint_id): x for x in self.store.checkpoints()
                          if x.history_id == self.history_id and x.branch_id == self.branch_id}
            if not candidates:
                return [], view.view_id
            leaves = set(candidates) - {x.parent_checkpoint_id for x in candidates.values()}
            require(len(leaves) == 1, "AMBIGUOUS_COMMITTED_LINEAGE")
            chain = []; key = next(iter(leaves)); seen = set()
            while key is not None:
                require(key not in seen and key in candidates, "BROKEN_COMMITTED_LINEAGE")
                seen.add(key); cp = candidates[key]
                require(dict(cp.runtime_identity) == self.runtime_identity
                        and cp.configuration_sha256 == content_hash(self.configuration), "RECOVERY_SOURCE_OR_CONFIG_MISMATCH")
                require(len(cp.restart_state_ids) == 1, "RECOVERY_DESCRIPTOR_INVALID")
                state = self.store.read_state(cp.restart_state_ids[0])
                d = thaw_json(state.value)
                require(state.domain == DOMAIN and state.history_id == self.history_id
                        and state.branch_id == self.branch_id and d["schema"] == SCHEMA
                        and d["source_sha256"] == c._sha(self.source)
                        and d["configuration_sha256"] == c._sha(self.configuration)
                        and d["plan"] == self.plan_record and d["run_id"] == self.run_id,
                        "RECOVERY_DESCRIPTOR_CONTEXT_MISMATCH")
                require(thaw_json(cp.output_manifest) == {"descriptor_id": str(state.state_id),
                        "descriptor_sha256": content_hash(d)} and d["parent_checkpoint_id"] == cp.parent_checkpoint_id,
                        "CHECKPOINT_DESCRIPTOR_BINDING_MISMATCH")
                native = json.loads(self._blob("frontiers", d["native_sha256"]).read_bytes())
                chain.append((cp, d, native)); key = cp.parent_checkpoint_id
            require(len(seen) == len(candidates), "DISCONNECTED_COMMITTED_HISTORY")
            chain.reverse(); previous = None; global_count = 0
            for cp, d, native in chain:
                require(d["start_year"] == (previous["time_year"] if previous else 0)
                        and d["first_global_sequence"] == global_count
                        and d["last_global_sequence"] == global_count + d["records"] - 1
                        and d["regional_clock"] == d["unified_clock"] == d["end_year"],
                        "COMMITTED_HIGH_WATER_MISMATCH")
                self._validate_pair(d, native, previous)
                previous = native; global_count += d["records"]
            return chain, view.view_id

    def recover(self):
        try:
            chain, view = self._load_chain()
        except Exception as exc:
            raise RecoveryError("COMMITTED_RECOVERY_INVALID: " + str(exc)) from exc
        self.close()
        self.parent_view = view; self.failed = False
        if not chain:
            self.last_id = self.last_native = None; self.global_count = 0
            return None
        cp, d, native = chain[-1]
        self.last_id = str(cp.checkpoint_id); self.last_native = native
        self.global_count = d["last_global_sequence"] + 1
        self._new_runtime(native)
        return {"time_year": native["time_year"], "checkpoint_id": self.last_id,
                "committed_records": self.global_count, "view_id": view}

    def native_checkpoint(self):
        return c._copy(self.last_native)

    def history(self):
        chain, _ = self._load_chain()
        snapshot = None
        for _, d, _ in chain:
            for kind, payload in self._rows(d):
                if kind == "REGIONAL_SNAPSHOT":
                    snapshot = payload
                    payload = c._copy(snapshot)
                elif kind == "REGIONAL_DELTA":
                    snapshot = c._apply_owned(snapshot, payload)
                    kind, payload = "REGIONAL_SNAPSHOT", c._copy(snapshot)
                yield kind, payload

    def close(self):
        if self.writer is not None:
            self.writer.close()
