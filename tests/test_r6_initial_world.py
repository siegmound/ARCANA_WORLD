from __future__ import annotations

from hashlib import sha256

import numpy as np
import pytest

from arcana_worldsim.r6.initial_world.generator import generate_initial_world
from arcana_worldsim.r6.initial_world.grid import GlobalGrid1Degree
from arcana_worldsim.r6.initial_world.latent import (
    PARENT_MEAN_TOLERANCE_M, build_latent_state, reconstruct_land_geometry,
)
from arcana_worldsim.r6.initial_world.materialize import (
    _deterministic_npz, _make_states, _package_markdown,
    _validate_canonical_package,
)
from arcana_worldsim.r6.initial_world.refinement import Region, materialize_region
from arcana_worldsim.r6.initial_world.seeds import derive_seed_streams
from arcana_worldsim.r6.initial_world.validation import validate_initial_world
from arcana_worldsim.r6.store import HistoryStore


def test_grid_geometry_ids_wrapping_and_spherical_area():
    grid = GlobalGrid1Degree()
    assert grid.shape == (180, 360)
    assert grid.cell_count == 64_800
    assert grid.lat_centers_deg[[0, -1]].tolist() == [-89.5, 89.5]
    assert grid.lon_centers_deg[[0, -1]].tolist() == [-179.5, 179.5]
    assert len({grid.cell_id(r, c) for r in (0, 89, 179) for c in range(360)}) == 1080
    assert grid.cell_id(0, 0) != grid.cell_id(0, 1)
    assert (10, 359) in grid.neighbors(10, 0)
    assert len(grid.neighbors(0, 0)) == 359 + 3
    assert np.all(grid.cell_areas_m2() > 0)
    expected = 4 * np.pi * grid.radius_m**2
    assert np.isclose(grid.cell_areas_m2().sum(), expected, rtol=1e-14)


def test_seed_streams_are_semantic_and_order_independent():
    baseline = {s.name: s.digest_sha256 for s in derive_seed_streams()}
    extended = {s.name: s.digest_sha256 for s in derive_seed_streams(
        ("plate_mosaic", "continental_blocks", "coastline", "land_relief", "future_unrelated"))}
    assert all(extended[name] == digest for name, digest in baseline.items())
    assert len(set(baseline.values())) == len(baseline)


def test_canonical_generator_is_repeatable_and_contract_valid():
    first = generate_initial_world()
    second = generate_initial_world()
    one = validate_initial_world(first)
    two = validate_initial_world(second)
    assert one == two
    assert one["result"] == "PASS_WITH_UNKNOWN"
    assert one["t0_ma"] == 210.0
    assert one["grid_shape"] == [180, 360]
    assert 0.25 <= one["land_fraction_area_weighted"] <= 0.35
    assert 0.80 <= one["dominant_component_share_of_land"] <= 0.95
    assert one["connected_land_component_count"] == 5
    assert one["dominant_component_latitudinal_span_deg"] >= 60
    assert one["dominant_component_longitudinal_span_deg"] >= 120
    for key, value in first.arrays().items():
        assert np.array_equal(value, second.arrays()[key], equal_nan=True), key


def test_province_topography_and_unknown_masks_are_explicit():
    fields = generate_initial_world()
    land = fields.land_ocean_mask.astype(bool)
    assert set(np.unique(fields.province_class[land])).issubset({0, 1, 2, 3})
    assert np.all(fields.province_class[~land] == -2)
    assert np.all(fields.elevation_support_mask == land)
    assert np.isfinite(fields.land_surface_elevation_m[land]).all()
    assert np.isnan(fields.land_surface_elevation_m[~land]).all()
    assert np.all(fields.bathymetry_unknown_mask == ~land)
    for mask in (fields.plate_motion_unknown_mask, fields.deep_unknown_mask,
                 fields.climate_unknown_mask, fields.hydrology_unknown_mask):
        assert mask.all()
    result = validate_initial_world(fields)
    assert result["drainage_ready_terrain_support"] == "PASS"
    assert result["local_sink_count_diagnostic_only"] >= 0
    assert "flow network" in result["drainage_interpretation"]


def test_alternate_seed_sensitivity_is_noncanonical_and_structurally_valid():
    alt = generate_initial_world(seed_root_material=b"ARCANA:R6:INITIAL_WORLD:SENSITIVITY:TEST")
    result = validate_initial_world(alt)
    assert result["result"] == "PASS_WITH_UNKNOWN"
    assert alt.metadata["canonical_seed"] is False
    canonical = generate_initial_world()
    assert alt.metadata["seed_root_sha256"] != canonical.metadata["seed_root_sha256"]
    assert not np.array_equal(alt.land_ocean_mask, canonical.land_ocean_mask)


def test_deterministic_payload_and_r6_state_store_round_trip(tmp_path):
    fields = generate_initial_world()
    payload = _deterministic_npz(fields.arrays())
    assert sha256(payload).hexdigest() == sha256(_deterministic_npz(fields.arrays())).hexdigest()
    with np.load(__import__("io").BytesIO(payload), allow_pickle=False) as z:
        assert set(z.files) == set(fields.arrays())
        assert np.array_equal(z["land_ocean_mask"], fields.land_ocean_mask)
        assert np.array_equal(z["land_surface_elevation_m"], fields.land_surface_elevation_m, equal_nan=True)
    payload_sha = sha256(payload).hexdigest()
    identity = {"dependencies": {"test": "a" * 64}, "grid": fields.grid.metadata(),
                "payload_sha256": payload_sha, "runtime_identity": {"test": "fixture"}}
    states, anchor, provenance, _, _, _ = _make_states(fields, payload_sha, identity)
    store = HistoryStore(tmp_path / "history")
    store.append_provenance(provenance)
    for state in states:
        store.append_state(state)
    store.append_temporal(anchor)
    reopened = HistoryStore(tmp_path / "history")
    assert {str(s.state_id) for s in reopened.states()} == {str(s.state_id) for s in states}
    row = reopened.read_temporal(anchor.record_id)
    assert row["role"] == "REFINEMENT_ANCHOR"
    assert set(row["domain_ids"]) == {"physical_geography", "land_ocean", "province_state", "topography"}
    assert not ({"deep", "climate", "hydrology"} & set(row["domain_ids"]))


def test_canonical_package_rejects_false_dependencies_and_unknown_numeric_values():
    package = {
        "schema": "ARCANA_R6_CANONICAL_INITIAL_STATE_PACKAGE_V1",
        "r6_global_t0_ma": 210.0,
        "states": [
            {"domain": "physical_geography", "support_class": "DERIVED_SUPPORTED", "payload_ref": "sha256:x"},
            {"domain": "land_ocean", "support_class": "DERIVED_SUPPORTED", "payload_ref": "sha256:x"},
            {"domain": "province_state", "support_class": "DERIVED_SUPPORTED", "payload_ref": "sha256:x"},
            {"domain": "topography", "support_class": "DERIVED_SUPPORTED", "payload_ref": "sha256:x"},
            {"domain": "deep", "support_class": "UNKNOWN", "payload_ref": None},
        ],
        "unknown_domains": ["deep", "climate", "hydrology", "bathymetry", "tectonic_kinematics"],
        "materialized_payload": {"sha256": "a" * 64, "bytes": 1},
        "r5_runtime_dependency": False,
        "a1_runtime_dependency": False,
        "simulation1_trajectory_dependency": False,
        "scientific_forward_simulation_executed": False,
        "provider_acquisition_executed": False,
        "p7q_reopened": False,
        "physical_soil_created": False,
        "scientific_authority_register_mutated": False,
        "execution_indexes_mutated": False,
        "current_state_updated": False,
    }
    _validate_canonical_package(package)
    invalid = dict(package, a1_runtime_dependency=True)
    with pytest.raises(ValueError, match="dependency"):
        _validate_canonical_package(invalid)
    invalid = dict(package, states=[{"domain": "deep", "support_class": "UNKNOWN",
                                    "payload_ref": "payload://fake-number"}])
    with pytest.raises(ValueError, match="UNKNOWN"):
        _validate_canonical_package(invalid)


def test_canonical_package_markdown_uses_manifest_payload_path():
    package = {
        "canonical_status": "CANONICAL_R6_INITIAL_PHYSICAL_STATE__UNKNOWN_DOMAINS_PRESERVED",
        "run_id": "r6run_test", "history_id": "r6hist_test", "global_base_branch_id": "r6branch_test",
        "grid": {"grid_id": "R6_GLOBAL_GEOGRAPHY_1DEG_V1"},
        "materialized_payload": {"relative_path": "../external/run/payload.npz",
                                 "sha256": "a" * 64, "bytes": 123},
        "states": [],
        "first_post_t0_consumer_adjudication": {"selected_domain": "PHYSICAL_WORLD_EVOLUTION",
                                                "missing": ["plate-motion-law"]},
        "r5_runtime_dependency": False, "a1_runtime_dependency": False,
        "simulation1_trajectory_dependency": False,
        "scientific_forward_simulation_executed": False,
        "provider_acquisition_executed": False, "p7q_reopened": False,
        "physical_soil_created": False,
    }
    text = _package_markdown(package, "b" * 64)
    assert "../external/run/payload.npz" in text
    assert "plate-motion-law" in text


def _diagnostic_region(fields):
    """Pick first maximum-score 4x4 parent window with both land and ocean."""
    land = fields.land_ocean_mask.astype(bool)
    best = None
    for row in range(88, 100):
        for col in range(0, 356):
            window = land[row:row + 4, col:col + 4]
            if not (window.any() and (~window).any()):
                continue
            provinces = fields.province_class[row:row + 4, col:col + 4][window]
            coastal = int(fields.coastline_mask[row:row + 4, col:col + 4].sum())
            variety = len(np.unique(provinces))
            terrain = fields.land_surface_elevation_m[row:row + 4, col:col + 4]
            relief = float(np.nanstd(terrain))
            score = (coastal, variety, relief, -row, -col)
            if best is None or score > best[0]:
                best = (score, row, col)
    assert best is not None
    _, row, col = best
    return Region(row - 90.0, col - 180.0, row - 86.0, col - 176.0)


def _materialize(fields, region, resolution):
    return materialize_region(
        fields, region, resolution,
        parent_history_id="r6hist_fixture", parent_state_id="r6state_fixture")


def _latent(fields):
    return build_latent_state(fields, world_id="r6world_fixture",
                              parent_history_id="r6hist_fixture",
                              parent_state_id="r6state_fixture",
                              parent_payload_sha256="a" * 64)


def _materialize_latent(fields, latent, region, resolution):
    return materialize_region(
        fields, region, resolution, parent_history_id="r6hist_fixture",
        parent_state_id="r6state_fixture", latent_state=latent)


def test_regional_refinement_reconstructs_canonical_terrain_without_raster_sampling():
    fields = generate_initial_world()
    region = _diagnostic_region(fields)
    result = _materialize(fields, region, 1.0)
    row0 = int(region.south_deg + 90)
    col0 = int(region.west_deg + 180)
    np.testing.assert_array_equal(
        result["fields"]["land_ocean_mask"],
        fields.land_ocean_mask[row0:row0 + 4, col0:col0 + 4])
    np.testing.assert_array_equal(
        result["fields"]["land_surface_elevation_m"],
        fields.land_surface_elevation_m[row0:row0 + 4, col0:col0 + 4])
    assert result["descriptor"]["classification"] == "DERIVED_REFINEMENT_BRANCH"
    assert result["descriptor"]["field_resolution_classes"]["land_ocean_mask"] == "COARSE_ONLY"


def test_regional_seed_and_generation_are_independent_of_order_and_partition():
    fields = generate_initial_world()
    region = _diagnostic_region(fields)
    mid = (region.west_deg + region.east_deg) / 2
    west = Region(region.south_deg, region.west_deg, region.north_deg, mid)
    east = Region(region.south_deg, mid, region.north_deg, region.east_deg)
    together = _materialize(fields, region, 0.25)
    east_first = _materialize(fields, east, 0.25)
    west_second = _materialize(fields, west, 0.25)
    repeated = _materialize(fields, region, 0.25)
    np.testing.assert_array_equal(
        together["fields"]["land_surface_elevation_m"],
        repeated["fields"]["land_surface_elevation_m"])
    np.testing.assert_array_equal(
        together["fields"]["land_surface_elevation_m"],
        np.concatenate((west_second["fields"]["land_surface_elevation_m"],
                        east_first["fields"]["land_surface_elevation_m"]), axis=1))
    for name in ("land_ocean_mask", "coastline_mask", "plate_id", "crust_class",
                 "boundary_class", "province_class"):
        np.testing.assert_array_equal(
            together["fields"][name],
            np.concatenate((west_second["fields"][name],
                            east_first["fields"][name]), axis=1))


def test_refinement_resolutions_preserve_coarse_categories_unknowns_and_parent_mean():
    fields = generate_initial_world()
    region = _diagnostic_region(fields)
    for resolution, size in ((1.0, 4), (0.25, 16), (0.1, 40)):
        result = _materialize(fields, region, resolution)
        assert result["fields"]["land_ocean_mask"].shape == (size, size)
        assert result["fields"]["land_surface_elevation_m"].shape == (size, size)
        assert result["descriptor"]["promotion"] == "NONE__NON_CANONICAL_DIAGNOSTIC_BRANCH"
        assert np.isnan(result["fields"]["land_surface_elevation_m"][
            ~result["fields"]["elevation_support_mask"]]).all()
        if resolution == 0.25:
            fine = result["fields"]["land_surface_elevation_m"].reshape(4, 4, 4, 4)
            coarse = fields.land_surface_elevation_m[
                int(region.south_deg + 90):int(region.north_deg + 90),
                int(region.west_deg + 180):int(region.east_deg + 180)]
            # A technical same-process macro-consistency diagnostic, not a
            # scientific accuracy tolerance or empirical terrain claim.
            finite = np.isfinite(fine)
            fine_sum = np.where(finite, fine, 0.0).sum(axis=(1, 3))
            fine_count = finite.sum(axis=(1, 3))
            fine_mean = np.divide(fine_sum, fine_count, where=fine_count > 0,
                                  out=np.full(fine_sum.shape, np.nan))
            land_coarse = np.isfinite(coarse)
            difference = np.max(np.abs(fine_mean[land_coarse] - coarse[land_coarse]))
            assert difference <= 25.0
        unknown_result = materialize_region(
            fields, region, resolution, parent_history_id="h", parent_state_id="s",
            requested_fields=("climate", "hydrology", "deep", "plate_motion", "bathymetry"))
        assert unknown_result["fields"]["bathymetry_unknown_mask"].shape == (size, size)
        assert unknown_result["fields"]["bathymetry_unknown_mask"].any()
        for name in ("plate_motion_unknown_mask", "deep_unknown_mask",
                     "climate_unknown_mask", "hydrology_unknown_mask"):
            assert unknown_result["fields"][name].all()


def test_latent_identity_is_deterministic_and_regenerates_global_categories_exactly():
    fields = generate_initial_world()
    first, second = _latent(fields), _latent(fields)
    assert first.sha256 == second.sha256
    assert first.canonical_bytes() == second.canonical_bytes()
    land, coast = reconstruct_land_geometry(
        fields, first, fields.grid.lat_centers_deg,
        fields.grid.lon_centers_deg, base_grid_centers=True)
    np.testing.assert_array_equal(land, fields.land_ocean_mask.astype(bool))
    np.testing.assert_array_equal(coast, fields.coastline_mask.astype(bool))


def test_latent_refinement_has_subgrid_coast_and_multiscale_parent_conservative_terrain():
    fields = generate_initial_world()
    latent = _latent(fields)
    region = _diagnostic_region(fields)
    parent_land = fields.land_ocean_mask.astype(bool)
    row0, col0 = int(region.south_deg + 90), int(region.west_deg + 180)
    for resolution, size in ((1.0, 4), (0.25, 16), (0.1, 40)):
        result = _materialize_latent(fields, latent, region, resolution)
        land = result["fields"]["land_ocean_mask"].astype(bool)
        assert land.shape == (size, size)
        assert result["descriptor"]["latent_geometry_sha256"] == latent.sha256
        assert result["descriptor"]["parent_world_id"] == latent.world_id
        assert result["descriptor"]["latent_geometry_schema"] == latent.schema
        assert result["descriptor"]["provenance"][
            "canonical_parent_payload_sha256"] == latent.parent_payload_sha256
        assert result["descriptor"]["provenance"]["refinement_branch_only"] is True
        assert result["descriptor"]["validation"]["land_geometry"][
            "parent_majority_violations"] == 0
        if resolution == 0.25:
            fractions = land.reshape(4, 4, 4, 4).mean(axis=(1, 3))
            coarse = parent_land[row0:row0 + 4, col0:col0 + 4]
            assert np.array_equal(fractions >= 0.5, coarse)
            assert np.any((fractions > 0) & (fractions < 1))
            topo = result["fields"]["land_surface_elevation_m"]
            assert result["descriptor"]["validation"]["topography"][
                "fine_spectrum_added"] is True
            assert result["descriptor"]["validation"]["topography"][
                "fine_detail_rms_m"] > 1.0
            assert result["descriptor"]["validation"]["topography"][
                "parent_mean_max_error_m"] <= PARENT_MEAN_TOLERANCE_M
            assert np.isfinite(topo[land]).all()
            coarse_topography = fields.land_surface_elevation_m[
                row0:row0 + 4, col0:col0 + 4]
            for i in range(4):
                for j in range(4):
                    if np.isfinite(coarse_topography[i, j]):
                        child = topo[i * 4:(i + 1) * 4, j * 4:(j + 1) * 4]
                        valid = np.isfinite(child)
                        assert abs(float(child[valid].mean()) -
                                   float(coarse_topography[i, j])) <= PARENT_MEAN_TOLERANCE_M
        if resolution == 0.1:
            unknown = _materialize_latent(
                fields, latent, region, resolution)["descriptor"]["field_resolution_classes"]
            assert unknown["province_class"] == "COARSE_SUPPORT_ON_FINE_GRID"


def test_latent_refinement_preserves_unknowns_and_reports_field_specific_support():
    fields = generate_initial_world()
    latent = _latent(fields)
    region = _diagnostic_region(fields)
    result = materialize_region(
        fields, region, 0.25, parent_history_id="r6hist_fixture",
        parent_state_id="r6state_fixture", latent_state=latent,
        requested_fields=("land_ocean_mask", "coastline_mask", "province_class",
                          "land_surface_elevation_m", "bathymetry", "plate_motion",
                          "deep", "climate", "hydrology"))
    classes = result["descriptor"]["field_resolution_classes"]
    assert classes["land_ocean_mask"] == "STRUCTURALLY_REFINABLE"
    assert classes["coastline_mask"] == "STRUCTURALLY_REFINABLE"
    assert classes["province_class"] == "COARSE_SUPPORT_ON_FINE_GRID"
    assert classes["land_surface_elevation_m"] == "MULTISCALE_REFINABLE"
    assert result["fields"]["bathymetry_unknown_mask"][
        ~result["fields"]["land_ocean_mask"].astype(bool)].all()
    for field in ("plate_motion", "deep", "climate", "hydrology"):
        assert result["fields"][f"{field}_unknown_mask"].all()
    assert result["descriptor"]["promotion"] == "NONE__NON_CANONICAL_DIAGNOSTIC_BRANCH"
    assert result["descriptor"]["forward_simulation"] is False


def test_latent_regional_generation_is_order_and_tile_independent_with_coast_seams():
    fields = generate_initial_world()
    latent = _latent(fields)
    region = _diagnostic_region(fields)
    mid = (region.west_deg + region.east_deg) / 2
    west = Region(region.south_deg, region.west_deg, region.north_deg, mid)
    east = Region(region.south_deg, mid, region.north_deg, region.east_deg)
    together = _materialize_latent(fields, latent, region, 0.25)
    east_first = _materialize_latent(fields, latent, east, 0.25)
    west_second = _materialize_latent(fields, latent, west, 0.25)
    for name in ("land_ocean_mask", "coastline_mask", "plate_id", "crust_class",
                 "boundary_class", "province_class", "land_surface_elevation_m"):
        merged = np.concatenate((west_second["fields"][name],
                                 east_first["fields"][name]), axis=1)
        np.testing.assert_array_equal(together["fields"][name], merged)
