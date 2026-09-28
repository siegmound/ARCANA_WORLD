import hashlib
import json
from pathlib import Path

import numpy as np

from arcana_worldsim.r6.t0_materialization.b_pangaea_v2 import (
    _array_sha256,
    close_ocean_surface,
    compose_ocean_surface,
    gdh1_water_loaded_depth_m,
)

ROOT = Path(__file__).resolve().parents[1]


def test_b_v2_materialization_bounds_and_field_package_hashes():
    report = json.loads((ROOT / "R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json").read_text())
    package = ROOT / report["field_package_path"]
    assert hashlib.sha256(package.read_bytes()).hexdigest() == report["field_package_sha256"]
    with np.load(package, allow_pickle=False) as fields:
        age = fields["oceanic_lithosphere_age_ma"]
        residual = fields["ocean_surface_authorial_residual_m"]
        land = fields["physical_crust_domain_id"] != 1
        assert age.shape == (180, 360) and np.isnan(age[land]).all()
        assert np.nanmin(age) == 0.0 and np.nanmax(age) <= 160.0
        assert abs(report["derived_fields"]["oceanic_age"]["area_weighted_ocean_median_ma"] - 70) < 1e-8
        assert abs(report["derived_fields"]["ocean_authorial_residual_bathymetry"]["observed_area_weighted_ocean_rms_m"] - 500) < 1e-8
        assert abs(report["derived_fields"]["ocean_authorial_residual_bathymetry"]["observed_area_weighted_ocean_mean_m"]) < 1e-7
        assert np.nanmax(np.abs(residual)) <= 1200.0
        for name, value in fields.items():
            assert _array_sha256(value) == report["normalized_field_hashes"][name]


def test_b_v2_domains_and_runtime_boundary_are_candidate_only():
    report = json.loads((ROOT / "R6_T0_B_PANGAEA_LIKE_V2_MATERIALIZATION_REPORT.json").read_text())
    shares = report["thermal_domain_area_fractions"]
    assert 0.50 <= shares["COLD_STABLE"] <= 0.60
    assert 0.30 <= shares["NORMAL"] <= 0.40
    assert 0.08 <= shares["HOT_EXTENDED"] <= 0.15
    assert report["authorial_realization_id"] == "B_PANGAEA_LIKE_LATE_TRIASSIC_v2"
    assert report["canonical_status"] == "CANDIDATE_UNTIL_MATERIALIZATION_VALIDATION"
    assert report["pre_orbdata_outputs"]["fegs_generated"] == 0
    assert report["runtime_manifest_candidates"]["runtime_authorized"] is False
    assert report["governance"]["dt_or_t1_created"] is False


def test_gdh1_exact_relation_branch_behavior_and_monotonicity():
    ages = np.array([0.0, 19.999999, 20.0, 20.000001, 55.0, 70.0, 160.0])
    depths = gdh1_water_loaded_depth_m(ages)
    expected = np.where(ages < 20.0, 2600.0 + 365.0 * np.sqrt(ages),
                        5651.0 - 2473.0 * np.exp(-0.0278 * ages))
    assert np.array_equal(depths, expected)
    assert np.all(np.diff(depths) > 0.0)
    # The prescribed coefficients have a small finite jump at the branch.
    young_limit = 2600.0 + 365.0 * np.sqrt(20.0)
    old_at_20 = 5651.0 - 2473.0 * np.exp(-0.0278 * 20.0)
    assert abs((old_at_20 - young_limit) - 0.408645584509) < 1e-8
    assert np.isnan(gdh1_water_loaded_depth_m(np.array([np.nan]))[0])


def test_surface_composition_preserves_land_and_unknown_support():
    ages = np.array([[0.0, 20.0, np.nan], [70.0, 160.0, 55.0]])
    residual = np.array([[10.0, -20.0, 30.0], [40.0, 50.0, -60.0]])
    land_elevation = np.array([[np.nan, np.nan, np.nan], [np.nan, np.nan, 123.25]])
    ocean = np.array([[True, True, True], [True, True, False]])
    thermal, total, unknown = compose_ocean_surface(ages, residual, land_elevation, ocean)
    depth = gdh1_water_loaded_depth_m(ages)
    assert thermal[0, 0] == -depth[0, 0]
    assert total[0, 0] == thermal[0, 0] + residual[0, 0]
    assert np.isnan(thermal[0, 2]) and np.isnan(total[0, 2]) and unknown[0, 2]
    assert np.isnan(thermal[1, 2]) and total[1, 2] == land_elevation[1, 2]
    assert not unknown[1, 2]


def test_versioned_ocean_surface_closure_replay_preserves_parent_components(tmp_path):
    parent_manifest = ROOT / "R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json"
    parent = json.loads(parent_manifest.read_text(encoding="utf-8"))
    (tmp_path / parent_manifest.name).write_bytes(parent_manifest.read_bytes())
    source = ROOT / parent["field_package_path"]
    (tmp_path / source.name).write_bytes(source.read_bytes())

    first = close_ocean_surface(tmp_path)
    first_package_hash = first["materialized"]["field_package_sha256"]
    second = close_ocean_surface(tmp_path)
    assert second["materialized"]["field_package_sha256"] == first_package_hash
    assert hashlib.sha256((tmp_path / second["materialized"]["field_package_path"]).read_bytes()).hexdigest() == first_package_hash
    assert first["component_lineage"]["age_field"]["sha256_before_after"] == [
        "aed3d311296947aad0f4cc041cfbb1b2784763704b23b1a3e746d2079a607dc2"] * 2
    assert first["component_lineage"]["authorial_residual"]["sha256_before_after"] == [
        "315078fc021637823399a8a96272dcfc69d7746a3098064042119d7453755cfc"] * 2
    assert first["component_lineage"]["land_component"]["sha256_before_after"] == [
        "79b8a50159c5f74b94a0e0f4d856336a829c9e1d1cf9ee145ba0daac97f96c45"] * 2
    assert first["statistics"]["known_ocean_elevation_cells"] == first["statistics"]["ocean_cells"]
    assert first["statistics"]["ocean_cells_at_or_above_zero_datum"] == 0
    assert first["statistics"]["ocean_coverage_fraction"] == 1.0
    assert first["statistics"]["residual_hard_cap_abs_m"] <= 1200.0
    assert first["authority"]["thermal_component"] == "SPECIALIST_DERIVED_T0"
    assert first["authority"]["authorial_residual"] == "AUTHORIAL_T0_PRIMITIVE"
    assert first["authority"]["total_surface"] == "SPECIALIST_DERIVED_T0"
    assert first["authority"]["orbdata_generated_bathymetry"] is False
    assert first["model_form_uncertainty"]["axis"] == "OCEAN_PLATE_COOLING_MODEL_FORM"
    assert first["pre_orbdata_impact"]["PRE_ORBDATA_ready"] is False
    assert first["governance"]["age_regenerated"] is False
    with np.load(tmp_path / first["materialized"]["field_package_path"], allow_pickle=False) as fields:
        ocean = fields["physical_crust_domain_id"] == 1
        assert _array_sha256(fields["physical_crust_domain_id"]) == first[
            "component_lineage"]["unchanged_parent_field_hashes"]["physical_crust_domain_id"]
        assert np.isnan(fields["ocean_thermal_isostatic_elevation_m"][~ocean]).all()
        assert np.array_equal(fields["total_surface_elevation_m"][~ocean],
                              fields["canonical_land_surface_elevation_m"][~ocean])
        assert np.all(fields["total_surface_elevation_m"][ocean] < 0.0)
