from __future__ import annotations

from dataclasses import replace

import pytest

import arcana_worldsim.r6.integrated_geological_microdomain as micro
from test_r6_tectonic_deep_pilot import _state


def _synthetic_inputs():
    base = _state()
    state_a = replace(base, materials=tuple(replace(
        material,
        role_id=("CONTINENTAL_CRUST_REFERENCE" if material.role_id == "CRUST"
                 else "LITHOSPHERIC_MANTLE_REFERENCE"),
    ) for material in base.materials))
    state_b = replace(state_a, width_m=state_a.width_m * 1.02, initial_width_m=state_a.initial_width_m * 1.02)
    digest_a = micro._state_digest(state_a)
    digest_b = micro._state_digest(state_b)
    rows = []
    for support, trajectory, seq, state, digest in (
            ("R6G1D-R091-C028", "DIRECT-TEST-C028", 12, state_a, digest_a),
            ("R6G1D-R091-C029", "DIRECT-TEST-C029", 0, state_b, digest_b)):
        rows.append((state, {
            "support_id": support, "trajectory_id": trajectory, "sequence": seq,
            "time_s": 0.0, "state_payload_sha256": digest,
            "frozen_euler_extension_m_per_year": 0.11467052868814648,
            "archive_path": "SYNTHETIC_FIXTURE_ONLY", "archive_sha256": micro.ARCHIVE_SHA256,
            "state_class": "DIAGNOSTIC_OBSERVATION",
        }))
    return rows


def test_two_synthetic_support_call_paths_share_one_run_without_inferred_lateral_edge(monkeypatch):
    loaded = _synthetic_inputs()
    original_payloads = [state.payload() for state, _ in loaded]
    monkeypatch.setattr(micro, "load_microdomain_inputs", lambda _path: (loaded, micro.ARCHIVE_SHA256))

    result = micro.run_integrated_microdomain("synthetic-fixture", duration_years=3.0)

    assert result["scope"] == "NONCANONICAL_TWO_COLUMN_ENGINEERING_MICRODOMAIN"
    assert result["topology"]["lateral_interface_count"] == 0
    assert result["topology"]["lateral_deep_transport"] == "DISABLED_NO_INFERRED_CONTINUITY"
    assert result["topology"]["vertical_interface_count"] == 144
    assert set(result["supports"]) == {"R6G1D-R091-C028", "R6G1D-R091-C029"}
    assert all(len(row["material_volumes"]) == 73 for row in result["supports"].values())
    assert all(len(row["initial_material_volumes"]) == 73 for row in result["supports"].values())
    assert all(row["initial_state"]["temperature_k"] == original_payloads[i]["temperature_k"]
               for i, row in enumerate(result["supports"].values()))
    assert [state.payload() for state, _ in loaded] == original_payloads
    assert len(result["steps"]) == 3
    assert all(len(row["supports"]) == 2 for row in result["steps"])

    # A declared synthetic modal/material interface transfers Deep inventory,
    # while no heat or radiogenic power is silently injected into that ledger.
    assert result["deep_ledger"]["source_j"] == 0.0
    assert result["deep_ledger"]["loss_j"] == 0.0
    assert result["deep_ledger"]["thermal_to_deep_transfer_j"] == 0.0
    assert result["deep_ledger"]["conservation_residual_j"] == pytest.approx(0.0, abs=1e-5)
    all_transfers = [edge for step in result["steps"] for edge in step["deep"]["transfers"]]
    assert any(edge["transfer_a_to_b_j"] != 0.0 for edge in all_transfers)
    assert all(row["is_deep_energy_transfer"] is False
               for support in result["supports"].values()
               for row in support["final_thermal_diagnostics"]["conductive_interfaces"])
    assert all(cell["geological_inventory_dfeu"] is None
               for support in result["supports"].values()
               for cell in support["material_volumes"])


def test_deformation_updates_geometry_without_creating_deep_inventory(monkeypatch):
    loaded = _synthetic_inputs()
    monkeypatch.setattr(micro, "load_microdomain_inputs", lambda _path: (loaded, micro.ARCHIVE_SHA256))
    result = micro.run_integrated_microdomain("synthetic-fixture", duration_years=2.0,
                                              synthetic_mobility_per_year=0.0)
    assert result["deep_ledger"]["initial_inventory_j"] == result["deep_ledger"]["final_inventory_j"]
    assert result["deep_ledger"]["conservation_residual_j"] == 0.0
    for support in result["supports"].values():
        assert support["final_state"]["width_m"] > support["initial"]["width_m"]
        assert support["final_state"]["lithosphere_m"] < support["initial"]["lithosphere_m"]
        assert support["column_volume_sum_m3_final"] == pytest.approx(
            support["column_volume_sum_m3_initial"], rel=2e-13
        )
        assert support["state_payload_sha256_initial"] != support["state_payload_sha256_final"]
        assert all(cell["initial_deep_inventory_j"] == cell["deep_inventory_j"]
                   for cell in support["material_volumes"])
        assert any(cell["synthetic_zeta_accessibility"] != cell["initial_synthetic_zeta_accessibility"]
                   for cell in support["material_volumes"])
        assert support["initial_thermal_diagnostics"]["deep_energy_source_from_thermal"] == 0.0
        assert support["final_thermal_diagnostics"]["deep_energy_source_from_thermal"] == 0.0


def test_invalid_density_roles_and_unstable_deep_transport_fail_closed(monkeypatch):
    loaded = _synthetic_inputs()
    monkeypatch.setattr(micro, "load_microdomain_inputs", lambda _path: (loaded, micro.ARCHIVE_SHA256))
    with pytest.raises(ValueError, match="DENSITY_ROLE_SET_MISMATCH"):
        micro.run_integrated_microdomain("synthetic-fixture", synthetic_deep_density_by_role_j_m3={"CONTINENTAL_CRUST_REFERENCE": 1.0})
    with pytest.raises(ValueError, match="EXPLICIT_STEP_UNSTABLE"):
        micro.run_integrated_microdomain("synthetic-fixture", synthetic_mobility_per_year=100.0)
