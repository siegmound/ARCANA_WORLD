from __future__ import annotations

from dataclasses import replace
import json
import math
from pathlib import Path

import pytest

from arcana_worldsim.r6 import integrated_geological_microdomain as micro
from arcana_worldsim.r6.tectonic_boundary_microdomain import (
    DEFAULT_ENGINEERING_CONFIG,
    _file_sha_size,
    _view_digest,
    _write_view_cache,
    boundary_view_cache_default_path,
    load_cached_t0_boundary_view,
    _run_case,
    _series_spring_partition,
    build_t0_boundary_binding,
)
from test_r6_tectonic_deep_pilot import _state


def _fixture_inputs():
    base = _state()
    state_a = replace(base, materials=tuple(replace(
        material,
        role_id=("CONTINENTAL_CRUST_REFERENCE" if material.role_id == "CRUST"
                 else "LITHOSPHERIC_MANTLE_REFERENCE"),
    ) for material in base.materials))
    state_b = replace(state_a, width_m=state_a.width_m * 1.01,
                      initial_width_m=state_a.initial_width_m * 1.01)
    return [
        (state_a, {"support_id": "R6G1D-R091-C028", "sequence": 12,
                   "state_payload_sha256": micro._state_digest(state_a)}),
        (state_b, {"support_id": "R6G1D-R091-C029", "sequence": 0,
                   "state_payload_sha256": micro._state_digest(state_b)}),
    ]


def _binding_fixture():
    return {"boundary": {"boundary_id": "SYNTHETIC_T0_BOUNDARY_FIXTURE"}}


def test_t0_binding_reconstructs_b5_edge_to_eng10k_profiles():
    repo = Path(__file__).resolve().parents[1]
    external = repo.parents[1] / "_ARCANA_EXTERNAL_SOURCES"
    archive = Path(r"F:\corsiiiuu\Magistrale\Arcana\ENG10K_LUNA_ANALYSIS\ENG10K_ARCHIVE_ec79bf89_01.tar.gz")
    if not external.exists() or not archive.exists():
        pytest.skip("local governed B5 sources or ENG10K archive unavailable")
    result = build_t0_boundary_binding(
        repo, external, archive, cache_path=boundary_view_cache_default_path(repo))
    assert result["time_scope"] == "T0_INSTANT_ONLY_NO_POSITIVE_DURATION_VALIDITY"
    assert result["support_cells"] == [
        {"support_id": "R6G1D-R091-C028", "grid_cell": [91, 28], "plate_id": 11},
        {"support_id": "R6G1D-R091-C029", "grid_cell": [91, 29], "plate_id": 5},
    ]
    assert result["boundary"]["boundary_id"] == "R6BND-T0-3eb57747e6f0a3f3305f"
    assert result["boundary"]["positive_duration_validity"] == "UNKNOWN"
    assert result["boundary"]["t0_velocity_used_as_positive_time_forcing"] is False
    assert set(result["eng10k_profile_binding_checks"]) == {
        "R6G1D-R091-C028", "R6G1D-R091-C029"}


def test_disconnected_and_contact_cases_advance_columns_and_conserve_deep():
    loaded = _fixture_inputs()
    before = [state.payload() for state, _ in loaded]
    cfg = dict(DEFAULT_ENGINEERING_CONFIG)
    cfg["steps"] = 2
    disconnected = _run_case(loaded, _binding_fixture(), config=cfg,
                              coupled=False, lateral_mode="BLOCKED")
    connected = _run_case(loaded, _binding_fixture(), config=cfg,
                          coupled=True, lateral_mode="BLOCKED")
    for support, (original, _meta) in zip(
            ("R6G1D-R091-C028", "R6G1D-R091-C029"), loaded):
        original_roles = [material.role_id for material in original.materials]
        assert disconnected["support_material_roles"][support] == original_roles
        assert connected["support_material_roles"][support] == original_roles
    assert disconnected["steps"][0]["mechanics"]["interface_force_n"] == 0
    assert connected["steps"][0]["mechanics"]["interface_force_n"] > 0
    assert connected["steps"][0]["mechanics"]["work_balance_residual_j"] == pytest.approx(0, abs=1e-14)
    assert connected["steps"][0]["mechanics"]["displacement_closure_m"] == pytest.approx(0, abs=1e-14)
    assert connected["steps"][0]["interface_stress_pa"] is None
    assert connected["state_final_sha256"] != disconnected["state_final_sha256"]
    for result in (disconnected, connected):
        assert result["deep_conservation_residual_j"] == pytest.approx(0, abs=1e-5)
        assert all(step["deep"]["lateral_interface_count"] == 0 for step in result["steps"])
        assert all(value >= 0 and math.isfinite(value) for value in result["deep_stocks_j_by_cell"].values())
    assert [state.payload() for state, _ in loaded] == before


def test_lateral_deep_requires_explicit_mode_and_structural_modulation_is_separate():
    loaded = _fixture_inputs()
    cfg = dict(DEFAULT_ENGINEERING_CONFIG)
    cfg["steps"] = 1
    blocked = _run_case(loaded, _binding_fixture(), config=cfg,
                        coupled=True, lateral_mode="BLOCKED")
    constant = _run_case(loaded, _binding_fixture(), config=cfg,
                         coupled=True, lateral_mode="SYNTHETIC_CONSTANT")
    modulated = _run_case(loaded, _binding_fixture(), config=cfg,
                          coupled=True, lateral_mode="SYNTHETIC_STRUCTURE_MODULATED")
    assert blocked["steps"][0]["deep"]["lateral_interface_count"] == 0
    assert constant["steps"][0]["deep"]["lateral_interface_count"] == 73
    fractions_c = [x["fraction"] for x in constant["steps"][0]["deep"]["lateral_transfers"]]
    fractions_m = [x["fraction"] for x in modulated["steps"][0]["deep"]["lateral_transfers"]]
    assert all(b > a for a, b in zip(fractions_c, fractions_m))
    assert blocked["deep_stocks_j_by_cell"] != constant["deep_stocks_j_by_cell"]
    assert constant["deep_stocks_j_by_cell"] != modulated["deep_stocks_j_by_cell"]
    for result in (constant, modulated):
        assert result["deep_conservation_residual_j"] == pytest.approx(0, abs=1e-5)
        assert result["steps"][0]["deep"]["thermal_to_deep_j"] == 0
        assert result["steps"][0]["deep"]["mechanical_work_to_deep_j"] == 0


def test_spring_partition_validates_inputs_and_balances_work():
    result = _series_spring_partition(0.01, (2e6, 1e6, 2e6), 1.0)
    assert result["interface_force_n"] == pytest.approx(5000.0)
    assert result["column_a_displacement_m"] + result["interface_gap_m"] + result["column_b_displacement_m"] == pytest.approx(0.01)
    assert result["spring_energy_j"] == pytest.approx(result["external_work_j"])
    with pytest.raises(ValueError, match="CONFIGURATION_INVALID"):
        _series_spring_partition(-1.0, (1.0, 1.0, 1.0), 1.0)


def test_b5_cached_edge_view_rechecks_source_and_payload_identity(tmp_path, monkeypatch):
    dependency = tmp_path / "governed-input.bin"
    dependency.write_bytes(b"original")
    digest, size, _ = _file_sha_size(dependency)
    current = [{"logical_path": "governed-input.bin", "path_kind": "REPOSITORY",
                "path": str(dependency.resolve()), "sha256": digest, "byte_size": size}]
    monkeypatch.setattr(
        "arcana_worldsim.r6.tectonic_boundary_microdomain._cached_view_source_identity",
        lambda *_args, **_kwargs: ("r6/si1-bandwidth-f2av", "head-1", "source-1", current),
    )
    monkeypatch.setattr(
        "arcana_worldsim.r6.tectonic_boundary_microdomain._validate_cached_edge_content",
        lambda *_args, **_kwargs: None,
    )
    binding = {"source_branch": "r6/si1-bandwidth-f2av", "source_head": "head-1",
               "source_identity_sha256": "source-1",
               "boundary": {"boundary_id": "R6BND-T0-3eb57747e6f0a3f3305f"},
               "support_cells": [{"support_id": "R6G1D-R091-C028"},
                                 {"support_id": "R6G1D-R091-C029"}]}
    cache = tmp_path / "edge-view.json"
    _write_view_cache(cache, binding, source_files=current)
    loaded, check = load_cached_t0_boundary_view(
        cache, tmp_path, tmp_path, expected_branch="r6/si1-bandwidth-f2av")
    assert _view_digest(loaded) == _view_digest(binding)
    assert check["mode"] == "VERIFIED_CACHE_REUSE_NO_GLOBAL_TOPOLOGY_REBUILD"
    dependency.write_bytes(b"changed")
    changed_digest, changed_size, _ = _file_sha_size(dependency)
    current[0].update(sha256=changed_digest, byte_size=changed_size)
    with pytest.raises(ValueError, match="SOURCE_FILE_CHANGED"):
        load_cached_t0_boundary_view(
            cache, tmp_path, tmp_path, expected_branch="r6/si1-bandwidth-f2av")


def test_b5_cached_edge_view_rejects_payload_tampering(tmp_path, monkeypatch):
    dependency = tmp_path / "governed-input.bin"
    dependency.write_bytes(b"same")
    digest, size, _ = _file_sha_size(dependency)
    current = [{"logical_path": "governed-input.bin", "path_kind": "REPOSITORY",
                "path": str(dependency.resolve()), "sha256": digest, "byte_size": size}]
    monkeypatch.setattr(
        "arcana_worldsim.r6.tectonic_boundary_microdomain._cached_view_source_identity",
        lambda *_args, **_kwargs: ("r6/si1-bandwidth-f2av", "head-1", "source-1", current),
    )
    monkeypatch.setattr(
        "arcana_worldsim.r6.tectonic_boundary_microdomain._validate_cached_edge_content",
        lambda *_args, **_kwargs: None,
    )
    binding = {"source_branch": "r6/si1-bandwidth-f2av", "source_head": "head-1",
               "source_identity_sha256": "source-1",
               "boundary": {"boundary_id": "R6BND-T0-3eb57747e6f0a3f3305f"},
               "support_cells": [{"support_id": "R6G1D-R091-C028"},
                                 {"support_id": "R6G1D-R091-C029"}]}
    cache = tmp_path / "edge-view.json"
    _write_view_cache(cache, binding, source_files=current)
    record = json.loads(cache.read_text(encoding="utf-8"))
    record["binding"]["boundary"]["boundary_id"] = "tampered"
    cache.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="BINDING_DIGEST_MISMATCH"):
        load_cached_t0_boundary_view(
            cache, tmp_path, tmp_path, expected_branch="r6/si1-bandwidth-f2av")
