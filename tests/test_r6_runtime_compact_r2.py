"""R2 exact codec, authenticated order and ownership contract tests."""
import copy
import math

import pytest

from arcana_worldsim.r6.int10k_runtime_compact import (
    CompactError, CompactRuntime, make_delta, apply_delta, verify_entries,
)
from arcana_worldsim.r6.regional_geological_evolution import _canonical
from arcana_worldsim.r6.regional_geological_evolution import RegionalConfig, run_regional_segment
from test_r6_regional_geological_evolution import _initial_states, _identity


def snapshot(year=0):
    return {"time_year": year, "cells": [
        {"cell_id": "C0", "water": 1.0, "deposits": [
            {"event_id": "a", "mass_kg": 1.0, "density_kg_m3": 3.0},
            {"event_id": "b", "mass_kg": 2.0, "provenance": {"year": None}}]},
        {"cell_id": "C1", "deposits": []}]}


@pytest.mark.parametrize("operation", ["append", "replace", "remove", "reorder", "empty", "fields", "cells"])
def test_codec_exact_and_mutation_detached(operation):
    parent = snapshot()
    target = snapshot(1)
    rows = target["cells"][0]["deposits"]
    if operation == "append":
        rows.append({"event_id": "c", "mass_kg": -0.0})
    elif operation == "replace":
        rows[0]["mass_kg"] = 3.0
    elif operation == "remove":
        rows.pop(0)
    elif operation == "reorder":
        rows.reverse()
    elif operation == "empty":
        target["cells"] = []
    elif operation == "fields":
        del target["cells"][0]["water"]
        target["cells"][0]["new"] = {"unicode": "地", "null": None}
        target["new_top"] = []
    else:
        target["cells"].reverse()
    before = _canonical(parent)
    delta = make_delta(parent, target)
    result = apply_delta(parent, delta)
    assert _canonical(result) == _canonical(target)
    assert _canonical(parent) == before
    result["cells"].clear()
    assert _canonical(parent) == before
    assert delta == make_delta(parent, target)


@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf, object()])
def test_codec_rejects_invalid_json(invalid):
    target = snapshot(1)
    target["cells"][0]["new"] = invalid
    with pytest.raises((ValueError, TypeError)):
        make_delta(snapshot(), target)


def test_codec_rejects_cycles_duplicate_material_and_cell_ids():
    target = snapshot(1)
    target["cycle"] = target
    with pytest.raises((ValueError, TypeError)):
        make_delta(snapshot(), target)
    for field in ("cell", "material"):
        target = snapshot(1)
        if field == "cell":
            target["cells"].append(copy.deepcopy(target["cells"][0]))
        else:
            target["cells"][1]["deposits"].append(copy.deepcopy(target["cells"][0]["deposits"][0]))
        with pytest.raises(CompactError):
            make_delta(snapshot(), target)


@pytest.mark.parametrize("tamper", ["parent", "hash", "omission", "duplicate", "reorder"])
def test_codec_rejects_stale_corrupt_or_changed_operations(tamper):
    parent = snapshot()
    target = snapshot(1)
    target["cells"][0]["deposits"].append({"event_id": "c"})
    delta = make_delta(parent, target)
    if tamper == "parent":
        parent["cells"][0]["water"] = 4
    elif tamper == "hash":
        delta["target_snapshot_sha256"] = "0" * 64
    elif tamper == "omission":
        delta["cells"][0]["values"].clear()
    elif tamper == "duplicate":
        delta["cells"].append(delta["cells"][0])
    else:
        delta["cells"].reverse()
    with pytest.raises(CompactError):
        apply_delta(parent, delta)


def runtime(checkpoint=None, consumer=None):
    return CompactRuntime(_initial_states(), _identity(), config=RegionalConfig(duration_years=1000),
                          runtime_compact_history=True, checkpoint=checkpoint, consumer=consumer)


@pytest.mark.parametrize("years,split", [(3, 1), (10, 5)])
def test_runtime_exact_r1_split_and_full_legacy_materialization(years, split):
    expected = []
    r1 = run_regional_segment(_initial_states(), _identity(), config=RegionalConfig(duration_years=1000),
                             segment_years=years, history_independent_continuation=True,
                             runtime_copy_optimization=True,
                             history_consumer=lambda kind, payload: expected.append((kind, _canonical(payload))))
    direct = runtime()
    direct.advance(years)
    prefix = runtime()
    prefix.advance(split)
    resumed = runtime(prefix.checkpoint())
    resumed.advance(years-split)
    assert _canonical(direct.checkpoint()) == _canonical(resumed.checkpoint()) == _canonical(r1["checkpoint"])
    assert _canonical(direct.balances()) == _canonical(r1["balances"])
    def by_kind(rows):
        return {kind: [payload for k, payload in rows if k == kind] for kind in {k for k, _ in rows}}
    actual = [(kind, _canonical(payload)) for kind, payload in direct.legacy_history()]
    combined = [(kind, _canonical(payload)) for obj in (prefix, resumed) for kind, payload in obj.legacy_history()]
    assert by_kind(actual) == by_kind(combined) == by_kind(expected)
    assert direct.metrics["old_deposit_rows_copied_per_step"] == 0
    assert direct.metrics["full_snapshots_built_per_step"] == 0


def test_runtime_reader_and_callback_mutation_are_isolated():
    def consumer(kind, payload):
        payload.clear()
        payload["bad_external_value"] = math.nan
    actual = runtime(consumer=consumer)
    actual.advance(3)
    before = _canonical(actual.checkpoint())
    actual.snapshot()["cells"].clear()
    actual.checkpoint()["regional_checkpoint"]["regional_state"]["cells"].clear()
    records = list(actual.legacy_history())
    records[-1][1].clear()
    assert _canonical(actual.checkpoint()) == before
    assert len(actual.snapshot()["cells"]) == 9


def test_failed_consumer_poisons_session_and_blocks_partial_queries():
    def fail(kind, payload):
        if kind == "UNIFIED_STEP":
            raise RuntimeError("injected consumer failure")
    obj = runtime(consumer=fail)
    with pytest.raises(RuntimeError, match="injected"):
        obj.advance()
    for query in (obj.advance, obj.snapshot, obj.checkpoint):
        with pytest.raises(CompactError, match="POISONED"):
            query()


@pytest.mark.parametrize("mutation", ["drop", "duplicate", "reorder", "corrupt", "truncate"])
def test_authenticated_stream_rejects_event_loss_or_order_change(mutation):
    obj = runtime()
    obj.advance()
    entries = list(obj.entries)
    assert list(verify_entries(entries, obj.initial_head, obj.head))
    if mutation == "drop":
        entries.pop(2)
    elif mutation == "duplicate":
        entries.insert(2, entries[2])
    elif mutation == "reorder":
        entries[2:4] = reversed(entries[2:4])
    elif mutation == "corrupt":
        entries[2] = entries[2].replace(b'"mass_kg":', b'"mass_kg":0,"changed":', 1)
        if entries[2] == obj.entries[2]:
            entries[2] = b'{}'
    else:
        entries.pop()
    with pytest.raises(CompactError):
        list(verify_entries(entries, obj.initial_head, obj.head))


def test_private_deposit_rows_are_immutable_and_invalid_checkpoint_fails():
    obj = runtime()
    obj.advance()
    cp = obj.checkpoint()
    cp["regional_checkpoint"]["regional_state"]["records"] = [{"bad": math.nan}]
    with pytest.raises(ValueError):
        runtime(cp)
    log = next(c["deposits"] for c in obj._owner.region["cells"] if len(c["deposits"]))
    row = next(iter(log))
    with pytest.raises(TypeError):
        row["mass_kg"] = 0
    with pytest.raises(AttributeError):
        log.clear()
