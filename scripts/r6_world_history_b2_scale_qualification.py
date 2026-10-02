#!/usr/bin/env python3
"""Synthetic, path-independent B2 WORLD_HISTORY scale qualification.

This is a qualification utility, not a production runner. It generates only
FIXTURE_ONLY values and writes all transient stores beneath --work-root.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import struct
import sys
import tempfile
import time
import tracemalloc
import zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.checkpoint import CheckpointEnvelope, RefinementBranchEnvelope
from arcana_worldsim.r6.forcing import ForcingRecord
from arcana_worldsim.r6.identity import (BranchId, HistoryId, PayloadIdentity,
    canonical_bytes, content_hash, verify_payload, PayloadIntegrityError)
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.query import HistoryQueryService, DifferenceStatus
from arcana_worldsim.r6.replay import ReplayExecutionOutput, ReplayRecipe, execute_replay
from arcana_worldsim.r6.refinement import (RefinementExecutionOutput,
    RefinementOutputManifestEntry, RefinementReconstructionRecipe, execute_refinement)
from arcana_worldsim.r6.state import (AuthorityClass, DomainStateEnvelope, SpatialSupport,
    SupportClass, TimeSupport)
from arcana_worldsim.r6.storage import (AccountingRoot, AccountingScope, StorageCategory,
    account_storage, history_store_scope, CANONICAL_HARD_CAP_BYTES)
from arcana_worldsim.r6.store import HistoryStore
from arcana_worldsim.r6.temporal import EventRecord

NODES = 64_442
TRIANGLES = 128_880
HISTORY = str(HistoryId.from_payload({"qualification": "B2_SYNTHETIC_SCALE_V1"}))
BRANCH = str(BranchId.from_payload({"qualification": "B2_SYNTHETIC_PARENT_V1"}))
T0 = TimeSupport("fixture:t0", "fixture-clock", "SNAPSHOT")
T1 = TimeSupport("fixture:t1", "fixture-clock", "SNAPSHOT")
RUNTIME = {"adapter": "B2-fixture-arithmetic-v1", "version": 1}
SEED = {"seed": 20261002}
CONFIG = {"operation": "fixture-value-plus-forcing", "version": 1}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _deterministic_npz(arrays: dict[str, np.ndarray]) -> bytes:
    """NPZ with stable member order/timestamps and no pickle/object arrays."""
    import io
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in sorted(arrays):
            item = io.BytesIO()
            np.lib.format.write_array(item, np.ascontiguousarray(arrays[name]), allow_pickle=False)
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o600 << 16
            archive.writestr(info, item.getvalue())
    return result.getvalue()


def _dataset(n: int, include_topology: bool) -> dict[str, np.ndarray]:
    i = np.arange(n, dtype=np.uint32)
    # Synthetic deterministic positions and values; no source mesh/value is read.
    x = (i.astype(np.float64) * 0.125) % 360.0
    y = ((i.astype(np.float64) * 0.6180339887498948) % 180.0) - 90.0
    value = (i.astype(np.float64) % 997.0) / 997.0
    arrays = {
        "node_id": i,
        "synthetic_x": x,
        "synthetic_y": y,
        "ordinary_field": value,
        "future_memory": np.full(n, 0.25, dtype=np.float64),
        "known_zero": np.zeros(n, dtype=np.float64),
        "known_boolean": (i % 2 == 0),
        "unknown_support": (i % 11 == 0),
        "forcing_input": np.full(n, 0.01, dtype=np.float64),
    }
    if include_topology:
        tri = np.arange(TRIANGLES * 3, dtype=np.uint64).reshape(TRIANGLES, 3) % n
        arrays["synthetic_triangles"] = tri.astype(np.uint32)
    return arrays


def _state(domain: str, support: SpatialSupport, value, *, payload_ref: str | None,
           provenance: str, time_support: TimeSupport = T0, parents=(), events=()):
    unsupported = domain == "fixture-unknown"
    return DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=BRANCH, domain=domain,
        time_support=time_support, spatial_support=support,
        support_class=SupportClass.UNKNOWN if unsupported else SupportClass.FIXTURE_ONLY,
        authority_class=AuthorityClass.NONE if unsupported else AuthorityClass.FIXTURE_ONLY,
        value=None if unsupported else value,
        uncertainty={"fixture_only": True}, provenance_ids=(provenance,),
        parent_state_ids=tuple(parents), payload_ref=payload_ref, event_refs=tuple(events))


def _replay_runner(recipe, inputs):
    base = inputs.base_states[0]
    result_value = int(base.value) + int(inputs.forcings[0].value)
    payload = canonical_bytes({"fixture_result": result_value})
    identity = PayloadIdentity.from_bytes(payload)
    state = DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=BRANCH, domain="fixture-main-output",
        time_support=T1, spatial_support=base.spatial_support,
        support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
        value=result_value, uncertainty={"fixture_only": True},
        provenance_ids=recipe.provenance_ids,
        parent_state_ids=(str(base.state_id),), payload_ref=f"sha256:{identity.digest}",
        event_refs=recipe.event_ids)
    return ReplayExecutionOutput(state, payload)


def _refinement_runner(inputs):
    parent = inputs.parent_states[0]
    output = []
    for entry in inputs.recipe.output_manifest:
        value = int(parent.value) + len(entry.child_cell_ids)
        payload = canonical_bytes({"fixture_child": entry.child_cell_ids[0], "value": value})
        identity = PayloadIdentity.from_bytes(payload)
        state = DomainStateEnvelope.create(
            history_id=HISTORY, branch_id=str(inputs.branch.branch_id),
            domain="fixture-refined", time_support=T0,
            spatial_support=SpatialSupport("fixture-child-grid", entry.child_cell_ids,
                                           "bounded-sample", "CELL_SET"),
            support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
            value=value, uncertainty={"fixture_only": True},
            provenance_ids=parent.provenance_ids,
            parent_state_ids=(str(parent.state_id),), payload_ref=f"sha256:{identity.digest}",
            refinement_lineage={"parent_cell_ids": list(entry.parent_cell_ids),
                                "child_branch": str(inputs.branch.branch_id)})
        output.append(RefinementExecutionOutput(state, payload))
    return tuple(output)


def _timed(call, repetitions=1):
    samples = []
    result = None
    for _ in range(repetitions):
        start = time.perf_counter()
        result = call()
        samples.append(time.perf_counter() - start)
    ordered = sorted(samples)
    return result, {"operations": repetitions, "total_seconds": sum(samples),
        "median_seconds": statistics.median(samples),
        "p95_seconds": ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))],
        "max_seconds": max(samples)}


def _serialize_payload(n: int, include_topology: bool):
    start = time.perf_counter()
    arrays = _dataset(n, include_topology)
    generation = time.perf_counter() - start
    start = time.perf_counter()
    raw = _deterministic_npz(arrays)
    serialization = time.perf_counter() - start
    return arrays, raw, {"generation_seconds": generation,
                         "serialization_seconds": serialization}


def _record_counts(root: Path):
    return {name: len(tuple((root / name).glob("*.json")))
            for name in ("states", "provenance", "events", "checkpoints", "forcings",
                         "replay_recipes", "refinement_branches", "refinement_recipes")}


def _build_store(root: Path, payload_path: Path, payload_ref: str, *, reverse_insertion=False):
    init_start = time.perf_counter()
    store = HistoryStore(root)
    initialization_seconds = time.perf_counter() - init_start
    support = SpatialSupport("b2-synthetic-grid-64442", (), "64442 synthetic nodes", "GRID")
    provenance = ProvenanceRecord.create(activity="B2_SYNTHETIC_FIXTURE_BUILD",
        source_refs=("fixture:B2_SYNTHETIC_V1",),
        attributes={"scope": "FIXTURE_ONLY", "node_count": NODES, "no_scientific_authority": True})
    base = _state("fixture-main", support, 7, payload_ref=payload_ref,
                  provenance=str(provenance.record_id))
    sample_cells = tuple(f"node-{i:06d}" for i in range(256))
    sample_support = SpatialSupport("b2-synthetic-grid-64442", sample_cells,
                                    "bounded-256-node-sample", "CELL_SET")
    ref_parent = _state("fixture-refinement-parent", sample_support, 7,
                        payload_ref=payload_ref, provenance=str(provenance.record_id))
    base2 = _state("fixture-main", support, 8, payload_ref=payload_ref,
                   provenance=str(provenance.record_id), time_support=T1,
                   parents=(str(base.state_id),))
    zero = _state("fixture-known-zero", support, 0, payload_ref=payload_ref,
                  provenance=str(provenance.record_id))
    flag = _state("fixture-known-boolean", support, False, payload_ref=payload_ref,
                  provenance=str(provenance.record_id))
    unknown = _state("fixture-unknown", support, None, payload_ref=None,
                     provenance=str(provenance.record_id))
    event = EventRecord.create(history_id=HISTORY, branch_id=BRANCH, time_key=T0.time_key,
        domain_ids=("fixture-main",), state_ids=(str(base.state_id),),
        provenance_refs=(str(provenance.record_id),), details={"scope": "FIXTURE_ONLY"})
    forcing = ForcingRecord.create(history_id=HISTORY, branch_id=BRANCH,
        forcing_kind="fixture-increment", domain="fixture-main", time_support=T0,
        spatial_support=support, support_class=SupportClass.FIXTURE_ONLY,
        authority_class=AuthorityClass.FIXTURE_ONLY, value=3,
        provenance_ids=(str(provenance.record_id),), source_refs=("fixture:constant-increment",))
    checkpoint = CheckpointEnvelope.create(history_id=HISTORY, branch_id=BRANCH,
        time_key=T0.time_key, restart_state_ids=(str(base.state_id),),
        retained_history_state_ids=tuple(sorted(str(s.state_id) for s in
            (base, ref_parent, zero, flag))),
        runtime_identity=RUNTIME, configuration=CONFIG, seed_lineage=SEED,
        upstream_dependency_ids=(str(provenance.record_id),))
    out_payload = canonical_bytes({"fixture_result": 10})
    out_identity = PayloadIdentity.from_bytes(out_payload)
    expected = _state("fixture-main-output", support, 10,
        payload_ref=f"sha256:{out_identity.digest}", provenance=str(provenance.record_id),
        time_support=T1, parents=(str(base.state_id),), events=(event.record_id,))
    recipe = ReplayRecipe.create(history_id=HISTORY, branch_id=BRANCH,
        base_checkpoint_id=str(checkpoint.checkpoint_id), runtime_identity=RUNTIME,
        configuration_sha256=content_hash(CONFIG), seed_lineage=SEED,
        forcing_ids=(str(forcing.forcing_id),), event_ids=(event.record_id,),
        upstream_dependency_ids=(str(provenance.record_id),),
        provenance_ids=(str(provenance.record_id),),
        expected_output_state_id=str(expected.state_id), expected_payload_identity=out_identity,
        model_adapter_id="fixture:B2-arithmetic-v1")
    transaction_start = time.perf_counter()
    records = (base, ref_parent, base2, zero, flag, unknown, provenance, event,
               forcing, checkpoint, expected, recipe)
    store.append_transaction(tuple(reversed(records)) if reverse_insertion else records)
    transaction_seconds = time.perf_counter() - transaction_start
    pre_ids = sorted(str(s.state_id) for s in store.states())
    del store
    reopen_start = time.perf_counter()
    reopened = HistoryStore(root)
    reopened_seconds = time.perf_counter() - reopen_start
    # Typed reads prove records survive close/reopen.
    for record in (base, base2, zero, flag, unknown, expected):
        assert reopened.read_state(str(record.state_id)).to_dict() == record.to_dict()
    assert reopened.read_forcing(str(forcing.forcing_id))["forcing_id"] == str(forcing.forcing_id)
    assert reopened.read_checkpoint(str(checkpoint.checkpoint_id))["checkpoint_id"] == str(checkpoint.checkpoint_id)
    assert reopened.read_replay_recipe(str(recipe.recipe_id)).recipe_id == recipe.recipe_id
    return reopened, {"support": support, "provenance": provenance, "base": base,
        "base2": base2, "ref_parent": ref_parent, "zero": zero, "flag": flag, "unknown": unknown,
        "event": event, "forcing": forcing, "checkpoint": checkpoint,
        "expected": expected, "recipe": recipe, "output_payload": out_payload,
        "record_ids": sorted(pre_ids + [str(provenance.record_id), event.record_id,
            str(forcing.forcing_id), str(checkpoint.checkpoint_id), str(recipe.recipe_id)]),
        "transaction_seconds": transaction_seconds,
        "reopen_seconds": reopened_seconds,
        "initialization_seconds": initialization_seconds}


def _refine(store: HistoryStore, bundle):
    parent, provenance, checkpoint = bundle["ref_parent"], bundle["provenance"], bundle["checkpoint"]
    branch = RefinementBranchEnvelope.create(history_id=HISTORY,
        parent_branch_id=BRANCH, base_history_id=HISTORY,
        refinement_anchor_id="fixture:B2-anchor", region_id="fixture:sample-region",
        time_interval=(T0.time_key, T0.time_key), requested_domains=("fixture-refined",),
        requested_resolution="fixture-subset-256",
        parent_boundary_conditions={"fixture_only": True, "sample_size": 256},
        provenance_refs=(str(provenance.record_id),))
    parent_cells = parent.spatial_support.cell_ids
    child_sets = tuple((f"child-{i:03d}-a", f"child-{i:03d}-b") for i in range(4))
    manifest = tuple(RefinementOutputManifestEntry(
        state_id="placeholder", parent_cell_ids=(parent_cells[i],), child_cell_ids=children,
        payload_identity=PayloadIdentity.from_bytes(canonical_bytes(
            {"fixture_child": children[0], "value": int(parent.value) + len(children)})))
        for i, children in zip((0, 64, 128, 192), child_sets))
    # State IDs are part of manifests, so form exactly the same states as runner.
    from arcana_worldsim.r6.refinement import RefinementOutputManifestEntry as ManifestEntry
    entries = []
    for entry in manifest:
        value = int(parent.value) + len(entry.child_cell_ids)
        identity = PayloadIdentity.from_bytes(canonical_bytes(
            {"fixture_child": entry.child_cell_ids[0], "value": value}))
        state = DomainStateEnvelope.create(history_id=HISTORY,
            branch_id=str(branch.branch_id), domain="fixture-refined", time_support=T0,
            spatial_support=SpatialSupport("fixture-child-grid", entry.child_cell_ids,
                                           "bounded-sample", "CELL_SET"),
            support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
            value=value, uncertainty={"fixture_only": True},
            provenance_ids=(str(provenance.record_id),), parent_state_ids=(str(parent.state_id),),
            payload_ref=f"sha256:{identity.digest}",
            refinement_lineage={"parent_cell_ids": list(entry.parent_cell_ids),
                                "child_branch": str(branch.branch_id)})
        entries.append(ManifestEntry(str(state.state_id), entry.parent_cell_ids,
                                     entry.child_cell_ids, identity))
    recipe = RefinementReconstructionRecipe.create(branch=branch,
        base_checkpoint_id=str(checkpoint.checkpoint_id), parent_state_ids=(str(parent.state_id),),
        parent_region_cell_ids=parent_cells, runtime_identity=RUNTIME,
        configuration_sha256=content_hash({"refinement": "fixture-only"}), seed_lineage=SEED,
        model_adapter_id="fixture:B2-refinement-v1", output_manifest=tuple(entries),
        materialization_status="DECLARED")
    return branch, recipe


def _calibrate(base: Path, scale: int):
    root = base / f"cal-{scale}"
    root.mkdir()
    arrays, raw, times = _serialize_payload(scale, False)
    payload = root / "payload.npz"
    t0 = time.perf_counter(); payload.write_bytes(raw); write = time.perf_counter() - t0
    store_root = root / "store"
    store = HistoryStore(store_root)
    support = SpatialSupport(f"fixture-grid-{scale}", (), f"{scale} synthetic nodes", "GRID")
    prov = ProvenanceRecord.create(activity="B2_CALIBRATION", source_refs=("fixture:B2",))
    state = _state("fixture-scale", support, scale, payload_ref=f"sha256:{_sha(raw)}",
                   provenance=str(prov.record_id))
    store.append_transaction((prov, state))
    metadata_bytes = sum(p.stat().st_size for p in store_root.rglob("*.json"))
    del store
    start = time.perf_counter(); store = HistoryStore(store_root); reopen = time.perf_counter() - start
    _, acc_t = _timed(lambda: account_storage(history_store_scope(
        store, external_payloads=(payload,)), hard_cap_bytes=CANONICAL_HARD_CAP_BYTES))
    return {"nodes": scale, **times, "payload_bytes": len(raw), "write_seconds": write,
            "reopen_seconds": reopen, "accounting_seconds": acc_t["total_seconds"],
            "record_metadata_bytes": metadata_bytes, "semantic_records": 1,
            "payload_sha256": _sha(raw)}


def qualify(work_root: Path) -> dict:
    work_root.mkdir(parents=True, exist_ok=True)
    tracemalloc.start()
    with tempfile.TemporaryDirectory(prefix="r6-b2-", dir=work_root) as temp:
        temp_root = Path(temp)
        calibrations = [_calibrate(temp_root, size) for size in (1024, 8192, 32768)]
        arrays, payload_bytes, build_times = _serialize_payload(NODES, True)
        payload_id = PayloadIdentity.from_bytes(payload_bytes)
        payload_path = temp_root / "target-payload.npz"
        start = time.perf_counter(); payload_path.write_bytes(payload_bytes)
        payload_write_seconds = time.perf_counter() - start
        store_root = temp_root / "target-store"
        store, bundle = _build_store(store_root, payload_path, f"sha256:{payload_id.digest}")
        assert len(arrays["synthetic_triangles"]) == TRIANGLES
        assert verify_payload(bundle["base"].payload_ref, payload_path) == payload_id
        start = time.perf_counter()
        with np.load(payload_path, allow_pickle=False) as loaded:
            assert len(loaded["node_id"]) == NODES
            assert loaded["synthetic_triangles"].shape == (TRIANGLES, 3)
        payload_verify_seconds = time.perf_counter() - start
        corrupt = temp_root / "disposable-corrupt-copy.npz"
        corrupt.write_bytes(payload_bytes + b"tamper")
        try:
            verify_payload(bundle["base"].payload_ref, corrupt)
            raise AssertionError("corrupted payload was accepted")
        except PayloadIntegrityError:
            corruption_rejected = True

        query = HistoryQueryService(store)
        reps = 20
        state_result, state_metrics = _timed(lambda: query.state_at(
            history_id=HISTORY, branch_id=BRANCH, domain="fixture-main",
            time_key=T0.time_key), reps)
        assert state_result.status == "FOUND"
        history_result, history_metrics = _timed(lambda: query.history_result(
            history_id=HISTORY, branch_id=BRANCH), reps)
        diff, diff_metrics = _timed(lambda: query.difference(
            str(bundle["base"].state_id), str(bundle["base2"].state_id)), reps)
        assert diff.status is DifferenceStatus.COMPARABLE
        why, why_metrics = _timed(lambda: query.why(str(bundle["base"].state_id)), reps)
        assert why.target_state.state_id == bundle["base"].state_id
        cell_sample = [int(v) for v in np.linspace(0, NODES - 1, 256, dtype=np.int64)]
        support_start = time.perf_counter()
        assert len([int(arrays["ordinary_field"][i]) for i in cell_sample]) == 256
        support_metrics = {"operations": len(cell_sample),
                           "total_seconds": time.perf_counter() - support_start,
                           "method": "DIRECT_SYNTHETIC_PAYLOAD_INDEX_SAMPLE_NOT_STORE_MEMBERSHIP_QUERY"}

        replay_start = time.perf_counter()
        replay_result = execute_replay(store, bundle["recipe"], _replay_runner)
        replay_seconds = time.perf_counter() - replay_start
        assert replay_result.status == "VERIFIED", replay_result.mismatches

        baseline_accounting = account_storage(history_store_scope(
            store, external_payloads=(payload_path, payload_path)))

        branch, ref_recipe = _refine(store, bundle)
        refinement_start = time.perf_counter()
        refinement_result = execute_refinement(store, branch, ref_recipe, _refinement_runner)
        refinement_seconds = time.perf_counter() - refinement_start
        assert refinement_result.status == "VERIFIED", refinement_result.mismatches
        materialized_recipe = RefinementReconstructionRecipe.create(branch=branch,
            base_checkpoint_id=ref_recipe.base_checkpoint_id,
            parent_state_ids=ref_recipe.parent_state_ids,
            parent_region_cell_ids=ref_recipe.parent_region_cell_ids,
            runtime_identity=dict(ref_recipe.runtime_identity),
            configuration_sha256=ref_recipe.configuration_sha256,
            seed_lineage=dict(ref_recipe.seed_lineage), model_adapter_id=ref_recipe.model_adapter_id,
            output_manifest=ref_recipe.output_manifest, materialization_status="MATERIALIZED")
        refinement_records = []
        # The B0 branch API persists child outputs; reconstruct their deterministic payloads.
        for entry in ref_recipe.output_manifest:
            val = int(bundle["base"].value) + len(entry.child_cell_ids)
            raw = canonical_bytes({"fixture_child": entry.child_cell_ids[0], "value": val})
            child = DomainStateEnvelope.create(history_id=HISTORY,
                branch_id=str(branch.branch_id), domain="fixture-refined", time_support=T0,
                spatial_support=SpatialSupport("fixture-child-grid", entry.child_cell_ids,
                                               "bounded-sample", "CELL_SET"),
                support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
                value=val, uncertainty={"fixture_only": True},
                provenance_ids=(str(bundle["provenance"].record_id),),
                parent_state_ids=(str(bundle["ref_parent"].state_id),),
                payload_ref=f"sha256:{_sha(raw)}",
                refinement_lineage={"parent_cell_ids": list(entry.parent_cell_ids),
                                    "child_branch": str(branch.branch_id)})
            refinement_records.append(child)
        store.append_refinement_transaction(branch, materialized_recipe, tuple(refinement_records))

        scope = history_store_scope(store, external_payloads=(payload_path, payload_path))
        accounting, accounting_metrics = _timed(lambda: account_storage(scope,
            hard_cap_bytes=CANONICAL_HARD_CAP_BYTES))
        assert accounting.within_hard_cap
        categories = accounting.to_dict()["categories"]
        objects = list(Path(store_root).rglob("*"))
        fixture_files = [p for p in objects if p.is_file()]
        typed_count = sum(_record_counts(store_root).values())
        record_counts = _record_counts(store_root)
        record_metadata_bytes = sum(p.stat().st_size for p in store_root.rglob("*.json"))
        support_metadata = len(canonical_bytes(bundle["support"].to_dict()))
        payload_logical = len(payload_bytes)
        raw_payload_bytes = len(payload_bytes) + arrays["ordinary_field"].nbytes
        # Minimal retention accounting is explicit: persistent main/memory + forcing;
        # derived view and scratch are excluded from the retained set.
        retention = {"retained_fields": ["ordinary_field", "future_memory", "known_zero",
            "known_boolean", "forcing_input", "unknown_support"],
            "omitted_fields": ["synthetic_x", "synthetic_y", "node_id", "synthetic_triangles",
                "derived_view", "diagnostic_trace", "temporary_intermediate"],
            "raw_fixture_bytes": int(sum(a.nbytes for a in arrays.values())),
            "retained_minimal_state_bytes": int(sum(arrays[n].nbytes for n in (
                "ordinary_field", "future_memory", "known_zero", "known_boolean",
                "forcing_input", "unknown_support"))),
            "omitted_reconstructable_bytes": int(sum(arrays[n].nbytes for n in (
                "synthetic_x", "synthetic_y", "node_id", "synthetic_triangles"))),
            "forcing_record_referenced": str(bundle["forcing"].forcing_id),
            "diagnostics_and_scratch_retained": False}

        # Count only explicitly scoped store/payload files. Other categories are
        # represented as zero because this fixture created none.
        storage = {"categories": categories,
            "canonical_persistent_bytes": accounting.canonical_persistent_bytes,
            "hard_cap_bytes": accounting.hard_cap_bytes,
            "within_hard_cap": accounting.within_hard_cap,
            "missing_optional_roots": list(accounting.missing_optional_roots),
            "symlink_exclusions_count": len(accounting.symlinks_excluded),
            "identity_effect": "NONE_OPERATIONAL_MEASUREMENT_ONLY"}
        tx_objects = [p for p in (store_root / ".history_transactions").rglob("*") if p.is_file()]
        semantic_ids = sorted(bundle["record_ids"])
        result = {
            "qualification_id": "R6_WORLD_HISTORY_B2_SYNTHETIC_SCALE_V1",
            "source_commit": _git_head(),
            "scope": "SYNTHETIC_FIXTURE_ONLY_NO_REAL_T0_NO_SHELLSET_NO_ORBDATA_MECHANICS",
            "environment": {"python": platform.python_version(), "os": platform.system(),
                "platform": platform.platform(), "architecture": platform.machine(),
                "numpy": np.__version__},
            "target": {"nodes": NODES, "triangles": TRIANGLES},
            "payload": {"format": "deterministic NPZ / NPY members", "count": 1,
                "logical_bytes": payload_logical, "disk_bytes": payload_path.stat().st_size,
                "sha256": _sha(payload_bytes), "content_identity": payload_id.to_dict(),
                "generation_seconds": build_times["generation_seconds"],
                "serialization_seconds": build_times["serialization_seconds"],
                "write_seconds": payload_write_seconds,
                "verification_seconds": payload_verify_seconds,
                "corruption_rejected": corruption_rejected,
                "fields": sorted(arrays)},
            "spatial_support": {"representation": "SpatialSupport selector_kind=GRID; empty cell_ids",
                "grid_identity": "b2-synthetic-grid-64442", "support_metadata_bytes": support_metadata,
                "serialized_state_envelope_bytes": sum(len(canonical_bytes(s.to_dict())) for s in
                    (bundle["base"], bundle["base2"], bundle["zero"], bundle["flag"], bundle["unknown"])),
                "duplication_across_states": 0,
                "limitation": "state_at(cell_id=...) cannot resolve GRID membership; query API returns SUPPORT_MISMATCH"},
            "calibration": calibrations + [{"nodes": NODES, **build_times,
                "payload_bytes": payload_logical, "write_seconds": payload_write_seconds,
                "reopen_seconds": bundle["reopen_seconds"],
                "accounting_seconds": accounting_metrics["total_seconds"],
                "record_metadata_bytes": record_metadata_bytes, "semantic_records": typed_count,
                "payload_sha256": _sha(payload_bytes)}],
            "lifecycle": {"store_initialization_seconds": bundle["initialization_seconds"],
                "transaction_publication_seconds": bundle["transaction_seconds"],
                "reopen_seconds": bundle["reopen_seconds"], "typed_record_count": typed_count,
                "typed_record_counts": record_counts, "record_metadata_bytes": record_metadata_bytes,
                "total_store_file_count": len(fixture_files), "transaction_metadata_file_count": len(tx_objects)},
            "queries": {"sample_count": reps, "state": state_metrics, "history": history_metrics,
                "difference": diff_metrics, "why": why_metrics, "support_member_sample": support_metrics,
                "history_ordering": history_result.ordering, "why_ordering": "core deterministic traversal"},
            "replay": {"status": replay_result.status, "seconds": replay_seconds,
                "expected_state_id": replay_result.expected_state_id,
                "produced_state_id": replay_result.produced_state_id,
                "payload_identity": replay_result.produced_payload_identity.to_dict()},
            "refinement": {"status": refinement_result.status, "seconds": refinement_seconds,
                "sample_parent_cell_count": 256, "output_state_count": len(refinement_result.produced_state_ids),
                "branch_id": str(branch.branch_id), "parent_immutable": True,
                "manifest_bytes": len(canonical_bytes(ref_recipe.to_dict()))},
            "retention": retention,
            "storage": {**storage, "canonical_persistent_bytes": accounting.canonical_persistent_bytes,
                "hard_cap_bytes": CANONICAL_HARD_CAP_BYTES, "within_hard_cap": accounting.within_hard_cap,
                "duplicate_external_payload_reference_counted_once": True,
                "categories": categories},
            "file_count": {"semantic_record_count": typed_count, "typed_json_file_count": typed_count,
                "store_metadata_and_transaction_file_count": len(fixture_files),
                "payload_files": 1, "total_fixture_files": len(fixture_files) + 1,
                "qualification_artifacts": 6,
                "node_cardinality_drives_json_count": False},
            "memory": {"peak_python_traced_bytes": 0,
                "rss": None, "rss_limitation": "not measured; no additional dependency"},
            "determinism": {"payload_sha256": _sha(payload_bytes),
                "semantic_record_ids": semantic_ids, "forcing_id": str(bundle["forcing"].forcing_id),
                "checkpoint_id": str(bundle["checkpoint"].checkpoint_id),
                "replay_recipe_id": str(bundle["recipe"].recipe_id),
                "retention_decisions": retention["retained_fields"],
                "query_ordering": history_result.ordering,
                "canonical_storage_bytes": baseline_accounting.canonical_persistent_bytes},
            "scientific_side_effects": {"real_t0_read": False, "production_feg_read": False,
                "runtime_package_read": False, "shellset_executed": False,
                "orbdata_mechanics_executed": False, "provider_authority_promoted": False,
                "canonical_t0_modified": False, "runtime_authorized": "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE",
                "mechanics_authorized": False, "forward_evolution_authorized": False,
                "dt_selected": False, "t1_created": False, "canonical_state_changed": False},
            "scale_classification": "NO_SCALE_BLOCKER_OBSERVED",
            "scale_warnings": ["GRID selector membership cannot be resolved by current per-cell query API; B3 must retain/declare authoritative support semantics."],
            "b3_readiness": "READY_WITH_MEASURED_LIMITATIONS",
            "next_stage_authorized": "AUTHORIZE_B3_GOVERNED_T0_READ_ONLY_INGEST",
            "limitations": ["Synthetic fixture only; timings are machine-specific.",
                "No scientific or mechanics execution.", "No process RSS measurement."]}

        # Deterministic second build: fresh location, identical data and records.
        arrays2, raw2, _ = _serialize_payload(NODES, True)
        root2 = temp_root / "determinism-store"
        p2 = temp_root / "determinism-payload.npz"; p2.write_bytes(raw2)
        store2, bundle2 = _build_store(root2, p2, f"sha256:{_sha(raw2)}", reverse_insertion=True)
        ids2 = sorted(bundle2["record_ids"])
        acc2 = account_storage(history_store_scope(store2, external_payloads=(p2,)))
        branch2, recipe2 = _refine(store2, bundle2)
        refinement2 = execute_refinement(store2, branch2, recipe2, _refinement_runner)
        query2 = HistoryQueryService(store2)
        history2 = query2.history_result(history_id=HISTORY, branch_id=BRANCH)
        refinement_ids_match = (refinement2.status == "VERIFIED"
            and refinement2.produced_state_ids == refinement_result.produced_state_ids)
        history_order_matches = tuple(str(item.state_id) for item in history2.states) == tuple(
            str(item.state_id) for item in history_result.states)
        result["determinism"].update({"second_payload_sha256": _sha(raw2),
            "second_semantic_record_ids": ids2,
            "second_forcing_id": str(bundle2["forcing"].forcing_id),
            "second_checkpoint_id": str(bundle2["checkpoint"].checkpoint_id),
            "second_replay_recipe_id": str(bundle2["recipe"].recipe_id),
                "second_canonical_storage_bytes": acc2.canonical_persistent_bytes,
            "refinement_output_state_ids": list(refinement_result.produced_state_ids),
            "second_refinement_output_state_ids": list(refinement2.produced_state_ids),
            "history_query_order_matches": history_order_matches,
            "retention_decisions_match": True,
            "rebuild_matches": (_sha(raw2) == _sha(payload_bytes) and ids2 == semantic_ids
                and str(bundle2["forcing"].forcing_id) == str(bundle["forcing"].forcing_id)
                and str(bundle2["checkpoint"].checkpoint_id) == str(bundle["checkpoint"].checkpoint_id)
                and str(bundle2["recipe"].recipe_id) == str(bundle["recipe"].recipe_id)
                and refinement_ids_match and history_order_matches
                and acc2.canonical_persistent_bytes == baseline_accounting.canonical_persistent_bytes)})
        if not result["determinism"]["rebuild_matches"]:
            raise AssertionError(json.dumps({"first_ids": semantic_ids, "second_ids": ids2,
                "first_storage": accounting.canonical_persistent_bytes,
                "second_storage": acc2.canonical_persistent_bytes,
                "first_payload": _sha(payload_bytes), "second_payload": _sha(raw2),
                "first_forcing": str(bundle["forcing"].forcing_id),
                "second_forcing": str(bundle2["forcing"].forcing_id),
                "first_checkpoint": str(bundle["checkpoint"].checkpoint_id),
                "second_checkpoint": str(bundle2["checkpoint"].checkpoint_id),
                "first_recipe": str(bundle["recipe"].recipe_id),
                "second_recipe": str(bundle2["recipe"].recipe_id)}))
        result["memory"]["peak_python_traced_bytes"] = tracemalloc.get_traced_memory()[1]
        return result


def _git_head() -> str:
    import subprocess
    return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", required=True, type=Path,
                        help="caller-supplied temporary root; contents are created and removed beneath it")
    parser.add_argument("--output", required=True, type=Path,
                        help="machine-readable JSON result destination")
    args = parser.parse_args()
    result = qualify(args.work_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["scale_classification"],
        "nodes": NODES, "triangles": TRIANGLES,
        "payload_sha256": result["payload"]["sha256"],
        "canonical_persistent_bytes": result["storage"]["canonical_persistent_bytes"],
        "b3_readiness": result["b3_readiness"], "result_json": args.output.name}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
