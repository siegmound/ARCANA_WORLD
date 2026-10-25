from __future__ import annotations

import hashlib
import json

import pytest

from arcana_worldsim.r6.geological_surface_microdomain import (
    SIDECAR_FILENAME,
    SUPPORTS,
    SurfaceConfig,
    SurfaceMicrodomainError,
    load_verified_r6_initial_columns,
    run_surface_microdomain,
    write_result,
)


def _source_states():
    states = {}
    for index, support in enumerate(SUPPORTS):
        states[support] = {
            "time_s": 0.0,
            "width_m": 100_000.0 + index * 10_000.0,
            "temperature_k": [288.0] * 73,
            "z_m": [0.0] * 73,
            "materials": [{"role_id": "CONTINENTAL_CRUST_REFERENCE",
                           "rho_kg_m3": 2700.0}] * 73,
        }
    return states


def _identity():
    return {"source_result_sha256": "a" * 64,
            "support_state_sha256": {support: "b" * 64 for support in SUPPORTS},
            "t0_boundary_id": "TEST_BOUNDARY",
            "t0_boundary_length_m": 111_194.92664455874,
            "support_cells": [
                {"support_id": SUPPORTS[0], "grid_cell": [91, 28]},
                {"support_id": SUPPORTS[1], "grid_cell": [91, 29]},
            ]}


def test_surface_uplift_and_diffusive_cover_transport_conserve_mass_and_geometry():
    result = run_surface_microdomain(_source_states(), _identity())

    assert result["schema"] == "ARCANA_R6_GEOLOGICAL_SURFACE_MICRODOMAIN_V1"
    assert result["input_authority"]["surface_elevation"].startswith("SYNTHETIC")
    assert len(result["steps"]) == 3
    assert result["steps"][0]["surface_transport"]["transferred_volume_m3"] > 0
    assert result["mass_balance_residual_kg"] == pytest.approx(0.0, abs=1e-7)
    assert result["final_cover_mass_kg"] == pytest.approx(result["initial_cover_mass_kg"])
    assert result["boundary_mass_flux_kg"] == 0.0
    assert result["final_surface_volume_m3"] - result["initial_surface_volume_m3"] == pytest.approx(
        result["prescribed_uplift_volume_m3"], rel=1e-12)
    assert result["deep_inventory_change_j"] == 0.0
    assert result["cells"][0]["subsurface_role_id"] == "CONTINENTAL_CRUST_REFERENCE"
    assert result["cells"][0]["subsurface_temperature_k"] == 288.0
    assert result["cells"][0]["surface_elevation_m"] != result["cells"][1]["surface_elevation_m"]
    assert all(cell["cover_mass_kg"] >= 0 for cell in result["cells"])


def test_transport_off_keeps_cover_spatially_fixed_but_applies_prescribed_uplift():
    config = SurfaceConfig(enable_surface_transport=False)
    result = run_surface_microdomain(_source_states(), _identity(), config=config)
    assert result["steps"][0]["surface_transport"]["transferred_volume_m3"] == 0.0
    assert [cell["cover_thickness_m"] for cell in result["cells"]] == [5.0, 5.0]
    assert result["mass_balance_residual_kg"] == 0.0
    assert result["final_surface_volume_m3"] - result["initial_surface_volume_m3"] == pytest.approx(
        result["prescribed_uplift_volume_m3"])


def test_large_step_is_capped_without_negative_cover_or_mass_loss():
    config = SurfaceConfig(duration_years=100.0, dt_years=100.0,
                           linear_diffusivity_m2_year=1e20)
    result = run_surface_microdomain(_source_states(), _identity(), config=config)
    assert result["mass_balance_residual_kg"] == pytest.approx(0.0, abs=1e-7)
    assert all(cell["cover_thickness_m"] >= 0 for cell in result["cells"])
    assert result["steps"][0]["surface_transport"]["transferred_volume_m3"] <= 0.5 * (
        result["cells"][0]["surface_area_m2"] * 25.25)


def test_incompatible_supports_and_invalid_inputs_fail_closed():
    bad = _source_states()
    bad.pop(SUPPORTS[1])
    with pytest.raises(SurfaceMicrodomainError, match="SUPPORT_SET_MISMATCH"):
        run_surface_microdomain(bad, _identity())
    with pytest.raises(SurfaceMicrodomainError, match="NONFINITE"):
        run_surface_microdomain(_source_states(), _identity(),
                                config=SurfaceConfig(initial_relief_m=(float("nan"), 0.0)))


def test_verified_input_loader_checks_manifest_sidecar_and_state_fingerprints(tmp_path):
    result = {
        "cases": [{"case_id": "UNCoupled_reference",
                   "state_initial": _source_states(),
                   "state_initial_sha256": {support: hashlib.sha256(json.dumps(
                       state, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                       allow_nan=False).encode()).hexdigest()
                       for support, state in _source_states().items()}}],
        "scope": "SYNTHETIC_TEST_ONLY",
        "t0_boundary_binding": {
            "archive_sha256": "c" * 64,
            "source_branch": "test",
            "source_head": "test",
            "source_identity_sha256": "d" * 64,
            "vector_partition_payload_sha256": "e" * 64,
            "support_cells": [
                {"support_id": SUPPORTS[0], "grid_cell": [91, 28]},
                {"support_id": SUPPORTS[1], "grid_cell": [91, 29]},
            ],
            "boundary": {"boundary_id": "TEST_BOUNDARY",
                         "boundary_kind": "GEOMETRIC_SHARED_INTERFACE",
                         "ordered_plate_pair": [5, 11],
                         "length_m": 111_194.92664455874},
        },
    }
    # The production loader also checks exact profile cardinality and finite nodes.
    result_bytes = json.dumps(result, sort_keys=True, separators=(",", ":"),
                              ensure_ascii=False, allow_nan=False).encode()
    sidecar = f"{hashlib.sha256(result_bytes).hexdigest()}  RESULT.json\n".encode()
    manifest = {"schema": "ARCANA_CONSTITUTIVE_MECHANICS_MANIFEST_V1",
                "result": {"path": "RESULT.json", "size_bytes": len(result_bytes),
                           "sha256": hashlib.sha256(result_bytes).hexdigest()},
                "sidecar": {"path": SIDECAR_FILENAME, "size_bytes": len(sidecar),
                            "sha256": hashlib.sha256(sidecar).hexdigest()}}
    (tmp_path / "RESULT.json").write_bytes(result_bytes)
    (tmp_path / SIDECAR_FILENAME).write_bytes(sidecar)
    (tmp_path / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    states, identity = load_verified_r6_initial_columns(tmp_path)
    assert set(states) == set(SUPPORTS)
    assert identity["source_result_sha256"] == hashlib.sha256(result_bytes).hexdigest()
    (tmp_path / SIDECAR_FILENAME).write_text("0" * 64 + "  RESULT.json\n", encoding="ascii")
    with pytest.raises(SurfaceMicrodomainError, match="SIDECAR_MANIFEST_MISMATCH"):
        load_verified_r6_initial_columns(tmp_path)


def test_result_writer_is_manifested_and_refuses_existing_directory(tmp_path):
    result = run_surface_microdomain(_source_states(), _identity())
    out = tmp_path / "surface-result"
    manifest = write_result(result, out)
    raw = (out / "RESULT.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == manifest["result"]["sha256"]
    assert json.loads((out / "MANIFEST.json").read_text())["result"] == manifest["result"]
    with pytest.raises(FileExistsError):
        write_result(result, out)
