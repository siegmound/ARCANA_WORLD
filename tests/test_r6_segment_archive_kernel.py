from __future__ import annotations

import hashlib

import pytest

pytest.importorskip("numpy", reason="NumPy unavailable; native reduced-kernel observer integration not executable")

from arcana_worldsim.r6.functional_development import NodeMaterial, ReducedState
from arcana_worldsim.r6 import int3_eng10k as eng
from arcana_worldsim.r6.segment_archive import SegmentArchiveWriter, validate_segment_archive


def _state() -> ReducedState:
    n = 73
    crust = NodeMaterial("SYNTHETIC_CRUST", 3.0, 2800.0, 1000.0, 1e-6)
    mantle = NodeMaterial("SYNTHETIC_MANTLE", 4.0, 3300.0, 1100.0, 0.0)
    materials = tuple(crust if i < 26 else mantle for i in range(n))
    coordinate = tuple(i / (n - 1) for i in range(n))
    return ReducedState(
        time_s=0.0, initial_width_m=100_000.0, width_m=100_000.0,
        initial_crust_m=28_000.0, initial_lithosphere_m=80_000.0,
        crust_m=28_000.0, lithosphere_m=80_000.0, beta=1.0,
        accumulated_strain=0.0, crust_fraction=0.35,
        material_coordinate=coordinate,
        temperature_k=tuple(280.0 + i * 10.0 for i in range(n)),
        materials=materials, surface_temperature_k=280.0,
        base_temperature_k=1000.0,
    )


def _provenance() -> dict:
    digest = hashlib.sha256(b"synthetic test identity").hexdigest()
    return {"identity_status": "SYNTHETIC_TEST_ONLY", "source_commit": "TEST_ONLY",
            "source_composite_sha256": digest, "configuration_sha256": digest,
            "provider_identities": {"provider": digest}, "input_identities": {"input": digest}}


def test_actual_kernel_observations_export_without_changing_final_state_or_diagnostics(tmp_path):
    initial = _state()
    duration_years = 1000.0
    baseline_final, baseline_diagnostics = eng.advance_with_bounded_samples(
        initial, support_id="TEST-C028", duration_years=duration_years,
        extension_velocity_m_per_year=0.11467052868814648,
        resolution_factor=0.0005,
    )
    writer = SegmentArchiveWriter(tmp_path / "kernel-segment", segment_id="kernel-fixture",
                                  provenance=_provenance(), expected_trajectory_count=1)
    observed = []
    with writer.trajectory(trajectory_id="kernel-direct", support_id="TEST-C028",
                           trajectory_kind="DIRECT", resolution_factor=0.0005,
                           start_time_s=initial.time_s,
                           requested_duration_s=duration_years * eng.SECONDS_PER_YEAR):
        final, diagnostics = eng.advance_with_bounded_samples(
            initial, support_id="TEST-C028", duration_years=duration_years,
            extension_velocity_m_per_year=0.11467052868814648,
            resolution_factor=0.0005,
            state_observer=lambda value: (observed.append(value), writer.observe(value)),
        )
        writer.complete_trajectory(final, integration_substeps=diagnostics["integration_substeps"])
    writer.finalize()

    assert final == baseline_final
    assert diagnostics == baseline_diagnostics
    assert len(observed) == diagnostics["integration_substeps"] + 1
    assert validate_segment_archive(tmp_path / "kernel-segment")["state_count"] == len(observed)
