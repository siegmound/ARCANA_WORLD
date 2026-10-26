from __future__ import annotations

import numpy as np
import pytest

fs = pytest.importorskip("fastscapelib")

from scripts.r6_fastscapelib_landscape_benchmark import (  # noqa: E402
    BASE_K,
    N_STEPS,
    run_landscape,
    synthetic_initial_topography,
)


def test_fastscapelib_runs_dynamic_route_bedrock_incision_and_fixed_outlet():
    initial, _, _ = synthetic_initial_topography()
    result = run_landscape(initial_elevation=initial)

    assert fs.__version__ == "0.3.0"
    assert np.isfinite(result["elevation_m"]).all()
    assert result["diagnostics"]["lowered_nodes"] > 0
    assert result["diagnostics"]["topographic_lowering_volume_diagnostic_m3"] > 0
    assert result["diagnostics"]["deposition_supported"] is False
    assert np.array_equal(result["elevation_m"][-1, :], initial[-1, :])
    assert np.max(result["drainage_area_m2"]) > 0


def test_synthetic_erodibility_change_changes_incision():
    initial, _, _ = synthetic_initial_topography()
    low = run_landscape(k_coef=BASE_K / 2, initial_elevation=initial)
    high = run_landscape(k_coef=BASE_K * 2, initial_elevation=initial)

    low_volume = low["diagnostics"]["topographic_lowering_volume_diagnostic_m3"]
    high_volume = high["diagnostics"]["topographic_lowering_volume_diagnostic_m3"]
    assert high_volume > low_volume > 0
    assert not np.array_equal(high["elevation_m"], low["elevation_m"])


def test_elevation_checkpoint_restart_matches_continuous_run():
    initial, _, _ = synthetic_initial_topography()
    continuous = run_landscape(k_coef=BASE_K, steps=N_STEPS,
                               initial_elevation=initial)
    first = run_landscape(k_coef=BASE_K, steps=N_STEPS // 2,
                          initial_elevation=initial)
    resumed = run_landscape(k_coef=BASE_K, steps=N_STEPS - N_STEPS // 2,
                            initial_elevation=first["elevation_m"])

    np.testing.assert_array_equal(resumed["elevation_m"], continuous["elevation_m"])


def test_nonfinite_and_invalid_checkpoint_fields_fail_closed():
    initial, _, _ = synthetic_initial_topography()
    invalid = initial.copy()
    invalid[1, 1] = np.nan
    with pytest.raises(ValueError, match="CHECKPOINT_TOPOGRAPHY_INVALID"):
        run_landscape(initial_elevation=invalid)
    with pytest.raises(ValueError, match="EROSION_CONFIGURATION_INVALID"):
        run_landscape(k_coef=-1.0, initial_elevation=initial)
