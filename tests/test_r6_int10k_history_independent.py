from __future__ import annotations

import copy
import hashlib
import json

import pytest

from arcana_worldsim.r6.int10k_history_independent import (
    CHECKPOINT_SCHEMA,
    HistoryCollector,
    HistoryContinuationError,
    HistoryReader,
    seal_history_independent_checkpoint,
    verify_history_independent_checkpoint,
)


def _accumulators():
    return {
        "material_flows": {
            "bedrock_detachment_kg_by_material_id": {},
            "outlet_export_kg_by_material_id": {},
            "deposition_kg_by_material_id": {},
            "internal_transfer_kg_by_material_id": {},
            "mobile_cover_erosion_kg_by_material_id": {},
        },
        "mechanical": {"external_work_j": 0.0, "viscous_dissipation_j": 0.0,
                       "algorithmic_energy_increment_j": 0.0},
        "deep": {"gross_internal_transport_j": 0.0, "net_transport_0_to_1_j": 0.0,
                 "minimum_reservoir_stock_j": 4.0},
    }


def _checkpoint(year=1):
    source = {"source": "synthetic-test"}
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"),
                                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    sha = lambda value: hashlib.sha256(canonical(value)).hexdigest()
    unified = {
        "schema": "ARCANA_R6_UNIFIED_MULTIPHYSICS_CHECKPOINT_V2",
        "state": {"elapsed_external_steps": year,
                  "history_independent_continuation": True,
                  "history_accumulators": _accumulators()},
    }
    unified["state_sha256"] = sha({"schema": unified["schema"], "state": unified["state"]})
    region = {"schema": "ARCANA_R6_REGIONAL_GEOLOGICAL_STATE_V2",
              "time_years": year, "history_independent_continuation": True,
              "source_identity": source, "source_identity_sha256": sha(source),
              "cells": [{"cell_id": "C0"}]}
    result = {
        "schema": "ARCANA_R6_REGIONAL_FRONTIER_CHECKPOINT_V1",
        "regional_state": region,
        "unified_checkpoint": unified,
    }
    result["checkpoint_sha256"] = sha({key: value for key, value in result.items()
                                        if key != "checkpoint_sha256"})
    return result


def _reseal_engine_checkpoint(result):
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"),
                                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    sha = lambda value: hashlib.sha256(canonical(value)).hexdigest()
    unified = result["unified_checkpoint"]
    unified["state_sha256"] = sha({"schema": unified["schema"], "state": unified["state"]})
    result["checkpoint_sha256"] = sha({key: value for key, value in result.items()
                                        if key != "checkpoint_sha256"})


def _sealed(year=1):
    return seal_history_independent_checkpoint(
        _checkpoint(year), time_year=year,
        source_identity={"source": "synthetic-test"},
        configuration={"years": 3},
    )


def test_history_free_checkpoint_roundtrip_and_no_prefix():
    checkpoint = _sealed()
    restored = verify_history_independent_checkpoint(
        checkpoint, source_identity={"source": "synthetic-test"},
        configuration={"years": 3})
    assert checkpoint["schema"] == CHECKPOINT_SCHEMA
    assert checkpoint["history_prefix_required"] is False
    assert checkpoint["history_high_water_mark"] == 1
    assert checkpoint["next_regional_record_ordinal"] == 2
    state = restored["regional_state"]
    assert not {"records", "snapshots", "routing_events", "initial_condition_events"}.intersection(state)
    assert "records" not in restored["unified_checkpoint"]["state"]


def test_checkpoint_rejects_corruption_identity_version_and_ordinals():
    source = {"source": "synthetic-test"}
    config = {"years": 3}
    checkpoint = _sealed()
    altered = copy.deepcopy(checkpoint)
    altered["time_year"] = 2
    with pytest.raises(HistoryContinuationError, match="DIGEST"):
        verify_history_independent_checkpoint(altered, source_identity=source, configuration=config)
    with pytest.raises(HistoryContinuationError, match="SOURCE_OR_CONFIG"):
        verify_history_independent_checkpoint(checkpoint, source_identity={"source": "other"}, configuration=config)
    with pytest.raises(HistoryContinuationError, match="SOURCE_OR_CONFIG"):
        verify_history_independent_checkpoint(checkpoint, source_identity=source, configuration={"years": 10})
    altered = copy.deepcopy(checkpoint)
    altered["schema"] = "UNKNOWN"
    # Reseal the changed bytes so the version gate, rather than only the digest gate, is exercised.
    from arcana_worldsim.r6.int10k_history_independent import _sha
    altered["checkpoint_sha256"] = _sha({key: value for key, value in altered.items()
                                          if key != "checkpoint_sha256"})
    with pytest.raises(HistoryContinuationError, match="DIGEST_OR_SCHEMA"):
        verify_history_independent_checkpoint(altered, source_identity=source, configuration=config)


def test_checkpoint_rejects_missing_or_malformed_accumulators():
    source = {"source": "synthetic-test"}
    config = {"years": 3}
    bad = _checkpoint()
    del bad["unified_checkpoint"]["state"]["history_accumulators"]
    _reseal_engine_checkpoint(bad)
    sealed = seal_history_independent_checkpoint(
        bad, time_year=1, source_identity=source, configuration=config)
    with pytest.raises(HistoryContinuationError, match="ACCUMULATORS_MISSING"):
        verify_history_independent_checkpoint(sealed, source_identity=source, configuration=config)
    bad = _checkpoint()
    bad["unified_checkpoint"]["state"]["history_accumulators"]["deep"]["net_transport_0_to_1_j"] = float("nan")
    with pytest.raises(HistoryContinuationError, match="CANONICAL"):
        seal_history_independent_checkpoint(
            bad, time_year=1, source_identity=source, configuration=config)

    bad = _checkpoint()
    del bad["unified_checkpoint"]["state"]["history_accumulators"]["deep"]["gross_internal_transport_j"]
    _reseal_engine_checkpoint(bad)
    sealed = seal_history_independent_checkpoint(
        bad, time_year=1, source_identity=source, configuration=config)
    with pytest.raises(HistoryContinuationError, match="ACCUMULATORS_INVALID"):
        verify_history_independent_checkpoint(sealed, source_identity=source, configuration=config)


def test_frontier_rejects_embedded_history_instead_of_silently_stripping_it():
    bad = _checkpoint()
    bad["regional_state"]["records"] = []
    _reseal_engine_checkpoint(bad)
    with pytest.raises(HistoryContinuationError, match="REGIONAL_HISTORY"):
        seal_history_independent_checkpoint(
            bad, time_year=1, source_identity={"source": "synthetic-test"},
            configuration={"years": 3})


def test_collector_enforces_direct_and_resumed_ordinals_without_prefix():
    direct = HistoryCollector()
    direct.emit("REGIONAL_SNAPSHOT", {"time_year": 0, "cells": []})
    for year in range(1, 4):
        direct.emit("REGIONAL_YEAR_RECORD", {"time_year": year})
        direct.emit("REGIONAL_SNAPSHOT", {"time_year": year, "cells": []})
        direct.emit("UNIFIED_STEP", {"step": year, "elapsed_years": float(year)})
    prefix = direct.export()
    assert [r["time_year"] for r in prefix["regional_records"]] == [1, 2, 3]
    assert [r["time_year"] for r in prefix["regional_snapshots"]] == [0, 1, 2, 3]

    resumed = HistoryCollector(regional_start_year=1, unified_start_step=1,
                               include_initial_snapshot=False)
    resumed.emit("REGIONAL_YEAR_RECORD", {"time_year": 2})
    resumed.emit("REGIONAL_SNAPSHOT", {"time_year": 2, "cells": []})
    resumed.emit("UNIFIED_STEP", {"step": 2, "elapsed_years": 2.0})
    with pytest.raises(HistoryContinuationError, match="ORDINAL"):
        resumed.emit("UNIFIED_STEP", {"step": 2, "elapsed_years": 2.0})


def test_history_reader_is_exact_and_never_interpolates():
    event = {"kind": "DEPOSITION", "material_id": "M0", "time_year": 1}
    reader = HistoryReader({
        "regional_records": [{"time_year": 1, "events": [event]},
                             {"time_year": 3, "events": []}],
        "regional_snapshots": [{"time_year": 0, "cells": []}],
        "unified_steps": [{"step": 1, "elapsed_years": 1.0,
                           "deep": {"inventory_j_by_material_volume": {"V0": 3.0}}}],
    })
    assert reader.regional_record(3)["time_year"] == 3
    assert reader.deep_inventory(1, "V0")["inventory_j"] == 3.0
    assert reader.material_provenance("M0") == [event]
    with pytest.raises(HistoryContinuationError, match="TIME_NOT_ARCHIVED"):
        reader.regional_record(2)
    with pytest.raises(HistoryContinuationError, match="TIME_NOT_ARCHIVED"):
        reader.regional_snapshot(1)
    with pytest.raises(HistoryContinuationError, match="TIME_NOT_ARCHIVED"):
        reader.unified_step(2)
