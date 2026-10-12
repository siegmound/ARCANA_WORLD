from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from arcana_worldsim.r6.functional_development import NodeMaterial, T0Profile
from arcana_worldsim.r6.functional_development import (
    initial_reduced_state, pure_shear_thermal_step, state_from_payload,
)
from arcana_worldsim.r6.checkpoint import CheckpointEnvelope
from arcana_worldsim.r6.forcing import ForcingRecord
from arcana_worldsim.r6.replay import ReplayRecipe
from arcana_worldsim.r6.state import DomainStateEnvelope
from arcana_worldsim.r6.int0a_pipeline import (
    IntegrationContractError,
    advance_pair,
    build_fixture_pair_plan,
    capture_numerical_step_samples,
    trajectory_document,
    write_candidate_bundle,
)

ROOT = Path(__file__).resolve().parents[1]
_HASHES = {"source_identity_sha256": "1" * 64,
           "kinematics_semantic_identity_sha256": "2" * 64,
           "kinematics_artifact_sha256": "3" * 64,
           "mapping_sha256": "4" * 64,
           "vector_partition_payload_sha256": "5" * 64,
           "b6n8n_field_package_sha256": "6" * 64,
           "b6n8n_index_sha256": "7" * 64,
           "event_eligibility_census_sha256": "8" * 64}


def _profile(support_id: str, offset: float = 0.0) -> T0Profile:
    crust = NodeMaterial("CRUST", 2.0, 3000.0, 1000.0, 0.0)
    mantle = NodeMaterial("MANTLE", 2.5, 3200.0, 1100.0, 0.0)
    return T0Profile(support_id, "CONTINENTAL_NORMAL", "REFERENCE_ENGINEERING_SCENARIO",
                     10.0, 20.0, 280.0, 300.0, 0.05,
                     (0.0, 10.0, 20.0), (280.0 + offset, 290.0 + offset, 300.0 + offset),
                     (crust, crust, mantle), ("CRUST", "MANTLE"),
                     {"source": "SYNTHETIC_FIXTURE"})


def _side(plate_id: int, support_id: str, row: int, column: int,
          profile: T0Profile | None = None) -> dict:
    profile = profile or _profile(support_id)
    return {"support_id": support_id, "plate_id": plate_id,
            "row": row, "column": column, "support_class": profile.support_class,
            "admitted_continental_binding": True,
            "t0_profile": {"scenario_id": profile.scenario_id,
                "crust_m": profile.crust_m, "model_base_m": profile.model_base_m,
                "surface_temperature_k": profile.temperature_k[0],
                "surface_heat_flow_w_m2": profile.surface_heat_flow_w_m2,
                "z_m": list(profile.z_m), "temperature_k": list(profile.temperature_k),
                "material_roles": list(profile.material_roles),
                "material_properties": [vars(item) for item in profile.materials],
                "support_lineage": {"support_id": support_id}}}


def _assessment(ux: float = 0.02, profile_a: T0Profile | None = None) -> dict:
    selected = {"boundary_id": "TEST-EDGE-5-11", "ordered_plate_pair": [5, 11],
        "parent_grid_edge": {"row": 90, "column": 20, "axis": "EAST"},
        "SECTION_ELIGIBILITY": "ELIGIBLE", "SIGNED_EXTENSION": "EXTENSION",
        "junction_adjacent": False, "signed_Ux_m_per_year": ux,
        "velocity_components": {"normal_ab_xyz": [1.0, 0.0, 0.0],
                                "tangent_xyz": [0.0, 1.0, 0.0]},
        "sides_plate_a_then_plate_b": [
            _side(5, "TEST-CELL-5", 90, 20, profile_a),
            _side(11, "TEST-CELL-11", 90, 21)],}
    return {"stage": "T-F2B", "selected_ordered_plate_pair": [5, 11],
        "selected_boundary_id": selected["boundary_id"], "source_grid_radius_m": 6_371_000.0,
        "source_head": "a" * 40, "source_branch": "fixture/only",
        "no_world_history_access_or_publication": True, "canonical_state_changed": False,
        "fixture_marker": "SYNTHETIC_FIXTURE_ONLY",
        "edge_matrix": [selected], "kinematics_uncertainty": {"status": "FIXTURE_ONLY"},
        "pair_event_census": {"pair_id": "5:11", "eligibility": "ELIGIBLE_QUIESCENT",
            "scope_is_activation_authority": False},
        "mapping_join": {"mapping_sha256": "4" * 64},
        **_HASHES}


def test_pair_plan_binds_two_support_profiles_and_euler_forcing_to_existing_kernel():
    plan = build_fixture_pair_plan(_assessment())
    assert plan.support_ids == ("TEST-CELL-5", "TEST-CELL-11")
    assert tuple(profile.support_id for profile in plan.profiles) == plan.support_ids
    states, diagnostics = advance_pair(plan, duration_s=31_557_600.0,
                                       maximum_kinematic_fraction_per_substep=0.01)
    assert len(states) == len(diagnostics) == 2
    assert all(state.width_m > plan.initial_width_m for state in states)
    assert all(item["duration_s"] == 31_557_600.0 for item in diagnostics)


def test_upstream_forcing_and_profile_changes_change_downstream_kernel_input_or_output():
    base = build_fixture_pair_plan(_assessment(ux=0.02))
    more_forcing = build_fixture_pair_plan(_assessment(ux=0.04))
    base_states, _ = advance_pair(base, duration_s=31_557_600.0,
                                  maximum_kinematic_fraction_per_substep=0.01)
    forced_states, _ = advance_pair(more_forcing, duration_s=31_557_600.0,
                                    maximum_kinematic_fraction_per_substep=0.01)
    assert [s.width_m for s in base_states] != [s.width_m for s in forced_states]

    changed_profile = build_fixture_pair_plan(_assessment(
        ux=0.02, profile_a=_profile("TEST-CELL-5", offset=5.0)))
    changed_states, _ = advance_pair(changed_profile, duration_s=31_557_600.0,
                                     maximum_kinematic_fraction_per_substep=0.01)
    assert changed_states[0].temperature_k != base_states[0].temperature_k


def test_diagnostic_capture_records_initial_and_every_kernel_step_without_changing_endpoint():
    plan = build_fixture_pair_plan(_assessment())
    duration_s = 31_557_600.0
    captured, diagnostics, samples = capture_numerical_step_samples(
        plan, duration_s=duration_s,
        maximum_kinematic_fraction_per_substep=0.01,
    )
    ordinary, ordinary_diagnostics = advance_pair(
        plan, duration_s=duration_s,
        maximum_kinematic_fraction_per_substep=0.01,
    )

    assert {key: len(value) for key, value in samples.items()} == {
        support: row["substeps"] + 1
        for support, row in zip(plan.support_ids, diagnostics)
    }
    assert [state.payload() for state in captured] == [state.payload() for state in ordinary]
    assert diagnostics == ordinary_diagnostics
    for support, final, rows in zip(plan.support_ids, captured, samples.values()):
        assert rows[0]["time_s"] == 0.0
        assert rows[-1]["time_s"] == final.time_s
        assert rows[-1]["temperature_k"] == list(final.temperature_k)
        assert rows[-1]["z_m"] == [x * final.lithosphere_m for x in final.material_coordinate]
        assert all(a["time_s"] < b["time_s"] for a, b in zip(rows, rows[1:]))


def test_diagnostic_sample_limit_fails_closed():
    plan = build_fixture_pair_plan(_assessment())
    with pytest.raises(IntegrationContractError, match="DIAGNOSTIC_SAMPLE_LIMIT_EXCEEDED"):
        capture_numerical_step_samples(
            plan, duration_s=10.0 * 31_557_600.0,
            maximum_kinematic_fraction_per_substep=1e-6,
            maximum_samples_per_support=2,
        )


def test_synthetic_checkpoint_restore_replays_remaining_kernel_interval():
    plan = build_fixture_pair_plan(_assessment())
    full, _ = advance_pair(plan, duration_s=31_557_600.0,
                           maximum_kinematic_fraction_per_substep=0.01)
    def resumed_states():
        resumed = []
        for profile in plan.profiles:
            initial = initial_reduced_state(profile, initial_width_m=plan.initial_width_m)
            first_half, _ = pure_shear_thermal_step(initial, duration_s=15_778_800.0,
                extension_velocity_m_s=plan.signed_extension_m_per_year / 31_557_600.0,
                maximum_kinematic_fraction_per_substep=0.01)
            restored = state_from_payload(json.loads(json.dumps(first_half.payload())))
            assert restored.payload() == first_half.payload()
            second_half, _ = pure_shear_thermal_step(restored, duration_s=15_778_800.0,
                extension_velocity_m_s=plan.signed_extension_m_per_year / 31_557_600.0,
                maximum_kinematic_fraction_per_substep=0.01)
            resumed.append(second_half)
        return resumed
    restarted, repeated = resumed_states(), resumed_states()
    assert [state.payload() for state in restarted] == [state.payload() for state in repeated]
    assert all(state.time_s == 31_557_600.0 for state in restarted)
    assert len(full) == len(restarted) == 2


@pytest.mark.parametrize("mutation, message", [
    (lambda a: a.update(selected_ordered_plate_pair=[1, 3]), "SCOPE_OR_CANONICAL"),
    (lambda a: a["edge_matrix"][0].update(ordered_plate_pair=[1, 3]), "NOT_ADMITTED"),
    (lambda a: a["edge_matrix"][0].update(SECTION_ELIGIBILITY="EXCLUDED"), "NOT_ADMITTED"),
    (lambda a: a["edge_matrix"][0]["sides_plate_a_then_plate_b"][1].update(plate_id=5), "NOT_ADMITTED"),
    (lambda a: a.update(kinematics_artifact_sha256="UNKNOWN"), "PROVIDER_IDENTITY_UNKNOWN"),
    (lambda a: a.update(pair_event_census={"pair_id": "5:11", "eligibility": "UNKNOWN"}), "EVENT_CENSUS"),
    (lambda a: a["edge_matrix"][0].update(velocity_components={
        "normal_ab_xyz": [2.0, 0.0, 0.0], "tangent_xyz": [0.0, 1.0, 0.0]}), "FRAME_INVALID"),
])
def test_incompatible_support_time_or_provenance_fails_closed(mutation, message):
    assessment = copy.deepcopy(_assessment())
    mutation(assessment)
    with pytest.raises(IntegrationContractError, match=message):
        build_fixture_pair_plan(assessment)


def test_fixture_records_cannot_enter_the_repository_authority_path():
    assessment = _assessment()
    assessment.pop("fixture_marker")
    with pytest.raises(IntegrationContractError, match="SYNTHETIC_FIXTURE_MARKER_REQUIRED"):
        build_fixture_pair_plan(assessment)


def test_trajectory_contract_keeps_events_and_physical_validity_unknown():
    plan = build_fixture_pair_plan(_assessment())
    states, _ = advance_pair(plan, duration_s=31_557_600.0,
                             maximum_kinematic_fraction_per_substep=0.01)
    document = trajectory_document(plan, states, duration_s=31_557_600.0,
                                   numerical_configuration={"test": True})
    assert document["time_support"]["t0_age_ma"] == 210.0
    assert document["time_support"]["candidate_age_ma"] == pytest.approx(209.999999)
    assert document["spatial_support"]["support_ids"] == list(plan.support_ids)
    assert document["event_candidates"]["not_equivalent_to_proven_no_event"] is True
    assert document["canonical_publication"] is False
    assert len(document["fields"]) == 2
    assert document["b0_checkpoints"]["candidate"]["validation_status"] == "CANDIDATE_NONCANONICAL"
    assert document["b0_replay_recipe"]["expected_output_state_id"] == (
        document["b0_domain_states"]["candidate"]["state_id"])
    assert document["b0_replay_status"] == "DESCRIPTOR_ONLY_NOT_REGISTERED_IN_HISTORYSTORE"
    assert DomainStateEnvelope.from_dict(document["b0_domain_states"]["initial"])
    assert DomainStateEnvelope.from_dict(document["b0_domain_states"]["candidate"])
    assert CheckpointEnvelope.from_dict(document["b0_checkpoints"]["initial"])
    assert CheckpointEnvelope.from_dict(document["b0_checkpoints"]["candidate"])
    assert ForcingRecord.from_dict(document["b0_forcing_record"])
    assert ReplayRecipe.from_dict(document["b0_replay_recipe"]).forcing_ids == (
        document["b0_forcing_record"]["forcing_id"],)
    assert document["b0_replay_recipe"]["configuration_sha256"] == (
        document["b0_checkpoints"]["initial"]["configuration_sha256"])
    assert document["b0_replay_recipe"]["configuration_sha256"] == (
        document["b0_checkpoints"]["candidate"]["configuration_sha256"])


def test_candidate_bundle_is_deterministic_and_refuses_protected_or_existing_root(tmp_path):
    plan = build_fixture_pair_plan(_assessment())
    states, _ = advance_pair(plan, duration_s=31_557_600.0,
                             maximum_kinematic_fraction_per_substep=0.01)
    document = trajectory_document(plan, states, duration_s=31_557_600.0,
                                   numerical_configuration={"fraction": 0.01})
    first = tmp_path / "candidate-a"
    result = write_candidate_bundle(document, first, repository_root=ROOT,
                                    protected_roots=(tmp_path / "world_history",))
    trajectory_bytes = (first / "CANDIDATE_TRAJECTORY.json").read_bytes()
    assert result["trajectory_sha256"] == hashlib.sha256(trajectory_bytes).hexdigest()
    assert json.loads(trajectory_bytes)["canonical_publication"] is False
    second = tmp_path / "candidate-b"
    result2 = write_candidate_bundle(document, second, repository_root=ROOT,
                                     protected_roots=(tmp_path / "world_history",))
    assert (second / "CANDIDATE_TRAJECTORY.json").read_bytes() == trajectory_bytes
    assert ((second / "CANDIDATE_MANIFEST.json").read_bytes()
            == (first / "CANDIDATE_MANIFEST.json").read_bytes())
    assert result2["trajectory_sha256"] == result["trajectory_sha256"]
    with pytest.raises(IntegrationContractError, match="OVERLAPS_PROTECTED_ROOT"):
        write_candidate_bundle(document, ROOT / "WORLD_HISTORY", repository_root=ROOT,
                               protected_roots=(ROOT / "WORLD_HISTORY",))
    with pytest.raises(IntegrationContractError, match="OVERLAPS_PROTECTED_ROOT"):
        write_candidate_bundle(document, tmp_path / "world_history" / "child",
                               repository_root=ROOT, protected_roots=(tmp_path / "world_history",))
    with pytest.raises(IntegrationContractError, match="ALREADY_EXISTS"):
        write_candidate_bundle(document, first, repository_root=ROOT,
                               protected_roots=(tmp_path / "world_history",))
