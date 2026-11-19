"""R2 opt-in private frontier and lossless scratch history adapter.

This is not a durable HistoryStore, transaction manager or retention policy.
Runtime frames bind an authenticated chain; full canonical snapshot SHA is
explicitly deferred until materialization. Sealed codec deltas bind both SHAs.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from types import MappingProxyType
from typing import Mapping

from . import regional_geological_evolution as regional
from . import unified_multiphysics_microdomain as unified
from .int10k_history_independent import (
    seal_history_independent_checkpoint, verify_history_independent_checkpoint,
)

DELTA_SCHEMA = "ARCANA_R6_RUNTIME_R2_DELTA_V1"
FRAME_SCHEMA = "ARCANA_R6_RUNTIME_R2_UNSEALED_FRAME_V1"
STREAM_SCHEMA = "ARCANA_R6_RUNTIME_R2_SCRATCH_STREAM_V1"


class CompactError(ValueError):
    pass


def _copy(value):
    return json.loads(regional._canonical(value))


def _sha(value):
    return hashlib.sha256(regional._canonical(value)).hexdigest()


def _validate_snapshot(value):
    if not isinstance(value, dict) or type(value.get("time_year")) is not int or value["time_year"] < 0:
        raise CompactError("SNAPSHOT_TIME_INVALID")
    if not isinstance(value.get("cells"), list):
        raise CompactError("SNAPSHOT_CELLS_INVALID")
    cells, events = set(), set()
    for cell in value["cells"]:
        if not isinstance(cell, dict) or not isinstance(cell.get("cell_id"), str):
            raise CompactError("CELL_ID_INVALID")
        if cell["cell_id"] in cells or not isinstance(cell.get("deposits"), list):
            raise CompactError("CELL_DUPLICATE_OR_DEPOSITS_INVALID")
        cells.add(cell["cell_id"])
        for row in cell["deposits"]:
            if not isinstance(row, dict) or not isinstance(row.get("event_id"), str) or not row["event_id"]:
                raise CompactError("DEPOSIT_ID_MISSING")
            if row["event_id"] in events:
                raise CompactError("DEPOSIT_ID_DUPLICATE")
            events.add(row["event_id"])


def make_delta(parent, target):
    """General offline sealed codec; scanning/hashing full inputs is explicit."""
    parent, target = _copy(parent), _copy(target)
    _validate_snapshot(parent)
    _validate_snapshot(target)
    if target["time_year"] != parent["time_year"] + 1:
        raise CompactError("DELTA_CLOCK_INVALID")
    old = {cell["cell_id"]: cell for cell in parent["cells"]}
    cells = []
    for cell in target["cells"]:
        before = old.get(cell["cell_id"], {}).get("deposits", [])
        after = cell["deposits"]
        start = 0
        while start < min(len(before), len(after)) and regional._canonical(before[start]) == regional._canonical(after[start]):
            start += 1
        suffix = 0
        while suffix < min(len(before), len(after))-start and regional._canonical(before[-suffix-1]) == regional._canonical(after[-suffix-1]):
            suffix += 1
        cells.append({"fields": {k: v for k, v in cell.items() if k != "deposits"},
                      "start": start, "delete": len(before)-start-suffix,
                      "values": after[start:len(after)-suffix if suffix else len(after)]})
    body = {"schema": DELTA_SCHEMA, "parent_year": parent["time_year"],
            "year": target["time_year"],
            "parent_snapshot_sha256": _sha(parent), "target_snapshot_sha256": _sha(target),
            "snapshot_fields": {k: v for k, v in target.items() if k != "cells"}, "cells": cells}
    return {**body, "delta_sha256": _sha(body)}


def _apply_owned(parent, delta):
    """Private reconstruction buffer; never shares this buffer with a reader."""
    if delta["parent_year"] != parent["time_year"] or delta["year"] != parent["time_year"] + 1:
        raise CompactError("DELTA_PARENT_CLOCK_INVALID")
    previous = {c["cell_id"]: c for c in parent["cells"]}
    cells = []
    seen = set()
    for operation in delta["cells"]:
        fields = operation["fields"]
        cid = fields["cell_id"]
        if cid in seen or "deposits" in fields:
            raise CompactError("DELTA_CELL_DUPLICATE_OR_FIELDS_INVALID")
        seen.add(cid)
        rows = previous.get(cid, {}).get("deposits", [])
        start, delete = operation["start"], operation["delete"]
        if type(start) is not int or type(delete) is not int or min(start, delete) < 0 or start+delete > len(rows):
            raise CompactError("DELTA_SPLICE_INVALID")
        rows[start:start+delete] = _copy(operation["values"])
        cells.append({**_copy(fields), "deposits": rows})
    result = _copy(delta["snapshot_fields"])
    result["cells"] = cells
    if result.get("time_year") != delta["year"]:
        raise CompactError("DELTA_TARGET_CLOCK_INVALID")
    return result


def apply_delta(parent, delta):
    """Detached, fail-closed public reconstruction with canonical SHA checks."""
    parent, delta = _copy(parent), _copy(delta)
    _validate_snapshot(parent)
    required = {"schema", "parent_year", "year", "parent_snapshot_sha256", "target_snapshot_sha256",
                "snapshot_fields", "cells", "delta_sha256"}
    if set(delta) != required or delta["schema"] != DELTA_SCHEMA:
        raise CompactError("DELTA_FIELDS_OR_SCHEMA_INVALID")
    if _sha({k: v for k, v in delta.items() if k != "delta_sha256"}) != delta["delta_sha256"]:
        raise CompactError("DELTA_DIGEST_INVALID")
    if _sha(parent) != delta["parent_snapshot_sha256"]:
        raise CompactError("DELTA_PARENT_SHA_INVALID")
    try:
        result = _apply_owned(parent, delta)
        _validate_snapshot(result)
    except (KeyError, TypeError, IndexError) as exc:
        raise CompactError("DELTA_STRUCTURE_INVALID") from exc
    if _sha(result) != delta["target_snapshot_sha256"]:
        raise CompactError("DELTA_TARGET_SHA_INVALID")
    return result


def verify_entries(entries, initial_head, expected_head):
    """Check omission, truncation, duplication, reorder and corruption."""
    previous = initial_head
    for sequence, encoded in enumerate(entries):
        try:
            record = json.loads(encoded)
            if set(record) != {"schema", "sequence", "parent_sha256", "kind", "payload", "sha256"}:
                raise CompactError("STREAM_FIELDS_INVALID")
            if (record["schema"] != STREAM_SCHEMA or record["sequence"] != sequence
                    or record["parent_sha256"] != previous):
                raise CompactError("STREAM_ORDER_OR_PARENT_INVALID")
            body = {k: v for k, v in record.items() if k != "sha256"}
            if _sha(body) != record["sha256"]:
                raise CompactError("STREAM_DIGEST_INVALID")
            previous = record["sha256"]
            yield record["kind"], record["payload"]
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise CompactError("STREAM_STRUCTURE_INVALID") from exc
    if previous != expected_head:
        raise CompactError("STREAM_TRUNCATED_OR_HEAD_INVALID")


def _freeze(value):
    if type(value) is dict:
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if type(value) is list:
        return tuple(_freeze(v) for v in value)
    return value


def _thaw(value):
    if isinstance(value, Mapping):
        return {k: _thaw(v) for k, v in value.items()}
    if type(value) is tuple:
        return [_thaw(v) for v in value]
    return value


class _DepositLog:
    """Only append is available to the numerical operator; rows are immutable."""
    def __init__(self, rows, ids, metrics):
        self.__rows = []
        self.__ids = ids
        self.__metrics = metrics
        for row in rows:
            self.append(row)

    def __len__(self):
        return len(self.__rows)

    def __iter__(self):
        for row in self.__rows:
            self.__metrics["deposit_rows_read"] += 1
            yield row

    def append(self, row):
        detached = _copy(row)
        eid = detached.get("event_id")
        if not isinstance(eid, str) or not eid or eid in self.__ids:
            raise CompactError("DEPOSIT_ID_MISSING_OR_DUPLICATE")
        self.__ids.add(eid)
        self.__rows.append(_freeze(detached))
        self.__metrics["deposit_rows_frozen"] += 1

    def new_rows(self, start):
        rows = self.__rows[start:]
        self.__metrics["deposit_rows_exported"] += len(rows)
        return [_thaw(row) for row in rows]

    def export(self):
        return self.new_rows(0)


def _sort_owned(value):
    """Reproduce annual JSON key/reduction order without visiting deposit logs."""
    if type(value) is dict:
        items = sorted(value.items())
        value.clear()
        value.update(items)
        for child in value.values():
            _sort_owned(child)
    elif type(value) is list:
        for child in value:
            _sort_owned(child)


class _CompactOwner:
    def __init__(self, region):
        self.region = region
        self.in_step = False
        self.metrics = {"deposit_rows_read": 0, "deposit_rows_frozen": 0, "deposit_rows_exported": 0,
                        "old_deposit_rows_copied_per_step": 0, "full_snapshots_built_per_step": 0}
        ids = set()
        for cell in region["cells"]:
            cell["deposits"] = _DepositLog(cell["deposits"], ids, self.metrics)

    def begin(self, state):
        if state is not self.region or not self.in_step:
            raise CompactError("PRIVATE_FRONTIER_OWNERSHIP_INVALID")
        for key in regional._HISTORY_EXCLUDED_FROM_FRONTIER:
            if state.get(key):
                raise CompactError("PRIVATE_FRONTIER_CONTAINS_HISTORY")
        _sort_owned(state)
        self.starts = [len(c["deposits"]) for c in state["cells"]]
        return state

    def frame(self, year):
        return {"schema": FRAME_SCHEMA, "parent_year": year-1, "year": year,
                "parent_snapshot_sha256": None, "target_snapshot_sha256": None,
                "canonical_sha_status": "DEFERRED_UNTIL_MATERIALIZATION",
                "snapshot_fields": {"time_year": year},
                "cells": [{"fields": _copy({k: v for k, v in c.items() if k != "deposits"}),
                           "start": start, "delete": 0, "values": c["deposits"].new_rows(start)}
                          for c, start in zip(self.region["cells"], self.starts)]}


class CompactRuntime:
    """Explicit R2 API. Live state is private; outputs are copies or immutable bytes.

    Calling checkpoint/snapshot/legacy_history requests O(D) compatibility work.
    No whole-region checkpoints or full snapshots are generated by advance().
    A failed step poisons this session; restart requires a verified checkpoint.
    """
    def __init__(self, initial_states, source_identity, *, config,
                 runtime_compact_history=False, checkpoint=None, consumer=None,
                 run_plan=None):
        if runtime_compact_history is not True:
            raise CompactError("COMPACT_OPT_IN_REQUIRED")
        config.validate()
        self._source = _copy(dict(source_identity))
        self._initial = {support: unified._state_from_payload(_copy(state.payload()))
                         for support, state in initial_states.items()}
        self._config = config
        uplift_total = (0.1, 0.0)
        if run_plan is not None:
            from .runtime_run_plan import AnnualUpliftPlan
            from .geological_surface_microdomain import SUPPORTS
            if (type(run_plan) is not AnnualUpliftPlan
                    or run_plan.planned_years != config.duration_years
                    or set(self._initial) != set(SUPPORTS)
                    or {row["support_id"] for row in self._source.get("support_cells", [])} != set(SUPPORTS)):
                raise CompactError("EXPLICIT_PLAN_HORIZON_OR_SOURCE_SUPPORT_MISMATCH")
            totals = run_plan.totals_by_support()
            uplift_total = tuple(totals[support] for support in SUPPORTS)
        self._unified_config = unified.UnifiedConfig(
            duration_years=float(config.duration_years), external_step_years=1.0,
            hydrology_dt_seconds=31_557_600.0, opening_rate_m_year=0.01,
            prescribed_uplift_total_m_by_support=uplift_total,
            precipitation_m_year_by_support=(0.0, 0.0),
            evapotranspiration_m_year_by_support=(0.0, 0.0),
            infiltration_capacity_m_year_by_support=(0.0, 0.0), substrate_erosion_enabled=False)
        self._configuration = {"regional_config": asdict(config), "unified_config": asdict(self._unified_config)}
        self._unified_checkpoint = None
        if checkpoint is None:
            region = regional.create_synthetic_region(config, source_identity=self._source)
        else:
            restored = verify_history_independent_checkpoint(
                checkpoint, source_identity=self._source, configuration=self._configuration)
            region = _copy(restored["regional_state"])
            self._unified_checkpoint = _copy(restored["unified_checkpoint"])
        anchor = {"time_year": region["time_years"], "cells": region["cells"]}
        self._root_bytes = regional._canonical(anchor)
        _validate_snapshot(json.loads(self._root_bytes))
        self._root_year = region["time_years"]
        self._initial_head = _sha({"snapshot_sha256": hashlib.sha256(self._root_bytes).hexdigest(),
                                   "source": self._source, "configuration": self._configuration})
        self._head = self._initial_head
        self._entries = []
        self._frames = []
        self._consumer = consumer
        self._poisoned = False
        self._busy = False
        self._last_balances = None
        if checkpoint is None:
            self._emit("REGIONAL_SNAPSHOT", anchor)
            for event in region.get("initial_condition_events", []):
                self._emit("REGIONAL_EVENT", event)
        for key in regional._HISTORY_EXCLUDED_FROM_FRONTIER:
            region.pop(key, None)
        self._owner = _CompactOwner(region)

    @property
    def configuration(self):
        return _copy(self._configuration)

    @property
    def time_year(self):
        return self._owner.region["time_years"]

    @property
    def metrics(self):
        return dict(self._owner.metrics)

    @property
    def entries(self):
        return tuple(self._entries)

    @property
    def head(self):
        return self._head

    @property
    def initial_head(self):
        return self._initial_head

    def _check(self):
        if self._poisoned or self._busy:
            raise CompactError("SESSION_POISONED_OR_REENTRANT")

    def _emit(self, kind, payload):
        # Validate and detach once before a consumer can observe anything.
        detached = _copy(payload)
        body = {"schema": STREAM_SCHEMA, "sequence": len(self._entries),
                "parent_sha256": self._head, "kind": kind, "payload": detached}
        sha = _sha(body)
        encoded = regional._canonical({**body, "sha256": sha})
        self._entries.append(encoded)
        self._head = sha
        if kind == "REGIONAL_DELTA":
            self._frames.append(regional._canonical(detached))
        if self._consumer is not None:
            self._consumer(kind, _copy(detached))

    def advance(self, years=1):
        self._check()
        if type(years) is not int or years < 1 or self.time_year+years > self._config.duration_years:
            raise CompactError("SEGMENT_DURATION_INVALID")
        self._busy = True
        try:
            for _ in range(years):
                if self._unified_checkpoint is None:
                    result = unified.run_unified_microdomain(
                        self._initial, self._source, config=self._unified_config, segment_years=1.0,
                        history_independent_continuation=True, history_consumer=self._emit)
                else:
                    result = unified.continue_unified_microdomain(
                        self._unified_checkpoint, self._source, config=self._unified_config,
                        segment_years=1.0, history_independent_continuation=True, history_consumer=self._emit)
                self._unified_checkpoint = result["continuation"]
                region = self._owner.region
                for key in regional._HISTORY_EXCLUDED_FROM_FRONTIER:
                    region.pop(key, None)
                self._owner.in_step = True
                regional.advance_region(region, years=1, config=self._config,
                                        history_consumer=self._emit, _runtime_owner=self._owner)
                self._owner.in_step = False
                record = region["records"][-1]
                self._last_balances = _copy({"water": record["water_balance_m3"],
                                             "solid_mass_kg": record["solid_mass_balance_kg"],
                                             "deep": result["integrated_balances"]["deep"]})
                for key in regional._HISTORY_EXCLUDED_FROM_FRONTIER:
                    region.pop(key, None)
        except BaseException:
            self._poisoned = True
            raise
        finally:
            self._owner.in_step = False
            self._busy = False
        return {"schema": "ARCANA_R6_RUNTIME_R2_PROGRESS_V1", "time_year": self.time_year,
                "stream_head": self.head, "metrics": self.metrics}

    def snapshot(self, year=None):
        self._check()
        year = self.time_year if year is None else year
        if type(year) is not int or year < self._root_year or year > self.time_year:
            raise CompactError("TIME_NOT_ARCHIVED")
        state = json.loads(self._root_bytes)
        for encoded in self._frames:
            frame = json.loads(encoded)
            if frame["year"] > year:
                break
            state = _apply_owned(state, frame)
        return _copy(state)

    def legacy_history(self):
        self._check()
        state = json.loads(self._root_bytes)
        for kind, payload in verify_entries(self.entries, self.initial_head, self.head):
            if kind == "REGIONAL_DELTA":
                state = _apply_owned(state, payload)
                yield "REGIONAL_SNAPSHOT", _copy(state)
            else:
                yield kind, payload

    def checkpoint(self):
        self._check()
        if self._unified_checkpoint is None:
            raise CompactError("NO_ADVANCED_UNIFIED_CHECKPOINT")
        region = self._owner.region
        detached = _copy({k: v for k, v in region.items() if k != "cells"})
        detached["cells"] = [{**_copy({k: v for k, v in c.items() if k != "deposits"}),
                              "deposits": c["deposits"].export()} for c in region["cells"]]
        detached["history_independent_continuation"] = True
        engine = regional.seal_regional_checkpoint(detached, unified_checkpoint=_copy(self._unified_checkpoint))
        cp = seal_history_independent_checkpoint(engine, time_year=self.time_year,
                                                 source_identity=self._source, configuration=self._configuration)
        verify_history_independent_checkpoint(cp, source_identity=self._source, configuration=self._configuration)
        return cp

    def balances(self):
        self._check()
        return _copy(self._last_balances)
