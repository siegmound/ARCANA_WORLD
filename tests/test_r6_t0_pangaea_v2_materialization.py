import hashlib
import json
from pathlib import Path

import numpy as np

from arcana_worldsim.r6.t0_materialization.b_pangaea_v2 import _array_sha256

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
