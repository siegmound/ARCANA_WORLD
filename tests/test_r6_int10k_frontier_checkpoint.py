from __future__ import annotations

import copy
import json

import pytest

from arcana_worldsim.r6 import int10k_frontier_checkpoint as frontier
from arcana_worldsim.r6.regional_geological_evolution import (
    SCHEMA as REGIONAL_SCHEMA, seal_regional_checkpoint,
)
from arcana_worldsim.r6.unified_multiphysics_microdomain import seal_unified_checkpoint


def _sha(value):
    return frontier.hash_canonical(value)


def _legacy_checkpoint(year=2, *, extra_history=False):
    source = {
        "source_archive_sha256": "a" * 64,
        "source_manifest_sha256": "b" * 64,
        "source_result_sha256": "c" * 64,
        "support_state_sha256": {
            "R6G1D-R091-C028": "d" * 64,
            "R6G1D-R091-C029": "e" * 64,
        },
    }
    source_sha = _sha(source)
    cfg = {"duration_years": 10, "routing_mode": "DYNAMIC_TOPOGRAPHY"}
    run_identity = {"config": {"duration_years": 10, "step_years": 1}}
    run_identity_sha = _sha(run_identity)
    regional = {
        "schema": REGIONAL_SCHEMA,
        "authority": "SYNTHETIC_TEST_FIXTURE",
        "baseline_drainage_targets": {},
        "source_identity": source,
        "source_identity_sha256": source_sha,
        "config": cfg,
        "time_years": year,
        "cells": [{"cell_id": "C0", "cover": 1.0, "deposits": []}],
        "cumulative": {"water_m3": float(year)},
        "drainage_targets": {},
        "initial_totals": {},
        "interfaces": [],
        "material_catalog": [],
        "r6_support_mapping": {},
        "routing_mode": "DYNAMIC_TOPOGRAPHY",
        "t0_boundary_reference": {},
        "unperturbed_reference_drainage_targets": {},
        "records": [{"time_year": i, "events": []} for i in range(1, year + 1)],
        "snapshots": [{"time_year": i, "cells": []} for i in range(year + 1)],
        "routing_events": ([{"time_year": 1}] if extra_history and year else []),
        "initial_condition_events": [],
    }
    unified_state = {
        "source_identity": source,
        "run_identity": run_identity,
        "run_identity_sha256": run_identity_sha,
        "elapsed_external_steps": year,
        "planned_external_steps": 10,
        "cumulative_sediment": {},
        "cumulative_substrate_erosion_kg": 0.0,
        "cumulative_water": {"precipitation": float(year)},
        "deep_inventory_j_by_support": [1.0, 2.0],
        "deep_volume_ids": [],
        "deep_zeta_by_support": [0.2, 0.3],
        "geometry_roundoff_tolerance_m3": 1e-6,
        "initial_cover_mass_kg": 0.0,
        "initial_deep_inventory_j": 3.0,
        "initial_geometry_area_m2_by_support": {},
        "initial_material_inventory": {},
        "initial_state_sha256_by_support": {},
        "initial_substrate_mass_kg": 0.0,
        "initial_surface_snapshot": {},
        "initial_suspended_sediment_kg": 0.0,
        "initial_thermal_states": {},
        "initial_water_storage_m3": 0.0,
        "mechanical_reference_cells": {},
        "opening_total_m": {},
        "previous_displacement_m_by_support": {},
        "previous_interface_gap_m": 0.0,
        "previous_stored_energy_j": 0.0,
        "sediment_roundoff_tolerance_kg": 1e-6,
        "surface_state": {"cells": [{"cell_id": "C0", "water_m3": 0.0}]},
        "synthetic_modal_parameters_by_role": {},
        "thermal_states_by_support": {"C028": {"temperature_k": [1200.0]}},
        "total_strain": {},
        "viscous_strain": {"C028": [0.01]},
        "water_roundoff_tolerance_m3": 1e-6,
        "records": [{"elapsed_years": float(i), "deep": {}} for i in range(1, year + 1)],
    }
    unified = seal_unified_checkpoint(unified_state)
    return seal_regional_checkpoint(regional, unified_checkpoint=unified)


def test_frontier_projection_and_history_are_separate_and_legacy_restore_is_exact():
    legacy = _legacy_checkpoint(2, extra_history=True)
    projected, history = frontier.capture_frontier_v2(legacy)
    checkpoint = frontier.seal_checkpoint_v2(projected)
    cp = json.loads(frontier.serialize_checkpoint_v2(checkpoint))
    assert cp["schema"] == frontier.CHECKPOINT_SCHEMA
    assert cp["frontier"]["history_high_water_mark"]["time_year"] == 2
    assert "records" not in cp["frontier"]["regional_dynamic_state"]
    assert "snapshots" not in cp["frontier"]["regional_dynamic_state"]
    assert "routing_events" not in cp["frontier"]["regional_dynamic_state"]
    assert "records" not in cp["frontier"]["unified_dynamic_state"]
    restored = frontier.restore_legacy_checkpoint_v1(
        checkpoint, history, expected_source_identity=cp["frontier"]["source_identity"],
        expected_configuration=cp["frontier"]["configuration"])
    assert restored == legacy
    assert len(history.canonical_json) > 0


def test_frontier_checkpoint_size_excludes_added_historical_rows():
    short = _legacy_checkpoint(2)
    long = _legacy_checkpoint(7)
    cp_short = frontier.seal_checkpoint_v2(frontier.capture_frontier_v2(short)[0])
    cp_long = frontier.seal_checkpoint_v2(frontier.capture_frontier_v2(long)[0])
    short_payload = json.loads(cp_short.canonical_json)
    long_payload = json.loads(cp_long.canonical_json)
    # Synthetic fixture holds dynamic inventories constant; only its history grows.
    assert "records" not in short_payload["frontier"]["unified_dynamic_state"]
    assert len(cp_short.canonical_json) == len(cp_long.canonical_json)
    assert len(frontier.capture_frontier_v2(short)[1].canonical_json) < len(
        frontier.capture_frontier_v2(long)[1].canonical_json)


def test_history_prefix_required_and_rejected_when_missing_or_changed():
    legacy = _legacy_checkpoint(2)
    checkpoint_frontier, history = frontier.capture_frontier_v2(legacy)
    checkpoint = frontier.seal_checkpoint_v2(checkpoint_frontier)
    with pytest.raises(frontier.FrontierCheckpointError, match="HISTORY_PREFIX"):
        frontier.restore_legacy_checkpoint_v1(
            checkpoint, {"schema": frontier.HISTORY_PREFIX_SCHEMA},
            expected_source_identity=checkpoint_frontier.payload["source_identity"],
            expected_configuration=checkpoint_frontier.payload["configuration"])
    bad_history = history.payload
    bad_history["regional_year_records"].pop()
    with pytest.raises(frontier.FrontierCheckpointError, match="HISTORY_COVERAGE"):
        frontier.restore_legacy_checkpoint_v1(
            checkpoint, bad_history,
            expected_source_identity=checkpoint_frontier.payload["source_identity"],
            expected_configuration=checkpoint_frontier.payload["configuration"])


def test_checkpoint_corruption_schema_unknown_and_missing_fields_fail_closed():
    projected, _ = frontier.capture_frontier_v2(_legacy_checkpoint())
    checkpoint = frontier.seal_checkpoint_v2(projected)
    value = checkpoint.envelope
    value["frontier"]["time_year"] = 999
    with pytest.raises(frontier.FrontierCheckpointError, match="DIGEST"):
        frontier.verify_checkpoint_v2(value)

    value = checkpoint.envelope
    value["schema_version"] = 99
    with pytest.raises(frontier.FrontierCheckpointError, match="SCHEMA"):
        frontier.verify_checkpoint_v2(value)

    value = checkpoint.envelope
    del value["frontier"]["regional_dynamic_state"]["cells"]
    value["checkpoint_sha256"] = _sha({k: v for k, v in value.items()
                                       if k != "checkpoint_sha256"})
    value["frontier_sha256"] = _sha(value["frontier"])
    value["checkpoint_sha256"] = _sha({k: v for k, v in value.items()
                                       if k != "checkpoint_sha256"})
    with pytest.raises(frontier.FrontierCheckpointError, match="FRONTIER_FIELDS"):
        frontier.verify_checkpoint_v2(value)


def test_source_configuration_and_e0_identity_mismatch_are_rejected():
    projected, history = frontier.capture_frontier_v2(_legacy_checkpoint())
    checkpoint = frontier.seal_checkpoint_v2(projected)
    p = projected.payload
    wrong_source = copy.deepcopy(p["source_identity"])
    wrong_source["source_result_sha256"] = "f" * 64
    with pytest.raises(frontier.FrontierCheckpointError, match="SOURCE"):
        frontier.verify_checkpoint_v2(checkpoint.envelope,
                                      expected_source_identity=wrong_source)
    wrong_config = copy.deepcopy(p["configuration"])
    wrong_config["regional"]["duration_years"] = 11
    with pytest.raises(frontier.FrontierCheckpointError, match="CONFIGURATION"):
        frontier.verify_checkpoint_v2(checkpoint.envelope,
                                      expected_configuration=wrong_config)
    changed = p
    changed["e0_input_identities"]["source_result_sha256"] = "f" * 64
    with pytest.raises(frontier.FrontierCheckpointError, match="E0_INPUT"):
        frontier.seal_checkpoint_v2(changed)


def test_nonfinite_dynamic_state_is_rejected():
    projected, _ = frontier.capture_frontier_v2(_legacy_checkpoint())
    value = projected.payload
    value["regional_dynamic_state"]["cells"][0]["cover"] = float("nan")
    with pytest.raises(frontier.FrontierCheckpointError):
        frontier.seal_checkpoint_v2(value)
